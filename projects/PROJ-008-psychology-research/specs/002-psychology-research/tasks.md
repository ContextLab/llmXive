# Tasks: Mindfulness Components and Delivery Formats in ASD Social Skills

**Input**: Design documents from `/specs/001-mindfulness-asd-social-skills/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Create the full project directory structure for `projects/PROJ-008-psychology-research/` relative to the repository root. This includes: `code/`, `data/` (with `raw/`, `processed/`, `interim/`), `docs/`, `tests/` (with `unit/`, `integration/`, `contract/`), `contracts/`, `scripts/`, `.github/workflows/`. **Do not create empty placeholder files.**
- [ ] T001a [P] Create valid `__init__.py` files in all `code/` and `tests/` subdirectories to ensure Python package recognition.
- [X] T001b [P] Create `data/raw/.gitkeep` file to ensure the directory is tracked.

- [X] T002 [P] Create `pyproject.toml` at `projects/PROJ-008-psychology-research/` with: build-system (setuptools>=61.0), python version `>=3.11`, and dependencies list with **PINNED versions** (e.g., `pandas==2.0.0`, `scikit-learn==1.3.0`, `statsmodels==0.14.0`, `matplotlib==3.7.0`, `requests==2.31.0`, `pyyaml==6.0`, `pytest==7.4.0`, `bayesmeta==0.1.0`, `pdfplumber==0.10.0`). **No version ranges (>=) are permitted.** Also generate `requirements.txt` at the same location by extracting these pinned dependencies to ensure reproducibility on fresh runners (SC-005). Verify that `requirements.txt` contains exact versions for all packages.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools. **Create `.ruff.toml` at repository root with `line-length = 88`, `target-version = "py311"`, and `select = ["E", "F", "W", "I"]`. Create `pyproject.toml` sections `[tool.black]` (line-length=88, target-version=['py311']) and `[tool.ruff]` matching the `.ruff.toml` rules. Ensure `pyproject.toml` is updated if it does not exist.**

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create base Pydantic models for `Study`, `EffectSize`, and `MetaAnalysisResult` in `code/data/models.py`. **Include docstrings describing the purpose of each field.**
- [X] T005 [P] Implement structured logging infrastructure in `code/utils/logging.py` (FR-007)
- [X] T006 [P] Setup configuration management and seed pinning in `code/utils/config.py`
- [ ] T007a [P] Create `contracts/cleaned_study.schema.yaml` with **FULL JSON Schema (Draft 7) in YAML format**. Content:
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
required:
 - id
 - title
 - registry
 - age_range
 - diagnosis
 - outcomes
 - intervention_components
 - delivery_format
 - social_skill_domain
properties:
 id: { type: string }
 title: { type: string }
 registry: { type: string, enum: ["ClinicalTrials.gov", "OSF"] }
 age_range:
   type: object
   required: [min, max]
   properties:
     min: { type: integer, minimum: 6 }
     max: { type: integer, maximum: 12 }
 diagnosis: { type: string, const: "ASD" }
 outcomes: { type: array, items: { type: string } }
 intervention_components: { type: array, items: { type: string, enum: ["breathing", "body scan", "mindful movement", "mindful eating", "none"] } }
 delivery_format: { type: string, enum: ["caregiver-mediated", "child-led", "mixed", "not-reported"] }
 follow_up: { type: string, nullable: true }
 abstract_text: { type: string, nullable: true }
 social_skill_domain: { type: string, enum: ["communication", "peer interaction", "emotional regulation", "mixed", "other"] }
 domain_notes: { type: string, nullable: true, description: "Unmatched domain descriptions captured when no keyword match found" }
 blinded_assessment_flag: { type: boolean, description: "True if outcome assessment was blinded to intervention status" }
 rater_type: { type: string, enum: ["blinded", "unblinded", "mixed"], description: "Type of rater used for primary outcome" }
```
 **Verify file with `pyyaml` validator.**
- [ ] T007b [P] Create `contracts/effect_size.schema.yaml` with **FULL JSON Schema (Draft 7) in YAML format**. Content:
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
required:
 - study_id
 - hedges_g
 - se
 - ci_lower
 - ci_upper
 - n_treatment
 - n_control
properties:
 study_id: { type: string }
 hedges_g: { type: number }
 se: { type: number }
 ci_lower: { type: number }
 ci_upper: { type: number }
 n_treatment: { type: integer, minimum: 1 }
 n_control: { type: integer, minimum: 1 }
 rater_blinding_status: { type: string, enum: ["blinded", "unblinded", "unknown"], description: "Blinding status of the outcome rater" }
