# Predicting Plant Stress Resilience from Publicly Available Metabolomic Data

This project implements a mechanism-guided pipeline to predict plant stress resilience using metabolomic data. It supports both synthetic data generation (for development and validation) and ingestion of real-world datasets from public repositories.

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd projects/PROJ-455-predicting-plant-stress-resilience
 ```

2. **Create a virtual environment** (Python 3.11 recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Data Generation (Synthetic)

For development and testing, synthetic metabolomic data with embedded ground-truth pathways can be generated using the `code/data/generator.py` module.

**Generate a single synthetic dataset**:
```bash
python -c "from data.generator import generate_synthetic_data; generate_synthetic_data(n_samples=1000, stress_type='drought')"
```
This will create a Parquet file in `data/raw/synthetic_*.parquet`.

**Generate LODO (Leave-One-Dataset-Out) synthetic datasets**:
```bash
python -c "from data.generator import generate_lodo_synthetic_datasets; generate_lodo_synthetic_datasets(n_datasets=5, stress_types=['drought', 'salt', 'heat'])"
```
This creates multiple distinct Parquet files in `data/raw/` simulating external datasets for cross-validation.

## Execution Command

The full pipeline can be executed to ingest data, preprocess, train models, and validate results.

**Run the full pipeline** (uses synthetic data by default if no real data is configured):
```bash
python -m code.analysis.pipeline
```

**Run specific stages**:
- **Ingest & Preprocess**:
 ```bash
 python -c "from data.ingest import get_adapter; from data.preprocess import normalize_recovery, normalize_tic_and_log; adapter = get_adapter('mock'); df = adapter.fetch(); df = normalize_tic_and_log(df)"
 ```
- **Train Models**:
 ```bash
 python -c "from models.train import train_random_forest, get_top_features; model, metrics = train_random_forest(X, y); print(get_top_features(model, n=20))"
 ```
- **Validate (LODO & Cross-Stress)**:
 ```bash
 python -c "from models.validate import lodo_cv, cross_stress_eval; scores = lodo_cv(models, datasets)"
 ```

## Expected Output

Upon successful execution, the pipeline produces the following artifacts:

1. **Processed Data**:
 - `data/processed/normalized_profiles.parquet`: Cleaned and normalized metabolomic profiles.
 - `data/processed/recovery_indices.csv`: Mapped recovery metrics (0-1 scale).

2. **Model Artifacts**:
 - `data/results/model_rf.pkl`: Trained Random Forest model.
 - `data/results/model_svm.pkl`: Trained SVM model.
 - `data/results/metrics.json`: Performance metrics (R², Pearson r) and feature importance rankings.

3. **Validation Reports**:
 - `data/results/lodo_scores.json`: Leave-One-Dataset-Out cross-validation scores.
 - `data/results/pathway_enrichment.json`: KEGG pathway alignment and enrichment p-values.

4. **Logs**:
 - `logs/pipeline.log`: Detailed execution logs including data rejection reasons and training progress.

**Success Criteria**:
- No `DataRejectionError` for missing thresholds >10%.
- Model R² or Pearson r > 0.5 on held-out test sets.
- Pathway enrichment p-value < 0.05 or Jaccard similarity ≥ 0.3.
- Execution time < 6 hours (as per `tests/benchmark/test_pipeline_timing.py`).