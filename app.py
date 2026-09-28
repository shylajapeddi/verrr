import os
import re
import subprocess
import tempfile

from flask import Flask, render_template, request

from langchain_google_genai import ChatGoogleGenerativeAI


# --------------------------------------------------
# Flask App
# --------------------------------------------------

app = Flask(__name__)


# --------------------------------------------------
# Gemini Configuration
# --------------------------------------------------

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    print("WARNING: GEMINI_API_KEY is not set.")

MODEL_NAME = os.environ.get(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)

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


# --------------------------------------------------
# Gemini Helper
# --------------------------------------------------

def ask_gemini(prompt):
    """Send a prompt to Gemini and return the response text."""

    if llm is None:
        return "ERROR: Gemini is not configured. Check GEMINI_API_KEY."

    try:
        response = llm.invoke(prompt)

        if hasattr(response, "content"):
            return response.content

        return str(response)

    except Exception as e:
        return f"ERROR while calling Gemini: {str(e)}"


# --------------------------------------------------
# Extract Code From Gemini Response
# --------------------------------------------------

def extract_verilog(text):
    """Extract Verilog code from a Gemini response."""

    match = re.search(
        r"```(?:verilog|systemverilog|sv)?\s*(.*?)```",
        text,
        re.DOTALL | re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    return text.strip()


# --------------------------------------------------
# Generate Verilog Design
# --------------------------------------------------

def generate_verilog(task):
    """Generate synthesizable Verilog and a testbench."""

    prompt = f"""
You are an expert Verilog HDL engineer.

User requirement:
{task}

Create a complete Verilog solution.

Return EXACTLY in this format:

DESIGN:
```verilog
<complete synthesizable Verilog code>
