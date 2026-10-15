# Tasks: Evaluating the Impact of Code Generation on Software Security

**Inputs**: `spec.md`, `plan.md`, data‑model contracts, and the research requirements listed therein.

The checklist implements the smallest complete end‑to‑end study that satisfies every functional requirement (FR‑001 … FR‑007) and success‑criterion (SC‑001 … SC‑005).  
Tasks are ordered to respect data flow; later tasks depend on the outputs of earlier ones.

---  

- [ ] T001 [P] [US1] **Download the Juliet Test Suite (SARD) vulnerable Python snippets** from the verified URL `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/Juliet-Test-Suite/SARD/master/python_vuln.csv` — HTTP 404].  
  *Path*: `data/raw/juliet/python_vuln.csv`  
  *Verification*: SHA‑256 checksum of the downloaded file matches the value recorded in `data/checksums.json`; the file exists and is readable.

- [ ] T002 [P] [US1] **Filter the downloaded CSV** to retain only rows that contain a non‑empty `code` field, a known `vulnerability_label`, and language = Python. Write the filtered dataset to `data/processed/human_python.csv`. Additionally, abort with an error if the filtered set contains fewer than **five distinct OWASP vulnerability types**.  
  *Verification*: `data/processed/human_python.csv` has ≥ 100 rows, no missing `code` or `vulnerability_label`, and a log `data/logs/filter.log` records the distinct OWASP categories (must be ≥ 5).

- [ ] T003 [P] [US1] **Generate functionally equivalent vulnerable snippets** for every entry in `data/processed/human_python.csv` using the lightweight open‑source model **Salesforce/codegen‑350M‑multi** via the HuggingFace `transformers` pipeline (deterministic: `temperature=0`, `max_new_tokens=512`). Retry up to three times on API errors and pin the random seed (`numpy.random.seed(42)`, `random.seed(42)`). Store generated snippets in `data/generated/llm_samples.json` and record the run in `data/logs/generation.log`.  
  *Verification*: The number of generated samples equals the number of human samples; `data/logs/generation.log` contains the seed, API call counts, and any unrecoverable failures.

- [ ] T004 [P] [US1] **Validate each generated snippet**:  
  1. Perform a syntax check with Python `ast` → add a `syntax_valid` flag.  
  2. Assess functional equivalence **either** by executing the unit‑test suite supplied with the Juliet sample (via `pytest --cov=.`) **or** by computing semantic similarity with `sentence‑transformers/all‑mpnet‑base‑v2`; accept if coverage ≥ 90 % **or** similarity ≥ 0.85.  
  Write a consolidated CSV `data/validated/validated_samples.csv` containing `sample_id, source, functionality_id, syntax_valid, functional_equivalence_verified`.  
  Persist each validated snippet under `data/validated/human/<functionality_id>_human.py` and `data/validated/llm/<functionality_id>_llm.py`.  
  *Verification*: Compute **SC‑001** = `valid_llm / total_prompts`; assert SC‑001 ≥ 0.85. All rows have `functional_equivalence_verified` set appropriately; per‑sample files exist and are syntactically valid.

- [ ] T005 [P] [US2] **Run Semgrep** (Docker image `returntocorp/semgrep:1.46.0`) on the validated code directories `data/validated/human/` and `data/validated/llm/`. Output JSON results to `data/results/semgrep_human.json` and `data/results/semgrep_llm.json`.  
  *Verification*: Each run completes within the 6‑hour job limit; a `memory_monitor.py` ensures peak RAM ≤ 6 GB (OOM events logged in `data/logs/semgrep_oom.log` and offending samples are skipped). Both JSON files are readable and contain at least one finding.

- [ ] T006 [P] [US2] **Run SonarQube Community Edition** (Docker image `sonarqube:9.9-community`) on the same validated code sets via the official scanner. Export findings through the SonarQube REST API to `data/results/sonarqube_human.json` and `data/results/sonarqube_llm.json`.  
  *Verification*: Resource constraints identical to T005; OOM events logged in `data/logs/sonarqube_oom.log`; HTTP 200 for each export; both JSON files are readable and contain at least one finding.

- [ ] T007 [P] [US3] **Normalize findings** from Semgrep and SonarQube to the `VulnerabilityFinding` schema and write a unified Parquet file `data/interim/vuln_findings.parquet`. Map SonarQube severity to a numeric confidence (CRITICAL = 1.0, HIGH = 0.75, MEDIUM = 0.5, LOW = 0.25).  
  *Verification*: `tests/contract/test_contracts.py` passes; the Parquet file contains findings for ≥ 5 distinct OWASP vulnerability types that also appear in the ground‑truth dataset.

