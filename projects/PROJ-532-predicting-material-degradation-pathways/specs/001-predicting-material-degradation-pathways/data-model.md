# Data Model: Predicting Material Degradation Pathways from Compositional Data

## Entities

### AlloyRecord
Represents a single material sample in the dataset.
- **id**: `string` (Unique identifier, e.g., Zenodo record ID)
- **material_class**: `string` (e.g., "Stainless Steel", "High-Entropy Alloy")
- **composition**: `map<string, float>` (Elemental weight percentages, e.g., `{"Fe": 70.5, "Cr": 18.0, "Ni": 11.5}`)
- **derived_properties**: `map<string, float>` (Calculated: `electronegativity`, `atomic_radius` - **not** used for training)
- **degradation_labels**: `list<string>` (Multi-label: e.g., `["pitting", "scc"]`)
- **source_metadata**: `map<string, any>` (Source study, temperature, pH if available)

### FeatureVector
The input to the Random Forest model.
- **features**: `list<float>` (Flattened elemental weight percentages, sorted alphabetically by element)
- **target**: `list<int>` (Binary vector for multi-label classification, e.g., `[1, 0, 1, ...]`)

### ReferenceImportanceVector
The ground truth vector derived from literature for validation.
- **element_rankings**: `map<string, float>` (Rank score: -1.0 to 1.0, where 1.0 is protective, -1.0 is detrimental)
- **source_papers**: `list<string>` (Citations of the 5 review papers)
- **methodology**: `string` (Description of extraction method)

## Data Flow

1.  **Raw Ingestion**: `data/raw/*.csv` (Zenodo source) → `code/ingestion.py`
2.  **Cleaning**: Filtered/Imputed records → `data/processed/cleaned_alloys.csv`
3.  **Feature Engineering**: `data/processed/features.parquet` (Primary features + derived properties)
4.  **Splitting**: `data/processed/train_set.parquet`, `data/processed/test_ood_set.parquet` (Class-based split)
5.  **Literature**: `code/literature_review.py` → `data/contracts/literature_vector.json`
6.  **Training**: `code/training.py` → `results/model_artifact.pkl`
7.  **Evaluation**: `code/evaluation.py` → `results/metrics/performance_report.json`, `results/plots/confusion_matrix.png`
8.  **Explainability**: `code/explainability.py` → `results/plots/shap_summary.png`, `results/metrics/sensitivity_analysis.json`

## Schema Definitions

See `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` for formal definitions.
