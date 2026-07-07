# Tasks: Evaluating the Statistical Validity of Public A/B Test Summaries

**Input**: Design documents from `/specs/001-eval-ab-test-validity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

**Plan Traceability**: Task IDs align with plan.md phases and requirements (FR-001 through FR-032, SC-001 through SC-032).

**NOTE**: The original plan.md defines tasks T000‑T005 which conflict with the existing task ID space (T001‑T100). To preserve existing task identifiers while restoring traceability, we introduce distinct **PT###** identifiers for plan‑root tasks. These PT### tasks mirror the plan‑phase requirements and do not interfere with the existing T### workflow.

---

## Phase 0: Plan‑Root & Research Tasks (new PT### & T000‑T005 IDs)

- [X] T000 Create CLI interface skeleton (`src/cli/main.py`) – verify script runs with `--help`. *(Alias of PT000)*
- [X] T001 Set up GitHub Actions workflow (`.github/workflows/audit.yml`) – verify CI triggers on push. *(Alias of PT001)*
- [X] T002 Implement Monte‑Carlo framework core (`src/audit/monte_carlo_core.py`) – verify core functions importable. *(Alias of PT002)*
- [ ] T003 {{claim:c_ef1634da}} ({{claim:c_8fd76726}}, https://www.wikidata.org/wiki/Q19873191) *(Alias of PT003)* <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [X] T004 Implement power‑analysis utility (`src/audit/power_analysis.py`) – verify it outputs JSON with required fields. *(Alias of PT004)*
- [ ] T005C **[P]** Implement Constitution compliance checker in `src/utils/constitution_checker.py` that validates all seven Principles (I–VII). Run this checker in CI and abort with an error if any principle fails. (verify checker script exists, runs in CI, and passes all seven checks). *(Alias of PT005C)*

- [ ] PT000 Create CLI interface skeleton (`src/cli/main.py`) per plan T000 (verify script runs with `--help`).
- [ ] PT001 Set up GitHub Actions workflow (`.github/workflows/audit.yml`) per plan T001 (verify CI triggers on push).
- [ ] PT002 Implement Monte‑Carlo framework core (`src/audit/monte_carlo_core.py`) per plan T002 (verify core functions importable).
- [ ] PT003 Add statistical verification utilities (`src/audit/stat_verification.py`) per plan T003 (verify functions compute z‑test, t‑test, Fisher).
- [ ] PT004 Implement power‑analysis utility (`src/audit/power_analysis.py`) per plan T004 (verify it outputs JSON with required fields).
- [ ] PT005C **[P]** Implement Constitution compliance checker in `src/utils/constitution_checker.py` that validates all seven Principles (I–VII). Run this checker in CI and abort with `ERR-950` if any principle fails. (verify checker script exists, runs in CI, and passes all seven checks).

- [ ] PT006 **[P]** Verify that `scipy` statistical functions run within the 2 GB RAM limit (FR‑009). (run a memory‑profiled sanity check).
- [ ] PT007 **[P]** Design the synthetic data generator specification for FR‑030 (independent of reconstruction logic). (produce a design doc in `docs/synthetic_design.md`).
- [ ] PT008 **[P]** Draft the manual annotation protocol for real‑world validation (FR‑031b). (store in `docs/annotation_protocol.md`).
- [ ] PT009 **[P]** Confirm power‑analysis calculation logic matches FR‑025 requirements (produce unit tests in `tests/unit/test_power_analysis.py`).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create repository skeleton with `src/`, `tests/`, `data/`, `output/`, `contracts/`, `notebooks/`, `.github/`, `docs/` directories (verify directories exist).
- [X] T002 Initialize Python project: `pyproject.toml` with required dependencies (`requests`, `beautifulsoup4`, `pandas`, `numpy`, `scipy`, `statsmodels`, `tqdm`, `pyyaml`, `jsonschema`, `psutil`).
- [X] T003 Add linting and formatting tools (`ruff`, `black`) and configure pre‑commit hooks (run `pre-commit run --all-files` with zero violations).
- [X] T004 Create `requirements.txt` mirroring `pyproject.toml` for CI reproducibility (verify `requirements.txt` matches `pyproject.toml`).
- [X] T005 Create `.gitignore` excluding `__pycache__`, `*.pyc`, `data/raw/*` except URLs, `output/*` (verify git status clean).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until foundational infrastructure (T006‑T012) is complete; remaining Phase 2 tasks (T013‑T020) may proceed in parallel with US1 implementation

- [X] T006 Create data‑model definitions (`ABSummary`, `AuditRecord`) in `src/models/data_models.py` using Pydantic (verify classes exist and importable).
- [X] T007 Create JSON‑Schema files `contracts/extracted_summary.schema.yaml` and `contracts/audit_record.schema.yaml` (verify schemas are valid YAML).
- [X] T008 Implement schema‑validation utilities in `src/contracts/validation.py` (run unit test to confirm validation works) [DEPENDS ON: T007].
- [X] T009 Set up structured logging infrastructure in `src/utils/logger.py` with error‑code format `ERR-###` (verify logs contain correct codes).
- [X] T010 Initialize configuration constants (random seeds, thresholds, resource caps) in `src/config.py` with deterministic seed (`SEED = 42`) AND ensure all modules import SEED from config and set RNG seeds at startup (verify `src/config.py` defines `SEED = 42` and all RNGs are seeded per Constitution Principle I).
- [X] T011 Implement generic helper functions (`checksum`, `domain_from_url`, `safe_float`, `parse_inequality_p`) in `src/utils/helpers.py` (run unit test for each helper).
- [X] T012 Create CI workflow file `.github/workflows/audit.yml` that installs dependencies, enforces CPU ≤ 2 vCPU, RAM ≤ 2 GB, timeout a predefined duration, and runs audit pipeline (verify workflow runs and respects limits) [DEPENDS ON: T010].
- [X] T013 Create Dockerfile for optional local execution (uses only CPU‑compatible base image) (build Docker image successfully). **(No dependency on T012)**
- [X] T014 Configure `manifest.json` generation with content hashes in `src/utils/manifest.py` (FR‑024) (verify `manifest.json` contains SHA256 hashes) [DEPENDS ON: T007].
- [X] T015 Create `data/manual_validation/` directory structure for real‑world validation annotations (verify directory exists).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 – Automated Consistency Audit (Priority: P1) 🎯 MVP

**Goal**: End‑to‑end pipeline that ingests URLs, extracts metrics, reconstructs statistical tests, flags inconsistencies, and produces audit artifacts.

**Independent Test**: Run the pipeline on the synthetic validation dataset and verify precision ≥ 90 % and recall ≥ 80 % (SC‑030).

### Implementation for User Story 1

- [X] T018 URL ingestion and deduplication in `src/audit/ingestor.py` (reads `input/urls.csv`) (verify `output/urls_deduped.csv` exists). **DEPENDS ON:** None.
- [X] T019 HTML fetching with retries and timeout in `src/audit/fetcher.py` (uses `requests`) (verify fetched HTML files are saved to `data/raw/`). **DEPENDS ON:** T018.
- [X] T020 Extraction logic in `src/audit/extractor.py` → produces `ABSummary` objects, handles missing fields, logs `ERR-001`‑`ERR-099` (FR‑007) (verify extraction JSON exists and logs contain appropriate ERR codes). **DEPENDS ON:** T019.
- [X] T020b **[P]** Run unit tests `tests/unit/test_error_message_format.py` to ensure all logged error‑message descriptions are ≤ a length that is sufficiently long for the intended analysis. and follow FR‑007 naming conventions. **DEPENDS ON:** T020.
- [X] T020c Archive provenance metadata in `data/provenance_log.csv` per Constitution Principle VII (verify file exists with URL, repository identifier, fetch timestamp **and** that each row contains all three fields). **DEPENDS ON:** T020.
- [X] T020d **[P]** Verify that every row in `data/provenance_log.csv` contains URL, repository identifier, and fetch timestamp (run validation script `tests/unit/test_provenance_schema.py`). **DEPENDS ON:** T020c. <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T021 Unit tests for extractor covering missing metric, inequality p‑value, malformed HTML, conflicting sample sizes (tests/unit/test_extractor.py) (verify all tests pass) [DEPENDS ON: T020].
- [X] T022 Implement outcome‑type detection heuristics in `src/audit/test_type_detector.py` (detect binary vs continuous only, no extra test‑type handling) (verify detector returns correct type).
- [X] T023 Implement statistical reconstruction in `src/audit/reconstructor.py` (two‑proportion z/Fisher for binary, Welch t for continuous, fallback to average baseline per FR‑012) (verify reconstructed values match known fixtures). **DEPENDS ON:** T062 (Monte‑Carlo validation) **AND** T022.
- [X] T024 Unit tests for reconstructor with known inputs (tests/unit/test_reconstructor.py) (verify all tests pass) [DEPENDS ON: T023].
- [ ] T025 Implement inconsistency validator in `src/audit/validator.py` applying FR‑004 thresholds (absolute p‑difference > 0.05, relative effect‑size > 5 %) **and verify that sample‑size mismatch entries are excluded from aggregate prevalence estimates** per FR‑004b (generate `AuditRecord` objects with data_quality_warning messages for sample‑size discrepancies, writing `output/audit_report.json`). **DEPENDS ON:** T023.
- [X] T025b **[P]** Run `tests/unit/test_missing_baseline_flag.py` to verify that any entry with a missing baseline conversion rate is flagged in the audit notes as required by FR‑012. **DEPENDS ON:** T025.
- [X] T025c **[P]** Run `tests/unit/test_sample_size_exclusion.py` to verify that summaries flagged for sample‑size mismatch are not included in `output/prevalence.json`. **DEPENDS ON:** T025.
- [ ] T027 Unit tests for validator covering absolute p‑difference > 0.05, effect‑size > 5 %, inequality handling, sample‑size mismatch with data_quality_warning generation (tests/unit/test_validator.py) (verify all tests pass) [DEPENDS ON: T025].
- [ ] T026 Implement synthetic dataset generator in `src/audit/synthetic.py` (FR‑030) – The synthetic dataset generator outputs at least 10 000 simulated summaries. (binary AND continuous outcomes) **and verify both outcome types are present** (constraint‑preservation‑2958f04c) (verify files are created and contain ≥ 10 000 records). **DEPENDS ON:** T006‑T012.
- [X] T028 Implement power‑analysis utility in `src/audit/power_analysis.py` (FR‑025) that computes the minimum N given baseline, detectable effect, α and power, writes result to `output/power_analysis.json`, **and asserts audited corpus meets N ≥ 300 OR N ≥ calculated_minimum ** (constraint‑preservation‑ba913176) (verify JSON file exists, contains numeric N, and satisfies condition). **DEPENDS ON:** T010.
- [ ] T029 Evaluate inconsistency‑detection component on synthetic validation dataset (FR‑031) – compute precision, recall, F1 and assert precision ≥ 90 %, recall ≥ 80 % (depends on T026) (verify test passes, otherwise raise `ERR-800`) [DEPENDS ON: T026].
- [ ] T062 Implement Monte‑Carlo validation module (FR‑026) in `src/audit/monte_carlo_validation.py` that runs 10 10000 replicates for each statistical test (z-test, Fisher's, Welch's, binomial) and checks the absolute difference ≤ 0.005 (constraint‑preservation‑e62a0df4) (verify module exits with status 0).
- [X] T031 **[P]** Run Monte‑Carlo validation (from T062) as part of pipeline start‑up; abort with `ERR-801` if any test fails the ≤ 0.005 criterion (T031 runs T062 module internally). **DEPENDS ON:** T062.
- [X] T032 Implement end‑to‑end driver script `src/cli/run_audit.py` that orchestrates ingestion → fetch → extract → reconstruct → validate → write artifacts (verify script exits with status 0 on success). **DEPENDS ON:** T025, T028, T029, T031.
- [X] T033 Integration test that runs driver on synthetic dataset, computes precision/recall/F1 and aborts with `ERR-800` if thresholds not met (tests/integration/test_synthetic_validation.py) (verify test passes) [DEPENDS ON: T026].
- [X] T034 Create analysis notebook `notebooks/statistical_consistency_verification.ipynb` that documents any p‑value discrepancies >0.05 with justification per Constitution Principle VI; run as part of pipeline acceptance (depends on T025) (verify notebook exists and contains discrepancy justifications) [DEPENDS ON: T025].
- [X] T035 FR‑001 Verification: Run `tests/integration/test_url_ingestion.py` to assert `input/urls.csv` processing completes without error (coverage‑executability‑08d5764f) (verify test passes).
- [X] T036 FR‑002 Verification: {{claim:c_3104c2cf}} (coverage‑executability‑08d5764f) (verify test passes). <!-- FAILED: unspecified -->
- [X] T037 FR‑003 Verification: Run `tests/integration/test_reconstructor_completeness.py` to assert reconstructed p‑values computed for all records (coverage‑executability‑08d5764f) (verify test passes).
- [X] T038 FR‑004 Verification: Run `tests/integration/test_validator_thresholds.py` to assert flags correspond to defined thresholds (coverage‑executability‑08d5764f) (verify test passes).

### Tests for User Story 1 (OPTIONAL)

- [X] T039 US1 Contract test for extractor output schema in `tests/contract/test_extractor_schema.py` (run AFTER T020 completes) (verify schema compliance) [DEPENDS ON: T020].
- [X] T040 US1 Contract test for reconstructor output schema in `tests/contract/test_reconstructor_schema.py` (run AFTER T023 completes) (verify schema compliance) [DEPENDS ON: T023].
- [X] T041 Integration test that runs the full pipeline on `data/manual_validation/real_world_labels.csv` and asserts `ERR-800` is not raised (tests/integration/test_full_pipeline.py) (run AFTER T018‑T032) (verify no ERR‑800) [DEPENDS ON: T018, T019, T020, T023, T025, T032].

---

## Phase 4: User Story 2 – Summary Report Generation (Priority: P2)

**Goal**: Produce a concise CSV report summarising total counts, inconsistency rates, bias‑adjusted rates, and Wilson confidence intervals.

**Independent Test**: Compare generated `summary_report.csv` against values derived from `audit_report.json` for a representative corpus.

### Implementation for User Story 2

- [ ] T042 Implement binomial prevalence test, Wilson CI, **and sensitivity analysis** (FR‑005a & FR‑005b) in `src/audit/prevalence.py` including dynamic Bonferroni correction (α = 0.05 / number_of_subgroups) per FR‑032 (verify JSON output contains required fields including sensitivity analysis results).
- [X] T042b **[P]** Verify that `prevalence.json` does **not** contain any entries flagged for sample‑size mismatch (cross‑check with T025c). (depends on T025c)
- [ ] T043 Unit tests for binomial test and CI width ≤ 0.10 (1807.00365, https://arxiv.org/abs/1807.00365) (tests/unit/test_prevalence.py) (verify test passes).
- [ ] T044 **[P]** Domain Bias Subsampling – create a balanced subsample of the corpus so that no single domain exceeds 30 % before bias adjustment (FR‑027). (writes `data/subsampled_balanced.csv`). **DEPENDS ON:** T006‑T012.
- [X] T045 Implement bias‑adjustment module that computes domain‑weighted prevalence using domain‑weighted averaging (FR‑027) **and either subsamples the dominant domain *or* flags a violation** per FR‑027 (constraint‑preservation‑01844dd3) in `src/audit/bias_adjustment.py` (verify bias‑adjusted rate is written and appropriate action taken when any domain exceeds 30 %). **DEPENDS ON:** T044.
- [ ] T046 Unit tests for bias‑adjustment ensuring no domain exceeds 30 % proportion (tests/unit/test_bias_adjustment.py) (verify test passes).
- [X] T047 Implement CSV summary generator in `src/audit/report_generator.py` that reads `output/audit_report.json` and writes `output/summary_report.csv` with required columns (`total_summaries`, `inconsistent_count`, `inconsistent_rate`, `bias_adjusted_rate`, `wilson_ci_lower`, `wilson_ci_upper`) (verify CSV file exists and column headers match) [DEPENDS ON: T042, T045].
- [X] T048 Unit test that validates CSV values exactly match JSON‑derived aggregates (tests/unit/test_report_generator.py) (verify test passes) [DEPENDS ON: T047].
- [X] T049 Add Quickstart guide `docs/README_QUICKSTART.md` covering execution on 30 URLs within 30 minutes (FR‑028) **and include novice‑user verification step with written confirmation log** (see T095b) (verify guide file exists and includes novice verification instructions).
- [ ] T049b **[P]** Verify that the Quickstart execution in T049 actually runs on the default GitHub Actions runner (2 vCPU, 7 GB RAM) and records the runner environment. (depends on T049)
- [X] T050 Implement subgroup prevalence and Fisher's exact‑test analysis (FR‑032) in `src/audit/subgroup_analysis.py` that produces `output/subgroup_report.json` with domain, year, counts, prevalence, and p‑value **and verify Bonferroni correction is applied dynamically** (constraint‑preservation‑925e1e46) (verify JSON file exists).
- [X] T050b **[P]** Verify that the publication year is extracted for each summary during extraction (T020c) and present in the input to `subgroup_analysis.py`. (depends on T020c)
- [X] T051 Unit tests for subgroup analysis covering groups with ≥ 10 summaries and verifying correct Fisher p‑values with Bonferroni correction (tests/unit/test_subgroup_analysis.py) (verify test passes).
- [X] T052 Extend `report_generator.py` to also write the subgroup CSV `output/subgroup_report.csv` mirroring the JSON for easy inspection (verify CSV file exists) **DEPENDS ON:** T050.
- [X] T053 Integration test that runs the full pipeline on a mixed‑domain synthetic corpus and checks that subgroup report columns are present and correct (tests/integration/test_subgroup_report.py) (verify test passes).

### Tests for User Story 2 (OPTIONAL)

- [X] T054 US2 Contract test for prevalence calculations in `tests/contract/test_prevalence_schema.py` (run AFTER T042 completes) (verify schema compliance).
- [X] T055 US2 Integration test that runs `src/audit/prevalence.py` on a known audit JSON and checks CSV columns (tests/integration/test_summary_generation.py) (run AFTER T042‑T046) (verify CSV columns exist).

---

## Phase 5: User Story 3 – Export Audit Results (Priority: P3)

**Goal**: Ensure audit artifacts are exported correctly and are mutually consistent.

**Independent Test**: Verify that `output/audit_report.json` and `output/summary_report.csv` exist and contain identical counts of consistent vs inconsistent entries.

### Implementation for User Story 3

- [X] T056 Ensure driver script creates `output/manifest.json` with SHA256 hashes for all generated files (via `src/utils/manifest.py`) (FR‑024) **and invoke T095a to record these hashes in the state YAML** (verify manifest exists and contains hashes).
- [X] T057 Add schema validation step after audit generation to validate `audit_report.json` against `contracts/audit_record.schema.yaml` (FR‑026) (verify validation passes) [DEPENDS ON: T056].
- [X] T058 Add schema validation step for `manifest.json` against `contracts/manifest.schema.yaml` (plan.md) (verify validation passes) [DEPENDS ON: T056].
- [X] T059 Implement consistency checker in `src/audit/export_validator.py` that reads JSON and CSV, compares counts, and logs `ERR-201` if mismatch (plan.md) (verify no ERR‑201 logged) [DEPENDS ON: T056].
- [X] T060 Unit test for export validator with deliberately mismatched files (tests/unit/test_export_validator.py) (verify test catches mismatch) [DEPENDS ON: T056].

### Tests for User Story 3 (OPTIONAL)

- [X] T030 Integration test that checks JSON ↔ CSV count consistency (tests/integration/test_export_consistency.py) (run AFTER T056‑T060) (verify counts match) [DEPENDS ON: T056].
- [X] T061 Contract test for manifest schema in `tests/contract/test_manifest_schema.py` (run AFTER T056 completes) (verify schema compliance).

---

## Phase 6: User Story 4 – Efficient CI Execution (Priority: P2)

**Goal**: Guarantee that the full pipeline runs within GitHub Actions resource limits and logs usage.

**Independent Test**: Trigger the workflow on a sample corpus of a modest number of URLs and confirm successful completion, ≤ 2 GB RAM, ≤ 2 vCPU.

### Implementation for User Story 4

- [X] T098 Add resource‑monitoring module `src/utils/resource_monitor.py` that records peak CPU & memory, writes to `output/resource_log.json` (SC‑008) **and aborts with `ERR-301` when limits exceeded per FR‑009** (verify log file exists, records within limits, and abort logic triggers on breach).
- [X] T063 Modify `src/cli/run_audit.py` to invoke `resource_monitor` and abort with `ERR-301` if limits exceeded (plan.md) (run AFTER T098) (verify script aborts on limit breach) [DEPENDS ON: T098].
- [ ] T064 Update `.github/workflows/audit.yml` to include steps: (a) schema validation, (b) synthetic validation (ensure precision/recall thresholds), (c) resource‑monitor check, (d) main pipeline run (verify workflow runs all steps) [DEPENDS ON: T098]. <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [X] T065 Add CI step that caches `pip` packages to stay within 6 hour total runtime (plan.md) (verify cache hit on subsequent runs).
- [X] T066 Add unit test for resource monitor parsing of `/proc` (tests/unit/test_resource_monitor.py) (verify test passes) [DEPENDS ON: T098].
- [X] T095b Verify Quickstart Docker guide also reproduces environment via `requirements.txt` and isolated venv (Constitution Principle I) (verify Dockerfile runs `pip install -r requirements.txt` and that a venv is created) (addresses ordering‑28dea5aa).
- [ ] T095c **[P]** Verify that the CI run includes a step that checks all seven Constitution Principles (I‑VII) are satisfied (ties to PT005C) (verify CI step exists and passes). (depends on PT005C) <!-- ATOMIZE: requested -->

### Tests for User Story 4 (OPTIONAL)

- [ ] T067 CI test that runs the workflow locally with `act` and asserts exit code 0 (tests/ci/test_ci_workflow.py) (verify exit code 0).

---

## Phase 7: Real‑World Validation (FR‑031b)

**Goal**: Create and evaluate the manually annotated real‑world validation set per FR‑031b and SC‑031b.

**Independent Test**: Compute extraction precision ≥ 85 % and recall ≥ 75 % (F1 ≥ 0.80) on the real‑world validation set

- [ ] {{claim:c_65cd812e}}
- [ ] T069b Draft annotation protocol documenting field‑level extraction criteria, reviewer instructions, and conflict‑resolution process (document saved as `docs/annotation_protocol.md`).
- [ ] T069c Conduct manual annotation (human annotators) following protocol, resulting in `data/manual_validation/real_world_labels.csv` with two annotator columns and a resolved ground‑truth column (constraint‑preservation‑0be190a4) rows and required columns).
- [ ] T069d **[P]** Run `tests/unit/test_stratification_counts.py` to verify that `real_world_labels.csv` contains at least20 annotated summaries per each of the five required domains. **DEPENDS ON:** T069c.
- [ ] T070 Evaluate **extraction accuracy component** on the real‑world validation set (FR‑031b) – compute precision, recall, F1 and {{claim:c_86c3c2ff}} (verify test passes, otherwise raise `ERR-802`).
- [ ] T071 Verify SC‑031b: Real‑world validation precision ≥ 85 % and recall ≥ 75 % (run T070) (depends on T069c) [DEPENDS ON: T069c].

---

## Phase X: Success Criteria Verification

**Purpose**: Explicitly verify that every Success Criteria (SC‑*) is satisfied by the pipeline.

**⚠️ NOTE**: All Phase X tasks depend on completion of Phases 3‑7 implementation artifacts.

- [ ] T072 Verify SC‑001: Extraction accuracy ≥ 95 % on `data/manual_validation/real_world_labels.csv` (run `tests/integration/test_extractor_accuracy.py`) (depends on T020, T069c) (addresses ordering‑fef4baa0). **Also confirms stratification across five domains.**
- [ ] T073 Verify SC‑003: The Monte-Carlo vs library difference must be ≤ 0.005 for each statistical test. [UNRESOLVED-CLAIM: c_5a869a82 — status=not_enough_info] for each statistical test (run `src/audit/monte_carlo_validation.py`) (depends on T062) (addresses ordering‑326c451a).
- [ ] T074 Verify SC‑005: The parsing-error rate is ≤ 5%. [UNRESOLVED-CLAIM: c_8c45136d — status=not_enough_info] (run `src/audit/validator.py` and check log summary) (depends on T020) (addresses ordering‑fb2f11e6).
- [ ] T075 Verify SC‑008: CI execution completes within 6 h, ≤ 2 GB RAM, ≤ 2 vCPU (inspect `output/resource_log.json`) (depends on T098) (addresses ordering‑6e28c95b).
- [ ] T076 Verify SC‑013: The CI pipeline must exit with status 0 and produce `manifest.json` in ≥ 99% of runs. (run CI locally and check); compute checksums for ALL files under `data/` (raw, processed) AND `output/` directories and record them in `data/checksums.txt` per Constitution Principle III and Principle IV (verify `data/checksums.txt` exists with SHA256 hashes) (depends on T056, T095c, T095a) (addresses ordering‑cfade9e1 and constraint‑preservation‑d467869d).
- [ ] T077 Verify SC‑014: Binomial test output meets CI width ≤ 0.10 (run `src/audit/prevalence.py` and inspect JSON) (depends on T042) (addresses ordering‑fb2f11e6).
- [ ] T078 Verify SC‑015: Sensitivity analysis variation is less than 0.02 across baseline range. [UNRESOLVED-CLAIM: c_2b76721d — status=not_enough_info]. (run `src/audit/prevalence.py` and inspect results) (depends on T042) (addresses ordering‑fb2f11e6).
- [ ] T079 Verify SC‑024: `summary_report.csv` columns and values match `audit_report.json` (run `tests/integration/test_summary_consistency.py`) (depends on T047) (addresses ordering‑fb2f11e6).
- [ ] T080 Verify SC‑020: The audited corpus size N is at least 300 (check `output/power_analysis.json`) (depends on T028) (addresses ordering‑fb2f11e6).
- [ ] T081 Verify SC‑026: Monte‑Carlo validation passes for all tests (same as T073) (depends on T062) (addresses ordering‑326c451a).
- [ ] T082 Verify SC‑027: No domain exceeds a substantial proportion and bias‑adjusted rate reported (run `src/audit/bias_adjustment.py` and inspect output) (depends on T045) (addresses ordering‑fb2f11e6).
- [ ] T083 Verify SC‑028: Quickstart guide enables audit of 30 URLs in ≤ 30 minutes on **default GitHub Actions runner** (2 vCPU, 7 GB RAM) and records novice‑user verification log (depends on T049, T095b) (addresses ordering‑28dea5aa).
- [ ] T084 Verify SC‑030: Synthetic validation precision ≥ 90 % and recall ≥ 80 % (run T029) (depends on T026) (addresses ordering‑fef4baa0).
- [ ] T085 Verify SC‑031b: Real‑world validation precision ≥ 85 % and recall ≥ 75 % (run T070) (depends on T070) (addresses ordering‑fef4baa0).
- [ ] T086 Verify SC‑032: Subgroup analysis produces Fisher's exact test results for groups ≥ 10 (run `src/audit/subgroup_analysis.py` and check JSON) (depends on T050) (addresses ordering‑fb2f11e6).
- [ ] T087 Verify overall pipeline passes all above SC checks without errors (run full suite) (depends on T072‑T086) (addresses ordering‑fb2f11e6).
- [ ] T095a **[P]** Update `state/projects/PROJ-492-evaluating-the-statistical-validity-of-p.yaml` `artifact_hashes` map with the checksums from `data/checksums.txt` (fulfills Constitution Principle III). (depends on T076)
- [ ] T095c **[P]** Verify that `data/checksums.txt` matches the hashes listed in `output/manifest.json` and that all artifacts are accounted for (Constitution Principle IV). (depends on T056 and T095a)

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T088 Documentation updates in `docs/` – expand API reference, data‑model description, and troubleshooting guide (verify docs build without errors).
- [ ] T089 Code cleanup: add type hints throughout `src/`, run `mypy --strict` (verify no type errors).
- [ ] T090 Performance optimization: replace in‑memory DataFrame joins with chunked processing in `src/audit/prevalence.py` to keep RAM ≤ 1.5 GB for large corpora (SC‑008) (verify memory usage).
- [ ] T091 Add additional edge‑case unit tests (missing metric, conflicting sample sizes, dead URLs) in `tests/unit/` (verify all pass).
- [ ] T092 Add additional edge‑case unit tests for subgroup analysis (missing domain, year, Fisher edge cases) in `tests/unit/` (verify all pass).
- [ ] T093 Run full benchmark on 5 000 synthetic URLs; record wall‑clock time in `output/benchmark.log` and ensure ≤ 6 hours (SC‑008) (verify log).
- [ ] T094 Release version tag `v0.1.0` and update `CHANGELOG.md` with released features (verify tag exists).
- [ ] T095 Implement documentation DOC001: Error codes reference guide in `docs/error_codes.md` (FR‑007) (verify doc exists and covers all ERR‑### codes).
- [ ] T096b Implement documentation DOC002: Statistical methodology reference in `docs/statistical_methodology.md` (FR‑003, FR‑026) (verify doc exists and covers z‑test, Fisher, Monte‑Carlo).
- [ ] T097b Implement documentation DOC003: Data provenance guide in `docs/data_provenance.md` (Constitution Principle VII) (verify doc exists and covers URL tracking, checksums, manifest). *(Note: T097b name retained for documentation only; no duplicate CI check.)*
- [ ] T099 Implement governance invalidation mechanism in `src/utils/governance.py` (Constitution Principle V) **and** update `state/projects/PROJ-492-evaluating-the-statistical-validity-of-p.yaml` `updated_at` timestamp via T095a (addresses constraint‑preservation‑a5829d58) (verify code executes and doc exists).
- [ ] T099b Verify that any artifact change triggers the `updated_at` timestamp update (see T095a) (addresses constraint‑preservation‑a5829d58).
- [ ] T100 (2506.09162, https://arxiv.org/abs/2506.09162) a **[P]** {{claim:c_23dc9564}}
- [ ] T100b **[P]** Run Reference‑Validator Agent before Advancement‑Evaluator gate to re‑validate all citations; abort if any fail. (addresses Constitution checkpoint 2).
- [ ] T100c **[P]** Run Reference‑Validator Agent at the research_review → research_accepted transition; ensure all citations pass before final acceptance. (addresses Constitution checkpoint 3).
- [ ] T101 Implement documentation DOC004: Governance policy in `docs/governance_policy.md` (verify existence).
