---
description: "Task list for the alloy‑phase‑diagram prediction feature"
---

# Tasks: Predicting Alloy Phase Diagrams from Compositional Data  

**Input**: Design documents from `/specs/001-predict-alloy-phase-diagrams/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`  

The checklist below follows the canonical `- [ ] T### [P?] [USx?] description …` format. Checked boxes (`[X]`) indicate work that has passed verification; unchecked boxes (`[ ]`) are pending or reopened for correction.  

---  

## Phase 1: Setup and first end‑to‑end analysis  

- [ ] T001 **Establish code layout, dependencies, and quickstart documentation; validate input provenance.**  
  - Verify: `quickstart.md` exists and contains a runnable command (`python -m code.main --systems Cu‑Zn Al‑Cu`); a provenance report (`data/provenance.json`) is generated; raw data checksum (`data/raw/checksum.sha256`) matches recorded value.  

- [ ] T002 **Ingest experimental phase data from NIST‑JANAF/SGTE, validate schema, and log `INVALID_DATA_SCHEMA` or `MISSING_TEMP_COORDS` as needed (FR‑001).**  
  - Verify: unit test `tests/test_ingest.py` loads a sample file, asserts schema compliance, and checks that error codes are logged when appropriate.  

- [ ] T003 **Generate compositional descriptors (mean atomic radius, electronegativity variance, valence electron count, Hume‑Rothery concentration) for every alloy (FR‑002, FR‑015).**  
  - Verify: `tests/test_features.py` confirms the four descriptor columns exist, values are within 1 % of reference constants, and the output file `data/processed/features_enriched.csv` conforms to `AlloyFeatures` schema.  

- [ ] T004 **Implement LOSO cross‑validation ensuring test sets contain only elements present in the training set and no extrapolation beyond convex hull (FR‑003, FR‑010).**  
  - Verify: `tests/test_loso.py` asserts no new elements appear in test folds, and that folds violating convex‑hull constraints are skipped with `INVALID_SCOPE` logged.  

- [ ] T005 **Compute and report MAE and R² for each LOSO fold and aggregate across all folds (FR‑004).**  
  - Verify: `metrics.json` matches `model_metrics.schema.yaml`; `tests/test_metrics.py` validates presence of `mae`, `r2`, and aggregate fields.  

- [ ] T006 **Train a Random Forest Regressor, generate baseline null model (global mean), and compare performance with statistical significance (FR‑009).**  
  - Verify: `baseline_comparison.json` contains `percentage_improvement` and `p_value` < 0.05; `tests/test_baseline.py` checks these fields.  

- [ ] T007 **Perform statistical power analysis (target ≥ 0.8, α ≤ 0.05) before training; abort with `INSUFFICIENT_POWER` if power < 0.8 (FR‑011, FR‑014).**  
  - Verify: `power_analysis.json` includes `calculated_power` and `status`; pipeline exits with error code and logs `INSUFFICIENT_POWER` when power < 0.8.  

- [ ] T008 **Implement exponential backoff for API rate‑limit handling (max 3 retries) and log `API_RATE_LIMIT_EXCEEDED` on failure (FR‑007).**  
  - Verify: `tests/test_backoff.py` simulates transient failures, asserts three retries, and checks log entry and non‑zero exit code on ultimate failure.  

- [ ] T009 **Provide fallback to locally stored CSV if primary NIST‑JANAF/SGTE source is unavailable; verify file checksum (FR‑012).**  
  - Verify: `tests/test_fallback.py` forces primary source failure, confirms local CSV is used, and its SHA‑256 matches the recorded checksum in `state/...yaml`.  

- [ ] T010 **Log all required error codes (`MISSING_TEMP_COORDS`, `LOW_DATA_DENSITY`, `INVALID_DATA_SCHEMA`, `INSUFFICIENT_POWER`) with structured JSON lines (FR‑008).**  
  - Verify: `data/logs/error_codes.jsonl` contains entries with the specified codes when conditions occur; `tests/test_error_codes.py` validates presence.  

- [ ] T011 **Calculate per‑system prediction error standard deviation; trigger `LOW_DATA_DENSITY` if sample size < 5 or std > 50 K (FR‑013).**  
  - Verify: `visual_metrics.json` includes `std_dev_error` per system and logs `LOW_DATA_DENSITY` where conditions are met; unit test confirms behavior.  

- [ ] T012 **Enforce fidelity threshold: abort pipeline if MAE > 50 K and log `FIDELITY_THRESHOLD` (FR‑005, FR‑004).**  
  - Verify: pipeline exit status non‑zero, `data/logs/fidelity.log` contains `FIDELITY_THRESHOLD` flag when MAE exceeds 50 K.  

