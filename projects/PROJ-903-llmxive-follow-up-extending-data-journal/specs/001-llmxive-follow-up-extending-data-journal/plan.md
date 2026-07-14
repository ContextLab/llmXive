# Implementation Plan: Counterfactual Inspector Agent

**Branch**: `001-counterfactual-inspector` | **Date**: 2026-07-14 | **Spec**: `specs/001-llmxive-follow-up-extending-data-journal/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-data-journal/spec.md`

## Summary

This feature extends the `llmXive` pipeline with a "Counterfactual Inspector" agent designed to mitigate confirmation bias in automated data journalism. The system generates a baseline narrative based on the strongest statistical correlation, then invokes a dedicated agent to search for and verify alternative causal explanations (counterfactuals) using **partial correlation** and **confounder adjustment** to distinguish spurious correlations from genuine alternative explanations. The final output integrates the baseline and verified counterfactuals into a single, nuanced story with explicit data citations. The implementation prioritizes CPU-only execution on GitHub Actions free-tier runners (≤7 GB RAM, 6h runtime) using lightweight statistical libraries (`pandas`, `scipy`, `pgmpy` for causal graph estimation) and a small local LLM or batched API calls for narrative synthesis.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scipy`, `scikit-learn`, `pgmpy` (for causal structure learning), `transformers` (CPU-optimized), `pydantic`, `pytest`  
**Storage**: Local CSV/Parquet files under `data/`; JSON outputs under `output/`; Dataset registry under `data/registry.yaml`  
**Testing**: `pytest` (unit tests for statistical logic, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data processing pipeline / CLI tool  
**Performance Goals**: Complete analysis of a standard public policy dataset (≤10k rows, 50 columns) within 6 hours on 2 CPU cores, ≤7 GB RAM.  
**Constraints**: No GPU acceleration; no large-LLM fine-tuning; strict adherence to 6-hour runtime and 7 GB RAM limits; all counterfactual claims must be associational unless randomization is explicit; counterfactuals must be robust across thresholds and adjusted for confounders.  
**Scale/Scope**: Processing of **50 verified public policy datasets** defined in `data/registry.yaml` for evaluation; single-dataset execution for user demos. The registry is populated from verified UCI/Kaggle sources matching the "public policy" and "numeric variable" criteria.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| **I. Reproducibility** | PASS | All random seeds pinned in `code/`; datasets fetched from canonical HuggingFace/UCI URLs; `requirements.txt` pins versions; `data/registry.yaml` ensures consistent dataset selection. |
| **II. Verified Accuracy** | PASS | All citations (dataset URLs, statistical methods) validated against primary sources; `Reference-Validator` agent integrated. |
| **III. Data Hygiene** | PASS | Raw data checksummed; no in-place modifications; derived files named with hash suffixes; PII scan enforced. |
| **IV. Single Source of Truth** | PASS | All figures/stats in final output trace to specific `code/` blocks and `data/` rows; no hand-typed numbers. |
| **V. Versioning Discipline** | PASS | Content hashes for all artifacts; `state/` updated on changes; `Advancement-Evaluator` checks for stale records. |
| **VI. Counterfactual Rigor** | PASS | `Counterfactual Inspector` agent logs specific SQL/Python queries; comparative analysis (Baseline vs. Inspector) enforced; causal language restricted to associational claims; **partial correlation and confounder adjustment** implemented to ensure counterfactual validity. **50-dataset registry** explicitly defined in `data/registry.yaml`. |
| **VII. Expert Blinding** | PASS | `code/` implements blinded rubric scoring; metadata stripped; **paired t-test (`scipy.stats.ttest_rel`)** explicitly implemented in `evaluation/rubric.py` to compare Baseline vs. Inspector scores on anonymized data. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-data-journal/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-903-llmxive-follow-up-extending-data-journal/
├── code/
│   ├── __init__.py
│   ├── config.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py          # Fetches verified datasets from registry.yaml (handles 50 datasets)
│   │   └── processor.py       # Imputation, cleaning, partial correlation
│   ├── narrative/
│   │   ├── __init__.py
│   │   ├── baseline.py        # Generates primary narrative (FR-001) + Random Baseline
│   │   ├── inspector.py       # Counterfactual Agent (FR-002, FR-003) with confounder adjustment
│   │   └── synthesizer.py     # Merges baseline + counterfactuals (FR-004)
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── rubric.py          # Expert scoring logic (SC-001) + Statistical tests (scipy.stats.ttest_rel)
│   │   └── bias.py            # Bias mitigation metrics (SC-002)
│   └── main.py                # Entry point for CLI
├── data/
│   ├── raw/                   # Downloaded datasets (checksummed)
│   ├── derived/               # Processed CSVs/Parquets
│   └── registry.yaml          # List of 50 verified public policy datasets (UCI/Kaggle/HF)
├── tests/
│   ├── unit/
│   │   ├── test_processor.py
│   │   ├── test_inspector.py
│   │   └── test_synthesizer.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── contract/
│       └── test_schemas.py
├── output/                    # Generated stories, metrics
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure under `code/` to ensure modularity and testability. Separation of `narrative/` modules isolates the core logic (Baseline, Inspector, Synthesizer) for independent testing and replacement. `evaluation/` handles metrics and scoring, ensuring compliance with SC-001 and SC-002. The `data/registry.yaml` file explicitly defines the 50 datasets required by the Constitution, ensuring traceability.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Partial Correlation & Confounder Adjustment** | Required to distinguish spurious correlations from genuine alternative explanations (Methodology Concerns). | Simple correlation sweeping fails to account for confounders, leading to invalid "counterfactual" claims (e.g., sign flips due to Simpson's Paradox). |
| **Threshold Robustness Check** | Ensures counterfactuals are stable across significance levels, not just noise at low thresholds. | Fixed threshold sweeping treats arbitrary cutoffs as discovery parameters, risking false positives. |
| **Dataset Registry (`registry.yaml`)** | Required to meet Constitutional mandate of 50 datasets and ensure reproducibility. | Hardcoding 50 URLs in code is unmanageable and violates versioning discipline. |
| **Blinded Scoring with Statistical Tests** | Essential for valid evaluation of "Narrative Depth" and "Bias Mitigation". | Unblinded scoring introduces evaluator bias; manual comparison lacks statistical rigor. |
| **Random Baseline Control** | Required to isolate the Inspector's effect from the Baseline's inherent cherry-picking bias. | Comparing only to a Standard Baseline conflates the Baseline's weakness with the Inspector's strength. |

## Dataset Strategy

The system operates on a **Dataset Registry** (`data/registry.yaml`) containing 50 verified public policy datasets. This registry is populated from the "Verified datasets" block in `research.md` and expanded with additional verified sources (e.g., UCI, Kaggle) that meet the "public policy" and "numeric variable" criteria. The `loader.py` module reads this registry, validates each dataset (numeric column count ≥ 5, row count ≥ 30), and proceeds only if valid. Datasets failing validation are skipped and logged.

**Registry Expansion Plan**:
1.  Start with several verified datasets (California Housing, Crime and Communities, etc.).
2.  Script to scan UCI Machine Learning Repository and Kaggle for "public policy" tags.
3.  Filter for datasets with ≥5 numeric columns and ≥30 rows.
4.  Add verified URLs to `data/registry.yaml` until 50 are reached.
5.  All datasets must be checksummed and validated before inclusion.

## Execution Order

1.  **Phase 0**: Data Loading & Validation (Check 50 datasets).
2.  **Phase 1**: Baseline Generation (Standard & Random).
3.  **Phase 2**: Counterfactual Inspector (Partial Correlation, Confounder Adjustment, Robustness Sweep).
4.  **Phase 3**: Synthesis & Integration.
5.  **Phase 4**: Evaluation (Blinded Scoring, Statistical Tests).
6.  **Phase 5**: Reporting.
