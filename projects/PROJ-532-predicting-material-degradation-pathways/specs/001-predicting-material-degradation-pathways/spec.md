# Feature Specification

## User Stories

### US1: Data Ingestion and Preprocessing
As a researcher, I want to ingest raw corrosion data and encode it into feature vectors so that I can train a model.
- Acceptance Criteria:
 - Filter non-metallics
 - Handle missing values
 - Generate OOD split

### US2: Model Training
As a researcher, I want to train a Random Forest model on CPU so that I can predict degradation pathways.
- Acceptance Criteria:
 - CPU-only execution
 - Macro-F1 score > baseline
 - Permutation test p < 0.05

### US3: Explainability
As a researcher, I want to validate feature importance against literature so that I can trust the model.
- Acceptance Criteria:
 - SHAP analysis
 - Spearman correlation > 0.6
 - Literature vector comparison
