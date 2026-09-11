# Tasks: The Influence of Perceived Agency in AI Interactions on Trust

**Input**: Design documents from `specs/001-perceived-agency-trust/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are **REQUIRED** to ensure reproducibility and validation.

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

---

## Pre-Phase 0: Validation Gates (MANDATORY)

**Purpose**: Verify citations and scale text against primary sources BEFORE any implementation begins.
**⚠️ CRITICAL**: If T000-GATE-METADATA fails, the project transitions to `human_input_needed` immediately. No downstream tasks can run. T000-HUMAN-SOURCE requires human input to complete.

- [ ] T000-GATE-METADATA [Const-II] **Gate**: Validate citation metadata via Crossref API.
 **Input**: `spec.md` and `plan.md`.
 **Logic**:
 1. Parse `spec.md` and `plan.md` to extract claimed citations (e.g., "Lee & See (2004)", "Langer (1975)").
 2. For Lee & See (2004), use the **explicitly known DOI** `10.1518/hfes.46.1.50_30392` as defined in the plan. **Do NOT infer or search** for the DOI.
 3. Use `requests` to call ` and fetch metadata.
 4. Compute a string overlap score between fetched `title` and claimed title using `difflib.SequenceMatcher`.
 5. **Verify Metadata ONLY**: Title, DOI, Year, Journal. **DO NOT** attempt to verify item text via API as Crossref does not provide full text.
 6. If any overlap < 0.7, DOI lookup fails (404), or metadata is missing, raise `SystemExit(1)` with message **"Citation Metadata Verification Failed"**.
 **Output**: `data/processed/citation_log.json` containing `{author, year, title, doi, item_verification_status: "pending_human_source"}`.
 **Dependency**: None.

- [ ] T000-HUMAN-SOURCE [Const-II] **Gate**: Human-sourced verification of Lee & See (2004) 12-item text array.
 **Input**: `data/processed/citation_log.json` (from T000-GATE-METADATA).
 **Logic**:
 1. **Human Action**: The implementer MUST manually source the 12-item text array from **Lee & See (2004), Table 1** (the primary source PDF).
 2. The implementer MUST write these 12 items verbatim into `research/human_verified_items.json` with the key `items` (array of strings) and `source` ("Lee & See (2004), Table 1, verified against primary publication PDF").
 3. **Verification**: The task logic must verify that `research/human_verified_items.json` exists and contains exactly 12 non-empty string items.
 4. If the file is missing or malformed, raise `SystemExit(1)` with message **"Human-Verified Items Missing or Malformed"**.
 5. Update `data/processed/citation_log.json` (from T000-GATE-METADATA) to set `item_verification_status: "pending_auto_verify"`.
 **Output**: `research/human_verified_items.json` and updated `data/processed/citation_log.json`.
 **Dependency**: T000-GATE-METADATA.

- [ ] T000-GATE-ITEMS-AUTO [Const-II] **Gate**: Automated verification of human-sourced items.
 **Input**: `research/human_verified_items.json` (from T000-HUMAN-SOURCE) and `data/processed/citation_log.json`.
 **Logic**:
 1. Read `research/human_verified_items.json` from the file system.
 2. Verify the file exists and is valid JSON.
 3. Verify the array has a finite number of items, and each item is a non-empty string.
 4. Compute a cryptographic hash of the file content.
 5. Update `data/processed/citation_log.json` to set `item_verification_status: "verified"` and include the hash.
 6. If verification fails (missing file, wrong count, empty strings, or invalid JSON), raise `SystemExit(1)` with message **"Automated Item Verification Failed: File missing or content invalid"**.
 **Output**: Updated `data/processed/citation_log.json`.
 **Dependency**: T000-HUMAN-SOURCE.

---

## Phase 0: Research & Validation (Prerequisites)

**Purpose**: Verify citations, execute power analysis, generate protocol, and create research artifacts before implementation begins.

**Strict Sequence**: T000-GATE-METADATA -> T000-HUMAN-SOURCE -> T000-GATE-ITEMS-AUTO -> T008-init-std -> T042 -> T001a-1 -> T001a-2 -> T001b-1 -> T001b-2 -> T010c -> T010b-auto -> T011 -> T007g -> T002 -> T002b-REPORT -> T003-1 -> T008 -> T008-VALIDATE -> T008-CLI-EXPOSE.
**Reasoning**: T000-GATE-METADATA validates metadata. T000-HUMAN-SOURCE sources text. T000-GATE-ITEMS-AUTO verifies text. T008-init-std defines defaults. T042 generates protocol from defaults. T001a-1/2 validate plan schema. T010c creates verified source file from T000-GATE-ITEMS-AUTO. T010b-auto/T011/T007g verify scale items. T002 calculates power. T002b-REPORT generates the report. T008 finalizes config using T002's sample size and T042's protocol ranges. T008-VALIDATE ensures the final config is correct. T008-CLI-EXPOSE implements user configuration. **Note**: T002 (Power) and T007g (Scale Verification) can run in parallel after their respective prerequisites are met.

