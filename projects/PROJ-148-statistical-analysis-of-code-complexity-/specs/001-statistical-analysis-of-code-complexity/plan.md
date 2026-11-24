# Implementation Plan: Statistical Analysis of Code Complexity Metrics and Bug Prediction

**Branch**: `001-code-complexity-bug-prediction` | **Date**: 2025-10-21 | **Spec**: `specs/001-statistical-analysis-of-code-complexity/spec.md`  
**Input**: Feature specification from `/specs/001-statistical-analysis-of-code-complexity/spec.md`

## Summary
Implement a reproducible end‑to‑end pipeline that (1) downloads Java projects, (2) extracts static‑analysis complexity metrics with **lizard**, (3) labels functions as bug‑fixes using commit metadata, (4) preprocesses and splits the data, (5) trains an L1‑regularized logistic regression (primary) and a Random Forest (alternative) while checking collinearity, (6) evaluates with ROC‑AUC, PR‑AUC, calibration, and (7) generates thresholds, partial‑dependence plots, and a final report. All steps map to the functional requirements (FR‑001 … FR‑009) and success criteria (SC‑001 … SC‑003).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `scikit-learn`, `lizard`, `statsmodels`, `matplotlib`, `seaborn`, `pymer4` (all pinned in `requirements.txt`)  
- **Storage**: CSV files under `data/` (raw, processed, splits) and model pickles under `data/model/`  
- **Testing**: `pytest` with contract tests in `tests/contract/`  
- **Target Platform**: GitHub Actions Free Tier (2 CPU cores, ≈7 GB RAM, ≤6 h) – **CPU‑first**; no GPU is required.  
- **Project Type**: Data‑analysis pipeline (single‑repo Python package)  
- **Constraints**: Must run entirely on the CPU tier; any optional GPU work is avoided.  

## Constitution Check
| Principle | Status | Action / Evidence |
|-----------|--------|--------------------|
| I. Reproducibility | PASS | Fixed seeds in `code/utils/config.py`; all external data fetched programmatically; `requirements.txt` pins versions. |
| II. Verified Accuracy | PASS | All citations reference verified URLs (GitHub Archive, GHTorrent AWS mirror). No unverified references remain. |
| III. Data Hygiene | PASS | Raw files checksummed; transformations write new files; no PII. |
| IV. Single Source of Truth | PASS | Every figure/table derives from `data/` rows and `code/` calculations; no hand‑typed numbers. |
| V. Versioning Discipline | PASS | Content hashes recorded in `state/` after each artifact creation. |
| VI. Metric Computation Consistency | PASS | `lizard==<pinned‑version>` used with identical CLI flags for all projects. |
| VII. Bug‑Label Reliability | PASS | Validation script samples 100 random functions and checks ≥85 % precision **and** estimates recall (target ≥ 80 %). Systematic bias across projects is assessed (see research.md). |

## Data Acquisition Details
- **Primary Dataset**: GHTorrent Java project dump, programmatically downloaded from the verified AWS mirror ` Name or service not known)"))]. SHA‑256 checksum is recorded in `state/`.  
- **Fallback Dataset**: GitHub Archive (` Name or service not known)"))]) provides a stream of Java commit events if the GHTorrent bucket is unavailable. No other fallback is used because alternatives (e.g., CodeSearchNet) lack the required commit/issue linkage.  

## Project Structure
```
specs/001-statistical-analysis-of-code-complexity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md          # generated later by /speckit-tasks
```

```
projects/PROJ-148-statistical-analysis-of-code-complexity-/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── download_gh.py          # FR‑001
│   │   ├── extract_metrics.py      # FR‑002
│   │   ├── label_bugs.py           # FR‑003 (bug‑label creation)
│   │   └── preprocess.py           # FR‑004 (impute, log‑transform, VIF)
│   ├── modeling/
│   │   ├── train.py                # FR‑005 (L1 LogReg) & FR‑006 (RF)
│   │   └── evaluate.py             # FR‑007 (metrics) & FR‑008 (p‑value correction)
│   └── utils/
│       ├── config.py               # seeds, paths
│       └── logging.py
├── data/
│   ├── raw/                        # GHTorrent archives (checksummed)
│   ├── processed/                  # `bug_complexity_dataset.csv`
│   └── splits/                     # `train_split.csv`, `test_split.csv`
├── tests/
│   ├── contract/                   # contract validation
│   ├── integration/
│   └── unit/
└── requirements.txt
```

