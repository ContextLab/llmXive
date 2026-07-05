# Quick Start Guide: Early Life Stress & Hippocampal Subfield Volumes

## Project Overview

This project investigates the impact of early-life stress (ACE scores) on hippocampal subfield volumes (CA3, DG, Subiculum) using data from the **ABCD Study Release 4.0**.

**Key Objectives:**
- Acquire and preprocess ABCD phenotypic and MRI subcortical segmentation data.
- Normalize hippocampal volumes by Intracranial Volume (ICV).
- Fit Linear Mixed-Effects Models (LMM) to assess associations while controlling for age, sex, site, and family clustering.
- Perform robustness checks via cluster-level permutation tests and sensitivity analyses.

**Important Note:** All reported findings are **associational** only. Causality cannot be inferred from this observational study.

## Data Requirements

This pipeline requires access to the **ABCD Study Release 4.0** data.

### Required Files
The pipeline expects the following files to be present in `data/raw/` after acquisition:
1. **Phenotypic Data**: `abcd_pheno_release4.tsv` (contains ACE scores, demographics, MRI quality flags).
2. **Subcortical Segmentation Stats**: `subcorticalSegmentationStats_release4.tsv` (contains CA3, DG, Subiculum, and ICV volumes).

### Data Acquisition
If you have not yet downloaded the data, run the acquisition script:
```bash
python code/main.py --task acquisition
```
*Note: You must have valid ABCD Study credentials and have completed the necessary data use agreements before running this step.*

## Installation & Setup

1. **Clone the repository** and navigate to the project directory:
 ```bash
 cd projects/PROJ-160-investigating-the-impact-of-early-life-s
 ```

2. **Create a virtual environment** and install dependencies:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 pip install -r requirements.txt
 ```

3. **Verify directory structure**:
 Ensure the following directories exist:
 - `code/`
 - `data/raw/`
 - `data/processed/`
 - `tests/`
 - `specs/001-gene-regulation/`

## Running the Pipeline

The entire analysis pipeline can be executed via the main entry point:

```bash
python code/main.py
```

This will sequentially run:
1. **Data Loading & Preprocessing**: Filters for quality, normalizes volumes, handles outliers.
2. **Statistical Modeling**: Fits LMMs for CA3, DG, Subiculum, and CA3:DG ratio.
3. **Robustness Validation**: Runs permutation tests and sensitivity analyses.

### Output Files

Upon successful completion, the following artifacts will be generated in `data/processed/`:
- `cleaned_dataset.csv`: Preprocessed data with normalized volumes.
- `model_results.json`: Detailed model coefficients, CIs, and p-values.
- `model_results_summary.csv`: Human-readable summary of associations.
- `sensitivity_report.csv`: Counts of significant findings across alpha thresholds.
- `robustness_report.json`: Aggregated metrics from permutation and sensitivity tests.

## Testing

Run the full test suite to verify integrity:

```bash
pytest tests/ -v
```

## Configuration

Edit `code/config.py` to adjust:
- Random seeds for reproducibility.
- Path definitions (if not using defaults).
- Alpha thresholds for sensitivity analysis (default: 0.01, 0.05, 0.1).

## Troubleshooting

- **Missing Data Files**: Ensure `data/raw/` contains the required ABCD TSV files.
- **Import Errors**: Verify the virtual environment is activated and `requirements.txt` is installed.
- **Memory Issues**: The pipeline is optimized for CPU-only execution; if out-of-memory errors occur, reduce `n_jobs` in `code/config_env.py`.