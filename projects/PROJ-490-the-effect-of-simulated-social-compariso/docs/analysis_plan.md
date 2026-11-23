# Analysis Plan: The Effect of Simulated Social Comparison on Self-Esteem in Virtual Reality

## Project Overview
**Project ID**: PROJ-490
**Title**: The Effect of Simulated Social Comparison on Self-Esteem in Virtual Reality
**Status**: Analysis Pipeline Complete

## Research Question
Does simulated social comparison in virtual reality environments significantly impact self-esteem, and how does this effect vary based on individual comparison tendencies?

## Methodology

### Data Sources
- **Primary Source**: Real-world datasets containing RSES (Rosenberg Self-Esteem Scale), INCOM (Integrative Negotiation Comparison Measure), and pre/post self-esteem scores
- **Fallback**: Synthetic data generator with ground-truth parameters (N ≥ 100, interaction β = 0.2) when real data is unavailable or lacks IRB/consent verification
- **Data Validation**: All datasets validated against schema contracts in `contracts/dataset.schema.yaml`

### Statistical Approach

#### 1. Preprocessing (FR-002, FR-013)
- Missing data handling using MICE (Multiple Imputation by Chained Equations) via `miceforest`
- Fallback to `sklearn.impute.IterativeImputer` if `miceforest` unavailable
- Exclusion of rows with > 20% missingness
- Variable normalization (avatar_condition to binary 0/1)
- **Note**: Change scores NOT calculated; ANCOVA uses pre_self_esteem as covariate

#### 2. Primary Analysis: ANCOVA Regression (FR-004)
- **Outcome**: post_self_esteem
- **Covariate**: pre_self_esteem
- **Predictors**:
 - avatar_condition (binary)
 - comparison_tendency (continuous)
 - interaction term: avatar_condition × comparison_tendency

#### 3. Model Assumption Validation
- **Normality**: Shapiro-Wilk test on residuals
- **Homoscedasticity**: Breusch-Pagan test
- **Collinearity**: Variance Inflation Factor (VIF) analysis
 - Flag if VIF ≥ 5
 - Apply descriptive framing without claiming independent effects (FR-004, SC-003)

#### 4. Robustness Analysis (FR-005, FR-006, FR-007)
- **Bootstrap Resampling**:
 - Sufficient iterations to estimate interaction effect stability
 - Confidence interval width variance calculation (flag if variance ≥ 0.01)
- **Sensitivity Analysis**:
 - Parameter recovery for synthetic data (|β̂ - β_true|)
 - Threshold sensitivity sweeps across p-value levels
 - Imputation limit sensitivity {low, moderate, high, very high}
- **Family-wise Error Correction**: Bonferroni/Holm correction applied to:
 - Sensitivity sweep tests
 - Model assumption tests (Shapiro, Breusch-Pagan, VIF)

### Interpretation Framework (FR-010)
- **Real Data**: "Empirical Association" - correlational findings
- **Synthetic Data**: "Simulated Causal Effect" - parameter recovery validation

## Output Artifacts

### Data Pipeline
- `data/raw/`: Downloaded CSVs or synthetic data with checksums in `state/projects/PROJ-490-the-effect-of-simulated-social-compariso.yaml`
- `data/processed/`: Preprocessed datasets after imputation

### Analysis Results
- `data/processed/regression_coefficients.csv`:
 - Columns: coefficient, std_error, t_statistic, p_value, ci_lower, ci_upper
- `data/processed/model_diagnostics.json`:
 - Shapiro-Wilk p-value
 - Breusch-Pagan p-value
 - VIF values for all predictors
 - Collinearity flags
 - Bootstrap stability metrics
- `data/processed/final_report.json`:
 - Data path used
 - Model results (coefficients, diagnostics)
 - Bootstrap stability analysis
 - Parameter recovery (if synthetic)
 - Sensitivity findings
 - Interpretation label

## Implementation Status

### Completed Tasks
- **Phase 1**: Project setup and structure (T001)
- **Phase 2**: Schema contracts, validation utilities, logging, configuration (T002-T005)
- **Phase 3**: Data discovery, synthetic generation, validation, and loading (T006-T013)
- **Phase 4**: Preprocessing, ANCOVA regression, assumption validation, interpretation, export (T014-T022)
- **Phase 5**: Bootstrap resampling, sensitivity analysis, family-wise error correction, final report (T023-T030)
- **Phase 6**: Documentation updates (T031)

### Code Structure
```
code/
├── analysis/
│ ├── bootstrap.py # Bootstrap resampling and CI calculation
│ ├── collinearity_handler.py # VIF calculation and descriptive framing
│ ├── export_results.py # CSV/JSON export functions
│ ├── interpretation.py # Dynamic interpretation labeling
│ ├── regression.py # ANCOVA and assumption validation
│ ├── report_generator.py # Final report generation
│ ├── run_full_pipeline.py # Pipeline orchestration
│ └── sensitivity.py # Sensitivity analysis and error correction
├── data/
│ ├── config.py # Configuration management
│ ├── download.py # Data discovery and synthetic generation
│ ├── loader.py # Data loading and hashing
│ ├── preprocess.py # Missing data handling and normalization
│ └── validate_raw.py # Variable validation
└── utils/
 ├── logger.py # Logging infrastructure
 └── validators.py # Schema validation utilities
```

## Reproducibility
- All random operations seeded via `config.py`
- Reproducibility verified by running `main.py` twice with fixed seeds and comparing output hashes (T034)
- All artifacts checksummed and recorded in state file

## Limitations and Considerations
- Synthetic data used only when real data unavailable or lacks proper consent verification
- VIF ≥ 5 triggers descriptive framing without causal claims
- Bootstrap CI width variance ≥ 0.01 flagged as stability concern
- Family-wise error correction applied to multiple testing scenarios

## Next Steps
- Continuous integration testing with pytest (T033)
- Code quality enforcement with flake8 and black (T032a, T032b)
- Documentation maintenance and update as pipeline evolves

---
*Last Updated: Analysis pipeline fully implemented and documented*