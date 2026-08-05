# Cross-Modal Comparison of Neural Prediction Error Signals

## Project Overview

This project implements an automated pipeline for comparing neural prediction error signals across auditory and visual modalities using EEG data from OpenNeuro datasets.

## Data Integrity and Source Policy

**CRITICAL POLICY: REAL DATA ONLY**

This project strictly adheres to the following data integrity principles:

1. **Mandatory Real Data Sources**: All analysis data MUST originate from verified OpenNeuro datasets:
 - **Auditory Modality**: OpenNeuro dataset `ds000246`
 - **Visual Modality**: OpenNeuro dataset `ds000117` (via Hugging Face Hub mirror)

2. **Prohibition of Synthetic Data**:
 - **NO synthetic data generation** is permitted at any stage of the pipeline.
 - **NO placeholder or mock datasets** are allowed.
 - **NO fallback to simulated values** if real data fetch fails.
 - Any attempt to substitute real measurements with generated values constitutes a violation of the project's core scientific integrity.

3. **Failure Protocol**:
 - If a real data source is unreachable or fails validation, the pipeline must **fail loudly** (raise an explicit error) and halt execution.
 - Silent fallbacks to synthetic data are strictly forbidden and will be rejected by the execution verification stage.

4. **Data Verification**:
 - All downloaded datasets are validated for sampling rate (≥500 Hz) [UNRESOLVED-CLAIM: c_a17308bf — status=not_enough_info] and trial counts (≥100 oddball, ≥300 standard) immediately upon fetch.
 - Data integrity is further verified via checksums recorded in `data/manifest.json`.

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd llmXive-cross-modal-comparison
 ```

2. **Create and activate a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Configure environment** (optional):
 - Create a `.env` file in the project root if custom paths or API keys are needed.
 - Refer to `code/config.py` for default configuration values.

## Usage

Run the full pipeline:
```bash
python code/main.py
```

This will:
1. Download and validate datasets from OpenNeuro.
2. Preprocess the data (filtering, ICA, re-referencing).
3. Extract prediction error signals (difference waves, peak latency, amplitude).
4. Perform source localization and statistical comparisons.
5. Generate a final report in `data/results/final_report.md`.

## Project Structure

```
.
├── code/
│ ├── data/ # Data loading, download, preprocessing
│ ├── analysis/ # Signal extraction, source localization, stats
│ ├── validation/ # Reliability checks
│ ├── utils/ # Logging, utilities
│ ├── config.py # Project configuration
│ └── main.py # Orchestration script
├── data/
│ ├── raw/ # Downloaded raw datasets
│ ├── processed/ # Cleaned data artifacts
│ └── results/ # Analysis outputs and reports
├── docs/
│ └── README.md # This file
├── tests/ # Unit and integration tests
├── requirements.txt # Dependencies
└── venv/ # Virtual environment (gitignored)
```

## License

This project is intended for research purposes.
