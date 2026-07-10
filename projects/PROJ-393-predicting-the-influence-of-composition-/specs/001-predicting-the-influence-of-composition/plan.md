# Implementation Plan: Predicting the Influence of Composition on the Magnetic Hysteresis of Heusler Alloys

**Branch**: `001-predict-heusler-hysteresis` | **Date**: 2023-10-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-predict-heusler-hysteresis/spec.md`

## Summary

This project implements an **exploratory** computational pipeline to aggregate experimental data on Heusler alloys, engineer composition-based descriptors, and train regression models (Linear, Random Forest) to predict magnetic hysteresis parameters (coercivity, saturation magnetization). 

**Critical Scientific Context**: The study acknowledges that magnetic hysteresis ($H_c$) is primarily a microstructure-dependent property. While composition sets the *potential* (saturation magnetization), $H_c$ is determined by domain wall pinning sites (defects, grain boundaries). Therefore, a global model predicting $H_c$ from composition alone is scientifically limited. This plan treats the modeling as a **first-order approximation** and an **exploratory** investigation into whether composition provides *any* predictive signal, explicitly acknowledging the high probability of spurious correlations due to unmeasured microstructural confounders. The success criteria are framed as exploratory benchmarks rather than definitive validation targets.

The approach strictly adheres to the project constitution regarding reproducibility, data hygiene, and computational feasibility on CPU-only CI. The plan explicitly addresses the scarcity of unified experimental datasets by designing a robust ingestion pipeline that aggregates from NIST, journal supplements, and manual curation, while strictly excluding DFT-calculated targets.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `pyyaml`, `requests`, `scikit-learn-extra` (for MICE)  
**Storage**: Local CSV/Parquet files under `data/` (raw and processed), JSONL for logs.  
**Testing**: `pytest` (unit tests for parsers, integration tests for pipeline stages).  
**Target Platform**: GitHub Actions free-tier (Linux, 2 CPU, 7GB RAM).  
**Project Type**: Computational research pipeline / CLI tool.  
**Performance Goals**: Full pipeline execution ≤ 6 hours; Memory usage < 6 GB; No GPU required.  
**Constraints**: No DFT targets in training; strict unit normalization (Oe, emu/g); **MICE imputation** for missing data; CPU-only inference/training.  
**Scale/Scope**: Target ≥50 experimental data points; ~5 engineered features per entry.

> **Dataset Note**: The "Verified datasets" block provided in the prompt contains URLs for NIST *security* guidelines (800-53), LLM leaderboards, and unrelated music/banking datasets. **None** of these contain Heusler alloy magnetic hysteresis data. The plan below explicitly addresses this gap by defining the ingestion strategy to fetch from the *actual* scientific sources (NIST Materials Data Repository, specific journal supplements) and manual curation, as mandated by FR-001 and the spec's assumption that no pre-existing unified dataset exists. The implementation will not use the irrelevant URLs listed in the prompt's "Verified datasets" block for the scientific data.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Random seeds pinned in `code/`; `requirements.txt` pins all deps; external data fetchers use fixed URLs/versions. |
| **II. Verified Accuracy** | **Compliant** | **Phase 0.2** explicitly validates citations before data ingestion; citations in `research.md` will be validated against primary sources before use. |
| **III. Data Hygiene** | **Compliant** | Raw data stored in `data/raw/` with checksums; derived data in `data/processed/`; no in-place edits. |
| **IV. Single Source of Truth** | **Compliant** | All figures/stats in the final report will be generated programmatically from `data/processed/` and `code/`. |
| **V. Versioning Discipline** | **Compliant** | **Phase 4.0** explicitly calculates and records artifact hashes into the state file. |
| **VI. Descriptor Consistency** | **Compliant** | Elemental properties loaded from a **fixed local CSV** (`data/raw/elemental_properties.csv`) to ensure numerical stability, not a dynamic library. |
| **VII. Experimental Context** | **Compliant** | Metadata fields `synthesis_method` and `crystal_structure` included in `AlloyEntry`; provenance tracked for all sources. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-heusler-hysteresis/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Canonical Schema)
│   ├── alloy_entry.schema.yaml
│   └── model_result.schema.yaml  # Consolidated canonical schema
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── raw/             # Ingested raw files (NIST, JSON, PDF extracts)
│   ├── processed/       # Standardized CSVs, feature-engineered datasets
│   └── checksums.txt    # SHA256 hashes of raw files
├── src/
│   ├── ingestion/       # Scripts to fetch and parse NIST, journals, manual data
│   ├── preprocessing/   # Unit normalization, missing value handling (MICE), DFT filtering
│   ├── features/        # Descriptor calculation (VEC, electronegativity, etc.)
│   ├── models/          # Training scripts (Linear, RF), hyperparameter tuning
│   ├── validation/      # F-tests, bootstrapping, partial dependence plots, stratified analysis
│   └── utils/           # Periodic table loader (local CSV), logging, checksums
├── tests/
│   ├── unit/            # Parser tests, unit conversion tests
│   └── integration/     # Full pipeline sanity checks
├── requirements.txt     # Pinned dependencies
└── main.py              # Entry point to run the full pipeline

docs/
├── reports/             # Final statistical report, partial dependence plots
│   ├── data_scarcity_warning.md  # FR-008 Output
│   ├── statistical_limitations.md # FR-009 Output
│   └── microstructure_note.md     # FR-010 Output
└── data_dictionary.md   # Documentation of fields and units
```

