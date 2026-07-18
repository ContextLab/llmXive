# Implementation Plan: Developing New Methods to Synthesize High-Performance Membranes using Sustainable Materials

**Branch**: `001-sustainable-membrane-synthesis` | **Date**: 2026-07-14 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-sustainable-membrane-synthesis/spec.md`

## Summary

This project addresses the research question: "Which structural features and material compositions of sustainable polymers determine permeability and selectivity performance comparable to conventional petrochemical-based membrane materials?" The approach involves aggregating sparse literature data, standardizing units (Barrer, LMH/bar), calculating molecular descriptors (RDKit), training a CPU-tractable Random Forest/Gradient Boosting regressor, and statistically validating the model's ability to discriminate between bio-candidates and petrochemical benchmarks. The entire pipeline is designed to execute within 6 hours on a 2-core CPU, 7GB RAM environment.

**Critical Scope Note**: Per FR-009, experimental validation of top candidates is a *future work* requirement. This computational phase identifies structural drivers and recommends candidates for future experimental validation; it does not perform the validation itself. The statistical test compares *predicted* performance distributions to assess model discrimination capability, not absolute material superiority (which requires the missing experimental ground truth).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `rdkit`, `scikit-learn`, `pandas`, `numpy`, `pyyaml`, `datasets` (HuggingFace)  
**Storage**: Local filesystem (`data/raw`, `data/processed`), CSV/Parquet  
**Testing**: `pytest` (unit, contract, integration)  
**Target Platform**: Linux (GitHub Actions c5.large equivalent)  
**Project Type**: Computational Chemistry / Data Science Pipeline  
**Performance Goals**: Full pipeline ≤ 6 hours; Model training ≤ 60 mins (with fallback reduction); Memory ≤ 7GB  
**Constraints**: No GPU; No large-LLM inference; Max tree depth: (fallback a higher value, then a lower value); Max ensemble size: sufficiently large to ensure statistical robustness.; Observational data framing (associational only).  
**Scale/Scope**: A sufficient number of valid literature records for training; A set of virtual candidates for screening.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`. `requirements.txt` pins exact versions. External datasets fetched from verified HuggingFace URLs only. |
| **II. Verified Accuracy** | PASS | **Action**: Phase 0 and Phase 4 include explicit execution of `validate_citations.py` script. Citations in `research.md` and `paper` will be validated against primary sources before artifact finalization. |
| **III. Data Hygiene** | PASS | Raw data preserved in `data/raw` with checksums. Transformations produce new files in `data/processed`. No in-place modification. |
| **IV. Single Source of Truth** | PASS | All figures/stats trace to specific rows in `data/processed` and blocks in `code/`. No hand-typed numbers in reports. |
| **V. Versioning Discipline** | PASS | Artifact hashes tracked in state YAML. Content hashes used to invalidate stale review records. |
| **VI. Computational Chemistry Integrity** | PASS | RDKit version pinned. Descriptors (VdW, H-bond) generated deterministically. RAM/CPU limits enforced in training scripts (max depth 10). |
| **VII. Statistical Validation Rigor** | PASS | Mann-Whitney U test used for *model discrimination* comparison. **Validation**: Phase 1 includes a check to ensure ≥10 known high-performance bio-membranes exist before reserving them for the test set. If <10 exist, the pipeline halts. |

## Project Structure

### Documentation (this feature)

```text
specs/001-sustainable-membrane-synthesis/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── polymer_record.schema.yaml
    ├── model_prediction.schema.yaml
    └── molecular_descriptor.schema.yaml
```

### Source Code (repository root)

```text
code/
├── ingestion/
│   ├── standardize_units.py
│   └── handle_missing_data.py
├── features/
│   ├── calculate_descriptors.py
│   └── feature_selection.py
├── modeling/
│   ├── train_model.py
│   └── cross_validate.py
├── screening/
│   ├── rank_candidates.py
│   └── statistical_test.py
├── utils/
│   ├── constants.py
│   └── logging_config.py
└── main_pipeline.py

data/
├── raw/
│   └── (downloaded datasets)
├── processed/
│   ├── standardized_polymers.csv
│   └── feature_matrix.csv
└── reports/
    ├── missing_data_report.json
    ├── clarification_flag.json
    └── power_analysis_report.json

tests/
├── unit/
├── integration/
└── contract/
```

**Structure Decision**: A modular pipeline structure (`ingestion`, `features`, `modeling`, `screening`) was selected to ensure separation of concerns, align with the functional requirements (FR-001 to FR-011), and facilitate unit testing of each stage (e.g., unit testing unit conversion separately from model training). This supports the "Reproducibility" and "Data Hygiene" principles by isolating transformation steps.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Multiple Imputation** | FR-006 requires handling missing critical variables (5-20%) without dropping records. | Simple mean imputation would bias the model and violate "Data Hygiene" by distorting variance. |
| **Fallback Tree Depth** | FR-003 mandates a 60-minute runtime target with a fallback to reduce depth. **Resolved**: Depth reduces to **6** first, then to **4** if still exceeded. | Fixed depth might exceed the 6-hour CI limit if the dataset is larger than expected, causing job failure. |
| **Mann-Whitney U Test** | Data is non-normal and observational; parametric t-tests would be invalid. | Parametric tests assume normality and equal variance, which is unlikely in sparse literature data. |
| **Feature Reduction (RFE)** | **New**: Small-N vs High-Dimensionality risk. | Training on all descriptors without reduction leads to severe overfitting and spurious R². RFE is mandatory. |
| **Predicted vs. Predicted Test** | **New**: Avoids comparing model predictions to experimental ground truth (circular). | Comparing predictions to experimental benchmarks conflates model error with material performance. |

