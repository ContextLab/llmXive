# The Influence of Visual Salience on Attentional Bias in Moral Judgements

## Project Overview

This project implements an automated research pipeline to investigate how visual salience influences attentional bias in moral judgement tasks. The pipeline ingests stimulus images, generates deep salience maps using DeepGaze II (with GBVS fallback), extracts eye-tracking metrics for "Face" ROIs, aligns datasets, and performs Linear Mixed Model (LMM) analysis.

**Key Scope Decisions (Governance):**
- **FR-008 (Weapons) Excluded:** Per SCR-001, "Weapons" ROIs are excluded due to lack of COCO class support. Analysis is limited to "Face" vs "Background".
- **FR-009 (Low-Level Covariates) Excluded:** Per SCR-002, explicit low-level covariate modeling is excluded to prevent multicollinearity with DeepGaze II features. VIF checks are performed for verification.
- **Correlational Only:** All results are marked with a "correlational only" disclaimer (FR-007) as per study design.

## Project Structure

```text
.
├── code/ # Python source code
│ ├── analysis/ # Statistical modeling & robustness
│ ├── ingestion/ # Data download & salience generation
│ ├── processing/ # Eye-tracking & segmentation
│ ├── scr/ # Spec Change Request governance scripts
│ ├── utils/ # Logging, versioning, validation
│ ├── config.py # Project configuration
│ └── data_models.py # Data structures
├── data/
│ ├── raw/ # Downloaded raw dataset
│ ├── interim/ # Intermediate processing artifacts
│ └── processed/ # Final aligned datasets & results
├── tests/ # Unit and integration tests
├── docs/ # Documentation & SCR reports
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Prerequisites

- Python 3.11+
- Hugging Face Token (`HF_TOKEN`)
- GPU (optional, CPU fallback available for salience generation)
- ~14GB disk space for dataset and artifacts

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-name>
 ```

2. Create a virtual environment and install dependencies:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```

3. Configure environment variables:
 ```bash
 cp.env.example.env
 # Edit.env to add your HF_TOKEN, DATA_PATH, SEED, and GPU_DEVICE
 ```

## Usage

### 1. Data Ingestion (User Story 1)

Download the dataset and generate salience maps:
```bash
python code/ingestion/download_data.py
python code/ingestion/salience_gen.py
```
*Note: Salience generation enforces <7GB RAM limit and CPU-only mode by default.*

### 2. Attention Metric Extraction (User Story 2)

Process eye-tracking data and generate face masks:
```bash
python code/processing/segmentation.py
python code/processing/eye_tracking.py
python code/processing/alignment.py
```

### 3. Statistical Analysis (User Story 3)

Perform power analysis, VIF checks, and LMM fitting:
```bash
python code/analysis/lmm_power.py
python code/analysis/vif_calc.py
python code/analysis/lmm_fit.py
python code/analysis/robustness.py
```

## Output Artifacts

- `data/processed/salience_maps/metadata.json`: List of processed images and map paths.
- `data/processed/aligned_metrics.csv`: Merged salience and fixation data.
- `data/processed/results.json`: Final LMM results with p-values and disclaimers.
- `data/interim/vif_report.txt`: Variance Inflation Factor interpretation.

## Governance & Compliance

- **SCR-001:** Documents the exclusion of "Weapons" (FR-008). See `docs/scr_001_weapons_exclusion.md`.
- **SCR-002:** Documents the exclusion of low-level covariates (FR-009). See `docs/scr_002_lowlevel_covariates_exclusion.md`.
- **Power Gate:** If statistical power < 0.8, the pipeline halts (see `data/interim/invalid_for_inference_flag.json`).
- **Correlational Disclaimer:** All significant findings are explicitly labeled as correlational.

## License

[Insert License Here]
