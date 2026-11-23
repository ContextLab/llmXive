# llmXive Project Setup Guide

## Prerequisites

- Python 3.10 or higher
- pip (Python package installer)
- virtualenv (or use Python's built-in venv)

## Virtual Environment Setup

This project uses a virtual environment to isolate dependencies. Follow these steps to set it up:

### Option 1: Using `venv` (Recommended, built into Python)

1. Navigate to the project root:
 ```bash
 cd /path/to/llmxive-follow-up-extending-wbench-a-com
 ```

2. Create the virtual environment:
 ```bash
 python -m venv venv
 ```

3. Activate the virtual environment:
 - On Linux/macOS:
 ```bash
 source venv/bin/activate
 ```
 - On Windows:
 ```bash
 venv\Scripts\activate
 ```

4. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

### Option 2: Using `virtualenv`

1. Install virtualenv if not already installed:
 ```bash
 pip install virtualenv
 ```

2. Create the virtual environment:
 ```bash
 virtualenv venv
 ```

3. Activate and install dependencies (same as above).

## Project Structure

```
.
├── code/
│ ├── README.md # This file
│ ├── requirements.txt # Python dependencies
│ ├── setup_directories.py
│ ├── config.py
│ └──... (other modules)
├── data/
│ ├── raw/
│ ├── processed/
│ └── checksums.json
├── tests/
│ ├── unit/
│ ├── integration/
│ └── contract/
├── results/
└── specs/
```

## Quick Start

1. **Setup Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # Or venv\Scripts\activate on Windows
 pip install -r code/requirements.txt
 ```

2. **Verify Directory Structure**:
 ```bash
 python code/setup_directories.py
 ```

3. **Run the Pipeline**:
 Refer to `quickstart.md` for detailed execution instructions.

## Common Issues

- **Permission denied on activation**: Ensure you have write permissions in the project directory.
- **Module not found**: Verify the virtual environment is activated and dependencies are installed.
- **Python version mismatch**: Ensure you are using Python 3.10+.

## Development Workflow

- Always activate the virtual environment before running scripts.
- Use `pip install -r code/requirements.txt` after pulling updates.
- Run tests before committing:
 ```bash
 pytest tests/
 ```
- Format code with Black and lint with Ruff (see T003).

## License

[Project License]
