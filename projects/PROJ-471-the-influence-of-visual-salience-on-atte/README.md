# The Influence of Visual Salience on Attentional Bias in Moral Judgements

**Project ID**: PROJ-471
**Status**: Research Pipeline Implementation

## Overview

This project implements an automated scientific pipeline to investigate how visual salience influences attentional bias in moral judgment tasks. The pipeline ingests OpenNeuro eye-tracking data, generates salience maps using DeepGaze II (with GBVS fallback), extracts fixation metrics for "Face" regions, and performs statistical modeling (LMM) with robustness verification.

## Key Features

- **Data Ingestion**: Streams real datasets from Hugging Face/OpenNeuro.
- **Salience Generation**: CPU-optimized DeepGaze II with automatic GBVS fallback for high-contrast images.
- **ROI Segmentation**: YOLOv8-based face detection (Weapons excluded per SCR-001).
- **Statistical Analysis**: Linear Mixed Models (LMM) with FDR correction and power analysis.
- **Governance**: Formal Spec Change Requests (SCRs) applied to scope (e.g., exclusion of FR-008, FR-009).

## Prerequisites

- Python 3.11+
- Git
- Hugging Face Token (for dataset access)
- 7GB+ RAM (for streaming datasets)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repo-url>
 cd PROJ-471-the-influence-of-visual-salience-on-atte
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Configure environment**:
 - Copy `.env.example` to `.env`.
 - Fill in `HF_TOKEN` (Hugging Face API token) and other required keys.
 ```bash
 cp.env.example.env
 # Edit.env with your credentials
 ```

## Quickstart

Run the pipeline stages sequentially. Each stage produces artifacts in `data/`.

```bash
# 1. Ingest Data & Generate Salience Maps
python code/ingestion/download_data.py
python code/ingestion/salience_gen.py

# 2. Process Eye Tracking & Alignment
python code/processing/segmentation.py
python code/processing/eye_tracking.py
python code/processing/alignment.py

# 3. Statistical Analysis
python code/analysis/lmm_power.py
python code/analysis/vif_calc.py
python code/analysis/lmm_fit.py
python code/analysis/robustness.py
python code/analysis/write_final_results.py
```

## Project Structure

```
.
├── code/ # Source code
│ ├── ingestion/ # Data download & salience generation
│ ├── processing/ # Eye-tracking parsing & alignment
│ ├── analysis/ # Statistical modeling & robustness
│ ├── utils/ # Logging, versioning, config
│ └── config.py # Global configuration
├── data/
│ ├── raw/ # Downloaded datasets
│ ├── interim/ # Intermediate processing results
│ └── processed/ # Final aligned metrics & results
├── tests/ # Unit and integration tests
├── docs/ # Documentation & SCRs
├── requirements.txt # Python dependencies
├── README.md # This file
└──.env.example # Environment variable template
```

## Governance & Scope

This project adheres to strict governance protocols. The following Spec Change Requests (SCRs) have been applied:

- **SCR-001**: Exclusion of "Weapons" (FR-008) from ROI analysis due to lack of COCO class support. Only "Face" ROIs are processed.
- **SCR-002**: Exclusion of low-level covariates (FR-009) to prevent multicollinearity with DeepGaze II salience maps.
- **SCR-003**: Implementation of GBVS as a CPU-compatible fallback for DeepGaze II failures on high-contrast images.

## Validation

Run the integration test suite to verify pipeline integrity:

```bash
python tests/integration/test_pipeline.py
```

Run the quickstart validation to ensure all artifacts are present:

```bash
python code/validation/run_quickstart_validation.py
```

## License

Research use only. See LICENSE for details.
