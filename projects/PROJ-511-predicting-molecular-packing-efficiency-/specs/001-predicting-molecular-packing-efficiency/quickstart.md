# Quickstart: Predicting Molecular Packing Efficiency

## Prerequisites
*   Python 3.11+
*   `pip`
*   Access to the verified COD datasets (no credentials required).

## Installation

1.  **Clone and Setup**:
    ```bash
    cd projects/PROJ-511-predicting-molecular-packing-efficiency-
    python -m venv venv
    source venv/bin/activate
    pip install -r code/requirements.txt
    ```

2.  **Verify Dependencies**:
    Ensure `rdkit`, `torch`, and `transformers` are installed and importable.

## Running the Pipeline

The pipeline is executed in three main stages.

### Step 1: Data Acquisition & Feature Engineering
Download COD data, generate SMILES, compute 3D descriptors, encode SMILES, and save the full feature matrix.
```bash
python code/download_cod.py --output data/processed/raw_cod.jsonl
python code/generate_smiles.py --input data/processed/raw_cod.jsonl --output data/processed/with_smiles.csv
python code/compute_descriptors.py --input data/processed/with_smiles.csv --output data/processed/with_descriptors.csv
python code/encode_smiles.py --input data/processed/with_descriptors.csv --output data/processed/full_feature_matrix.csv
```

### Step 2: Model Training
Train the 2-layer MLP on the feature matrix to predict **PC_raw**.
```bash
python code/train_model.py --data data/processed/full_feature_matrix.csv --output data/artifacts/model.pt
```

### Step 3: Evaluation & Reporting
Run validation, permutation tests, sensitivity analysis, and generate the HTML report.
```bash
python code/evaluate_model.py --model data/artifacts/model.pt --data data/processed/full_feature_matrix.csv --output data/artifacts/validation_report.json
python code/sensitivity_analysis.py --model data/artifacts/model.pt --data data/processed/full_feature_matrix.csv --output data/artifacts/sensitivity_results.json
python code/report_generator.py --report data/artifacts/report.html
```

## Verification
*   Check `data/artifacts/validation_report.json` for `pearson_r >= 0.4` and `bonferroni_corrected_p <= 0.05`.
*   Check `data/processed/full_feature_matrix.csv` for ≥ 500 rows.
*   Run `pytest tests/` to ensure unit tests pass.
*   Check `data/source_log.json` to verify the dataset source and version.

## Troubleshooting
*   **OOM Error**: If the transformer inference fails, reduce the batch size in `code/encode_smiles.py` or enable the GPU escape hatch (automatic).
*   **Missing SMILES**: If many records are flagged as "generated", ensure `rdkit` is correctly parsing the CIF 3D coordinates.
*   **No Data**: If the dataset has < 500 records, check the filter criteria in `download_cod.py` (e.g., atom count limit).
*   **Timeout**: If the permutation test times out, check `validation_report.json` for the `actual_shuffles` field and the deviation log.
