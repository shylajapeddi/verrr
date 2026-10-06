import os
import re
import subprocess
import tempfile

from flask import Flask, render_template, request
from google import genai
from google.genai import types


app = Flask(__name__)


# ==========================================
# GEMINI CONFIGURATION
# ==========================================

API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
llm = None

if API_KEY:
    try:
        llm = ChatGoogleGenerativeAI(
            model=MODEL_NAME,
            google_api_key=API_KEY,
            temperature=0.2
        )

        print("Gemini initialized successfully.")

    except Exception as e:
        print("Gemini initialization error:", e)


# ==========================================
# ASK GEMINI
# ==========================================

def ask_gemini(prompt):

    if llm is None:
        return "ERROR: GEMINI_API_KEY is not configured."

    try:

        response = llm.invoke(prompt)

        if hasattr(response, "content"):
            return response.content

        return str(response)

    except Exception as e:

        return "ERROR: " + str(e)


# ==========================================
# GENERATE VERILOG
# ==========================================

def generate_verilog(task):

    prompt = (
        "You are an expert Verilog HDL engineer.\n\n"

        "User requirement:\n"
        + task
        + "\n\n"

        "Create a complete Verilog solution.\n\n"

        "Return EXACTLY in this format:\n\n"

        "DESIGN:\n"
        "```verilog\n"
        "<complete Verilog design>\n"
        "```\n\n"

        "TESTBENCH:\n"
        "```verilog\n"
        "<complete Verilog testbench>\n"
        "```\n\n"

        "Rules:\n"
        "1. Use Verilog/SystemVerilog syntax supported by Icarus Verilog.\n"
        "2. Create a complete synthesizable design.\n"
        "3. The testbench must correctly instantiate the design.\n"
        "4. Include useful test cases.\n"
        "5. The testbench must use $finish.\n"
        "6. Do not add explanations inside the code blocks."
    )

    response = ask_gemini(prompt)

    if response.startswith("ERROR:"):
        return "", "", response


    design_match = re.search(
        r"DESIGN:\s*```(?:verilog|systemverilog|sv)?\s*(.*?)```",
        response,
        re.DOTALL | re.IGNORECASE
    )


    testbench_match = re.search(
        r"TESTBENCH:\s*```(?:verilog|systemverilog|sv)?\s*(.*?)```",
        response,
        re.DOTALL | re.IGNORECASE
    )


    design = ""

    if design_match:
        design = design_match.group(1).strip()


    testbench = ""

    if testbench_match:
        testbench = testbench_match.group(1).strip()


    return design, testbench, response


# ==========================================
# RUN VERILOG SIMULATION
# ==========================================

def run_verilog_simulation(verilog_code, testbench_code):

    if not verilog_code:
        return "ERROR: Verilog design is empty."

    if not testbench_code:
        return "ERROR: Testbench is empty."


    with tempfile.TemporaryDirectory() as temp_dir:

        design_file = os.path.join(
            temp_dir,
            "design.v"
        )

        testbench_file = os.path.join(
            temp_dir,
            "testbench.v"
        )

        output_file = os.path.join(
            temp_dir,
            "simulation"
        )


        # Write design
        with open(
            design_file,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(verilog_code)


        # Write testbench
        with open(
            testbench_file,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(testbench_code)


        # ==================================
        # COMPILE
        # ==================================

        try:

            compile_result = subprocess.run(
                [
                    "iverilog",
                    "-g2012",
                    "-o",
                    output_file,
                    design_file,
                    testbench_file
                ],

                capture_output=True,
                text=True,
                timeout=30
            )

        except Exception as e:

            return (
                "ERROR during compilation: "
                + str(e)
            )


        if compile_result.returncode != 0:

            return (
                "COMPILATION FAILED\n\n"
                + compile_result.stderr
            )


        # ==================================
        # SIMULATION
        # ==================================

        try:

            simulation_result = subprocess.run(
                [
                    "vvp",
                    output_file
                ],

                capture_output=True,
                text=True,
                timeout=30
            )

        except Exception as e:

            return (
                "ERROR during simulation: "
                + str(e)
            )


        if simulation_result.returncode != 0:

            return (
                "SIMULATION FAILED\n\n"
                + simulation_result.stderr
            )


        output = simulation_result.stdout.strip()


        if not output:

            output = (
                "Simulation completed successfully "
                "with no console output."
            )


        return (
            "COMPILATION: PASSED\n"
            "SIMULATION: PASSED\n\n"
            "SIMULATION OUTPUT:\n"
            + output
        )


# ==========================================
# GENERATE TEST REPORT
# ==========================================

def generate_test_report(
    task,
    design,
    testbench,
    simulation_result
):

    prompt = (
        "You are a Verilog testing engineer.\n\n"

        "USER REQUIREMENT:\n"
        + task
        + "\n\n"

        "VERILOG DESIGN:\n"
        + design
        + "\n\n"

        "TESTBENCH:\n"
        + testbench
        + "\n\n"

        "SIMULATION RESULT:\n"
        + simulation_result
        + "\n\n"

        "Create a simple report with these sections:\n\n"

        "1. Requirement\n"
        "2. Design Summary\n"
        "3. Test Cases\n"
        "4. Simulation Result\n"
        "5. Final Status\n\n"

        "Do not invent simulation results.\n"
        "Keep the explanation simple."
    )


    return ask_gemini(prompt)


# ==========================================
# COMPLETE WORKFLOW
# ==========================================

def process_task(task):

    if not task.strip():

        return {
            "design": "",
            "testbench": "",
            "simulation": "",
            "report": "Please enter a Verilog requirement."
        }


    design, testbench, raw_response = generate_verilog(task)


    if not design or not testbench:

        return {
            "design": design,
            "testbench": testbench,
            "simulation": "",
            "report": (
                "Gemini did not return the expected "
                "DESIGN and TESTBENCH sections.\n\n"
                + raw_response
            )
        }


    simulation_result = run_verilog_simulation(
        design,
        testbench
    )


    report = generate_test_report(
        task,
        design,
        testbench,
        simulation_result
    )


    return {
        "design": design,
        "testbench": testbench,
        "simulation": simulation_result,
        "report": report
    }


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/", methods=["GET", "POST"])
def home():

    result = {
        "design": "",
        "testbench": "",
        "simulation": "",
        "report": ""
    }

    task = ""

    if request.method == "POST":

        try:
            task = request.form.get("task", "").strip()

            result = process_task(task)

        except Exception as e:

            print("ERROR IN HOME ROUTE:", str(e))

            result = {
                "design": "",
                "testbench": "",
                "simulation": "",
                "report": "ERROR: " + str(e)
            }

    return render_template(
        "index.html",
        task=task,
        design=result["design"],
        testbench=result["testbench"],
        simulation=result["simulation"],
        report=result["report"]
    )

# ==========================================
# HEALTH CHECK
# ==========================================

@app.route("/health")
def health():

    return {
        "status": "ok"
    }


# ==========================================
# START SERVER
# ==========================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )


    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
