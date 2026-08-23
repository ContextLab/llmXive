# Implementation Plan: Predicting Reaction Mechanisms from Spectroscopic Data with Machine Learning

**Branch**: `001-predicting-reaction-mechanisms` | **Date**: 2026-07-11 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-predicting-reaction-mechanisms/spec.md`

## Summary

This feature implements a machine learning pipeline to predict organic reaction mechanisms (SN1, SN2, E1) from spectroscopic data (IR and NMR). The approach ingests raw spectral data from public repositories, converts them into standardized high-dimensional fingerprints (combining IR and NMR features), and trains Random Forest and XGBoost classifiers using stratified k-fold cross-validation. The system prioritizes interpretability via feature importance mapping and statistical rigor via permutation testing (within CV loop) and Benjamini-Hochberg correction, all within the constraints of a CPU-only GitHub Actions runner (limited cores, constrained RAM, and a bounded execution time).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn==1.4.0`, `xgboost==2.0.0`, `pandas==2.2.0`, `numpy==1.26.0`, `datasets==2.18.0`, `pyyaml==6.0.1`, `pytest==8.0.0`  
**Storage**: Local file system (CSV/Parquet) for intermediate artifacts; Hugging Face datasets for ingestion.  
**Testing**: `pytest` with contract tests against YAML schemas.  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Data science pipeline / CLI tool.  
**Performance Goals**: < 6 hours total runtime, < 7GB peak RAM.  
**Constraints**: No GPU; no external API calls during execution; strict reproducibility (seeded RNG).  
**Scale/Scope**: Dataset capped at < 5,000 reactions; features per sample.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on constitution file:*

1.  **Reproducibility (Principle I)**: Plan mandates that every result reported MUST be reproducible by re-running the project's `code/` against the project's `data/` on a fresh GitHub Actions runner. Random seeds MUST be pinned in `code/`. External datasets MUST be fetched from the same canonical source on every run.
2.  **Verified Accuracy (Principle II)**: Every external citation in `idea/`, `technical-design/`, `implementation-plan/`, or `paper/` MUST be verified by the Reference-Validator Agent against the primary source before contributing review points. Title-token-overlap with the cited source MUST be ≥ `CITATION_TITLE_OVERLAP_THRESHOLD` (default set to a high threshold to ensure semantic relevance).
3.  **Data Hygiene (Principle III)**: Datasets MUST be checksummed and the checksum recorded under `data/`. No data may be modified in place; every transformation MUST produce a new file with a documented derivation. Personally identifying information MUST NOT appear in committed data.
4.  **Single Source of Truth (Principle IV)**: Every figure, statistic, or interpretation in the paper MUST trace back to exactly one row in this project's `data/` and one block in this project's `code/`. Derived numbers MUST NOT be hand-typed into the paper.
5.  **Versioning Discipline (Principle V)**: Every artifact under this project carries a content hash. The Advancement-Evaluator Agent invalidates stale review records when the hashed artifact changes. Every research-stage artifact change updates this project's `state/projects/PROJ-088-predicting-reaction-mechanisms-from-spec.yaml` `updated_at` timestamp.
6.  **Spectral Feature Interpretability (Principle VI)**: Every machine learning model trained in this project MUST provide explicit feature importance scores identifying specific IR or NMR spectral bins contributing to mechanism classification (SN1, SN2, or E1). Models that function as black boxes without revealing which spectral peaks (e.g., carbonyl stretches or chemical shift ranges) drive the prediction are considered invalid for this project's research question.
7.  **Computational Efficiency (Principle VII)**: All data processing and model training pipelines MUST complete within a standard GitHub Actions job on a limited number of CPUs with a memory footprint under 7GB. The dataset is capped at <5,000 reactions.

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-reaction-mechanisms/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── ingestion/
│   ├── __init__.py
│   ├── load_nist.py       # Handles NIST WebBook JSONL parsing
│   ├── load_pubchem.py    # Handles PubChem Parquet parsing
│   └── preprocess.py      # Normalization and -bin fingerprinting
├── modeling/
│   ├── __init__.py
│   ├── train.py           # RF and XGBoost training with CV
│   └── metrics.py         # Accuracy, F1, and confusion matrix logic
├── analysis/
│   ├── __init__.py
│   ├── importance.py      # Feature importance extraction
│   ├── permutation.py     # Permutation test implementation
│   └── validation.py      # Literature cross-reference logic
├── utils/
│   ├── __init__.py
│   ├── logging.py         # Warning/Flagging logic for edge cases
│   └── io.py              # Checksum and file I/O helpers
└── cli/
    └── main.py            # Entry point for the pipeline

