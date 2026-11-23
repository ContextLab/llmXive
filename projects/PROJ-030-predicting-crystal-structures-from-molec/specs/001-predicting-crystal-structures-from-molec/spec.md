# Specification: Predicting Crystal Structures from Molecular Fingerprints

## User Stories

### US1: Data Ingestion and Feature Extraction
- Ingest COD organic subset.
- Parse CIFs to extract SMILES and lattice parameters.
- Generate ECFP4 fingerprints.
- Handle polymorphism by treating (SMILES, Space Group) as distinct samples.
- Output: `data/processed/crystal_dataset.csv`

### US2: Model Training and Validation
- Train Random Forest, Gradient Boosting, and Ridge Regression models.
- Use scaffold-based splits to prevent data leakage.
- Handle class imbalance.
- Enforce time limits (max 6 hours).
- Compare against baselines (Molecular Weight, Majority Class).
- Verify success criteria (SC-001: Lift over majority baseline).
- Output: `data/results/model_metrics.json`

### US3: Feature Importance and Interpretability
- Compute permutation importance and SHAP values.
- Map top predictive bits to chemical substructures.
- Flag bits with multiple mappings (collisions).
- Output: `data/results/feature_importance_report.md`

## Success Criteria
- SC-001: Model accuracy > Majority Baseline + [deferred] lift.
- SC-002: Zero scaffold overlap between train/test.
- SC-003: Feature importance report contains >= 20 annotated bits, sorted.
- SC-004: Full pipeline execution <= 6 hours.
- SC-005: Rare space groups (<20 samples) grouped into 'Other'.
