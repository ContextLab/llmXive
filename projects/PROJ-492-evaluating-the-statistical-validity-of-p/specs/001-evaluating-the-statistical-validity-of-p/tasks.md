---
description: "Task list template for feature implementation"
---

# Tasks: Evaluating the Statistical Validity of Public A/B Test Summaries

**Input**: Design documents from `/specs/001-eval-ab-test-validity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/`, `data/`, `output/`, `contracts/` directories
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

  The /speckit-tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3...)
  - Feature requirements from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/

  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment

  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create repository skeleton with `src/`, `tests/`, `data/`, `output/`, `contracts/`, `.github/`, `docs/` directories (verify directories exist).
- [ ] T002 Initialize Python 3.11 project: `pyproject.toml` with required dependencies (`requests`, `beautifulsoup4`, `pandas`, `numpy`, `scipy`, `statsmodels`, `tqdm`, `pyyaml`, `jsonschema`, `psutil`) (verify `pyproject.toml` contains listed deps).
- [ ] T003 [P] Add linting and formatting tools (`ruff`, `black`) and configure pre‑commit hooks (run `pre-commit run --all-files` with zero violations).
- [ ] T004 [P] Create `requirements.txt` mirroring `pyproject.toml` for CI reproducibility (verify `requirements.txt` matches `pyproject.toml`).
- [ ] T098 [P] Implement `run_audit.sh` shell script wrapper that invokes `src/cli/run_audit.py` with proper environment setup for Docker and local execution (verify script is executable and runs successfully).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create data‑model definitions (`ABSummary`, `AuditRecord`) in `src/models/data_models.py` (verify classes exist and importable).
- [ ] T006 Create JSON‑Schema files `contracts/extracted_summary.schema.yaml` and `contracts/audit_record.schema.yaml` (verify schemas are valid YAML).
- [ ] T007 Implement schema‑validation utilities in `src/contracts/validation.py` (run unit test to confirm validation works).
- [ ] T008 Set up structured logging infrastructure in `src/utils/logger.py` with error‑code format `ERR-###` (verify logs contain correct codes).
- [ ] T009 [P] Initialize configuration constants (random seeds, thresholds, resource caps) in `src/config.py` with deterministic seed (SEED = 42) AND ensure all modules import SEED from config and set RNG seeds at startup (verify `src/config.py` defines `SEED = 42` and all RNGs are seeded).
- [ ] T010 Implement generic helper functions (`checksum`, `domain_from_url`, `safe-float`) in `src/utils/helpers.py` (run unit test for each helper).
- [ ] T011 Create CI workflow file `.github/workflows/audit.yml` that installs dependencies, enforces CPU ≤ 2 vCPU, RAM ≤ 2 GB, timeout 6 h, and runs `run_audit.sh` (verify workflow runs and respects limits).
- [ ] T012 Add Dockerfile for optional local execution (uses only CPU‑compatible base image) (build Docker image successfully).
- [ ] T013 [P] Configure `manifest.json` generation with content hashes in `src/utils/manifest.py` (FR‑024) (verify `manifest.json` contains SHA256 hashes).
- [ ] T096 [P] Create manual validation dataset: manually annotate ≥100 A/B test summaries stratified across at least 5 major domains, store as `data/manual_validation/annotated_summaries.csv` with ground-truth fields for extraction accuracy measurement (SC‑001) (verify file exists and contains ≥100 rows across 5+ domains).
- [ ] T076 [P] Compute checksums for all raw dataset files under `data/` and record them in `state/projects/PROJ-492-evaluating-the-statistical-validity-of-p.yaml` `artifact_hashes` map (Constitution Principle III) (verify yaml file updated with correct hashes).
- [ ] T077 Extend `manifest.json` generation to include the same checksums recorded in `state/projects/PROJ-492-evaluating-the-statistical-validity-of-p.yaml` artifact_hashes map (verify both locations contain identical hashes).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Consistency Audit (Priority: P1) 🎯 MVP

**Goal**: End‑to‑end pipeline that ingests URLs, extracts metrics, reconstructs statistical tests, flags inconsistencies, and produces audit artifacts.

**Independent Test**: Run the pipeline on the synthetic validation dataset (a large number of records) and verify precision ≥ 90% and recall ≥ 80% (SC‑030).

### Tests for User Story 1 (OPTIONAL) ⚠️