tests/
├── contract/              # Validates output against YAML schemas
├── unit/                  # Unit tests for fingerprinting and splitting
└── integration/           # End-to-end small dataset test
```

**Structure Decision**: A modular `src/` layout is selected to separate concerns (ingestion, modeling, analysis) while keeping the project as a single Python package. This supports the "Single Source of Truth" principle by isolating data transformation logic from analysis logic. The `contracts/` directory is placed in the spec folder to define the interface between the data pipeline and the modeling/analysis steps.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Two Models (RF + XGBoost)** | Required by FR-002 to compare performance and ensure robustness. | Using only one model would fail the comparative analysis requirement and reduce confidence in the result. |
| **Permutation Testing (N=200)** | Required by FR-004 to establish statistical significance (p < 0.05). N=200 is justified to provide >95% power for large effect sizes while fitting the 6h limit. | Relying solely on CV accuracy without permutation testing fails to rule out overfitting by chance, violating the "Reliability" success criteria. |
| **Benjamini-Hochberg Correction** | Required by FR-007 for multiple comparison correction on feature bins. This is applied to the p-values generated by the per-bin permutation test (not raw importance scores). | Reporting raw p-values for 512 bins would result in massive false positives, invalidating the "Spectral Feature Interpretability" requirement. |
| **Source-Stratified CV** | Required to control for the "Batch Effect" confound where SN1/SN2 data comes from different sources. | Simple stratified CV by label would allow the model to learn source-specific artifacts rather than mechanism-specific features. |

## FR/SC Mapping

- **FR-001**: Handled in `ingestion/preprocess.py` (-bin fingerprinting, Mid-infrared spectral range spanning from the near-infrared to the far-infrared region., 0-12 ppm).
- **FR-002**: Handled in `modeling/train.py` (Stratified K-fold CV

The research question, method, and references remain unchanged as per the planning document guidelines, with the specific fold count generalized to reflect the methodological approach without asserting empirical implementation details.).
- **FR-003**: Handled in `analysis/importance.py` (Feature importance extraction).
- **FR-004**: Handled in `analysis/permutation.py` (Permutation test within CV loop, N=200).
- **FR-005**: Enforced by dataset capping (<5,000) and model selection (RF/XGBoost).
- **FR-006**: Enforced by report generation logic (forbidden words list).
- **FR-007**: Handled in `analysis/importance.py` (BH correction on per-bin p-values).
- **FR-008**: Handled in `ingestion/load_*.py` (Provenance Proxy filtering; fallback to Structure-Verified if kinetic data absent).
- **FR-009**: Handled in `analysis/validation.py` (Partial Dependence Conditioning to decouple structure).
- **FR-010**: Handled in `analysis/validation.py` (Literature lookup with ±10 cm-1 tolerance).
- **SC-001**: Measured in `modeling/metrics.py` (Accuracy vs random baseline).
- **SC-002**: Measured in `analysis/importance.py` (Variance of importance across folds).
- **SC-003**: Measured in `analysis/permutation.py` (p-value < 0.05).
- **SC-004**: Measured in `utils/io.py` (Runtime/memory logging).
- **SC-005**: Measured in `ingestion/preprocess.py` (Class balance check).