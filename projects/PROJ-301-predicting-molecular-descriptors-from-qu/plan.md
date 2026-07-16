# Project Plan: Predicting Molecular Descriptors from Quantum Chemical Calculations with Machine Learning

## Overview

This project implements a machine learning pipeline to predict molecular descriptors (dipole moment, HOMO, LUMO) from quantum chemical calculations using the QM9 dataset. The pipeline is designed to be memory-safe, reproducible, and statistically rigorous.

## Objectives

1. Download and validate the QM9 dataset from HuggingFace.
2. Extract 2D and 3D molecular features.
3. Train Random Forest models with cross-validation.
4. Perform comparative analysis and identify failure boundaries.
5. Generate comprehensive reports and visualizations.

## Scope

**In Scope**:
- Data acquisition from HuggingFace (lisn/QM9)
- Feature extraction (Morgan fingerprints, 3D graph features)
- Model training (Random Forest with GridSearchCV)
- Statistical analysis (Wilcoxon signed-rank test)
- Failure boundary identification
- Pipeline validation and testing

**Out of Scope**:
- Deep learning models
- Other molecular datasets
- Real-time prediction services
- Web interface

## User Stories

### US1: Data Acquisition and Feature Extraction

**As a** researcher,
**I want** to download the QM9 dataset and extract 2D/3D features,
**So that** I can use them for model training.

**Acceptance Criteria**:
- Dataset downloaded from HuggingFace (lisn/QM9)
- Data integrity validated (required DFT columns, valid geometry)
- 2D Morgan fingerprints generated (radius=2, nBits=2048)
- 3D graph features extracted (atomic number, hybridization, distances, angles)
- Memory usage monitored and downsampling applied if ≥ 6.5 GB
- Output files: `features_2d.npy`, `features_3d.npy`, `labels.csv`

### US2: Model Training and Cross-Validation

**As a** data scientist,
**I want** to train Random Forest models with 5-fold cross-validation,
**So that** I can evaluate model performance and select hyperparameters.

**Acceptance Criteria**:
- Hyperparameter grid search: `n_estimators` ∈ {100, 500, 1000}, `max_depth` ∈ {10, 20, None}
- 5-fold cross-validation for both 2D and 3D models
- Models saved to `artifacts/models/`
- CV metrics (MAE, RMSE, std) recorded
- Stability ratio calculated (std_mae / mean_mae)
- Runtime monitored (graceful failure if > 6 hours)
- Output files: `model_2d.pkl`, `model_3d.pkl`, `cv_metrics.json`, `stability_report.json`

### US3: Comparative Analysis and Failure Boundary Identification

**As a** researcher,
**I want** to compare model performance and identify failure boundaries,
**So that** I can understand model limitations and improve predictions.

**Acceptance Criteria**:
- Mean predictor baseline calculated
- Per-molecule errors computed for both models
- Wilcoxon signed-rank test with Bonferroni correction (α = 0.0167)
- Failure boundary defined (REI ≥ 10% OR p < 0.0167)
- Parity plots generated
- Final report compiled
- Output files: `baseline_error.json`, `test_predictions.json`, `statistics.json`, `failure_boundary.json`, `parity_*.png`, `report.md`

## Technical Architecture

### Components

1. **Data Pipeline** (`code/01_data_download.py`, `code/02_feature_extraction.py`)
 - Downloads QM9 from HuggingFace
 - Parses and validates molecular structures
 - Extracts 2D/3D features
 - Monitors memory and applies downsampling

2. **Model Training** (`code/03_model_training.py`)
 - Loads features and labels
 - Performs grid search with cross-validation
 - Trains and saves models
 - Aggregates CV metrics
 - Monitors runtime

3. **Analysis** (`code/04_analysis.py`)
 - Computes baseline errors
 - Generates predictions
 - Performs statistical tests
 - Identifies failure boundaries
 - Creates visualizations
 - Generates final report

4. **Utilities** (`code/utils/`)
 - `logger.py`: Logging infrastructure
 - `memory_monitor.py`: Memory tracking and downsampling
 - `models.py`: Data model classes
 - `parsers.py`: SMILES and XYZ parsing

5. **Validation** (`code/05_quickstart_validator.py`)
 - Validates all artifacts exist and are correct
 - Runs end-to-end checks

### Data Flow

```
HuggingFace (QM9)
 ↓
data/raw/qm9_full.parquet
 ↓
data/processed/molecules_cleaned.parquet
 ↓
data/processed/features_*.npy, labels.csv
 ↓
artifacts/models/model_*.pkl
 ↓
artifacts/metrics/*.json
 ↓
artifacts/plots/*.png
 ↓
artifacts/report.md
```

## Dependencies

### Python Packages

- `rdkit`: Molecular structure handling
- `scikit-learn`: Machine learning models and metrics
- `pandas`: Data manipulation
- `numpy`: Numerical operations
- `pyarrow`: Parquet file I/O
- `tqdm`: Progress bars
- `huggingface_hub`: Dataset download
- `matplotlib`, `seaborn`: Visualization
- `scipy`: Statistical tests

