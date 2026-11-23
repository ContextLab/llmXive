# Quickstart Guide: Predicting Molecular Packing Efficiency

## Overview
This guide provides step-by-step instructions to run the full pipeline for predicting
molecular packing efficiency in crystals from SMILES representations.

## Prerequisites
- Python 3.9+
- pip and virtual environment
- Required packages (install via `pip install -r requirements.txt`)

## Installation

1. Clone the repository and navigate to the project directory:
 ```bash
 cd projects/PROJ-511-predicting-molecular-packing-efficiency-
 ```

2. Create and activate a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

The pipeline consists of several sequential steps. You can run them individually or
use the main pipeline script.

### Option 1: Run Individual Steps

Follow this order to execute each step:

1. **Setup Project Structure**
 ```bash
 python code/setup.py
 ```

2. **Download CIF Files**
 ```bash
 python code/download_cif.py
 ```

3. **Parse CIF Files**
 ```bash
 python code/parse_cif.py
 ```

4. **Compute Raw Metrics**
 ```bash
 python code/compute_RAW_metrics.py
 ```

5. **Filter Dataset**
 ```bash
 python code/filter_dataset.py
 ```

6. **Add 3D Descriptors** (NEW - T018)
 ```bash
 python code/add_3d_descriptors.py
 ```

7. **Validate Dataset**
 ```bash
 python code/validate_dataset.py
 ```

8. **Feature Assembly**
 ```bash
 python code/feature_assembly.py
 ```

9. **Train Model**
 ```bash
 python code/train.py
 ```

10. **Evaluate Model**
 ```bash
 python code/evaluate.py
 ```

11. **Generate Report**
 ```bash
 python code/generate_report.py
 ```

### Option 2: Run Full Pipeline

Execute the entire pipeline with a single command:
```bash
python code/run_pipeline.py
```

## Output Files

After successful execution, the following files will be generated:

- `data/dataset_intermediate.csv` - Intermediate dataset after parsing
- `data/dataset_with_metrics.csv` - Dataset with computed metrics
- `data/dataset_filtered.csv` - Filtered dataset
- `data/dataset.csv` - Final dataset with 3D descriptors (T018 output)
- `data/features_matrix.npy` - Feature matrix for model training
- `data/targets.npy` - Target values for model training
- `models/mlp.pt` - Trained model
- `results/validation_report.json` - Model validation metrics
- `results/report.html` - Human-readable report

## Verification

To verify the pipeline ran successfully:

1. Check that all output files exist:
 ```bash
 ls -la data/*.csv data/*.npy models/*.pt results/*.json results/*.html
 ```

2. Validate dataset schema:
 ```bash
 python code/validate_dataset.py
 ```

3. Check model performance:
 ```bash
 cat results/validation_report.json
 ```

## Troubleshooting

- **Missing dependencies**: Ensure all packages in `requirements.txt` are installed
- **CIF parsing errors**: Check that CIF files are valid and contain required metadata
- **Memory issues**: Reduce batch sizes or process data in chunks
- **Network issues**: If downloading CIF files fails, check your internet connection

## Next Steps

After completing the pipeline:
1. Review the generated report in `results/report.html`
2. Analyze the validation metrics in `results/validation_report.json`
3. Consider running sensitivity analysis with `python code/sensitivity.py`