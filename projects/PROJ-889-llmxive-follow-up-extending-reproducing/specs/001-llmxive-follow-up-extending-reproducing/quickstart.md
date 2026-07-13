# Quickstart: llmXive follow-up: extending "Reproducing, Analyzing, and Detecting Reward Hacking in Rubric-Based R"

## Prerequisites

- Python 3.11+
- `pip` or `poetry`
- Access to the CHERRL repository (for data download)

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-889-llmxive-follow-up-extending-reproducing
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    **Note**: `requirements.txt` includes `jsonschema` for runtime schema validation and `scipy` for Wilcoxon signed-rank test.

4.  **Download Data**:
    - Download the CHERRL training logs from the canonical source (verified URL TBD by user).
    - Place the raw log files in `data/raw/`.
    - Ensure files are named consistently (e.g., `seed_01_lexical.csv`, `seed_01_format.csv`).
    - If the canonical source is not available, the pipeline will halt with a clear error.

## Running the Pipeline

### 1. Ingest and Compute Divergence (with Sensitivity Analysis)
Run the ingestion script to compute $G(t)$, $\Delta G(t)$, z-scores, and perform hyperparameter grid search:
```bash
python code/ingestion.py --input-dir data/raw --output data/processed/trajectories_divergence.csv
```
**Output**: `trajectories_divergence.csv` with columns including `G_t`, `dG_t`, `z_score`, `hacked_label`, and metadata (`window_size`, `z_threshold`, `detection_method`).

### 2. Generate Ground Truth (with Extended Independence Check)
Run the ground truth script to derive labels from $J_{\text{gold}}$ and check independence of both $J_{\text{unbiased}}$ and $J_{\text{biased}}$ against $J_{\text{gold}}$:
```bash
python code/ground_truth.py --input data/processed/trajectories_divergence.csv --output data/processed/trajectories_gt.csv
```
**Output**: `trajectories_gt.csv` with columns including `gt_hacked`, `correlation_J_unbiased_J_gold`, `correlation_J_biased_J_gold`, and `independence_check_passed`.

*Note: If the independence check (FR-006) fails (either correlation > 0.8), this script will exit with an error and the correlation values. The dataset is considered invalid for this study.*

### 3. Run Detection and Evaluation
Run the full evaluation pipeline:
```bash
python code/evaluation.py --divergence data/processed/trajectories_divergence.csv --ground-truth data/processed/trajectories_gt.csv --output data/processed/metrics.csv
```
**Output**: `metrics.csv` with Precision, Recall, F1-scores, Wilcoxon/t-test results, effect sizes, and corrected p-values per bias type.

**Conditional Step**: If the standard deviation of F1-scores across rubric types exceeds 0.15 (SC-003 fails), the system automatically triggers rubric-specific tuning:
```bash
python code/tune_rubric_specific.py --divergence data/processed/trajectories_divergence.csv --ground-truth data/processed/trajectories_gt.csv --output data/processed/metrics_rubric_specific.csv
```
**Output**: `metrics_rubric_specific.csv` with per-rubric thresholds and updated metrics.

### 4. View Results
The output `data/processed/metrics.csv` (or `metrics_rubric_specific.csv` if tuning was triggered) contains Precision, Recall, F1-scores, statistical test results, effect sizes, and corrected p-values per bias type.

## Testing

Run the full test suite to verify correctness:
```bash
pytest tests/ -v
```

Run only contract validation tests:
```bash
pytest tests/contract/ -v
```

Run only unit tests:
```bash
pytest tests/unit/ -v
```

Run only integration tests:
```bash
pytest tests/integration/ -v
```

## Troubleshooting

- **Missing Data**: If `data/raw/` is empty, the pipeline will fail with a clear error. Ensure CHERRL logs are downloaded from the verified canonical source.
- **Independence Check Failed**: If `ground_truth.py` exits with "Correlation > 0.8", the dataset is invalid for this study. The error message will report which correlation(s) exceeded the threshold. Investigate whether $J_{\text{unbiased}}$ or $J_{\text{biased}}$ (or both) are coupled to $J_{\text{gold}}$.
- **Zero Variance**: The detector handles zero variance in $G(t)$ by setting $z\_score = 0$ or using an epsilon floor. No manual intervention required.
- **Non-Normal Distribution**: If the Kolmogorov-Smirnov test indicates non-normal $G(t)$ (p < 0.05), the system automatically switches to IQR-based detection (`detection_method = "iqr"`). This is logged in the output metadata.
- **Low Statistical Power**: With N=5 seeds, effect sizes may be small. The Wilcoxon test is more robust than a t-test for small samples. Review effect sizes and credible intervals alongside p-values.
