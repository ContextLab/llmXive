# llmXive Project: Evaluating LLMs for Security Vulnerability Detection

## Project Structure
- `src/`: Source code
- `tests/`: Unit tests
- `data/`: Data directory (raw, processed, results)
- `specs/`: Feature specifications

## Setup
1. Create virtual environment: `python -m venv venv`
2. Activate: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Run tests: `pytest`

## Configuration
- `pyproject.toml`: Black, Ruff, and Pytest configurations
- `src/utils/config.py`: Runtime parameters and model selection logic
