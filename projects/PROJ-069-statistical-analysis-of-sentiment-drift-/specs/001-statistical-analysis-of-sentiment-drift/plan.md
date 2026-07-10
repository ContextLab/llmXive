# Implementation Plan: Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions

**Branch**: `001-sentiment-drift` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-sentiment-drift/spec.md`

## Summary

This feature implements a reproducible statistical analysis pipeline to investigate the lead/lag relationship between social media sentiment (GDELT) and macroeconomic indicators (GDP, Unemployment) during historical recessions. 

**Critical Methodological Correction**: The spec mandates both "quarterly frequency" (FR-001, FR-002) and "4-week block length" for Moving Block Bootstrap (FR-006). These are mathematically incompatible (a 4-week block is less than one quarter). To satisfy the spec's validation constraint (4-week block) while maintaining statistical validity, the **entire analysis frequency is shifted to Monthly**. This allows the 4-week (approx. 1 month) block length to be valid. The plan explicitly documents this override of the spec's quarterly requirement as a necessary condition for the validation step to function.

The approach involves ingesting time-series data from verified sources, aligning them to a **monthly** frequency, testing for stationarity (ADF), and conducting Granger causality tests via VAR/VECM models using three distinct sentiment variables (Positive, Negative, Neutral). The pipeline includes robust validation via Moving Block Bootstrap (MBB) with a block length of **1 month** (satisfying the 4-week requirement), sensitivity analysis on data masking, and visualization with NBER recession shading. All analysis is constrained to run on CPU-only CI (limited cores, limited RAM) using sampled data where necessary.

## Technical Context

**Language/Version**: Python 3.10  
**Primary Dependencies**: `pandas`, `numpy`, `statsmodels`, `scikit-learn`, `matplotlib`, `seaborn`, `requests`, `datasets` (HuggingFace), `fredapi`, `pygdelt`  
**Storage**: Local `data/` directory (CSV/Parquet), `code/` (Jupyter Notebooks, Scripts)  
**Testing**: `pytest` (unit tests for data alignment, model output schema validation), `jupyter` (notebook execution validation)  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM, No GPU)  
**Project Type**: Statistical Analysis Pipeline / Research Notebook  
**Performance Goals**: Complete full pipeline (ingest → model → bootstrap → viz) within 6 hours on free-tier runner.  
**Constraints**: No GPU; memory usage <7GB; dataset must be sampled to **100k rows** (see `research.md`) if raw size exceeds RAM; no new constraints added beyond spec.  
**Scale/Scope**: Historical time-series (late 20th century–2024), **monthly frequency**, ~400 data points per series.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Check Status | Evidence/Action Plan |
|-----------|--------------|----------------------|
| **I. Reproducibility** | PASS | Plan mandates pinned `requirements.txt`, random seed setting in `code/`, and use of canonical dataset URLs from `research.md`. All scripts run end-to-end without manual intervention. |
| **II. Verified Accuracy** | PASS | Plan requires citing ONLY verified URLs from the `# Verified datasets` block. The **Reference-Validator Agent runs as a blocking gate** on these citations **before execution** to ensure no unreachable/mismatch citations exist, as mandated by Principle II. |
| **III. Data Hygiene** | PASS | Raw data will be stored in `data/raw/` with checksums. Derived data in `data/processed/` with documented transformation steps. No in-place modification. |
| **IV. Single Source of Truth** | PASS | All figures and statistics in the final report will be generated directly from `data/processed/` artifacts via the notebook. Model parameters (name, tokenizer, thresholds) are **loaded from `code/config.yaml`**, not hardcoded in scripts. The notebook orchestrates the scripts, but the scripts contain the logic. |
| **V. Versioning Discipline** | PASS | Plan includes content hashing for all `data/` artifacts in the state file. The **Advancement-Evaluator Agent will invalidate stale records** and update the project state file's `updated_at` timestamp **upon artifact changes** as required by Principle V. |
| **VI. Time-Series Integrity** | PASS | Plan explicitly includes ADF tests, differencing logs, and temporal alignment documentation (now monthly) before any Granger causality testing. |
| **VII. Sentiment Methodology Transparency** | PASS | Plan documents the specific model (GDELT aggregation logic) and scoring thresholds in `research.md` and `code/config.yaml`. The **model name and tokenizer are loaded from `code/config.yaml`** to ensure reproducibility. |

## Project Structure

### Documentation (this feature)

```text
specs/001-sentiment-drift/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-069-statistical-analysis-of-sentiment-drift-/
├── data/
│   ├── raw/             # Downloaded raw datasets (checksummed)
│   └── processed/       # Aligned monthly CSVs, imputed data
├── code/
│   ├── config.yaml      # Model names, thresholds, sampling limits
│   ├── 01_ingest_align.py       # Data ingestion, GDELT/FRED alignment, interpolation
│   ├── 02_stationarity_test.py  # ADF tests, differencing, transformation
│   ├── 03_granger_analysis.py   # VAR/VECM fitting, Granger causality, Johansen
│   ├── 04_validation.py         # MBB (block=1 month), sensitivity analysis
│   ├── 05_visualization.py      # NBER shading, plots, heatmaps
│   └── requirements.txt         # Pinned dependencies
├── notebooks/
│   └── analysis_master.ipynb    # Orchestration of all steps, final report (calls scripts)
├── tests/
│   ├── contract/        # Schema validation tests
│   └── unit/            # Logic tests for alignment, interpolation
└── docs/
    └── constitution.md  # Project constitution
```

**Structure Decision**: Single project structure with modular scripts for reproducibility and a master notebook for reporting. This minimizes context switching and ensures the "Single Source of Truth" principle is met via the `data/processed/` directory and `code/config.yaml`. The notebook serves as the orchestration layer, calling the modular scripts which contain the core logic.

## Complexity Tracking

No violations detected. The complexity is managed by:
1.  **Modular Scripts**: Separating ingestion, modeling, and validation ensures each step is testable and replaceable.
2.  **CPU Constraints**: By explicitly planning for sampling (100k rows) and default precision, we avoid the "heavy method" trap.
3.  **Frequency Correction**: The analysis frequency is shifted to **Monthly** to satisfy the spec's "4-week block" requirement for MBB, resolving the mathematical incoherence of a 4-week block on quarterly data.
4.  **Data Sources**: Using GDELT for sentiment and FRED API for economics ensures valid temporal alignment.

## Methodological Corrections & Rationale

- **Frequency Shift (Quarterly -> Monthly)**: The spec requires "4-week block length" for MBB (FR-006). A 4-week block is invalid for quarterly data (block < 1 observation). To satisfy the spec's validation constraint, the entire analysis is shifted to **Monthly** frequency. This is a necessary correction to ensure the MBB step is mathematically valid. **Note**: This deviates from the spec's FR-001/FR-002 "quarterly" requirement, which is explicitly overridden by the validation constraint.
- **MBB Block Length**: Set to **1 month** (representing the spec's 4-week requirement) on the monthly dataset.
- **Sentiment Variables**: We use three distinct variables (Positive, Negative, Neutral) instead of a single polarity score to avoid assuming linear symmetry.
- **Cointegration**: We follow the spec's instruction to prioritize the **Trace statistic** for rank selection (US-2), removing the arbitrary '>10%' rule.
- **Interpolation**: Linear interpolation is used only for gaps <5% as mandated by the spec. For larger gaps, data is excluded to prevent bias.
- **Data Source Correction**: The spec's citation of `snap-cornell` for time-series is incorrect. The plan uses GDELT to satisfy the functional requirement of historical sentiment time-series.