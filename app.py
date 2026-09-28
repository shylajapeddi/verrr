import os
import re
import subprocess
import tempfile

from flask import Flask, render_template, request
from langchain_google_genai import ChatGoogleGenerativeAI

app = Flask(__name__)

# -----------------------------
# Gemini Configuration
# -----------------------------

API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

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


# -----------------------------
# Gemini Function
# -----------------------------

def ask_gemini(prompt):
    """Send a prompt to Gemini."""

    if llm is None:
        return "ERROR: GEMINI_API_KEY is not configured."

    try:
        response = llm.invoke(prompt)

        if hasattr(response, "content"):
            return response.content

        return str(response)

    except Exception as e:
        return f"ERROR: {str(e)}"


# -----------------------------
# Generate Verilog
# -----------------------------

def generate_verilog(task):
    """Generate Verilog design and testbench."""

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

    design = (
        design_match.group(1).strip()
        if design_match
        else ""
    )

    testbench = (
        testbench_match.group(1).strip()
        if testbench_match
        else ""
    )

    return design, testbench, response
