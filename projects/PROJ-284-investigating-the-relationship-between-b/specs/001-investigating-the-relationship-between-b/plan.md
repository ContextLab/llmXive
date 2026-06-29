# Implementation Plan: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Sensorimotor Performance

**Branch**: `001-brain-proprioception-correlation` | **Date**: 2024-05-21 | **Spec**: `specs/001-investigating-the-relationship-between-b/spec.md`

## Summary

This project implements a computational neuroscience pipeline to investigate the **associational relationship** between resting-state brain network dynamics (graph metrics: modularity, participation coefficient, within-module degree, and **global efficiency**) and **sensorimotor performance** (using the Motor Task Performance composite score as a validated proxy for proprioceptive function) using data from the Human Connectome Project (HCP). 

**Computational Strategy**: To ensure feasibility on a 2-core CPU/7GB RAM GitHub Actions runner within 6 hours, the pipeline prioritizes **verified preprocessed HCP S1200 ICA-FIX data** (derived metrics) for the primary analysis. Raw NIfTI preprocessing is treated as a fallback or subset validation step only if verified preprocessed data is unavailable. The system employs dynamic batch sizing and memory profiling to prevent overflow. The analysis uses a Multivariate (PCA/MANOVA) approach to handle interdependent network metrics and reports % Confidence Intervals instead of post-hoc power.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nibabel`, `numpy`, `pandas`, `scikit-learn`, `networkx`, `matplotlib`, `seaborn`, `nilearn`, `requests`, `pytest`, `statsmodels`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/analysis`)  
**Testing**: `pytest` (unit tests for metric extraction, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`)  
**Project Type**: Computational Research Pipeline  
**Performance Goals**: Complete analysis of up to 50 subjects within 6 hours (using preprocessed data); memory usage < 7 GB.  
**Constraints**: No GPU usage; no deep learning training; strict adherence to HCP data access protocols; explicit handling of missing data; dynamic batch sizing.  
**Scale/Scope**: 30-50 subjects; 400x400 connectivity matrices; 4 network metrics per subject (Modularity, Global Efficiency, Participation Coefficient, Within-Module Degree).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: **PASS**. The plan mandates pinned dependencies (`requirements.txt`), random seed setting, and reproducible data fetching via HCP API (or verified static URLs for ICA-FIX data). All scripts will be runnable end-to-end.
- **Principle II (Verified Accuracy)**: **PASS**. The plan restricts dataset citations to the verified URLs provided in the spec (HCP S1200 ICA-FIX). The "Verified datasets" section in `research.md` explicitly maps FR-001 requirements to the available preprocessed data.
- **Principle III (Data Hygiene)**: **PASS**. The plan includes a checksumming step for all downloaded data and enforces a "raw vs. processed" directory separation. No in-place modifications are allowed.
- **Principle IV (Single Source of Truth)**: **PASS**. All statistics in the final report will be generated programmatically from the `data/analysis` CSVs, not hand-typed.
- **Principle V (Versioning Discipline)**: **PASS**. The plan includes a script to generate content hashes for all artifacts and update the project state file.
- **Principle VI (Neuroimaging Data Provenance)**: **PASS**. The plan specifies recording the HCP API version (or dataset release tag) and logging the preprocessing parameters (motion threshold, tSNR calculation method) in a `pipeline_config.yaml`. The fallback to preprocessed ICA-FIX data is explicitly recognized as part of the HCP S1200 release, maintaining the "exclusively HCP" constraint.
- **Principle VII (Statistical Correlation Integrity)**: **PASS**. The plan explicitly implements Spearman/Pearson correlations with FD covariate control and Benjamini-Hochberg FDR correction. It also includes a step to **log the correlation coefficient threshold (r > 0.3)** as required, even if not used as a gating condition.

## Project Structure

### Documentation (this feature)

```text
specs/001-investigating-the-relationship-between-b/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Configuration and constants
├── data/
│   ├── download.py      # HCP data fetching logic (API + verified static)
│   ├── preprocess.py    # fMRI preprocessing (motion correction, etc.) - Fallback only
│   └── metrics.py       # Graph metric extraction
├── analysis/
│   ├── correlations.py  # Statistical testing (PCA/MANOVA, FDR, CI)
│   └── power.py         # CI estimation (replacing post-hoc power)
├── viz/
│   ├── scatter.py       # Scatter plot generation
│   └── network.py       # Network diagram generation
├── report/
│   └── generate.py      # Markdown/PDF report assembly
├── tests/
│   ├── test_metrics.py
│   └── test_pipeline.py
└── main.py              # Orchestration script
```

**Structure Decision**: Single project structure selected to simplify data flow and dependency management for a research pipeline. The `code/` directory is isolated to ensure reproducibility and prevent global package pollution.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Derived-First Strategy | Raw NIfTI preprocessing for a cohort of subjects on a multi-core CPU requires a substantial amount of time.. | Preprocessing raw data for all subjects would cause CI timeout (SC-004). Using verified ICA-FIX data meets the "preprocessed" requirement without the computational cost. |
| Dynamic Batch Sizing | Required to handle 7GB RAM limit on CI with large 400x400 matrices. | Static batch size (e.g., 10) risks OOM crashes if memory usage spikes. |
| Proxy Measure Handling | HCP S1200 lacks direct proprioceptive tests; Motor Task Performance is a validated proxy. | Using direct proprioceptive data is impossible; ignoring the proxy limitation would violate Assumption 5 and Constitution Principle II. |
| Multivariate Approach (PCA/MANOVA) | Network metrics (Modularity, PC, WMD) are mathematically coupled. | Testing them as independent predictors leads to pseudo-replication and unstable results. |

## Implementation Phases

### Phase 0: Data Acquisition & Validation
- **Step 0.1**: Fetch HCP S1200 ICA-FIX data (verified preprocessed) for up to 50 subjects.
- **Step 0.2**: Verify data integrity (checksums) and subject availability (Motor Task Score, FD).
- **Step 0.3**: (Fallback) If ICA-FIX data unavailable, attempt raw NIfTI download via HCP API for a **subset** (e.g., A small cohort of subjects) to validate the preprocessing pipeline.

### Phase 1: Preprocessing (Fallback Only)
- **Step 1.1**: Execute motion correction, slice-time correction, normalization, smoothing on raw NIfTI (if fallback triggered).
- **Step 1.2**: Calculate tSNR (mean/std, excluding initial volumes) and ensure motion < 0.5mm.
- **Step 1.3**: Extract time-series using Schaefer 400-parcel atlas. **Apply motion regression** to time-series before connectivity calculation.

### Phase 2: Metric Extraction
- **Step 2.1**: Compute 400x400 functional connectivity matrices (Pearson correlation).
- **Step 2.2**: Extract metrics: Modularity, Global Efficiency, Participation Coefficient (mean), Within-Module Degree (mean).
- **Step 2.3**: Perform PCA on the 4 metrics to derive a single "Network Architecture" factor (or prepare for MANOVA).

### Phase 3: Statistical Analysis
- **Step 3.1**: Calculate correlations between Network Metrics (and PCA factor) and Motor Task Score.
- **Step 3.2**: Control for Framewise Displacement (FD) as a covariate.
- **Step 3.3**: Apply Benjamini-Hochberg FDR correction (q < 0.05).
- **Step 3.4**: **Log correlation threshold (r > 0.3)** and calculate % Confidence Intervals (replacing post-hoc power).
- **Step 3.5**: Flag significant findings (q < 0.05).

### Phase 4: Visualization & Reporting
- **Step 4.1**: Generate scatter plots for significant correlations with annotated r, q, and confidence intervals.
- **Step 4.2**: Generate network diagrams for significant findings.
- **Step 4.3**: **Generate Limitation Statement**: Explicitly state that Motor Task Performance is a proxy for proprioceptive accuracy and findings are associational.
- **Step 4.4**: Assemble final Markdown/PDF report.

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Raw data preprocessing exceeds 6 hours | Prioritize verified preprocessed (ICA-FIX) data; raw processing limited to subset. |
| Memory overflow (7GB limit) | Dynamic batch sizing; process subjects in groups of a moderate size, reducing if OOM detected. |
| Missing behavioral data | Exclude subjects with missing Motor Task Score; log count; proceed with N >= 30. |
| Collinearity of metrics | Use PCA/MANOVA to handle shared variance; report primary factor. |
| Motion confounds | Motion regression during time-series extraction + FD covariate in final correlation. |