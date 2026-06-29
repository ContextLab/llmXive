# Implementation Plan: Predicting Plant Pathogen Host Range from Genomic Data

**Branch**: `001-predicting-plant-pathogen-host-range-fro` | **Date**: 2026-06-24 | **Spec**: `spec.md`

## Summary

This plan implements a computational pipeline to predict plant pathogen host range by extracting genomic features (effectors, Pfam domains, GC content, k-mers, secondary metabolism clusters) from NCBI GenBank genomes, integrating them with interaction records from PHI-base/InteractomeD, and training an interpretable L2-regularized logistic regression model. 

**Critical Feasibility Strategy**: The spec mandates EffectorP and antiSMASH (FR-003). These tools are computationally intensive and may exceed the standard CI runtime if run from scratch on a large set of pathogens. To satisfy both the spec's construct validity requirements and the CI constraints, this plan adopts a **Pre-computed Feature Cache** strategy:
1.  **Offline Pre-computation**: The full feature extraction (EffectorP, antiSMASH, k-mers) is run on a high-performance node (outside CI) for the full pathogen dataset. The resulting feature vectors are committed to `data/raw/` as the "Single Source of Truth".
2.  **CI Validation**: The CI pipeline consumes these pre-computed vectors. It performs all data merging, preprocessing, model training, evaluation, and reporting steps. This ensures the *full pipeline logic* is validated on the *full dataset* within the 5-hour CI limit, without sacrificing biological validity by using invalid proxies.

The pipeline enforces strict CPU-only execution, handles missing data as 'unknown', and includes nested cross-validation for feature selection (PCA + VIF) and significance testing (permutation + FDR).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `biopython`, `scikit-learn`, `pandas`, `numpy`, `shap` (cpu version), `requests`, `tqdm`, `pytest`.  
**Storage**: Local filesystem (`data/`, `code/`, `models/`).  
**Testing**: `pytest` (unit/integration), contract tests against YAML schemas.  
**Target Platform**: Linux (GitHub Actions free-tier: CPU, 7GB RAM).  
**Project Type**: CLI/Data Pipeline / Machine Learning Research.  
**Performance Goals**: End-to-end CI runtime (modeling + eval) ≤ 5 hours for A diverse set of pathogens; Memory ≤ 4GB; Prediction ≤ 30s.  
**Constraints**: No GPU; No proprietary tools; All data must be reproducible from public sources; Missing interactions = 'unknown'.  
**Scale/Scope**: A set of pathogens (pre-computed features), ~k host interactions.

> **Note on Construct Validity**: The plan explicitly **rejects** all "proxies" (e.g., motif counters, Pfam-only counts) for EffectorP 3.0 and antiSMASH 7.0. The hypothesis relies on the specific biological definitions of these tools. If the pre-computed cache cannot be generated (e.g., tools unavailable), the project scope must be reduced or the hypothesis abandoned. No invalid substitution is permitted.

## Constitution Check

| Principle | Status | Action/Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | All random seeds pinned; `requirements.txt` pins versions; data fetched from NCBI/PHI-base via scripts; pre-computed vectors checksummed. |
| **II. Verified Accuracy** | **Pass** | Citations in `research.md` will be validated against the "Verified datasets" block. No fabricated URLs. |
| **III. Data Hygiene** | **Pass** | Raw data (FASTA, CSV) stored in `data/raw/` with checksums; pre-computed features in `data/raw/` with checksums. |
| **IV. Single Source of Truth** | **Pass** | Model outputs trace to specific feature extraction scripts; pre-computed vectors are the SSoT for features. |
| **V. Versioning Discipline** | **Pass** | Artifacts (models, data) will be hashed in state YAML. |
| **VI. Biological Provenance** | **Pass** | Accession numbers logged; source DBs (NCBI, PHI-base) recorded; feature extraction tools (EffectorP, antiSMASH) versions logged in metadata. |
| **VII. Interpretability** | **Pass** | SHAP values and permutation tests required for all feature categories. |

## Project Structure

### Documentation (this feature)
```text
specs/001-predicting-plant-pathogen-host-range-fro/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── interaction.schema.yaml
│   ├── genomic_features.schema.yaml
│   ├── model_output.schema.yaml
│   ├── data_quality.schema.yaml
│   ├── sensitivity_analysis.schema.yaml
│   └── bias_awareness.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)
```text
src/
├── data/
│   ├── download.py          # FR-001, FR-002 (NCBI, PHI-base)
│   ├── preprocess.py        # FR-013, FR-014, FR-016 (Missing data, VIF, PCA, Scenario Mode)
│   └── feature_extractor.py # FR-003 (Effector, Pfam, GC, k-mer, SM) - *Offline only*
├── models/
│   ├── train.py             # FR-004, FR-006, FR-012 (CV, Hold-out, Nested PCA/VIF)
│   ├── evaluate.py          # FR-005, FR-006, FR-016 (AUPRC, Permutation, Sensitivity)
│   └── interpret.py         # FR-007, FR-017, FR-018 (SHAP, Breadth, Bias Report)
├── cli/
│   ├── run_pipeline.sh      # Main entry point
│   └── predict_host_range.sh # US-3 entry point
├── utils/
│   ├── logging.py           # FR-010, SC-005
│   └── validators.py        # Contract checks
└── config.py                # Paths, seeds, thresholds

