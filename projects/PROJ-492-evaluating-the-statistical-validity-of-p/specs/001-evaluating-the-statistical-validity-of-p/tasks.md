# Tasks: Evaluating the Statistical Validity of Public A/B Test Summaries

**Input**: Design documents from `/specs/001-eval-ab-test-validity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Plan Traceability**: Task IDs align with plan.md phases and requirements (FR-001 through FR-032, SC-001 through SC-032).

## NOTE
The original plan.md defines tasks T000‑T005 which conflict with the existing task ID space (T001‑T100). To preserve existing task identifiers while restoring traceability, we introduce distinct **PT###** identifiers for plan‑root tasks. These PT### tasks mirror the plan‑phase requirements and do not interfere with the existing T### workflow.

---

## Phase 0: Plan‑Root Tasks (new PT### IDs)

- [ ] PT000 Create CLI interface skeleton (`code/cli/main.py`) per plan T000 (verify script runs with `--help`).
- [ ] PT001 Set up GitHub Actions workflow (`.github/workflows/audit.yml`) per plan T001 (verify CI triggers on push).
- [ ] PT002 Implement Monte‑Carlo framework core (`code/audit/monte_carlo_core.py`) per plan T002 (verify core functions importable).
- [ ] PT003 Add statistical verification utilities (`code/audit/stat_verification.py`) per plan T003 (verify functions compute z‑test, t‑test, Fisher).
- [ ] PT004 Implement power‑analysis utility (`code/audit/power_analysis.py`) per plan T004 (verify it outputs JSON with required fields).
- [ ] PT005C **[P]** Implement Constitution compliance checker in `code/utils/constitution_checker.py` that validates all seven Principles (I–VII). Run this checker in CI and abort with `ERR-950` if any principle fails. (verify checker script exists, runs in CI, and passes all seven checks).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create repository skeleton with `code/`, `tests/`, `data/`, `output/`, `contracts/`, `notebooks/`, `.github/`, `docs/` directories (verify directories exist).
- [ ] T002 Initialize Python project: `pyproject.toml` with required dependencies (`requests`, `beautifulsoup4`, `pandas`, `numpy`, `scipy`, `statsmodels`, `tqdm`, `pyyaml`, `jsonschema`, `psutil`). 
- [ ] T003 Add linting and formatting tools (`ruff`, `black`) and configure pre‑commit hooks (run `pre-commit run --all-files` with zero violations).
- [ ] T004 Create `requirements.txt` mirroring `pyproject.toml` for CI reproducibility (verify `requirements.txt` matches `pyproject.toml`).
- [ ] T005 Create `.gitignore` excluding `__pycache__`, `*.pyc`, `data/raw/*` except URLs, `output/*` (verify git status clean).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until foundational infrastructure (T006‑T012) is complete; remaining Phase 2 tasks (T013‑T020) may proceed in parallel with US1 implementation

**Checkpoint**: Foundational infrastructure (T006‑T012) ready - US1 implementation can now begin; T013 and other non‑blocking foundational tasks (T013‑T020) can proceed in parallel with US1 after T006‑T012 completion.

- [ ] T006 Create data‑model definitions (`ABSummary`, `AuditRecord`) in `code/models/data_models.py` using Pydantic (verify classes exist and importable).
- [ ] T007 Create JSON‑Schema files `contracts/extracted_summary.schema.yaml` and `contracts/audit_record.schema.yaml` (verify schemas are valid YAML).
- [ ] T008 Implement schema‑validation utilities in `code/contracts/validation.py` (run unit test to confirm validation works) [DEPENDS ON: T007].
- [ ] T009 Set up structured logging infrastructure in `code/utils/logger.py` with error‑code format `ERR-###` (verify logs contain correct codes).
- [ ] T010 Initialize configuration constants (random seeds, thresholds, resource caps) in `code/config.py` with deterministic seed (`SEED = 42`) AND ensure all modules import SEED from config and set RNG seeds at startup (verify `code/config.py` defines `SEED = 42` and all RNGs are seeded per Constitution Principle I).
- [ ] T011 Implement generic helper functions (`checksum`, `domain_from_url`, `safe-float`, `parse_inequality_p`) in `code/utils/helpers.py` (run unit test for each helper).
- [ ] T012 Create CI workflow file `.github/workflows/audit.yml` that installs dependencies, enforces CPU ≤ 2 vCPU, RAM ≤ 2 GB, timeout a predefined duration, and runs audit pipeline (verify workflow runs and respects limits) [DEPENDS ON: T010].
- [ ] T013 Create Dockerfile for optional local execution (uses only CPU‑compatible base image) (build Docker image successfully) [DEPENDS ON: T012].
- [ ] T014 Configure `manifest.json` generation with content hashes in `code/utils/manifest.py` (FR‑024) (verify `manifest.json` contains SHA256 hashes) [DEPENDS ON: T007].
- [ ] T015 Create `data/manual_validation/` directory structure for real‑world validation annotations (verify directory exists).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 – Automated Consistency Audit (Priority: P1) 🎯 MVP

**Goal**: End‑to‑end pipeline that ingests URLs, extracts metrics, reconstructs statistical tests, flags inconsistencies, and produces audit artifacts.

**Independent Test**: Run the pipeline on the synthetic validation dataset and verify precision ≥ 90 % and recall ≥ 80 % (SC‑030).

### Implementation for User Story 1

- [ ] T018 URL ingestion and deduplication in `code/audit/ingestor.py` (reads `input/urls.csv`) (verify `output/urls_deduped.csv` exists). **DEPENDS ON:** None.
- [ ] T019 HTML fetching with retries and timeout in `code/audit/fetcher.py` (uses `requests`) (verify fetched HTML files are saved to `data/raw/`). **DEPENDS ON:** T018.
- [ ] T020 Extraction logic in `code/audit/extractor.py` → produces `ABSummary` objects, handles missing fields, logs `ERR-001`‑`ERR-099` (FR‑007) (verify extraction JSON exists and logs contain appropriate ERR codes). **DEPENDS ON:** T019.
- [ ] T020b **[P]** Run unit tests `tests/unit/test_error_message_format.py` to ensure all logged error‑message descriptions are ≤ 200 characters and follow FR‑007 naming conventions. **DEPENDS ON:** T020.
- [ ] T020c Archive provenance metadata in `data/provenance_log.csv` per Constitution Principle VII (verify file exists with URL, repository identifier, and fetch timestamp). **DEPENDS ON:** T020.
- [ ] T020d **[P]** Verify that every row in `data/provenance_log.csv` contains URL, repository identifier, and fetch timestamp (run validation script `tests/unit/test_provenance_schema.py`). **DEPENDS ON:** T020c.
- [ ] T021 Unit tests for extractor covering missing metric, inequality p‑value, malformed HTML, conflicting sample sizes (tests/unit/test_extractor.py) (verify all tests pass) [DEPENDS ON: T020].
- [ ] T022 Implement outcome‑type detection heuristics in `code/audit/test_type_detector.py` (detect binary vs continuous only, no extra test‑type handling) (verify detector returns correct type).
- [ ] T023 Implement statistical reconstruction in `code/audit/reconstructor.py` (two‑proportion z/Fisher for binary, Welch t for continuous, fallback to average baseline per FR‑012) (verify reconstructed values match known fixtures).
- [ ] T024 Unit tests for reconstructor with known inputs (tests/unit/test_reconstructor.py) (verify all tests pass) [DEPENDS ON: T023].
- [ ] T025 Implement inconsistency validator in `code/audit/validator.py` applying FR‑004 thresholds (absolute p‑difference > 0.05, relative effect‑size > 5 %) **and verify that sample‑size mismatch entries are excluded from aggregate prevalence estimates** per FR‑004b (generate `AuditRecord` objects with data_quality_warning messages for sample‑size discrepancies, writing `output/audit_report.json`). **DEPENDS ON:** T023.
- [ ] T025b **[P]** Run `tests/unit/test_missing_baseline_flag.py` to verify that any entry with a missing baseline conversion rate is flagged in the audit notes as required by FR‑012. **DEPENDS ON:** T025.
- [ ] T025c **[P]** Run `tests/unit/test_sample_size_exclusion.py` to verify that summaries flagged for sample‑size mismatch are not included in `output/prevalence.json`. **DEPENDS ON:** T025.
- [ ] T027 Unit tests for validator covering absolute p‑difference > 0.05, effect‑size > 5 %, inequality handling, sample‑size mismatch with data_quality_warning generation (tests/unit/test_validator.py) (verify all tests pass) [DEPENDS ON: T025].
- [ ] T026 Implement synthetic dataset generator in `code/audit/synthetic.py` (FR‑030) – outputs `data/processed/synthetic_validation.csv` + `data/processed/synthetic_ground_truth.json` with at least 10 000 simulated summaries (binary AND continuous outcomes) **and verify both outcome types are present** (constraint‑preservation‑2958f04c) (verify files are created and contain ≥ 10 000 records). **DEPENDS ON:** T028.
- [ ] T026b **[P]** Verify that the synthetic dataset contains at least one binary and one continuous outcome record (run outcome‑type check script `tests/unit/test_synthetic_outcome_types.py`). **DEPENDS ON:** T026.
- [ ] T028 Implement power‑analysis utility in `code/audit/power_analysis.py` (FR‑025) that computes the minimum N given baseline, detectable effect, α and power, writes result to `output/power_analysis.json`, **and asserts audited corpus meets N ≥ 300 OR N ≥ calculated_minimum** (constraint‑preservation‑ba913176) (verify JSON file exists, contains numeric N, and satisfies condition). **DEPENDS ON:** T025.
- [ ] T029 Evaluate inconsistency‑detection component on synthetic validation dataset (FR‑031) – compute precision, recall, F1 and assert precision ≥ 90 %, recall ≥ 80 %, F1 ≥ 0.85 (depends on T026) (verify test passes, otherwise raise `ERR-800`) [DEPENDS ON: T026].
- [ ] T062 Implement Monte‑Carlo validation module (FR‑026) in `code/audit/monte_carlo_validation.py` that runs 10 000 replicates for each statistical test (z-test, Fisher's, Welch's, binomial) and checks the absolute difference ≤ 0.005 (constraint‑preservation‑e62a0df4) (verify module exits with status 0).
- [ ] T031 **[P]** Run Monte‑Carlo validation (from T062) as part of pipeline start‑up; abort with `ERR-801` if any test fails the ≤ 0.005 criterion (T031 runs T062 module internally). **DEPENDS ON:** T062.
- [ ] T032 Implement end‑to‑end driver script `code/cli/run_audit.py` that orchestrates ingestion → fetch → extract → reconstruct → validate → write artifacts (verify script exits with status 0 on success).
- [ ] T033 Integration test that runs driver on synthetic dataset, computes precision/recall/F1 and aborts with `ERR-800` if thresholds not met (tests/integration/test_synthetic_validation.py) (verify test passes) [DEPENDS ON: T026].
- [ ] T034 Create analysis notebook `notebooks/statistical_consistency_verification.ipynb` that documents any p‑value discrepancies >0.05 with justification per Constitution Principle VI; run as part of pipeline acceptance (depends on T025) (verify notebook exists and contains discrepancy justifications) [DEPENDS ON: T025].
- [ ] T035 FR‑001 Verification: Run `tests/integration/test_url_ingestion.py` to assert `input/urls.csv` processing completes without error (coverage‑executability‑08d5764f) (verify test passes).
- [ ] T036 FR‑002 Verification: Run `tests/integration/test_extractor_accuracy.py` to assert extracted fields exist for > 95 % of valid pages (coverage‑executability‑08d5764f) (verify test passes).
- [ ] T037 FR‑003 Verification: Run `tests/integration/test_reconstructor_completeness.py` to assert reconstructed p‑values computed for all records (coverage‑executability‑08d5764f) (verify test passes).
- [ ] T038 FR‑004 Verification: Run `tests/integration/test_validator_thresholds.py` to assert flags correspond to defined thresholds (coverage‑executability‑08d5764f) (verify test passes).

### Tests for User Story 1 (OPTIONAL) ⚠️

- [ ] T039 US1 Contract test for extractor output schema in `tests/contract/test_extractor_schema.py` (run AFTER T020 completes) (verify schema compliance) [DEPENDS ON: T020].
- [ ] T040 US1 Contract test for reconstructor output schema in `tests/contract/test_reconstructor_schema.py` (run AFTER T023 completes) (verify schema compliance) [DEPENDS ON: T023].
- [ ] T041 Integration test that runs the full pipeline on `data/manual_validation/real_world_labels.csv` and asserts `ERR-800` is not raised (tests/integration/test_full_pipeline.py) (run AFTER T018‑T032) (verify no ERR‑800) [DEPENDS ON: T018, T019, T020, T023, T025, T032].

---

## Phase 4: User Story 2 – Summary Report Generation (Priority: P2)

**Goal**: Produce a concise CSV report summarising total counts, inconsistency rates, bias‑adjusted rates, and Wilson confidence intervals.

**Independent Test**: Compare generated `summary_report.csv` against values derived from `audit_report.json` for a representative corpus.

### Implementation for User Story 2

- [ ] T042 Implement binomial prevalence test, Wilson CI, **and sensitivity analysis** (FR‑005a & FR‑005b) in `code/audit/prevalence.py` including baseline proportion sweep across a range of low proportions, and **Bonferroni‑corrected α = 0.0056** per SC‑015 (verify JSON output contains required fields including sensitivity analysis results).
- [ ] T042b **[P]** Verify that `prevalence.json` does **not** contain any entries flagged for sample‑size mismatch (cross‑check with T025c). (depends on T025c)
- [ ] T043 Unit tests for binomial test and CI width ≤ 0.10 (tests/unit/test_prevalence.py) (verify test passes).
- [ ] T044 **[P]** Power Analysis utility (FR‑025): run `code/audit/power_analysis.py` to compute minimum required N and verify audited corpus meets N ≥ 300 (or exceeds calculated minimum). Stores results in `output/power_analysis.json`. (uses underlying implementation from T028) **DEPENDS ON:** T028.
- [ ] T045 Implement bias‑adjustment module that computes domain‑weighted prevalence using domain‑weighted averaging (FR‑027) **and either subsamples the dominant domain *or* flags a violation** per FR‑027 (constraint‑preservation‑01844dd3) in `code/audit/bias_adjustment.py` (verify bias‑adjusted rate is written and appropriate action taken when any domain exceeds 30 %). 
- [ ] T046 Unit tests for bias‑adjustment ensuring no domain exceeds 30 % proportion (tests/unit/test_bias_adjustment.py) (verify test passes).
- [ ] T047 Implement CSV summary generator in `code/audit/report_generator.py` that reads `output/audit_report.json` and writes `output/summary_report.csv` with required columns (`total_summaries`, `inconsistent_count`, `inconsistent_rate`, `bias_adjusted_rate`, `wilson_ci_lower`, `wilson_ci_upper`) (verify CSV file exists and column headers match) [DEPENDS ON: T042, T045].
- [ ] T048 Unit test that validates CSV values exactly match JSON‑derived aggregates (tests/unit/test_report_generator.py) (verify test passes) [DEPENDS ON: T046].
- [ ] T049 Add Quickstart guide `docs/README_QUICKSTART.md` covering execution on 30 URLs within 30 minutes (FR‑028) **and include novice‑user verification step with written confirmation log** (see T095b) (verify guide file exists and includes novice verification instructions).
- [ ] T049b **[P]** Verify that the Quickstart execution in T049 actually runs on the default GitHub Actions runner (using `act` or CI) and records the runner environment. (depends on T049)
- [ ] T050 Implement subgroup prevalence and Fisher's exact‑test analysis (FR‑032) in `code/audit/subgroup_analysis.py` that produces `output/subgroup_report.json` with domain, year, counts, prevalence, and p‑value **and verify Bonferroni correction is applied** (constraint‑preservation‑925e1e46) (verify JSON file exists).
- [ ] T050b **[P]** Verify that the publication year is extracted for each summary and present in the input to `subgroup_analysis.py`. (depends on T050)
- [ ] T051 Unit tests for subgroup analysis covering groups with ≥ 10 summaries and verifying correct Fisher p‑values with Bonferroni correction (tests/unit/test_subgroup_analysis.py) (verify test passes).
- [ ] T052 Extend `report_generator.py` to also write the subgroup CSV `output/subgroup_report.csv` mirroring the JSON for easy inspection (verify CSV file exists) [DEPENDS ON: T046].
- [ ] T053 Integration test that runs the full pipeline on a mixed‑domain synthetic corpus and checks that subgroup report columns are present and correct (tests/integration/test_subgroup_report.py) (verify test passes).

### Tests for User Story 2 (OPTIONAL) ⚠️

- [ ] T054 US2 Contract test for prevalence calculations in `tests/contract/test_prevalence_schema.py` (run AFTER T042 completes) (verify schema compliance).
- [ ] T055 US2 Integration test that runs `code/audit/prevalence.py` on a known audit JSON and checks CSV columns (tests/integration/test_summary_generation.py) (run AFTER T042‑T046) (verify CSV columns exist).

---

## Phase 5: User Story 3 – Export Audit Results (Priority: P3)

**Goal**: Ensure audit artifacts are exported correctly and are mutually consistent.

**Independent Test**: Verify that `output/audit_report.json` and `output/summary_report.csv` exist and contain identical counts of consistent vs inconsistent entries.

### Implementation for User Story 3

- [ ] T056 Ensure driver script creates `output/manifest.json` with SHA256 hashes for all generated files (via `code/utils/manifest.py`) (FR‑024) **and invoke T096a to record these hashes in the state YAML** (see constraint‑preservation‑ac869b9f) (verify manifest exists and contains hashes).
- [ ] T057 Add schema validation step after audit generation to validate `audit_report.json` against `contracts/audit_record.schema.yaml` (FR‑026) (verify validation passes) [DEPENDS ON: T056].
- [ ] T058 Add schema validation step for `manifest.json` against `contracts/manifest.schema.yaml` (plan.md) (verify validation passes) [DEPENDS ON: T056].
- [ ] T059 Implement consistency checker in `code/audit/export_validator.py` that reads JSON and CSV, compares counts, and logs `ERR-201` if mismatch (plan.md) (verify no ERR‑201 logged) [DEPENDS ON: T056].
- [ ] T060 Unit test for export validator with deliberately mismatched files (tests/unit/test_export_validator.py) (verify test catches mismatch) [DEPENDS ON: T056].

### Tests for User Story 3 (OPTIONAL) ⚠️

- [ ] T030 Integration test that checks JSON ↔ CSV count consistency (tests/integration/test_export_consistency.py) (run AFTER T056‑T060) (verify counts match) [DEPENDS ON: T056].
- [ ] T061 Contract test for manifest schema in `tests/contract/test_manifest_schema.py` (run AFTER T056 completes) (verify schema compliance).

---

## Phase 6: User Story 4 – Efficient CI Execution (Priority: P2)

**Goal**: Guarantee that the full pipeline runs within GitHub Actions resource limits and logs usage.

**Independent Test**: Trigger the workflow on a sample corpus of a modest number of URLs and confirm successful completion, ≤ 2 GB RAM, ≤ 2 vCPU.

### Implementation for User Story 4

- [ ] T098 Add resource‑monitoring module `code/utils/resource_monitor.py` that records peak CPU & memory, writes to `output/resource_log.json` (SC‑008) **and aborts with `ERR-301` when limits exceeded per FR‑009** (verify log file exists, records within limits, and abort logic triggers on breach).
- [ ] T063 Modify `code/cli/run_audit.py` to invoke `resource_monitor` and abort with `ERR-301` if limits exceeded (plan.md) (run AFTER T098) (verify script aborts on limit breach) [DEPENDS ON: T098].
- [ ] T064 Update `.github/workflows/audit.yml` to include steps: (a) schema validation, (b) synthetic validation (ensure precision/recall thresholds), (c) resource‑monitor check, (d) main pipeline run (verify workflow runs all steps) [DEPENDS ON: T098].
- [ ] T065 Add CI step that caches `pip` packages to stay within 6 hour total runtime (plan.md) (verify cache hit on subsequent runs).
- [ ] T066 Add unit test for resource monitor parsing of `/proc` (tests/unit/test_resource_monitor.py) (verify test passes) [DEPENDS ON: T098].
- [ ] T095b Verify Quickstart Docker guide also reproduces environment via `requirements.txt` and isolated venv (Constitution Principle I) (verify Dockerfile runs `pip install -r requirements.txt` and that a venv is created) (addresses ordering‑28dea5aa).
- [ ] T095c **[P]** Verify that the CI run includes a step that checks all seven Constitution Principles (I‑VII) are satisfied (ties to PT005C) (verify CI step exists and passes). (depends on PT005C)

### Tests for User Story 4 (OPTIONAL) ⚠️

- [ ] T067 CI test that runs the workflow locally with `act` and asserts exit code 0 (tests/ci/test_ci_workflow.py) (verify exit code 0).

---

## Phase 7: Real‑World Validation (FR‑031b)

**Goal**: Create and evaluate the manually annotated real‑world validation set per FR‑031b and SC‑031b.

**Independent Test**: Compute extraction precision ≥ 85 % and recall ≥ 75 % (F1 ≥ 0.80) on the real‑world validation set.

- [ ] T069a Source ≥ 100 public A/B test summary URLs across five major domains (tech, e‑commerce, finance, healthcare, SaaS) with at least 20 per domain (constraint‑preservation‑0be190a4) (verify `data/manual_validation/source_urls.csv` exists and meets distribution).
- [ ] T069b Draft annotation protocol documenting field‑level extraction criteria, reviewer instructions, and conflict‑resolution process (document saved as `docs/annotation_protocol.md`).
- [ ] T069c Conduct manual annotation (human annotators) following protocol, resulting in `data/manual_validation/real_world_labels.csv` with two annotator columns and a resolved ground‑truth column (constraint‑preservation‑0be190a4) (verify file exists with ≥ 100 rows and required columns).
- [ ] T069d **[P]** Run `tests/unit/test_stratification_counts.py` to verify that `real_world_labels.csv` contains at least 20 annotated summaries per each of the five required domains. **DEPENDS ON:** T069c.
- [ ] T070 Evaluate **extraction accuracy component** on the real‑world validation set (FR‑031b) – compute precision, recall, F1 and assert precision ≥ 85 %, recall ≥ 75 %, F1 ≥ 0.80 (matches FR‑031b & SC‑031b) (uses `tests/integration/test_extraction_accuracy_realworld.py`) (verify test passes, otherwise raise `ERR-802`).
- [ ] T071 Verify SC‑031b: Real‑world validation precision ≥ 85 % and recall ≥ 75 % (run T070) (depends on T069c) [DEPENDS ON: T069c].

---

## Phase X: Success Criteria Verification

**Purpose**: Explicitly verify that every Success Criteria (SC‑*) is satisfied by the pipeline.

**⚠️ NOTE**: All Phase X tasks depend on completion of Phases 3‑7 implementation artifacts.

- [ ] T072 Verify SC‑001: Extraction accuracy ≥ 95 % on `data/manual_validation/real_world_labels.csv` (run `tests/integration/test_extractor_accuracy.py`) (depends on T020, T069c) (addresses ordering‑fef4baa0). **Note**: This is distinct from SC‑031b which uses a lower threshold.
- [ ] T073 Verify SC‑003: Monte‑Carlo vs library difference ≤ 0.005 for each statistical test (run `code/audit/monte_carlo_validation.py`) (depends on T062) (addresses ordering‑326c451a).
- [ ] T074 Verify SC‑005: Parsing‑error rate ≤ 5 % (run `code/audit/validator.py` and check log summary) (depends on T020) (addresses ordering‑fb2f11e6).
- [ ] T075 Verify SC‑008: CI execution completes within 6 h, ≤ 2 GB RAM, ≤ 2 vCPU (inspect `output/resource_log.json`) (depends on T098) (addresses ordering‑6e28c95b).
- [ ] T076 Verify SC‑013: CI pipeline exits with status 0 and produces `manifest.json` in ≥ 99 % of runs (run CI locally and check); compute checksums for ALL files under `data/` (raw, processed) AND `output/` directories and record them in `data/checksums.txt` per Constitution Principle III and Principle IV (Single Source of Truth) (verify `data/checksums.txt` exists with SHA256 hashes) (depends on T056, T095c, T095a) (addresses ordering‑cfade9e1 and constraint‑preservation‑d467869d).
- [ ] T077 Verify SC‑014: Binomial test output meets formatting and CI width ≤ 0.10 (run `code/audit/prevalence.py` and inspect JSON) (depends on T042) (addresses ordering‑fb2f11e6).
- [ ] T078 Verify SC‑015: Sensitivity analysis variation < 0.02 across baseline range (run `code/audit/prevalence.py` and inspect results) (depends on T042) (addresses ordering‑fb2f11e6).
- [ ] T079 Verify SC‑024: `summary_report.csv` columns and values match `audit_report.json` (run `tests/integration/test_summary_consistency.py`) (depends on T046) (addresses ordering‑fb2f11e6).
- [ ] T080 Verify SC‑025: Audited corpus size N ≥ 300 (check `output/power_analysis.json`) (depends on T028) (addresses ordering‑fb2f11e6).
- [ ] T081 Verify SC‑026: Monte‑Carlo validation passes for all tests (same as T073) (depends on T062) (addresses ordering‑326c451a).
- [ ] T082 Verify SC‑027: No domain exceeds a substantial proportion. and bias‑adjusted rate reported (run `code/audit/bias_adjustment.py` and inspect output) (depends on T045) (addresses ordering‑fb2f11e6).
- [ ] T083 Verify SC‑028: Quickstart guide enables audit of 30 URLs in ≤ 30 minutes on **default GitHub Actions runner** **and** novice‑user verification (time execution of Quickstart script and verify written confirmation log AND novice‑user verification step **and record the runner environment to confirm it is the default GitHub Actions runner**) (depends on T049, T095b) (addresses ordering‑28dea5aa).
- [ ] T084 Verify SC‑030: Synthetic validation precision ≥ 90 % and recall ≥ 80 % (run T029) (depends on T026) (addresses ordering‑fef4baa0).
- [ ] T085 Verify SC‑031b: Real‑world validation precision ≥ 85 % and recall ≥ 75 % (run T070) (depends on T070) (addresses ordering‑fef4baa0).
- [ ] T086 Verify SC‑032: Subgroup analysis produces Fisher's exact test results for groups ≥ 10 (run `code/audit/subgroup_analysis.py` and check JSON) (depends on T050) (addresses ordering‑fb2f11e6).
- [ ] T087 Verify overall pipeline passes all above SC checks without errors (run full suite) (depends on T072‑T086) (addresses ordering‑fb2f11e6).
- [ ] T096 **[P]** Verify that `data/checksums.txt` (generated by T076) matches the hashes listed in `output/manifest.json` and that all artifacts are accounted for (Constitution Principle IV: Single Source of Truth). (depends on T056 and T076) (addresses constraint‑preservation‑ac869b9f).
- [ ] T096a Update `state/projects/PROJ-492-evaluating-the-statistical-validity-of-p.yaml` `artifact_hashes` map with the checksums from `data/checksums.txt` (fulfills Constitution Principle III) (depends on T076) (addresses coverage‑d467869d).
- [ ] T096c Verify that the `data/checksums.txt` entries match the `state/projects/PROJ-492-evaluating-the-statistical-validity-of-p.yaml` `artifact_hashes` map (Constitution Principle III verification) (depends on T076, T096a) (addresses coverage‑d467869d).
- [ ] T097a Update `state/projects/PROJ-492-evaluating-the-statistical-validity-of-p.yaml` `updated_at` timestamp after any artifact change (fulfills Constitution Principle V) (depends on any preceding artifact‑modifying task) (addresses coverage‑a6ef6a7b).
- [ ] T097b Verify that the CI run includes a step that checks all seven Constitution Principles (I‑VII) are satisfied (ties to PT005C / PT005C) (addresses coverage‑57fe6cbc).

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T088 Documentation updates in `docs/` – expand API reference, data‑model description, and troubleshooting guide (verify docs build without errors).
- [ ] T089 Code cleanup: add type hints throughout `code/` , run `mypy --strict` (verify no type errors).
- [ ] T090 Performance optimization: replace in‑memory DataFrame joins with chunked processing in `code/audit/prevalence.py` to keep RAM ≤ 1.5 GB for large corpora (SC‑008) (verify memory usage).
- [ ] T091 Add additional edge‑case unit tests (missing metric, conflicting sample sizes, dead URLs) in `tests/unit/` (verify all pass).
- [ ] T092 Add additional edge‑case unit tests for subgroup analysis (missing domain, year, Fisher edge cases) in `tests/unit/` (verify all pass).
- [ ] T093 Run full benchmark on 5 000 synthetic URLs; record wall‑clock time in `output/benchmark.log` and ensure ≤ 6 hours (SC‑008) (verify log).
- [ ] T094 Release version tag `v0.1.0` and update `CHANGELOG.md` with released features (verify tag exists).
- [ ] T095 Implement documentation DOC001: Error codes reference guide in `docs/error_codes.md` (FR‑007) (verify doc exists and covers all ERR‑### codes).
- [ ] T096b Implement documentation DOC002: Statistical methodology reference in `docs/statistical_methodology.md` (FR‑003, FR‑026) (verify doc exists and covers z‑test, Fisher, Monte‑Carlo).
- [ ] T097b Implement documentation DOC003: Data provenance guide in `docs/data_provenance.md` (Constitution Principle VII) (verify doc exists and covers URL tracking, checksums, manifest).
- [ ] T099 Implement governance invalidation mechanism in `code/utils/governance.py` (Constitution Principle V) **and** update `state/projects/PROJ-492-evaluating-the-statistical-validity-of-p.yaml` `updated_at` timestamp via T097a (addresses constraint‑preservation‑a5829d58) (verify code executes and doc exists).
- [ ] T099b Verify that any artifact change triggers the `updated_at` timestamp update (see T097a) (addresses constraint‑preservation‑a5829d58).
- [ ] T100a **[P]** Run Reference‑Validator Agent after each artifact write (e.g., after manifest generation, after checksum file creation) to ensure citations are reachable and title‑overlap ≥ 0.7; log results. (addresses Constitution checkpoint 1).
- [ ] T100b **[P]** Run Reference‑Validator Agent before Advancement‑Evaluator gate to re‑validate all citations; abort if any fail. (addresses Constitution checkpoint 2).
- [ ] T100c **[P]** Run Reference‑Validator Agent at the research_review → research_accepted transition; ensure all citations pass before final acceptance. (addresses Constitution checkpoint 3).
- [ ] T101 Implement documentation DOC004: Governance policy in `docs/governance_policy.md` (verify existence).
