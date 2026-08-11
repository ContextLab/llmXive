# PROJ-756: Assessing Dataset Imbalance Effects on Materials Property Predictions

**Objective**: Quantify how dataset imbalance (skewed target distributions and compositional diversity) affects the predictive performance and feature importance of machine learning models in materials science.

This project implements a full pipeline to:
1. Ingest real materials data from OQMD, AFLOW, and Materials Project APIs.
2. Compute Magpie compositional descriptors.
3. Quantify imbalance scores (Target Gini, Compositional Gini via K-Means).
4. Train baseline models on skewed data.
5. Apply resampling (stratified binning, cost-sensitive, SMOTE fallback) to balance data.
6. Compare model performance and SHAP feature importance rankings.

## Directory Layout

The project follows a strict structure under `projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/`:

```text
.
├── code/ # Python source modules
│ ├── main.py # CLI entry point
│ ├── ingestion.py # API ingestion with backoff & logging
│ ├── downloaders.py # Data fetching & checksums
│ ├── descriptors.py # Magpie descriptor computation
│ ├── imbalance.py # Imbalance score calculation
│ ├── training.py # Model training (RF, GB)
│ ├── evaluation.py # Model evaluation & statistical tests
│ ├── resampling.py # Resampling strategies & SMOTE fallback
│ ├── shap_analysis.py # SHAP value computation & validation
│ ├── correlation_analysis.py
│ └──... (other utility modules)
├── data/
│ ├── raw/ # Downloaded raw parquet files (OQMD, AFLOW, MP)
│ ├── processed/ # Computed descriptors and feature matrices
│ └── synthetic/ # Synthetic ground truth for SHAP validation
├── results/
│ ├── baseline_report.csv
│ ├── performance_degradation.csv
│ ├── statistical_test_results.csv
│ ├── correlation_analysis.csv
│ ├── shap_analysis/ # SHAP values, rank shifts, plots
│ └──... (other analysis outputs)
├── tests/ # Unit, contract, and integration tests
├── state/ # Pipeline state tracking (YAML)
├── logs/ # API error logs and execution traces
├── artifacts/ # Generated artifacts (schemas, etc.)
├── contracts/ # Schema definitions for validation
├── requirements.txt # Python dependencies
└── README.md
```

## Prerequisites

- **Python**: 3.11 or higher
- **System**: `pip`, `git`
- **API Keys** (Optional but recommended for full data coverage):
 - **Materials Project**: Set `MP_API_KEY` environment variable.
 - **OQMD/AFLOW**: Public access via REST API (no key required, but rate limits apply).

## Installation

1. **Clone and Navigate**:
 ```bash
 git clone <repository-url>
 cd projects/PROJ-756-assessing-dataset-imbalance-effects-on-m
 ```

2. **Create Virtual Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install Dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

## Quick Start

### 1. Full Pipeline Execution (Recommended)

Runs the entire workflow: ingestion → descriptors → imbalance analysis → baseline training → resampling → evaluation → SHAP analysis.

```bash
python code/main.py --full-pipeline --streaming
```

* `--full-pipeline`: Executes all stages sequentially.
* `--streaming`: Processes large datasets in chunks to stay within memory limits (~7GB RAM).
* `--include-mp`: Attempts to fetch Materials Project data (requires `MP_API_KEY`).

**Output**:
- `results/baseline_report.csv`
- `results/performance_degradation.csv`
- `results/shap_analysis/rank_shift.csv`
- `results/statistical_test_results.csv`

### 2. Fallback Mode (MP Unavailable)

If the Materials Project API is unreachable or the key is missing, run in fallback mode to process OQMD and AFLOW only.

```bash
python code/main.py --full-pipeline --fallback-mode --streaming
```

### 3. Individual Stage Execution

You can run specific stages independently if data artifacts already exist.

**Ingest Data**:
```bash
python code/ingestion.py
```

**Compute Descriptors**:
```bash
python code/descriptors.py
```

**Calculate Imbalance Scores**:
```bash
python code/imbalance.py
```

**Train Baseline Models**:
```bash
python code/training.py --mode baseline
```

**Run Resampling & Evaluation**:
```bash
python code/resampling.py && python code/evaluation.py
```

**SHAP Analysis**:
```bash
python code/shap_analysis.py
```

## Configuration

- **Logging**: All API errors are logged to `logs/api_errors.log` in JSON Lines format.
- **State**: Pipeline progress and artifact hashes are tracked in `state/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m.yaml`.
- **Data Integrity**: The system enforces "Fail Loudly" on data fetch errors. No synthetic fallback data is generated unless explicitly triggered by the SMOTE fallback logic (capped at 30%).

## Verification

To ensure no synthetic data fabrication occurred in data loaders:

```bash
python code/verify_no_synthetic_fallback.py
```

To validate the full pipeline execution time (must be ≤ 6 hours):

```bash
python code/verify_streaming_strategy.py
```

## Contributing

When adding new tasks:
1. Update `tasks.md` with the new task ID and dependencies.
2. Implement the code in `code/`.
3. Write corresponding tests in `tests/`.
4. Ensure all artifacts are written to `data/`, `results/`, or `figures/`.

## License

[Insert License Here]