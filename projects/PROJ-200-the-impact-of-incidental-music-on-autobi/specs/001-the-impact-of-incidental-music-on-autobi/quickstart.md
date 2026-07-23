# Quickstart: The Impact of Incidental Music on Autobiographical Memory Retrieval

## Prerequisites

- Python 3.11+
- `git`
- Access to the project repository

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd projects/PROJ-200-the-impact-of-incidental-music-on-autobi
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

 *Note: `requirements.txt` pins exact versions to ensure reproducibility (Constitution Principle I).*

## Running the Pipeline

The pipeline is executed in sequential stages. Each stage produces intermediate artifacts.

### Step 1: Data Download & Ingestion
```bash
python code/01_download_data.py
```
- Downloads the simulated datasets (mock MSD/AMT) to `data/raw/`.
- Computes checksums and records them in `state.yaml`.

### Step 2: Preprocessing & Matching
```bash
python code/02_preprocess.py
```
- Cleans data, handles missing values.
- Performs Levenshtein matching for cue-text to track-name.
- Filters low-confidence matches (logs warnings if match rate < 80% per SC-004).
- Outputs: `data/processed/ingested_cohort.parquet`.

### Step 3: Aggregation & Exposure Calculation
```bash
python code/03_aggregate.py
python code/04_exposure.py
```
- Aggregates data to User-Track Pair level.
- Calculates `adolescent_exposure_ratio` (FR-001).
- Checks for missing birth years (>50%) and triggers exclusion logic (FR-008, EC-001).
- Filters by `total_listens` >= 3 (FR-009).
- Outputs: `data/processed/user_track_pairs.parquet`.

### Step 4: Modeling & Sensitivity Analysis
```bash
python code/05_model.py
python code/06_sensitivity.py
```
- Fits LMM for each Levenshtein threshold (1-5). **Aggregation is re-run for each threshold.**
- Checks VIF (EC-003).
- Performs parametric bootstrap (replaces block-permutation).
- Outputs: `data/final/regression_summary.csv`, `data/final/bootstrap_results.csv`, `data/final/sensitivity_analysis.csv`.

### Step 5: Selection Bias Correction
```bash
python code/07_selection_correction.py
```
- Applies Heckman correction to account for non-random cue selection.
- Outputs: `data/final/selection_correction.csv`.

### Step 6: Visualization
```bash
python code/08_visualize.py
```
- Generates diagnostic plots (residuals, QQ plots).
- Outputs: `data/final/plots/`.

## Validation

Run the test suite to verify the pipeline logic:
```bash
pytest tests/
```
- **Unit Tests**: Verify exposure calculation, fallback logic, and VIF checks.
- **Integration Tests**: Run the full pipeline on a small mock dataset to ensure end-to-end flow.

## Troubleshooting

- **Missing Birth Years**: If users are excluded, check `data/processed/user_track_pairs.parquet` for the `is_excluded_from_primary` flag.
- **Low Match Rate**: If the warning is logged, review `data/processed/ingested_cohort.parquet` for the distribution of Levenshtein scores.
- **Multicollinearity**: If VIF > 5, review `data/final/regression_summary.csv` and consider removing the correlated predictor.
