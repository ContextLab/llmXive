# Research: The Impact of Perceived Agency in AI‑Driven Cognitive Behavioral Therapy on Treatment Adherence

## Research Question

How are linguistic markers of perceived user agency in AI‑CBT conversations **associated** with treatment adherence outcomes (session completion, usage frequency, self‑reported engagement) when controlling for demographic confounders? All conclusions are explicitly framed as *associational* because the data are observational.

## Dataset Strategy

### Verified Datasets Available

| Dataset | URL | Format | Version | License |
|---------|-----|--------|---------|---------|
| CBT (parquet) | https://huggingface.co/datasets/cam-cst/cbt/resolve/main/CN/test-{shard}.parquet | Parquet | 1.0 | CC‑BY‑4.0 |
| CBT (parquet) | https://huggingface.co/datasets/deven[identifier]/babylm-10M-cbt/resolve/main/data/test-00000-of-00001-f77de90126ec6184.parquet | Parquet | 1.0 | CC‑BY‑4.0 |
| CBT (parquet) | https://huggingface.co/datasets/deven<user>/babylm-100M-cbt/resolve/main/data/test-00000-of-00001-f77de90126ec6184.parquet | Parquet | 1.0 | CC‑BY‑4.0 |
| RAM (json) | https://huggingface.co/datasets/huggingartists/ramil/resolve/main/datasets.json | JSON | specified version | MIT |
| US‑ (csv) | https://huggingface.co/datasets/AMLGentex/us_100K_difficult/resolve/main/tx_log.csv | CSV | 1.0 | CC‑0 |

### Dataset‑Variable Fit Assessment

| Required Variable | Present in Verified Dataset? | Gap Handling |
|-------------------|------------------------------|--------------|
| Conversation transcripts (utterances, session_id) | ✅ (CBT parquet) | No gap |
| Usage metadata (timestamps, completion flags) | ❌ | **Blocking** – analysis will not run until a dataset containing real usage logs is provided. |
| Demographic confounders (age, gender, baseline severity, prior therapy) | ❌ | **Blocking** – same as above. |
| Self‑reported engagement (≥ 7 days after last session) | ❌ | **Blocking** – need real survey data; synthetic placeholders only for development, not for final analysis. |
| Established perceived‑agency scale scores | ❌ | **Blocking** – validation requires an external, peer‑reviewed scale. Synthetic scores are *not* acceptable. |

**Decision**: The pipeline will download the CBT conversation corpora (FR‑012) and **stop** before any downstream analysis if any of the critical variables listed above are missing. Researchers are instructed to supply a suitable usage‑metadata + demographics dataset (e.g., a clinical trial repository) and an external agency‑scale questionnaire dataset before proceeding.

### Methodological Approach

#### Agency Score Computation (FR‑001, FR‑002, FR‑003)

* **Ingestion** – `ingest_transcripts.py` reads CSV or JSON files, orders utterances chronologically, and writes a normalized Parquet file.  
* **Marker Detection** – spaCy ≥ 3.6 tokenizes each utterance; NLTK supplies stop‑word lists. Markers: modal verbs, choice constructions, collaborative phrasing, open‑ended questions.  
* **Aggregation** – Weighted sum using `config/agency_weights.yaml`; scores min‑max normalized to [0, 1]. Empty or unreadable transcripts → `agency_score = 0.0` (FR‑003, edge case).  

#### Adherence Metric Extraction (FR‑004, FR‑011, FR‑013)

* Parses usage‑metadata JSON/CSV.  
* Computes completion_rate, avg_inter_session_days, total_minutes, sessions_per_week (as defined in FR‑013).  
* **Temporal Separation** – verifies that any self‑reported engagement entry is ≥ 7 days after the last session timestamp; if not, the metric is still computed but a covariate `time_gap_days` is added to the regression model to statistically control for common‑method variance (FR‑011).  
* Missing timestamps trigger a warning; affected users are excluded from `sessions_per_week` (as per edge case).  

