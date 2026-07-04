# Implementation Plan: The Effect of Priming on Prosocial Behavior in Online Communities

**Branch**: `001-the-effect-of-priming-on-prosocial-behav` | **Date**: 2023-10-27 | **Spec**: `spec.md`

## Summary

This project implements a computational social science study to determine if the presence of prosocial cues (keywords like "help", "support", "charity") in Reddit thread titles correlates with increased prosocial language in subsequent replies. The technical approach involves: (1) ingesting and filtering Reddit data from five specific subreddits using a verified multi-subreddit source (pushshift/reddit), (2) classifying threads into "Prime" and "Control" groups using NLTK tokenization and negation logic, (3) computing prosocial action counts and VADER sentiment scores on a CPU-only environment, (4) validating measurement tools against a human-annotated gold standard with distinct intent-based criteria, (5) generating **sentence embeddings** to control for semantic topic confounding, and (6) executing a **Generalized Linear Mixed Model (GLMM)** with a Negative Binomial link to test the hypothesis, controlling for topic, age, and other confounders. The implementation strictly adheres to the project constitution regarding reproducibility, data hygiene, and privacy.

**Critical Statistical Correction**: The original spec (FR-005) requests a Linear Mixed-Effects Model (LMM) with Gaussian assumptions. However, the dependent variable `prosocial_action_count` is count data (integers ≥ 0). To ensure scientific validity, this plan mandates the use of a **Generalized Linear Mixed Model (GLMM)** with a **Negative Binomial distribution**. This corrects the violation of normality assumptions inherent in applying LMM to count data. The plan explicitly flags this as a necessary deviation from the spec's statistical method description, pending a formal spec amendment to align FR-005 with GLMM.

**Topic Confounding Mitigation**: To address the "topic selection effect" (where Prime threads are inherently about prosocial topics), this plan introduces a **semantic topic control**. We will compute sentence embeddings for thread titles using a lightweight, CPU-tractable model (`all-MiniLM-L6-v2`). These embeddings (or their principal components) will be included as covariates in the GLMM to isolate the effect of the specific prime keyword from the general prosocial nature of the topic.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `nltk`, `vaderSentiment`, `statsmodels`, `scikit-learn`, `seaborn`, `matplotlib`, `requests`, `pyyaml`, `pydantic`, `sentence-transformers` (CPU-only version), `torch` (CPU wheel)  
**Storage**: Local CSV/Parquet files (data hygiene enforced via checksums); no external DB.  
**Testing**: `pytest` (unit tests for classification logic, integration tests for pipeline flow, contract tests for schema validation).  
**Target Platform**: GitHub Actions `ubuntu-latest` (2 vCPU, 7 GB RAM, CPU-only).  
**Project Type**: Data Science / Research Pipeline (CLI).  
**Performance Goals**: Full pipeline (10k comments) ≤ 4 hours; Memory usage ≤ 6 GB peak.  
**Constraints**: No GPU usage; strict PII anonymization (SHA-256 hashing); dataset must contain all target subreddits.  
**Scale/Scope**: A large volume of comments; subreddits; Multiple raters for validation.

