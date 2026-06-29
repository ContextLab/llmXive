# Implementation Plan: 001-code-generation-performance-outcomes

**Branch**: `001-code-generation-performance-outcomes` | **Date**: 2024-01-15 | **Spec**: `specs/001-code-generation-performance-outcomes/spec.md`
**Input**: Feature specification from `/specs/001-code-generation-performance-outcomes/spec.md`

## Summary

This feature implements a statistical analysis pipeline to evaluate the impact of LLM‑assisted code generation on developer task completion time and code quality, stratified by experience level. The core methodology is a **two‑way ANCOVA (ANOVA with covariates)** with interaction terms, effect‑size reporting, family‑wise error correction, and a sensitivity analysis on experience‑level thresholds. All findings are explicitly labeled **associational**.

**Critical Blocking Issue**: The spec references "OpenDev benchmark" and "GitHub Copilot adoption studies" as data sources, but **no verified developer‑productivity datasets containing the required variables are present in the project's verified‑datasets block**. The pipeline will **halt** until such datasets are added (see *Dataset Acquisition Strategy* below). Without verified data, FR‑001 and FR‑011 cannot be satisfied, and Principle I (Reproducibility) remains pending.

**Statistical Methodology Note**: While FR‑003 states "two‑way ANOVA", the implementation uses **ANCOVA** when continuous covariates (task_complexity, team_size) are available. This is a spec‑to‑implementation mismatch that requires FR‑003 revision in spec.md to reflect ANCOVA methodology or explicitly state conditional fallback to ANOVA when covariates are absent.

## Technical Context

- **Language/Version**: Python 3.11  
- **Primary Dependencies** (pinned in `code/requirements.txt`):
  - pandas>=2.0.0
  - numpy>=1.24.0
  - scipy>=1.11.0
  - scikit-learn>=1.3.0
  - matplotlib>=3.7.0
  - pyyaml>=6.0
- **Statistical Parameters** (specified prior to execution per Constitution Principle VI):
  - Alpha (family‑wise) = 0.05  
  - Desired power = 0.80 (medium effect, Cohen's d = 0.5)  
  - Minimum observations per experience stratum = 30 (power‑flagged if < 30)  
- **Compute Feasibility**: All methods are CPU‑only; expected runtime ≤ 4 h on GitHub Actions free‑tier (2 CPU, ~7 GB RAM, ~14 GB disk). No GPU or large‑model dependencies.

## Dataset Acquisition Strategy

| Step | Action |
|------|--------|
| 1 | Search for publicly available developer‑productivity datasets that contain **tool_usage**, **task_time**, **defect_rate**, **experience_years**, and optional confounders (**task_complexity**, **project_type**, **team_size**). |
| 2 | Verify each candidate dataset via the Reference‑Validator Agent; record its SHA‑256 checksum in `state/projects/PROJ-462.../artifacts.yaml`. |
| 3 | Add the verified URL(s) to the project's "# Verified datasets" block. |
| 4 | If no suitable dataset can be located, the pipeline aborts with a clear error and the project must revisit the research question. |

Only after successful completion of Step 4 does the pipeline proceed to the remaining phases.

## Constitution Check

| Constitution Principle | Compliance Status | Implementation Action |
|------------------------|-------------------|----------------------|
| I. Reproducibility | **PENDING** – blocked until verified dataset added | Dataset download & checksum validation will guarantee reproducibility once data are available. |
| II. Verified Accuracy | ✅ PASS | All citations are validated by the Reference‑Validator. |
| III. Data Hygiene | ✅ PASS | Checksums recorded; no in‑place modifications. |
| IV. Single Source of Truth | ✅ PASS | All figures and tables trace back to a single row in `data/` and a single code block. |
| V. Versioning Discipline | ✅ PASS | Content hashes stored in `state/projects/.../artifacts.yaml`. |
| VI. Statistical Validity | ✅ PASS | Alpha = 0.05, power = 0.80, effect‑size target = 0.5 specified in Technical Context (not deferred). |
| VII. Experience Stratification Integrity | ✅ PASS | Classification thresholds are version‑controlled in `code/analysis/experience.py`. |

## Project Structure

```text
specs/001-code-generation-performance-outcomes/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   └── analysis.schema.yaml
code/
├── __init__.py
├── requirements.txt
├── ingest/
│   ├── download.py          # FR-001: download + checksum
│   └── validate.py          # FR-002, FR-010
├── analysis/
│   ├── anova.py             # FR-003, FR-011 (ANCOVA when covariates present)
│   ├── effect_sizes.py      # FR-004
│   └── sensitivity.py       # FR-009
├── viz/
│   └── plots.py             # FR-007
├── export/
│   └── results.py           # FR-008
└── main.py                  # Orchestrates pipeline + contract validation
data/
├── raw/
├── processed/
└── output/
tests/
├── contract/
│   ├── test_dataset_schema.py
│   └── test_analysis_schema.py
├── integration/
│   └── test_pipeline.py
└── unit/
    ├── test_anova.py
    └── test_effect_sizes.py
state/projects/PROJ-462-evaluating-the-impact-of-code-generation/
└── artifacts.yaml
```

## Phase Overview (ordered)

| Phase | Description | FR / SC addressed |
|-------|-------------|-------------------|
| 0 | **Dataset Acquisition** – download, checksum, verify variable presence. | FR‑001, FR‑002, FR‑010 |
| 1 | **Contract Validation** – validate raw and processed files against `dataset.schema.yaml`. | (new) |
| 2 | **Statistical Modeling** – ANCOVA (or ANOVA if covariates absent) with interaction, covariate control, VIF diagnostics, power flagging. | FR‑003, FR‑004, FR‑005, FR‑011, SC‑001, SC‑002, SC‑003, SC‑006, SC‑008 |
| 3 | **Effect‑Size & Multiple‑Comparison** – compute Cohen's d, apply Holm‑Bonferroni. | FR‑004, FR‑005, SC‑003, SC‑004 |
| 4 | **Sensitivity Analysis** – sweep experience thresholds (1, 2, 3 years). | FR‑009, SC‑005 |
| 5 | **Visualization** – boxplots with interaction lines. | FR‑007 |
| 6 | **Export** – CSV & JSON of all results + metadata. | FR‑008 |
| 7 | **Final Contract Check** – validate `analysis.schema.yaml` against `data/output/analysis.json`. | (new) |

All phases respect the compute limits of the GitHub Actions free tier.

## Edge‑Case Handling (already in plan)

- Missing experience data → filtered, % removed reported, flag if > 20 % (FR‑010).  
- Skewed outcome distributions → Welch's ANOVA fallback (methodology note).  
- Small stratum size (< 30) → power flag raised, effect sizes interpreted cautiously (SC‑006).  
- Collinearity → VIF computed; warning if VIF > 5 (SC‑008).  
- Missing confounders → model drops absent covariates; optional propensity‑score matching noted (FR‑011 fallback).  

--- 

## References

All external citations are verified via the Reference‑Validator Agent per Constitution Principle II.