- [ ] T014 US1 Contract test for extractor output schema in `tests/contract/test_extractor_schema.py` (run AFTER T019 completes) (verify schema compliance).
- [ ] T015 US1 Contract test for reconstructor output schema in `tests/contract/test_reconstructor_schema.py` (run AFTER T022 completes) (verify schema compliance).
- [ ] T016 US1 Integration test that runs the full pipeline on `data/manual_validation/annotated_summaries.csv` and asserts `ERR-800` is not raised (tests/integration/test_full_pipeline.py) (run AFTER T017-T027) (verify no ERR‑800).

### Implementation for User Story 1

- [ ] T017 [P] US1 Implement URL ingestion and deduplication in `src/audit/ingestor.py` (reads `input/urls.csv`) (verify `output/urls_deduped.csv` exists).
- [ ] T018 [P] US1 Implement HTML fetching with retries and timeout in `src/audit/fetcher.py` (uses `requests`) (verify fetched HTML files are saved).
- [ ] T019 [P] US1 Implement extraction logic in `src/audit/extractor.py` → produces `ABSummary` objects, handles missing fields, logs `ERR-001`‑`ERR-099` (FR‑007) (verify extraction JSON exists and logs contain appropriate ERR codes).
- [ ] T020 [P] US1 Unit tests for extractor covering missing metric, inequality p‑value, malformed HTML (tests/unit/test_extractor.py) (verify all tests pass).
- [ ] T021 [P] US1 Implement outcome‑type detection heuristics in `src/audit/test_type_detector.py` (detect binary vs continuous only, no extra test‑type handling) (verify detector returns correct type).
- [ ] T022 [P] US1 Implement statistical reconstruction in `src/audit/reconstructor.py` (two‑proportion z/Fisher, Welch t, fallback to average baseline per FR‑012) (verify reconstructed values match known fixtures).
- [ ] T023 [P] US1 Unit tests for reconstructor with known inputs (tests/unit/test_reconstructor.py) (verify all tests pass).
- [ ] T024 [P] US1 Implement inconsistency validator in `src/audit/validator.py` applying FR‑004 thresholds AND FR‑004b sample-size mismatch detection (>5% threshold), generating `AuditRecord` objects, writing `output/audit_report.json` (verify flags are set correctly).
- [ ] T025 [P] US1 Unit tests for validator covering absolute p‑difference > 0.05, effect‑size > 5%, inequality handling, sample-size mismatch (tests/unit/test_validator.py) (verify all tests pass).
- [ ] T026 [P] US1 Implement synthetic dataset generator in `src/audit/synthetic.py` (FR‑030) – outputs CSV + ground‑truth JSON (verify files are created).
- [ ] T069 [P] US1 Evaluate inconsistency‑detection component on synthetic validation dataset (FR‑031) – compute precision, recall, F1 and assert precision ≥ 90%, recall ≥ 80%, F1 ≥ 0.85 (verify test passes, otherwise raise `ERR-800`).
- [ ] T070 [P] US1 Implement FR‑001: system accepts list of URLs as input (handled by T017) – verify `input/urls.csv` is read and processed without error.
- [ ] T071 [P] US1 Implement FR‑002: automatic extraction of sample size, effect size, and p‑value (handled by T019) – verify extracted fields exist for >95% of valid pages.
- [ ] T072 [P] US1 Implement FR‑003: reconstruction of p‑values using appropriate statistical test (handled by T022) – verify reconstructed p‑values are computed for all records.
- [ ] T073 [P] US1 Implement FR‑004: inconsistency‑detection thresholds (handled by T024) – verify flags correspond to the defined thresholds.
- [ ] T061 [P] US1 Implement power‑analysis utility (FR‑025) in `src/audit/power_analysis.py` that computes the minimum N given baseline, detectable effect, α and power, and writes the result to `output/power_analysis.json` (verify JSON file exists and contains numeric N).
- [ ] T062 [P] US1 Implement Monte‑Carlo validation module (FR‑026) in `src/audit/monte_carlo_validation.py` that runs many replicates for each statistical test and checks the absolute difference ≤ 0.01 (verify module exits with status 0).
- [ ] T074 [P] US1 Run Monte‑Carlo validation (from T062) as part of pipeline start‑up; abort with `ERR-801` if any test fails the ≤ 0.01 criterion (verify pipeline aborts on failure).
- [ ] T027 [P] US1 Implement end‑to‑end driver script `src/__main__.py` (or `run_audit.sh`) that orchestrates ingestion → fetch → extract → reconstruct → validate → write artifacts (verify script exits with status 0 on success).
- [ ] T028 [P] US1 Integration test that runs driver on synthetic dataset, computes precision/recall/F1 and aborts with `ERR-800` if thresholds not met (tests/integration/test_synthetic_validation.py) (verify test passes).
- [ ] T095 [P] Create analysis notebook `notebooks/statistical_consistency_verification.ipynb` that documents any p-value discrepancies >0.05 with justification per Constitution Principle VI; run as part of pipeline acceptance (verify notebook exists and contains discrepancy justifications) (depends on T024).

