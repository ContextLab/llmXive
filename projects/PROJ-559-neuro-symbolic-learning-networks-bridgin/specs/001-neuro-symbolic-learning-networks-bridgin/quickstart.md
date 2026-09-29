# Quickstart: Neuro-Symbolic Learning Networks

## Prerequisites

- Python 3.11+
- R 4.3+ (optional, if using R scripts directly)
- Git
- Access to a GitHub Actions runner (or local environment with similar resources).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-559-neuro-symbolic-learning-networks-bridgin
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

## Configuration

Edit `code/config.yaml` to set:
- `random_seed`: For reproducibility.
- `dataset_urls`: Verify they match the `# Verified datasets` block.
- `simulation_size`: Number of students per condition.
- `timeout_seconds`: Download timeout (default: a configurable duration).

## Running the Pipeline

### 0. Validate Citations (Automated Gate)
Before running the pipeline, the `Reference-Validator Agent` ensures all citations are valid.
```bash
python code/tools/reference_validator.py --threshold 0.7
```
*Note*: In CI, this step runs as `validate-citations` in the GitHub Actions workflow. If the threshold is not met, the job fails with exit code 1, blocking the merge.

### 1. Download and Validate Data
```bash
python code/data/download_assistments.py
python code/data/download_khan.py  # Optional: fails gracefully if missing
python code/data/unify_datasets.py # Handles partial success
python code/data/validate_schema.py
```
*Expected Output*: `data/raw/assistments.csv` and `data/processed/unified_problems.csv`.

### 2. Human Data Acquisition (T030b) - MANUAL STEP
- **Protocol**: Deploy a mock survey interface (e.g., Google Forms) to collect data from ≥50 participants for the pilot and ≥200 for the final analysis.
- **Ingestion**: Save collected data as `data/pilot/real_pilot_data.csv` (pilot) and `data/processed/real_student_data.csv` (final).
- **Fallback**: If no data is collected after 48h, run the pipeline in **Feasibility Mode** (skip calibration, disable human claims).

### 3. Generate Explanations
```bash
python code/generation/batch_generate.py --conditions neural,symbolic,neuro_symbolic
python code/generation/quality_check.py # T016: Coherence check
```
*Expected Output*: Explanation files in `data/traces/`.

### 4. Calibrate Simulator (Pilot Phase)
```bash
python code/simulation/pilot_calibrator.py
```
*Note*: If `real_pilot_data.csv` is missing, this step is skipped, and the pipeline enters Feasibility Mode.

### 5. Run Simulation
```bash
python code/simulation/run_simulation.py
```
*Expected Output*: `data/processed/interaction_logs.csv`.

### 6. Run Analysis
```bash
bash code/analysis/run_analysis.sh
```
*Note*: This script orchestrates the Python analysis and R script invocation, capturing output into the SSoT.
*Expected Output*: `results/regression_summary.md` and `results/effect_sizes.csv`.

## Verification

- **Check Resource Usage**: Monitor CPU/RAM during the run. Peak should be < 2 cores / 7 GB.
- **Check Outputs**: Verify that `interaction_logs.csv` has a substantial number of rows and includes all three conditions.
- **Check Logs**: Ensure no timeout errors occurred.

## Troubleshooting

- **Download Timeout**: If the 300s timeout is exceeded, check network connectivity or reduce the dataset subset size.
- **Memory Error**: If OOM occurs, reduce `simulation_size` or enable streaming for the dataset.
- **Model Error**: If the LLM fails, ensure the correct model name is in `config.yaml` and that 4-bit loading is enabled.
- **Missing Human Data**: If `real_pilot_data.csv` is missing, the pipeline will log a warning and proceed in Feasibility Mode.
- **Citation Validation Failure**: If `reference_validator.py` fails, check the `# Verified datasets` block and the `spec.md` citations for typos or broken links.