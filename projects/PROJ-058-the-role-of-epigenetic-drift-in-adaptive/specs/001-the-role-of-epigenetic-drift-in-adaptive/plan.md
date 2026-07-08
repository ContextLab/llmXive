# Implementation Plan: The Role of Epigenetic Drift in Adaptive Landscape Exploration

**Branch**: `001-role-of-epigenetic-drift` | **Date**: 2026-07-08 | **Spec**: `specs/001-role-of-epigenetic-drift/spec.md`
**Input**: Feature specification from `/specs/001-role-of-epigenetic-drift/spec.md`

## Summary

This project investigates the **associational strength** between multi-generational epigenetic variance (methylation) and gene expression variance (RNA-seq) in model organisms (mouse, C. elegans, Drosophila) under fluctuating environmental conditions. **Crucially, this study is observational and cannot establish causality.** The hypothesis is reframed to test for a statistical association rather than a "primary driver" mechanism.

The technical approach involves:
1.  **Data Discovery**: Querying public repositories (GEO/ENCODE) via verified dataset sources to identify ≥3 matched multi-generational datasets. **If no such datasets exist in the verified sources, the pipeline halts with a "Data Unavailable" status.**
2.  **Preprocessing**: Normalizing RNA-seq and methylation data. **To avoid circular validation, variance is calculated using a Leave-One-Generation-Out (LOGO) jackknife approach**, where the variance of Layer A is derived from disjoint sample subsets (e.g., odd generations) compared to Layer B (even generations).
3.  **Analysis**: Computing Spearman's rank correlation between epigenetic and expression variance, stratified by environmental condition and **specific stressor type** (e.g., temperature vs. nutrient) if metadata permits.
4.  **Validation**: Reporting **uncertainty intervals** for variance estimates (acknowledging N<10 instability) and performing sensitivity analysis across generation thresholds (3, 4, 5).
5.  **Visualization**: Generating scatter plots of the variance relationship, explicitly flagged if temporal resolution is insufficient.

The implementation is constrained to CPU-only execution on GitHub Actions free-tier (2 CPU, **2GB RAM limit**, 6h limit), utilizing efficient Python libraries (`pandas`, `scipy`, `numpy`, `scikit-learn`) and avoiding GPU-dependent deep learning or large language models.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `scikit-learn`, `requests`, `pyyaml`, `tqdm`  
**Storage**: Local file system (`data/`, `code/`, `output/`); no external database.  
**Testing**: `pytest` for unit tests on data processing and statistical functions.  
**Target Platform**: Linux (GitHub Actions Free Tier Runner).  
**Project Type**: Data Science Pipeline / Research Script.  
**Performance Goals**: Complete full pipeline (download, process, analyze, visualize) within 6 hours on 2 CPU cores; **memory usage < 2GB** (aligned with SC-005).  
**Constraints**: No GPU/CUDA; no 8-bit/4-bit quantization; no large-LLM inference; strict adherence to verified dataset URLs; no manual intervention during pipeline execution.  
**Scale/Scope**: Analysis of ≤5,000 genes across ≤3 matched datasets (if available).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Notes |
|-----------|-------------------|-------|
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, random seeds in `code/`, and fetching from canonical verified sources only. |
| **II. Verified Accuracy** | **PASS** | All dataset citations restricted to the "Verified datasets" block. **The discovery script calls `validate_reference(accession, title)` which performs a title-token overlap check (threshold ≥ 0.7) against a local registry of verified accession titles to satisfy the Reference-Validator Agent requirement.** |
| **III. Data Hygiene** | **PASS** | Pipeline design separates raw data (`data/raw/`) from derived data (`data/processed/`). Checksums will be recorded in state YAML. |
| **IV. Single Source of Truth** | **PASS** | Figures and stats will be generated programmatically from `data/processed/` matrices; no hand-typed values. |
| **V. Versioning Discipline** | **PASS** | Content hashes for artifacts will be computed and stored in `state/...yaml`. |
| **VI. Multi-Omic Data Integrity** | **PASS** | Preprocessing for methylation and RNA-seq will be executed in isolated modules (`code/preprocess/methyl.py`, `code/preprocess/rna.py`) to prevent cross-contamination. **LOGO jackknife ensures independence of sample sets.** |
| **VII. Temporal Resolution Validation** | **PASS** | The analysis phase explicitly checks for "fluctuation timescale" metadata. **If a dataset lacks sufficient granularity (N<3 generations or missing timescale), the `CorrelationResult` includes a `temporal_resolution_flag: "insufficient"` and the result is excluded from the final association claim.** |

## Project Structure

### Documentation (this feature)

```text
specs/001-role-of-epigenetic-drift/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Configuration, paths, seeds
├── discovery/
│   ├── __init__.py
│   └── query_geno.py    # FR-000, FR-001: Dataset discovery logic + Reference-Validator call
├── preprocess/
│   ├── __init__.py
│   ├── rna_seq.py       # FR-002: RNA-seq normalization (LOGO jackknife)
│   └── methyl.py        # FR-002: Methylation normalization (LOGO jackknife)
├── analysis/
│   ├── __init__.py
│   ├── correlation.py   # FR-003, FR-004: Spearman & Uncertainty Estimation
│   └── sensitivity.py   # FR-005: Threshold sweep
├── viz/
│   ├── __init__.py
│   └── plots.py         # FR-006: Scatter plots
└── main.py              # Orchestration script

tests/
├── unit/
│   ├── test_preprocess.py
│   └── test_analysis.py
└── contract/
    └── test_schema.py   # Validates against contracts/

data/
├── raw/                 # Downloaded parquet/jsonl (checksummed)
└── processed/           # Unified variance matrices (LOGO split)

output/
└── figures/             # Generated PNGs
```

**Structure Decision**: Single Python package structure (`code/`) chosen to maintain isolation of multi-omic processing steps (Constitution Principle VI) and ensure reproducibility on CI. No web server or mobile components required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Multi-stage preprocessing** | Required to enforce "Multi-Omic Data Integrity" (Principle VI) and prevent cross-contamination of artifacts between methylation and RNA-seq streams. | A single monolithic script would risk mixing normalization logic, violating the strict separation required for independent biochemical assays. |
| **Leave-One-Generation-Out (LOGO) Jackknife** | Required to break the circular validation where variance of Layer A and Layer B are derived from the same N samples. | Simple bootstrap resampling on the same N (3-5) does not create independent samples and fails to address the tautology of "noisy genes are noisy in both layers." |
| **Stressor Stratification** | Required to address the confound of "fluctuating" conditions aggregating distinct stressors (temperature vs. nutrient). | Aggregating all "fluctuating" data without stratification would render the correlation meaningless or spurious. |
| **Temporal Resolution Flag** | Required by Constitution Principle VII to explicitly flag null results due to insufficient granularity. | Proceeding with low-N data without flagging would lead to misinterpretation of methodological blind spots as biological buffering. |
