# Implementation Plan: Measuring the Carbon Footprint of LLM‑Assisted Code Generation

**Branch**: `001-carbon-footprint-llm-code` | **Date**: 2026-06-26 | **Spec**: `specs/001-carbon-footprint-llm-code/spec.md`
**Input**: Feature specification from `/specs/001-carbon-footprint-llm-code/spec.md`

## Summary

This project implements a computational study to measure and compare the carbon footprint of LLM-assisted code generation against a **Theoretical Human Reference Energy Model**. The system downloads prompts from the CodeXGLUE dataset (with a strict **Verified Fallback Protocol** if the canonical source is unreachable/unverified), runs inference using GPT-2-medium and DistilGPT-2 on a CPU-only environment while instrumenting energy usage with CodeCarbon, estimates human baseline emissions based on a standardized laptop power model and task duration, and performs statistical analysis (One-Sample T-Test or Wilcoxon) to determine if the LLM's energy cost deviates significantly from the theoretical reference. The output is a reproducible markdown report with statistical rigor, robustness checks, and limitations.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets`, `transformers`, `codecarbon`, `scikit-learn`, `pandas`, `matplotlib`, `seaborn`  
**Storage**: Local file system (`data/` for raw/processed data, `output/` for reports)  
**Testing**: `pytest` (contract tests against YAML schemas, unit tests for calculation logic)  
**Target Platform**: GitHub Actions free-tier runner (Linux, multiple CPUs, standard memory allocation, no GPU)  
**Project Type**: computational research pipeline / CLI  
**Performance Goals**: Total runtime ≤ 6 hours, peak RAM ≤ 7 GB, disk usage ≤ 14 GB  
**Constraints**: No GPU usage, no CUDA dependencies, CPU-only model inference, strict memory limits  
**Scale/Scope**: Target a representative subset of prompts from CodeXGLUE (dynamic reduction to 100 if runtime > 4h), model variants (GPT-2-medium, DistilGPT-2)

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Action Plan |
|-----------|--------|------------------------|
| I. Reproducibility | **PASS** | Plan mandates pinned `requirements.txt`, random seed setting, and deterministic data fetching. Includes a **Verified Fallback Protocol** for dataset availability. |
| II. Verified Accuracy | **PASS** | All external citations will be validated. If CodeXGLUE is not in the verified URL list, the pipeline switches to a locally verified subset or a verified alternative (HumanEval/MBPP) to ensure no unverified data enters the study. Human baseline data is synthesized locally to avoid external fetch risks. |
| III. Data Hygiene | **PASS** | Raw data will be checksummed upon download; derivations (e.g., normalized emissions) will be written to new files. PII scan enforced by pipeline. |
| IV. Single Source of Truth | **PASS** | All statistics in the final report will be generated programmatically from the `data/` artifacts, not hand-typed. |
| V. Versioning Discipline | **PASS** | Artifacts will be hashed; the state file will be updated on any change to `data/` or `code/`. |
| VI. Energy Measurement Standardization | **PASS** | CodeCarbon's regional factor will be extracted and applied to the Human Baseline calculation to ensure consistency. |
| VII. Comparative Statistical Rigor | **PASS** | One-Sample T-Test/Wilcoxon implementation with normality checks (Shapiro-Wilk) and effect size calculation (Cohen's d / rank-biserial) is mandated for constant baselines. |

## Project Structure

### Documentation (this feature)

```text
specs/001-carbon-footprint-llm-code/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (created by /speckit-tasks)
```

### Source Code (repository root)

```text
projects/PROJ-726-measuring-the-carbon-footprint-of-llm-as/
├── code/
│   ├── requirements.txt
│   ├── download_data.py        # Fetches CodeXGLUE (with fallback) or loads verified local subset
│   ├── validate_baseline.py    # Validates human baseline data (synthesized locally)
│   ├── run_inference.py        # Runs GPT-2/DistilGPT-2 with CodeCarbon
│   ├── calculate_emissions.py  # Joins LLM results with Human Baseline, calculates co2_per_loc
│   ├── statistical_analysis.py # One-Sample T-Test/Wilcoxon, robustness checks, plots
│   └── generate_report.py      # Produces final markdown report
├── data/
│   ├── raw/                    # Downloaded parquet files (checksummed) or verified local subset
│   ├── processed/              # Normalized emission records, paired datasets
│   └── outputs/                # Final JSON/CSV stats, plots
├── tests/
│   ├── contract/               # Schema validation tests
│   ├── unit/                   # Logic tests for emission calculations
│   └── integration/            # End-to-end pipeline sanity checks
└── output/
    └── report.md               # Final markdown report
```

**Structure Decision**: Single project structure (DEFAULT) selected. The pipeline is linear (download → infer → calculate → analyze → report), making a monolithic `code/` directory with distinct scripts the most maintainable approach for a research study. No complex service decomposition is required.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed all principles. | N/A |