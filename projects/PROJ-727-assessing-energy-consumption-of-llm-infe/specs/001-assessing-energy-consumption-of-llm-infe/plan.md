# Implementation Plan: Assessing Energy Consumption of LLM Inference

## 1. Project Overview

This project implements an automated pipeline to assess the energy consumption of LLMs (GPT-2-small, CodeBERT, StarCoder-1B) on the HumanEval dataset.

## 2. Architecture

- **Language**: Python 3.10+
- **Core Libraries**: `transformers`, `torch` (CPU), `codecarbon`, `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`
- **Data Source**: HumanEval (via `human_eval` package or direct download)
- **Execution**: Sequential model loading to manage RAM constraints.

## 3. Feasibility Notes & Amendments

### RAM Constraints and Model Substitution
The initial plan proposed evaluating "StarCoder-base" (15B parameters). However, on the target CPU-only execution environment with limited RAM, loading a 15B model is infeasible and will result in Out-of-Memory (OOM) failures.

**Amendment (FR-001)**:
- **Original**: StarCoder-base
- **Replaced With**: StarCoder-1B
- **Justification**: StarCoder-1B is small enough to fit in available RAM while still providing a meaningful data point for the "larger model" category in the comparative analysis. This substitution is authorized and required for the pipeline to complete successfully.

## 4. Execution Phases

### Phase 1: Setup
- Initialize project structure.
- Configure dependencies (`requirements.txt`).
- Set up linting and formatting.

### Phase 2: Foundational
- **Critical**: Update `spec.md` and `plan.md` to reflect StarCoder-1B substitution (Task T005a).
- Create configuration constants (`code/config.py`).
- Download HumanEval dataset.
- Implement calibration and versioning.

### Phase 3: User Story 1 (Inference)
- Implement `code/inference.py` to run models sequentially.
- Use `codecarbon` for energy tracking.
- Generate `data/processed/energy_results_raw.csv`.

### Phase 4: User Story 2 (Analysis)
- Implement statistical tests (ANOVA, Tukey, Regression).
- Perform sensitivity analysis.
- Generate `data/processed/stats_report.csv`.

### Phase 5: User Story 3 (Visualization)
- Generate plots.
- Save to `data/processed/`.

## 5. Risk Management

- **OOM Errors**: Mitigated by using StarCoder-1B and explicit garbage collection (`gc.collect()`) between model loads.
- **CodeCarbon Accuracy**: Mitigated by calibration task (T006) ensuring CPU load detection works.
- **Data Integrity**: Enforced by requiring real HumanEval data and real measurements; no synthetic data allowed.

## 6. Deliverables

- `data/processed/energy_results_aggregated.csv`
- `data/processed/stats_report.csv`
- `data/processed/energy_bar.png`
- `data/processed/tradeoff_scatter.png`
- `data/processed/sensitivity_delta.csv`