---

## Phase 4: User Story 2 - Summary Report Generation (Priority: P2)

**Goal**: Produce a concise CSV report summarising total counts, inconsistency rates, bias‑adjusted rates, and Wilson confidence intervals.

**Independent Test**: Compare generated `summary_report.csv` against values derived from `audit_report.json` for a representative corpus.

### Tests for User Story 2 (OPTIONAL) ⚠️

- [ ] T029 US2 Contract test for prevalence calculations in `tests/contract/test_prevalence_schema.py` (run AFTER T031 completes) (verify schema compliance).
- [ ] T030 US2 Integration test that runs `src/audit/prevalence.py` on a known audit JSON and checks CSV columns (tests/integration/test_summary_generation.py) (run AFTER T031-T035) (verify CSV columns exist).

### Implementation for User Story 2

- [ ] T031 [P] US2 Implement binomial prevalence test, Wilson CI, AND sensitivity analysis (FR‑005a & FR‑005b) in `src/audit/prevalence.py` including baseline proportion sweep from 0.02 to 0.10 (step 0.01) and max variation reporting (verify JSON output contains required fields including sensitivity analysis results).
- [ ] T032 [P] US2 Unit tests for binomial test and CI width ≤ 0.10 (tests/unit/test_prevalence.py) (verify test passes).
- [ ] T033 [P] US2 Implement bias‑adjustment module that computes domain‑weighted prevalence using logistic‑regression weighting (FR‑027) in `src/audit/bias_adjustment.py` (verify bias‑adjusted rate is written).
- [ ] T034 [P] US2 Unit tests for bias‑adjustment ensuring no domain exceeds [deferred] (tests/unit/test_bias_adjustment.py) (verify test passes).
- [ ] T035 [P] US2 Implement CSV summary generator in `src/audit/report_generator.py` that reads `audit_report.json` and writes `output/summary_report.csv` with required columns (plan.md) (verify CSV file exists and column headers match).
- [ ] T036 [P] US2 Unit test that validates CSV values exactly match JSON‑derived aggregates (tests/unit/test_report_generator.py) (verify test passes).
- [ ] T037 [P] US2 Add Quickstart guide `README_QUICKSTART.md` covering execution on 30 URLs within 30 minutes (FR‑028) (verify guide file exists).
- [ ] T097 [P] US2 Verify FR-028 Quickstart execution time: run audit on 30 URLs and measure wall-clock time, assert ≤30 minutes on default GitHub Actions runner (verify measurement recorded in `output/quickstart_timing.log`) (verify timing test passes).
- [ ] T057 [P] US2 Implement subgroup prevalence and Fisher's exact‑test analysis (FR‑032) in `src/audit/subgroup_analysis.py` that produces `output/subgroup_report.json` with domain, year, counts, prevalence, and p‑value (verify JSON file exists).
- [ ] T058 [P] US2 Unit tests for subgroup analysis covering groups with ≥ 10 summaries and verifying correct Fisher p‑values (tests/unit/test_subgroup_analysis.py) (verify test passes).
- [ ] T059 [P] US2 Extend `report_generator.py` to also write the subgroup CSV `output/subgroup_report.csv` mirroring the JSON for easy inspection (verify CSV file exists).
- [ ] T060 [P] US2 Integration test that runs the full pipeline on a mixed‑domain synthetic corpus and checks that subgroup report columns are present and correct (tests/integration/test_subgroup_report.py) (verify test passes).

---

## Phase 5: User Story 3 - Export Audit Results (Priority: P3)