- [ ] T008-init-std [P] **Initialize** default configuration for sensitivity analysis.
 **Structure**: YAML file `code/analysis/config_defaults.yaml` AND `code/analysis/config_user.yaml` template.
 **Content**: Define default sensitivity sweep ranges based on standard practice (e.g., `attention_thresholds: [70, 80, 90, 95]`, `adherence_cutoffs: [70, 80, 90]`).
 **Logic**:
 1. Create `code/analysis/config_defaults.yaml` with hardcoded standard practice values.
 2. Create `code/analysis/config_user.yaml` template with placeholders for user overrides.
 3. **User Configuration**: This file serves as the **single source of truth for defaults**. The final config (T008) will allow users to override these ranges via `code/analysis/config_user.yaml`. If the user file exists, its values take precedence.
 **Output**: `code/analysis/config_defaults.yaml` and `code/analysis/config_user.yaml`.
 **Dependency**: T000-GATE-METADATA, T000-HUMAN-SOURCE, T000-GATE-ITEMS-AUTO.

- [ ] T042 [P] [FR-006] Generate `docs/protocol.md` with pre‑registered analysis plan. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
 **Requirement**: Reference FR‑006, US‑3, and the specific sensitivity sweep parameters.
 **Logic**:
 1. Read sensitivity sweep ranges defined in `code/analysis/config_defaults.yaml` (from T008-init-std).
 2. Write these ranges and the full pre‑registered analysis steps to `docs/protocol.md`.
 **Output**: `docs/protocol.md`.
 **Dependency**: T008-init-std.

- [ ] T001a-1 [P] [Dataset Fit] Parse `plan.md` to locate the 'Technical Context' and 'Project Structure' sections.
 **Logic**:
 1. Use the `mistune` markdown parser to parse `plan.md`.
 2. Extract the content under headings `## Technical Context` and `## Project Structure`.
 3. Search within those blocks for variable definitions using a **robust regex** that matches the variable names `(Condition ID|Adherence Rate|Trust Score|Perceived Agency Score|Attention Check Status)`.
 4. If no matches are found, raise a clear `RuntimeError` indicating the missing variables.
 **Output**: `research/dataset_schema_parsed.txt` containing the extracted text.
 **Dependency**: T000-GATE-METADATA, T000-HUMAN-SOURCE, T000-GATE-ITEMS-AUTO.

- [ ] T001a-2 [P] [Dataset Fit] Verify the *plan's intent* to capture required variables and generate the report.
 **Logic**:
 1. Read `research/dataset_schema_parsed.txt` (from T001a-1) and `spec.md`.
 2. Confirm that FR‑002 and US‑1 explicitly mandate capture of the identified variables.
 3. Write `research/dataset_verification_report.md` with a clear "Verified" status; abort with `SystemExit(1)` if any required variable is missing.
 **Output**: `research/dataset_verification_report.md`.
 **Dependency**: T001a-1.

- [ ] T001b-1 [P] [Lit Review] Extract citation metadata and content from `data/processed/citation_log.json` (T000-GATE-METADATA) for "Lee & See (2004)" and "Langer (1975)".
 **Logic**: If `source_url` is present, fetch the abstract/findings; otherwise use the `content_verified` summary from the validator.
 **Output**: `research/citation_metadata.json` containing `title`, `doi`, `summary_findings`.
 **Dependency**: T000-GATE-METADATA, T000-HUMAN-SOURCE, T000-GATE-ITEMS-AUTO.

- [ ] T001b-2 [P] [Lit Review] Generate the literature review summary required by Plan.md Phase 0.
 **Logic**: Summarize key findings from the two citations using `summary_findings` from T001b-1.
 **Output**: `research/literature_review.md`.
 **Dependency**: T001b-1.

