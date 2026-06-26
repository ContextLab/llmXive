# Tasks: Evaluating the Statistical Validity of Public A/B Test Summaries

**Input**: Design documents from `/specs/001-eval-ab-test-validity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Plan Traceability**: Task IDs align with plan.md phases and requirements (FR-001 through FR-032, SC-001 through SC-032).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/`, `data/`, `output/`, `contracts/`, `notebooks/`, `docs/` directories
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

- [ ] T001 Create repository skeleton with `code/`, `tests/`, `data/`, `output/`, `contracts/`, `notebooks/`, `.github/`, `docs/` directories (verify directories exist).
- [ ] T002 Initialize Python 3.11 project: `pyproject.toml` with required dependencies (`requests`, `beautifulsoup4`, `pandas`, `numpy`, `scipy`, `statsmodels`, `tqdm`, `pyyaml`, `jsonschema`, `psutil`) (verify `pyproject.toml` contains listed deps).
- [ ] T003 [P] Add linting and formatting tools (`ruff`, `black`) and configure pre‑commit hooks (run `pre-commit run --all-files` with zero violations).
- [ ] T004 [P] Create `requirements.txt` mirroring `pyproject.toml` for CI reproducibility (verify `requirements.txt` matches `pyproject.toml`).
- [ ] T005 [P] Create `.gitignore` excluding `__pycache__`, `*.pyc`, `data/raw/*` except URLs, `output/*` (verify git status clean).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until foundational infrastructure (T006-T012) is complete; remaining Phase 2 tasks (T013-T020) may proceed in parallel with US1 implementation

**Checkpoint**: Foundational infrastructure (T006-T012) ready - US1 implementation can now begin; T013 and other non-blocking foundational tasks (T013-T020) can proceed in parallel with US1 after T006-T012 completion.

- [ ] T006 Create data‑model definitions (`ABSummary`, `AuditRecord`) in `code/models/data_models.py` using Pydantic (verify classes exist and importable).
- [ ] T007 Create JSON‑Schema files `contracts/extracted_summary.schema.yaml` and `contracts/audit_record.schema.yaml` (verify schemas are valid YAML).
- [ ] T008 [P] Implement schema‑validation utilities in `code/contracts/validation.py` (run unit test to confirm validation works) [DEPENDS ON: T007].
- [ ] T009 Set up structured logging infrastructure in `code/utils/logger.py` with error‑code format `ERR-###` (verify logs contain correct codes).
- [ ] T010 [P] Initialize configuration constants (random seeds, thresholds, resource caps) in `code/config.py` with deterministic seed (SEED = 42) AND ensure all modules import SEED from config and set RNG seeds at startup (verify `code/config.py` defines `SEED = 42` and all RNGs are seeded per Constitution Principle I).
- [ ] T011 Implement generic helper functions (`checksum`, `domain_from_url`, `safe-float`, `parse_inequality_p`) in `code/utils/helpers.py` (run unit test for each helper).
- [ ] T012 [P] Create CI workflow file `.github/workflows/audit.yml` that installs dependencies, enforces CPU ≤ 2 vCPU, RAM ≤ 2 GB, timeout 6 h, and runs audit pipeline (verify workflow runs and respects limits) [DEPENDS ON: T010].
- [ ] T013 [P] Create Dockerfile for optional local execution (uses only CPU‑compatible base image) (build Docker image successfully).
- [ ] T014 [P] Configure `manifest.json` generation with content hashes in `code/utils/manifest.py` (FR‑024) (verify `manifest.json` contains SHA256 hashes) [DEPENDS ON: T007].
- [ ] T015 [P] Create `data/manual_validation/` directory structure for real-world validation annotations (verify directory exists).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Consistency Audit (Priority: P1) 🎯 MVP

**Goal**: End‑to‑end pipeline that ingests URLs, extracts metrics, reconstructs statistical tests, flags inconsistencies, and produces audit artifacts.

**Independent Test**: Run the pipeline on the synthetic validation dataset and verify precision ≥ 90% and recall ≥ 80% (SC‑030).

### Implementation for User Story 1

