# Implementation Plan: Emotional Contagion in Online Forums

**Branch**: `001-emotional-contagion-decisions` | **Date**: 2026-01-15 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-emotional-contagion-decisions/spec.md`

## Summary

This project implements an observational analysis pipeline to quantify the influence of emotional contagion (seed-post sentiment) on collective decision-making quality in online forums (Reddit/Stack Exchange). The system extracts thread data, computes VADER sentiment scores, derives an emotional contagion index (Pearson correlation of seed sentiment vs. reply sentiment trajectory slope), and fits Generalized Linear Mixed Models (GLMM) to test associations while controlling for platform-level random effects. The pipeline is strictly constrained to CPU-only execution on GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `nltk`, `scikit-learn`, `statsmodels`, `pyyaml`, `requests`, `scipy`  
**Storage**: Local CSV/JSONL files (no external DB); checksummed artifacts in `data/`.  
**Testing**: `pytest` (unit tests for extraction/sentiment; integration tests for pipeline).  
**Target Platform**: Linux (GitHub Actions free-tier runner: multi-core CPU, sufficient RAM, adequate disk).  
**Project Type**: Data analysis CLI / research pipeline.  
**Performance Goals**: Complete analysis of N=500 threads within 6 hours on CPU.  
**Constraints**: No GPU/CUDA; no deep learning training; memory usage <7 GB; data sampled if necessary.  
**Scale/Scope**: ~500 threads across ≥2 subreddits and ≥1 Stack Exchange site.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Plan Action |
|-----------|--------|----------------------------|
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. External data fetched from canonical HuggingFace URLs. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | Citations restricted to verified dataset URLs provided in the prompt. No hallucinated sources. |
| **III. Data Hygiene** | **PASS** | Raw data preserved in `data/raw/` with checksums. Derived data in `data/processed/` with derivation logs. PII scan enforced. Checksums recorded in `state/` under `artifact_hashes`. |
| **IV. Single Source of Truth** | **PASS** | All statistics in `paper/` generated directly from `code/` outputs; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts tracked via content hashes in `state/`. Checksums recorded in `state/projects/PROJ-139-...yaml` under `artifact_hashes` map. |
| **VI. Ground-Truth Alignment** | **PASS** | Ground-truth availability validation (FR-009) implemented. External benchmark comparison performed for valid threads. If <30% valid, study reports failure to meet SC-006, does not pivot to internal proxies. |
| **VII. Sentiment Tool Validation** | **PASS** | VADER validation against 'Sentiment' corpus (or manual annotation of a representative sample) is MANDATORY. Inter-rater reliability (Cohen's Kappa) calculated and stored in `data/`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-emotional-contagion-decisions/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── thread.schema.yaml
│   ├── sentiment.schema.yaml
│   └── result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-139-the-influence-of-emotional-contagion-on-/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── contracts/       # Physical location of schema files (copied from specs/)
│   │   ├── thread.schema.yaml
│   │   ├── sentiment.schema.yaml
│   │   └── result.schema.yaml
│   ├── data/
│   │   ├── download.py        # Fetches from verified HF URLs / Pushshift API
│   │   ├── extract.py         # Thread/seed extraction (FR-001, FR-002)
│   │   ├── sentiment.py       # VADER analysis (FR-003, FR-004)
│   │   ├── metrics.py         # Decision quality & contagion index (FR-005, FR-008)
│   │   ├── modeling.py        # GLMM fitting (FR-006)
│   │   └── validation.py      # Ground truth checks (FR-009)
│   ├── analysis/
│   │   └── run_pipeline.py    # Orchestration script
│   └── tests/
│       ├── test_extract.py
│       ├── test_sentiment.py
│       └── test_modeling.py
├── data/
│   ├── raw/                   # Downloaded JSONL/Parquet (checksummed)
│   └── processed/             # Derived CSVs (thread_metrics.csv)
├── state/
│   └── projects/PROJ-139-the-influence-of-emotional-contagion-on-.yaml  # artifact_hashes map
└── docs/
    └── paper.md
```

**Structure Decision**: Single project structure with modular `code/` subdirectories. The `contracts/` directory is physically located in `code/contracts/` for runtime validation, with source copies in `specs/.../contracts/`. This resolves ambiguity.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **GLMM vs. OLS** | Thread-level random effects are required to account for intra-thread correlation (FR-006). | OLS would violate independence assumptions, leading to inflated Type I errors. |
| **Sensitivity Analysis (FR-008)** | Required to test robustness of conclusions against arbitrary cutoff choices (agreement/entropy). | Single-point analysis is insufficient for rigorous psychological inference. |
| **Ground Truth Validation (FR-009)** | Essential for distinguishing "consensus" from "truth" (Assumption 2). | Ignoring ground truth would conflate popularity with accuracy, violating Principle VI. |
| **API Download Logic** | Spec (FR-001) mandates API-first acquisition. | Static assumption of archives would violate spec requirement for dynamic API fallback. |

## Implementation Phases

### Phase 0: Data Acquisition & Validation
1. **API Download Fallback Logic**: Implement `download.py` to attempt Pushshift API -> Reddit Official API -> Load from verified HuggingFace archives. Log origin type.
2. **Sentiment Tool Validation**: Run VADER against 'Sentiment' (or manual sample annotation). Calculate Cohen's Kappa. Store report in `data/`.
3. **Ground Truth Proxy Definition**: Define 'Solved' flag heuristics for AskScience. Log expected % of valid threads.

### Phase 1: Extraction & Preprocessing
1. **Thread Extraction**: Extract threads with ≥3 seed posts. Exclude <3.
2. **Seed Identification**: Extract first top-level posts.
3. **Reply Selection**: Extract an initial subset of replies for trajectory (fixed window for metric consistency). Exclude threads with <5 replies from contagion analysis.

### Phase 2: Sentiment & Metrics
1. **VADER Analysis**: Compute compound scores.
2. **Contagion Index**: Calculate Pearson correlation between Seed Sentiment and Slope of Reply Sentiment (linear regression of sentiment vs. position) for an initial subset of replies.
3. **Decision Quality**:
   - **Agreement Proportion**: Ratio of replies agreeing with *Seed Sentiment* direction (not Majority Stance).
   - **Shannon Entropy**: On sentiment buckets.
   - **External Validation**: Compare Consensus (Majority) to 'Solved' flag (if available).
4. **Ground Truth Logging**: Log count and percentage of valid threads. Report SC-006 compliance.

### Phase 3: Statistical Modeling
1. **GLMM Fitting**: Thread-level unit of analysis. Random intercept: Subreddit. Fixed effects: Contagion Index, Thread Length, Time-to-Decision.
2. **Significance Testing**: Wald tests (α=0.05).
3. **Multiple Comparison Correction**: Benjamini-Hochberg FDR if ≥3 tests.

### Phase 4: Sensitivity & Reporting
1. **Threshold Sweep**: Agreement {, 0.6, 0.7}, Entropy levels ranging from low to moderate..
2. **FP/FN Calculation**: For valid threads, compute False Positive/Negative rates of Consensus vs. Ground Truth.
3. **Final Report**: Include SC-006 pass/fail status, Ground Truth percentage, and model results.

### Phase 5: Verification
1. **Checksums**: Record all artifacts in `state/` `artifact_hashes`.
2. **Reproducibility**: Re-run pipeline; verify checksums.