# Quickstart: Evaluating the Impact of LLM-Generated Code Explanations

## Prerequisites

- Python 3.11+
- Git
- HuggingFace account (for model access, if required)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/001-evaluating-the-impact-of-llm-generated-c
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

4.  **Set environment variables**:
    Create a `.env` file in `code/` (or set in shell):
    ```bash
    export HF_TOKEN="your_huggingface_token_here"
    export MODEL_PATH="TinyLlama/TinyLlama-1.1B-Chat-v1.0" # Primary CPU model
    ```

## Running the Pipeline

The pipeline is designed to run end-to-end.

### Step 1: Data Curation & Explanation Generation
Generates explanations for the curated snippets.
```bash
python code/01_data_curation.py
python code/02_explanation_gen.py
```
*Note: This step uses TinyLlama-1.1B for CPU feasibility. CodeLlama-7B is a fallback.*

### Step 2: Survey Simulation
Generates mock participant data to simulate the survey results.
```bash
python code/03_survey_logic.py
```
*Output: `data/intermediate/mock_responses.csv` (row-level) and `data/intermediate/participant_summary.csv` (aggregate).*

### Step 3: Data Cleaning
Applies filtering rules (PII removal, speeder exclusion) and calculates `missing_count` for the summary.
```bash
python code/04_data_cleaning.py
```
*Output: `data/intermediate/cleaned_responses.csv` and updated `participant_summary.csv`.*

### Step 4: Statistical Analysis
Runs LMM, Tukey HSD, and BLEU descriptive analysis.
```bash
python code/05_analysis.py
```
*Output: `data/processed/results.csv`.*

### Step 5: Report Generation
Assembles the final report with the required limitation statement.
```bash
python code/06_report_gen.py
```
*Output: `data/processed/final_report.md`.*

## Validation

To verify the pipeline:
```bash
pytest tests/
```

## Troubleshooting

- **OOM Error**: If `02_explanation_gen.py` runs out of memory, ensure `load_in_4bit=True` is set for TinyLlama. If it still fails, the fallback to CodeLlama-7B (if GPU available) will trigger.
- **Missing Data**: Ensure `code/01_data_curation.py` successfully downloaded the HumanEval subset.