**Structure Decision**: Single-project structure (`code/` and `tests/` at root) selected to maintain simplicity for a computational research pipeline. This aligns with the "Single Source of Truth" principle by keeping data and code in a tight, reproducible loop.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Separate Ingestion Module** | Data sources are heterogeneous (JSONL, PDFs, manual text) and require distinct parsers. | A monolithic script would be unmaintainable and violate the "Data Hygiene" principle of preserving raw data. |
| **Explicit DFT Filter** | Spec requires excluding DFT targets to ensure statistical validity of experimental correlations. | Simple filtering by column name is insufficient; requires semantic parsing of "source" metadata. |
| **MICE Imputation** | Listwise deletion on small datasets (N<50) would destroy statistical power. MICE preserves sample size. | Simple mean imputation introduces bias; listwise deletion reduces N below meaningful thresholds. |
| **Stratified Analysis** | Microstructure confounds composition effects. Stratification isolates composition effects within homogeneous groups. | Global regression would conflate processing effects with composition effects, invalidating causal claims. |
| **Exploratory Framing** | N=50 is insufficient for robust generalization. Framing as exploratory manages scientific expectations. | Treating it as confirmatory would be scientifically unsound given the sample size and confounders. |

## Implementation Phases

### Phase 0: Research & Validation (Pre-Implementation)

**Goal**: Validate data sources, verify citations, and establish the research baseline.

*   **0.1 Data Source Verification**: Confirm availability of NIST MDR, Journal Supplements, and Manual Curation targets.
*   **0.2 Verified Accuracy Gate (Constitution Principle II)**:
    *   Run the Reference-Validator Agent against all proposed citations in `research.md`.
    *   **GATE**: Do not proceed to ingestion if any citation is unreachable or mismatched.
    *   Record validation status in `state/projects/PROJ-393...yaml`.
*   **0.3 Power Analysis Update**:
    *   Explicitly calculate power for N=50, 5 predictors, R²=0.6.
    *   Document that detecting R²=0.6 is statistically improbable and frame the study as **Exploratory**.

### Phase 1: Data Engineering & Contract Definition

**Goal**: Ingest, clean, and engineer features while defining data contracts.

*   **1.1 Ingestion Pipeline**:
    *   Fetch data from NIST, Journals, and Manual sources.
    *   Store raw files in `data/raw/` with checksums.