- [ ] T018 [P] US1 Implement URL ingestion and deduplication in `code/audit/ingestor.py` (reads `input/urls.csv`) (verify `output/urls_deduped.csv` exists).
- [ ] T019 [P] US1 Implement HTML fetching with retries and timeout in `code/audit/fetcher.py` (uses `requests`) (verify fetched HTML files are saved to `data/raw/`).
- [ ] T020 [P] US1 Implement extraction logic in `code/audit/extractor.py` → produces `ABSummary` objects, handles missing fields, logs `ERR-001`‑`ERR-099` (FR‑007) (verify extraction JSON exists and logs contain appropriate ERR codes).
- [ ] T020b [P] US1 Add verification step to ensure all error-message descriptions logged by T009/T020 are ≤200 characters per FR-007 (run unit tests to validate length constraint) [DEPENDS ON: T020].
- [ ] T020c [P] US1 Archive provenance metadata (original URL, fetch timestamp) in `data/provenance_log.csv` alongside extracted metrics per Constitution Principle VII (verify file exists with URL tracking) [DEPENDS ON: T020].
- [ ] T021 [P] US1 Unit tests for extractor covering missing metric, inequality p‑value, malformed HTML, conflicting sample sizes (tests/unit/test_extractor.py) (verify all tests pass) [DEPENDS ON: T020].
- [ ] T022 [P] US1 Implement outcome‑type detection heuristics in `code/audit/test_type_detector.py` (detect binary vs continuous only, no extra test‑type handling) (verify detector returns correct type).
- [ ] T023 [P] US1 Implement statistical reconstruction in `code/audit/reconstructor.py` (two‑proportion z/Fisher for binary, Welch t for continuous, fallback to average baseline per FR‑012) (verify reconstructed values match known fixtures).
- [ ] T024 [P] US1 Unit tests for reconstructor with known inputs (tests/unit/test_reconstructor.py) (verify all tests pass) [DEPENDS ON: T023].
- [ ] T025 [P] US1 Implement inconsistency validator in `code/audit/validator.py` applying FR‑004 thresholds (absolute p‑difference > 0.05, relative effect‑size > 5%) AND FR‑004b sample-size mismatch detection (>5% threshold), generating `AuditRecord` objects with data_quality_warning messages for sample-size discrepancies, writing `output/audit_report.json` (verify flags are set correctly and data_quality_warning messages are generated).
- [ ] T027 [P] US1 Unit tests for validator covering absolute p‑difference > 0.05, effect‑size > 5%, inequality handling, sample-size mismatch with data_quality_warning generation (tests/unit/test_validator.py) (verify all tests pass) [DEPENDS ON: T025].
- [ ] T026 [P] US1 Implement synthetic dataset generator in `code/audit/synthetic.py` (FR‑030) – outputs `data/processed/synthetic_validation.csv` + `data/processed/synthetic_ground_truth.json` with at least 10,000 simulated summaries (binary AND continuous outcomes) using analytical formulas (verify files are created and contain ≥10,000 records).
- [ ] T028 [P] US1 Implement power‑analysis utility (FR‑025) in `code/audit/power_analysis.py` that computes the minimum N given baseline, detectable effect, α and power, writes result to `output/power_analysis.json`, AND asserts audited corpus meets N≥300 requirement (verify JSON file exists, contains numeric N, and N≥300) [DEPENDS ON: T025].
- [ ] T029 [P] US1 Evaluate inconsistency‑detection component on synthetic validation dataset (FR‑031) – compute precision, recall, F1 and assert precision ≥ 90%, recall ≥ 80%, F1 ≥ 0.85 (depends on T026) (verify test passes, otherwise raise `ERR-800`) [DEPENDS ON: T026].
- [ ] T062 US1 Implement Monte‑Carlo validation module (FR‑026) in `code/audit/monte_carlo_validation.py` that runs A sufficient number of replicates for each statistical test (z-test, Fisher's, Welch's, binomial) and checks the absolute difference ≤ 0.005 (verify module exits with status 0).
- [ ] T031 [P] [DEPENDS ON: T062] Run Monte‑Carlo validation (from T062) as part of pipeline start‑up; abort with `ERR-801` if any test fails the ≤ 0.005 criterion (verify pipeline aborts on failure).
- [ ] T032 [P] US1 Implement end‑to‑end driver script `code/cli/run_audit.py` that orchestrates ingestion → fetch → extract → reconstruct → validate → write artifacts (verify script exits with status 0 on success).
- [ ] T033 US1 Integration test that runs driver on synthetic dataset, computes precision/recall/F1 and aborts with `ERR-800` if thresholds not met (tests/integration/test_synthetic_validation.py) (verify test passes) [DEPENDS ON: T026].
- [ ] T034 [P] US1 Create analysis notebook `notebooks/statistical_consistency_verification.ipynb` that documents any p-value discrepancies >0.05 with justification per Constitution Principle VI; run as part of pipeline acceptance (depends on T025) (verify notebook exists and contains discrepancy justifications) [DEPENDS ON: T025].
- [ ] T035 [P] US1 FR-001 Verification: Assert `input/urls.csv` processing completes without error (verification of T018).
- [ ] T036 [P] US1 FR-002 Verification: Assert extracted fields exist for >95% of valid pages (verification of T020).
- [ ] T037 [P] US1 FR-003 Verification: Assert reconstructed p-values computed for all records (verification of T023).
- [ ] T038 [P] US1 FR-004 Verification: Assert flags correspond to defined thresholds (verification of T025).