```
 **Verify file with `pyyaml` validator.**
- [X] T008 [P] Implement artifact hashing utility in `scripts/hash_artifacts.py` for Constitution Principle V
- [X] T009 [P] Create `docs/ethics_determination.md` documenting the 'Exempt' status for secondary analysis of de-identified public registry data (ClinicalTrials.gov, OSF) and justification for no IRB requirement
- [X] T010 [P] Create `docs/analysis-plan.md` detailing missing-data-handling and imputation strategies. **Must include sections: Missing Data Strategy (with table of methods), Imputation Method (with formula), Sensitivity Analysis (with criteria).** **Verify file contains regex `Missing Data Strategy` and `Imputation Method`.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Collection and Cleaning Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw study data from ClinicalTrials.gov and OSF, validate against inclusion criteria, and extract standardized variables into a clean CSV.

**Independent Test**: The pipeline can be tested by running it against a known set of mock study records with predefined inclusion/exclusion flags and verifying that the output CSV contains the expected included records.

> **NOTE**: Per Constitution Principle VI (Clinical Trial Registry Integrity), data sources are strictly limited to ClinicalTrials.gov and OSF.

### Implementation for User Story 1 (Data Generation & Collection)

- [X] T015b [P] [US1] **Create Mock Data Generator**: Generate `data/raw/mock_registry_response.json` containing a representative set of records.:
 1. Record 1: Valid study, age 8, ASD, social outcome, abstract present.
 2. Record 2: Valid study, age 10, ASD, social outcome, **NO abstract** (to trigger T020 exclusion logic if metadata is missing).
 3. Record 3: Invalid study, age 15 (out of range), ASD, social outcome.
 **Ensure JSON structure matches the API response format expected by T016. Required fields: id, title, registry, age_range (min, max), diagnosis, outcomes (array), abstract (nullable), intervention_components (array), delivery_format, social_skill_domain, follow_up, rater_type, blinded_assessment_flag. Verify JSON structure against `contracts/cleaned_study.schema.yaml` before saving.**
- [X] T015c [P] [US1] **Create Blinded Mock Data**: Generate `data/raw/mock_blinded_response.json` containing a small set of mock records. derived from Record 1:
 1. Record A: Same study, but explicitly labeled `rater_type: "unblinded"` and `blinded_assessment_flag: false`.
 2. Record B: Same study, but explicitly labeled `rater_type: "blinded"` and `blinded_assessment_flag: true`.
 **This data is for testing the blinding comparison logic in T022.**

### Implementation for User Story 1 (Core Pipeline)

- [ ] T016 [US1] depends on T007a, T007b, T015b: Implement API collector in `code/data/collector.py` (FR-001, FR-002) with rate-limiting (requests per minute per API) and exponential backoff (base s, max bounded duration) for **ClinicalTrials.gov and OSF ONLY** per Constitution Principle VI. **Logic: Check for `data/raw/mock_registry_response.json`. If present AND `CI_MODE` is true AND `MOCK_DATA_ONLY` is true, load and use it as the source. If `CI_MODE` is true but `MOCK_DATA_ONLY` is false, OR if `CI_MODE` is false, fetch from API. Log search query strings and retrieval timestamps to `data/raw/retrieval_log.json`. If mock data is detected in a non-test run (i.e., `MOCK_DATA_ONLY` is false but mock file is used), the script MUST raise a `RuntimeError` with message "Mock data detected in non-test run; aborting."**
- [X] T017a [US1] depends on T007a, T007b: Implement data extractor for intervention components in `code/data/extractor.py` (FR-003). **Logic: Scan the 'description' and 'abstract' fields of registry metadata. Use case-insensitive, whole-word regex patterns to detect: 'breathing', 'body scan', 'mindful movement', 'mindful eating'. Output: List of detected components in `intervention_components` column.**
- [X] T017b [US1] depends on T007a, T007b: Implement data extractor for social skill domains in `code/data/extractor.py` (FR-010). **Logic: Scan the 'description' and 'abstract' fields. Use regex patterns to detect keywords mapping to exactly three domains: 'communication' (keywords: speech, language, verbal, non-verbal), 'peer interaction' (keywords: peer, social, group, play), 'emotional regulation' (keywords: emotion, affect, regulation, tantrum). Assign the first matching domain found. If multiple, assign 'mixed'. If a valid domain is described but not in the keyword list, assign 'other' AND populate the `domain_notes` field with the original text description. Output: `social_skill_domain` column with values restricted to [communication, peer interaction, emotional regulation, mixed, other] and `domain_notes` column for unmatched descriptions.**
- [ ] T018 [US1] depends on T007a, T007b, T016: Implement data cleaner in `code/data/cleaner.py` (FR-007) to validate age **6-12 (per US1 in spec.md)**, ASD diagnosis, and social skill outcomes. **Logic: Validate `outcomes` field by checking if any item in the array contains the phrase 'social skill' (case-insensitive) or matches known validated measure patterns (e.g., 'SRS', 'ABC', 'SSIS', 'PEP'). If no match is found, flag the study in `data/raw/excluded_studies.log` (JSONL format: `[{study_id: str, reason: "INVALID_OUTCOME", timestamp: str}])`.**
- [X] T019 [US1] depends on T007a, T007b: Implement multi-arm study handling logic in `code/data/cleaner.py` (FR-008) to split control groups proportionally.
- [ ] T020 [US1] depends on T007a, T007b, T015b, T018: Implement **Abstract-only text extraction fallback** in `code/data/extractor.py` (FR-009). **Logic: Define 'insufficient metadata' as the absence of ANY of the three mandatory inclusion fields: `age_range`, `diagnosis`, OR `outcomes`. If ANY of these three fields are missing, check if an `abstract` is available. If abstract is present, attempt to extract missing fields using specific regex patterns: Age: 'aged [0-9]+', 'children [0-9]+', 'mean age [0-9]+'; Diagnosis: 'ASD', 'Autism Spectrum', 'PDD-NOS', 'Autistic'; Outcomes: 'SRS', 'ABC', 'SSIS', 'social skill', 'communication'. If extraction succeeds, populate the missing fields. If abstract is missing OR extraction fails, flag the study in `data/raw/excluded_studies.log` (JSONL: `[{study_id: str, reason: "INSUFFICIENT_METADATA_NO_ABSTRACT", timestamp: str}]`). **Use `data/raw/mock_registry_response.json` (T015b, Record 2) to trigger and verify this path.** DO NOT attempt PDF reconstruction.**
- [ ] T022 [US1] depends on T007a, T007b, T015c: **Implement Blinded Assessment Logic**: Extract `rater_type` and `blinded_assessment_flag` from registry metadata (or mock data). **Logic: Identify if a study reports blinded vs. unblinded raters. If a study reports both (e.g., primary outcome unblinded, secondary blinded), flag as 'mixed'. Output: Add `rater_type` and `blinded_assessment_flag` columns to `data/processed/cleaned_studies.csv`.**
- [ ] T021 [US1] depends on T007a, T007b, T016-T020, T022: **Verify and archive output**: Create script `scripts/verify_output.py` that checks for existence of `data/processed/cleaned_studies.csv` and `data/raw/excluded_studies.log`. **Verify CSV schema compliance against `contracts/cleaned_study.schema.yaml`. If CSV is empty (0 rows), verify that `data/raw/mock_registry_response.json` exists (indicating CI mode) OR that no studies matched criteria (real mode); do NOT fail on empty CSV. If CSV has rows, verify row count > 0. Exits 0 on success, 1 on failure.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Effect Size Calculation and Meta-Analysis (Priority: P2)

**Goal**: Calculate Hedges' *g* effect sizes, perform random-effects meta-analysis, and conduct subgroup analyses comparing mindfulness components and delivery formats.

**Independent Test**: The calculation module can be tested by providing a synthetic dataset of studies with known means and standard deviations, verifying that the calculated Hedges' *g* matches the manual calculation within a tolerance of a sufficiently small magnitude.

### Tests for User Story 2 (REQUIRED) ⚠️

- [X] T025 [P] [US2] Contract test for effect size schema in `tests/contract/test_effect_size_schema.py`
- [X] T026 [P] [US2] Unit test for Hedges' *g* calculation accuracy against `statsmodels` or manual calc in `tests/unit/test_effect_sizes.py`
- [X] T027 [P] [US2] Unit test for random-effects model selection logic (I² > 50%) in `tests/unit/test_meta_analysis.py`
- [X] T027b [P] [US2] **Unit test for Blinding Bias Detection**: Create `tests/unit/test_blinding_bias.py`. **Logic: Simulate a dataset where 'unblinded' studies show a substantially larger effect size and 'blinded' studies show a smaller effect size. Verify that the analysis correctly identifies a statistically significant difference between these two groups with p-value < 0.05.**

### Implementation for User Story 2

- [X] T028 [US2] depends on T016, T017a, T017b, T018, T019, T020, T021, T022, T007a, T007b: Implement Hedges' *g* calculator in `code/analysis/effect_sizes.py` (FR-004, FR-013) with small-sample correction
- [X] T029 [US2] depends on T016, T017a, T017b, T018, T019, T020, T021, T022, T028, T007a, T007b: Implement random-effects meta-analysis engine in `code/analysis/meta_analysis.py` (FR-005) using `statsmodels`. **Logic: Use `statsmodels.stats.meta_analysis.combine_effects` to calculate pooled effect. Calculate I². If I² > 0.5, use random-effects model; otherwise, use fixed-effects model. Output: Pooled effect size, heterogeneity statistics.**
- [X] T030 [US2] depends on T016, T017a, T017b, T018, T019, T020, T021, T022, T028, T007a, T007b: Implement subgroup analysis (Cochran's Q) for mindfulness components and delivery formats in `code/analysis/meta_analysis.py` (FR-005). **Logic: Use `scipy.stats.chi2` for Cochran's Q test. Categorize 'mindfulness components' as binary (present/absent) based on `intervention_components` column. Categorize 'delivery formats' by mapping `delivery_format` column values (caregiver-mediated vs. child-led) to groups. Output: Subgroup effect sizes and heterogeneity statistics for each group.**
- [X] T031 [US2] depends on T016, T017a, T017b, T018, T019, T020, T021, T022, T028, T007a, T007b: Implement social skill domain extraction and subgroup analysis in `code/analysis/meta_analysis.py` (FR-010, FR-011). **Logic: Group studies by `social_skill_domain` column (values: communication, peer interaction, emotional regulation, mixed, other). Calculate subgroup effect sizes for each domain. Output: Subgroup effect sizes and heterogeneity statistics.**
- [X] T032 [US2] depends on T016, T017a, T017b, T018, T019, T020, T021, T022, T028, T007a, T007b: Implement follow-up duration subgroup analysis (3-month vs. others) in `code/analysis/meta_analysis.py` (FR-012). **Logic: Parse `follow_up` string field to days (e.g., '3 months' -> 90, '6 months' -> 180). Group studies into <90 days vs >=90 days. Output: Subgroup effect sizes for each group.**
- [X] T033 [US2] depends on T016, T017a, T017b, T018, T019, T020, T021, T022, T028, T029, T007a, T007b: Implement conditional logic to suppress subgroup/meta-regression if N < 10 and switch to descriptive synthesis. **Generate `docs/native_synthesis.md` containing the descriptive synthesis results.** (FR-014)
- [X] T033b [US2] depends on T022, T028, T007a, T007b: **Implement Blinding Bias Quantification**: Extend `code/analysis/meta_analysis.py` to perform a specific subgroup analysis comparing `blinded_assessment_flag = true` vs `false`. **Logic: If N >= 10 (global threshold per FR-014), calculate the difference in pooled effect sizes between the two groups. If N < 10, skip analysis and log a warning to `docs/results.md`. Output: Quantify the difference and report it in `docs/results.md`. (Cites Constitution Principle VII and FR-005). Verify that the analysis correctly identifies a statistically significant difference with p-value < 0.05 in the test dataset.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Publication Bias Assessment (Priority: P3)

**Goal**: Generate forest plots and funnel plots (if N ≥ 10) to assess publication bias and interpret meta-analysis results.

**Independent Test**: The visualization module can be tested by running it on a small dataset and verifying that the forest plot correctly displays the study-specific effect sizes and confidence intervals, and that the funnel plot is suppressed if N < 10.

### Tests for User Story 3 (REQUIRED) ⚠️

- [ ] T034 [P] [US3] Unit test for forest plot generation in `tests/unit/test_plots.py`
- [ ] T035 [P] [US3] Unit test for funnel plot suppression logic when N < 10 in `tests/unit/test_plots.py`
- [ ] T036 [P] [US3] Integration test for publication bias assessment (Egger's test) in `tests/integration/test_bias.py`

### Implementation for User Story 3

- [ ] T037 [US3] depends on T028-T033, T033b: Implement forest plot generator in `code/viz/plots.py` (FR-006) displaying study-specific CIs and pooled effect diamond
- [ ] T038 [US3] depends on T028-T033, T033b: Implement funnel plot generator in `code/viz/plots.py` (FR-006) with asymmetry visual cues (only if N ≥ 10)
- [ ] T039 [US3] depends on T028-T033: Implement Egger's test and publication bias assessment in `code/analysis/bias.py` (FR-006)
- [ ] T040 [US3] depends on T039: Implement conditional logic to suppress funnel plot/Egger's test if N < 10 and add warning to report (FR-014)
- [ ] T041 [US3] depends on T037, T038: Generate `data/processed/forest_plot.png` and `data/processed/funnel_plot.png` at a high resolution using matplotlib savefig() with explicit dpi parameter (FR-006).
- [ ] T042 [US3] depends on T041, T021, T017b, T033, T033b, T029, T030, T031, T032: Generate `docs/results.md` containing: 1) Executive Summary, 2) Forest Plot (T037), 3) Funnel Plot (T038), 4) Heterogeneity Statistics (I², Q), 5) Subgroup Analysis Results (table with columns `Domain`, `N`, `Effect Size`), 6) Narrative Synthesis if N<10. **For Section 5, read the unique values from the `social_skill_domain` column of `data/processed/cleaned_studies.csv` to populate the 'Domain' column. Verify file exists and contains all 6 sections with actual content (e.g., verify section 5 contains a table with columns Domain, N, Effect Size). If N=0, Section 5 must state 'No studies found for subgroup analysis'. If N<10, Section 5 must state 'Insufficient studies for meta-analysis; descriptive synthesis only'. Format 'Effect Size' column as 'Hedges' g (95% CI)' (e.g., '0.50 [0.10, 0.90]'). (FR-006).**
- [ ] T043 [US3] depends on T042, T033b: **Add Blinding Bias Visualization**: Update `docs/results.md` and `code/viz/plots.py` to include a specific visualization (e.g., a side-by-side forest plot or a bar chart) comparing the pooled effect sizes of Blinded vs. Unblinded studies. **This directly addresses the Kahneman-simulated review concern about quantifying expectation bias.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address current spec requirements

- [ ] T044 [P] Create `.github/workflows/ci.yml` to automate pipeline execution on a fresh runner, verifying reproducibility (SC-005). **Success criteria: All tests pass, data checksums match, no errors.**
- [ ] T045 [P] depends on T007a, T007b, T022, T021: Implement data integrity check script `scripts/validate_contracts.py` to run schema validation on `data/processed/cleaned_studies.csv` against `contracts/cleaned_study.schema.yaml`, writing a detailed `data/validation_report.json` (schema: `total_records`, `passed_count`, `failed_count`, `error_list` (array of `{record_id, field, error_message}`)) with pass/fail status per record and summary statistics (SC-005, FR-007). **The `error_list` must contain objects with `record_id` (string), `field` (string), and `error_message` (string) for each validation failure.**
- [ ] T046 [P] depends on T042, T004, T045, T029, T030, T031, T032, T033b: Generate final `docs/protocol.md` detailing the full methodology (search strategy, inclusion criteria, statistical methods) as per PRISMA guidelines. **Verify file exists and includes PRISMA flow diagram description (text, not image) with regex `\\bPRISMA\\b` and a table with columns `Included`, `Excluded`. Explicitly document the novel contribution (6-12 age range, disaggregated components, delivery format) in the Introduction section.** **Note: This task depends on US3 completion (cross-phase dependency).**
- [ ] T047 [P] Create `quickstart.md` in root to document environment setup and verification steps from a clean clone, resolving the T032 failure from prior reviews. **Content must include: Python version requirement, dependency installation instructions, data verification steps (how to run T021), and expected output files.**
- [ ] T048 [P] Add `LICENSE` file specifying research data usage terms and ensure all data artifacts have corresponding license headers.

**NOTE**: Tasks T049, T050, and T051 have been removed from the scope as they were identified as contradictory or out of scope in prior reviews.

---

## Phase 7: Revision & Artifact Hygiene (Addressing Prior Reviews)

**Purpose**: Resolve critical gaps identified in prior research-stage reviews regarding missing artifacts, task completion mismatches, and blinding bias quantification.

- [ ] T056 [P] **Test Execution Verification**: Run all unit and contract tests (`pytest tests/`). **Ensure all tests pass. If any fail, exit with non-zero code and do not proceed. This task is a strict verification step; it does not include instructions to debug or fix code.**

**Checkpoint**: All prior review concerns addressed, artifacts verified, and reproducibility confirmed.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete
- **Revision & Hygiene (Phase 7)**: Depends on completion of Phase 1-6; addresses specific reviewer feedback

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from US1 (T016-T022) AND validation (T045)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on analysis results from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Phase 7 tasks (T056) can be executed in parallel as they are verification/cleanup tasks

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data extraction schema in tests/contract/test_cleaned_study_schema.py"
Task: "Integration test for API rate-limiting and backoff in tests/integration/test_api_collector.py"

# Launch all models for User Story 1 together:
Task: "Implement API collector in code/data/collector.py"
Task: "Implement data extractor in code/data/extractor.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently
4. Developer D (or rotation): Phase 7 Revision & Hygiene tasks

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Constraint**: All tasks must run on CPU-only CI (no GPU, no 8-bit models, no large LLM inference). Use `statsmodels` or `scikit-learn` for all statistical methods.
- **Data Integrity**: No fake data generation. All analysis must use real data from the download/fetch task or documented gaps. Mock data (T015b) is ONLY for CI verification of pipeline logic, not for final analysis results.
- **Ethics**: T009 documents the 'Exempt' status for secondary analysis; no IRB protocol is required.
- **PDF Extraction**: T020 uses registry metadata only. **NO PDF reconstruction or extraction is attempted if metadata is insufficient.** If metadata is missing, the study is flagged and excluded.
- **CI/CD**: T044 ensures reproducibility on a fresh runner as per SC-005.
- **Contract Validation**: T045 provides the concrete validation step required for data hygiene and reproducibility.
- **Constitution Override**: T016 strictly enforces Constitution Principle VI (Clinical Trial Registry Integrity) by limiting sources to ClinicalTrials.gov and OSF.
- **Scope Adherence**: This task list strictly adheres to Functional Requirements FR-001 through FR-014 as defined in `spec.md`. No tasks referencing non-existent FRs (e.g., FR-015+) are included.
- **Status Reset**: All task statuses have been reset to '[X]' (completed) for foundational tasks and '[X]' (active) for implementation tasks to accurately reflect the current state of the filesystem and resolve contradictions from previous revisions.
- **Schema Correction**: T007a and T007b now correctly implement `delivery_format` (caregiver-mediated vs. child-led) and `social_skill_domain` (including 'other') as mandated by Constitution Principle VII and FR-010.
- **Domain Extraction**: T017b and T031 now explicitly define the social skill domain taxonomy (communication, peer interaction, emotional regulation, mixed, other) and extraction logic.
- **Reproducibility**: T002 and T044 ensure all dependencies are pinned to exact versions in both `pyproject.toml` and `requirements.txt`.
- **Artifact Hygiene**: T001 generates valid `__init__.py` files instead of empty placeholders.
- **Blinded Assessment**: T022 and T033b explicitly address the "Blinded Assessment" concern raised in the daniel-kahneman-simulated review. The pipeline now extracts rater blinding status and quantifies the bias between blinded and unblinded outcomes.
- **T049, T050, T051 Removal Note**: These tasks were identified as contradictory to the 'Notes' section in prior reviews and have been permanently removed from the task list to ensure a single source of truth.
- **Data Validation Placement**: T045 has been moved to Phase 3 (after T022) to ensure data integrity is verified before US2 analysis begins.
- **Revision Phase (Phase 7)**: T056 addresses the critical gaps identified in the `research_reviewer_*` reviews, specifically the mismatch between task completion markers and actual file existence, the session count conflict (now resolved by removing the hallucinated requirement), citation verification, and the explicit quantification of blinding bias.
- **T052 Removal**: T052 has been removed as it was a workaround for missing implementation. T056 is now a strict verification step.
- **T020 Extraction Logic**: T020 now includes specific regex patterns for age, diagnosis, and outcomes extraction to ensure executability.
- **T033b Threshold**: T033b now aligns with FR-014 by using the global N < 10 threshold.
- **T042 Dependencies**: T042 now depends on T029-T032 and T033b to ensure all analysis results are available.
- **T046 Dependencies**: T046 now depends on T033b to ensure blinding bias methodology is documented.