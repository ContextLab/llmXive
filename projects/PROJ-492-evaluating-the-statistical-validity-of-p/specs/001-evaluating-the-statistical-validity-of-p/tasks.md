# Tasks: Evaluating the Statistical Validity of Public A/B Test Summaries

**Inputs**: active `spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer feedback.  

The goal is to deliver a reproducible end‑to‑end audit pipeline that satisfies every functional requirement (FR‑001 … FR‑031b) and success‑criteria (SC‑001 … SC‑031b) in the specification while remaining within the GitHub‑Actions resource caps (FR‑009).

---

## Phase 1 – Setup and first end‑to‑end analysis  

- [ ] T001 [US1] Consolidate the project layout under `code/src/audit/` (CLI, extraction, reconstruction, Monte‑Carlo, power‑analysis, synthetic‑generator modules). Remove any duplicated `PT###` entries, ensure all imports work, and document the runnable command in `specs/001-evaluating-the-statistical-validity-of-p/quickstart.md`.
  - **Verification**: `python -m code.src.audit.run_audit --help` exits with status 0; `quickstart.md` contains the exact command `python -m code.src.audit.run_audit data/input/urls.csv output/`.  

- [ ] T017 [US1] Curate a deterministic corpus of **≥ 300** reachable URLs pointing to public A/B test summaries, write them to `data/input/urls.csv`, download each page, and store the raw HTML snapshot under `data/raw/`. Generate `data/checksums.txt` with SHA‑256 hashes of all snapshots.   <!-- FAILED-IN-EXECUTION: code/src/audit/curate_corpus.py exit=1 -->
  - **Verification**: `urls.csv` has ≥ 300 rows; every URL has a corresponding file in `data/raw/`; all hashes are present in `data/checksums.txt`.  

- [ ] T004 [US1] Create `code/src/audit/monte_carlo_validation.py` that runs **10 000** Monte‑Carlo replicates for each statistical routine (two‑proportion z/Fisher, Welch’s t, binomial test). Compare the SciPy/StatsModels result to the Monte‑Carlo estimate and assert an absolute difference ≤ 0.005. Write `output/monte_carlo_validation_report.json` summarising each test’s difference and a pass flag.  
  - **Verification**: script exits 0; the JSON lists all four tests, each `diff` ≤ 0.005; any failure logs an `ERR‑801` and aborts the pipeline.  

- [ ] T005 [US1] Run the full audit end‑to‑end on the corpus created by T017 using `code/src/audit/run_audit.py`. The pipeline must ingest URLs, fetch HTML, extract fields into `ABSummary` records, reconstruct p‑values/effect sizes, flag inconsistencies (FR‑004/FR‑004b), and write:  
  - `output/audit_report.json` (conforms to `audit_report.schema.yaml`)  
  - `output/audit_records.parquet` (optional intermediate)  
  - `output/parsing_errors.log` (contains `ERR‑###` messages).  
  - **Verification**: JSON validates against the schema; parsing‑error rate ≤ 5 % (SC‑005); at least one synthetic record with `diff_abs_p = 0.06` is flagged inconsistent.  

---

## Phase 2 – Complete the study and validate its evidence  

- [ ] T006 [US1] Execute `code/src/audit/power_analysis.py` to compute the minimum sample size **N** needed for a two‑sided binomial test that detects an inconsistency proportion of 0.10 with α = 0.05 and power ≥ 0.80 (FR‑025). Write the result to `output/power_analysis.json` and ensure the actual corpus size from T017 meets or exceeds this N.  
  - **Verification**: JSON contains fields `required_N` and `achieved_N`; `achieved_N ≥ required_N`.  

- [ ] T007 [US1] Evaluate the inconsistency‑detection logic on a **synthetically generated** dataset (generated on‑the‑fly inside this task, no separate generator). Compute precision, recall, and F1 for the flagging of `is_inconsistent`. Write `output/synthetic_validation_report.json`.  
  - **Verification**: precision ≥ 0.90, recall ≥ 0.80, F1 ≥ 0.85; report includes a `pass: true` flag; any shortfall logs `ERR‑800`.  

- [ ] T018 [US1] Author the annotation protocol for the real‑world extraction validation set (FR‑031b). Store the markdown at `docs/annotation_protocol.md` and include: stratified sampling plan, dual‑annotator workflow, third‑annotator resolution, label schema, and quality‑control checklist.  
  - **Verification**: file exists, contains all required sections, and is referenced by T019.  

- [ ] T019 [US1] Build the real‑world extraction validation set (≥ 100 summaries, ≥ 20 per domain) following the protocol in T018. Store the human‑verified ground‑truth labels in `data/manual_validation/real_world_labels.csv`. Run the extraction module on this set, compute field‑level extraction accuracy (≥ 95 % – SC‑001) and precision/recall/F1 for the three key fields (≥ 85 % precision, ≥ 75 % recall, F1 ≥ 0.80 – SC‑031b). Write `output/real_world_validation_report.json`.  
  - **Verification**: CSV has ≥ 100 rows with the required domain distribution; the report lists `field_accuracy`, `precision`, `recall`, `f1_score`, and a `pass: true` flag.  

- [ ] T008 [US2] Implement the prevalence analysis in `code/src/audit/prevalence.py`:  
  1. Perform a two‑sided binomial test of the observed inconsistency proportion against the baseline 0.05 (FR‑005a).  
  2. Compute a 95 % Wilson confidence interval (SC‑014) and ensure its total width ≤ 0.10.  
  3. Conduct the sensitivity sweep over baseline proportions 0.02–0.10 (step 0.01) and verify that the maximum change in prevalence across the sweep is < 0.02 (SC‑015).  
  Write `output/prevalence.json`.  
  - **Verification**: JSON contains `p_value`, `wilson_ci_lower`, `wilson_ci_upper`, `sensitivity_variation`; all thresholds satisfied; entries flagged for sample‑size mismatch (FR‑004b) are excluded.  

