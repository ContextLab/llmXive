# Quickstart: llmXive Follow-up: Counterfactual Inspector Agent

## 1. Prerequisites

-   Python 3.11+
-   Git
-   Access to HuggingFace (for dataset loading)
-   2 vCPU / 7GB RAM environment (e.g., GitHub Actions, local VM)

## 2. Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-903-llmxive-follow-up-extending-data-journal
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins specific versions of `transformers`, `scipy`, and `datasets` to ensure CPU compatibility.*

## 3. Running the Pipeline

### 3.1. Single Dataset Test
To test the pipeline on a single dataset (e.g., the Synthetic SQL dataset):

```bash
python code/main.py --dataset "gretelai/synthetic_text_to_sql" --mode baseline_and_inspector
```

**Expected Output**:
-   A JSON file in `data/processed/` containing the `IntegratedStory`.
-   Console logs showing the Baseline Narrative and any Counterfactual Insights found.

### 3.2. Full Batch Run
To run the experiment on all available datasets (or the subset defined in config):

```bash
python code/main.py --mode full_experiment --output-dir results/
```

**Note**: This will take -6 hours on a standard GitHub Actions runner.

## 4. Evaluation & Metrics

### 4.1. Generating Blinded Stories
Before expert evaluation, generate anonymized stories:

```bash
python code/evaluation/rubric.py --generate-blinded --output-dir eval_data/
```

### 4.2. Calculating Metrics
After expert scores are manually entered (or simulated for testing):

```bash
python code/evaluation/metrics.py --input eval_data/scores.json
```

**Output**:
-   `metrics_report.json`: Contains SC-001 (Narrative Depth), SC-002 (Bias), SC-003 (Feasibility), SC-004 (Traceability).

## 5. Troubleshooting

-   **OOM Error**: If the process crashes with "Out of Memory", ensure `datasets` is loaded in chunks or use the `--sample-size` flag to limit rows.
-   **LLM Timeout**: If the local LLM takes too long, set `LLM_FALLBACK_MODE=api` in the environment variables to switch to the batched API mode.
-   **No Counterfactuals Found**: This is a valid result. The system will output a story stating "No significant counterfactuals found" rather than hallucinating.

## 6. Verification

Run the contract tests to ensure data integrity:

```bash
pytest tests/contract/
```
