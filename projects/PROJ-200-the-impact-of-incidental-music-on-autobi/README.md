# The Impact of Incidental Music on Autobiographical Memory Retrieval

**Project ID**: PROJ-200-the-impact-of-incidental-music-on-autobi

## Overview

This project investigates the relationship between incidental music exposure during adolescence and the vividness/valence of autobiographical memories retrieved with those musical cues. We utilize the Million Song Dataset (MSD) for exposure metrics and the Autobiographical Memory Test (AMT) dataset for memory retrieval data.

## Key Updates & Specification Alignment

This implementation adheres to the updated specification (Phase 2.5) which resolves contradictions between the original plan and requirements:

- **Unit of Analysis**: The primary unit of analysis is the **User-Track Pair**, not the individual memory instance.
- **Primary Predictor**: `residualized_exposure_score` is used, calculated by regressing `adolescent_exposure_score` on `overall_popularity_score` and extracting residuals.
- **Model Formula**: `mean_vividness ~ residualized_exposure + popularity + (1|user_id)`.
- **Permutation Test**: A **block-permutation** is performed on User-Track Pair rows, shuffling exposure scores while preserving the User-Track grouping structure.
- **Aggregation**: All metrics are aggregated per User-Track Pair.
- **Match Rate Handling**: The pipeline logs a warning if the match rate is < 80% but proceeds (SC-004).
- **Edge Cases**: The fallback check for missing birth years (>50%) is performed **before** applying the Minimum Listen Threshold filter.

## Architecture

The pipeline is organized into the following phases:

1. **Data Ingestion (US1)**: Downloads MSD and AMT data, filters for valid birth years, and computes exposure scores.
2. **Cue Matching & Aggregation (US2)**: Matches AMT cues to MSD tracks using fuzzy string matching (Levenshtein ≤ 4) and aggregates memory attributes to User-Track pairs.
3. **Statistical Modeling (US3)**: Fits linear mixed-effects models, runs sensitivity analysis, and performs block-permutation tests.

## Directory Structure

```text
.
├── code/ # Python implementation modules
│ ├── __init__.py
│ ├── config.py # Configuration and paths
│ ├── data_ingestion.py # Data loading and exposure calculation
│ ├── cue_matching.py # Fuzzy matching and normalization
│ ├── aggregation.py # Aggregation to User-Track pairs
│ ├── modeling.py # Statistical modeling and tests
│ ├── utils.py # Logging and utilities
│ ├── main.py # Pipeline orchestration
│ └──... (generator scripts)
├── data/
│ ├── raw/ # Raw downloaded datasets
│ ├── processed/ # Intermediate processed data (parquet)
│ └── final/ # Final analysis results and plots
├── tests/ # Unit and integration tests
├── contracts/ # Data schemas
├── state.yaml # Checksum tracking
├── requirements.txt # Dependencies
└── README.md
```

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-200-the-impact-of-incidental-music-on-autobi
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

 **Required Dependencies**:
 - `pandas`
 - `numpy`
 - `scikit-learn`
 - `statsmodels`
 - `python-Levenshtein`
 - `pyyaml`
 - `tqdm`
 - `scipy`
 - `matplotlib`
 - `seaborn`
 - `pyarrow`

## Usage

### Running the Full Pipeline

The main entry point orchestrates the entire flow from ingestion to final results.

```bash
python code/main.py
```

This will:
1. Download and verify datasets (if not present).
2. Process and filter the cohort.
3. Match cues and aggregate to User-Track pairs.
4. Fit mixed-effects models and run sensitivity/permutation tests.
5. Generate diagnostic plots and final summaries.

### Running Specific Stages

You can also run individual stages using the generator scripts in `code/`:

- **Ingestion**: `python code/generate_ingested_cohort.py`
- **User-Track Pairs**: `python code/generate_user_track_pairs.py`
- **Regression Summary**: `python code/generate_regression_summary.py`
- **Final Results**: `python code/generate_final_results.py`
- **Diagnostic Plots**: `python code/generate_diagnostic_plots.py`

### Validation

To ensure the pipeline runs correctly and outputs are valid:

```bash
python code/quickstart_validator.py
```

## Data Sources

- **Million Song Dataset (MSD)**: Used for track metadata and listen counts.
- **Autobiographical Memory Test (AMT)**: Used for memory cues and vividness/valence ratings.

*Note: The pipeline will attempt to download these datasets automatically. Ensure you have an internet connection and sufficient disk space (approx. 5GB+ for raw data).*

## Configuration

Configuration is managed via `code/config.py`. Key parameters include:
- `LEVENSHEIT_THRESHOLD`: Maximum distance for cue matching (default: 4).
- `MIN_LISTEN_THRESHOLD`: Minimum listens required for a track (default: 10).
- `BIRTH_YEAR_FALLBACK_THRESHOLD`: Percentage of missing birth years to trigger global exposure (default: 0.50).

## Testing

Run the test suite using `pytest`:

```bash
pytest tests/ -v
```

Tests are organized by user story:
- `tests/unit/test_ingestion.py`: US1 logic.
- `tests/unit/test_matching.py`: US2 logic.
- `tests/unit/test_modeling.py`: US3 logic.
- `tests/integration/test_pipeline.py`: End-to-end validation.

## License

This project is for research purposes.