- [ ] T013 **Memory‑use test: stream a 1 M‑row dataset and ensure peak RAM < 7 GB (FR‑006).**  
  - Verify: `tests/test_memory.py` runs the streaming pipeline, records peak RAM, and asserts it is below 7 GB; logs `peak_ram_gb`.  

- [ ] T014 **Convex‑hull extrapolation validation: skip LOSO folds with out‑of‑scope test elements and log `INVALID_SCOPE` (FR‑010).**  
  - Verify: `tests/test_convex_hull.py` forces an out‑of‑scope fold, asserts it is skipped, and checks log for `INVALID_SCOPE`.  

- [ ] T015 **Generate visualization plots for at least two binary systems (Cu‑Zn, Al‑Cu) with experimental and predicted phase boundaries; produce `visual_metrics.json` containing per‑system MAE (must be ≤ 50 K) (FR‑005).**  
  - Verify: PNG/SVG files exist in `artifacts/plots/`; `visual_metrics.json` contains `system`, `mae`, and `notes`; a flag `FIDELITY_THRESHOLD` is logged if any system’s MAE > 50 K.  

---  

## Phase 2: Complete the study and validate its evidence  

- [ ] T016 **Validate `dataset.schema.yaml` against the processed dataset (contract compliance).**  
  - Verify: `tests/test_dataset_schema.py` passes JSON‑schema validation.  

- [ ] T017 **Validate `model_output.schema.yaml` against saved model artifacts (contract compliance).**  
  - Verify: `tests/test_model_output_schema.py` passes validation.  

- [ ] T018 **Create and verify core data‑model entities: AlloyComposition CSV, PhaseBoundary CSV, ModelMetrics JSON, PowerAnalysisResult JSON (data‑model coverage).**  
  - Verify: each file exists, conforms to its respective schema, and `tests/test_data_model.py` confirms correctness.  

- [ ] T019 **Update `quickstart.md` with clear installation steps, usage instructions, and runnable command (coverage‑41f62d3e).**  
  - Verify: `quickstart.md` contains “Installation” and “Usage” sections and the command `python -m code.main --systems Cu‑Zn Al‑Cu`.  

- [ ] T020 **Run full end‑to‑end pipeline on the complete dataset, producing all artifacts listed in the data model (Phase 2 deliverables).**  
  - Verify: `artifacts/model.pkl`, `artifacts/metrics.json`, `artifacts/visual_metrics.json`, and all schema‑validated files exist; CI checks hashes against `state/...yaml`.  

- [ ] T021 **End‑to‑end dry run on minimal subset (Cu‑Zn) producing `model.pkl`, `fidelity_report.json`, and `plots/Cu‑Zn.png` (reopened T068).**  
  - Verify: command `python -m code.main --systems Cu‑Zn --max-systems 1` completes, artifacts exist, and pass schema validation.  

- [ ] T022 **Cross‑validation consistency check: run training three times with fixed `random_state` and ensure identical `mean_mae`, `mean_r2`, `percentage_improvement` (reopened T069).**  
  - Verify: `data/logs/cv_consistency.log` records three runs and asserts tolerance ≤ 1e‑8.  

- [ ] T023 **Performance‑optimization review: profile before and after optimizations, require ≥ 10 % improvement in time and memory (reopened T072).**  
  - Verify: `benchmark_before.json`, `benchmark_after.json`, and `optimizations.log` show required improvements.  

- [ ] T024 **Limitations report documenting at least three concrete project limits (reopened T073).**  
  - Verify: `docs/limitations.md` lists three items and is referenced from `docs/README.md`.  

- [ ] T025 **Compliance checklist mapping all FRs, SCs, and constitutional principles to task IDs (reopened T074).**  
  - Verify: `docs/compliance_checklist.md` contains a table row for each FR‑001 … FR‑015 and SC‑001 … SC‑009 with “Compliant” status and linked task IDs; CI script parses and ensures no “Non‑Compliant” entries.  

- [ ] T026 **Release preparation: create tag `v1.0.0`, `RELEASE_NOTES.md`, and `reproducibility_package.zip`; CI must reproduce artifact hashes (reopened T075).**  
  - Verify: git tag exists, release notes list changes, zip contains `code/`, `data/processed/`, `state/`; CI clones at tag, extracts zip, runs dry‑run, and confirms hashes match.  

- [ ] T027 **Security audit: run Bandit and Safety; produce `security_audit_report.md` with “No Critical Issues” (reopened T076).**  
  - Verify: CI runs `bandit -r code/` and `safety check -r requirements.txt`, both exit 0; report is parsed and no severity ≥ high is found.  