### System Requirements

- Python 3.11+
- 8+ GB RAM (14 GB recommended for full dataset)
- 14+ GB free disk space

## Spec Amendments & Overrides

### T009.1 Amendment: Data Source Update

**Original Specification (FR-001)**: Use QM9 dataset from standard source.

**Amendment**: Update FR-001 to explicitly use the HuggingFace dataset `lisn/QM9` as the primary and verified source.

**Rationale**:
- Ensures reproducibility and consistency across runs.
- HuggingFace provides a programmatic interface with integrity checks.
- Aligns with modern data access patterns.

**Implementation**:
- `code/01_data_download.py` uses `datasets.load_dataset("lisn/QM9")`
- All data validation checks the presence of required DFT columns.
- Checksums are computed for downloaded files.

**Verification**:
- Task T009 explicitly records this amendment in this document.
- Execution logs confirm download from `lisn/QM9`.

### T023 Amendment: Statistical Significance Threshold

**Original Specification**: Use standard α = 0.05 for statistical tests.

**Amendment**: Apply Bonferroni correction for multiple comparisons (3 descriptors), resulting in α = 0.05 / 3 ≈ 0.0167.

**Rationale**:
- Controls family-wise error rate when testing multiple descriptors.
- Increases statistical power for meaningful comparisons.

**Implementation**:
- `code/04_analysis.py` uses `alpha = 0.0167` for significance testing.
- `artifacts/metrics/statistics.json` reports corrected p-values.

## Risk Management

### Risks

1. **Memory Exceedance**
 - **Mitigation**: Memory monitor with automatic downsampling at 6.5 GB.
 - **Fallback**: Stratified random sampling to reduce dataset size.

2. **Download Failures**
 - **Mitigation**: Retry logic and integrity checks.
 - **Fallback**: Manual download with checksum verification.

3. **Runtime Timeout**
 - **Mitigation**: Runtime monitoring with 6-hour limit.
 - **Fallback**: Graceful failure with partial results saved.

4. **Model Instability**
 - **Mitigation**: Stability ratio monitoring.
 - **Fallback**: Warning logged, pipeline continues for analysis.

### Contingency Plans

- If memory limit cannot be met even with downsampling, reduce dataset size further and document the limitation.
- If HuggingFace is unavailable, use alternative verified mirror (documented in logs).
- If statistical tests fail to converge, report results with appropriate caveats.

## Success Metrics

1. **Data Pipeline**: Successfully downloads and processes QM9 dataset.
2. **Feature Extraction**: Generates valid 2D and 3D feature matrices.
3. **Model Training**: Completes 5-fold CV within 6 hours.
4. **Statistical Analysis**: Identifies significant differences between models.
5. **Failure Boundaries**: Correctly identifies molecules where 3D model underperforms.
6. **Documentation**: All artifacts and reports generated correctly.

## Timeline

### Phase 1: Setup (Week 1)
- Project structure initialization
- Dependency installation
- Tool configuration (linting, formatting)

### Phase 2: Foundational (Week 1-2)
- Utility module implementation
- Data model definition
- Memory monitoring setup
- Spec amendment documentation

### Phase 3: User Story 1 (Week 2-3)
- Data download and validation
- Feature extraction
- Memory safety verification

### Phase 4: User Story 2 (Week 3-4)
- Model training implementation
- Cross-validation
- Runtime monitoring

### Phase 5: User Story 3 (Week 4-5)
- Comparative analysis
- Statistical testing
- Visualization and reporting

### Phase 6: Polish (Week 5-6)
- Documentation updates
- Code cleanup
- Testing and validation
- End-to-end verification

## Deliverables

1. **Code**: Complete pipeline implementation in `code/`
2. **Data**: Processed datasets in `data/`
3. **Models**: Trained models in `artifacts/models/`
4. **Metrics**: Performance metrics in `artifacts/metrics/`
5. **Plots**: Visualizations in `artifacts/plots/`
6. **Reports**: Final report in `artifacts/report.md`
7. **Documentation**: README, quickstart, data-model docs in `docs/`
8. **Tests**: Unit and integration tests in `tests/`

## Maintenance

- Regular updates to dependencies
- Periodic re-validation against new QM9 releases
- Monitoring of HuggingFace dataset availability
- Documentation updates as features evolve

## Glossary

- **QM9**: Quantum Machine 9 dataset, a collection of 134k small organic molecules.
- **DFT**: Density Functional Theory, quantum chemical method used for reference values.
- **Morgan Fingerprint**: Circular molecular fingerprint (ECFP).
- **HOMO**: Highest Occupied Molecular Orbital.
- **LUMO**: Lowest Unoccupied Molecular Orbital.
- **REI**: Relative Error Increase.
- **CV**: Cross-Validation.
- **MAE**: Mean Absolute Error.
- **RMSE**: Root Mean Squared Error.