### Tests for User Story 1 (OPTIONAL) ⚠️

- [ ] T039 US1 Contract test for extractor output schema in `tests/contract/test_extractor_schema.py` (run AFTER T020 completes) (verify schema compliance) [DEPENDS ON: T020].
- [ ] T040 US1 Contract test for reconstructor output schema in `tests/contract/test_reconstructor_schema.py` (run AFTER T023 completes) (verify schema compliance) [DEPENDS ON: T023].
- [ ] T041 US1 Integration test that runs the full pipeline on `data/manual_validation/real_world_labels.csv` and asserts `ERR-800` is not raised (tests/integration/test_full_pipeline.py) (run AFTER T018-T032) (verify no ERR‑800) [DEPENDS ON: T018, T019, T020, T023, T025, T032].

---

## Phase 4: User Story 2 - Summary Report Generation (Priority: P2)

**Goal**: Produce a concise CSV report summarising total counts, inconsistency rates, bias‑adjusted rates, and Wilson confidence intervals.

**Independent Test**: Compare generated `summary_report.csv` against values derived from `audit_report.json` for a representative corpus.

### Implementation for User Story 2

- [ ] T042 [P] US2 Implement binomial prevalence test, Wilson CI, AND sensitivity analysis (FR‑005a & FR‑005b) in `code/audit/prevalence.py` including baseline proportion sweep from 0.02 to 0.10 (step 0.01) and max variation reporting (verify JSON output contains required fields including sensitivity analysis results).
- [ ] T043 [P] US2 Unit tests for binomial test and CI width ≤ 0.10 (tests/unit/test_prevalence.py) (verify test passes).
- [ ] T044 [P] US2 Implement bias‑adjustment module that computes domain‑weighted prevalence using logistic‑regression weighting (FR‑027) in `code/audit/bias_adjustment.py` AND implements subsampling action (randomly sample down to 30% threshold) when any domain exceeds [deferred] of corpus (verify bias‑adjusted rate is written and subsampling logic is triggered when threshold exceeded).
- [ ] T045 [P] US2 Unit tests for bias‑adjustment ensuring no domain exceeds [deferred] proportion (tests/unit/test_bias_adjustment.py) (verify test passes).
- [ ] T046 [P] US2 Implement CSV summary generator in `code/audit/report_generator.py` that reads `output/audit_report.json` and writes `output/summary_report.csv` with required columns (`total_summaries`, `inconsistent_count`, `inconsistent_rate`, `bias_adjusted_rate`, `wilson_ci_lower`, `wilson_ci_upper`) (verify CSV file exists and column headers match) [DEPENDS ON: T042, T044].
- [ ] T047 [P] US2 Unit test that validates CSV values exactly match JSON‑derived aggregates (tests/unit/test_report_generator.py) (verify test passes) [DEPENDS ON: T046].
- [ ] T048 [P] US2 Add Quickstart guide `docs/README_QUICKSTART.md` covering execution on 30 URLs within 30 minutes (FR‑028) AND include novice user verification step with written confirmation log (verify guide file exists and includes novice verification instructions).
- [ ] T049 US2 Verify FR-028 Quickstart execution time: run audit on 30 URLs and measure wall-clock time, assert ≤30 minutes on default GitHub Actions runner AND verify by novice user (depends on T048) (verify measurement recorded in `output/quickstart_timing.log` and novice verification documented as written confirmation log) [DEPENDS ON: T048].
- [ ] T050 [P] US2 Implement subgroup prevalence and Fisher's exact‑test analysis (FR‑032) in `code/audit/subgroup_analysis.py` that produces `output/subgroup_report.json` with domain, year, counts, prevalence, and p‑value (verify JSON file exists).
- [ ] T051 [P] US2 Unit tests for subgroup analysis covering groups with ≥ 10 summaries and verifying correct Fisher p‑values with Bonferroni correction (tests/unit/test_subgroup_analysis.py) (verify test passes).
- [ ] T052 [P] US2 Extend `report_generator.py` to also write the subgroup CSV `output/subgroup_report.csv` mirroring the JSON for easy inspection (verify CSV file exists) [DEPENDS ON: T046].
- [ ] T053 [P] US2 Integration test that runs the full pipeline on a mixed‑domain synthetic corpus and checks that subgroup report columns are present and correct (tests/integration/test_subgroup_report.py) (verify test passes).

