"""
Setup script to ensure prompt directory and files exist.
This script creates the data/prompts/ directory and populates it
with the four required prompt condition templates if they do not exist.
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = PROJECT_ROOT / "data" / "prompts"

PROMPT_FILES = {
    "zero_shot_basic.txt": (
        "Translate the following Python code to JavaScript. Ensure the logic and functionality remain identical.\n\n"
        "Python Code:\n{python_code}\n\n"
        "JavaScript Code:"
    ),
    "zero_shot_style.txt": (
        "Translate the following Python code to JavaScript. Adhere to modern JavaScript best practices (ES6+), "
        "use strict mode, and ensure variable naming conventions are adapted appropriately (e.g., snake_case to camelCase).\n\n"
        "Python Code:\n{python_code}\n\n"
        "JavaScript Code:"
    ),
    "few_shot_basic.txt": (
        "Translate the following Python code to JavaScript.\n\n"
        "Example 1:\n"
        "Python:\n"
        "def add(a, b):\n"
        "    return a + b\n\n"
        "JavaScript:\n"
        "function add(a, b) {\n"
        "    return a + b;\n"
        "}\n\n"
        "Example 2:\n"
        "Python:\n"
        "def greet(name):\n"
        "    print(f\"Hello, {name}\")\n\n"
        "JavaScript:\n"
        "function greet(name) {\n"
        "    console.log(`Hello, ${name}`);\n"
        "}\n\n"
        "Now translate this:\n"
        "Python Code:\n{python_code}\n\n"
        "JavaScript Code:"
    ),
    "few_shot_style.txt": (
        "Translate the following Python code to JavaScript. Follow modern JavaScript (ES6+) standards, "
        "use arrow functions where appropriate, and convert variable naming from snake_case to camelCase.\n\n"
        "Example 1:\n"
        "Python:\n"
        "def calculate_area(radius):\n"
        "    return 3.14159 * radius * radius\n\n"
        "JavaScript:\n"
        "const calculateArea = (radius) => {\n"
        "    return 3.14159 * radius * radius;\n"
        "};\n\n"
        "Example 2:\n"
        "Python:\n"
        "def is_even(number):\n"
        "    return number % 2 == 0\n\n"
        "JavaScript:\n"
        "const isEven = (number) => number % 2 === 0;\n\n"
        "Now translate this:\n"
        "Python Code:\n{python_code}\n\n"
        "JavaScript Code:"
    ),
}

def main():
    """Create prompt directory and files."""
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ensuring prompt directory exists: {PROMPTS_DIR}")

    for filename, content in PROMPT_FILES.items():
        file_path = PROMPTS_DIR / filename
        if not file_path.exists():
            file_path.write_text(content, encoding="utf-8")
            print(f"Created prompt file: {file_path}")
        else:
            print(f"Prompt file already exists: {file_path}")

    print("Prompt setup complete.")

if __name__ == "__main__":
    main()
