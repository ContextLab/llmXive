# Tasks: Evaluating the Impact of Code Generation on Software Security

**Inputs**: `spec.md`, `plan.md`, data‑model contracts, and the research requirements listed therein.

The checklist implements the smallest complete end‑to‑end study that satisfies every functional requirement (FR‑001 … FR‑007) and success‑criterion (SC‑001 … SC‑005).  
Tasks are ordered to respect data flow; later tasks depend on the outputs of earlier ones.

---

- [ ] T001 [P] [US1] **Download the Devign dataset (vulnerable C/C++ code) from the verified URL `[UNRESOLVED-CLAIM: https://github.com/anishathalye/devign-dataset/archive/refs/heads/master.zip`.** — HTTP 404] Extract the CSV `devign-master/devign.csv` to `data/raw/devign/devign.csv` and verify its SHA‑256 checksum (recorded in `data/checksums.json`).   <!-- FAILED-IN-EXECUTION: code/download_devign.py exit=1 -->
  *Verification*: `sha256sum data/raw/devign/devign.csv` matches the recorded value; the file exists and is readable.

- [ ] T002 [P] [US1] **Filter the downloaded CSV** to retain only rows that contain a non‑empty `code` field, a known `vulnerability_label`, and a language supported by our pipeline (Python). Write the filtered dataset to `data/processed/human_python.csv`. Additionally, verify that the filtered ground‑truth dataset contains at least **five distinct OWASP vulnerability types**; abort with an error if this condition is not met.   <!-- FAILED-IN-EXECUTION: code/filter_human_python.py exit=1 -->
  *Verification*: row count ≥ 100, no rows with missing `code` or `vulnerability_label`; a log `data/logs/filter.log` records the number of excluded rows and the distinct OWASP categories discovered (must be ≥ 5).

- [ ] T003 [P] [US1] **Generate functionally equivalent vulnerable snippets** for every entry in `data/processed/human_python.csv` using a **public LLM API** (e.g., OpenAI `gpt-4o` via `openai.ChatCompletion`). Use a deterministic prompt, `temperature=0`, `max_new_tokens=1024`, and retry up to 3 times on API errors. **Pin the random seed** (`numpy.random.seed(42)`, `random.seed(42)`) before any sampling and record the seed value in `data/logs/generation.log`. Store generated snippets in `data/generated/llm_samples.json`.  
  *Verification*: number of generated samples equals number of human samples; `data/logs/generation.log` records seed, API call counts, and any unrecoverable failures.

- [ ] T004 [P] [US1] **Validate each generated snippet**:  
  1. Perform a syntax check with Python `ast` → add `syntax_valid` flag.  
  2. Assess functional equivalence **either** by running the unit‑test suite supplied with the Devign sample (`pytest --cov=.`) **or** by computing semantic similarity using `sentence‑transformers/all‑mpnet‑base‑v2`; accept if coverage ≥ 90 % **or** similarity ≥ 0.85.  
  Write a consolidated CSV `data/validated/validated_samples.csv` containing columns `sample_id, source, functionality_id, syntax_valid, functional_equivalence_verified`. Also write each validated snippet to `data/validated/human/` or `data/validated/llm/` as `<functionality_id>_<source>.py`.  
  *Verification*: compute SC‑001 = `valid_llm / total_prompts`; assert SC‑001 ≥ 0.85. All rows have `functional_equivalence_verified` set appropriately; per‑sample files exist and are syntactically valid.

- [ ] T005 [P] [US2] **Run Semgrep** (Docker image `returntocorp/semgrep:1.46.0`) on the validated code directories `data/validated/human/` and `data/validated/llm/`. Output JSON results to `data/results/semgrep_human.json` and `data/results/semgrep_llm.json`.  
  *Verification*: each run completes within the 6‑hour job limit; `memory_monitor.py` ensures RAM usage never exceeds 6 GB (OOM events logged in `data/logs/semgrep_oom.log` and offending samples skipped); both JSON files are created, readable, and contain at least one finding.

- [ ] T006 [P] [US2] **Run SonarQube Community Edition** (Docker image `sonarqube:9.9-community`) on the same code sets via the official scanner. Export findings through the SonarQube REST API to `data/results/sonarqube_human.json` and `data/results/sonarqube_llm.json`.  
  *Verification*: resource constraints identical to T005; OOM events logged in `data/logs/sonarqube_oom.log`; HTTP status 200 for each export; both JSON files are created, readable, and contain at least one finding.

