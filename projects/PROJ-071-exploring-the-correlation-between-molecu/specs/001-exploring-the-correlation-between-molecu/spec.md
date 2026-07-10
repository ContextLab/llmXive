# Specification: Molecular Complexity vs Degradation

## User Stories
- **US1**: Ingest FDA-approved structures, verify degradation data, calculate complexity metrics.
- **US2**: Standardize degradation units, perform correlation and regression analysis with cross-validation.
- **US3**: Generate diagnostic plots and a reproducibility report.

## Requirements
- **FR-001**: Fetch data from HuggingFace dataset `Synthyra/FDA-Approved-Drugs`.
- **FR-002**: Calculate TPSA, Rotatable Bond Count, MW, Aromatic Ring Count, Wiener Index, Zagreb Index.
- **FR-003**: Enforce Data Availability Gate (N >= 30).
- **FR-004**: Perform Multiple Linear Regression with optional covariates (pH, Temp).
- **FR-005**: Implement LASSO regression with K-fold cross-validation.
- **FR-006**: Generate residual diagnostics (Shapiro-Wilk, Breusch-Pagan).
- **FR-007**: Log reproducibility metadata (versions, hashes).
