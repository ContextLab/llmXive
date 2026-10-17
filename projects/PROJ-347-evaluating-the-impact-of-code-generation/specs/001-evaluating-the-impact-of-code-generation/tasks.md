- [ ] T002 [US-1] **Download human‑written vulnerable code** – fetch the Python subset of the Devign dataset (which includes known vulnerability labels) via the HuggingFace `datasets` library, streaming to avoid large memory use. Store the raw records under `data/raw/devign/`.  
  *Path*: `src/ingest/download_devign.py`  
  *Verification*:  
  1. The script finishes without error and creates `data/raw/devign/devign_train.jsonl`.  
  2. A SHA‑256 checksum of the downloaded shard is recorded in `data/checksums.json` and matches the value reported by the dataset.  

- [ ] T003 [US-1] **Filter and retain only qualified Python snippets** – keep rows that (a) have a non‑empty `code` field, (b) possess a known `vulnerability_label`, and (c) are labelled as Python. Abort with an informative error if fewer than five distinct OWASP Top 10 categories remain. Write the filtered table to `data/processed/human_samples.csv`.  
  *Path*: `src/ingest/filter_devign.py`  
  *Verification*:  
  1. `data/processed/human_samples.csv` contains ≥ 300 rows (to satisfy the power analysis) and a header with `functionality_id,code,vulnerability_label,language`.  
  2. `data/logs/filter.log` lists the distinct vulnerability categories; the count is ≥ 5.  

- [ ] T004 [US-1] **Generate LLM‑equivalent snippets** – for every `functionality_id` in `human_samples.csv` invoke the open‑source model **Salesforce/codegen‑350M‑multi** via the `transformers` pipeline (`temperature=0`, `max_new_tokens=512`). Seed all RNGs (`numpy`, `random`, `torch`) with 42 and retry up to three times on API errors. Store the generated code in `data/generated/llm_samples.csv` and record the process in `data/logs/generation.log`.  
  *Path*: `src/llm/generate.py`  
  *Verification*:  
  1. The number of rows in `llm_samples.csv` exactly matches the number of rows in `human_samples.csv`.  
  2. `generation.log` contains the seed, total API call count, and any unrecoverable failures (none for a successful run).  

- [ ] T005 [US-1] **Validate functional equivalence, security pattern, and compute SC‑001** – for each human/LLM pair:  
  1. Parse with Python `ast` → `syntax_valid`.  
  2. Run the unit‑test suite bundled with the Devign sample (via `pytest --cov=.`) and require coverage ≥ 90 %; also compute semantic similarity using `sentence‑transformers/all‑mpnet‑base‑v2` and require a cosine score ≥ 0.85. Both conditions must be satisfied (AND).  
  3. Execute the security‑focused pattern test (`validate/security_pattern.py`) to ensure input‑sanitisation checks pass.  
  4. Set `functional_equivalence_verified` to true only when **syntax_valid** is true, both coverage ≥ 90 % **and** similarity ≥ 0.85 hold, **and** the security pattern test succeeds.  
  5. Persist each validated snippet under `data/validated/human/<functionality_id>.py` and `data/validated/llm/<functionality_id>.py`.  
  6. Write a summary CSV `data/validated/validated_pairs.csv` with columns `functionality_id,source,syntax_valid,functional_equivalence_verified`.  
  *Path*: `src/validate/validate_pairs.py`  
  *Verification*:  
  1. Compute `SC‑001 = (number of LLM samples with functional_equivalence_verified = true) / (total LLM samples)`. The script asserts `SC‑001 ≥ 0.85`; otherwise it aborts with a clear message.  
  2. Every row in `validated_pairs.csv` has the two boolean flags, and the corresponding `.py` files exist and are syntactically valid.  

- [ ] T016 **Compute code‑size metrics** – for each validated CodeSample (both human and LLM), calculate lines‑of‑code using `radon` and cyclomatic complexity using `radon.complexity`. Append these metrics to the `CodeSample` records and write `data/metrics/code_metrics.csv` (columns: `sample_id,source,functionality_id,lines_of_code,cyclomatic_complexity`).  
  *Path*: `src/validate/compute_metrics.py`  
  *Verification*:  
  1. The CSV contains a row for every validated sample and all numeric fields are non‑negative integers.  
  2. Schema validation against `code_sample.schema.yaml` passes.  