### Tests for User Story 2 (OPTIONAL) ⚠️

- [ ] T054 US2 Contract test for prevalence calculations in `tests/contract/test_prevalence_schema.py` (run AFTER T042 completes) (verify schema compliance).
- [ ] T055 US2 Integration test that runs `code/audit/prevalence.py` on a known audit JSON and checks CSV columns (tests/integration/test_summary_generation.py) (run AFTER T042-T046) (verify CSV columns exist).

---

## Phase 5: User Story 3 - Export Audit Results (Priority: P3)

**Goal**: Ensure audit artifacts are exported correctly and are mutually consistent.

**Independent Test**: Verify that `output/audit_report.json` and `output/summary_report.csv` exist and contain identical counts of consistent vs inconsistent entries.

### Implementation for User Story 3

- [ ] T056 [P] US3 Ensure driver script creates `output/manifest.json` with SHA256 hashes for all generated files (via `code/utils/manifest.py`) (FR‑024) (verify manifest exists and contains hashes) [DEPENDS ON: T014].
- [ ] T057 [P] US3 Add schema validation step after audit generation to validate `audit_report.json` against `contracts/audit_record.schema.yaml` (FR‑026) (verify validation passes) [DEPENDS ON: T056].
- [ ] T058 [P] US3 Add schema validation step for `manifest.json` against `contracts/manifest.schema.yaml` (plan.md) (verify validation passes) [DEPENDS ON: T056].
- [ ] T059 [P] US3 Implement consistency checker in `code/audit/export_validator.py` that reads JSON and CSV, compares counts, and logs `ERR-201` if mismatch (plan.md) (verify no ERR‑201 logged) [DEPENDS ON: T056].
- [ ] T060 [P] US3 Unit test for export validator with deliberately mismatched files (tests/unit/test_export_validator.py) (verify test catches mismatch) [DEPENDS ON: T056].

### Tests for User Story 3 (OPTIONAL) ⚠️

- [ ] T030 US3 Integration test that checks JSON ↔ CSV count consistency (tests/integration/test_export_consistency.py) (run AFTER T056-T060) (verify counts match) [DEPENDS ON: T056].
- [ ] T061 US3 Contract test for manifest schema in `tests/contract/test_manifest_schema.py` (run AFTER T056 completes) (verify schema compliance).

---

## Phase 6: User Story 4 - Efficient CI Execution (Priority: P2)

**Goal**: Guarantee that the full pipeline runs within GitHub Actions resource limits and logs usage.

**Independent Test**: Trigger the workflow on a sample corpus of a modest number of URLs and confirm successful completion, ≤ 2 GB RAM, ≤ 2 vCPU.

### Implementation for User Story 4

- [ ] T098 [P] US4 Add resource‑monitoring module `code/utils/resource_monitor.py` that records peak CPU & memory, writes to `output/resource_log.json` (SC‑008) AND implements abort with ERR-301 when limits exceeded per FR-009 (verify log file exists, records within limits, and abort logic triggers on breach).
- [ ] T063 US4 Modify `code/cli/run_audit.py` to invoke `resource_monitor` and abort with `ERR-301` if limits exceeded (plan.md) (run AFTER T098) (verify script aborts on limit breach) [DEPENDS ON: T098].
- [ ] T064 [P] [DEPENDS ON: T098] US4 Update `.github/workflows/audit.yml` to include steps: (a) schema validation, (b) synthetic validation (ensure precision/recall thresholds), (c) resource‑monitor check, (d) main pipeline run (verify workflow runs all steps).
- [ ] T065 [P] US4 Add CI step that caches `pip` packages to stay within 6 hour total runtime (plan.md) (verify cache hit on subsequent runs).
- [ ] T066 [P] US4 Add unit test for resource monitor parsing of `/proc` (tests/unit/test_resource_monitor.py) (verify test passes) [DEPENDS ON: T098].

### Tests for User Story 4 (OPTIONAL) ⚠️

- [ ] T067 [P] US4 CI test that runs the workflow locally with `act` and asserts exit code 0 (tests/ci/test_ci_workflow.py) (verify exit code 0).

