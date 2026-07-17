# PROJ-188: Evaluating the Impact of LLM-Generated Code Explanations on Comprehension

## Overview
This project investigates how LLM-generated code explanations affect developer comprehension compared to code-only and code-with-docstring conditions.

## Structure
- `code/`: Implementation scripts
- `tests/`: Unit and integration tests
- `data/`: Raw, intermediate, and processed data
- `specs/`: Feature specifications and design documents

## Prerequisites
- Python 3.11
- See `code/requirements.txt` for dependencies

## Quick Start
1. Install dependencies: `pip install -r code/requirements.txt`
2. Run data curation: `python code/01_data_curation.py`
3. Run survey logic: `python code/02_survey_logic.py`
4. Run analysis: `python code/03_analysis.py`

## Governance
This project requires the Constitution to be amended to align Principle VII with Spec FR-001 before execution of T014.