**Goal**: Ensure audit artifacts are exported correctly and are mutually consistent.

**Independent Test**: Verify that `output/audit_report.json` and `output/summary_report.csv` exist and contain identical counts of consistent vs. inconsistent entries.

### Tests for User Story 3 (OPTIONAL) ⚠️

- [ ] T038 US3 Contract test for manifest schema in `tests/contract/test_manifest_schema.py` (run AFTER T040 completes) (verify schema compliance).
- [ ] T039 US3 Integration test that checks JSON ↔ CSV count consistency (tests/integration/test_export_consistency.py) (run AFTER T040-T044) (verify counts match).

### Implementation for User Story 3

- [ ] T040 [P] US3 Ensure driver script creates `output/manifest.json` with SHA256 hashes for all generated files (via `src/utils/manifest.py`) (FR‑024) (verify manifest exists and contains hashes).
- [ ] T041 [P] US3 Add schema validation step after audit generation to validate `audit_report.json` against `contracts/audit_record.schema.yaml` (FR‑026) (verify validation passes).
- [ ] T042 US3 Add schema validation step for `manifest.json` against `contracts/manifest.schema.yaml` (plan.md) (run AFTER T040) (verify validation passes).
- [ ] T043 [P] US3 Implement consistency checker in `src/audit/export_validator.py` that reads JSON and CSV, compares counts, and logs `ERR-201` if mismatch (plan.md) (verify no ERR‑201 logged).
- [ ] T044 [P] US3 Unit test for export validator with deliberately mismatched files (tests/unit/test_export_validator.py) (verify test catches mismatch).

---

## Phase 6: User Story 4 - Efficient CI Execution (Priority: P2)

**Goal**: Guarantee that the full pipeline runs within GitHub Actions resource limits and logs usage.

**Independent Test**: Trigger the workflow on a sample corpus of a modest number of URLs and confirm successful completion, ≤ 2 GB RAM, ≤ 2 vCPU.

### Tests for User Story 4 (OPTIONAL) ⚠️

- [ ] T045 [P] US4 CI test that runs the workflow locally with `act` and asserts exit code 0 (tests/ci/test_ci_workflow.py) (verify exit code 0).

### Implementation for User Story 4

- [ ] T046 [P] US4 Add resource‑monitoring module `src/utils/resource_monitor.py` that records peak CPU & memory, writes to `output/resource_log.json` (SC‑008) (verify log file exists and records within limits).
- [ ] T047 US4 Modify `run_audit.sh` to invoke `resource_monitor` and abort with `ERR-301` if limits exceeded (plan.md) (run AFTER T046) (verify script aborts on limit breach).
- [ ] T048 [P] US4 Update `.github/workflows/audit.yml` to include steps: (a) schema validation, (b) synthetic validation (ensure precision/recall thresholds), (c) resource‑monitor check, (d) main pipeline run (verify workflow runs all steps).
- [ ] T049 [P] US4 Add CI step that caches `pip` packages to stay within 6 hour total runtime (plan.md) (verify cache hit on subsequent runs).
- [ ] T050 [P] US4 Add unit test for resource monitor parsing of `/proc` (tests/unit/test_resource_monitor.py) (verify test passes).

---

## Phase X: Success Criteria Verification

**Purpose**: Explicitly verify that every Success Criteria (SC‑*) is satisfied by the pipeline.

**⚠️ NOTE**: All Phase X tasks depend on completion of Phases 3-6 implementation artifacts.

