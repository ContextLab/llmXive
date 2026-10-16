# Tasks: Evaluating the Statistical Validity of Public A/B Test Summaries

**Inputs**: Active `spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer feedback (Feynman reviewer, 2026-06-27).

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 [P1] [US1] Repair the task‑identity and layout damage: consolidate the duplicated T001–T004/PT000–PT004 entries into a single canonical source layout under `code/src/` (CLI `code/src/cli/run_audit.py`, statistics `code/src/audit/stat_verification.py`, Monte Carlo core `code/src/audit/monte_carlo_core.py`, power analysis `code/src/audit/power_analysis.py`, synthetic generator `code/src/audit/synthetic.py`, annotation protocol `code/src/audit/annotation_protocol.md`), remove the alias `PT###` duplicates, and document the runnable command in `specs/001-evaluating-the-statistical-validity-of-p/quickstart.md`. Preserve the verified implementations from the previously checked tasks (ingestor, fetcher, extractor, reconstructor, validator, prevalence scaffolding, report generator, manifest, resource monitor) by moving them into `code/src/audit/` without behavioral change.  
  - Verification: `python -m code.src.cli.run_audit --help` exits 0; every module under `code/src/audit/` imports; no duplicate task IDs remain in `tasks.md`; `quickstart.md` names the exact command.

- [ ] T017 [P1] [US1] Generate a deterministic corpus of public A/B test summary URLs: curate ≥ 300 reachable URLs, write them to `data/input/urls.csv`, and for each URL download and store the raw HTML snapshot under `data/raw/` (used for reproducible re‑runs).  
  - Verification: `data/input/urls.csv` exists with ≥ 300 rows; each URL has a corresponding file in `data/raw/`; checksum file `data/checksums.txt` includes all snapshots.

- [ ] T002 [P1] [US1] Rebuild the synthetic validation dataset generator in `code/src/audit/synthetic.py` (FR‑030). Generate exactly 10 000 simulated A/B test summaries (mix of binary and continuous outcomes) with ground‑truth p‑values and effect sizes computed using `statsmodels` (independent of the FR‑003 reconstruction implementation), seeded via the project seed. Write `data/synthetic/synthetic_validation.csv` and `data/synthetic/synthetic_ground_truth.json` conforming to `specs/001-evaluating-the-statistical-validity-of-p/contracts/synthetic_dataset.schema.yaml`.  
  - Verification: files exist, contain ≥ 10 000 records, both `outcome_type` values appear, JSON validates against the schema, and a fixed seed reproduces identical output on re‑run.

- [ ] T003 [P1] [US1] Run Monte Carlo validation of every statistical test (two‑proportion z‑test, Fisher’s exact, Welch’s t‑test, binomial test) with **10 000** replicates each in `code/src/audit/monte_carlo_validation.py` (FR‑026, SC‑003, SC‑026). Compare the `scipy` implementation against the Monte Carlo estimate and assert absolute difference ≤ 0.005 per test; write `output/monte_carlo_validation_report.json` (FR‑026).  
  - Verification: module exits 0; report lists each test with its difference and a pass flag; all differences ≤ 0.005; aborts with `ERR-801` on any failure.

- [ ] T004 [P1] [US1] Run the audit end‑to‑end on the deterministic URL corpus produced by T017: ingestion → fetch → extract → reconstruct → validate, producing `output/audit_report.json` with `AuditRecord` fields (`url`, `reported_p`, `reported_effect_size`, `reported_sample_size_a/b`, `reconstructed_p`, `reconstructed_effect_size`, `diff_abs_p`, `diff_abs_effect`, `flag_inconsistent`, `notes`) validated against `specs/001-evaluating-the-statistical-validity-of-p/contracts/audit_record.schema.yaml`.  
  - Additional verification steps:  
    • Validate extracted `ABSummary` entities against the **canonical** `specs/001-evaluating-the-statistical-validity-of-p/contracts/abs_summary.schema.yaml`.  
    • Confirm FR‑004 flagging thresholds are enforced (e.g., a synthetic record with `diff_abs_p = 0.06` is flagged inconsistent).  
    • Extraction failures raise/log `ERR-###` codes (FR‑007); the loader must fail loudly on dead URLs — never substitute synthetic data.  
  - Verification: driver exits 0; JSON validates against the schema; every `reconstructed_p` traces to the extracted counts for that URL; parsing‑error rate ≤ 5 % (SC‑005).

## Phase 2: Complete the study and validate its evidence