- [ ] T010c [P] [SC-004] **Create** the verified source file for Lee & See (2004) items. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
 **Logic**:
 1. Verify `data/processed/citation_log.json` (from T000-GATE-METADATA, T000-HUMAN-SOURCE, T000-GATE-ITEMS-AUTO) confirms the item text source and status "verified".
 2. Read the 12 items from `research/human_verified_items.json` (created by T000-HUMAN-SOURCE).
 3. Create `data/verified_sources/lee_see_2004_items.json` with the exact 12-item text array.
 4. Validate the JSON array contains a specified number of items.
 5. Write `research/item_source_log.json` confirming the source of these items (referencing `research/human_verified_items.json`).
 **Output**: `data/verified_sources/lee_see_2004_items.json` and `research/item_source_log.json`.
 **Dependency**: T000-GATE-METADATA, T000-HUMAN-SOURCE, T000-GATE-ITEMS-AUTO.

- [ ] T002 [P] Execute pre‑study power analysis calculation for **planned directional contrasts** AND **overall ANOVA** using Python `scipy` and `numpy`.
 **Script**: `code/research/power_analysis.py`.
 **Args**: Hard‑coded design parameters: `effect_size` (f=0.25), `alpha` (0.05 (Wikipedia: Power (statistics), https://en.wikipedia.org/wiki/Power_(statistics))), `power` (0.80).
 **Implementation**: (code omitted for brevity – see original).
 **Output**: `research/power_calculation.json` (machine‑readable with keys `params` and `results`).
 **Dependency**:T000-GATE-METADATA, T000-HUMAN-SOURCE, T000-GATE-ITEMS-AUTO, T001a-2.

- [ ] T002b-REPORT [P] Generate the pre-study power analysis report.
 **Requirement**: Generate `docs/power_analysis_report.md` as referenced in the Plan.md Phase 0.
 **Logic**:
 1. Read `research/power_calculation.json` (from T002).
 2. Generate a human-readable report `docs/power_analysis_report.md` summarizing the power calculation, required sample size, and design parameters.
 **Output**: `docs/power_analysis_report.md`.
 **Dependency**: T002.

- [ ] T010b-auto [P] [SC-004] Retrieve the canonical Lee & See (2004) Trust Scale items **automatically**.
 **Logic**:
 1. Verify `data/processed/citation_log.json` (from T000-GATE-METADATA, T000-HUMAN-SOURCE, T000-GATE-ITEMS-AUTO) confirms the item text source.
 2. Fetch the 12 items from the version-controlled source file `data/verified_sources/lee_see_2004_items.json` (created by T010c).
 3. Validate the fetched JSON array has exactly 12 items.
 4. Write `docs/trust_scale_items.md` with the verified items (if not already done by T000-HUMAN-SOURCE).
 5. If the file is missing or malformed, raise `SystemExit(1)`.
 **Output**: `docs/trust_scale_items.md`.
 **Dependency**: T000-GATE-METADATA, T000-HUMAN-SOURCE, T000-GATE-ITEMS-AUTO, T010c.

- [ ] T011 [P] [SC-004] Verify `docs/trust_scale_items.md` matches the validated text.
 **Logic**: Compare the JSON array against the reference list defined in `research/item_source_log.json` (from T010c).
 **Output**: Pass/Fail log.
 **Dependency**: T010b-auto.

- [ ] T007g [P] [SC-004] Generate `research/trust_scale_verification_report.md`.
 **Logic**: Read `research/item_source_log.json`; extract items from `docs/trust_scale_items.md`; confirm exact match; write report.
 **Output**: `research/trust_scale_verification_report.md`.
 **Dependency**: T010b-auto, T011, T000-GATE-METADATA, T000-HUMAN-SOURCE, T000-GATE-ITEMS-AUTO.

- [ ] T003-1 [P] Validate `research/literature_review.md`, `research/power_calculation.json`, AND `docs/power_analysis_report.md` against `plan.md` Phase 0 requirements.
 **Logic**: Assert presence of required sections and keys. **Specifically validate that `docs/power_analysis_report.md` exists and contains the required power confirmation.**
 **Dependency**: T002, T002b-REPORT, T001a-2, T001b-2, T042.

- [ ] T008 [P] Setup environment configuration management by creating `code/analysis/config.yaml`.
 **Structure**: YAML with keys: `sample_size` (read from `research/power_calculation.json` → `results.final_n`), `alpha_level` (0.05), `seed` (42), `data_path` (`data/raw/`), `sensitivity_config` (object containing sweep ranges).
 **Logic**:
 1. Read sensitivity sweep ranges defined in `docs/protocol.md` (generated by T042).
 2. Populate `sensitivity_config` in `config.yaml` **exactly** matching those ranges, but **allow user overrides** via `code/analysis/config_user.yaml` if it exists.
 3. Read `sample_size` from `research/power_calculation.json` (generated by T002).
 **Output**: `code/analysis/config.yaml`.
 **Dependency**: T042, T002.

- [ ] T008-VALIDATE [P] Validate the final config.yaml against the protocol and defaults.
 **Logic**:
 1. Read `code/analysis/config.yaml` and `docs/protocol.md`.
 2. Verify that `sensitivity_config` in `config.yaml` matches the ranges in `protocol.md` (or is a valid user override).
 3. If mismatch, raise `SystemExit(1)`.
 **Output**: `research/config_validation_report.json`.
 **Dependency**: T008, T042.

- [ ] T008-CLI-EXPOSE [FR-006] Implement CLI argument handling for sensitivity analysis ranges.
 **Logic**:
 1. Create `code/analysis/cli.py` with arguments `--attention-thresholds`, `--adherence-cutoffs`, etc.
 2. Parse these arguments as **comma-separated lists of integers** (e.g., `--attention-thresholds 70,80,90`). **Explicitly strip whitespace and raise ValueError on non-integer tokens.**
 3. Override the values in `code/analysis/config.yaml` at runtime.
 4. Ensure the sensitivity analysis (T038) reads these runtime values.
 **Output**: `code/analysis/cli.py`.
 **Dependency**: T008, T008-init-std.

- [ ] T035a [P] [US3] **Manipulation Check**: Perform ANOVA on `Perceived_Agency_Score` by condition.
 **Logic**:
 1. Compute ANOVA on `Perceived_Agency_Score` grouped by `Condition`.
 2. If p > 0.05, report "Manipulation Failed" and **halt** analysis pipeline (do not proceed to Trust analysis).
 3. Output `results/manipulation_check.json` with `status`, `f_stat`, `p_value`.
 **Output**: `results/manipulation_check.json`.
 **Dependency**: T026 (Data Capture).

- [ ] T035b [P] [US3] **Achieved Power**: Calculate achieved power post-hoc.
 **Logic**:
 1. Read `research/power_calculation.json` for target N.
 2. Compute achieved power based on actual N and observed effect size.
 3. If achieved power < 0.80, append "Limitation: Insufficient Power" to final report.
 4. **Do not halt** pipeline; report limitation.
 **Output**: `results/power_status.json`.
 **Dependency**: T002, T034.

- [ ] T035c [P] [US3] **Cognitive Load Check**: Perform ANOVA on `Cognitive_Load_Score` by condition.
 **Logic**:
 1. Compute ANOVA on `Cognitive_Load_Score` grouped by `Condition`.
 2. If p < 0.05, flag `Cognitive_Load_Score` as a covariate for the main Trust analysis (ANCOVA).
 3. Output `results/cognitive_load_check.json` with `status`, `f_stat`, `p_value`, `is_covariate`.
 **Output**: `results/cognitive_load_check.json`.
 **Dependency**: T026 (Data Capture).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

**Strict Sequence**: T004 -> (T005, T006, T010) parallel -> T009 -> T012 -> T017i -> T017h -> T015 -> T016.
**Note**: All tasks below depend only on directory creation (T004) unless otherwise noted.

- [ ] T004 [P] Create project directory structure. `mkdir -p code/experiment code/experiment/tests code/analysis code/analysis/tests data/raw data/processed data/verified_sources docs specs/001-perceived-agency-trust/contracts`. Add `__init__.py` in all `code/` subdirectories and `tests/` subdirectories.

- [ ] T005 [P] Initialize Python project with pinned dependencies in `requirements.txt` (streamlit, pandas, numpy, scipy, statsmodels, pingouin, pytest, requests, pyyaml, jsonschema).

- [ ] T006 [P] Configure linting (flake8/black). Create `.flake8` and `pyproject.toml` for black. Verify with `black --check`.

- [ ] T010 [P] Create base data processing utilities in `code/analysis/data_utils.py`. Functions: `load_csv`, `compute_checksum`, `scan_pii`. Implements SHA‑256 checksumming and PII flagging.

- [ ] T009 [P] [FR-001] Create **final** data schema contracts in `specs/001-perceived-agency-trust/contracts/`.
 **Content**:
 1. `participant.schema.yaml` defines fields: `participant_id` (string, UUID), `condition` (enum: High, Low, Control), `adherence_rate` (float, 0‑100), `trust_score` (float, 1‑5), `attention_check` (boolean), `perceived_agency_score` (float, 1‑7, manipulation check only), `attention_score` (float, 0‑100).
 2. Defines `trust_item_1` … `trust_item_12` as **static keys** of type `string` (they will hold the respondent's chosen Likert label, not the question text). The actual question wording lives in `docs/trust_scale_items.md`.
 3. `analysis_output.schema.yaml` and `power_analysis.schema.yaml` as per spec.
 **Dependency**: T004, T000-GATE-METADATA, T000-HUMAN-SOURCE, T000-GATE-ITEMS-AUTO.

- [ ] T012 [P] [SC-004] Finalize data schema contracts. Ensure `participant.schema.yaml` matches description in T009 and documents `perceived_agency_score` as manipulation check only.
 **Dependency**: T009.

- [ ] T017i [P] [SC-004] Generate `docs/data-model.md` describing entities (Participant, Condition, Result) and referencing contracts.

- [ ] T017h [P] [SC-004] Generate `docs/quickstart.md` with step‑by‑step local setup instructions.

- [ ] T015 [P] Produce experimental interface design specification in `docs/design/interface_design.md` (wireframes via Mermaid). Reference FR‑001 and US‑1.

- [ ] T016 [P] Produce analysis pipeline specification in `docs/design/analysis_pipeline_spec.md`. Include algorithm flow, statistical test definitions, data cleaning rules. Reference US‑2 and US‑3.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [ ] T018 [P] [FR-001] Implement randomization logic in `code/experiment/randomization.py` (assign High/Low/Control with fixed seed).
 **Dependency**: T004.

---

## Phase 3: User Story 1 - Experimental Task Execution and Data Capture (Priority: P1) 🎯 MVP

**Goal**: Present the simulated decision‑making task with randomized conditions and capture behavioral/psychometric data.

- [ ] T019 [P] [US1] Implement "High Agency" condition interface in `code/experiment/app.py` (functional sliders that do NOT alter AI output).
 **Dependency**: T018, T010.

- [ ] T020 [P] [US1] Implement "Low Agency" condition interface in `code/experiment/app.py` (restricted controls).
 **Dependency**: T018, T010.

- [ ] T021 [P] [US1] Implement "Control" condition interface in `code/experiment/app.py` (static AI display).
 **Dependency**: T018, T010.

- [ ] T022 [US1] [FR-002] Implement adherence tracking logic in `code/experiment/app.py`.
 **Requirement**: Capture behavioral adherence as a percentage.
 **Formula**: `adherence_rate = (followed_recommendations / total_recommendations) * 100`.
 **Dependency**: T018, T010.

- [ ] T023 [US1] Implement attention check questions and straight‑lining detection in `code/experiment/app.py`. Include standard attention checks; flag if consecutive identical responses exceed a threshold. **Calculate `attention_score` as the percentage (0-100) of correct answers from 5 distinct questions. ** Output `attention_check_status` (boolean) AND `attention_score` (float).
 **Dependency**: T018, T010.

- [ ] T024 [US1] [FR-002] [SC-004] Implement Lee & See (2004) Trust Scale items in `code/experiment/app.py` survey section.
 **Requirement**: Load verbatim 12‑item array from `docs/trust_scale_items.md` at runtime. Map items to `trust_item_1` … `trust_item_12`. Use `st.radio` with five Likert options (1‑5).
 **Dependency**: T018, T010, T010b-auto, T011, T000-GATE-METADATA, T000-HUMAN-SOURCE, T000-GATE-ITEMS-AUTO.

- [ ] T024b [US1] [FR-002] Runtime verification gate for Trust Scale.
 **Logic**: Before the experiment starts, load `docs/trust_scale_items.md` and compare the JSON array **exactly** against the verified list in `research/trust_scale_verification_report.md`. If mismatch, raise `SystemExit(1)` and block start.
 **Dependency**: T024, T007g.

- [ ] T024c [US1] Implement Trust Score aggregation in `code/experiment/app.py`.
 **Requirement**: `trust_score = mean(trust_item_1,..., trust_item_12)` (numeric conversion of Likert labels). Store in export.
 **Dependency**: T024.

- [ ] T025 [US1] Implement data export to `data/raw/` with checksum generation and timestamped filename. Ensure schema compliance.
 **Dependency**: T018, T010, T024c, T024b.

- [ ] T025b [US1] Runtime schema validation before export. Validate against `participant.schema.yaml`; abort on failure.
 **Dependency**: T025, T012.

- [ ] T026 [US1] Implement manipulation check question (`perceived_agency_score`, 1‑7 Likert) and cognitive load question (`cognitive_load_score`, 1‑7 Likert). Document that they are **only** for descriptive analysis or covariate checks, never used as direct proxies for Trust.
 **Dependency**: T018, T010.

- [ ] T027 [P] [US1] Unit test for randomization logic (`code/experiment/tests/test_randomization.py`). Verify distribution and seed stability.

- [ ] T028 [P] [US1] Integration test for session flow (`code/experiment/tests/test_session_flow.py`). Verify end‑to‑end data capture.

---

## Phase 4: User Story 2 - Statistical Analysis Pipeline Execution (Priority: P2)

**Strict Sequence**: T029 -> T035a -> T035b -> T035c -> T030 -> T031-UNIFIED-CORRECTION -> T032 -> T033 -> T034 -> T036 -> T037.
**Reasoning**: T035a (Manipulation Check) must run first. If it fails, the pipeline halts. T035b (Power) and T035c (Cognitive Load) run next to provide context. T030 (Omnibus + Contrasts) runs if Manipulation Check passes. T031-UNIFIED-CORRECTION computes pairwise comparisons and unified correction.

- [ ] T029 [P] Implement data cleaning pipeline in `code/analysis/data_cleaning.py` (handle missing values, flag attention check failures).

- [ ] T030 [US2] Implement One‑Way ANOVA and **Planned Directional Contrasts** in `code/analysis/contrasts.py`. Use orthogonal contrast vectors `[1, -1, 0]` (High vs. Low) and `[0.5, 0.5, -1]` ((High+Low) vs. Control). **Crucially, compute and output the Omnibus ANOVA result (F-stat, p-value, df) in a machine-readable format (`results/omnibus_anova.json` with keys `f_stat`, `p_value`, `df`).** **Execute planned directional contrasts regardless of the Omnibus result.** Output summary tables with t-statistics, p-values, df for contrasts.
 **Dependency**: T029, T035a (if passed), T035c.

- [ ] T031-UNIFIED-CORRECTION [US2] [FR-005] Implement **Tukey HSD** for pairwise comparisons AND **Holm-Bonferroni Unified Correction** in `code/analysis/pairwise_tukey.py`.
 **Requirement**: Compute all pairwise comparisons (High vs. Low, High vs. Control, Low vs. Control) using Tukey HSD method. **Also compute Holm-Bonferroni correction for the unified set of 5 tests (2 planned contrasts + 3 pairwise comparisons) as the primary method for family-wise error control.**
 **Logic**:
 1. Read `results/omnibus_anova.json` (from T030). **Explicitly check for the key `p_value` (float).**
 2. If `p_value` > 0.05, **halt** post-hoc tests (Tukey) and report null result, but **do not halt** planned contrasts (already run in T030).
 3. If Omnibus is significant, compute all pairwise comparisons using Tukey HSD.
 4. Extract **raw p-values** from T030 (contrasts) and this task (pairwise).
 5. Apply **Holm-Bonferroni correction** to the unified set of 5 raw p-values.
 6. Output summary tables with raw p-values, Tukey-adjusted p-values, and **Holm-Bonferroni adjusted p-values** to `results/tukey_pairwise.json` and `results/unified_correction.json`. **Explicitly mark Holm-Bonferroni as the primary correction method in the output.**
 **Dependency**: T030.

- [ ] T032 [US2] Implement Cohen's d effect size calculation in `code/analysis/effect_sizes.py` for all pairwise comparisons.
 **Dependency**: T031-UNIFIED-CORRECTION.

- [ ] T033 [US2] Create synthetic data generator in `code/analysis/synthetic_data.py` for pipeline testing.

- [ ] T034 [US2] Integrate all steps into `code/analysis/run_analysis.py`.

- [ ] T036 [P] Contract test for analysis output schema (`tests/contract/test_analysis_output.py`).

- [ ] T037 [P] Unit test for contrast calculation logic using synthetic data (`tests/unit/test_contrasts.py`).

---

## Phase 5: User Story 3 - Methodological Robustness & Sensitivity Reporting (Priority: P3)

**Goal**: Generate reports including power analysis, multiple‑comparison corrections, and sensitivity analysis.

- [ ] T038 [US3] Implement sensitivity analysis in `code/analysis/sensitivity.py`.
 **Requirement**: Sweep participant exclusion thresholds defined in `code/analysis/config.yaml` (`sensitivity_config`) OR CLI arguments (T008-CLI-EXPOSE).
 **Logic**:
 1. Load `sensitivity_config` from `code/analysis/config.yaml` (merged from defaults and user overrides) OR CLI arguments.
 2. **Verify** that `docs/protocol.md` and `code/analysis/config.yaml` exist before proceeding.
 3. Verify ranges match those listed in `docs/protocol.md` (generated by T042) or are valid user overrides.
 4. Iterate over each threshold type (attention pass rate, straight‑lining, adherence cutoff, trust outlier) using the start‑end‑step values defined in the protocol.
 5. For each sweep, re‑run primary analysis and record `p_value_primary` and `effect_size_primary`.
 **Output**: CSV `results/sensitivity_sweep.csv` with columns `threshold_type`, `threshold_value`, `p_value_primary`, `effect_size_primary`.
 **Dependency**: T030, T031-UNIFIED-CORRECTION, T042, T008, T008-VALIDATE, T008-CLI-EXPOSE.

- [ ] T038b [US3] Implement sensitivity analysis reporting in `code/analysis/report.py`.
 **Requirement**: Append a "Sensitivity Analysis" section to `docs/report.md` summarizing stability across sweeps.
 **Dependency**: T038.

- [ ] T039 [US3] Implement final report generation in `code/analysis/report.py`.
 **Requirement**: Compile ANOVA, contrasts, post‑hoc, effect sizes, pre‑study power (`research/power_calculation.json`), and sensitivity analysis.
 **Power Limitation Handling**: Read `results/power_status.json` (from T035b); if `power_status` is "insufficient", append a "Limitations" section stating "Limitation: Insufficient Power" with achieved vs target power.
 **Output**: `docs/report.md`.
 **Dependency**: T002, T002b-REPORT, T034, T038, T038b, T035a, T035b.

- [ ] T040 [US3] Add null result handling logic in `code/analysis/report.py` (explicitly report null findings and observed effect sizes).

- [ ] T041 [P] Unit test for sensitivity sweep logic (`tests/unit/test_sensitivity.py`).

---

## Phase 6: Polish & Cross‑Cutting Concerns

- [ ] T043 [P] Create GitHub Actions workflow `.github/workflows/experiment.yml` to run analysis on `data/processed/`.

- [ ] T044 [P] Code cleanup and refactoring for type hints and docstrings (Google style). Run `pyright` and ensure zero errors.

- [ ] T045 [P] Add validation scripts to verify `participant.schema.yaml` compliance against `data/raw/` exports.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Pre-Phase 0 (Gates)**: T000-GATE-METADATA. **CRITICAL**: If this fails, project halts. T000-HUMAN-SOURCE requires human input.
- **Phase 0 (Research)**: T000-GATE-METADATA -> T000-HUMAN-SOURCE -> T000-GATE-ITEMS-AUTO -> T008-init-std -> T042 -> T001a-1 -> T001a-2 -> T001b-1 -> T001b-2 -> T010c -> T010b-auto -> T011 -> T007g -> T002 -> T002b-REPORT -> T003-1 -> T008 -> T008-VALIDATE -> T008-CLI-EXPOSE. **Note**: T010c, T010b-auto, T011, and T007g are **REQUIRED** for the transition to Phase 1 and Phase 2. T008 must run AFTER T002 to access sample size. **Parallelism**: T002 and T007g can run in parallel after their respective prerequisites.
- **Phase 1 (Setup)**: Depends on Phase 0 completion. Tasks T004, T005, T006, T010, T009, T012, T017i, T017h, T015, T016 can run in parallel as they depend only on T004 and T000-GATE-METADATA/T000-HUMAN-SOURCE/T000-GATE-ITEMS-AUTO where applicable. **Order within Phase 1**: T004 -> T010 -> T009 -> T012 -> T017i -> T017h.
- **Phase 2 (Foundational)**: Depends on Phase 0 (including T010b-auto/T011/T007g) and Phase 1 completion. **BLOCKS all user stories**.
- **Phase 3 (US1)**: Depends on Phase 2 completion. T024b execution is additionally blocked by T007g completion.
- **Phase 4 (US2)**: Depends on Phase 2 completion. **Strict Sequence**: T035a -> T035b -> T035c -> T030 -> T031-UNIFIED-CORRECTION.
- **Phase 5 (US3)**: Depends on Phase 4 completion AND T042 (Protocol) completion. Relies on US2 outputs (ANOVA, post-hoc) for sensitivity sweeps and post-hoc power.
- **Phase 6 (Polish)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **CRITICAL**: Must be completed before data collection begins. **Execution Note**: T024b runtime requires T007g.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Can run on synthetic data independently of US1 completion, but requires US1 data schema.
- **User Story 3 (P3)**: Can start ONLY AFTER Phase 4 (US2) completion AND T042 (Protocol) completion. Relies on US2 outputs (ANOVA, post-hoc) for sensitivity sweeps and post-hoc power.

### Within Each User Story

- Implementation MUST be written before tests (unless TDD explicitly requested).
- Models before services.
- Services before endpoints.
- Core implementation before integration.
- Story complete before moving to next priority.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel (within Phase 2).
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel.
- Models within a story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.

---

## Parallel Example: User Story 1

```bash
# Launch interface implementations for User Story 1 together:
Task: "Implement High Agency condition interface in code/experiment/app.py"
Task: "Implement Low Agency condition interface in code/experiment/app.py"
Task: "Implement Control condition interface in code/experiment/app.py"

# Launch tests for User Story 1 together (after implementation):
Task: "Unit test for randomization logic in code/experiment/tests/test_randomization.py"
Task: "Integration test for session flow in code/experiment/tests/test_session_flow.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Pre-Phase 0: Gates (T000-GATE-METADATA, T000-HUMAN-SOURCE, T000-GATE-ITEMS-AUTO).
2. Complete Phase 0: Research & Validation (Includes T008-init-std, T042, T001a, T001b, T010c, T010b, T011, T007g, T002, T002b-REPORT, T008, T008-VALIDATE, T008-CLI-EXPOSE).
3. Complete Phase 1: Setup.
4. Complete Phase 2: Foundational (CRITICAL - blocks all stories).
5. Complete Phase 3: User Story 1.
6. **STOP and VALIDATE**: Test User Story 1 independently (run pilot with synthetic or real participants).
7. Deploy experiment interface for recruitment.

### Incremental Delivery

1. Complete Pre-Phase 0 + Phase 0 + Setup + Foundational → Foundation ready.
2. Add User Story 1 → Test independently → Deploy experiment interface (MVP!).
3. Add User Story 2 → Test on synthetic data → Ready for real data analysis.
4. Add User Story 3 → Test robustness → Generate final report.
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Pre-Phase 0 + Phase 0 + Setup + Foundational together.
2. Once Foundational is done:
 - Developer A: User Story 1 (Experiment Interface).
 - Developer B: User Story 2 (Analysis Core).
 - Developer C: User Story 3 (Robustness & Reporting).
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies.
- [Story] label maps task to specific user story for traceability.
- Each user story should be independently completable and testable.
- Commit after each task or logical group.
- Stop at any checkpoint to validate story independently.
- **Data Integrity**: Ensure `data/raw/` is never modified in-place. All cleaning must write to `data/processed/`.
- **Compute Feasibility**: All statistical tasks (ANOVA, contrasts, sensitivity) are CPU-tractable and fit within GitHub Actions free-tier limits.
- **Fabrication Guard**: Do NOT use `random.*` to generate input data for the analysis pipeline unless explicitly testing with synthetic data generators. Real analysis must use real CSV exports from `data/raw/`.
- **Gate Tasks**: T000-GATE-METADATA (Reference Validation), T000-HUMAN-SOURCE (Human Sourcing), and T000-GATE-ITEMS-AUTO (Automated Verification) are mandatory gates. T034 is now a reporting step, not a gate.
- **Critical Dependencies**: T002 must complete after T001a-2 and T001b-2. T008 depends on T042 and T002 (sample size). T024 depends on T010b-auto, T011, T000-GATE-METADATA, T000-HUMAN-SOURCE, T000-GATE-ITEMS-AUTO. T035a/b/c depend on T026 and T002. T030 depends on T035a (pass) and T035c. T031-UNIFIED-CORRECTION depends on T030. T038 depends on Phase 4, T042, and T008-CLI-EXPOSE. T039 depends on T002, T002b-REPORT, Phase 4, T038, T038b, and T035a/b.
- **Execution Flow**: T010c/T010b-auto/T011/T007g are prerequisites for Phase 2. T007g is a prerequisite for T024b execution. T042 is a prerequisite for T038 execution. T008 is a prerequisite for T038 (via config.yaml) and must run after T002. T008-init-std is the source of truth for T042. T000-GATE-METADATA is the source of truth for item metadata. T000-HUMAN-SOURCE is the source of truth for item text (via file). T000-GATE-ITEMS-AUTO verifies the text. T008-CLI-EXPOSE implements user configuration for T038.
- **Correction Strategy**: Holm-Bonferroni is the primary correction method for the unified set of 5 tests (2 contrasts + 3 pairwise). Tukey HSD is reported for pairwise comparisons but is secondary for family-wise error control.
- **Planned Contrasts**: Planned directional contrasts (T030) are executed regardless of Omnibus ANOVA significance. Post-hoc tests (Tukey) are halted if Omnibus is non-significant.