- [ ] T009 [US2] Perform domain‑bias assessment and subgroup analyses in `code/src/audit/bias_assessment.py`:  
  1. Compute domain‑frequency distribution; if any domain exceeds 30 % of the corpus, down‑sample to a maximum of 30 % and log a `bias_warning`.  
  2. Calculate a domain‑weighted bias‑adjusted inconsistency rate.  
  3. For each domain and for each publication‑year with ≥ 10 summaries, run a Fisher’s exact test (or chi‑square) and apply Bonferroni correction.  
  Write `output/bias_report.json` and `output/subgroup_report.csv`.  
  - **Verification**: JSON contains `raw_rate`, `bias_adjusted_rate`; CSV includes columns `domain`, `year`, `inconsistent_count`, `total`, `rate`, `p_value_adj`; no domain > 30 % after down‑sampling.  

- [ ] T010 [US2] Generate the final aggregated summary artefacts:  
  1. `output/summary_report.csv` with columns `total_summaries`, `inconsistent_count`, `inconsistent_rate`, `bias_adjusted_rate`, `wilson_ci_lower`, `wilson_ci_upper`.  
  2. Run `code/src/audit/export_validator.py` to cross‑check that the counts in `audit_report.json` match those in `summary_report.csv`; any mismatch logs `ERR‑201`.  
  3. Compute SHA‑256 checksums for **all** files under `data/` and `output/` (producing `data/checksums.txt` and `output/checksums.txt`).  
  4. Create `output/manifest.json` (conforms to `manifest.schema.yaml`) that records the run ID, timestamps, status, list of output files, checksums, and resource‑usage metrics.  
  - **Verification**: CSV exists with exact column names; JSON↔CSV counts identical; both checksum files contain a line for every file; `manifest.json` validates; total runtime ≤ 6 h, RAM ≤ 2 GB, CPU ≤ 2 vCPUs (SC‑008).  

- [ ] T099 [US2] Run the Constitution‑compliance audit (`code/src/audit/constitution_audit.py`). The script must verify Principles I‑VII (reproducibility, verified accuracy, data hygiene, single source of truth, versioning, statistical consistency, source provenance). Write `output/constitution_audit_report.json`.  
  - **Verification**: report lists each principle with `status: pass`; any failure aborts the pipeline.  

---

## Phase 3 – Reproducible results and paper handoff  

- [ ] T011 [US2] Write the Quickstart guide (`README_QUICKSTART.md`) that a novice can follow to run the audit on a **30‑URL** sample within **30 minutes** on the default GitHub‑Actions runner. Include the exact command, expected runtime, and a verification step that writes `output/novice_verification.log` containing a timestamped success message.  
  - **Verification**: guide exists; running the documented command on the sample completes ≤ 30 min and produces the log file; the log contains the phrase `Quickstart verification successful`.  

- [ ] T012 [US2] Draft a concise methods‑and‑results account in `specs/001-evaluating-the-statistical-validity-of-p/results.md`. The document must:  
  1. Cite every numeric claim (prevalence, CI, bias‑adjusted rate, synthetic precision/recall, real‑world extraction accuracy) and link it to the exact output file.  
  2. Explicitly state the methodological limitation that the audit tests **internal statistical consistency only** (cannot assess external data fidelity).  
  3. Note the heuristic baseline handling (FR‑012) and its flag in audit notes.  
  - **Verification**: each number in the text is accompanied by a footnote referencing a file path; the limitations paragraph is present.  

- [ ] T013 [US2] Perform a full reproducibility run: reset the workspace (remove `output/`), then execute the documented workflow from the seed‑controlled entry point (`python -m code.src.audit.run_audit data/input/urls.csv output/ --seed 42`). Verify that all deterministic artefacts (synthetic files, Monte Carlo report, power analysis, manifest) are byte‑identical to the previously committed versions, and that all success criteria (SC‑001 … SC‑031b) still hold. Document the handoff in `specs/001-evaluating-the-statistical-validity-of-p/handoff.md` by listing the artefacts that the downstream paper pipeline will consume.  
  - **Verification**: a diff of the regenerated deterministic files against the repository shows no differences; the handoff markdown lists `audit_report.json`, `summary_report.csv`, `prevalence.json`, `bias_report.json`, `real_world_validation_report.json`, and `constitution_audit_report.json`.  

---

## Dependencies and requirement coverage  

| Requirement | Satisfying Task(s) |
|-------------|--------------------|
| FR‑001, FR‑002 | T005 |
| FR‑003 | T005 |
| FR‑004, FR‑004b | T005 |
| FR‑005a, FR‑005b | T008 |
| FR‑007 | T005 |
| FR‑009 | T010 |
| FR‑012 | T005 |
| FR‑024 | T010 |
| FR‑025 | T006 |
| FR‑026 | T004 |
| FR‑028 | T011 |
| FR‑031b | T019 |
| SC‑001 | T019 |
| SC‑003, SC‑026 | T004 |
| SC‑005 | T005 |
| SC‑008 | T010 |
| SC‑013 | T010 |
| SC‑014, SC‑015 | T008 |
| SC‑024, SC‑025, SC‑028 | T010, T011 |
| SC‑031b | T019 |

---===END TASKS===---