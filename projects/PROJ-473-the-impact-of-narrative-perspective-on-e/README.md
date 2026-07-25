# The Impact of Narrative Perspective on Empathy and Moral Judgement

This project investigates whether first-person or third-person narration influences reader empathy and moral judgement.

## Setup

1. Ensure Python 3.11 is installed.
2. Create a virtual environment:
 ```bash
 python3.11 -m venv venv
 source venv/bin/activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
4. Download the required spaCy model:
 ```bash
 python -m spacy download en_core_web_sm
 ```

## Project Structure

- `code/`: Source code for data loading, extraction, analysis, and utilities.
- `data/`: Raw and processed data files.
- `tests/`: Unit and integration tests.
- `artifacts/`: Final analysis outputs (plots, reports).
- `specs/`: Research design documents.

## Running the Pipeline

Refer to `code/main.py` for entry points to the extraction, matching, and analysis pipelines.