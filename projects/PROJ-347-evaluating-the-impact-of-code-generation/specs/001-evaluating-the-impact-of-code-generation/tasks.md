# Tasks: Evaluating the Impact of Code Generation on Software Security

**Inputs**: `spec.md`, `plan.md`, the current research idea, existing artifacts, and any reviewer feedback.

The goal is to deliver a complete, reproducible study that satisfies every functional requirement (FR‑001 – FR‑012) and success‑criterion (SC‑001 – SC‑005).  
Tasks are grouped to keep the total count between 8 – 15 substantive items while preserving all scientific steps.  
Unchecked boxes indicate work that still needs to be performed; checked boxes (if any) remain from prior successful runs.

---

- [X] T001 **Quickstart – environment sanity check** – create a reproducible virtual environment, install the exact pinned dependencies, pull required Docker images, and verify that the environment is functional (e.g., `python --version`, `docker version`).
  *Path*: `scripts/quickstart_env.sh` (script to be created)  
  *Verification*:  
  1. `bash scripts/quickstart_env.sh` exits with code 0.  
  2. Log `logs/quickstart_env.log` contains lines confirming venv activation, successful `pip install -r requirements.txt`, and Docker image pulls.  

- [ ] T002 **Download human‑written vulnerable code** – stream the Python subset of the **Devign** dataset via the HuggingFace `datasets` library, record a SHA‑256 checksum for each shard, and store the raw records under `data/raw/devign/`.   <!-- FAILED-IN-EXECUTION: code/download_devign.py exit=1 -->
  *Path*: `src/ingest/download_devign.py`  
  *Verification*:  
  1. Script finishes without error and creates `data/raw/devign/devign_train.jsonl`.  
  2. A matching checksum entry appears in `data/checksums.json`.  

- [ ] T003 **Filter, retain, and verify OWASP coverage** – keep only rows that (a) contain non‑empty `code`, (b) have a known `vulnerability_label`, and (c) are labelled as Python. Abort with a clear error if fewer than five distinct OWASP Top 10 categories remain. Write the filtered table to `data/processed/human_samples.csv`.  
  *Path*: `src/ingest/filter_devign.py`  
  *Verification*:  
  1. `human_samples.csv` contains **≥ 300 rows** (meeting the power‑analysis requirement).  
  2. The header includes `functionality_id,code,vulnerability_label,language`.  
  3. `data/logs/filter.log` lists at least five distinct vulnerability categories; the script exits with code 0 only in that case.  

- [ ] T004 **Generate LLM‑equivalent snippets** – for every `functionality_id` in `human_samples.csv` invoke the open‑source model **Salesforce/codegen‑350M‑multi** via a `transformers` pipeline (`temperature=0`, `max_new_tokens=512`). Seed `numpy`, `random`, and `torch` with 42 and retry up to three times on API errors. Store generated code in `data/generated/llm_samples.csv` and log the process in `data/logs/generation.log`.  
  *Path*: `src/llm/generate.py`  
  *Verification*:  
  1. Row count of `llm_samples.csv` **exactly matches** that of `human_samples.csv`.  
  2. `generation.log` records the seed, total API call count, and any unrecoverable failures (none for a successful run).  

- [ ] T005 **Validate functional equivalence, security pattern, and compute SC‑001** – for each human/LLM pair:  
  1. Parse with Python `ast` → `syntax_valid`.  
  2. Run the bundled unit‑test suite (`pytest --cov=.`) and require coverage ≥ 90 %.  
  3. Compute semantic similarity with `sentence‑transformers/all‑mpnet‑base‑v2`; require cosine ≥ 0.85.  
  4. Execute `validate/security_pattern.py` to ensure input‑sanitisation checks pass.  
  5. Set `functional_equivalence_verified` to **true** only when **all** the above succeed.  
  6. Persist each validated snippet under `data/validated/human/<functionality_id>.py` and `data/validated/llm/<functionality_id>.py`.  
  7. Write a summary CSV `data/validated/validated_pairs.csv` with columns `functionality_id,source,syntax_valid,functional_equivalence_verified`.  
  *Path*: `src/validate/validate_pairs.py`  
  *Verification*:  
  1. Compute `SC‑001 = (number of LLM samples with functional_equivalence_verified = true) / (total LLM samples)`. The script asserts `SC‑001 ≥ 0.85`; otherwise it aborts with a clear message.  
  2. Every row in `validated_pairs.csv` contains the two boolean flags, and the corresponding `.py` files exist and are syntactically valid.  