## Constitution Check

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`; dataset sources fixed to verified HuggingFace URLs; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | All dataset URLs cited from the `# Verified datasets` block (including the verified `pushshift/reddit` multi-subreddit source); no external citations invented. |
| **III. Data Hygiene** | **PASS** | Raw data preserved; derivations written to new files; checksums recorded in state YAML; PII scan enforced. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats trace to `data/` and `code/`; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts hashed; state file updated on change. |
| **VI. Measurement Validity** | **PASS** | VADER and action lexicon validated against human annotations (Cohen's Kappa ≥ 0.7) per FR-011/SC-006. Human codebook explicitly distinguishes *intent* from *lexical form* to avoid circular validation. |
| **VII. Privacy/Anonymization** | **PASS** | Usernames hashed (SHA-256); timestamps stripped after deriving `thread_age`; no PII in output. |

## Project Structure

### Documentation (this feature)

```text
specs/001-the-effect-of-priming-on-prosocial-behav/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   └── gold_standard.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── main.py              # Orchestration entry point
├── config.py            # Constants (subreddits, keywords, seeds)
├── ingestion/
│   ├── __init__.py
│   ├── fetch_data.py    # Data retrieval, validation, & filtering
│   └── classify.py      # Prime/Control classification logic
├── processing/
│   ├── __init__.py
│   ├── scoring.py       # VADER & Action Count
│   ├── embedding.py     # Sentence embedding generation (CPU)
│   ├── validation.py    # Human annotation comparison
│   └── anonymize.py     # PII hashing
├── analysis/
│   ├── __init__.py
│   ├── glmm.py          # Generalized Linear Mixed Model (Negative Binomial)
│   ├── sensitivity.py   # Bootstrap & robustness checks
│   └── viz.py           # Boxplot generation
├── utils/
│   ├── logger.py
│   └── checksum.py
└── tests/
    ├── test_classify.py
    ├── test_scoring.py
    └── test_glmm.py

data/
├── raw/                 # Downloaded parquet files (checksummed)
├── processed/           # Anonymized, scored, embedded CSVs
└── validation/          # gold_standard.csv, validation_reports/

output/
├── results.json         # Final stats & p-values
├── figures/             # boxplot.png
└── logs/
```

**Structure Decision**: Single `code/` directory with modular sub-packages (`ingestion`, `processing`, `analysis`) to maintain clear separation of concerns while keeping the project runnable as a single CLI tool. This minimizes overhead and fits the GitHub Actions runner constraints.

## FR/SC Coverage Mapping

| FR/SC ID | Plan Phase/Step | Implementation Detail |
| :--- | :--- | :--- |
| **FR-001** | Ingestion | `fetch_data.py` loops until a sufficient number of comments are collected or exhaustion; aborts if <4k/group. |
| **FR-001a** | Ingestion | `fetch_data.py` validates subreddit presence; switches to verified `pushshift/reddit` if primary fails. |
| **FR-002** | Classification | `classify.py` uses NLTK `word_tokenize` + negation window (variable size) logic. |
| **FR-002a** | Classification | Negation exclusions logged and assigned to Control. |
| **FR-002c** | Classification | **Not Implemented (Optional)**. Confidence score feature skipped as per plan decision. |
| **FR-003** | Scoring | `scoring.py` computes VADER scores + `prosocial_action_count`. |
| **FR-003b** | Scoring | Action lexicon excludes prime keywords and semantic equivalents (`donate`, `share`, etc.). |
| **FR-004** | Analysis | `glmm.py` generates descriptive stats JSON. |
| **FR-005** | Analysis | `glmm.py` fits **GLMM (Negative Binomial)** formula with `statsmodels`; p < 0.05 threshold. *Note: Deviates from spec's LMM(Gaussian) to ensure statistical validity.* **Includes topic embedding covariate.** |
| **FR-005a** | Analysis | `sensitivity.py` runs A sufficient number of bootstrap resamples will be generated to ensure robust estimation of sampling variability. + model variants. |
| **FR-005b** | Analysis | `glmm.py` checks variance component; drops `user_id` if singular fit. |
| **FR-006** | Analysis | `viz.py` generates `boxplot.png`. |
| **FR-009** | Anonymization | `anonymize.py` hashes usernames (SHA-256) after computing `thread_age`. |
| **FR-010** | Validation | `validation.py` performs stratified sampling with a minimum threshold per stratum and merge logic. |
| **FR-010a** | Validation | **Explicitly implemented**: Merge hierarchy (Thematic -> Thread Type -> Global) as per spec. |
| **FR-011** | Validation | `human_annotation_protocol.md` defines protocol; `gold_standard.csv` structure enforced. |
| **FR-012** | Performance | All processing uses CPU-optimized pandas/nltk; memory profiling in CI. Embedding generation is vectorized. |
| **FR-013** | Pre-study | `main.py` includes power analysis check (d=0.15) and prevalence estimation before full run. |
| **FR-014** | Ingestion | **Pre-flight Check**: `fetch_data.py` programmatically confirms subreddit presence before retrieval. |
| **SC-001** | Analysis | GLMM p-value output in `results.json`. |
| **SC-002** | Analysis | Control variable significance checked in GLMM output. |
| **SC-003** | Analysis | p < 0.05 threshold applied. |
| **SC-004** | Performance | CI timeout set to 4 hours; runtime monitored. |
| **SC-005** | Anonymization | PII scan script runs on `data/processed/`. |
| **SC-006** | Validation | Cohen's Kappa ≥ 0.7 calculated in `validation.py`. |
| **SC-007** | Validation | `gold_standard.csv` requires ≥ 3 raters. |
| **SC-008** | Validation | `neg_score` correlation with VADER `neg` checked. |
| **SC-009** | Anonymization | `thread_age` validation in `data-model.md`. |
| **SC-010** | Pre-study | Power analysis warning logged if N < required. |

## Computational Feasibility

- **Hardware**: GitHub Actions `ubuntu-latest` (2 vCPU, 7 GB RAM).
- **Strategy**: 
  - Data loaded in chunks or filtered immediately to stay under 6 GB RAM.
  - VADER and NLTK are CPU-efficient; no GPU required.
 - **Embedding Generation**: `sentence-transformers` with `all-MiniLM-L6-v2` is CPU-optimized and runs efficiently on cores for A dataset of [deferred] rows (approx. 1-2 mins).
  - GLMM via `statsmodels` (Negative Binomial) is CPU-native and scales linearly for N=10k.
  - Bootstrap (multiple iterations) is parallelized via `joblib` (multiprocessing) but limited to a small number of cores to avoid OOM.
- **Risk Mitigation**: If memory exceeds 6 GB, `pandas` will be replaced with `dask` or data will be downsampled (logged) per FR-013.

## Data Gap Resolution Protocol

1. **Primary Source**: Attempt to load `pushshift/reddit` (HuggingFace) as the primary verified multi-subreddit source.
2. **Pre-flight Validation**: Before retrieval, `fetch_data.py` executes `validate_subreddits()` to confirm the presence of all 5 target subreddits (`r/AskReddit`, `r/relationships`, `r/socialscience`, `r/psychology`, `r/dataisbeautiful`).
3. **Switch Logic**: If the primary source lacks any required subreddit, the system **MUST** switch to the verified fallback (same source, different query parameters or a secondary verified multi-subreddit dataset if available) **before** proceeding. If no verified multi-subreddit source is available, the system aborts with a clear error message listing the missing subreddits.
4. **Abort Condition**: If the dataset is exhausted before reaching `TARGET_N` or group sizes are insufficient, the system aborts and logs the insufficiency.

## Human Annotation Protocol Implementation

- **Deliverable**: `human_annotation_protocol.md` will be created in `data/validation/`.
- **Content**:
  - Recruitment of independent raters.
  - **Codebook Definition**: Explicitly defines "prosocial action" based on **intent** (e.g., "offers help", "provides resources") and **outcome** (e.g., "reduces distress"), distinct from the specific verb list used for the automated count. This ensures validation measures *behavioral intent* rather than *lexical matching*.
  - Format for `gold_standard.csv` (columns: `comment_id`, `rater_id`, `label_prosocial`, `label_neg`).

## Stratified Sampling Logic (FR-010a Compliance)

The `validation.py` module implements the following hierarchy for insufficient strata:
1. **Merge Thematic**: Merge subreddits within the same thematic category (e.g., "social-science" = `r/socialscience` + `r/psychology`).
2. **Merge Thread Type**: If still insufficient, merge Prime and Control groups within the thematic category.
3. **Global Pool**: If still insufficient, draw from the global pool until the -sample minimum is met.
This logic is explicitly coded and tested to ensure compliance with FR-010a.

## Topic Control Strategy

To address the "topic selection effect":
1. **Embedding Model**: Use `sentence-transformers/all-MiniLM-L6-v2`. This The model is small., runs on CPU, and produces high-dimensional vectors.
2. **Dimensionality Reduction**: Due to multicollinearity concerns, we will apply Principal Component Analysis (PCA) to the embeddings and retain a subset of top components as covariates.
3. **Model Integration**: These A set of components will be added as fixed effects in the GLMM.: `prosocial_action_count ~ thread_type + thread_age + comment_count + topic_pc1 + topic_pc2 + topic_pc3 + (1|thread_id) + (1|user_id)`.
4. **Validation**: We will verify that the embeddings distinguish between Prime and Control topics, ensuring they are capturing relevant semantic variance.