- [ ] T008 [P] [US3] **Construct the PairOutcome table** required for the paired McNemar test. For every `functionality_id` and every vulnerability type, record `human_flag` (1 if a finding exists for the human sample, else 0) and `llm_flag` (similarly for the LLM sample). Write the result to `data/interim/pair_outcomes.csv`.  
  *Verification*: Each pair appears exactly once per vulnerability type; row count equals `total_pairs × number_of_vulnerability_types`.

- [ ] T009 [P] [US3] **Perform statistical comparison**:  
  * For each vulnerability type, apply McNemar’s test (`statsmodels.stats.contingency_tables.mcnemar`) on the **bias‑corrected** counts produced by T015.  
  * If any cell in the 2×2 table is zero, re‑run with `exact=True`.  
  * Apply Bonferroni correction across all tested types.  
  Write the final results to `data/outputs/analysis_results.csv` following the `AnalysisResult` schema (including `p_value_adj`, `is_significant`, `test_method`).  
  *Verification*: All required columns are present; at least one type yields `is_significant = true` **or** the report explicitly states “no significant differences” with the adjusted p‑values.

- [ ] T010 [P] [US3] **Conduct a sensitivity sweep** over confidence thresholds `{0.0, 0.5, 0.9}`. For each threshold, repeat the aggregation (T008) and statistical test (T009) and store the outcomes in `data/outputs/sensitivity_results.csv` (additional column `confidence_threshold`).  
  *Verification*: The CSV contains three rows per vulnerability type (one per threshold) and records the variation in `p_value_adj`.

- [ ] T011 [P] [US4] **Audit a random subset** of flagged findings: select ≥ 20 % of findings (stratified by vulnerability type) using a fixed seed (`42`). Run a lightweight fuzzing harness (`afl‑fast` in Docker) or a manual reviewer script on those samples; update the `validated_by_audit` flag and write `data/validation/audit_results.csv`. Log the process in `data/logs/audit.log`.  
  *Verification*: The number of audited samples matches the target proportion; `audit.log` records pass/fail outcomes and the calibration factor derived from the audit.

- [ ] T012 [P] [US5] **Generate visualisations**:  
  * Bar‑chart comparing vulnerability rates between human and LLM code → `figures/vuln_rate_comparison.png`.  
  * Line‑chart showing sensitivity‑sweep p‑values → `figures/sensitivity_plot.png`.  
  Use `matplotlib` with a deterministic style (seeded random colour map).  
  *Verification*: Both PNG files are non‑empty, readable, and referenced in the final report.

- [ ] T013 [P] [US5] **Assemble the final markdown report** `report/report.md` containing:  
  * Dataset statistics (size, SC‑001 compliance).  
  * Table of raw counts and Bonferroni‑adjusted p‑values (from `analysis_results.csv`).  
  * Significance statements and discussion of limitations.  
  * Embedded figures (`![](../figures/vuln_rate_comparison.png)`, `![](../figures/sensitivity_plot.png)`).  
  * Description of the manual audit process and its outcomes.  
  * Links to all primary output artifacts (`data/outputs/*`).  
  *Verification*: The report builds without broken links; `pytest tests/test_report.py` parses the markdown and confirms that every referenced file exists.

- [ ] T014 [P] [SC‑004] **Measure pipeline performance**: a wrapper script records start/end timestamps and monitors peak RAM usage (via `psutil`). After the final task, write `data/logs/pipeline_performance.log` containing `total_runtime_seconds` and `peak_ram_gb`.  
  *Verification*: CI asserts `total_runtime_seconds ≤ 21600` (6 h) and `peak_ram_gb ≤ 7`; failure aborts the run.

- [ ] T015 [P] [FR‑004] **Compute bias‑correction factors and apply them**:  
  1. Split the validated dataset into a training subset (80 %) and a held‑out validation subset (20 %).  
  2. Run Semgrep and SonarQube on the held‑out subset to obtain true positives/false positives against the known Juliet labels, compute precision and recall for each tool.  
  3. Derive weighting factors (e.g., inverse‑precision) and apply them to the raw vulnerability counts from T007, producing bias‑corrected counts saved as `data/processed/bias_corrected_counts.csv`.  
  *Verification*: The precision/recall calculation script outputs a summary JSON; the corrected counts file contains the same columns as the raw counts plus a `weight` column, and downstream statistical tasks (T009) consume this file.  

---  

## Dependency Summary

| Requirement | Covered by Task(s) |
|-------------|--------------------|
| FR‑001, SC‑001 | T001‑T004 |
| FR‑002, SC‑004 | T005‑T006, T014 |
| FR‑003, SC‑005 | T007 |
| FR‑004 | T008‑T011, **T015** |
| FR‑005 | T012‑T013 |
| FR‑006 | T010 |
| FR‑007 | T002, T004 (exclusion logic) |

All tasks are currently unchecked; execution in the order presented will produce a fully reproducible end‑to‑end analysis that satisfies the specification and the success criteria.