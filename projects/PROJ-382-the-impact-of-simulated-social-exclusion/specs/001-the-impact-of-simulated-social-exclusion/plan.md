# Implementation Plan: The Impact of Simulated Social Exclusion on Subsequent Prosocial Behavior

**Branch**: `001-social-exclusion-prosociality` | **Date**: 2026-07-01 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-social-exclusion-prosociality/spec.md`

## Summary

This project implements a reproducible statistical pipeline to quantify the effect of experimentally induced social exclusion on subsequent prosocial behavior (monetary donation). The approach involves ingesting open behavioral datasets from OSF, validating schemas against strict requirements (`condition`, `prosocial_amount`, `randomized`), and performing a rigorous meta-analysis. The analysis calculates the **Average Marginal Effect (AME)** of exclusion on the *Total Expected Donation* (Probability of Donation × Mean Amount | Donation) to ensure cross-study comparability. The pipeline separates **Causal Pool** (RCTs) and **Associational Pool** (observational) analyses, includes pre-registered search protocols to mitigate selection bias, and performs robustness checks including E-values for unmeasured confounding and small-sample bias corrections.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `pyyaml`, `requests`, `scikit-learn`, `pyyaml`  
**Storage**: Local file system (`data/raw`, `data/processed`), CSV/Parquet formats  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, 7GB RAM)  
**Project Type**: Data Analysis Pipeline / Research Script  
**Performance Goals**: Complete meta-analysis within 6 hours; RAM usage < 6GB; CPU usage < 2 cores.  
**Constraints**: No GPU; no large model training; strict adherence to OSF data availability; no causal claims from non-randomized data.  
**Scale/Scope**: Conditional aggregation of ≥3 valid datasets. **Feasibility Note**: If the pre-registered search yields <3 valid datasets, the pipeline halts with "Insufficient Data" as a valid scientific outcome.  
**Versioning Discipline**: The `state/` file is updated with content hashes of `code/` and `data/` artifacts after every run to satisfy Principle V.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`; external datasets fetched via verified URLs; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | Dataset URLs sourced *only* from the verified list or pre-registered search strings; no invented URLs. |
| **III. Data Hygiene** | **PASS** | Raw data checksummed upon download; transformations produce new files; PII scan enforced. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats trace to `data/processed` and `code/`; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts carry content hashes; `state/` file updated on change; hash of `code/` and `data/` recorded. |
| **VI. Experimental Condition Fidelity** | **PASS** | `condition` variable strictly normalized to binary (0/1) based on exclusion manipulation. **Deterministic Logging**: The exact mapping logic (e.g., 'ignored' -> 1) and raw values are recorded in `data/processed/mapping_log.json` to satisfy Principle VI. |
| **VII. Behavioral Outcome Independence** | **PASS** | `prosocial_amount` treated as a distinct outcome. **Temporal Validation**: The pipeline checks for separate task identifiers/timestamps in raw data (if available) to validate the assumption of temporal separation required by Principle VII. |

## Project Structure

### Documentation (this feature)

```text
specs/001-social-exclusion-prosociality/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-382-the-impact-of-simulated-social-exclusion/
├── code/
│   ├── requirements.txt
│   ├── ingest.py              # OSF download, schema validation, standardization, mapping logging
│   ├── preprocess.py          # Imputation, outlier handling, pool splitting, temporal validation
│   ├── analysis.py            # ZIG/Hurdle models, AME calculation, Meta-analysis, E-values, Bias correction
│   └── main.py                # Orchestration script
├── data/
│   ├── raw/                   # Downloaded CSV/Parquet (checksummed)
│   └── processed/             # Cleaned, standardized dataframes, mapping logs
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── state/
    └── projects/PROJ-382-the-impact-of-simulated-social-exclusion.yaml
```

**Structure Decision**: Single-project structure selected to align with the research pipeline nature (ingest -> process -> analyze). No frontend/backend split required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Zero-Inflated Model** | Donation data is heavily zero-inflated (many non-donors). | Standard OLS or Gamma GLM would fail to model the zero-generation process, biasing effect sizes. |
| **Average Marginal Effect (AME)** | Raw conditional coefficients (log-odds vs log-scale) are incomparable across studies. | Pooling raw coefficients violates meta-analysis homogeneity assumptions; AME provides a unified marginal metric. |
| **Dual Pool Analysis** | Causal claims require randomization; observational data must be separated. | Pooling RCTs and non-RCTs would violate causal inference assumptions and overstate evidence. |
| **Pre-registered Search** | To prevent selection bias in finding datasets. | Unconstrained keyword search risks cherry-picking significant results, invalidating causal claims. |
| **E-Value Calculation** | To test robustness to unmeasured confounding in the Associational Pool. | Standard sensitivity sweeps (link functions) do not address the fundamental identification problem of confounding. |