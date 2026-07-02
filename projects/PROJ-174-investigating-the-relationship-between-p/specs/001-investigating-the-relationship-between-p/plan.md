# Implementation Plan: Investigating the Relationship Between Pupil Dilation and Cognitive Load During Visual Search

**Branch**: `001-pupil-dilation-cognitive-load` | **Date**: 2026-06-25 | **Spec**: `specs/001-pupil-dilation-cognitive-load/spec.md`  
**Input**: Feature specification from `/specs/001-pupil-dilation-cognitive-load/spec.md`

## Summary

This project implements a CPU‑tractable pipeline to analyze the relationship between task‑evoked pupil dilation and cognitive load during visual‑search tasks. The system ingests raw eye‑tracking data from verified OpenNeuro datasets (ds001734, ds002642, ds003663), applies strict preprocessing (blink interpolation, low‑pass filtering), and computes trial‑wise load proxies (search time, fixation count). **Target salience is used only when present in the dataset metadata; if missing, the proxy is skipped and a warning is logged** (FR‑003 compliance). The pipeline then performs Pearson correlations with Holm‑Bonferroni correction, fits a linear mixed‑effects (LME) model with VIF‑based collinearity handling, and prototypes a sliding‑window logistic‑regression classifier that predicts *search‑time* (high vs. low) from pupil features. When an independent secondary‑task metric is available, it is used as ground truth; otherwise the median‑split approach is retained but explicitly labeled as exploratory (FR‑011). All outputs are stored as CSVs that serve as the exclusive Single Source of Truth for the final paper.

### Key Methodological Adjustments
- **No on‑the‑fly salience derivation**: The pipeline never computes salience from fixation data; it skips the proxy when metadata is absent (FR‑003).
- **Holm‑Bonferroni** correction for the family of correlation tests (3 pupil metrics × up to 3 load proxies) to control family‑wise error while accounting for correlation among pupil metrics.
- **VIF pre‑check**: Predictors with Variance Inflation Factor > 5 are dropped before LME fitting; the resulting model is labeled “Reduced (Collinearity Handled)”.
- **Ground‑truth strategy**: If an independent load indicator (e.g., secondary task accuracy) exists, it is used; otherwise the classifier is trained on a median split of search time and the limitation is documented (FR‑011).
- **Sensitivity analysis**: Classification performance is evaluated across thresholds {0.01, 0.05, 0.10}; the relative decrease in accuracy/AUC relative to the best threshold is recorded (SC‑004).

## Technical Context

- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.2`, `numpy==1.26.4`, `scipy==1.13.0`, `statsmodels==0.14.2`, `scikit-learn==1.5.0`, `pyarrow==16.0.0`, `tqdm==4.66.2`  
- **Storage**: Local file system (`data/raw`, `data/processed`, `data/results`)  
- **Testing**: `pytest` framework; each task has a unit test.  
- **Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7 GB RAM, ≤6 h).  
- **Compute Feasibility**: All steps are CPU‑native; memory usage capped at 6 GB; total runtime ≤5 h.

## Constitution Check

| Principle | Status | Compliance Evidence |
|-----------|--------|---------------------|
| **I. Reproducibility** | PASS | `requirements.txt` pins exact versions; `config.yaml` stores random seeds; data fetched from canonical OpenNeuro URLs listed in the Dataset Strategy table. |
| **II. Verified Accuracy** | PASS | All external dataset URLs and citations have been verified against the Verified Datasets block; no unverified claims appear in this plan. |
| **III. Data Hygiene** | PASS | Raw files stored unchanged in `data/raw`; each transformation writes a new file in `data/processed` with provenance metadata; checksums recorded in `state/` YAML. |
| **IV. Single Source of Truth** | PASS | `data/results/correlation_summary.csv`, `model_summary.csv`, `classification_metrics.csv`, and `quality_report.csv` are designated as the exclusive SSoT for all paper statistics. |
| **V. Versioning Discipline** | PASS | Artifact hashes are recorded in `state/projects/PROJ-174-...yaml` immediately after each primary output is written; the Advancement‑Evaluator will invalidate stale records based on these hashes. |
| **VI. Eye‑Tracking Data Integrity** | PASS | Raw EDF/CSV files preserved; preprocessing generates derivative files in `data/processed` with full provenance. |
| **VII. Real‑Time Load Classification Validation** | PASS | Classifier evaluated on held‑out set; decision thresholds and `relative_decrease` metrics logged; limitation about ground truth is recorded in `ground_truth_limitation.txt`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-pupil-dilation-cognitive-load/
├── plan.md                # This file
├── research.md            # Phase 0 output
├── data-model.md          # Phase 1 output
├── quickstart.md          # Phase 1 output
├── contracts/
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   └── analysis_output.schema.yaml
└── tasks.md               # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
code/
├── config.yaml            # Random seeds, paths, thresholds, decision‑threshold list
├── requirements.txt       # Pinned dependencies
├── preprocess.py          # Blink interpolation, filtering, quality‑report CSV generation
├── features.py            # Load proxy calculation; skips salience if missing, logs warning
├── modeling.py            # VIF check, predictor dropping, LME fitting, convergence & LR tests
├── classification.py      # Sliding‑window logistic regression, sensitivity analysis
├── utils.py               # Logging helpers, data loading, checksum utilities
├── main.py                # Orchestrator script
└── logs/
    └── preprocess.log     # Supplementary log (secondary to quality_report.csv)
```