- [ ] T006 **Compute code‑size metrics** – for every validated sample (human and LLM) calculate lines‑of‑code using `radon` and cyclomatic complexity via `radon.complexity`. Append these metrics to the `CodeSample` records and write `data/metrics/code_metrics.csv` (columns: `sample_id,source,functionality_id,lines_of_code,cyclomatic_complexity`).  
  *Path*: `src/validate/compute_metrics.py`  
  *Verification*:  
  1. CSV contains a row for **every** validated sample; all numeric fields are non‑negative integers.  
  2. Validation against `code_sample.schema.yaml` passes (`pytest tests/contract/test_contracts.py`).  

- [ ] T007 **Static analysis orchestrator** – runs the suite of static‑analysis sub‑tasks (T007a–T007e) in sequence and verifies overall success.  
  *Path*: `src/analysis/run_static_pipeline.py`  
  *Verification*:  
  1. All sub‑tasks complete without error; a summary log `logs/static_pipeline.log` records successful completion of each step.  

- [ ] T007a **Run Semgrep** – execute Semgrep Docker image (`returntocorp/semgrep:1.46.0`) on both human and LLM validated directories, output JSON files `data/results/semgrep_human.json` and `semgrep_llm.json`.  
  *Path*: `src/analysis/run_semgrep.py`  
  *Verification*:  
  1. Both JSON files are well‑formed and contain at least one finding.  

- [ ] T007b **Run SonarQube Community Edition** – launch SonarQube Docker (`sonarqube:9.9-community`) via scanner on the validated directories, output `data/results/sonarqube_human.json` and `sonarqube_llm.json`.  
  *Path*: `src/analysis/run_sonarqube.py`  
  *Verification*:  
  1. JSON outputs are well‑formed and contain findings.  

- [ ] T007c **Run Bandit** – execute Bandit (`bandit==1.7.8`) on both code sets, producing `data/results/bandit_human.json` and `bandit_llm.json`.  
  *Path*: `src/analysis/run_bandit.py`  
  *Verification*:  
  1. JSON outputs are well‑formed.  

- [ ] T007d **Normalize findings** – ingest all tool‑specific JSON outputs, map confidence scores to the `[0,1]` range, and write a unified Parquet file `data/interim/vuln_findings.parquet` conforming to `VulnerabilityFinding` schema.  
  *Path*: `src/analysis/normalize_findings.py`  
  *Verification*:  
  1. Parquet file passes contract tests and includes findings for **≥ 5** distinct OWASP categories.  

- [ ] T007e **Construct PairOutcome table** – from the normalized findings, create `data/interim/pair_outcomes.csv` with columns `functionality_id,vulnerability_type,human_flag,llm_flag`.  
  *Path*: `src/analysis/construct_pair_outcomes.py`  
  *Verification*:  
  1. CSV has exactly `total_pairs × number_of_vulnerability_types` rows and each `(functionality_id, vulnerability_type)` pair appears once.  

- [ ] T008 **Statistical comparison and confidence‑threshold sensitivity sweep** –  
  1. Load `pair_outcomes.csv` and, for each vulnerability type, perform McNemar’s test (`statsmodels.stats.contingency_tables.mcnemar`). Use exact test when any cell is zero.  
  2. Apply Bonferroni correction across all tested types.  
  3. Write primary results to `data/outputs/analysis_results.csv` following the `AnalysisResult` schema (including `p_value_adj`, `is_significant`, `test_method`).  
  4. Repeat steps 1‑3 for three confidence‑threshold settings: `default‑0.05`, `default`, `default+0.05` (e.g., 0.45, 0.5, 0.55 for Semgrep). Append a `confidence_threshold` column and write the combined table to `data/outputs/sensitivity_results.csv`.  
  *Path*: `src/stats/mcnemar_and_sensitivity.py`  
  *Verification*:  
  1. `analysis_results.csv` passes schema validation.  
  2. At least one row has `is_significant = true` **or** the file includes a comment “No significant differences (all adjusted p ≥ 0.05)”.  
  3. `sensitivity_results.csv` contains exactly three rows per vulnerability type.  

- [ ] T009 **OWASP category coverage check (SC‑005)** – read `analysis_results.csv` and ensure that for each OWASP Top 10 category present in the original dataset there is at least one vulnerability finding (human or LLM). Abort the pipeline with a clear error listing any missing categories.  
  *Path*: `src/validation/owasp_coverage_check.py`  
  *Verification*:  
  1. Script exits with code 0 only when every required category has ≥ 1 finding; otherwise it logs missing categories and exits non‑zero.  

- [ ] T010 **Precision and recall per static‑analysis tool (FR‑008)** – using the ground‑truth labels from the Devign dataset, compare each tool’s findings (from `vuln_findings.parquet`) against the true labels to compute precision and recall per OWASP category. Write `data/metrics/precision_recall.csv` (columns: `tool_source,vulnerability_type,precision,recall`).  
  *Path*: `src/validation/precision_recall.py`  
  *Verification*:  
  1. All precision/recall values lie in `[0, 1]`.  
  2. The CSV passes a sanity‑check test (`pytest tests/precision_recall_test.py`).  