## Implementation Phases

### Phase 0: Research & Feasibility (Output: `research.md`)
1. **Dataset Verification**: Confirm availability of ≥30 valid records (Structure + Performance) from manual literature extraction.
2. **Citation Validation**: Run `validate_citations.py` against all literature sources (Constitution Principle II).
3. **Feasibility Gate**: If <30 valid records found, halt with `data_insufficient_report.json`.

### Phase 1: Data Ingestion & Standardization (Output: `data/processed/standardized_polymers.csv`)
1. **Ingestion**: Parse literature data. Convert units to Barrer.
2. **Missing Data Handling**:
   - **>20% Missing Critical**: Halt with `ERR_DATA_INSUFFICIENT`.
   - **A Small but Critical Percentage of Missing Data**: Trigger imputation (polymer-class average) AND generate `clarification_flag.json` (FR-006, SC-005).
3. **Held-Out Set Validation**: Check if ≥10 known high-performance bio-membranes exist. If not, halt (Constitution Principle VII).
4. **Split**: Reserve a held-out test set of bio-membranes (if available).

### Phase 2: Feature Engineering & Model Training (Output: `artifacts/model.pkl`)
1. **Descriptor Calculation**: Compute RDKit descriptors (VdW, H-bonds, etc.).
2. **Feature Reduction (RFE)**: **Mandatory**. Use Recursive Feature Elimination to select a small, optimal subset of descriptors (target: a small set of features) to mitigate overfitting in the small-N regime.
3. **Training**: Train Random Forest (Max Depth tuned via hyperparameter optimization, n_estimators will be set to a value sufficient for model convergence and stability, following standard ensemble practices.).
   - **Fallback**: If runtime > 60 mins, reduce Max Depth to **6**. Retry.
   - **Fallback 2**: If still > 60 mins, reduce Max Depth to **4**. Retry.
4. **Validation**: Stratified k-fold CV

The research question remains: How does the proposed model generalize across different data distributions? The method involves employing stratified k-fold cross-validation to ensure representative sampling across folds. References include Smith et al. (2020) and arXiv:2103.00001.. Report R², MAE.

### Phase 3: Candidate Screening & Statistical Validation (Output: `data/reports/screening_results.json`)
1. **Virtual Library Generation**: Generate a diverse set of candidates from sustainable polymer classes (cellulose, chitosan, lignin) using SMILES templates.
2. **Prediction**: Predict performance for bio-candidates AND a control set of petrochemical benchmarks using the *same* model.
3. **Statistical Test**: Mann-Whitney U test comparing the *distribution of predicted bio-candidate performance* vs. *distribution of predicted petrochemical performance*.
   - **Purpose**: Assess model's ability to discriminate classes (not material superiority).
   - **Limitation**: Explicitly acknowledge that this test validates model discrimination, not absolute material superiority, due to lack of experimental ground truth for bio-candidates (FR-009).
4. **Power Analysis**: Calculate power for N=30 assuming a **large effect** (rank-biserial correlation = 0.5). Acknowledge low power for medium/small effects.

### Phase 4: Reporting & Future Work (Output: `data/reports/final_report.md`)
1. **Report Generation**: Compile results, feature importance, and statistical test outcomes.
2. **Citation Re-Validation**: Re-run `validate_citations.py` to ensure all references in the report are valid.
3. **Candidate Recommendation**: Output `candidate_recommendation_report.md` listing top 3 candidates for *future* experimental validation (FR-009). Explicitly state that experimental validation is a future work requirement not performed in this phase.

## FR/SC Coverage Matrix

| ID | Requirement/Success Criterion | Plan Element Addressing It |
| :--- | :--- | :--- |
| **FR-001** | Aggregate multiple sources, standardize units. | Phase 1: Ingestion & Unit Conversion. |
| **FR-002** | Generate molecular descriptors | Phase 2: Descriptor Calculation (RDKit). |
| **FR-003** | Train ensemble, max depth 10, fallback | Phase 2: Training with Fallback (Depth 6 → 4). |
| **FR-004** | 5-fold CV, R² ≥ 0.1 | Phase 2: Validation Step. |
| **FR-005** | Mann-Whitney U test | Phase 3: Statistical Test (Predicted vs. Predicted). |
| **FR-006** | Missing data handling, halt >20% | Phase 1: Missing Data Logic. |
| **FR-007** | Frame as associational | Research Context & Report Disclaimer. |
| **FR-008** | Encode synthesis method | Phase 2: Categorical Encoding. |
| **FR-009** | Experimental validation of top 3 | **Future Work**: Output `candidate_recommendation_report.md`. |
| **FR-010** | Power analysis report | Phase 3: Power Analysis Step. |
| **FR-011** | Dimensionality reduction (PCA/RFE) | Phase 2: RFE Step (Mandatory). |
| **SC-001** | R² ≥ 0.1 | Phase 2: Validation Metric. |
| **SC-002** | + candidates screened | Phase 3: Virtual Library Generation. |
| **SC-003** | p-value < 0.05 | Phase 3: Statistical Test Output. |
| **SC-004** | Runtime ≤ 6h | Phase 2: Fallback Logic. |
| **SC-005** | Missing variable flag >5% | Phase 1: `clarification_flag.json` generation. |
