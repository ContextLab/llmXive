# Tasks: Evaluating the Statistical Validity of Public A/B Test Summaries  

**Inputs**: active `spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer feedback.  

The goal is to deliver a reproducible end‑to‑end audit pipeline that satisfies every functional requirement (FR‑001 … FR‑031b) and success‑criteria (SC‑001 … SC‑031b) in the specification while remaining within the GitHub‑Actions resource caps (FR‑009).  

---  

## Phase 1 – Setup and first end‑to‑end analysis  

- [ ] **T001** [US1] Consolidate the project layout under `code/src/audit/` (CLI, extraction, reconstruction, Monte‑Carlo, power‑analysis, synthetic‑generator modules), document the runnable command in `specs/001-evaluating-the-statistical-validity-of-p/quickstart.md`.  
  - **Verification**: `python -m code.src.audit.run_audit --help` exits with status 0 and the quickstart file contains the exact command `python -m code.src.audit.run_audit data/input/urls.csv output/`.  

- [ ] **T017** [US1] Curate a deterministic corpus of **≥ 300** reachable URLs that point to public A/B‑test summaries, write them to `data/input/urls.csv`, download each page and store the raw HTML snapshot under `data/raw/`, then generate SHA‑256 checksums for every snapshot in `data/checksums.txt`.  
  - **Verification**: `urls.csv` contains ≥ 300 rows; for every URL there is a corresponding file in `data/raw/`; `data/checksums.txt` lists a hash line for each snapshot; all downloads return HTTP 200 and HTML content (no dead links).  

- [ ] **T004** [US1] Implement `code/src/audit/monte_carlo_validation.py` that runs **10 000** Monte‑Carlo replicates for each statistical routine (two‑proportion z/Fisher, Welch’s t, binomial test). Compare the SciPy/StatsModels result to the Monte‑Carlo estimate and assert that the absolute difference ≤ 0.005. Write the summary to `output/monte_carlo_validation_report.json`.  
  - **Verification**: script exits 0; the JSON contains entries for all four tests with a field `diff` ≤ 0.005 and a top‑level flag `pass: true`. Any failure logs an `ERR‑801` and aborts the pipeline.  

- [ ] **T005** [US1] Run the full audit pipeline on the corpus created by **T017** using `code/src/audit/run_audit.py`. The pipeline must:  
  1. ingest `data/input/urls.csv`,  
  2. fetch HTML,  
  3. extract required fields into `ABSummary` records (FR‑002),  
  4. reconstruct p‑values/effect sizes (FR‑003, FR‑012),  
  5. flag inconsistencies according to FR‑004/FR‑004b,  
  6. write `output/audit_report.json` (conforms to `audit_report.schema.yaml`),  
  7. write a parsing‑error log `output/parsing_errors.log` containing `ERR‑###` codes.  
  - **Verification**: `audit_report.json` validates against its schema; parsing‑error rate ≤ 5 % of total URLs (SC‑005); at least one record where `|reported_p – reconstructed_p| = 0.06` is flagged `inconsistent`; overall field‑level extraction accuracy (proportion of correctly captured fields) is ≥ 95 % (SC‑001); precision/recall/F1 for the three key fields are validated separately in **T019** (SC‑031b).  

---  

## Phase 2 – Complete the study and validate its evidence  

- [ ] **T006** [US1] Execute `code/src/audit/power_analysis.py` to compute the minimum sample size **N** required for a two‑sided binomial test that detects an inconsistency proportion of 0.10 with α = 0.05 and power ≥ 0.80 (FR‑025). Write the result to `output/power_analysis.json` and confirm that the actual corpus size from **T017** meets or exceeds this `required_N`.  
  - **Verification**: JSON contains fields `required_N` and `actual_N`; `actual_N ≥ required_N`.  

- [ ] **T007** [US1] Generate a synthetic validation dataset on‑the‑fly inside the task (no pre‑existing generator), run the full audit logic on it, and compute precision, recall, and F1 for the flag `is_inconsistent`. Write `output/synthetic_validation_report.json`.  
  - **Verification**: report shows `precision ≥ 0.90`, `recall ≥ 0.80`, `f1_score ≥ 0.85`, and a top‑level `pass: true`. Any shortfall logs `ERR‑800`.  

- [ ] **T018** [US1] Author the annotation protocol for the real‑world extraction validation set (FR‑031b) and store it at `docs/annotation_protocol.md`. The protocol must detail: stratified sampling plan (≥ 20 per domain, 5 domains), dual‑annotator workflow, third‑annotator resolution, label schema, and quality‑control checklist.  
  - **Verification**: file exists, contains all required sections, and is referenced by **T019**.  

- [ ] **T019** [US1] Build the real‑world extraction validation set (≥ 100 summaries, ≥ 20 per domain) following the protocol in **T018**. Store human‑verified ground‑truth labels in `data/manual_validation/real_world_labels.csv`. Run the extraction module on this set, compute field‑level extraction accuracy (≥ 95 % – SC‑001) and precision/recall/F1 for the three key fields (≥ 85 % precision, ≥ 75 % recall, F1 ≥ 0.80 – SC‑031b). Write `output/real_world_validation_report.json`.  
  - **Verification**: CSV has ≥ 100 rows with correct domain distribution; the JSON reports `field_accuracy ≥ 0.95` (SC‑001), `precision ≥ 0.85`, `recall ≥ 0.75`, `f1_score ≥ 0.80` (SC‑031b), and `pass: true`.  