- [ ] T005 [P1] [US1] Scale the corpus to the power‑analysis minimum: run `code/src/audit/power_analysis.py` (FR‑025) to compute the minimum N for power ≥ 0.80 at α = 0.05 detecting proportion 0.10 vs. baseline 0.05, write `output/power_analysis.json`, and audit a real corpus of N ≥ 300 (or the calculated minimum) deduplicated public A/B test summaries (source from T017). Write per‑summary audit records to `output/audit_report.json`.  
  - Verification: `output/power_analysis.json` exists with numeric N and power; audited corpus size recorded in the audit metadata meets N ≥ 300 or the calculated minimum (SC‑025); deduplication collapses duplicate URLs.

- [ ] T006 [P1] [US1] Evaluate the inconsistency‑detection component (FR‑004 logic) on the synthetic dataset from T002: compute precision, recall, F1 in `code/tests/integration/test_synthetic_validation.py` and assert precision ≥ 90 %, recall ≥ 80 %, F1 ≥ 0.85 (FR‑031, SC‑030); write `output/synthetic_validation_report.json`.  
  - Verification: test passes (else `ERR-800`); report contains the three metrics and pass flag; metrics computed from the ground‑truth labels in T002's output.

- [ ] T018 [P1] [US1] Author the annotation protocol required for real‑world validation (FR‑031b). Create `docs/annotation_protocol.md` describing stratified sampling, dual‑annotator workflow, third‑annotator resolution, and label schema.  
  - Verification: file exists, follows the described protocol, and is referenced by T007.

- [ ] T007 [P1] [US1] Build and evaluate the real‑world extraction validation set (FR‑031b, SC‑001, SC‑031b):  
    1. Use the protocol from T018 to source ≥ 100 public A/B test summary URLs stratified across five domains (≥ 20 per domain).  
    2. Store human‑verified labels in `data/manual_validation/real_world_labels.csv` (columns: `url`, `ground_truth_sample_size_a`, `ground_truth_sample_size_b`, `ground_truth_effect_size`, `ground_truth_p`, `annotator_1`, `annotator_2`, `annotator_3`, `resolution_notes`).  
    3. Run the extraction module on this set and compute **field‑accuracy** (proportion of correctly captured fields) ≥ 95 % (satisfying SC‑001) **and** precision ≥ 85 %, recall ≥ 75 %, F1 ≥ 0.80 (satisfying SC‑031b).  
    Write `output/real_world_validation_report.json`.  
  - Verification: label CSV has ≥ 100 rows with ≥ 20 per domain; inter‑annotator agreement ≥ 85 % recorded; field‑accuracy ≥ 95 %; precision/recall/F1 meet thresholds; report shows the metrics with pass flag (else `ERR-802`).

- [ ] T008 [P2] [US2] Implement and run the prevalence analysis (FR‑005a, FR‑005b) in `code/src/audit/prevalence.py`: two‑sided binomial test of the inconsistency proportion against baseline 0.05 at α = 0.05, 95 % Wilson CI (width ≤ 0.10, SC‑014), and sensitivity analysis over baselines 0.02–0.10 step 0.01 reporting maximum prevalence variation (< 0.02, SC‑015). Exclude entries flagged for sample‑size mismatch (FR‑004b) from aggregates. Write `output/prevalence.json`.  
  - Verification: JSON contains p‑value (3 dp), Wilson bounds, raw rate, sensitivity table; CI width ≤ 0.10; no size‑mismatch entries included (cross‑check against audit flags).

