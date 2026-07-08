# Implementation Plan: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

**Branch**: `001-statistical-cognitive-decline` | **Date**: 2024-05-22 | **Spec**: `specs/001-statistical-cognitive-decline/spec.md`

## Summary

This feature implements a statistical pipeline to analyze linguistic features in interview transcripts from the ADReSS Challenge dataset. The goal is to detect differences between Control, Mild Cognitive Impairment (MCI), and Alzheimer's Disease (AD) groups using lexical, syntactic, and semantic metrics. **Scope Constraint**: Due to the unavailability of a verified source for the DementiaBank Pitt Corpus, the implementation scope is reduced to ADReSS raw transcripts only. The DementiaBank requirement in the spec is flagged as a blocking gap requiring spec amendment. The implementation adheres to strict CPU-only constraints (GitHub Actions free tier: CPU, limited RAM) and prioritizes reproducibility, data hygiene, and statistical rigor (Bonferroni correction, nested cross-validation, Rank-Biserial effect sizes).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `nltk`, `spaCy` (with `en_core_web_sm`), `sentence-transformers` (CPU-only model `all-MiniLM-L6-v2`), `numpy`, `scipy`, `pyyaml`, `tqdm`  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/interim`); no external database.  
**Testing**: `pytest` (unit, integration, contract tests against YAML schemas).  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`).  
**Project Type**: Data analysis pipeline / CLI tool.  
**Performance Goals**: Total runtime ≤ 6 hours; Memory usage ≤ 6 GB peak (safety margin for 7 GB limit).  
**Constraints**: No GPU; no deep learning training from scratch; no 8-bit/4-bit quantization; strict UTF-8 normalization; exclusion of transcripts < 50 words; **DementiaBank excluded** (unverified source).  
**Scale/Scope**: A cohort of participants (ADReSS only); ~ linguistic features; Multiple classifiers (Logistic Regression, Random Forest).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | All random seeds pinned in `code/`. Dependencies pinned in `requirements.txt`. External datasets fetched via canonical URLs (ADReSS GitHub). |
| **II. Verified Accuracy** | Citations in `research.md` restricted to verified sources. DementiaBank excluded from scope due to lack of verified URL. |
| **III. Data Hygiene** | Raw data preserved in `data/raw` with checksums. Derived data in `data/processed` with derivation logs. PII scan via pre-commit hook. |
| **IV. Single Source of Truth** | All statistics in `paper/` generated directly from `code/` output (no hand-typing). |
| **V. Versioning Discipline** | Content hashes recorded in `state/projects/PROJ-272...yaml` for all artifacts. |
| **VI. Linguistic Feature Transparency** | Feature definitions (spaCy parsing, self-similarity) documented in `research.md` and implemented in `code/linguistic_features.py`. |
| **VII. Clinical Ground Truth Independence** | Labels sourced from ADReSS clinical assessments; semantic features computed from raw text only (pre-computed embeddings ignored). |

**Note on DementiaBank**: The plan excludes DementiaBank from the implementation scope because no verified source URL exists in the "Verified datasets" block. This is a **Spec Gap** (FR-001, Edge Case) that requires a spec update to remove the DementiaBank requirement or provide a verified source.

## Project Structure

### Documentation (this feature)

```text
specs/001-statistical-cognitive-decline/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── feature.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, thresholds
├── ingestion.py         # Data loading, cleaning, UTF-8 normalization (ADReSS GitHub)
├── features.py          # Lexical, syntactic (spaCy), semantic extraction
├── stats.py             # Mann-Whitney U, Bonferroni correction, Rank-Biserial effect sizes
├── modeling.py          # Logistic Regression, Random Forest, Nested CV
├── utils.py             # Logging, seed setting, data validation
└── main.py              # Pipeline orchestration

data/
├── raw/                 # Downloaded raw files (checksummed)
├── interim/             # Intermediate cleaned data
└── processed/           # Final feature matrix (CSV/Parquet)

tests/
├── unit/
│   ├── test_ingestion.py
│   ├── test_features.py
│   └── test_stats.py
├── contract/
│   └── test_schemas.py  # Validates output against contracts/*.schema.yaml
└── integration/
    └── test_pipeline.py # End-to-end run on sample data

requirements.txt
```

**Structure Decision**: Single project structure (`code/`) selected for simplicity and alignment with data analysis workflow. No frontend/backend split required.

## Complexity Tracking

*No violations identified. The single-project structure is sufficient for the scope (data ingestion, feature extraction, statistical testing, modeling). Scope reduced to ADReSS only.*