- [ ] **T008** [US2] Implement the prevalence analysis in `code/src/audit/prevalence.py`:  
  1. Perform a two‑sided binomial test of the observed inconsistency proportion against the baseline 0.05 (FR‑005a).  
  2. Compute a 95 % Wilson confidence interval (SC‑014) and ensure its total width ≤ 0.10.  
  3. Sweep baseline proportions from 0.02 to 0.10 (step 0.01) and verify that the maximum variation in estimated prevalence is < 0.02 (SC‑015).  
  Write results to `output/prevalence.json`.  
  - **Verification**: JSON contains `p_value`, `wilson_ci_lower`, `wilson_ci_upper`, `ci_width ≤ 0.10`, and `sensitivity_variation < 0.02`.  

- [ ] **T010** [US2] Generate the final aggregated summary artifacts:  
  1. `output/summary_report.csv` with columns `total_summaries`, `inconsistent_count`, `inconsistent_rate`, `bias_adjusted_rate`, `wilson_ci_lower`, `wilson_ci_upper`.  
  2. Run `code/src/audit/export_validator.py` to cross‑check that the counts in `output/audit_report.json` exactly match those in `summary_report.csv`; any mismatch logs `ERR‑201`.  
  3. Compute SHA‑256 checksums for **all** files under `data/` and `output/`, producing `data/checksums.txt` and `output/checksums.txt`.  
  4. Create `output/manifest.json` conforming to `manifest.schema.yaml` that records run ID, timestamps, status, list of output files, checksums, and resource‑usage metrics (CPU time, peak memory, total runtime).  
  - **Verification**: CSV exists with exact column names; validator reports “counts match”; both checksum files contain a line for every file; `manifest.json` validates against its schema; total runtime ≤ 6 h, RAM ≤ 2 GB, CPU ≤ 2 vCPUs (SC‑008).  

- [ ] **T099** [US2] Run the Constitution‑compliance audit (`code/src/audit/constitution_audit.py`). The script must verify Principles I‑VII (including Principle II “Verified Accuracy” by invoking the Reference‑Validator on all citation strings in the repository) and write `output/constitution_audit_report.json`.  
  - **Verification**: JSON lists each principle with `status: pass`; any failure aborts the pipeline.  

---  

## Phase 3 – Reproducible results and paper handoff  

- [ ] **T011** [US2] Write the Quickstart guide (`README_QUICKSTART.md`) that a novice can follow to run the audit on a **30‑URL** sample within **30 minutes** on the default GitHub‑Actions runner. Include the exact command, expected runtime, and a verification step that produces `output/novice_verification.log` containing the phrase `Quickstart verification successful`.  
  - **Verification**: guide file exists; executing the documented command on the 30‑URL sample completes ≤ 30 min and creates the log file with the required phrase.  

- [ ] **T012** [US2] Draft a concise methods‑and‑results account in `specs/001-evaluating-the-statistical-validity-of-p/results.md`. The document must:  
  1. Cite every numeric claim (prevalence, CI, bias‑adjusted rate, synthetic precision/recall, real‑world extraction accuracy) and link each to the exact output file path.  
  2. Explicitly state the methodological limitation that the audit tests **internal statistical consistency only** (cannot assess external data fidelity).  
  3. Note the heuristic baseline handling (FR‑012) and its flag in audit notes.  
  - **Verification**: each number in the text is accompanied by a footnote referencing a file; the limitations paragraph is present; the baseline‑heuristic note is mentioned.  

- [ ] **T013** [US2] Perform a full reproducibility run: delete the `output/` directory, then execute the documented workflow from the seed‑controlled entry point (`python -m code.src.audit.run_audit data/input/urls.csv output/ --seed 42`). Verify that all deterministic artefacts (synthetic files, Monte‑Carlo report, power analysis, manifest) are byte‑identical to the committed versions and that all success criteria (SC‑001 … SC‑031b) still hold. Document the handoff in `specs/001-evaluating-the-statistical-validity-of-p/handoff.md` by listing the artefacts the downstream paper pipeline will consume.  
  - **Verification**: `git diff --quiet` shows no differences for the deterministic files; the handoff markdown lists `audit_report.json`, `summary_report.csv`, `prevalence.json`, `bias_report.json`, `real_world_validation_report.json`, `constitution_audit_report.json`, and `manifest.json`.  

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
| SC‑001 | T005 (field‑level accuracy) |
| SC‑003, SC‑026 | T004 |
| SC‑005 | T005 |
| SC‑008 | T010 |
| SC‑013 | T010 |
| SC‑014, SC‑015 | T008 |
| SC‑024, SC‑025, SC‑028 | T010, T011 |
| SC‑031b | T019 |
| Constitution II (Verified Accuracy) | T099 (Reference‑Validator invoked) |

---===END TASKS===---