*   **1.2 Preprocessing & Missing Data Handling**:
    *   Standardize units (Oe, emu/g).
    *   **Missing Data Strategy**: Apply **Multiple Imputation by Chained Equations (MICE)** for missing values in descriptors or targets.
    *   **Rule**: If >50% of a row is missing, perform listwise deletion. Otherwise, use MICE (multiple imputations).
    *   Filter out DFT targets (FR-008).
*   **1.3 Completeness Metric Calculation (SC-004)**:
    *   Calculate the proportion of valid data points per source.
    *   Output `data/processed/completeness_report.json`.
*   **1.4 Feature Engineering**:
    *   Compute multiple descriptors (Electronegativity, VEC, Radii Variance, d-electrons, Size Mismatch) using **fixed local CSV** (Constitution Principle VI).
*   **1.5 Contract Validation**:
    *   Validate `data/processed/alloys_features.csv` against `contracts/alloy_entry.schema.yaml` and `contracts/composition_descriptor.schema.yaml`.
    *   **GATE**: Do not proceed to modeling if schema validation fails.

### Phase 2: Modeling & Training

**Goal**: Train models with robust validation.

*   **2.1 Model Training**:
    *   Train Linear Regression and Random Forest with k-fold cross-validation.
    *   Hyperparameter tuning via GridSearchCV.
*   **2.2 Outlier Detection & Sensitivity (Addressing Scientific Soundness)**:
    *   Perform outlier detection (Isolation Forest) and sensitivity analysis before F-tests.
    *   Document impact of outliers on model stability.

### Phase 3: Statistical Validation & Reporting

**Goal**: Validate models, address confounders, and generate required reports.

*   **3.1 Null Model Comparison**:
    *   Perform F-test against null model (mean prediction).
    *   Compute p-value (SC-001).
*   **3.2 Bootstrapping**:
    *   Resample bootstrapping for 95% CI of R² (SC-002).
*   **3.3 Stratified Analysis & Confounder Control (Addressing Methodology)**:
    *   Group data by `synthesis_method` (if available).
    *   Run models within strata to isolate composition effects from processing effects.
    *   Report results separately for each stratum.
*   **3.4 Partial Dependence Plots**:
    *   Generate PDPs for top 3 features (SC-003).
*   **3.5 Data Scarcity Warning Generation (FR-008)**:
    *   If N < 50, generate `docs/reports/data_scarcity_warning.md` explicitly stating the limitation.
*   **3.6 Statistical Limitations Report (FR-009)**:
    *   Generate `docs/reports/statistical_limitations.md` containing the mandatory disclaimer: "F-test validates statistical fit, not physical mechanism."
*   **3.7 Microstructure Context Report (FR-010)**:
    *   Generate `docs/reports/microstructure_note.md` explicitly logging synthesis methods and noting that hysteresis is heavily influenced by microstructure.
*   **3.8 Success Criteria Evaluation (SC-006 - Exploratory)**:
    *   Evaluate model against held-out test set.
    *   Report R² and p-value.
    *   **Crucial**: Mark SC-006 (R² ≥ 0.6) as **"Exploratory Benchmark"**. If not met, do not flag as "Failure" but as "Consistent with Physical Reality" (given the confounders).
*   **3.9 Physical Plausibility Check (Addressing Scientific Soundness)**:
    *   Explicitly state in the final report that composition does not causally determine $H_c$ without microstructure.
    *   Interpret any correlations as "first-order approximations" only.

### Phase 4: Versioning & Finalization

**Goal**: Ensure reproducibility and state updates.

*   **4.0 Versioning & Hashing (Constitution Principle V)**:
    *   Calculate SHA256 hashes for all artifacts in `data/` and `code/`.
    *   Update `state/projects/PROJ-393...yaml` with `artifact_hashes` and `updated_at`.
*   **4.1 Final Report Assembly**:
    *   Combine metrics, plots, and mandatory disclaimers into `docs/reports/final_report.md`.
