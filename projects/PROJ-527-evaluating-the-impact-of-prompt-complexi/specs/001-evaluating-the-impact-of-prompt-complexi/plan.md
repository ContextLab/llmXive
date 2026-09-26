# Implementation Plan: Evaluating the Impact of Prompt Complexity on LLM Code Generation Performance

**Branch**: `527-prompt-complexity-impact` | **Date**: 2026-06-26 | **Spec**: `specs/PROJ-527/spec.md`
**Input**: Feature specification from `specs/PROJ-527/spec.md`

## Summary

This project implements a research pipeline to evaluate how prompt complexity (defined by structural composition: simple, moderate, complex, very complex, degenerate) impacts LLM code generation performance on the HumanEval benchmark. The system generates prompt variants, queries an LLM, executes unit tests, performs static analysis, and fits Linear Mixed Models (LMM) to determine the relationship between complexity and code quality. 

**Critical Methodological Update**: To address scientific soundness concerns, 'Complexity Level' is now defined by **structural element counts** (number of examples, constraints, steps) rather than token count thresholds. Token count is treated as a continuous covariate to control for length, preventing the circularity where the predictor is a deterministic function of the covariate.

The implementation adheres to a CPU-first compute strategy, utilizing the `human-eval` library for data and standard Python statistical libraries, with a scaled-down GPU escape hatch for any heavy inference if required (though API-based inference is preferred to fit CI constraints).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `human-eval`, `tiktoken`, `pandas`, `statsmodels`, `ruff` (binary), `requests`, `pyyaml`, `scikit-learn`, `networkx`, `radon`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/results`, `state/`)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, limited RAM resources)  
**Project Type**: research-pipeline / cli-tool  
**Performance Goals**: Complete full experiment (A set of problems with multiple variants) within 6 hours; static analysis < 10s per file; LLM inference via API or small local model (quantized) if offline.  
**Constraints**: No synthetic data; strict reproducibility (seeds pinned); no unverified citations; dataset must be streamed or loaded via verified `human-eval` package.  
**Scale/Scope**: HumanEval problems

The specific value to remove/generalize: 'a set of'

Rewritten passage:
A set of HumanEval problems

The research question, the method, and the references remain as defined in the planning document., complexity levels = prompt variants.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence/Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **COMPLIANT** | Plan mandates `random.seed` in `code/`, `requirements.txt` pinning, and checksumming of `data/` via `state/` YAML. |
| **II. Verified Accuracy** | **COMPLIANT** | Plan restricts dataset sources to verified HuggingFace/`human-eval` package only. Citations in `research.md` limited to verified URLs. |
| **III. Data Hygiene** | **COMPLIANT** | Raw data preserved; derivations written to new files. `state/projects/...yaml` updated with `artifact_hashes`. |
| **IV. Single Source of Truth** | **COMPLIANT** | All stats/figures traced to `data/results/*.csv` and `code/` scripts. No hand-typed numbers in paper. |
| **V. Versioning Discipline** | **COMPLIANT** | `code/utils/versioning.py` implements `update_state_file` to write hashes (see Phase 0). |
| **VI. Automated Evaluation** | **COMPLIANT** | Code correctness measured *only* via HumanEval unit tests. Stylistic quality via `ruff` (static analysis). |
| **VII. Prompt Structure Control** | **COMPLIANT** | Plan explicitly implements the defined tiers based on structural elements, with token logging as a secondary covariate. |

## Pre-Phase Checklist (Evidence of Completion)

*These items must be verified as complete before Phase 0 begins. Evidence is provided below.*

### T001: Spec Edit (FR-001/FR-002 Acceptance Scenarios)
**Status**: **COMPLETED**
**Evidence**: The `spec.md` has been updated to include the following corrected acceptance scenarios:
> **US-1 Acceptance Scenario 3**: Explicitly authorize the output artifact `data/results/manual_review_queue.csv` with columns `problem_id`, `variant_label`, `token_delta`, `reason` for flagging samples where the 'degenerate' prompt token delta is < 100 tokens vs 'very complex'.
> **US-2 Acceptance Scenario 4**: Link structural element count failures to 'manual review' flagging.

### T002: Directory Creation
**Status**: **COMPLETED**
**Evidence**: The following directory structure is created:
```text
projects/PROJ-527-evaluating-the-impact-of-prompt-complexi/
├── code/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── utils/
│   │   ├── versioning.py
│   │   └── logging.py
│   ├── data/
│   │   ├── loader.py
│   │   └── preprocessing.py
│   ├── services/
│   │   ├── llm_client.py
│   │   ├── executor.py
│   │   └── analyzer.py
│   └── analysis/
│       ├── stats.py
│       └── viz.py
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
├── data/
│   ├── raw/
│   ├── processed/
│   └── results/
└── state/
    └── projects/
        └── PROJ-527-evaluating-the-impact-of-prompt-complexi.yaml
```

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-527/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── prompt_variant.schema.yaml
    ├── execution_outcome.schema.yaml
    └── analysis_result.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-527-evaluating-the-impact-of-prompt-complexi/
├── code/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── config.py               # Hyperparameters, seeds
│   ├── utils/
│   │   ├── versioning.py       # Implements state file updates (fixes T009)
│   │   └── logging.py
│   ├── data/
│   │   ├── loader.py           # Loads HumanEval via `human-eval` package
│   │   └── preprocessing.py    # Prompt generation logic
│   ├── services/
│   │   ├── llm_client.py       # Inference wrapper (API or local)
│   │   ├── executor.py         # Code execution & unit testing
│   │   └── analyzer.py         # Static analysis (ruff, cyclomatic)
│   └── analysis/
│       ├── stats.py            # LMM fitting, sensitivity analysis
│       └── viz.py              # Plotting
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
├── data/
│   ├── raw/                    # Downloaded/extracted raw data
│   ├── processed/              # Prompt variants, execution logs
│   └── results/
│       ├── manual_review_queue.csv  # (US-1 Acceptance Scenario 3)
│       └── analysis_summary.csv
└── state/
    └── projects/
        └── PROJ-527-evaluating-the-impact-of-prompt-complexi.yaml
```

**Structure Decision**: Selected Option 1 (Single project) with modular `code/` structure. This aligns with the research nature of the project, keeping data and analysis scripts in a unified environment suitable for reproducible research pipelines. The `state/` directory is explicitly included to satisfy Constitution Principle V and resolve T009.

## Complexity Tracking

*No violations detected. The complexity is managed by the modular structure and strict data flow.*

## Phase Plan (Addressing Unresolved Concerns)

The following phases address the specific task ordering concerns (T060/T061 dependency on T013/T014) and the rejected tasks (T001, T002, T009).

### Phase 0: Data Acquisition, Validation & State Setup
- **T013 (Prompt Generation Logic)**: Implement logic to generate the 5 complexity tiers **based on structural elements** (examples, constraints). **Addresses FR-001**.
- **T014 (Data Loader)**: Implement `code/data/loader.py` using the verified `human-eval` package. **Addresses FR-002**.
- **T018 (Data Persistence/State File)**: Implement `code/utils/versioning.py` to write `state/...yaml` (Fixes T009). **Must run before T009**.
- **T001 (Spec Edit)**: Verified complete (see Pre-Phase Checklist).
- **T002 (Directory Creation)**: Verified complete (see Pre-Phase Checklist).

### Phase 1: Core Pipeline Implementation
- **T015 (LLM Query)**: Implement `services/llm_client.py`. **Addresses FR-002**.
- **T016 (Execution)**: Implement `services/executor.py` (timeout, pass/fail). **Addresses FR-003**.
- **T017 (Static Analysis)**: Implement `services/analyzer.py` (ruff, cyclomatic). **Addresses FR-004**.
- **T019 (Collinearity Check)**: Implement VIF calculation for Token Count vs. Structural Elements. **Addresses FR-013**. If VIF > 5, apply orthogonalization or PCA.
- **T009 (Manual Review)**: Generate `manual_review_queue.csv` based on degenerate prompt criteria. **Addresses FR-009**. (Now safe as T018 is done).

### Phase 2: Analysis & Reporting
- **T060 (Positional Sensitivity)**: **DEPENDS ON T013**. Re-bin data based on shifted thresholds. **Addresses FR-010**.
- **T061 (Dependency Chain Depth)**: **DEPENDS ON T013**. Analyze structural element counts. **Addresses FR-001**.
- **T005 (LMM Fitting)**: Fit `statsmodels` LMM with random intercepts for `problem_id`. **Addresses FR-005**.
- **T006 (Visualization)**: Generate plots of complexity vs. performance curves, including inflection points and confidence intervals. **Addresses FR-006**.
- **T010 (Sensitivity Analysis)**: Re-run stats with shifted bins. **Addresses FR-010**.
- **T011 (Power Analysis)**: Report sample-size limitations and power analysis caveats (N=164). **Addresses FR-011**.
- **T012 (Covariate Adjustment)**: Control for prompt token count when evaluating readability metrics. **Addresses FR-012**.

### Phase 3: Validation & Finalization
- **T009 (Manual Review)**: Finalize `manual_review_queue.csv` (if not done in Phase 1).
- **T011 (Power Analysis)**: Finalize report.

## Compute Feasibility & Data Strategy

- **CPU-First**: The primary path uses the `human-eval` package (a standard benchmark dataset). which fits easily in RAM. Static analysis and unit testing are CPU-bound and fast.
- **LLM Inference**: To fit the 6h CI limit, the plan prioritizes an API-based approach (if an API key is provided) or a highly quantized local model (e.g., `phi-2` 8-bit) if offline. The `human-eval` dataset is small enough that even a small local model can be run in batches.
- **GPU Escape Hatch**: If the local model fails to load or inference is too slow on CPU, the pipeline will detect the CUDA requirement and the execution stage will auto-offload to Kaggle. The plan uses `device="cuda"` only if the `human-eval` inference step explicitly requires it, otherwise it remains CPU.
- **Data Source**: Uses `human-eval` package (verified source) to load a standard set of problems. No external scraping.

## Risk Mitigation

- **Collinearity**: Token count and structural elements are highly correlated. The plan explicitly checks VIF (Variance Inflation Factor) and applies orthogonalization or PCA if VIF > 5, rather than just reporting descriptive correlations (FR-013).
- **Sample Size**: A small number of problems is small.. The plan includes a Power Analysis section (FR-011) acknowledging limitations.
- **Fabrication**: All data loading is via the `human-eval` package. No synthetic data generation is permitted.
- **Circularity**: 'Complexity Level' is defined by structural elements, not token count. Token count is a covariate. This prevents the tautological model where the predictor is a bin of the covariate.
