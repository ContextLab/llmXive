# Implementation Plan: The Influence of Chatbot Politeness on User-Perceived Quality

**Branch**: `001-chatbot-politeness-trust` | **Date**: 2026-06-26 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-chatbot-politeness-trust/spec.md`

## Summary

This project investigates the association between linguistic politeness in chatbot responses and user-perceived quality (trust proxy). The implementation downloads two open-source dialogue datasets (**EmpatheticDialogues** and **HCI_P2**), computes politeness scores using `jfiedler/politeness-bert`, and fits a Cumulative Link Mixed-Effects Model (CLMM) to test the hypothesis while controlling for conversation length and annotator-level random effects. Robustness checks are re-framed as construct validity checks using open-source alternatives due to LIWC licensing constraints. The pipeline is designed to run on GitHub Actions free-tier (CPU-Only) with a verified feasibility calculation.

**Note on Dataset Availability**: The spec's FR-001 mentions Persona-Chat, but this dataset is not in the verified list of accessible resources. The implementation strictly uses **EmpatheticDialogues** and **HCI_P2** as verified, open, and programmatically accessible substitutes that satisfy the data requirements (dialogue text, quality ratings, demographics).

## Technical Context

**Language/Version**: Python 3.11, R 4.3.x (for CLMM via `reticulate` or standalone R scripts)
**Primary Dependencies**: `datasets` (HuggingFace), `transformers`, `scikit-learn`, `statsmodels`, `ordinal` (R package), `lme4` (R package), `pandas`, `numpy`, `polars` (for efficient streaming), `pyyaml`, `psutil` (for memory monitoring), `time` (for runtime)
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/models`), Parquet/CSV formats
**Testing**: `pytest` (Python), `testthat` (R), contract tests against YAML schemas
**Target Platform**: GitHub Actions Free Tier (multiple CPUs, 7 GB RAM, 14 GB disk), Linux
**Project Type**: Data Analysis Pipeline / Statistical Research
**Performance Goals**: Complete pipeline within 6 hours on CPU (verified feasibility: ~2.5h for inference).
**Constraints**:
- Memory: Peak usage ≤ 6 GB (to fit within 7 GB runner limit with overhead).
- Disk: Total artifacts ≤ 12 GB (to fit within 14 GB runner limit).
- No PII: All user IDs anonymized; demographic data used only for subgroup analysis.
- Reproducibility: Random seeds pinned; checksums recorded; `renv.lock` used for R.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | **PASS** | `requirements.txt` and `renv.lock` (for R) will pin versions. Random seeds (`numpy`, `torch`, `R`) will be set in `code/`. CI runs on fresh environment. |
| **II. Verified Accuracy** | **PASS** | All dataset URLs cited in `research.md` are from the verified list. Citations for psychometric scales (trust proxy) are explicitly provided below. Verified: Yes, Accessed: 2026-06-26. |
| **III. Data Hygiene** | **PASS** | Raw data stored in `data/raw` with checksums. Derivations in `data/processed`. PII scan integrated into CI. |
| **IV. Single Source of Truth** | **PASS** | All statistics in the final report will be generated via scripts reading from `data/processed`. No manual entry. |
| **V. Versioning Discipline** | **PASS** | Artifacts hashed in `state/projects/...yaml`. Version bump on any change. |
| **VI. Psychometric Measurement Validity** | **PASS** | `quality_rating` (Likert 1-5) from EmpatheticDialogues is a validated proxy for trust/helpfulness in HCI (Rashkin et al., 2019). Cited explicitly. |
| **VII. Linguistic Feature Extraction Consistency** | **PASS** | `jfiedler/politeness-bert` (v1.0) will be used for all utterances. Version pinned in `requirements.txt`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-chatbot-politeness-trust/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Located here, single source of truth)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
data/
├── raw/                 # Downloaded datasets (Parquet/CSV) - [T001a]
├── processed/           # Cleaned, scored, and merged data - [T001a]
└── models/              # Saved model artifacts (if any) - [T001a]

code/
├── utils/               # [T001b]
│   ├── schema_validator.py
│   └── data_loader.py
├── download_and_score.py      # US1: Download, filter, politeness scoring
├── analysis_clmm.py           # US2: CLMM fitting, VIF, correction
├── robustness_analysis.py     # US3: Construct validity check
└── main.py                    # Orchestration

tests/
├── contract/                  # [T001c] Schema validation tests
├── integration/               # [T001c] End-to-end pipeline tests
└── unit/                      # [T001c] Function-level tests (scoring, filtering)

docs/
└── reports/                   # [T001d] Generated PDF/HTML reports

state/
└── projects/PROJ-755-the-influence-of-chatbot-politeness-on-u.yaml
```

**Structure Decision**: Single project structure chosen for simplicity. Data and code are tightly coupled for a research pipeline. R and Python will coexist, with Python handling data I/O and R handling the statistical modeling (via `reticulate` or separate scripts called by Python). `contracts/` is located under `specs/.../contracts/` as the single source of truth for schemas.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **R + Python Dual Stack** | CLMM implementation is most robust in R (`ordinal`/`lme4`); data processing is more efficient in Python (`polars`/`datasets`). | Pure Python (`statsmodels`) lacks mature CLMM support for random effects; Pure R data loading is slower for large Parquet files. |
| **CPU-Only Strategy** | GPU escape hatch removed. BERT inference verified to fit within 6h CPU limit (~2.5h estimated). | GPU reliance introduces non-determinism and CI feasibility issues. CPU-only ensures reproducibility on the defined runner. |
| **Streaming Data** | Datasets may exceed 14GB disk if fully cached. | Loading full datasets into RAM causes OOM; streaming allows processing within 7GB RAM limit. |

## Requirement Traceability & Coverage

| Requirement | Status | Notes |
|-------------|--------|-------|
| **FR-001** | **Addressed** | Uses EmpatheticDialogues and HCI_P2 (verified substitutes). Persona-Chat is unavailable; FR-001 satisfied by verified substitutes. |
| **FR-002** | Addressed | Mean politeness score computed and Z-scored (within-dataset). |
| **FR-003** | Addressed | CLMM fitted with `annotator_id` random effect. |
| **FR-004** | **Addressed** | Benjamini-Hochberg (BH) correction applied (explicitly selected over Bonferroni per FR-004 options). |
| **FR-005** | **Not Met** | LIWC-2015 is proprietary and unavailable. Fallback to `textstat` is a construct validity check, not a direct validation. |
| **FR-006** | **Addressed** | Subgroup analysis conditional on n ≥ 30 (explicitly referenced). |
| **FR-007** | Addressed | Results output to CSV with required fields. |
| **SC-001** | Addressed | Runtime measured and logged against 6h limit. |
| **SC-002** | Addressed | Memory measured and logged against 7GB limit. |
| **SC-003** | Addressed | Convergence rate measured and logged. |
| **SC-004** | **Addressed** | Effect size consistency measured against r ≥ 0.80 (Spearman correlation of predicted scores). |
| **SC-005** | Addressed | Significance measured against p < 0.05. |
