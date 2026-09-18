# Research Methodology: Predicting Battery Electrolyte Decomposition Products via DFT and Machine Learning

## Overview

This document describes the methodology, data sources, and key deviations from the original specification for the project **PROJ-085-predicting-battery-electrolyte-decomposi**.

## Data Sources

### Primary Dataset

The project attempts to ingest pre-computed DFT structures from the HuggingFace dataset:

**Dataset ID**: `materialsproject/mp-dft-electrolytes`

This dataset is intended to provide DFT-computed properties for battery electrolyte molecules including:
- HOMO/LUMO energies
- Band gaps
- Geometric features (bond lengths, angles, dihedrals)
- Reactant and product energies for decomposition reactions

**Note**: If the primary dataset is unavailable or does not contain the specific electrolyte entries (EC, DMC, LiPF6), the pipeline will attempt to use a fallback mechanism. However, **no synthetic data fabrication is permitted** - if real data cannot be obtained, the pipeline must fail loudly to indicate the data gap.

### Alternative Sources

The project may reference additional datasets for validation or distribution shape checking, but these are **not** used as primary training data:
- General HOMO/LUMO datasets (for distribution validation only)
- NOMAD repository entries (if specific electrolyte data is found)

## Methodology

### 1. Data Ingestion and Filtering

The ingestion pipeline (`code/data/ingestion.py`) performs:
- Fetching DFT data from HuggingFace or local cache
- Filtering for target electrolyte species (EC, DMC, LiPF6)
- Deduplication based on molecule ID and potential
- Validation against schema contracts

### 2. Descriptor Extraction

The descriptor pipeline (`code/data/descriptors.py`) extracts:
- **Electronic descriptors**: HOMO, LUMO, band gap
- **Geometric descriptors**: Bond lengths, bond angles, dihedral angles
- **Thermodynamic features**: Reactant/product energies from DFT calculations

Metallic outliers (zero/negative band gap) are flagged and excluded.

### 3. Target Calculation

Decomposition energy ($E_{decomp}$) is calculated using:

$$E_{decomp} = E_{products} - E_{reactants} - nF\phi$$

Where:
- $E_{products}$: Sum of product energies
- $E_{reactants}$: Sum of reactant energies
- $n$: Number of electrons transferred
- $F$: Faraday constant
- $\phi$: Applied potential (0V, 2V, or 4V)

The stoichiometry heuristic in `code/utils/reactions.yaml` selects the correct reaction entry based on molecule ID and potential.

### 4. Feature Engineering and Binning

Data is split into:
- **Low potential bin**: 0-2V range
- **High potential bin**: 4V (mapped from spec's 3-5V range)

**Deviation Note**: The spec's requirement for a 3-5V range is approximated by the single 4V data point due to dataset constraints. This is a known limitation.

### 5. Model Training

A Random Forest Regressor is trained with:
- 5-fold cross-validation
- Hyperparameter tuning via GridSearchCV
- Separate models for low and high potential bins

### 6. Feature Importance Analysis

Permutation importance is calculated for each bin to identify:
- Top features driving decomposition energy predictions
- Features that emerge in high-potential conditions but are absent in low-potential conditions

**Key Analysis (T024)**: Identify descriptors entering the top-3 in high-potential (4V) but absent from low-potential (0-2V). This analysis is implemented in `code/models/feature_shift_analyzer.py`.

### 7. Validation

**Internal Validation**: Predictions are validated against held-out DFT data (internal consistency check).

**External Validation (FR-006)**: **UNFULFILLED** - No experimental decomposition onset potential dataset is available. Internal DFT validation is used as a fallback.

## Deviations from Specification

### 1. Data Availability (FR-001, FR-006)

**Issue**: The verified datasets block does not contain specific battery electrolyte data (EC, DMC, LiPF6) with the required DFT descriptors.

**Impact**:
- Training data must come from available real sources or the pipeline fails
- External validation (FR-006) cannot be performed due to lack of experimental onset potential data

**Mitigation**:
- Internal DFT validation is used as a fallback
- Spec amendment (T038) formally removes FR-006 and SC-003 requirements
- Warning flags are added to reports (T034)

### 2. Potential Range Mapping (T024, T022)

**Issue**: The spec requires analysis of 3-5V range, but available data only includes 0V, 2V, and 4V points.

**Deviation**: All references to "high potential (3-5V)" are explicitly mapped to the 4V data point. This is documented as a known limitation in:
- `code/models/feature_shift_analyzer.py`
- `code/models/trainer.py`
- All generated reports

### 3. Circular Target Definition

**Issue**: The target variable ($E_{decomp}$) is constructed from features ($E_{products}$, $E_{reactants}$) using a deterministic formula.

**Impact**: Standard correlation metrics may show near-perfect correlation by mathematical definition rather than physical discovery.

**Mitigation**:
- Partial correlation analysis (FR-010) is implemented to detect feature leakage
- Features with partial correlation > 0.9 are flagged/rejected
- Validation focuses on generalization to held-out DFT data rather than experimental data

### 4. Synthetic Data Policy

**Policy**: **NO SYNTHETIC DATA FABRICATION**

The pipeline must:
- Load real data from verified sources (HuggingFace, NOMAD)
- Fail loudly if real data is unavailable
- Never fall back to synthetic/mock data generation
- Never hard-code fake sample rows

This policy ensures scientific validity and reproducibility.

## Key Artifacts

### Code
- `code/data/ingestion.py`: Data fetching and filtering
- `code/data/descriptors.py`: Feature extraction
- `code/data/target_calc.py`: Decomposition energy calculation
- `code/models/trainer.py`: Model training
- `code/models/evaluator.py`: Model evaluation
- `code/models/feature_shift_analyzer.py`: Feature shift detection (T024)

### Data
- `data/processed/electrolyte_features.csv`: Processed feature matrix
- `data/processed/electrolyte_heldout.csv`: Held-out validation set
- `data/processed/bins.csv`: Bin assignments (Low/High)
- `data/processed/model_run.json`: Model artifacts and feature importances
- `data/validation/feature_shift_analysis.json`: Feature shift analysis report (T024)

### Reports
- `data/validation/sensitivity_report.md`: Sensitivity analysis results
- `docs/research.md`: This methodology document

## Reproducibility

To reproduce the analysis:
1. Ensure all dependencies are installed (`requirements.txt`)
2. Run the ingestion pipeline to fetch real data
3. Execute the descriptor extraction pipeline
4. Run model training and evaluation
5. Generate feature shift analysis (T024)

All random seeds are controlled via `code/config.py`.

## References

- Specification: `specs/001-battery-electrolyte-decomposition/spec.md`
- Plan: `plan.md`
- Data Model: `data-model.md`
- Task T024: Feature shift analysis implementation
- Task T038: Spec amendment for FR-006/SC-003 removal