- [ ] T001 **Quickstart setup** – create a virtual environment, install pinned dependencies, pull required Docker images, and run a minimal pipeline on 5 paired samples to confirm the orchestration works.  
  *Path*: `scripts/quickstart.sh` (script to be created)  
  *Verification*:  
  1. After `bash scripts/quickstart.sh` finishes, the command `python -m src.run_pipeline --seed 42 --max-pairs 5` exits with code 0.  
  2. `logs/quickstart.log` contains lines confirming virtual‑env activation, successful `pip install -r requirements.txt`, Docker pulls for `returntocorp/semgrep:1.46.0` and `sonarqube:9.9-community`, and a final “Pipeline completed” message.  

- [ ] T006 [US-2] **Run the static‑analysis toolchain** – execute the three open‑source scanners on the validated directories:  
  * Semgrep (`returntocorp/semgrep:1.46.0`) → `data/results/semgrep_human.json` / `semgrep_llm.json`  
  * SonarQube Community Edition (`sonarqube:9.9-community`) via the official scanner → `data/results/sonarqube_human.json` / `sonarqube_llm.json`  
  * Bandit (`bandit==1.7.8`) → `data/results/bandit_human.json` / `bandit_llm.json`  
  The runner monitors memory; any process exceeding 6 GB is terminated, the event logged in `data/logs/<tool>_oom.log`, and the offending sample is skipped.  
  *Path*: `src/analysis/static_tools.py`  
  *Verification*:  
  1. Each JSON file is well‑formed, contains at least one finding, and can be opened with `json.load`.  
  2. `data/logs/memory_monitor.log` shows peak RAM ≤ 6 GB for every tool.  
  3. The total wall‑clock time for the three tools is ≤ 30 minutes on the test batch of 5 pairs (as proved by the quickstart run).  

- [ ] T007 [US-3] **Normalize findings to the contract schema** – ingest the six JSON result files, map fields to the `VulnerabilityFinding` schema (e.g., Semgrep `confidence` → `confidence_score`; SonarQube severity → normalized confidence: CRITICAL = 1.0, HIGH = 0.75, MEDIUM = 0.5, LOW = 0.25; Bandit severity mapped similarly). Write a unified Parquet file `data/interim/vuln_findings.parquet`.  
  *Path*: `src/analysis/normalize_findings.py`  
  *Verification*:  
  1. `pytest tests/contract/test_contracts.py` passes for the Parquet file.  
  2. The Parquet file contains findings for ≥ 5 distinct OWASP categories that also appear in the ground‑truth dataset.  

- [ ] T008 [US-3] **Create the PairOutcome table** – for every `functionality_id` and every vulnerability type, set `human_flag` = 1 if any finding (after normalization) exists for the human sample, otherwise 0; similarly for `llm_flag`. Write the result to `data/interim/pair_outcomes.csv`.  
  *Path*: `src/analysis/construct_pair_outcomes.py`  
  *Verification*:  
  1. Row count equals `total_pairs × number_of_vulnerability_types`.  
  2. Each (`functionality_id`, `vulnerability_type`) combination appears exactly once.  

- [ ] T009 [US-3] **Primary statistical comparison** – load `pair_outcomes.csv` and, for each vulnerability type, perform McNemar’s test (`statsmodels.stats.contingency_tables.mcnemar`). If any cell of the 2 × 2 table is zero, re‑run with `exact=True`. Apply a Bonferroni correction across all tested types. Write the final table to `data/outputs/analysis_results.csv` following the `AnalysisResult` schema (including `p_value_adj`, `is_significant`, `test_method`).  
  *Path*: `src/stats/mcnemar_test.py`  
  *Verification*:  
  1. The CSV contains the columns required by the schema and passes schema validation.  
  2. At least one row has `is_significant = true` **or** the file includes a comment line stating “No significant differences (all adjusted p ≥ 0.05)”.  

