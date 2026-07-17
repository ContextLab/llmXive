# Quickstart: The Influence of Typographic Salience on Moral Judgments

## Prerequisites
-   Python 3.11+
-   `pip`
-   (Optional) Docker for isolated execution.

## Setup

### 1. Clone and Install
```bash
cd projects/PROJ-507-the-influence-of-visual-salience-on-mora
pip install -r code/requirements.txt
```

### 2. Data Preparation
The pipeline expects data in `data/raw/`.
-   **Option A (Real Data)**: Download `Dahoas/rm-single-context` using `datasets.load_dataset("Dahoas/rm-single-context")` and save the raw JSON/Parquet files to `data/raw/`.
-   **Option B (No Synthetic Data)**: Do not use synthetic data. The study relies on real data from the verified dataset.

### 3. Run the Pipeline
Execute the scripts in order:
```bash
# 1. Ingest and Filter
python code/01_data_ingestion.py

# 2. Ambiguity Filtering (using reward scores)
python code/03_ambiguity_filter.py

# 3. Stimulus Manipulation (Typographic)
python code/02_stimulus_manipulation.py

# 4. Survey Data Simulation (or load real CSV)
python code/04_survey_deployment.py --simulate  # Generates dummy responses for testing

# 5. Data Cleaning
python code/05_data_cleaning.py

# 6. Statistical Analysis
python code/06_statistical_analysis.py
```

### 4. Verify Results
Check `data/processed/analysis_results.json` for:
-   LMM fixed effects (Salience).
-   Bonferroni-corrected p-values.
-   Effect sizes (Partial Eta-Squared).
-   **Note**: All values must be derived from the actual dataset. No placeholder values are accepted.

## Troubleshooting
-   **Sentence-BERT Timeout**: If inference is too slow, reduce the number of stimuli or use a smaller model.
-   **Data Missing**: Ensure `data/raw/` contains the downloaded `Dahoas` dataset files.
-   **LMM Convergence**: If the model fails to converge, check for perfect separation or insufficient data (try `--robust` flag for bootstrap).