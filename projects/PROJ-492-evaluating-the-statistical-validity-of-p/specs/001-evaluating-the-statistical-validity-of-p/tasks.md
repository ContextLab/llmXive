---  
description: "Task list template for feature implementation"  
---  

# Tasks: Evaluating the Statistical Validity of Public A/B Test Summaries  

**Input**: Design documents from `/specs/001-eval-ab-test-validity/`  
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/  

**Tests**: The examples below include test tasks. Tests are OPTIONAL – only include them if explicitly requested in the feature specification.  

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.  

## Format: `[ID] [P?] [Story] Description`  

- **[P]**: Can run in parallel (different files, no dependencies)  
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)  
- Include exact file paths in descriptions  

## Path Conventions  

- **Single project**: `src/`, `tests/` at repository root  
- **Web app**: `backend/src/`, `frontend/src/`  
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`  
- Paths shown below assume single project – adjust based on plan.md structure  

---  

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure  

- [ ] T001 Create repository skeleton with `src/`, `tests/`, `data/`, `output/`, `contracts/`, `.github/`, `docs/` directories (plan.md)  
- [ ] T002 Initialize Python 3.11 project: `pyproject.toml` with required dependencies (`requests`, `beautifulsoup4`, `pandas`, `numpy`, `scipy`, `statsmodels`, `tqdm`, `pyyaml`, `jsonschema`, `psutil`) (plan.md)  
- [ ] T003 [P] Add linting and formatting tools (`ruff`, `black`) and configure pre‑commit hooks (plan.md)  
- [ ] T004 [P] Create `requirements.txt` mirroring `pyproject.toml` for CI reproducibility (plan.md)  

---  

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented  

**⚠️ CRITICAL**: No user story work can begin until this phase is complete  

- [ ] T005 Create data‑model definitions (`ABSummary`, `AuditRecord`) in `src/models/data_models.py` (plan.md)  
- [ ] T006 Create JSON‑Schema files `contracts/extracted_summary.schema.yaml` and `contracts/audit_record.schema.yaml` (plan.md)  
- [ ] T007 Implement schema‑validation utilities in `src/contracts/validation.py` (plan.md)  
- [ ] T008 Set up structured logging infrastructure in `src/utils/logger.py` with error‑code format `ERR-###` (FR‑007) (plan.md)  
- [ ] T009 Add configuration constants (random seeds, thresholds, resource caps) in `src/config.py` (plan.md)  
- [ ] T010 Implement generic helper functions (`checksum`, `domain_from_url`, `safe_float`) in `src/utils/helpers.py` (plan.md)  
- [ ] T011 Create CI workflow file `.github/workflows/audit.yml` that installs dependencies, enforces CPU ≤ 2 vCPU, RAM ≤ 2 GB, timeout 6 h, and runs `run_audit.sh` (FR‑009) (plan.md)  
- [ ] T012 Add Dockerfile for optional local execution (uses only CPU‑compatible base image) (plan.md)  
- [ ] T013 [P] Configure `manifest.json` generation with content hashes in `src/utils/manifest.py` (FR‑024) (plan.md)  

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel  

---  

## Phase 3: User Story 1 – Automated Consistency Audit (Priority: P1) 🎯 MVP  

**Goal**: End‑to‑end pipeline that ingests URLs, extracts metrics, reconstructs statistical tests, flags inconsistencies, and produces audit artifacts.  

**Independent Test**: Run the pipeline on the synthetic validation dataset (1 000 records) and verify precision ≥ 90 % and recall ≥ 80 % (SC‑030).  

### Tests for User Story 1 (OPTIONAL) ⚠️  

- [ ] T014 [P] US1 Contract test for extractor output schema in `tests/contract/test_extractor_schema.py`  
- [ ] T015 [P] US1 Contract test for reconstructor output schema in `tests/contract/test_reconstructor_schema.py`  
- [ ] T016 [P] US1 Integration test that runs the full pipeline on `data/synthetic/validation.csv` and asserts `ERR-800` is not raised (tests/integration/test_full_pipeline.py)  

### Implementation for User Story 1  