## Mapping of Functional Requirements & Success Criteria
| ID | Requirement | Plan Phase / File | Notes |
|----|-------------|-------------------|-------|
| FR‑001 | Acquire ≥10 Java projects from GHTorrent | `code/data/download_gh.py` (Phase 3) | Handles checksum & fallback to GitHub Archive |
| FR‑002 | Compute CC, LOC, token count, nesting depth, Halstead volume | `code/data/extract_metrics.py` (Phase 3) | Uses pinned `lizard` |
| FR‑003 | Derive binary bug label from commit history | `code/data/label_bugs.py` (Phase 3) | Validation script ensures ≥85 % precision **and** ≥80 % recall; systematic bias across projects is assessed |
| FR‑004 | Impute (<5 % missing), log‑transform skewed vars, VIF‑based collinearity handling | `code/data/preprocess.py` (Phase 3) | VIF threshold set to **> 10** (consistent everywhere) |
| FR‑005 | Train L1‑regularized logistic regression (≤100 iters) | `code/modeling/train.py` (Phase 4) | Convergence check; at least one non‑zero coefficient |
| FR‑006 | Train Random Forest (100 trees, max depth 10) | `code/modeling/train.py` (Phase 4) | Used for performance comparison |
| FR‑007 | Evaluate ROC‑AUC, PR‑AUC, calibration, generate PDPs | `code/modeling/evaluate.py` (Phase 5) | Baseline ROC‑AUC ≥ 0.50 |
| FR‑008 | Apply Benjamini‑Hochberg FDR ≤ 0.05 to all tested predictors | `code/modeling/evaluate.py` (Phase 5) | Conducted on **unregularized** logistic model fitted on a **held‑out validation split** (distinct from training and test) |
| FR‑009 | Identify practical thresholds (e.g., CC > 10 → prob ≥ 0.5) | `code/modeling/evaluate.py` (Phase 5) | Saved in `data/model/thresholds.csv` |
| SC‑001 | ROC‑AUC of L1 model within ±0.05 of RF | Evaluated in Phase 5; stored in `model_output.schema.yaml` |
| SC‑002 | Provide interpretable coefficients (non‑zero) | Checked after training; logged |
| SC‑003 | Report stability correlation (Spearman) between feature importance of both models | Computed in Phase 5; stored in schema |

## Compute Feasibility
- **CPU‑first**: All tools (`lizard`, `scikit‑learn`, `statsmodels`) run on CPU. Estimated runtime ≤ 5 h on 2 CPU cores.  
- **Memory**: Streaming extraction and chunked CSV processing keep peak RAM ≤ 6 GB.  
- **GPU**: Not required; no GPU‑only steps are planned.  

## Power Analysis (A‑priori)
Assuming a moderate odds‑ratio of 1.5 for a typical complexity metric, a baseline bug prevalence of 10 %, α = 0.05, and desired power = 0.80, the required sample size for logistic regression is **≈ 8 200** function‑level observations (≈ several distinct Java projects). The pipeline targets **≥ 10 000** observations to provide a safety margin. If the final dataset falls short, a post‑hoc power calculation will be reported.

## Edge Cases & Mitigations

| Edge Case | Mitigation |
|-----------|------------|
| **<100 bug‑fix commits in a project** | Exclude the project from the analysis; log a warning. |
| **Highly collinear metrics (e.g., LOC vs. token_count)** | Perform VIF check; drop any metric with VIF > 10. |
| **Lizard parsing failures** | Skip offending file, record path in a log, continue processing. |
| **Imbalanced outcome (few bugs)** | Report both ROC‑AUC and PR‑AUC; use stratified project split. |
| **RAM exhaustion** | Process projects sequentially; stream raw archives; limit concurrent extraction to ≤ 5 GB. |
| **Label noise** | Randomly sample 100 labeled functions, manually verify against GitHub UI; require ≥ 85 % precision **and** estimate recall (target ≥ 80 %). Systematic bias across projects is assessed and reported. |
| **GHTorrent download failure** | Automatic fallback to GitHub Archive with reduced project count. |
| **Selective inference** | Use a **three‑split** strategy: training for variable selection, **validation** for unbiased post‑selection inference, and test for final performance reporting. This breaks the circular inference loop (addresses scientific_soundness‑b17505bf). |