- [ ] T017 **Verify OWASP category coverage (SC‑005)** – read `analysis_results.csv` and ensure that for each OWASP Top 10 category present in the original dataset there is at least one vulnerability finding (human or LLM). Fail the pipeline with a clear error if any required category is missing.  
  *Path*: `src/validation/owasp_coverage_check.py`  
  *Verification*:  
  1. Script exits with code 0 only when every required category has ≥ 1 finding; otherwise it logs missing categories and exits with non‑zero status.  

- [ ] T010 [US-3] **Confidence‑threshold sensitivity sweep** – repeat the aggregation (T008) and statistical test (T009) for three confidence cut‑offs: `default‑0.05`, `default`, and `default+0.05` (e.g., 0.45, 0.5, 0.55 for Semgrep confidence). Append a `confidence_threshold` column to each result row and write the combined table to `data/outputs/sensitivity_results.csv`.  
  *Path*: `src/stats/sensitivity_sweep.py`  
  *Verification*:  
  1. The CSV contains three rows per vulnerability type (one per threshold).  
  2. Variation in `p_value_adj` across thresholds is recorded and can be plotted.  

- [ ] T011 [US-3] **Random audit of flagged findings** – select ≥ 20 % of all findings (stratified by vulnerability type) using a fixed seed 42. For each selected finding run CodeQL (`ghcr.io/github/codeql-action:latest`) and a lightweight fuzzing harness (`afl‑fast` in Docker) to confirm true/false status. Update the `validated_by_audit` flag in the Parquet file and export the audit log to `data/validation/audit_results.csv`. Log the process in `data/logs/audit.log`.  
  *Path*: `src/audit/manual_audit.py`  
  *Verification*:  
  1. The number of audited rows matches the ≥ 20 % target.  
  2. `audit.log` records pass/fail outcomes and the derived calibration factor.  

- [ ] T014 **Measure pipeline performance** – wrap the full pipeline execution (`src/run_pipeline.py`) with a script that records start/end timestamps and monitors peak RAM via `psutil`. Write `data/logs/pipeline_performance.log` containing `total_runtime_seconds` and `peak_ram_gb`. CI asserts `total_runtime_seconds ≤ 21600` (6 h) and `peak_ram_gb ≤ 7`.  
  *Path*: `scripts/performance_monitor.sh`  
  *Verification*: After a full run on the target 300‑pair dataset, the log shows values within the limits; the CI job fails if they exceed.  

- [ ] T013 **Assemble the final markdown report** – create `report/report.md` containing:  
  * Dataset statistics (size, SC‑001 compliance).  
  * Table of raw counts and Bonferroni‑adjusted p‑values (from `analysis_results.csv`).  
  * Significance statements and discussion of limitations.  
  * Embedded figures (`![](../figures/vuln_rate_comparison.png)`, `![](../figures/sensitivity_plot.png)`).  
  * Description of the manual audit process and its outcomes.  
  * Links to all primary output artifacts (`data/outputs/*`, `data/interim/*`).  
  *Verification*: `pytest tests/test_report.py` parses the markdown, confirms that every referenced file exists, and that the report contains a non‑empty “Results” section.  

- [ ] T015 **Compute precision and recall per static‑analysis tool (satisfies FR-008)** – using the ground‑truth vulnerability labels from the Devign dataset, compare each tool’s findings (from `vuln_findings.parquet`) against the true labels to calculate precision and recall per tool and per OWASP category. Write `data/metrics/precision_recall.csv`.  
  *Path*: `src/validation/precision_recall.py`  
  *Verification*:  
  1. CSV contains columns `tool_source,vulnerability_type,precision,recall`.  
  2. All values are between 0 and 1 and the file passes schema‑agnostic sanity checks.  

- [ ] T012 **Generate visualisations** – using `matplotlib` with a deterministic style (seeded RNG for colours):  
  1. Bar‑chart comparing vulnerability rates between human and LLM code → `figures/vuln_rate_comparison.png`.  
  2. Line‑chart showing how `p_value_adj` varies across the three confidence thresholds → `figures/sensitivity_plot.png`.  
  *Path*: `src/report/figures.py`  
  *Verification*: Both PNG files are non‑empty, openable with standard image viewers, and their filenames appear in the final markdown report.  