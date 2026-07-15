# Specification Summary: Predicting Coating Adhesion Strength

## Project Goal

To develop a robust, statistically validated machine learning pipeline that predicts coating adhesion strength from material composition and surface metrology features, adhering to strict scientific reproducibility and data quality standards.

## Key Requirements

1. **Data Integrity**:
 - Use only real, verified data sources (Materials Project, NIST).
 - Enforce strict identifier-based linking; reject heuristic mapping.
 - Halt execution if data sources are inaccessible or invalid.

2. **Safety Gates**:
 - **Power Analysis**: Ensure N ≥ 1,000.
 - **Exclusion Ratio**: < 10% missing target data.
 - **Success Rate**: ≥ 95% processing success.
 - **Construct Validity**: Derived features must correlate significantly with the target.

3. **Modeling Rigor**:
 - Use nested cross-validation to prevent data leakage.
 - Compare full-feature models against composition-only and surface-only baselines.
 - Apply Nadeau & Bengio corrected t-tests with Bonferroni correction.

4. **Performance**:
 - Target runtime < 4 hours.
 - CPU-only execution (no GPU dependencies).

## User Stories

- **US1 (P1)**: Dataset Curation and Alignment. Ingest, clean, and align data into a single validated CSV.
- **US2 (P2)**: Predictive Modeling and Feature Importance. Train models, compute SHAP values, and rank features.
- **US3 (P3)**: Statistical Comparison and Baseline Benchmarking. Compare models against baselines using corrected t-tests.

## Implementation Phases

- **Phase 0**: Data Gap Analysis (Critical Blocker).
- **Phase 1**: Setup (Directory structure, dependencies).
- **Phase 2**: Foundational (Safety gates, validation logic).
- **Phase 3**: User Story 1 (Data Ingestion & Alignment).
- **Phase 4**: User Story 2 (Modeling & SHAP).
- **Phase 5**: User Story 3 (Statistical Evaluation).
- **Phase N**: Polish & Cross-Cutting Concerns (Documentation, CI, Security).

## Success Criteria

- Pipeline runs end-to-end on real data.
- All safety gates pass (Power, Exclusion, Success Rate).
- Models produce statistically significant improvements over baselines (or correctly flag "Informative Null").
- Documentation is complete and accurate.
- Runtime is under 4 hours.