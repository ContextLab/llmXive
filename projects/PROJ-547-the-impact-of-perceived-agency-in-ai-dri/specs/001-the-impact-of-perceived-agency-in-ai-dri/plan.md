# Implementation Plan: The Impact of Perceived Agency in AI‑Driven Cognitive Behavioral Therapy on Treatment Adherence

**Branch**: `PROJ-547-perceived-agency` | **Date**: 2026-06-24 | **Spec**: `specs/PROJ-547-perceived-agency/spec.md`
**Input**: Feature specification from `/specs/PROJ-547-perceived-agency/spec.md`

## Summary

This project investigates how linguistic markers of perceived user agency in AI‑CBT conversations predict treatment adherence metrics (session completion, usage frequency, self‑reported engagement) using publicly available chatbot datasets. The technical approach involves: (1) ingesting conversation transcripts (CSV/JSON) and computing agency scores via linguistic marker detection (spaCy/NLTK); (2) extracting adherence metrics from usage metadata while enforcing a ≥ 7‑day temporal gap for self‑reported engagement; (3) performing multiple regression models with Benjamini‑Hochberg FDR correction, runtime guard (< 30 min) and post‑hoc power analysis; (4) psychometrically validating the agency metric against an *external* established perceived‑agency scale; (5) comprehensive logging and audit of processing steps; (6) handling missing confounders via multiple imputation (m = 5) or bias‑assessment complete‑case analysis.

All steps are designed to run on a GitHub Actions free‑tier runner (≤ 2 CPU, ≤ 6 GB RAM, ≤ 14 GB disk, ≤ 6 h total runtime) and to satisfy the Constitution (reproducibility, data hygiene, single source of truth, ethical handling, psychometric validation).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: spaCy ≥ 3.6, NLTK ≥ 3.8, pandas ≥ 2.0, statsmodels ≥ 0.14, scikit‑learn ≥ 1.3, pyyaml ≥ 6.0, matplotlib ≥ 3.8, tqdm ≥ 4.66, iterative‑imputer (sklearn)  
**Storage**: CSV/JSON/Parquet under `data/`  
**Testing**: pytest  
**Target Platform**: Linux (GitHub Actions free‑tier)  
**Performance Goals**: ≤ 6 GB RAM, ≤ 2 CPU cores, ≤ 6 h total runtime, regression step ≤ 30 min  
**Constraints**: No GPU, no large‑LLM inference, all libraries CPU‑only.

## Constitution Check

| Constitution Principle | Compliance Approach | Status |
|------------------------|---------------------|--------|
| **I. Reproducibility (NON-NEGOTIABLE)** | Pinned `requirements.txt`, fixed random seeds in `config/`, deterministic dataset download URLs, all scripts under `code/` runnable end‑to‑end. | PASS |
| **II. Verified Accuracy** | All citations in `research.md` validated against primary sources; dataset URLs taken from verified block only; title‑token overlap ≥ 0.7 enforced by Reference‑Validator. | PASS |
| **III. Data Hygiene** | SHA‑256 checksums recorded in `data/metadata.yaml`; raw files never overwritten; each transformation writes a new file with derivation log. | PASS |
| **IV. Single Source of Truth** | Every figure/ statistic traced back to a row in `data/` and a line in a script under `code/`. No hand‑typed numbers. | PASS |
| **V. Versioning Discipline** | Content hashes for all artifacts stored in `state/projects/…yaml`; updates bump `updated_at`. | PASS |
| **VI. Ethical Data Handling** | De‑identified data stored under `data/`; consent document referenced at `data/consent/consent_document.pdf`. | PASS |
| **VII. Psychometric Validity of Agency Measures** | Validation notebook under `code/validation/`; validation results stored in `data/validated_features/validation_report.yaml`. | PASS |

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-547-perceived-agency/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── agency_score.schema.yaml
└── tasks.md          # generated later
```

### Source Code (repository root)

```text
code/
├── data_acquisition/
│   ├── download_datasets.py          # FR‑012: download verified URLs, verify checksums
│   └── validate_metadata.py          # Record source, version, license, checksum
├── agency_scoring/
│   ├── ingest_transcripts.py         # FR‑001: CSV/JSON ingestion, chronological parsing
│   ├── detect_markers.py             # FR‑002: spaCy/NLTK marker detection
│   ├── compute_scores.py             # FR‑003: weighted aggregation, min‑max norm
│   └── config/
│       └── agency_weights.yaml       # Default marker weights
├── adherence_extraction/
│   ├── extract_metrics.py            # FR‑004, FR‑013: compute 5 metrics + 7‑day check
│   └── impute_confounders.py         # FR‑010: multiple imputation (m=5) or bias report
├── analysis/
│   ├── merge_datasets.py             # FR‑005: merge agency, adherence, demographics
│   ├── run_regression.py             # FR‑005: logistic/beta/OLS, FDR, runtime guard, power calc
│   └── generate_plots.py             # FR‑006: PNG regression plots
├── validation/
│   ├── compute_reliability.py        # FR‑009: split‑half (Spearman‑Brown)
│   ├── compute_convergent.py         # FR‑009: Pearson r with *external* agency scale
│   └── report_generator.py           # FR‑009: creates `data/validated_features/validation_report.yaml` and PDF
├── logging/
│   ├── pipeline_logger.py            # FR‑008: timestamped log entries
│   └── verify_logging.py             # SC‑005: compute logging completeness metric
├── pipeline/
│   └── run_full_pipeline.py          # orchestrates all steps in correct order
└── config/
    ├── regression_config.yaml        # Confounders, model settings, FDR method
    └── imputation_config.yaml        # Imputation parameters
