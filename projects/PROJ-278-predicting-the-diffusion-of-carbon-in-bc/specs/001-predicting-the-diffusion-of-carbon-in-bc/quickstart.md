# Quickstart Guide: Predicting Carbon Diffusion in BCC Metals

This guide provides step-by-step instructions to run the full pipeline end-to-end,
ensuring reproducibility as required by task T024.

## Prerequisites

- Python 3.11+
- Project dependencies installed (see `code/requirements.txt`)
- Sufficient disk space for raw and processed data (~500MB)
- Sufficient RAM for model training (~6GB recommended)

## Installation

1. Clone the repository and navigate to the project root.
2. Create a virtual environment (optional but recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Execution Steps

The pipeline consists of four main stages. You can run them individually or use the
validation runner to execute them all in sequence.

### Option A: Run Individual Scripts

Execute the following commands in order from the project root:

1. **Download Data**
 ```bash
 python code/01_download.py
 ```
 *Outputs*: `data/raw/dataset_raw.parquet`

2. **Preprocess Data**
 ```bash
 python code/02_preprocess.py
 ```
 *Outputs*: `data/processed/dataset_cleaned.csv`, `split_config.json`

3. **Train Models**
 ```bash
 python code/03_train.py
 ```
 *Outputs*: `data/outputs/best_model.pkl`, `data/outputs/baseline_model.pkl`, `data/outputs/model_results.json`

4. **Evaluate Models**
 ```bash
 python code/04_evaluate.py
 ```
 *Outputs*: `data/outputs/feature_importance.json`, `data/outputs/variance_partition.csv`, `data/outputs/pdp_*.png`

### Option B: Run Full Validation (Recommended for T024)

To validate the entire pipeline in one go (as per T024 requirements):

```bash
python code/05_validate.py
```

This script:
- Executes all four stages sequentially.
- Validates outputs against the schemas defined in `specs/.../contracts/`.
- Logs success or failure with detailed error messages.

## Expected Artifacts

After a successful run, the following files should exist:

- `data/raw/dataset_raw.parquet`
- `data/processed/dataset_cleaned.csv`
- `split_config.json`
- `data/outputs/best_model.pkl`
- `data/outputs/baseline_model.pkl`
- `data/outputs/model_results.json`
- `data/outputs/feature_importance.json`
- `data/outputs/variance_partition.csv`
- `data/outputs/pdp_*.png` (Partial Dependence Plots)

## Troubleshooting

- **Missing Data**: If `01_download.py` fails, check your internet connection and ensure the HuggingFace dataset is accessible.
- **Schema Validation Errors**: If validation fails in `05_validate.py`, ensure the schema files in `specs/.../contracts/` match the actual output structure.
- **Memory Errors**: If training fails due to memory, check the `psutil` logs in `memory_monitor.py` and ensure your system meets the 6GB RAM requirement.

## Reproducibility

To ensure reproducibility:
- Use the same Python version (3.11).
- Pin dependencies in `requirements.txt`.
- Set the `random_seed` in `code/config.yaml` (default is 42).
- Run `python code/05_validate.py` to confirm the pipeline produces consistent results.