tests/
├── unit/
├── integration/
└── contract/                # Validates against contracts/*.yaml

data/
├── raw/                     # Downloaded FASTA, CSVs, **Pre-computed Feature Vectors**
├── processed/               # Interaction matrices (by scenario), VIF masks, PCA transforms
└── models/                  # model.pkl, scaler.pkl
```

**Structure Decision**: Single `src/` tree for modularity, separating data ingestion, feature engineering, and modeling. `cli/` provides the user-facing scripts. `contracts/` defines the data contracts for validation.

## Logging Strategy (SC-005)

To satisfy SC-005, the `pipeline.log` MUST contain at least one INFO entry for each major step. The following mapping is enforced:

| Module | Step | Required INFO Message Pattern |
| :--- | :--- | :--- |
| `download.py` | Download | `INFO: Download complete for [N] pathogens.` |
| `feature_extractor.py` | Feature Extraction | `INFO: Feature extraction complete for [N] pathogens.` |
| `preprocess.py` | Preprocessing | `INFO: Preprocessing complete. [N] samples retained. Scenario: [PRIMARY|SENSITIVITY].` |
| `train.py` | Model Training | `INFO: Model training complete. Best lambda: [value].` |
| `evaluate.py` | Evaluation | `INFO: Evaluation complete. AUPRC: [value].` |
| `interpret.py` | Reporting | `INFO: Reports generated: bias_awareness.json, data_quality_report.json.` |

## Phase Plan (Computational Task Ordering)

1.  **Phase 0: Data Acquisition & Validation**
    *   Download pathogen genomes from NCBI. (FR-001).
    *   Fetch interaction data from PHI-base/Interactome3D (FR-002).
    *   Merge, deduplicate, and log missing records as 'unknown' (FR-013).
    *   **Generate Data-Quality Report**: Calculate missing % per pathogen. Output `data/reports/data_quality_report.json` (FR-013).
    *   *Gate*: Verify all 50 pathogens have at least one interaction record (FR-011).

2.  **Phase 1: Feature Extraction (Offline Pre-computation)**
    *   *Note: This phase is run offline on a high-performance node. The resulting vectors are committed to `data/raw/`.*
    *   Compute GC content and k-mer frequencies (FR-003c, 003d).
    *   Run EffectorP (FR-003a) and antiSMASH 7.0 (FR-003e).
    *   Compute Pfam domain counts (FR-003b).
    *   Construct `FeatureVector` per pathogen.
    *   *Gate*: Check for zero-feature pathogens (Edge Case).

3.  **Phase 2: Preprocessing & Collinearity Check**
    *   Encode interaction matrix (binary).
    *   **Scenario Mode Logic (FR-016)**:
        *   **Primary Mode**: Missing interactions are excluded from the label vector (treated as 'unknown'). The training set only includes rows with `infects` ∈ {0, 1}.
        *   **Sensitivity Mode**: Missing interactions are explicitly imputed as `0` (negative) in a derived matrix. This creates a dense label vector where all unobserved pairs are treated as non-infecting.
    *   **Nested PCA & VIF**: For each CV fold:
        1.  Select training set based on the active Scenario Mode.
        2.  Run PCA on training set k-mers (retain >= 95% variance).
        3.  Run VIF on reduced features (threshold >= 5).
        4.  Remove collinear features.
    *   Split data: Train/Val (stratified) + Hold-out (FR-012).

4.  **Phase 3: Model Training & Evaluation**
    *   **Step A (Primary Model)**: Train L2 Logistic Regression with inner -fold CV (FR-004) using **Primary Mode** data.
    *   **Step B (Sensitivity Model)**: Train L2 Logistic Regression with inner k-fold CV (FR-004) using **Sensitivity Mode** data.
    *   **Evaluation**: Evaluate both models on the Hold-out set (SC-001).
    *   **Permutation Testing**: Perform permutation testing (FR-006) for both models.
    *   **Sensitivity Analysis Report**: Compare AUPRC of Primary vs. Sensitivity models. Output `data/reports/sensitivity_analysis.json` (FR-016). If AUPRC delta > threshold, flag.

5.  **Phase 4: Interpretation & Reporting**
    *   Generate SHAP values (FR-007) for the Primary Model.
    *   Compute Host-Range Breadth (FR-017): Distinguish 'Observed' (count of known hosts) vs 'Predicted' (mean probability).
    *   **Generate Bias-Awareness Report**: Calculate interaction count per pathogen. If top 10 pathogens account for >80% of interactions, flag as HIGH BIAS. Output `data/reports/bias_awareness.json` (FR-018).
    *   Output `model.pkl`, `significant_features.tsv`, `pipeline.log`.

## Constitution Check (Detailed)

| Principle | Status | Action/Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Seeds pinned; `requirements.txt` pins versions; pre-computed vectors checksummed. |
| **II. Verified Accuracy** | **Pass** | Citations validated; no fabricated URLs. |
| **III. Data Hygiene** | **Pass** | Raw data and pre-computed vectors checksummed. |
| **IV. Single Source of Truth** | **Pass** | Pre-computed vectors are the SSoT for features. |
| **V. Versioning Discipline** | **Pass** | Artifacts hashed. |
| **VI. Biological Provenance** | **Pass** | Tool versions (EffectorP 3.0, antiSMASH 7.0) logged in metadata. |
| **VII. Interpretability** | **Pass** | SHAP and permutation tests required. |