- [ ] T007 [P] [US3] **Normalize findings** from Semgrep and SonarQube to the `VulnerabilityFinding` schema and write a unified Parquet file `data/interim/vuln_findings.parquet`. Map SonarQube severity to a numeric confidence (CRITICAL = 1.0, HIGH = 0.75, MEDIUM = 0.5, LOW = 0.25). Verify that the normalized findings contain **≥ 5 distinct OWASP vulnerability types that are also present in the ground‑truth dataset** (as ensured by T002).  
  *Verification*: `tests/contract/test_contracts.py` passes; the file contains findings for ≥ 5 distinct OWASP categories verified against ground truth.

- [ ] T008 [P] [US3] **Construct the PairOutcome table** required for the paired McNemar test. For every `functionality_id` and every vulnerability type, record `human_flag` and `llm_flag` (1 = vulnerability detected, 0 = not) and write `data/interim/pair_outcomes.csv`.  
  *Verification*: each pair appears exactly once per vulnerability type; row count equals `total_pairs × number_of_types`.

- [ ] T009 [P] [US3] **Perform statistical comparison**:  
  * For each vulnerability type, apply McNemar’s test (`statsmodels.stats.contingency_tables.mcnemar`).  
  * If any cell in the 2×2 table is zero, re‑run with `exact=True`.  
  * Apply Bonferroni correction across all tested types.  
  Write the final results to `data/outputs/analysis_results.csv` following the `AnalysisResult` schema (including `p_value_adj`, `is_significant`, `test_method`).  
  *Verification*: all required columns present; at least one type yields `is_significant = true` **or** the report clearly states “no significant differences” with the adjusted p‑values.

- [ ] T010 [P] [US3] **Conduct a sensitivity sweep** over confidence thresholds `{0.0, 0.5, 0.9}`. For each threshold, repeat the aggregation (T008) and statistical test (T009) and store the outcomes in `data/outputs/sensitivity_results.csv` (additional column `confidence_threshold`).  
  *Verification*: the CSV contains three rows per vulnerability type (one per threshold) and documents the variation in `p_value_adj`.

- [ ] T011 [P] [US4] **Audit a random subset** of flagged findings: select ≥ 10 % of findings (stratified by vulnerability type) using a fixed seed (`42`). Run a lightweight fuzzing harness (`afl‑fast` in Docker) or a manual reviewer script on those samples; update the `validated_by_audit` flag in `data/validation/audit_results.csv`.  
  *Verification*: number of audited samples matches the target proportion; audit log `data/logs/audit.log` records pass/fail outcomes.

- [ ] T012 [P] [US5] **Generate visualisations**:  
  * Bar‑chart comparing vulnerability rates between human and LLM code (`figures/vuln_rate_comparison.png`).  
  * Line‑chart showing sensitivity‑sweep p‑values (`figures/sensitivity_plot.png`).  
  Use `matplotlib` with a deterministic style.  
  *Verification*: both PNG files are created, non‑empty, and referenced in the final report.

- [ ] T013 [P] [US5] **Assemble the final markdown report** `report/report.md` containing:  
  * Summary of dataset statistics (size, SC‑001).  
  * Table of raw counts and adjusted p‑values (from `analysis_results.csv`).  
  * Significance statements and any limitations.  
  * Embedded figures (`![](../figures/vuln_rate_comparison.png)`).  
  * Description of the manual audit process and its outcomes.  
  * Links to all primary output artifacts (`data/outputs/*`).  
  *Verification*: the report builds without broken links; `pytest tests/test_report.py` parses the markdown and confirms that every referenced file exists.

- [ ] T014 [P] [SC‑004] **Measure pipeline performance**: a wrapper script records start/end timestamps and monitors peak RAM usage (via `psutil`). After the final task, write `data/logs/pipeline_performance.log` containing `total_runtime_seconds` and `peak_ram_gb`.  
  *Verification*: CI asserts `total_runtime_seconds ≤ 21600` (6 h) and `peak_ram_gb ≤ 7`; failure aborts the run.

---  

## Dependency Summary

| Requirement | Covered by Task(s) |
|-------------|-------------------|
| FR‑001, SC‑001 | T001‑T004 |
| FR‑002, SC‑004 | T005‑T006, T014 |
| FR‑003, SC‑005 | T007 |
| FR‑004 | T008‑T011 |
| FR‑005 | T012‑T013 |
| FR‑006 | T010 |
| FR‑007 | T002, T004 (exclusion logic) |

All tasks are unchecked and ready to be executed in the order presented. The pipeline will produce a fully reproducible end‑to‑end analysis that satisfies the specification and the success criteria.