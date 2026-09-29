# Tasks: Mindfulness Components and Delivery Formats in ASD Social Skills

**Input**: Design documents from `/specs/001-mindfulness-asd-social-skills/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create the full project directory structure for `projects/PROJ-008-psychology-research/` relative to the repository root. This includes: `code/`, `data/` (with `raw/`, `processed/`, `interim/`), `docs/`, `tests/` (with `unit/`, `integration/`, `contract/`), `contracts/`, `scripts/`, `.github/workflows/`. **Execute `mkdir -p projects/PROJ-008-psychology-research/{code,data/{raw,processed,interim},docs,tests/{unit,integration,contract},contracts,scripts,.github/workflows}`. Do NOT create empty placeholder files.**
- [X] T001a [P] Create valid `__init__.py` files in all `code/` and `tests/` subdirectories to ensure Python package recognition.
- [X] T001b [P] Create `data/raw/.gitkeep` file to ensure the directory is tracked.

- [X] T002 [P] Create `pyproject.toml` at `projects/PROJ-008-psychology-research/` with: build-system (setuptools>=61.0), python version `>=3.11`, and dependencies list with **PINNED versions** (e.g., `pandas==2.0.0`, `scikit-learn==1.3.0`, `statsmodels==0.14.0`, `matplotlib==3.7.0`, `requests==2.31.0`, `pyyaml==6.0`, `pytest==7.4.0`, `bayesmeta==0.1.0`, `pdfplumber==0.10.0`). **No version ranges (>=) are permitted.** Also generate `requirements.txt` at the same location by extracting these pinned dependencies to ensure reproducibility on fresh runners (SC-005). Verify that `requirements.txt` contains exact versions for all packages.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools. **Create `.ruff.toml` at `projects/PROJ-008-psychology-research/.ruff.toml` with `line-length = 88`, `target-version = "py311"`, and `select = ["E", "F", "W", "I"]`. Create `pypy.toml` sections `[tool.black]` (line-length=88, target-version=['py311']) and `[tool.ruff]` matching the `.ruff.toml` rules. Ensure `pyproject.toml` is updated if it does not exist.**

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create base Pydantic models for `Study`, `EffectSize`, and `MetaAnalysisResult` in `code/data/models.py`. **Include docstrings describing the purpose of each field.**
- [X] T005 [P] Implement structured logging infrastructure in `code/utils/logging.py` (FR-007)
- [X] T006 [P] Setup configuration management and seed pinning in `code/utils/config.py`
- [X] T007a [P] **Create** `contracts/cleaned_study.schema.yaml` with **FULL JSON Schema (Draft 7) in YAML format**. Write the following content to the file:
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
- [X] T007b [P] **Create** `contracts/effect_size.schema.yaml` with **FULL JSON Schema (Draft 7) in YAML format**. Write the following content to the file:
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
 hedges_g: { number }
 se: { number }
 ci_lower: { number }
 ci_upper: { number }
 n_treatment: { integer, minimum: 1 }
 n_control: { integer, minimum: 1 }
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

### Implementation for User Story 1 (Data Generation & Collection)

- [X] T015b [P] [US1] **Create TEST-ONLY Mock Data Generator**: Generate `data/raw/mock_registry_response.json` containing a representative set of records. **THIS IS TEST-ONLY DATA. Do NOT include this file in final `data/` checksums or production analysis. Add `data/raw/mock_registry_response.json` to `.gitignore` (or equivalent exclusion) to ensure isolation.**
 1. Record 1: Valid study, age 8, ASD, social outcome, abstract present.
 2. Record 2: Valid study, age 10, ASD, social outcome, **NO abstract** (to trigger T020 exclusion logic if metadata is missing).
 3. Record 3: Invalid study, age 15 (out of range), ASD, social outcome.
 **Ensure JSON structure matches the API response format expected by T016. Required fields: id, title, registry, age_range (min, max), diagnosis, outcomes (array), abstract (nullable), intervention_components (array), delivery_format, social_skill_domain, follow_up, rater_type, blinded_assessment_flag. Verify JSON structure against `contracts/cleaned_study.schema.yaml` before saving.**
- [X] T015c [P] [US1] **Create TEST-ONLY Blinded Mock Data**: Generate `data/raw/mock_blinded_response.json` containing a small set of mock records derived from Record 1. **THIS IS TEST-ONLY DATA. Do NOT include this file in final `data/` checksums or production analysis. Add `data/raw/mock_blinded_response.json` to `.gitignore` (or equivalent exclusion) to ensure isolation.**
 1. Record A: Same study, but explicitly labeled `rater_type: "unblinded"` and `blinded_assessment_flag: false`.
 2. Record B: Same study, but explicitly labeled `rater_type: "blinded"` and `blinded_assessment_flag: true`.
 **This data is for testing the blinding comparison logic in T022.**

### Implementation for User Story 1 (Core Pipeline)

- [X] T016 [US1] depends on T007a, T007b, T006: Implement API collector in `code/data/collector.py` (FR-001, FR-002) with rate-limiting (requests per minute per API) and exponential backoff (base s, max bounded duration) for **ClinicalTrials.gov and OSF ONLY** per Constitution Principle VI. **Logic:
 1. For Production Runs: Fetch directly from ClinicalTrials.gov and OSF APIs. Log search query strings and retrieval timestamps to `data/raw/retrieval_log.json`.
 2. For CI/Testing Runs: The CI environment MUST set `CI_MODE=true`. In this mode, the script MUST load a **verified, checksummed snapshot** of real data (e.g, `data/raw/verified_snapshot_2026.json`) that was previously fetched from the canonical sources.
 3. **NO MOCK DATA**: The script MUST NOT load `data/raw/mock_registry_response.json` in any production or CI scenario. If a mock file is detected, the script MUST raise a `RuntimeError` with message "Mock data detected in production/CI run; aborting."
 4. **Fresh Runner Setup**: To test on a fresh runner, the CI workflow must first download the verified snapshot from a secure artifact storage (e.g., GitHub Actions cache) and place it at `data/raw/verified_snapshot_2026.json`.
 5. **Error Handling**: If the API fetch fails, the script MUST raise an error. Do NOT fall back to mock data.**
- [X] T017a [US1] depends on T007a, T007b: Implement data extractor for intervention components in `code/data/extractor.py` (FR-003). **Logic: Scan the 'description' and 'abstract' fields of registry metadata. Use case-insensitive, whole-word regex patterns to detect: 'breathing', 'body scan', 'mindful movement', 'mindful eating'. Output: List of detected components in `intervention_components` column.**
- [X] T017b [US1] depends on T007a, T007b: Implement data extractor for social skill domains in `code/data/extractor.py` (FR-010). **Logic: Scan the 'description' and 'abstract' fields. Use regex patterns to detect keywords mapping to exactly three domains: 'communication' (keywords: speech, language, verbal, non-verbal), 'peer interaction' (keywords: peer, social, group, play), 'emotional regulation' (keywords: emotion, affect, regulation, tantrum). Assign the first matching domain found. If multiple, assign 'mixed'. If a valid domain is described but not in the keyword list, assign 'other' AND populate the `domain_notes` field with the original text description. Output: `social_skill_domain` column with values restricted to [communication, peer interaction, emotional regulation, mixed, other] and `domain_notes` column for unmatched descriptions.**
- [X] T018 [US1] depends on T007a, T007b, T016: Implement data cleaner in `code/data/cleaner.py` (FR-007) to validate age **6-12 (per US1 in spec.md)**, ASD diagnosis, and social skill outcomes. **Logic: Validate `outcomes` field by checking if any item in the array contains the phrase 'social skill' (case-insensitive) or matches known validated measure patterns (e.g., 'SRS', 'ABC', 'SSIS', 'PEP'). If no match is found, flag the study in `data/raw/excluded_studies.log` (JSONL format: `[{study_id: str, reason: "INVALID_OUTCOME", timestamp: str}])`.**
- [X] T019 [US1] depends on T007a, T007b: Implement multi-arm study handling logic in `code/data/cleaner.py` (FR-008) to split control groups proportionally.
- [X] T020 [US1] depends on T007a, T007b, T016, T017a, T017b, T018, T019, T022: Implement **Abstract-only text extraction fallback** in `code/data/extractor.py` (FR-009). **Logic:
 1. Define 'insufficient metadata' as the absence of ANY of the three mandatory inclusion fields: `age_range`, `diagnosis`, OR `outcomes`.
 2. **STRICT EXCLUSION**: If ANY of these three fields are missing in the primary metadata, the study MUST be EXCLUDED immediately. **DO NOT attempt to extract missing fields from the abstract.** This preserves the integrity of the inclusion criteria.
 3. **Null Handling**: If the `abstract` field is missing or null in the API response, log the study as excluded with reason "INSUFFICIENT_METADATA_NO_ABSTRACT".
 4. **Regex Patterns**: (For future use if abstract extraction is ever permitted, though currently excluded): Age: 'aged [0-9]+', 'children [0-9]+', 'mean age [0-9]+'; Diagnosis: 'ASD', 'Autism Spectrum', 'PDD-NOS', 'Autistic'; Outcomes: 'SRS', 'ABC', 'SSIS', 'social skill', 'communication'.
 5. **Output**: Flag the study in `data/raw/excluded_studies.log` (JSONL: `[{study_id: str, reason: "INSUFFICIENT_METADATA_NO_ABSTRACT" OR "MISSING_PRIMARY_FIELD", timestamp: str}])`.**
- [X] T022 [US1] depends on T007a, T007b, T015c: **Implement Blinded Assessment Logic**: Extract `rater_type` and `blinded_assessment_flag` from registry metadata (or mock data). **Logic: Identify if a study reports blinded vs. unblinded raters. If a study reports both (e.g., primary outcome unblinded, secondary blinded), flag as 'mixed'. If the blinding information is missing or null in the metadata, flag the study as 'unknown' (do not fail). Output: Add `rater_type` and `blinded_assessment_flag` columns to `data/processed/cleaned_studies.csv`.**
- [X] T052 [US1] depends on T016, T017a, T017b, T018, T019, T020, T022, T007a, T007b: **Generate Verified Real Data Snapshot**: Run T016 in a controlled environment against real ClinicalTrials.gov/OSF APIs to produce a valid, checksummed snapshot. Save output as `data/raw/verified_snapshot_2026.json`. **This artifact MUST be uploaded to GitHub Actions cache/artifacts for use by T044 (CI Pipeline). This task ensures Constitution Principle I (Reproducibility) is met by providing the real data source for CI runs.**
- [ ] T021 [US1] depends on T052, T016, T017a, T017b, T018, T019, T020, T022, T007a, T007b: **Verify and archive output**: Create script `scripts/verify_output.py` that checks for existence of `data/processed/cleaned_studies.csv` and `data/raw/excluded_studies.log`. **Verify CSV schema compliance against `contracts/cleaned_study.schema.yaml`. If CSV is empty (0 rows), verify that `data/raw/verified_snapshot_2026.json` exists (indicating CI mode) OR that no studies matched criteria (real mode); do NOT fail on empty CSV. If CSV has rows, verify row count > 0. Exits 0 on success, 1 on failure.**

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
- [X] T029 [US2] depends on T028, T016, T017a, T017b, T018, T019, T020, T021, T022, T007a, T007b: Implement random-effects meta-analysis engine in `code/analysis/meta_analysis.py` (FR-005) using `statsmodels`. **Logic: Use `statsmodels.stats.meta_analysis.combine_effects` to calculate pooled effect. Calculate I². If I² > 0.5, use random-effects model; otherwise, use fixed-effects model. Output: Pooled effect size, heterogeneity statistics.**
- [X] T030 [US2] depends on T028, T017a, T017b, T007a, T007b: Implement subgroup analysis (Cochran's Q) for mindfulness components and delivery formats in `code/analysis/meta_analysis.py` (FR-005). **Logic: Use `scipy.stats.chi2` for Cochran's Q test. Categorize 'mindfulness components' as binary (present/absent) based on `intervention_components` column. Categorize 'delivery formats' by mapping `delivery_format` column values (caregiver-mediated vs. child-led) to groups. Output: Subgroup effect sizes and heterogeneity statistics for each group. (Note: This task does NOT depend on T029; it consumes T028 directly).**
- [X] T031a [US2] depends on T017b, T007a, T007b: **Implement Social Skill Domain Extraction**: Create function in `code/analysis/meta_analysis.py` to extract and validate `social_skill_domain` values from the cleaned CSV. **Logic: Ensure all values in `social_skill_domain` column are one of [communication, peer interaction, emotional regulation, mixed, other]. Flag any 'other' entries for manual review.**
- [X] T031b [US2] depends on T031a, T028: **Implement Social Skill Domain Subgroup Analysis**: Create function in `code/analysis/meta_analysis.py` to calculate subgroup effect sizes for each `social_skill_domain`. **Logic: Group studies by `social_skill_domain` column. Calculate subgroup effect sizes and heterogeneity statistics for each domain. Output: Subgroup effect sizes and heterogeneity statistics for each domain.**
- [X] T032 [US2] depends on T028, T007a, T007b: Implement follow-up duration subgroup analysis (3-month vs. others) in `code/analysis/meta_analysis.py` (FR-012). **Logic: Parse `follow_up` string field to days (e.g., '3 months' -> 90, '6 months' -> 180). Group studies into <90 days vs >=90 days. Output: Subgroup effect sizes for each group. (Note: This task does NOT depend on T029; it consumes T028 directly).**
- [X] T033 [US2] depends on T028, T029, T030, T031b, T032, T007a, T007b: Implement conditional logic to suppress subgroup/meta-regression if N < 10 and switch to descriptive synthesis (FR-014)
- [X] T033b [US2] depends on T022, T028, T007a, T007b: **Implement Blinding Bias Quantification**: Extend `code/analysis/meta_analysis.py` to perform a specific subgroup analysis comparing `blinded_assessment_flag = true` vs `false`. **Logic:
 1. If N >= 10 (global threshold per FR-014), calculate the difference in pooled effect sizes between the two groups.
 2. If N < 10, SKIP the analysis and log a warning to `docs/results.md` stating "Insufficient studies (N < 10) for blinding bias quantification."
 3. Output: Quantify the difference and report it in `docs/results.md`. (Cites Constitution Principle VII and FR-005). Verify that the analysis correctly identifies a statistically significant difference with p-value < 0.05 in the test dataset. (Note: This task does NOT depend on T029; it consumes T028 directly).**

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
- [ ] T042 [US3] depends on T039, T041: Generate `docs/results.md` containing: 1) Executive Summary, 2) Forest Plot (T037), 3) Funnel Plot (T038), 4) Heterogeneity Statistics (I², Q), 5) Subgroup Analysis Results (table with columns `Domain`, `N`, `Effect Size`), 6) Narrative Synthesis if N<10. **Logic for Section 5:
 1. Check if `data/processed/cleaned_studies.csv` exists.
 2. If file DOES NOT EXIST: Section 5 must state "Data pipeline failed to produce output - unable to perform subgroup analysis".
 3. If file EXISTS but has 0 data rows: Section 5 must state "No studies found (N=0) - unable to perform subgroup analysis".
 4. If file EXISTS with data rows: Read unique values from `social_skill_domain` column. If file exists but has 0 data rows, Section 5 must state "No studies found (N=0) - unable to perform subgroup analysis". If file is missing, Section 5 must state "Data pipeline failed to produce output - unable to perform subgroup analysis".
 5. Generate the table with columns `Domain`, `N`, `Effect Size` based on the data.**
- [ ] T043 [US3] depends on T042, T033b: **Add Blinding Bias Visualization**: Update `docs/results.md` and `code/viz/plots.py` to include a specific visualization (e.g., a side-by-side forest plot or a bar chart) comparing the pooled effect sizes of Blinded vs. Unblinded studies.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address current spec requirements

- [ ] T044 [P] Create `.github/workflows/ci.yml` at `projects/PROJ-008-psychology-research/.github/workflows/ci.yml` to automate pipeline execution on a fresh runner, verifying reproducibility (SC-005). **Ensure the workflow downloads `data/raw/verified_snapshot_2026.json` from the GitHub Actions cache/artifacts (populated by T052) before running T016 in CI_MODE.
  **FALLBACK LOGIC FOR INITIAL RUN**: If the snapshot is missing from the cache on the initial CI run (first time):
  1. The workflow must detect the missing artifact.
  2. Trigger a temporary manual override step (or a specific 'bootstrap' job) that runs T016 directly against real APIs (bypassing the CI_MODE check) to generate `data/raw/verified_snapshot_2026.json`.
  3. Upload the generated snapshot to the GitHub Actions cache/artifacts.
  4. Proceed with the standard CI pipeline execution.**
- [ ] T045 [P] Create `scripts/validate_contracts.py` to run schema validation on `data/processed/cleaned_studies.csv` against `contracts/cleaned_study.schema.yaml`.
- [ ] T046 [P] Generate `docs/protocol.md` containing the full methodology as per PRISMA guidelines.
- [ ] T047 [P] Create `quickstart.md` in root to document environment setup and verification steps.
- [ ] T048 [P] Add `LICENSE` file specifying research data usage terms and ensure all data artifacts have corresponding license headers.

---

## Phase 7: Revision & Artifact Hygiene (Addressing Prior Reviews)

**Purpose**: Resolve critical gaps identified in prior research-stage reviews regarding missing artifacts, task completion mismatches, and blinding bias quantification.

- [ ] T053 [P] **Resolve Session Count Conflict**: Update `docs/protocol.md` to explicitly state the final session count.
- [ ] T054 [P] **Verify Citations**: Review `docs/protocol.md` and `research.md` to ensure all citations are verified.
- [ ] T056 [P] **Test Execution Verification**: Run all unit and contract tests using the command `pytest tests/ -v --tb=short`.
- [ ] T058 [P] **Bootstrap CI Snapshot**: **Manual Step**: A human developer must run T016 (in non-CI mode) against real APIs, validate the output, and manually upload the resulting `data/raw/verified_snapshot_2026.json` to the GitHub Actions cache/artifacts. This task breaks the circular dependency for T044 by providing the initial snapshot. **Document the exact command and upload steps in `docs/CI_bootstrap.md`.**