- [ ] T017 [P] US1 Implement URL ingestion and deduplication in `src/audit/ingestor.py` (reads `input/urls.csv`)  
- [ ] T018 [P] US1 Implement HTML fetching with retries and timeout in `src/audit/fetcher.py` (uses `requests`)  
- [ ] T019 [P] US1 Implement extraction logic in `src/audit/extractor.py` → produces `ABSummary` objects, handles missing fields, logs `ERR-001`‑`ERR-099` (FR‑007) (plan.md)  
- [ ] T020 [P] US1 Unit tests for extractor covering missing metric, inequality p‑value, malformed HTML (tests/unit/test_extractor.py)  
- [ ] T021 [P] US1 Implement test‑type detection heuristics in `src/audit/test_type_detector.py` (handles binary vs continuous, chi‑square, logistic‑regression mentions) (plan.md)  
- [ ] T022 [P] US1 Implement statistical reconstruction in `src/audit/reconstructor.py` (two‑proportion z/Fisher, Welch t, fallback to average baseline per FR‑012)  
- [ ] T023 [P] US1 Unit tests for reconstructor with known inputs (tests/unit/test_reconstructor.py)  
- [ ] T024 [P] US1 Implement inconsistency validator in `src/audit/validator.py` applying FR‑004 thresholds, generating `AuditRecord` objects, writing `output/audit_report.json` (plan.md)  
- [ ] T025 [P] US1 Unit tests for validator covering absolute p‑difference > 0.05, effect‑size > 5 %, inequality handling (tests/unit/test_validator.py)  
- [ ] T026 [P] US1 Implement synthetic dataset generator in `src/audit/synthetic.py` (FR‑030) – outputs CSV + ground‑truth JSON (plan.md)  
- [ ] T027 [P] US1 Implement end‑to‑end driver script `src/__main__.py` (or `run_audit.sh`) that orchestrates ingestion → fetch → extract → reconstruct → validate → write artifacts (plan.md)  
- [ ] T028 [P] US1 Integration test that runs driver on synthetic dataset, computes precision/recall/F1 and aborts with `ERR-800` if thresholds not met (tests/integration/test_synthetic_validation.py)  

---  

## Phase 4: User Story 2 – Summary Report Generation (Priority: P2)  

**Goal**: Produce a concise CSV report summarising total counts, inconsistency rates, bias‑adjusted rates, and Wilson confidence intervals.  

**Independent Test**: Compare generated `summary_report.csv` against values derived from `audit_report.json` for a representative corpus.  

### Tests for User Story 2 (OPTIONAL) ⚠️  

- [ ] T029 [P] US2 Contract test for prevalence calculations in `tests/contract/test_prevalence_schema.py`  
- [ ] T030 [P] US2 Integration test that runs `src/audit/prevalence.py` on a known audit JSON and checks CSV columns (tests/integration/test_summary_generation.py)  

### Implementation for User Story 2  

- [ ] T031 [P] US2 Implement binomial prevalence test, Wilson CI, and sensitivity analysis (FR‑005a & FR‑005b) in `src/audit/prevalence.py`  
- [ ] T032 [P] US2 Unit tests for binomial test and CI width ≤ 0.10 (tests/unit/test_prevalence.py)  
- [ ] T033 [P] US2 Implement bias‑adjustment module that computes domain‑weighted prevalence using logistic‑regression weighting (FR‑027) in `src/audit/bias_adjustment.py`  
- [ ] T034 [P] US2 Unit tests for bias‑adjustment ensuring no domain exceeds 30 % (tests/unit/test_bias_adjustment.py)  
- [ ] T035 [P] US2 Implement CSV summary generator in `src/audit/report_generator.py` that reads `audit_report.json` and writes `output/summary_report.csv` with required columns (plan.md)  
- [ ] T036 [P] US2 Unit test that validates CSV values exactly match JSON‑derived aggregates (tests/unit/test_report_generator.py)  
- [ ] T037 [P] US2 Add Quickstart guide `README_QUICKSTART.md` covering execution on 30 URLs within 30 minutes (FR‑028) (plan.md)  

---  

## Phase 5: User Story 3 – Export Audit Results (Priority: P3)  

**Goal**: Ensure audit artifacts are exported correctly and are mutually consistent.  

**Independent Test**: Verify that `output/audit_report.json` and `output/summary_report.csv` exist and contain identical counts of consistent vs. inconsistent entries.  

### Tests for User Story 3 (OPTIONAL) ⚠️  

- [ ] T038 [P] US3 Contract test for manifest schema in `tests/contract/test_manifest_schema.py`  
- [ ] T039 [P] US3 Integration test that checks JSON ↔ CSV count consistency (tests/integration/test_export_consistency.py)  

### Implementation for User Story 3  

- [ ] T040 [P] US3 Ensure driver script creates `output/manifest.json` with SHA256 hashes for all generated files (via `src/utils/manifest.py`) (FR‑024)  
- [ ] T041 [P] US3 Add schema validation step after audit generation to validate `audit_report.json` against `contracts/audit_record.schema.yaml` (FR‑026)  
- [ ] T042 [P] US3 Add schema validation step for `manifest.json` against `contracts/manifest.schema.yaml` (plan.md)  
- [ ] T043 [P] US3 Implement consistency checker in `src/audit/export_validator.py` that reads JSON and CSV, compares counts, and logs `ERR-201` if mismatch (plan.md)  
- [ ] T044 [P] US3 Unit test for export validator with deliberately mismatched files (tests/unit/test_export_validator.py)  

---  

## Phase 6: User Story 4 – Efficient CI Execution (Priority: P2)  

**Goal**: Guarantee that the full pipeline runs within GitHub Actions resource limits and logs usage.  

**Independent Test**: Trigger the workflow on a sample corpus of 30 URLs and confirm successful completion under 6 hours, ≤ 2 GB RAM, ≤ 2 vCPU.  

### Tests for User Story 4 (OPTIONAL) ⚠️  