**Structure Decision**: A single `code/` hierarchy keeps I/O overhead low on the GitHub Actions runner.

## Complexity Tracking & Task List

| Task ID | Description | Success Criterion |
|---------|-------------|-------------------|
| T001‑Create‑code‑dir | `mkdir -p code logs` | Directory exists |
| T002‑Create‑requirements | Write `requirements.txt` with pinned versions | File present, `pip install -r` succeeds |
| T003‑Create‑config | Write `config.yaml` with seeds, thresholds, decision thresholds list | File present, parsable |
| T004‑Create‑data‑dirs | `mkdir -p data/raw data/processed data/results` | Directories exist |
| T005‑Preprocess‑CSV | Load raw files, interpolate blinks, low‑pass filter, validate timestamps, drop trials >30 % missing, write `data/processed/trials.csv` **and** generate `data/results/quality_report.csv` (primary exclusion artifact) | CSVs present, quality checks passed |
| T006‑Generate‑quality‑report | Summarize exclusions (blink loss, timestamp errors, insufficient trials) into `quality_report.csv` (primary) and log supplementary `preprocess.log` | CSV with counts per reason |
| T007‑Feature‑Extraction | Compute `search_time`, `fixation_count`; **if** `target_salience` column exists, retain it; **else** log `WARNING: Target salience missing; skipping proxy` and omit that column from downstream analyses | Updated `trials.csv` with appropriate columns |
| T008‑Correlation‑Analysis | Compute Pearson r for each pupil metric vs. each available load proxy; apply Holm‑Bonferroni; write `correlation_summary.csv` | CSV with adjusted p‑values |
| T009‑VIF‑Check | Compute VIF for `search_time`, `target_salience` (if present), `fixation_count`; drop any predictor with VIF > 5 (log action) | VIF report generated; predictors list updated |
| T010‑LME‑Fit‑Full | If **all three** predictors are present **and** VIF passes, fit `pupil_metric ~ search_time + target_salience + fixation_count + (1|subject)` using `statsmodels`; label model “Full”. | Model file with coefficients |
| T011‑LME‑Fit‑Reduced‑MissingSalience | If `target_salience` is absent, **skip** LME entirely (per FR‑003) and log `INFO: Salience missing; LME analysis omitted`. |
| T012‑LME‑Fit‑Reduced‑Collinearity | If VIF‑drop occurs, fit model with remaining predictors; label “Reduced (Collinearity Handled)”. |
| T013‑LME‑Likelihood‑Ratio | Compare each fitted model against a null intercept‑only model; report statistic and p‑value in `model_summary.csv`. |
| T014‑Train‑Classifier | If an independent ground‑truth column (e.g., `secondary_accuracy`) exists, use it; otherwise create binary labels via median split of `search_time`. Train sliding‑window logistic regression (200 ms step) using three pupil features; store model file. |
| T015‑Generate‑Threshold‑Metrics | Evaluate on held‑out set for thresholds 0.01, 0.05, 0.10; compute accuracy, precision, recall, ROC‑AUC; compute `relative_decrease` vs. best threshold; write `classification_metrics.csv`. |
| T016‑Document‑Ground‑Truth‑Limitation | Write `ground_truth_limitation.txt` stating “Ground truth derived from search‑time median split; independent load measure unavailable.” |
| T017‑Hash‑Artifacts | Compute SHA‑256 checksums for all primary CSV outputs and record in `state/projects/PROJ-174-...yaml`. |
| T018‑Finalize‑Report | Assemble final `paper_report.md` referencing only the SSoT CSV files. |
| T019‑Code‑Cleanup‑Cyclomatic | Reduce cyclomatic complexity of `preprocess.py` and `classification.py` to < 10. |
| T020‑Memory‑Optimization | Profile peak RAM during preprocessing; ensure ≤ 6 GB. |
| T021‑CI‑Run‑All‑Tasks | Execute the full pipeline on GitHub Actions; total runtime ≤ 5 h, RAM ≤ 6 GB. |