- [ ] T080 [P] Verify SC‑001: Extraction accuracy ≥ 95% on `data/manual_validation/annotated_summaries.csv` (run `tests/integration/test_extractor_accuracy.py`) (depends on T096).
- [ ] T081 [P] Verify SC‑003: Monte‑Carlo vs library difference ≤ 0.01 for each statistical test (run `src/audit/monte_carlo_validation.py`) (depends on T062).
- [ ] T082 [P] Verify SC‑005: Parsing‑error rate ≤ 5% (run `src/audit/validator.py` and check log summary) (depends on T019).
- [ ] T083 [P] Verify SC‑008: CI execution completes within 6 h, ≤ 2 GB RAM, ≤ 2 vCPU (inspect `output/resource_log.json`) (depends on T046).
- [ ] T084 [P] Verify SC‑013: CI pipeline exits with status 0 and produces `manifest.json` in ≥ 99% of runs (run CI locally and check) (depends on T040).
- [ ] T085 [P] Verify SC‑014: Binomial test output meets formatting and CI width ≤ 0.10 (run `src/audit/prevalence.py` and inspect JSON) (depends on T031).
- [ ] T086 [P] Verify SC‑015: Sensitivity analysis variation < 0.02 across baseline range (run `src/audit/prevalence.py` and inspect results) (depends on T031).
- [ ] T087 [P] Verify SC‑024: `summary_report.csv` columns and values match `audit_report.json` (run `tests/integration/test_summary_consistency.py`) (depends on T035).
- [ ] T088 [P] Verify SC‑025: Audited corpus size N ≥ 300 (check `output/power_analysis.json`) (depends on T061).
- [ ] T089 [P] Verify SC‑026: Monte‑Carlo validation passes for all tests (same as T081) (depends on T062).
- [ ] T090 [P] Verify SC‑027: No domain exceeds [deferred] and bias‑adjusted rate reported (run `src/audit/bias_adjustment.py` and inspect output) (depends on T033).
- [ ] T091 [P] Verify SC‑028: Quickstart guide enables audit of 30 URLs in ≤ 30 minutes on GH Actions (time execution of Quickstart script) (depends on T097).
- [ ] T092 [P] Verify SC‑030: Synthetic validation precision ≥ 90% and recall ≥ 80% (run T069) (depends on T069).
- [ ] T093 [P] Verify SC‑032: Subgroup analysis produces Fisher's exact test results for groups ≥ 10 (run `src/audit/subgroup_analysis.py` and check JSON) (depends on T057).
- [ ] T094 [P] Verify overall pipeline passes all above SC checks without errors (run full suite) (depends on T080-T093).

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T051 [P] Documentation updates in `docs/` – expand API reference, data‑model description, and troubleshooting guide (verify docs build without errors).
- [ ] T052 [P] Code cleanup: add type hints throughout `src/`, run `mypy --strict` (verify no type errors).
- [ ] T053 [P] Performance optimization: replace in‑memory DataFrame joins with chunked processing in `src/audit/prevalence.py` to keep RAM ≤ 1.5 GB for several thousand URLs. (SC‑008) (verify memory usage).
- [ ] T054 [P] Add additional edge‑case unit tests (missing metric, conflicting sample sizes, dead URLs) in `tests/unit/` (verify all pass).
- [ ] T055 [P] Run full benchmark on several thousand synthetic URLs; record wall‑clock time in `output/benchmark.log` and ensure ≤ 6 hours (SC‑008) (verify log).
- [ ] T056 [P] Release version tag `v0.1.0` and update `CHANGELOG.md` with released features (verify tag exists).
- [ ] T099 [P] Governance note: Constitution Principle V specifies Advancement-Evaluator Agent as sole writer of `current_stage` and invalidates stale records on artifact hash changes; this is a governance-level concern requiring plan/constitution update, not an implementation task. Document in `docs/governance.md` that this workflow must be implemented by the Advancement-Evaluator Agent outside tasks.md scope.

---

## Phase Dependencies

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3‑6)**: All depend on Foundational (Phase 2) completion
  - User stories can proceed in parallel (if staffed) or sequentially by priority (P1 → P2 → P3 → P4)
- **Success Criteria Verification (Phase X)**: Depends on completion of all user‑story artifacts
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - no dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational - consumes output of US1 (`audit_report.json`)
- **User Story 3 (P3)**: Can start after Foundational - consumes outputs of US1 & US2
- **User Story 4 (P2)**: Can start after Foundational - wraps the entire pipeline for CI

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before scripts
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked **[P]** can run in parallel
- All Foundational tasks marked **[P]** can run in parallel (within Phase 2)
- Once Foundational is done, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked **[P]** can run in parallel
- Different user stories can be worked on in parallel by different developers

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run synthetic‑validation integration test (T028) - must pass precision/recall thresholds
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational together
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test CI limits → Deploy/Demo
6. Run Polish phase for documentation, performance, and release

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
   - Developer D: User Story 4 (CI integration)
3. Stories complete and integrate independently without breaking previous work

---

## Notes

- **[P]** tasks = different files, no dependencies
- **[Story]** label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross‑story dependencies that break independence.