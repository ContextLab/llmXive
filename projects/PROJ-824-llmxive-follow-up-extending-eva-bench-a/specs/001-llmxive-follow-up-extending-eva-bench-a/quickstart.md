# Quickstart: llmXive follow-up: extending "EVA-Bench: A New End-to-end Framework for Evaluating Voice Agents"

## Prerequisites

-   Python 3.11+
-   `ffmpeg` installed on the system (required by `pydub`).
-   Access to HuggingFace (no token required for public datasets, but recommended for rate limits).

## Installation

1.  **Clone the repository** (if not already done):
    ```bash
    git clone <repo-url>
    cd projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a
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

## Running the Pipeline

### 1. Download Data
Fetch the EVA-Bench dataset and verify checksums.
```bash
python code/data/download.py
```
*Output*: `data/raw/eva_bench_csm_airline.jsonl` and `data/checksums.json`.
*Note*: This step will also verify the presence of audio files.

### 2. Validate Schemas
Ensure data conforms to the contract definitions.
```bash
python code/scripts/validate_schemas.py --input data/raw/ --schema contracts/dataset.schema.yaml
```

### 3. Run Latency Injection & Evaluation
Execute the full sweep (starting from a low latency threshold up to 2000ms) on all scenarios.
```bash
python code/processing/pipeline_runner.py --mode full
```
*Note*: If the run exceeds 4 hours, it will automatically switch to `--mode sample` (50 scenarios) to respect CI limits.

### 4. Analyze Results
Perform statistical analysis and generate plots.
```bash
python code/analysis/stats_models.py
python code/analysis/comparison.py
```
*Output*: `results/analysis_report.json`, `results/degradation_curves.png`.

### 5. Generate Report
Compile the final comparative report.
```bash
python code/visualization/plots.py --output results/final_report.pdf
```

## Validation

-   **Check Injection**: Verify `data/processed/` contains files with increased duration.
-   **Check Stats**: Ensure `results/analysis_report.json` contains a `breakpoint_ms`, `p_value`, and `sensitivity_range`.
-   **Check Time**: Confirm the entire run completed in < 6 hours (check `logs/timing.log`).
-   **Check Schemas**: Ensure all output files pass the contract validation defined in `contracts/`.