- [ ] T045 [P] US4 CI test that runs the workflow locally with `act` and asserts exit code 0 (tests/ci/test_ci_workflow.py)  

### Implementation for User Story 4  

- [ ] T046 [P] US4 Add resource‑monitoring module `src/utils/resource_monitor.py` that records peak CPU & memory, writes to `output/resource_log.json` (SC‑008)  
- [ ] T047 [P] US4 Modify `run_audit.sh` to invoke `resource_monitor` and abort with `ERR-301` if limits exceeded (plan.md)  
- [ ] T048 [P] US4 Update `.github/workflows/audit.yml` to include steps: (a) schema validation, (b) synthetic validation (ensure precision/recall thresholds), (c) resource‑monitor check, (d) main pipeline run (plan.md)  
- [ ] T049 [P] US4 Add CI step that caches `pip` packages to stay within 6 hour total runtime (plan.md)  
- [ ] T050 [P] US4 Add unit test for resource monitor parsing of `/proc` (tests/unit/test_resource_monitor.py)  

---  

## Phase N: Polish & Cross‑Cutting Concerns  

**Purpose**: Improvements that affect multiple user stories  

- [ ] T051 [P] Documentation updates in `docs/` – expand API reference, data‑model description, and troubleshooting guide (plan.md)  
- [ ] T052 [P] Code cleanup: add type hints throughout `src/`, run `mypy --strict` (plan.md)  
- [ ] T053 [P] Performance optimization: replace in‑memory DataFrame joins with chunked processing in `src/audit/prevalence.py` to keep RAM ≤ 1.5 GB for 5 000 URLs (SC‑008)  
- [ ] T054 [P] Add additional edge‑case unit tests (missing metric, conflicting sample sizes, dead URLs) in `tests/unit/` (plan.md)  
- [ ] T055 [P] Run full benchmark on 5 000 synthetic URLs; record wall‑clock time in `output/benchmark.log` and ensure ≤ 6 hours (SC‑008)  
- [ ] T056 [P] Release version tag `v0.1.0` and update `CHANGELOG.md` with released features (plan.md)  

---  

## Dependencies & Execution Order  

### Phase Dependencies  

- **Setup (Phase 1)**: No dependencies – can start immediately  
- **Foundational (Phase 2)**: Depends on Setup completion – BLOCKS all user stories  
- **User Stories (Phase 3‑6)**: All depend on Foundational (Phase 2) completion  
  - User stories can proceed in parallel (if staffed) or sequentially by priority (P1 → P2 → P3 → P4)  
- **Polish (Final Phase)**: Depends on all desired user stories being complete  

### User Story Dependencies  

- **User Story 1 (P1)**: Can start after Foundational – no dependencies on other stories  
- **User Story 2 (P2)**: Can start after Foundational – may consume output of US1 (`audit_report.json`)  
- **User Story 3 (P3)**: Can start after Foundational – consumes outputs of US1 & US2  
- **User Story 4 (P2)**: Can start after Foundational – wraps the entire pipeline for CI  

### Within Each User Story  

- Tests (if included) MUST be written and FAIL before implementation  
- Models before services  
- Services before endpoints / scripts  
- Core implementation before integration  
- Story complete before moving to next priority  

### Parallel Opportunities  

- All Setup tasks marked **[P]** can run in parallel  
- All Foundational tasks marked **[P]** can run in parallel (within Phase 2)  
- Once Foundational is done, all user stories can start in parallel (if team capacity allows)  
- All tests for a user story marked **[P]** can run in parallel  
- Models within a story marked **[P]** can run in parallel  
- Different user stories can be worked on in parallel by different developers  

---  

## Implementation Strategy  

### MVP First (User Story 1 Only)  

1. Complete Phase 1: Setup  
2. Complete Phase 2: Foundational (CRITICAL – blocks all stories)  
3. Complete Phase 3: User Story 1  
4. **STOP and VALIDATE**: Run synthetic‑validation integration test (T028) – must pass precision/recall thresholds  
5. Deploy/demo if ready  

### Incremental Delivery  

1. Complete Setup + Foundational → Foundation ready  
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)  
3. Add User Story 2 → Test independently → Deploy/Demo  
4. Add User Story 3 → Test independently → Deploy/Demo  
5. Add User Story 4 → Test CI limits → Deploy/Demo  
6. Run Polish phase for documentation, performance, and release  

### Parallel Team Strategy  

With multiple developers:  

1. Team completes Setup + Foundational together  
2. Once Foundational is done:  
   - Developer A: User Story 1  
   - Developer B: User Story 2  
   - Developer C: User Story 3  
   - Developer D: User Story 4 (CI integration)  
3. Stories complete and integrate independently without breaking previous work  

---  

## Notes  

- **[P]** tasks = different files, no dependencies  
- **[Story]** label maps task to specific user story for traceability  
- Each user story should be independently completable and testable  
- Verify tests fail before implementing  
- Commit after each task or logical group  
- Stop at any checkpoint to validate story independently  
- Avoid: vague tasks, same file conflicts, cross‑story dependencies that break independence