- [ ] T011 **Random audit of ≥ 20 % flagged findings** – stratify the set of all findings by vulnerability type, sample at least 20 % with a fixed seed 42, and for each selected finding run CodeQL (`ghcr.io/github/codeql-action:latest`) and a lightweight AFL‑fast fuzzing harness inside Docker. Update the `validated_by_audit` flag in `vuln_findings.parquet` and export an audit log `data/validation/audit_results.csv`. Log the process in `data/logs/audit.log`.  
  *Path*: `src/audit/manual_audit.py`  
  *Verification*:  
  1. The number of audited rows meets or exceeds the 20 % target.  
  2. `audit.log` records pass/fail outcomes and a derived calibration factor.  

- [ ] T012 **Generate visualisations** – using deterministic `matplotlib` settings (seeded RNG for colours), produce:  
  1. Bar‑chart `figures/vuln_rate_comparison.png` comparing vulnerability rates between human and LLM code (derived from `analysis_results.csv`).  
  2. Line‑chart `figures/sensitivity_plot.png` showing how `p_value_adj` varies across the three confidence thresholds (from `sensitivity_results.csv`).  
  *Path*: `src/report/figures.py`  
  *Verification*:  
  1. Both PNG files are non‑empty and openable with standard image viewers.  
  2. Filenames appear in the final markdown report (see T013).  

- [ ] T013 **Assemble final markdown report** – create `report/report.md` containing:  
  * Dataset statistics (size, SC‑001 compliance).  
  * Table of raw counts and Bonferroni‑adjusted p‑values (`analysis_results.csv`).  
  * Significance statements and discussion of limitations.  
  * Embedded figures (`![](../figures/vuln_rate_comparison.png)`, `![](../figures/sensitivity_plot.png)`).  
  * Description of the manual audit process and its outcomes.  
  * Links to all primary output artifacts (`data/outputs/*`, `data/interim/*`, `data/metrics/*`).  
  *Verification*: `pytest tests/test_report.py` parses the markdown, confirms that every referenced file exists, and that a non‑empty “Results” section is present.  

- [ ] T014 **Pipeline performance monitoring** – wrap the full pipeline execution (`src/run_pipeline.py`) with a Bash wrapper that records start/end timestamps and monitors peak RAM via `psutil`. Write `data/logs/pipeline_performance.log` containing `total_runtime_seconds` and `peak_ram_gb`. CI asserts `total_runtime_seconds ≤ 21600` (6 h) and `peak_ram_gb ≤ 7`.  
  *Path*: `scripts/performance_monitor.sh`  
  *Verification*: After a full run on the target 300‑pair dataset, the log shows values within the limits; the CI job fails otherwise.  

- [ ] T015 **Full pipeline execution on the target dataset (≥ 300 paired samples)** – run the orchestrated pipeline with seed 42 and `--max-pairs 300`. This step performs all steps from T002 through T014, producing the complete set of deliverables required for the study.  
  *Path*: `src/run_pipeline.py` (invoked via `bash scripts/performance_monitor.sh`)  
  *Verification*:  
  1. Exit code 0.  
  2. All files listed in the final report exist and pass their respective contract tests.  
  3. `SC‑001` ratio ≥ 0.85, `SC‑005` coverage satisfied, statistical results present, and power verification from T016 succeeded.  

- [ ] T016 **Validate statistical power (FR‑012)** – after data collection (post‑T005) compute the achieved statistical power for detecting an odds‑ratio ≈ 2.0 with the observed prevalence using `statsmodels.stats.power.GofPower`. Assert that the power is ≥ 80 %; abort with a clear error if not. Record the power value in `data/metrics/power_analysis.csv`.  
  *Path*: `src/validation/power_analysis.py`  
  *Verification*:  
  1. CSV contains a column `power` with a numeric value ≥ 0.80.  
  2. Script exits with code 0 only when the condition is met.  

- [ ] T017 **Verify significance stability across confidence thresholds (FR‑006 & SC‑003)** – compare the `is_significant` flag for each vulnerability type across the three rows in `sensitivity_results.csv`. Assert that the flag does **not** change; if any change is detected, abort and log the discrepancy in `data/logs/stability_check.log`.  
  *Path*: `src/validation/stability_check.py`  
  *Verification*:  
  1. Script exits with code 0 only when all `is_significant` values are identical across thresholds.  
  2. Log records either “stability confirmed” or details of mismatches.  