---

## Phase 7: Real-World Validation (FR-031b)

**Goal**: Create and evaluate the manually annotated real-world validation set per FR-031b and SC-031b.

**Independent Test**: Compute precision ≥ 85% and recall ≥ 75% (F1 ≥ 0.80) on the real-world validation set.

- [ ] T069 US1 Create real-world validation annotation task: ≥100 summaries with ground-truth labels determined by independent human annotators (two annotators, third resolves discrepancies) stored in `data/manual_validation/real_world_labels.csv` (FR‑031b) with stratification across FIVE MAJOR DOMAINS (tech, e-commerce, finance, healthcare, SaaS) with minimum 20 samples per domain (verify file exists with ≥100 rows, annotator columns, resolution notes, and domain distribution).
- [ ] T070 US1 Evaluate inconsistency‑detection component on real-world validation set (FR‑031b) – compute precision, recall, F1 and assert precision ≥ 85%, recall ≥ 75%, F1 ≥ 0.80 (depends on T069) (verify test passes, otherwise raise `ERR-802`) [DEPENDS ON: T069].
- [ ] T071 US1 Verify SC‑031b: Real-world validation precision ≥ 85% and recall ≥ 75% (run T070) (depends on T069) [DEPENDS ON: T069].

---

## Phase X: Success Criteria Verification

**Purpose**: Explicitly verify that every Success Criteria (SC‑*) is satisfied by the pipeline.

**⚠️ NOTE**: All Phase X tasks depend on completion of Phases 3-7 implementation artifacts.