---  

## Phase N: Execution verification and compliance  

- [ ] T046 **Verify injected data source file exists and its SHA‑256 checksum matches the recorded value.**  
  - Verify: `tests/test_data_source.py` asserts file presence and checksum equality.  

- [ ] T047 **Verify fallback CSV is used when primary source fails and its checksum matches the recorded value.**  
  - Verify: `tests/test_fallback_checksum.py` forces primary failure, checks fallback CSV existence, and validates its SHA‑256 against `state/...yaml`.  

- [ ] T048 **Validate convex‑hull handling by triggering `INVALID_SCOPE` and asserting the error code is logged.**  
  - Verify: `tests/test_convex_hull_handling.py` creates an out‑of‑scope test fold, runs LOSO, and checks `error_codes.jsonl` for `INVALID_SCOPE`.  

- [ ] T049 **Check that the statistical‑power report (`power_analysis.json`) contains all required fields and reports `FAIL` when calculated power < 0.8.**  
  - Verify: `tests/test_power_report.py` loads the JSON, verifies keys (`effect_size`, `sample_size`, `alpha`, `calculated_power`, `status`) and asserts `status == "FAIL"` for low‑power scenarios.  

- [ ] T050 **Ensure pipeline aborts with a non‑zero exit code and logs `FIDELITY_THRESHOLD` when MAE exceeds 50 K.**  
  - Verify: `tests/test_fidelity_abort.py` runs the pipeline on a deliberately high‑error dataset and checks exit code and log entry.  

- [ ] T053 **Run a memory‑use test on a 1 M‑row dataset and assert logged peak RAM is < 7 GB.**  
  - Verify: `tests/test_memory_usage.py` streams the large dataset, captures peak RAM from logs, and asserts `< 7`.  

- [ ] T054 **Run convex‑hull validation and confirm `fidelity_report.json` contains the correct `INVALID_SCOPE` flags for affected folds.**  
  - Verify: `tests/test_fidelity_report.py` inspects the JSON for expected flags.  

- [ ] T055 **Validate that `visual_fidelity_report.json` exists, conforms to its schema, and contains PASS/FAIL flags for each system.**  
  - Verify: `tests/test_visual_fidelity.json` loads the file, validates schema, and checks flag values.  

- [ ] T057 **Verify the error‑code mapping file includes entries for each expected schema mismatch, temperature‑range violation, and composition‑sum error.**  
  - Verify: `tests/test_error_code_mapping.py` scans `error_codes.jsonl` for required categories.  

- [ ] T058 **Confirm LOSO folds with fewer than three test samples are skipped and a `LOW_DATA_DENSITY` entry appears in the logs.**  
  - Verify: `tests/test_loso_low_density.py` creates such a fold, runs LOSO, and checks logs for `LOW_DATA_DENSITY`.  

---  

## Phase N+1: Reproducible results and paper handoff  

- [ ] T028 **Write methods/results account linking to concrete artifact paths (FR‑001 … FR‑015 coverage).**  
  - Verify: `docs/methods.md` references specific CSV/JSON/PNG files.  

- [ ] T029 **Re‑run documented workflow from declared inputs, confirm all tests and artifact checks, and produce paper‑stage handoff documentation (FR‑006 compliance).**  
  - Verify: CI clean run reproduces all artifacts; `docs/paper_handoff.md` exists and lists artifact locations.  

---  

## Phase N: Polish & cross‑cutting concerns (orphan tasks removed)  

*All orphan tasks from the previous version (T041‑T045, T056) have been removed and their functionality incorporated into the scoped tasks above.*  

---  

## Summary of pending work  

| Task | Status | Expected artifact(s) |
|------|--------|----------------------|
| T021 (formerly T068) | ☐ | `model.pkl`, `fidelity_report.json`, `plots/Cu‑Zn.png` |
| T022 (formerly T069) | ☐ | `baseline_comparison.json` |
| T019 (formerly T071) | ☐ | `README.md`, `docs/*.md`, doc‑build log |
| T023 (formerly T072) | ☐ | optimization logs & before/after benchmarks |
| T024 (formerly T073) | ☐ | `docs/limitations.md` |
| T025 (formerly T074) | ☐ | `docs/compliance_checklist.md` |
| T026 (formerly T075) | ☐ | Git tag, `RELEASE_NOTES.md`, reproducibility zip |
| T027 (formerly T076) | ☐ | `docs/security_audit_report.md` |
| T046‑T058 | ☐ | Various test files and JSON reports as described above |

All other tasks are checked and verified. Completing the pending items will bring the project to a fully reproducible, documented, and compliant state ready for hand‑off.  