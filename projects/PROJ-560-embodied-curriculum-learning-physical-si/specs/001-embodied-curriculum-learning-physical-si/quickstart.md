# Quickstart: Embodied Curriculum Learning

## Prerequisites

- Python 3.11+
- pip (Python package installer)

## Installation

1.  **Clone the repository** (or navigate to the project directory):
    ```bash
    cd projects/PROJ-560-embodied-curriculum-learning-physical-si
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
    *Note: `requirements.txt` pins versions for `pandas`, `scipy`, `statsmodels`, `numpy`, `pyyaml`.*

## Usage

### Mode 1: Secondary Analysis (Public Data)

Process an existing dataset (e.g., `data/raw/public_dataset.csv`) that contains `pre_test_score`, `post_test_score`, and `instruction_type`.

```bash
python code/src/cli.py \
  --mode=secondary_analysis \
  --input=data/raw/public_dataset.csv \
  --output=data/processed/analysis_result.json
```

**Expected Output**: `data/processed/analysis_result.json` containing t-statistics, p-values, and associational framing.

### Mode 2: Synthetic Data Generation

Generate a controlled dataset with known ground truths to validate the pipeline.

```bash
python code/src/cli.py \
  --mode=synthetic \
  --n_participants=100 \
  --effect_size=0.5 \
  --output=data/synthetic/generated_dataset.csv
```

**Expected Output**: `data/synthetic/generated_dataset.csv` with 100 rows, known mean differences, and `instruction_type` labels.

### Mode 3: Full Analysis with Sensitivity Sweep

Run the full analysis pipeline including the sensitivity sweep (requires N ≥ 30).

```bash
python code/src/cli.py \
  --mode=secondary_analysis \
  --input=data/raw/public_dataset.csv \
  --sweep_thresholds=0.01,0.05,0.10 \
  --output=data/processed/full_report.json
```

**Expected Output**: `data/processed/full_report.json` including `sensitivity_analysis` array and `robustness_warning` flags.

## Verification

To verify the installation and pipeline:

1.  Run the synthetic data generator with a known effect size.
2.  Run the analysis mode on the generated data.
3.  Check `full_report.json` to ensure:
    - `p_value` is significant (p < 0.05) for the known effect.
    - `inference_framing` is `"associational"`.
    - `power_flag` is `"adequate"` (if N is large enough).

## Troubleshooting

- **Missing Columns**: If the system reports "Missing `instruction_type`", it will automatically switch to Synthetic Data Mode. Ensure your public dataset has the required columns.
- **Small Sample**: If N < 30, the sensitivity sweep will be skipped, and a warning will be logged.
- **Collinearity**: If predictors are highly correlated ($|r| > 0.8$), the system will report a warning and refrain from claiming independent effects.
