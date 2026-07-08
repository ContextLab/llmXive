# Implementation Plan: The Impact of Linguistic Complexity on Trust in AI-Generated Text

**Branch**: `001-linguistic-complexity-trust` | **Date**: 2024-05-21 | **Spec**: `specs/001-the-impact-of-linguistic-complexity-on-t/spec.md`
**Input**: Feature specification from `specs/001-the-impact-of-linguistic-complexity-on-t/spec.md`

## Summary

This project investigates whether linguistic complexity (syntactic and lexical) in AI-generated text predicts human trust ratings when the source is explicitly identified as AI. The technical approach involves three phases: () generating a dataset of text samples using a local LLM (Gemma-2B) with controlled prompt variations; (2) collecting trust ratings via a Prolific survey using a within-subjects design (each participant rates a subset of samples); and (3) performing statistical analysis using Multilevel (Mixed-Effects) Models with PCA-derived orthogonal factors to test for non-linear (inverted-U) relationships, correcting for multiple comparisons via Benjamini-Hochberg (FDR).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (CPU-only), `torch` (CPU), `scikit-learn`, `statsmodels` (mixedlm), `pandas`, `numpy`, `seaborn`, `textstat`, `nltk`, `datasets`, `requests`  
**Storage**: Local CSV/Parquet files in `data/` (checksummed); SQLite for temporary survey state  
**Testing**: `pytest` for unit tests; contract tests against YAML schemas; CI integration via GitHub Actions  
**Target Platform**: Linux (GitHub Actions free-tier: Limited CPU, 7 GB RAM, 14 GB disk, No GPU)  
**Project Type**: Computational Research Pipeline (CLI scripts + Analysis)  
**Performance Goals**: Complete data generation and analysis within 6 hours on CI; memory usage < 6 GB during peak  
**Constraints**: No GPU usage; no large model training; data subset to fit RAM; random seeds pinned for reproducibility  
**Scale/Scope**: ~ generated text samples; N ≥ 100 valid participant responses; orthogonal complexity factors analyzed  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in all scripts (`code/`); `requirements.txt` pins versions; external datasets (Wikipedia) fetched via canonical `datasets` loader; CI runs on fresh runner. |
| **II. Verified Accuracy** | PASS | All citations (e.g., MTLD definition, Flesch-Kincaid formula) will be validated against primary sources by Reference-Validator Agent before paper inclusion. |
| **III. Data Hygiene** | PASS | Raw data (generated text, survey responses) preserved unchanged; derivations (cleaned datasets, analysis outputs) written to new files with checksums recorded in `state/...yaml`. No PII in data (participant IDs are anonymized). |
| **IV. Single Source of Truth** | PASS | All figures/statistics in paper trace to `data/` rows and `code/` blocks; no hand-typed numbers. |
| **V. Versioning Discipline** | PASS | Artifacts carry content hashes; `state/...yaml` updated on artifact changes. |
| **VI. Data Source Independence** | PASS | Predictor (complexity) derived from `code/generate_text.py` (local LLM); Outcome (trust) derived from `code/collect_trust.py` (Prolific survey); no mechanical construction linking them. |
| **VII. Metric Dimensionality** | PASS | Syntactic (FK, Sentence Length) and Lexical (MTLD) metrics are combined into orthogonal factors (via PCA) to ensure the phenomenon is not conflated with a single proxy or definitionally collinear variables. Analysis is performed on these distinct factors. |

## Project Structure

### Documentation (this feature)

```text
specs/001-the-impact-of-linguistic-complexity-on-t/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── text_sample.schema.yaml
│   ├── participant_response.schema.yaml
│   └── analysis_result.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-521-the-impact-of-linguistic-complexity-on-t/
├── code/
│   ├── __init__.py
│   ├── generate_text.py       # FR-001, FR-002: LLM generation + metric computation
│   ├── collect_trust.py       # FR-003, FR-004: Survey interface + attention checks
│   ├── analyze.py             # FR-005, FR-006, FR-007, FR-008: Mixed-Effects + PCA + FDR
│   ├── utils.py               # Helper functions (seed pinning, metric calculation, PCA)
│   └── requirements.txt       # Pinned dependencies
├── data/
│   ├── raw/
│   │   ├── generated_text.csv # Output of generate_text.py
│   │   └── trust_responses.csv # Output of collect_trust.py (or Prolific export)
│   ├── processed/
│   │   ├── cleaned_responses.csv # After attention check filtering
│   │   ├── pca_factors.csv     # PCA-derived orthogonal factors
│   │   └── analysis_inputs.csv   # Merged dataset for regression
│   └── outputs/
│       ├── regression_results.json # Coefficients, p-values, FDR adjusted
│       └── figures/                # Plots (Trust vs. Complexity)
├── tests/
│   ├── contract/
│   │   └── test_schemas.py     # Validates data against YAML schemas
│   ├── unit/
│   │   └── test_metrics.py     # Tests for FK, MTLD, sentence length
│   └── integration/
│       └── test_pipeline.py    # End-to-end test (generate -> collect -> analyze)
├── specs/001-the-impact-of-linguistic-complexity-on-t/
│   ├── spec.md
│   ├── plan.md
│   ├── research.md
│   ├── data-model.md
│   ├── quickstart.md
│   └── contracts/
└── state/
    └── projects/PROJ-521-the-impact-of-linguistic-complexity-on-t.yaml
```

**Structure Decision**: Single project structure (Option 1) chosen for simplicity. All scripts are CLI-based, decoupled by function (generation, collection, analysis), and share a common `utils.py` for metrics, PCA, and seeding. This aligns with the "Data Source Independence" principle by keeping generation and collection separate.

## Complexity Tracking

No violations detected. The project scope (A number of samples, 100 participants, 2 factors) is manageable within CI constraints. The use of Gemma-2B (small CPU model) and sampled data ensures feasibility. The shift to Mixed-Effects Modeling and PCA addresses collinearity and non-independence concerns.