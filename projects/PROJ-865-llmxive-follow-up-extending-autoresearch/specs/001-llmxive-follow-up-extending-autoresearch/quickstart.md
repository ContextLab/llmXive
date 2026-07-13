# Quickstart: llmXive follow-up: extending "AutoResearchClaw"

## 1. Prerequisites

- **Python**: 3.11 or higher.
- **System**: Linux environment (GitHub Actions runner compatible).
- **Memory**: Minimum 7 GB RAM available.
- **Disk**: Minimum 10 GB free space.

## 2. Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-865-llmxive-followup-extending-autoresearch
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
    *Note: `requirements.txt` pins versions to ensure reproducibility on CPU-only runners.*

## 3. Data Setup

The project uses verified HuggingFace datasets. Run the ingestion script to download, sample, and derive failure logs from reasoning traces:

```bash
python code/01_data_ingestion/download_arc_bench.py
python code/01_data_ingestion/parse_reasoning_traces.py
```

This script:
- Downloads the verified parquet files.
- Checksums the raw data.
- Samples a subset of topics.
- Derives `derived_error_log` fields from `reasoning` traces.
- Saves the result to `data/derived/annotated_cases.csv`.

## 4. Running the Pipeline

### Step 1: Annotate & Distill Rules
Generate the rule library from the annotated cases:
```bash
python code/02_annotation_distillation/annotate_failures.py
python code/02_annotation_distillation/distill_rules.py
```
*Output: `data/derived/rules_library.json` (validated against schema)*

### Step 2: Execute Experiments
Run the rule engine on CI and the baseline on a larger runner (or locally):
```bash
# On CI (Rule Engine)
python code/03_execution/run_experiments.py --mode rule_engine

# On Larger Runner (Baseline)
python code/03_execution/run_baseline_external.py --mode baseline
```
*Output: `data/derived/pivot_attempts.csv` (merged logs)*

### Step 3: Statistical Analysis
Fit the mixed-effects model and generate the report:
```bash
python code/04_analysis/statistical_model.py
python code/04_analysis/error_taxonomy.py
```
*Output: `results/statistical_report.md`, `results/metrics_summary.csv`*

## 5. Verification

To verify the pipeline:
1.  Run the unit tests:
    ```bash
    pytest tests/
    ```
2.  Check the checksums in `state/projects/PROJ-865-llmxive-follow-up-extending-autoresearch.yaml`.
3.  Ensure `results/statistical_report.md` contains the interaction term p-value.
4.  Ensure `update_state.py` was run after each phase.

## 6. Troubleshooting

- **Memory Error**: If you encounter `OOM` (Out of Memory), the system will automatically fallback to `TinyLlama-1.1B` for distillation. If that fails, it will switch to regex-based distillation.
- **Dataset Missing**: Ensure the HuggingFace token is set if authentication is required (though the verified URLs are public).
- **Rule Engine Failure**: Check that `rules_library.json` is valid JSON and matches the schema in `contracts/`.
- **Baseline Execution**: If the baseline runner fails, the pipeline will pause and wait for manual upload of baseline logs.