# Quickstart: Evaluating the Impact of LLM-Generated Code Explanations on Comprehension

## Prerequisites
- Python 3.11+
- Git
- Access to HuggingFace Hub (token required for CodeLlama if gated, though CodeSearchNet is public).

## Setup

1.  **Clone and Install**
    ```bash
    cd projects/PROJ-188-evaluating-the-impact-of-llm-generated-c
    python -m venv venv
    source venv/bin/activate
    pip install -r code/requirements.txt
    ```

2.  **Configure Environment**
    Create a `.env` file in `code/` with:
    ```bash
    HF_TOKEN=your_huggingface_token
    RANDOM_SEED=42
    MAX_TOKENS=150
    ```

## Execution

### Step 1: Data Curation & Explanation Generation
Run the curation script to download CodeSearchNet and generate explanations.
```bash
python code/01_data_curation.py
```
*Output*: `data/intermediate/explanations.jsonl`, `data/raw/codesearchnet.parquet`.

### Step 2: Survey Simulation (or Data Loading)
If simulating for testing:
```bash
python code/02_survey_logic.py --mode simulate --n_participants 90
```
*Output*: `data/intermediate/survey_responses.csv`.

If using real data, place CSV in `data/intermediate/survey_responses.csv` and skip.

### Step 3: Statistical Analysis
Run the analysis pipeline.
```bash
python code/03_analysis.py
```
*Output*: `data/processed/analysis_results.json`, `data/processed/figures/`.

## Verification
Check that the analysis output contains:
- Interaction p-value < 0.05 (if hypothesis supported).
- Tukey adjusted p-values.
- Sensitivity sweep results for BLEU thresholds {0.70, 0.80, 0.90}.