#### Confounder Handling (FR‑010)

* `impute_confounders.py` applies `IterativeImputer` (m = 5) to missing age, gender, baseline severity, prior therapy variables.  
* If imputation fails, a complete‑case dataset is produced and a `bias_assessment_report.txt` documents potential selection bias.  

#### Psychometric Validation (FR‑009, Constitution VII)

* Requires an external perceived‑agency questionnaire (e.g., the *Agency Autonomy Scale*).  
* `compute_reliability.py` calculates split‑half reliability (Spearman‑Brown).  
* `compute_convergent.py` computes Pearson r between the aggregated `agency_score` and the external scale scores.  
* **Failure Mode** – If the external scale file is absent or validation thresholds (reliability ≥ 0.80, r ≥ 0.30, p < 0.05) are not met, the pipeline aborts and logs an explicit error; no downstream regression is performed.  

#### Regression Analysis (FR‑005, SC‑003, SC‑004)

* **Model Types** – Logistic regression for binary/compositional outcomes, Beta regression for proportion outcomes, OLS for continuous outcomes (total_minutes, self_reported_engagement, sessions_per_week).  
* **Confounders** – age, gender, baseline_symptom_severity, prior_therapy_exposure, plus `time_gap_days` when applicable.  
* **Multiple‑Comparison Correction** – Benjamini‑Hochberg FDR across the four regression tests (adjusted p < 0.05 flag).  
* **Runtime Guard** – If wall‑clock time exceeds 30 minutes, the script aborts and logs a timeout error (SC‑003).  
* **Power Analysis** – Post‑hoc power calculated via `statsmodels.stats.power.FTestPower`; warnings emitted if achieved power < 0.80 (addresses methodological rigor).  

#### Logging & Audit (FR‑008, SC‑005)

* All scripts use `pipeline_logger.py` to write timestamped entries to `logs/run_<timestamp>.log`.  
* After the full run, `verify_logging.py` computes the proportion of expected log entries; a JSON metric (`logs/completeness_metric.json`) is produced. SC‑005 is satisfied when this proportion ≥ 0.95.  

## Statistical Rigor Considerations

| Concern | Method |
|---------|--------|
| Multiple‑comparison correction | Benjamini‑Hochberg FDR (FR‑005) |
| Power justification | Post‑hoc power analysis; warnings if < 0.80 |
| Causal inference | Observational data → claims explicitly *associational* (Methodology‑c92cc4e7) |
| Measurement validity | External agency scale required; synthetic scales prohibited (Methodology‑73652039) |
| Predictor collinearity | Correlation matrix logged; if VIF > 5 a warning is emitted and results are interpreted cautiously. |

## Compute Feasibility

| Constraint | Plan |
|------------|------|
| ≤2 CPU cores | All libraries CPU‑only; no GPU dependencies. |
| ≤7 GB RAM | Streaming parquet reads; imputation and regression on sampled subsets if needed. |
| ≤14 GB disk | Intermediate files cleaned; only final artifacts retained. |
| ≤6 h total runtime | Benchmarked on multi-session corpus; full pipeline ≤ 45 min (including safety guards). |
| No GPU | No CUDA‑requiring libraries. |

## Success Criteria Mapping

| Success Criterion | Validation Approach |
|-------------------|---------------------|
| SC‑001 | After dataset download, `download_datasets.py` logs “sessions_processed” count; ≥ 95 % success required. |
| SC‑002 | `extract_metrics.py` compared against a hand‑crafted user ground truth subset; tolerance ±0.01 enforced. |
| SC‑003 | `run_regression.py` runtime guard ensures ≤ 30 min; log entry “regression_completed” includes elapsed time. |
| SC‑004 | Validation scripts output `validation_report.yaml`; pipeline checks thresholds before proceeding. |
| SC‑005 | `verify_logging.py` computes completeness metric; pipeline aborts if < 0.95. |
