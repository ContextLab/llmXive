# PROJ-340: Investigating the Correlation Between Gut Microbiome Composition and Sleep Architecture

## Overview
This project implements an automated pipeline to analyze the correlation between gut microbiome composition and sleep architecture, adhering to strict reproducibility and validation principles.

## Project Structure
- `code/`: Python source modules
- `data/`: Raw, processed, and result data
- `tests/`: Unit and integration tests
- `specs/`: Design documents and contracts
- `data/processed/`: Intermediate processed data (gitignored except for.gitkeep)
- `data/results/`: Analysis outputs (gitignored except for.gitkeep)

## Setup
1. Ensure Python 3.11+ is installed.
2. Install dependencies: `pip install -r requirements.txt`
3. Run tests: `pytest`

## Execution
Run the main pipeline: `python code/main.py`

## Configuration
Copy `.env.example` to `.env` and configure environment variables as needed.