- [ ] T009 [P1] [US1] Implement and run domain bias assessment and subgroup analysis (FR‑027, FR‑032): compute domain proportions, subsample any domain exceeding 30 % of the corpus, compute the domain‑weighted (equal‑weight) bias‑adjusted inconsistency rate, and per‑domain/per‑year prevalence with Fisher’s exact tests for subgroups with ≥ 10 summaries (Bonferroni‑adjusted α = 0.05 / #subgroups). Write `output/bias_report.json` and `output/subgroup_report.json` (+ mirrored `output/subgroup_report.csv`).  
  - Verification: no domain exceeds 30 % in the analyzed corpus (SC‑027); bias report contains raw and adjusted rates; subgroup report contains prevalence, Fisher p‑value, and Bonferroni‑adjusted significance flag per qualifying subgroup (SC‑032).

- [ ] T010 [P2] [US2] Generate the final summary artifacts (FR‑024, SC‑024): `output/summary_report.csv` with columns `total_summaries`, `inconsistent_count`, `inconsistent_rate`, `bias_adjusted_rate`, `wilson_ci_lower`, `wilson_ci_upper`, values exactly matching `output/audit_report.json`; run the export consistency checker `code/src/audit/export_validator.py` comparing JSON and CSV counts (log `ERR-201` on mismatch); compute SHA256 checksums for all files under `data/` and `output/` into `data/checksums.txt` and `output/checksums.txt` respectively (Constitution III/IV) and record them in `output/manifest.json` with resource usage (SC‑008, SC‑013).  
  - Verification: CSV exists with exact column names; JSON↔CSV counts identical; both checksum files exist with valid SHA256 lines; manifest validates against the manifest contract; full run completes within 6 hours, ≤ 2 GB RAM, ≤ 2 vCPUs.

- [ ] T099 [P2] [US2] Constitution‑Compliance Audit (Principles I–VII). Execute `code/src/audit/constitution_audit.py` to verify that all code paths, data‑hygiene steps, checksum generation, resource‑usage logging, and reproducibility guarantees conform to the Constitution. Write `output/constitution_audit_report.json`.  
  - Verification: report lists each principle with pass/fail; all pass; any failure aborts the pipeline.

## Phase 3: Reproducible results and paper handoff

- [ ] T011 [P2] [US1] Write the Quickstart guide (FR‑028, SC‑028) in `README_QUICKSTART.md` with step‑by‑step command‑line instructions enabling a novice to run the audit on a 30‑URL sample within 30 minutes on the default runner, including expected runtime and the novice‑verification step. The verification step writes a log to `output/novice_verification.log`.  
  - Verification: guide exists with runnable commands; the documented 30‑URL command executes end‑to‑end and completes within 30 minutes; `output/novice_verification.log` is created and contains a timestamped success message.

- [ ] T012 [P2] [US1] Write a concise methods/results account in `specs/001-evaluating-the-statistical-validity-of-p/results.md` linked to the actual output cells (`output/audit_report.json`, `output/summary_report.csv`, `output/prevalence.json`, `output/subgroup_report.json`): report the inconsistency prevalence with Wilson CI, bias‑adjusted rate, subgroup findings, validation metrics (Monte Carlo, synthetic, real‑world extraction), and honestly state the construct‑validity limitation — the method tests internal consistency of reported numbers, not external accuracy against raw experimental data — plus the FR‑012 baseline‑heuristic uncertainty and FR‑030/031 synthetic‑validation limitations.  
  - Verification: every number in the account traces to a named output file; limitations section present; no invented results.

- [ ] T013 [P2] [US1] Re‑run the documented workflow from its declared inputs (`data/input/urls.csv`, seed 42) and confirm all required checks pass — schema validation of all outputs, Monte Carlo ≤ 0.005, synthetic precision/recall thresholds, real‑world extraction thresholds, JSON↔CSV consistency, resource limits — then document the paper‑stage handoff (tables, figures, and prevalence narrative to be produced by the paper pipeline from `output/`).  
  - Verification: full re‑run exits 0 with identical aggregate statistics for all deterministic components (synthetic, Monte Carlo, validation reports); handoff section names the source artifacts for each planned table/figure; no research task duplicates paper‑layout or publication work.

## Dependencies and requirement coverage

- **SC‑001** satisfied by T007 (field‑accuracy ≥ 95 %).  
- **SC‑003, SC‑026** satisfied by T003 (Monte Carlo 10 000 replicates, matching FR‑026).  
- **SC‑005** enforced in T004 (parsing‑error rate ≤ 5 %).  
- **SC‑014, SC‑015** satisfied by T008.  
- **SC‑027** satisfied by T009 (domain ≤ 30 %).  
- **SC‑028** satisfied by T011 (novice log).  
- **SC‑030** satisfied by T006 (synthetic precision/recall).  
- **SC‑031b** satisfied by T007 (precision/recall thresholds).  
- **SC‑032** satisfied by T009 (Bonferroni‑adjusted subgroup tests).  

**Execution order** (selected critical path):  
T001 → T017 → T002 → T003 → T004 → T005 → T006 → T008 → T009 → T010 → T011 → T012 → T013.  
Additional parallel‑safe tasks: T018 (annotation protocol) runs after T001; T007 runs after T018; T099 runs after T010.  

**Task Registry** (preserved IDs): T001‑T013, plus newly added T017, T018, T099.