- [ ] T072 [P] Verify SC‑001: Extraction accuracy ≥ 95% on `data/manual_validation/real_world_labels.csv` (run `tests/integration/test_extractor_accuracy.py`) (depends on T020, T069).
- [ ] T073 [P] Verify SC‑003: Monte‑Carlo vs library difference ≤ 0.005 for each statistical test (run `code/audit/monte_carlo_validation.py`) (depends on T062).
- [ ] T074 [P] Verify SC‑005: Parsing‑error rate ≤ 5% (run `code/audit/validator.py` and check log summary) (depends on T020).
- [ ] T075 [P] Verify SC‑008: CI execution completes within 6 h, ≤ 2 GB RAM, ≤ 2 vCPU (inspect `output/resource_log.json`) (depends on T098).
- [ ] T076 [P] Verify SC‑013: CI pipeline exits with status 0 and produces `manifest.json` in ≥ 99% of runs (run CI locally and check) (depends on T056).
- [ ] T077 [P] Verify SC‑014: Binomial test output meets formatting and CI width ≤ 0.10 (run `code/audit/prevalence.py` and inspect JSON) (depends on T042).
- [ ] T078 [P] Verify SC‑015: Sensitivity analysis variation < 0.02 across baseline range (run `code/audit/prevalence.py` and inspect results) (depends on T042).
- [ ] T079 [P] Verify SC‑024: `summary_report.csv` columns and values match `audit_report.json` (run `tests/integration/test_summary_consistency.py`) (depends on T046).
- [ ] T080 [P] Verify SC‑025: Audited corpus size N ≥ 300 (check `output/power_analysis.json`) (depends on T028).
- [ ] T081 [P] Verify SC‑026: Monte‑Carlo validation passes for all tests (same as T073) (depends on T062) [DEPENDS ON: T073].
- [ ] T082 [P] Verify SC‑027: No domain exceeds [deferred] proportion and bias‑adjusted rate reported (run `code/audit/bias_adjustment.py` and inspect output) (depends on T044).
- [ ] T083 [P] Verify SC‑028: Quickstart guide enables audit of 30 URLs in ≤ 30 minutes on GH Actions AND novice-user verification (time execution of Quickstart script and verify written confirmation log AND novice-user verification step) (depends on T048, T049).
- [ ] T084 US1 Verify SC‑030: Synthetic validation precision ≥ 90% and recall ≥ 80% (run T029) (depends on T026).
- [ ] T085 [P] Verify SC‑031b: Real-world validation precision ≥ 85% and recall ≥ 75% (run T070) (depends on T070).
- [ ] T086 [P] Verify SC‑032: Subgroup analysis produces Fisher's exact test results for groups ≥ 10 (run `code/audit/subgroup_analysis.py` and check JSON) (depends on T050).
- [ ] T087 [P] Verify overall pipeline passes all above SC checks without errors (run full suite) (depends on T072-T086).
- [ ] T096 [P] Compute checksums for ALL files under data/ (raw, processed, output) and record them in data/checksums.txt as mandated by Constitution Principle III (verify file exists with SHA256 hashes for all data files) [DEPENDS ON: T026, T025, T046, T069].
- [ ] T097 [P] Extend manifest.json generation to include the same checksums recorded in data/checksums.txt (depends on T096) (verify both locations contain identical hashes) [DEPENDS ON: T096].

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T088 [P] Documentation updates in `docs/` – expand API reference, data‑model description, and troubleshooting guide (verify docs build without errors).
- [ ] T089 [P] Code cleanup: add type hints throughout `code/`, run `mypy --strict` (verify no type errors).
- [ ] T090 [P] Performance optimization: replace in‑memory DataFrame joins with chunked processing in `code/audit/prevalence.py` to keep RAM ≤ 1.5 GB for large corpora (SC‑008) (verify memory usage).
- [ ] T091 [P] Add additional edge‑case unit tests (missing metric, conflicting sample sizes, dead URLs) in `tests/unit/` (verify all pass).
- [ ] T092 [P] Add additional edge‑case unit tests for subgroup analysis (missing domain, year, Fisher edge cases) in `tests/unit/` (verify all pass).
- [ ] T093 [P] Run full benchmark on 5,000 synthetic URLs; record wall‑clock time in `output/benchmark.log` and ensure ≤ 6 hours (SC‑008) (verify log).
- [ ] T094 [P] Release version tag `v0.1.0` and update `CHANGELOG.md` with released features (verify tag exists).
- [ ] T095 [P] Implement documentation DOC001: Error codes reference guide in `docs/error_codes.md` (FR-007) (verify doc exists and covers all ERR-### codes).
- [ ] T096b [P] Implement documentation DOC002: Statistical methodology reference in `docs/statistical_methodology.md` (FR-003, FR-026) (verify doc exists and covers z-test, Fisher, Monte‑Carlo).
- [ ] T097b [P] Implement documentation DOC003: Data provenance guide in `docs/data_provenance.md` (Constitution Principle VII) (verify doc exists and covers URL tracking, checksums, manifest).
- [ ] T099 [P] Implement governance invalidation mechanism in code/utils/governance.py (Constitution Principle V) AND documentation DOC004 in docs/governance_invalidations.md. Mechanism detects artifact hash changes and invalidates stale review records (verify code executes and doc exists).
- [ ] T100 [P] Run Reference-Validator Agent on all external citations (Kohavi et al., John et al.) in spec/plan/docs per Constitution Principle II at all three Constitution-specified points (artifact write, Advancement-Evaluator gate, research_review→research_accepted transition) and record verification log (verify citations validated before review points awarded and log confirms all 3 points).

---

## Phase Dependencies

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories (T006-T012 must complete before US1)
- **User Stories (Phase 3‑6)**: All depend on Foundational (Phase 2) completion
  - User stories can proceed in parallel (if staffed) or sequentially by priority (P1 → P2 → P3 → P4)
- **Real-World Validation (Phase 7)**: Depends on US1 implementation (T020, T025)
- **Success Criteria Verification (Phase X)**: Depends on completion of all user‑story artifacts
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational infrastructure (T006-T012) - no dependencies on other stories
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
- All Foundational tasks marked **[P]** can run in parallel (within Phase 2, T006-T012 block US1)
- Once Foundational infrastructure (T006-T012) is done, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked **[P]** can run in parallel
- Different user stories can be worked on in parallel by different developers

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational infrastructure (T006-T012) - CRITICAL - blocks all stories
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run synthetic‑validation integration test (T033) - must pass precision/recall thresholds
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational together
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test CI limits → Deploy/Demo
6. Run Real-World Validation (Phase 7) → Verify SC-031b
7. Run Polish phase for documentation, performance, and release

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational infrastructure (T006-T012) is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
   - Developer D: User Story 4 (CI integration)
   - Developer E: Real-World Validation (Phase 7)
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
- **Path Note**: All Python code paths use `code/` directory per Constitution Principle I (random seeds pinned in `code/`).
- **Constraint Level**: All tasks preserve or exceed FR/SC constraint levels (no weakening of FR-025 N≥300, FR-026 10,000 replicates, FR-004 0.05 threshold, SC-003 0.005 MC tolerance, etc.).
- **CPU Feasibility**: All tasks are designed to run on CPU-only CI (2 vCPU, 2 GB RAM, 6 h timeout); no GPU, no large-model inference, no 8-bit quantization.