```

## Phase Overview & Mapping to FR/SC

| Phase | FR/SC addressed | Key Tasks |
|-------|----------------|-----------|
| **0. Dataset Acquisition** | FR‑012, SC‑001 (processing rate) | `download_datasets.py` → checksum → `data/metadata.yaml`. |
| **1. Transcript Ingestion** | FR‑001, FR‑002 | `ingest_transcripts.py` parses CSV/JSON, orders utterances. |
| **2. Agency Scoring** | FR‑003, FR‑008 | `detect_markers.py` → `compute_scores.py` → `agency_scores.csv`. |
| **3. Usage & Demographic Data** | FR‑004, FR‑010, FR‑011, FR‑013 | `extract_metrics.py` (7‑day check) + `impute_confounders.py`. |
| **4. Validation (Psychometric)** | FR‑009, Constitution VII | `compute_reliability.py`, `compute_convergent.py` → `validation_report.yaml`. *If external agency scale missing, abort with logged error.* |
| **5. Merge & Prepare Modeling Dataset** | FR‑005 | `merge_datasets.py` → `merged_data.csv`. |
| **6. Regression Analysis** | FR‑005, SC‑003, SC‑004 | `run_regression.py` (runtime guard < 30 min, post‑hoc power, FDR). |
| **7. Results Generation** | FR‑006, FR‑008, SC‑005 | `generate_plots.py`, `pipeline_logger.py`, `verify_logging.py`. |
| **8. Logging & Audit** | FR‑008, SC‑005 | All scripts write to `logs/run_<timestamp>.log`; completeness metric computed. |

### Computational Limits (FR‑007)

All scripts are written to stream data where possible, avoid loading full parquet files into memory, and respect the ≤ 6 GB RAM ceiling. A runtime guard in `run_regression.py` aborts if wall‑clock time exceeds 30 minutes (SC‑003).

### Power Considerations

After regression, `run_regression.py` computes achieved statistical power for each outcome (using `statsmodels.stats.power.FTestPower`). If any power < 0.80, a warning is logged and the results summary flags the limitation (addressing methodological concern).

### Psychometric Validation Requirement

`compute_convergent.py` expects a CSV containing `session_id` and `external_agency_scale_score`. If this file is absent or empty, the script logs an error and the pipeline halts, ensuring compliance with FR‑009 and Constitution Principle VII (no circular synthetic validation).

### Imputation & Bias Assessment (FR‑010)

`impute_confounders.py` applies `IterativeImputer` (m = 5) to any missing confounder columns. If imputation fails, the script falls back to complete‑case analysis and generates `bias_assessment_report.txt` describing potential selection bias.

### Logging Completeness (SC‑005)

`verify_logging.py` parses `logs/run_*.log`, counts expected log entries (based on a predefined step list), and writes a metric file `logs/completeness_metric.json`. SC‑005 is satisfied when the proportion ≥ 0.95.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Multiple regression models (logistic, beta, OLS) | FR‑005 demands outcome‑appropriate models; single model would mis‑specify proportions. |
| Psychometric validation with external scale | FR‑009 requires validation against a *real* scale; synthetic validation would be tautological. |
| 7‑day temporal separation for self‑report | FR‑011 mandates this to mitigate common‑method bias; ignoring it would violate the spec. |
| Runtime guard for regression (< 30 min) | SC‑003 explicitly caps regression time; without guard the step could exceed limits on CI. |
| Logging completeness audit | SC‑005 requires ≥ 95 % of steps logged; a simple logger would not provide a measurable metric. |
| Multiple imputation for confounders | FR‑010 requires imputation or bias report; dropping missing data outright would lose valuable cases. |
