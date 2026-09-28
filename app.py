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

    prompt = f"""
You are an expert Verilog HDL engineer.

User requirement:
{task}

Create a complete Verilog solution.

Return EXACTLY in this format:

DESIGN:
```verilog
<complete Verilog design>