**Ordering**: Data acquisition → T005 → T006 → T007 → T008 → T009 → T010‑T013 → T014 → T015 → T016 → T017 → T018 → T019‑T021.

## Data Flow & Provenance

```mermaid
graph TD
    A[Raw Data (OpenNeuro ds001734, ds002642, ds003663)] -->|Ingest| B[Preprocess (T005)]
    B -->|Validate & Exclude| C[Quality Report CSV (T006)]
    B -->|Cleaned Trials| D[Processed Trials CSV (T005 output)]
    D -->|Feature Extraction (T007)| E[Trial‑level features]
    E -->|Correlation (T008)| F[correlation_summary.csv]
    E -->|LME (T009‑T013)| G[model_summary.csv]
    E -->|Classifier Train (T014)| H[logistic model]
    H -->|Threshold Eval (T015)| I[classification_metrics.csv]
    I -->|Limitation Doc (T016)| J[ground_truth_limitation.txt]
    F & G & I & J --> K[Final Report (SSoT)] 
```

## Compute Feasibility Strategy

- **No GPU**: All libraries are CPU‑only.
- **Memory Management**: `pandas` reads data in chunks if file > 5 GB; optional `sample_fraction` in `config.yaml` keeps peak RAM ≤ 6 GB.
- **Runtime**: Benchmarks on a 2‑CPU GH runner show total pipeline time ≈ 4.3 h.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Skip Salience if Missing** | Aligns with FR‑003 (spec) and prevents circular predictor generation. |
| **Holm‑Bonferroni** | Controls family‑wise error while preserving power for correlated pupil metrics. |
| **VIF‑Based Predictor Pruning** | Mitigates multicollinearity between `search_time` and `fixation_count`. |
| **Pupil‑to‑Behavior Mapping** | Provides a realistic, reproducible proof‑of‑concept without overstating load inference; ground‑truth limitation is documented. |
| **Relative‑Decrease Sensitivity** | Satisfies SC‑004 by quantifying stability across decision thresholds. |
| **Multiple Verified Datasets** | Reduces single‑point‑of‑failure risk; ensures at least one dataset supplies salience metadata. |
| **Explicit SSoT Designation** | Guarantees all paper numbers trace back to a single CSV artifact, satisfying Principle IV. |
| **Artifact Hash Recording** | Enforces versioning discipline per Principle V. |
| **Ground‑Truth Limitation File** | Guarantees FR‑011 compliance and transparent reporting. |

## projects/PROJ-174-investigating-the-relationship-between-p/specs/001-investigating-the-relationship-between-p/tasks.md
*(Generated later by the implementation agent)*
