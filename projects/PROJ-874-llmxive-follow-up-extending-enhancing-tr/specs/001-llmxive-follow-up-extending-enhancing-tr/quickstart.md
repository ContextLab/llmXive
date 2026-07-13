# Quickstart: llmXive Follow-up: Extending "Enhancing Train-Free Infinite-Frame Generation for Consistent Long Vid"

## Prerequisites

-   **Python**: 3.10 or higher.
-   **System**: Linux environment (GitHub Actions Free Tier compatible).
-   **Disk Space**: ~15 GB (for datasets, models, and outputs).
-   **RAM**: ≥ 7 GB available.
-   **GPU**: None required (CPU-only execution).

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-874-llmxive-follow-up-extending-enhancing-tr
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins `torch` to a CPU-only wheel to ensure compatibility with the CI runner.*

## Execution Workflow

The project follows a strict sequential workflow: **Download -> Pilot -> Generate -> Correct -> Evaluate -> Analyze**.

### Step 1: Download & Verify Data
Fetch the validated datasets from HuggingFace and verify checksums.
```bash
python code/download.py --config code/config.yaml
```
*Output*: `data/raw/` populated with verified datasets.

### Step 2: Pilot Study (Power Analysis)
Run a small pilot (N=5) to estimate variance for power analysis.
```bash
python code/analyze.py --mode pilot --config code/config.yaml
```
*Output*: `data/results/power_analysis.json` confirming N=50 sufficiency or flagging limitations.

### Step 3: Generate Baselines (Conditions A & B)
Run the MIGA pipeline to generate the baseline videos.
```bash
# Condition A: Full Self-Reflection
python code/generate.py --mode baseline-full --output data/processed/baseline_full/ --config code/config.yaml

# Condition B: Naive (No Self-Reflection)
python code/generate.py --mode baseline-naive --output data/processed/baseline_naive/ --config code/config.yaml
```
*Output*: Video files in `data/processed/baseline_full/` and `data/processed/baseline_naive/`.

### Step 4: Apply Flow Correction (Condition C)
Compute optical flow and apply warping to the naive baseline.
```bash
python code/correct.py --input data/processed/baseline_naive/ --output data/processed/flow_corrected/ --model raft-small --precision fp16
```
*Output*: Corrected video files in `data/processed/flow_corrected/`.

### Step 5: Evaluate Metrics
Calculate VBench, FVD, and Object Permanence scores for all conditions.
```bash
python code/evaluate.py --inputs data/processed/baseline_full/ data/processed/baseline_naive/ data/processed/flow_corrected/ --output data/results/metrics.csv
```
*Output*: `data/results/metrics.csv` containing scores for all videos.

### Step 6: Statistical Analysis & Reporting
Perform normality checks, significance testing, and failure analysis.
```bash
python code/analyze.py --metrics data/results/metrics.csv --output data/results/statistics.json
```
*Output*: `data/results/statistics.json` with p-values, test types, and failure case logs.

## Verification

To verify the setup, run the contract tests:
```bash
pytest tests/contract/
```
Ensure that the generated `data/results/metrics.csv` matches the schema defined in `contracts/metrics.schema.yaml`.

## Troubleshooting

-   **OOM Error**: Reduce the sample size in `code/config.yaml` or ensure no other processes are using RAM.
-   **CUDA Error**: Verify `torch` was installed with `cpu` tag. Remove any `device='cuda'` assignments in code.
-   **Dataset Missing**: Re-run `download.py` and check network connectivity to HuggingFace.