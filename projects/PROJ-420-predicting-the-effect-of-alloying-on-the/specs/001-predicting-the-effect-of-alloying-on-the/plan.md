# Implementation Plan: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

**Branch**: `001-predict-poissons-ratio` | **Date**: 2026-07-05 | **Spec**: `specs/001-predict-poissons-ratio/spec.md`
**Input**: Feature specification from `/specs/001-predict-poissons-ratio/spec.md`

## Summary

This project implements a computational pipeline to predict the Poisson's ratio of monolithic aluminum alloys based on the atomic fractions of major alloying elements (Cu, Mg, Si, Zn, Mn). The approach involves extracting data from Materials Project and NIST repositories, filtering for completeness, unit consistency, and **independent measurement validity**, applying Isometric Log-Ratio (ILR) transformation to handle compositional constraints, and training a Random Forest regressor. The pipeline prioritizes reproducibility, data hygiene, and the explicit framing of all findings as associational rather than causal, adhering to the project constitution.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `numpy`, `requests`, `pyyaml`, `joblib`, `statsmodels` (for VIF), `compositional` (for ILR), `pytest`  
**Storage**: Local file system (`data/raw`, `data/processed`, `code/`, `state/`)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7 GB RAM)  
**Project Type**: Data Science / Computational Materials Science  
**Performance Goals**: Complete data extraction, cleaning, modeling, and reporting within 6 hours on CPU-only infrastructure.  
**Constraints**: No GPU/CUDA; dataset size < 1000 entries; memory usage < 7 GB; strict adherence to compositional data analysis (CoDA) principles.  
**Scale/Scope**: Single outcome prediction (Poisson's ratio) for a specific subset of aluminum alloys.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Random seeds will be pinned in `code/`. Data sources will be fetched via deterministic scripts. `requirements.txt` will pin versions. The `compositional` package is used for ILR to ensure standard implementation. |
| **II. Verified Accuracy** | **At Risk (Blocking)** | **Critical**: If the "Verified datasets" block does not contain a verified URL for Materials Project or NIST specific to Al alloys with Poisson's ratio, the pipeline **must halt** with a clear error. The plan cannot proceed without verified sources. Compliance is conditional on the existence of these URLs in the verified block. |
| **III. Data Hygiene** | **Compliant** | Raw data will be stored in `data/raw` with checksums. Derived data in `data/processed` will be new files. No in-place modification. PII scan passed (N/A for materials data). |
| **IV. Single Source of Truth** | **Compliant** | All figures/stats in the final report will be generated programmatically from `data/processed` and `code/`. |
| **V. Versioning Discipline** | **Compliant** | Content hashes will be recorded in `state/projects/PROJ-420-predicting-the-effect-of-alloying-on-the.yaml` under the `artifact_hashes` key. A `state_update.py` script will manage this. |
| **VI. Unit Consistency** | **Compliant** | Elastic constants will be normalized to GPa before feature engineering. |
| **VII. Compositional Attribution** | **Compliant** | Feature importance will be derived via perturbation analysis on the original components, measuring impact on ILR-transformed predictions. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-poissons-ratio/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── alloy_record.schema.yaml
│   ├── dataset.schema.yaml
│   ├── model_metrics.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-420-predicting-the-effect-of-alloying-on-the/
├── data/
│   ├── raw/             # Downloaded JSON/CSV from MP and NIST
│   └── processed/       # Filtered, cleaned, ILR-transformed parquet
├── code/
│   ├── __init__.py
│   ├── data_extraction.py   # FR-001, FR-009: Download, parse, verify independence
│   ├── data_cleaning.py     # FR-002, FR-003: Filter, normalize, check VIF (drop Al)
│   ├── modeling.py          # FR-004, FR-005: ILR, RF, CV, Test split
│   ├── analysis.py          # FR-006, FR-007, FR-008: Importance (perturbation), VIF, Framing
│   ├── state_update.py      # FR-030: Update state.yaml with hashes
│   └── utils.py             # Shared helpers (checksums, ILR math)
├── state/                   # Versioning artifacts
│   └── projects/PROJ-420-predicting-the-effect-of-alloying-on-the.yaml
├── tests/
│   ├── unit/
│   └── contract/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected to align with the linear data science workflow (Extract -> Clean -> Model -> Analyze). This minimizes overhead for the small dataset size and ensures all steps are runnable in a single CI job.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| ILR Transformation | Required to handle the unit-sum constraint of compositional data (atomic fractions). | Standard linear regression on raw fractions would suffer from spurious correlation and multicollinearity. |
| Perturbation Importance | Required to assign importance to original components without invalid back-transformation. | Direct back-transformation of tree splits is mathematically invalid for non-linear models. |
| VIF Diagnostic (Drop Al) | Required by FR-007 to diagnose raw collinearity; dropping Al resolves infinite VIF. | Calculating VIF on all 5 elements (sum=1) yields infinite values, crashing the diagnostic. |
| Associational Framing Injection | Required by FR-008 and SC-005 to prevent causal misinterpretation. | Automated causal claims would be scientifically invalid and violate the project constitution. |
| Independent Measurement Filter (FR-009) | Required to ensure Poisson's ratio is not derived from Young's modulus. | Including derived data would make the prediction task trivial and invalid. |

## Methodology

### 1. Data Extraction and Filtering (FR-001, FR-002, FR-003, FR-009)
- **Source**: Materials Project and NIST (only if verified URLs exist in the "Verified datasets" block).
- **Filter**: Monolithic Al alloys only.
- **Completeness**: Must have Poisson's ratio, Young's modulus, and fractions for Cu, Mg, Si, Zn, Mn.
- **Independence Check (FR-009)**: 
  - **Rule**: Retain ONLY entries where `measurement_method` is explicitly "ultrasonic" or "experimental".
  - **Fallback**: If `measurement_method` is missing or indicates "DFT", "calculated", or "derived", **exclude the entry**. Do not attempt to infer independence.
- **Unit Normalization**: Elastic constants to GPa. Composition to atomic fractions summing to 1.0.
- **Exclusion Rule**: If sum of major elements < 0.95, exclude entry (log warning).

### 2. Feature Engineering (FR-004)
- **Compositional Constraint**: Atomic fractions sum to 1.0, causing perfect multicollinearity in raw space.
- **Transformation**: Apply **Isometric Log-Ratio (ILR)** transformation to the 5-element composition (Cu, Mg, Si, Zn, Mn).
  - **Implementation**: Use the `compositional` Python package (specifically `compositional.transforms.ilr`) to ensure reproducibility and alignment with standard CoDA literature. A custom implementation is rejected to avoid validation overhead.
  - ILR maps the simplex to real Euclidean space, removing the unit-sum constraint.
  - This allows standard regression algorithms (Random Forest) to function correctly.
- **Feature Importance Strategy (FR-006)**:
  - **Method**: Do **NOT** back-transform ILR splits.
  - **Execution**: Train Random Forest on ILR coordinates.
  - **Sensitivity Analysis**: Run Permutation Importance on the **ILR features** to get baseline importance.
  - **Aggregation**: To attribute importance to original elements (Cu, Mg, etc.), perform a **Perturbation-Based Sensitivity Analysis**:
    1. For each original element (e.g., Cu), generate a perturbed dataset by adding small Gaussian noise to the Cu fraction in the raw space.
    2. Re-transform the perturbed raw data to ILR coordinates.
    3. Predict with the trained model and measure the change in loss (MAE).
    4. The magnitude of the loss change represents the element's contribution.
  - This approach is valid and avoids the mathematical impossibility of inverting tree splits.

### 3. Modeling (FR-004, FR-005)
- **Algorithm**: Random Forest Regressor (CPU-tractable, handles non-linearity).
- **Validation**: -fold Cross-Validation.
- **Split**: [deferred] Train / [deferred] Test.
- **Metric**: Mean Absolute Error (MAE).
- **Computational Feasibility**: Random Forest on <1000 samples is well within 2 CPU / 7 GB RAM limits. No GPU required.

#### Statistical Power & Uncertainty
- **Sample Size Limitation**: The plan assumes ≥50 entries (per spec assumptions). If the actual dataset is smaller (e.g., N < 50), the variance of the 5-fold CV MAE estimate will be high.
- **Uncertainty Quantification**: To address this, the `modeling.py` script will perform **Bootstrap Resampling** (1000 iterations) on the CV error. For each iteration, it will resample the dataset with replacement, perform 5-fold CV, and record the MAE.
- **Output**: The final report will include the median MAE and the confidence interval derived from the bootstrap distribution. This quantifies the uncertainty of the predictive accuracy claim (SC-002).

### 4. Diagnostics and Interpretation (FR-006, FR-007, FR-008)
- **Feature Importance**: Extract via the perturbation method described in Step 2.
- **Collinearity (FR-007, SC-004)**:
  - Compute Variance Inflation Factors (VIF) on the **raw** (untransformed) composition.
  - **Method**: Drop one component (Al) to avoid infinite VIF due to the sum-to-one constraint.
  - **Output**: Write VIF scores to `diagnostics.json`.
  - **Clarification**: VIF > 5 is an **expected** outcome in raw compositional space due to the unit-sum constraint. This diagnostic confirms that the ILR transformation was necessary. It does **NOT** indicate a model failure or halt the pipeline. The "flag" is redefined as a diagnostic confirmation rather than a pass/fail metric.
  - **SC-004 Compliance**: These VIF scores from `diagnostics.json` will be explicitly included in the final report to satisfy the measurement requirement.
- **Associational Framing (FR-008, SC-005)**:
  - **Mechanism**: The `analysis.py` script will programmatically inject the phrase "associational (not causal)" into the final report template for every result statement.
  - **Verification**: A unit test (`tests/unit/test_framing.py`) will verify the presence of this phrase in the generated report before the file is written. If the phrase is missing, the script will raise an error.

## Statistical Rigor & Limitations

- **Multiple Comparisons**: Not applicable. The study focuses on a single outcome (Poisson's ratio) and a single model.
- **Sample Size**: The plan assumes ≥50 entries (per spec assumptions). If the actual dataset is smaller, the 5-fold CV may have high variance. This will be reported as a limitation, and bootstrap confidence intervals will be used to quantify uncertainty.
- **Causal Inference**: The dataset is observational. The plan explicitly avoids causal language. The "effect" in the title refers to the predictive association, not a causal mechanism.
- **Measurement Validity**: The plan relies on the assumption that the source databases contain valid, independent measurements of Poisson's ratio (FR-009). If the data is derived, it will be excluded.

## Compute Feasibility

- **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
- **Method**: Random Forest (scikit-learn) is CPU-efficient. Bootstrap resampling (1000 iterations) is computationally intensive but feasible for N < 1000 on 2 cores within 6 hours.
- **Data Size**: Expected < 1000 rows.
- **Runtime**: Estimated < 3 hours for full pipeline including bootstrap.
- **GPU**: Not required. No CUDA dependencies.

## Conclusion

This research plan addresses the user's question by establishing a rigorous, reproducible pipeline for predicting Poisson's ratio from composition. It adheres to the compositional data analysis principles (ILR) and maintains scientific integrity by framing results as associational. The primary risk is the availability of the specific dataset fields in the public repositories, which will be handled by the robust error handling defined in the edge cases.