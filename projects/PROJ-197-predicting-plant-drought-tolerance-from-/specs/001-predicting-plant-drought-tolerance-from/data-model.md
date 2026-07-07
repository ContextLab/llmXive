# Data Model: Predicting Plant Drought Tolerance

## 1. Entity-Relationship Overview

The project revolves around three core entities: `SpeciesRecord`, `ModelResult`, and `DataPipelineLog`.

### 1.1 SpeciesRecord
Represents a single plant species with merged physiological and **synthetic** genomic features.

| Attribute | Type | Description | Nullable |
| :--- | :--- | :--- | :--- |
| `species_id` | string | Unique species identifier (e.g., "Arabidopsis_thaliana") | No |
| `root_depth_cm` | float | Root system depth | Yes (Imputed) |
| `sla` | float | Specific Leaf Area | Yes (Imputed) |
| `synth_gene_01` | int (0/1) | **Synthetic** presence of gene 01 | No |
| `synth_gene_02` | int (0/1) | **Synthetic** presence of gene 02 | No |
| `drought_tolerance` | int (0/1) | **Synthetic** label (1: Tolerant, 0: Sensitive) | No |

*Note: Genomic features are synthetic placeholders generated for pipeline validation. They do not correspond to real ABA-signaling genes.*

### 1.2 ModelResult
Captures the outcome of a training run.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `model_type` | string | "RandomForest", "XGBoost", "KNN_Baseline" |
| `roc_auc` | float | Mean ROC-AUC score |
| `std_auc` | float | Standard deviation of AUC |
| `hyperparams` | dict | JSON string of hyperparameters used |
| `feature_importance` | list | List of (feature_name, score) tuples |

### 1.3 DataPipelineLog
Structured log of the ingestion process.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `timestamp` | string | ISO 8601 timestamp |
| `source_url` | string | URL of the dataset |
| `status` | string | "success", "partial", "failed" |
| `imputed_count` | int | Number of values imputed |
| `excluded_species` | list | List of species names excluded |

## 2. Data Flow

1.  **Download**: `download.py` fetches raw files (TRY) and generates synthetic genomic data.
2.  **Ingest**: `ingest.py` reads raw files, merges on `species_id`, applies standard MICE imputation, and saves `data/processed/merged.csv`.
3.  **Split**: `split.py` loads `merged.csv`, splits into `train.csv` and `test.csv`.
4.  **Train**: `train.py` loads `train.csv`, trains models, saves `data/processed/models/`.
5.  **Evaluate**: `evaluate.py` loads `test.csv` and models, computes metrics, saves `data/reports/metrics.json`.

## 3. Constraints

- **Imputation**: Missing values in continuous traits are imputed using standard MICE (not Phylogenetic MICE).
- **Genomic Features**: Binary (0/1), synthetic.
- **Phylogeny**: If a real tree is not available, a random distance matrix is generated for the KNN baseline.