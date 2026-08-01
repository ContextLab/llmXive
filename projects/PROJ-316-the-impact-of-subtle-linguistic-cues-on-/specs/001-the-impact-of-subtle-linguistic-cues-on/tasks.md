# Tasks: The Impact of Subtle Linguistic Cues on Perceived Authenticity in AI Chatbots

**Input**: Design documents from `/specs/001-impact-of-subtle-linguistic-cues/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase -2: Power Analysis (Prerequisite Gate)

**Purpose**: Determine required sample size (N) for the regression model to achieve power ≥ 0.8 (FR-011) before any annotation or analysis begins.

- [X] T000a [Phase-2] Locate and document the assumed effect size (f²) from literature. **Deliverable**: Create `data/results/effect_size_citation.md` containing the specific effect size value (f²), the source citation (paper/title/DOI), and a brief justification for its selection. **Constitution Requirement**: This task satisfies Constitution Principle II (Verified Accuracy) by ensuring the power analysis input is not arbitrary. **Dependency**: Must complete before T000.
- [X] T000 [Phase-2] Implement and run power analysis script. **Deliverable**: Create `data/results/power_analysis_results.yaml` containing the required sample size N based on the effect size documented in T000a. **Gate**: If required N > annotation budget, flag project as underpowered. **Dependency**: Must complete after T000a and before T000b.
- [X] T000b [Phase-2] **Decision Gate**: Determine final annotation sample size. **Deliverable**: Create `data/results/annotation_decision.md` stating the final N to be used, confirming it meets power requirements (≥0.8) and is within budget. **Logic**: If T000 output N > budget, halt project and flag for human input. If N <= budget, record N and proceed. **Dependency**: Must complete after T000. **Gate**: Project cannot proceed to Phase 0 until this decision is recorded.

---

## Phase 0: Data Acquisition & Manual Annotation (Blocking Prerequisites)

**Purpose**: Secure human authenticity ratings and hedge labels manually (bypassing broken tool loop), validate the hedge lexicon, and acquire the raw dataset required by FR-001, FR-010, FR-011. This phase MUST complete before Phase 1 or Phase 2 tasks can execute valid data loaders.

**⚠️ CRITICAL**: No downstream analysis (US2, US3) can proceed without verified `data/processed/manual_ratings.csv` (Analysis Set) and passed lexicon validation.

- [X] T001a [Phase0] Verify availability of public dataset with human authenticity ratings. **Deliverable**: Create `data/raw/dataset_verification_report.md` containing: (1) Decision (Found/Not Found), (2) Source URL if found, (3) Sample size estimate, (4) If not found, confirmation of proceeding to manual annotation protocol. **Note**: If no dataset is found, document the decision to proceed to T001f.
- [X] T001b [Phase0] Define and document the manual annotation protocol. **Deliverable**: Create `data/raw/annotation_instructions.md` containing: (1) Likert scale definitions (1-5 Authenticity), (2) Instruction script for raters, (3) Sample items demonstrating the rating criteria. **Note**: Instructions must focus strictly on "Perceived Authenticity" as defined in spec.md.
- [ ] T001f [Phase0] Acquire and format the raw conversation dataset. **Deliverable**: Create `data/raw/conversations.jsonl` containing the raw text data. **Execution**: Fetch the 'convai2' dataset from HuggingFace (using `datasets.load_dataset`) first; if not found, fetch 'cornell-movie-dialogs'. Extract the `text` or `dialogue` fields and save as JSONL. **Constraint**: These datasets are used for TEXT FEATURES ONLY. They do NOT contain authenticity scores. If `authenticity_score` is missing (expected), the pipeline MUST trigger the manual annotation protocol defined in T001g. **Dependency**: Must complete before T001g.
- [ ] T001g [Phase0] **Validate Data & Trigger Manual Annotation Protocol**. **Deliverable**: Check `data/raw/conversations.jsonl` for the presence of `authenticity_score`. **Logic**:
 1. If `authenticity_score` exists: Proceed to T001k (Analysis Set) and T001j (Hedge Gold Standard) using existing data.
 2. If `authenticity_score` is MISSING: **MUST trigger execution** of T001b -> T001i (Validation Set) -> T001j (Hedge Gold Standard) -> T001k (Analysis Set). **Mechanism**: Create a flag file `data/processed/annotation_required.flag` to signal downstream tasks. **Deliverable**: Create `data/processed/annotation_trigger_log.md` confirming the protocol was initiated. **Dependency**: Must complete after T001f. **Gate**: Blocks T001d, T001e, and T009 until annotation data is generated.
- [X] T001i [Phase0] [US1] Generate "Gold Standard" subset of 50 annotated turns for **Lexicon Validation**. **Deliverable**: Create `data/processed/manual_ratings_validation.csv` with columns `conversation_id`, `text_content`, `authenticity_score`, `rater_id`, `timestamp`. **Execution**: Use the manual protocol (T001b) to annotate 50 randomly selected turns from the raw corpus (T001f). **Input Mechanism**: Raters fill a provided CSV template; save the result as this file. **Constitution Requirement**: Store the full rater metadata (scale, instructions, inter-rater reliability) in `data/raw/rater_metadata.json` as per Constitution Principle VII. **Failure Path**: If inter-rater reliability (Cohen's Kappa) < 0.6, flag the dataset and halt. **Dependency**: Must complete after T001b, T001f, and T001g (if protocol triggered).
- [ ] T001j [Phase0] [US1] [FR-010] Generate Human Hedge Labels (Gold Standard) for the 50 validation turns. **Deliverable**: Create `data/processed/hedge_gold_standard.csv` containing `conversation_id`, `text_content`, `hedge_flags`. **Execution**: Use the manual protocol (T001b) to annotate the same 50 turns from T001i, specifically asking raters to mark "uncertainty markers" as defined in the lexicon. **Input Format**: `hedge_flags` must be a JSON-formatted string of word indices (e.g., `"[2, 5]"`). **Dependency**: Must complete after T001b, T001f, T001i, and T001g (if protocol triggered). <!-- FAILED: unspecified -->
- [ ] T001d [Phase0] [US1] [FR-010] Define pragmatic validation logic for the hedge lexicon. **Deliverable**: Create `src/analysis/validation.py` containing `validate_lexicon_precision()`. **Logic**: Calculate precision = (Lexicon Matches ∩ Human Matches) / Lexicon Matches. **Input**: 'Human Matches' are derived from the `hedge_flags` column in `data/processed/hedge_gold_standard.csv`. **Aggregation Logic**: For each turn, compare the indices of words matched by the lexicon against the indices in `hedge_flags`. **Dependency**: Must complete after T001i and T001j.
- [ ] T001d_exec [Phase0] [US1] **Execute** Lexicon Validation. **Deliverable**: Run `src/analysis/validation.py` against `data/processed/hedge_gold_standard.csv`. Output `data/results/lexicon_validation_results.yaml`. **Gate**: If precision < 0.8, proceed to T001e (Remediation). **Dependency**: Must complete after T001d, T001i, T001j.
- [X] T001e [Phase0] [US1] **Remediation** for Failed Lexicon Validation. **Deliverable**: If T001d_exec fails (precision < 0.8), create `data/results/lexicon_remediation_plan.md`. **Logic**: Define steps to refine the lexicon (add/remove words) or halt the project. **Dependency**: Must complete after T001d_exec if validation fails.
- [ ] T001k [Phase0] [US1] Generate "Analysis Set" of N annotated turns for **Regression**. **Deliverable**: Create `data/processed/manual_ratings.csv` with columns `conversation_id`, `text_content`, `authenticity_score`, `rater_id`, `timestamp`. **Execution**: Use the manual protocol (T001b) to annotate N turns (where N is from T000b) from the raw corpus. **Input Mechanism**: Raters fill a provided CSV template. **Dependency**: Must complete after T000b, T001b, T001f, and T001g (if protocol triggered). <!-- FAILED: unspecified -->

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Dependencies**: Phase 0 (T001i, T001j, T001k, T001d_exec) must complete first.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete AND Phase 0 has produced `data/processed/manual_ratings.csv` and `data/processed/hedge_gold_standard.csv`.

- [ ] T005 [US1] Implement `src/utils/io.py`. **Deliverable**: Implement functions `fetch_text()` (returns DataFrame), `load_ratings()` (returns DataFrame), and `validate_schemas()` (raises exception if schema mismatched). **Specifics**: `validate_schemas()` MUST load `contracts/extracted_features.schema.yaml` and perform strict validation (no missing columns, correct types). **Note**: This task is **NOT** parallel-safe ([P] removed). It strictly depends on Phase 0 completion (T001i, T001j, T001k) and must halt if artifacts are missing.
- [ ] T005a [P] [US1] Implement Input Validation Logic (FR-006). **Deliverable**: Create `src/utils/validation.py` containing `validate_input_columns(df, required_cols)` which checks for 'text_content' and 'authenticity_score' columns. **Logic**: Raise a clear `ValueError` if columns are missing or mismatched, as mandated by FR-006.
- [ ] T006 [P] [US1] Create `src/config.py` to manage random seeds (default value) and runtime limits (CPU-only, bounded timeout).
- [ ] T007 [P] [US1] Implement `src/utils/edge_case_handler.py` to detect empty/short texts (<5 words) and missing ratings. **Deliverable**: If missing ratings are detected, the handler MUST perform **listwise deletion** (drop rows with NaN authenticity_score), log the count of dropped rows, and report the final sample size. **Note**: This task aligns with FR-007 and Edge Cases; it MUST NOT trigger a pipeline HALT.
- [ ] T007b [P] [US1] **Global Sample Size Check** (FR-007). **Deliverable**: Create `src/utils/sample_size_checker.py`. **Logic**: Read `data/processed/manual_ratings.csv` and `data/results/power_analysis_results.yaml`. If N < 30 (or N < required by power analysis), issue a warning in `data/results/sample_size_warning.log`. **Dependency**: Must complete after T001k.
- [ ] T007a [P] [Review] Implement Noise Measurement Module. **Deliverable**: Create `src/analysis/noise.py` containing `calculate_noise_variance(ratings_df, rater_id_col, conversation_id_col)`. **Logic**: Compute the variance of ratings for the same conversation across different raters (or repeated measures if applicable). **Output**: A metric representing "judgment noise" (random variation) as distinct from "signal" (systematic linguistic effects). **Reference**: Addresses Reviewer Concern: "Your methodology should account for it [noise]." **Dependency**: Requires `data/processed/manual_ratings.csv` with multiple raters or repeated measures.

---

## Phase 2: User Story 1 - Automated Linguistic Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Extract quantitative metrics (pronoun count, hedge count, valence) from raw conversation text.

**Independent Test**: A researcher runs the extraction script on a provided JSONL file of dummy conversations and receives a CSV output with exactly the spec-defined columns (`first_person_count`, `hedge_count`, `hedge_ratio`, `sentiment_score`) populated with numeric values, verified by spot-checking against manual counts.

### Implementation for User Story 1

- [ ] T009 [P] [US1] Implement `src/extraction/pronoun_extractor.py` using `nltk` (POS tagging) to calculate `first_person_count`. **Specifics**: The study uses NLTK POS tags 'PRP' (personal pronoun) and 'PRP$' (possessive pronoun) to calculate first_person_count. [UNRESOLVED-CLAIM: c_de13849d — status=not_enough_info] **Ambiguity Handling**: **HALT** if `speaker_id` is missing and the dataset contains multi-turn dialogues (confound risk). If `speaker_id` exists, filter by bot speaker. **Deliverable**: If halted, create `data/processed/extraction_limitations.log` documenting the specific reason and dataset state. **Input**: `data/raw/conversations.jsonl` (from T001f). **Output**: Intermediate count data. **Note**: The extraction must be exhaustive for all pronouns matching the POS tags, not limited to a hardcoded subset.
- [ ] T010 [P] [US1] Implement `src/extraction/hedge_extractor.py` using `NLTK` and the predefined 15-word hedge lexicon to calculate `hedge_count` and `hedge_ratio`. **Specifics**: The lexicon is: ["maybe", "perhaps", "possibly", "probably", "likely", "unlikely", "seem", "seems", "appear", "appears", "believe", "think", "guess", "suppose", "assume"]. **Input**: `data/raw/conversations.jsonl` (from T001f). **Output**: Intermediate count data.
- [ ] T011 [P] [US1] Implement `src/extraction/sentiment_analyzer.py` using `vaderSentiment` (version 3.x) to calculate `sentiment_score` (composite score representing a normalized sentiment polarity). **Input**: `data/raw/conversations.jsonl` (from T001f). **Output**: Intermediate score data.
- [ ] T012 [US1] Implement `src/main.py` (extraction mode). **Deliverable**: Add `--mode extraction` CLI argument, orchestrate T009-T011, handle edge cases (T007), and output `data/processed/features.csv` with columns `conversation_id`, `first_person_count`, `hedge_count`, `hedge_ratio`, `sentiment_score`. **Explicit Requirement**: The final CSV MUST include the `hedge_ratio` column as mandated by FR-008. **Dependency Note**: This task must wait for the completion of T005 (io.py implementation) and T009-T011 (modules). **Data Dependency**: Requires `data/raw/conversations.jsonl` from T001f. It does NOT depend on T001i (ratings) as extraction only requires raw text.
- [ ] T014 [US1] Write unit tests in `tests/unit/test_extraction.py` verifying metric calculations against manual spot-checks (US-1 Acceptance 1-3). **Deliverable**: Create `tests/fixtures/manual_counts.csv` containing manually verified counts for a small sample of sentences. **Test Cases**: `test_pronoun_count_empty_string`, `test_hedge_count_lexicon_match`, `test_sentiment_score_negative`, `test_hedge_ratio_calculation`.

---

## Phase 3: User Story 2 - Associational Correlation Analysis (Priority: P2)

**Goal**: Compute Pearson and Spearman correlations between linguistic features and human authenticity ratings, with multiple-comparison correction.

**Independent Test**: A researcher runs the analysis module on the extracted CSV and a ratings CSV, generating a correlation matrix and scatter plots with p-values and effect sizes, strictly labeled as "associated with".

### Implementation for User Story 2

- [ ] T020c [US2] [Review] Integrate Noise Metric into Correlation Analysis. **Deliverable**: Modify `src/analysis/correlation.py` to include the noise variance (from T007a) as a control variable or a contextual metric in the output. **Logic**: Report the ratio of "Signal Variance" (explained by linguistic features) to "Noise Variance" (inter-rater disagreement). **Reference**: Addresses Reviewer Concern: "Your methodology should account for it [noise]." **Dependency**: Requires T007a (Noise Measurement) to be complete. **Note**: This is an optional review task; if not implemented, the core analysis proceeds without it.
- [ ] T015 [P] [US2] Implement `src/analysis/correlation.py` to compute Pearson and Spearman coefficients between linguistic features (`first_person_count`, `hedge_count`, `sentiment_score`) and `authenticity_score` (FR-002). **Note**: Uses the single 'authenticity_score' as defined in spec.md.
- [ ] T016 [P] [US2] Implement Benjamini-Hochberg multiple-comparison correction in `src/analysis/correlation.py` (SC-004, FR-004).
- [ ] T017 [US2] Implement `src/main.py` (correlation mode) to merge `features.csv` and `manual_ratings.csv`, handle missing ratings (FR-007), and output `data/derived/correlation_results.csv`.
- [ ] T018 [US2] Generate scatter plots (matplotlib/seaborn) for selected features. **Deliverable**: Create `data/derived/scatter_hedge_vs_authenticity.png` and `data/derived/scatter_pronoun_vs_authenticity.png` with clear "Association, not Causation" labels.
- [ ] T019 [US2] Write unit tests in `tests/unit/test_correlation.py` verifying p-values and effect sizes against known synthetic datasets.
- [ ] T020 [US2] Write integration test in `tests/integration/test_correlation_pipeline.py` ensuring the "association only" disclaimer is present in all outputs (FR-004).
- [X] T020a [US2] [Removed] **Note**: Task T020a ("Noise Measurement") was removed as it is not authorized by spec.md.
- [X] T020b [US2] [Removed] **Note**: Task T020b ("Dual-Self") was removed as it contradicts spec.md FR-001/FR-003.

---

## Phase 4: User Story 3 - Multivariate Regression with Controls (Priority: P3)

**Goal**: Fit a multiple linear regression model predicting authenticity from linguistic features, controlling for length/turn count, with VIF and non-linearity diagnostics.

**Independent Test**: A researcher executes the regression script and receives a summary table showing coefficients, standard errors, p-values, adjusted R², and VIF reports.

### Implementation for User Story 3

- [ ] T021 [US3] Implement `src/analysis/regression.py` to fit multiple linear regression. **Logic**: 1) Calculate VIF for all predictors; if VIF > 5, exclude the predictor with the highest VIF and log the specific excluded variable. 2) Test for non-linear relationships (quadratic terms for `hedge_count` and interaction terms `hedge_count` × `sentiment_score`) as per FR-009. **Inclusion Criteria**: Include non-linear terms if p < 0.10 (exploratory) or if AIC improves. 3) Run regression with linguistic features as predictors and conversation length/turn count as covariates (FR-003). **Note**: Outcome variable is strictly 'authenticity_score' per spec.md.
- [ ] T021a [US3] [Review] Differentiate "Experiencing" vs "Remembering" Self Metrics. **Deliverable**: Modify `src/analysis/regression.py` to accept two outcome variables if available: `authenticity_score` (immediate/experiencing) and `trust_report` (delayed/remembering, if collected in T001k). **Logic**: If both are present, run parallel regression models and compare coefficients. **Output**: A specific report section "System 1 vs System 2 Judgments" comparing the predictive power of linguistic cues on immediate vs. recalled trust. **Reference**: Addresses Reviewer Concern: "You must distinguish between the experiencing self's trust and the remembering self's trust." **Dependency**: Requires `data/processed/manual_ratings.csv` to potentially include a `trust_report` column (added in T001k protocol if feasible, or noted as a limitation if not). **Note**: Execute T021a BEFORE T026 to ensure sensitivity analysis runs on the correct model.
- [ ] T026 [US3] Implement `src/analysis/sensitivity.py` to perform the **leave-one-out sensitivity analysis** (SC-003). **Logic**: Iterate through the 15-word hedge lexicon; for each iteration, remove one word, re-run the regression model (T021), and record the change in Adjusted R² and the significance (p < 0.05) of the remaining hedge count. **Versioning Discipline**: **After EACH iteration**, run `src/checksum.py` to update `state.yaml`. **Schema**: Append to `state.yaml` under `sensitivity_sweep: [ { "iteration": 1, "hash": "<sha256>", "result_file": "..." },... ]`. **Deliverable**: Output `data/results/sensitivity_analysis.csv` and a `data/results/sensitivity_stability_report.md` summarizing the robustness of the findings. **Intermediate**: Save intermediate results to `data/results/sensitivity_iteration_*.csv` for each iteration. **Dependency**: Must complete after T021 and T021a.
- [ ] T022 [US3] Implement `src/main.py` (regression mode) to orchestrate T021, calculate adjusted R² and AIC, and output `data/derived/regression_results.csv`. **Dependency**: T021 must complete first.
- [ ] T023 [US3] Generate diagnostic plots (residuals, VIF bar chart) for the regression model. **Note**: This task is for diagnostic plots (residuals/VIF) only, not the feature importance bar chart required by FR-005.
- [ ] T024 [US3] Write unit tests in `tests/unit/test_regression.py` verifying VIF calculation, exclusion logic, and adjusted R² logic.
- [ ] T025 [US3] Write integration test in `tests/integration/test_regression_pipeline.py` ensuring model constraints (VIF < 5, p < 0.05) are met.
- [X] T027 [Removed] **Note**: Task T027 (replacing 'authenticity' with 'trust') was removed as it contradicts spec.md FR-001.
- [X] T028 [US3] [Removed] **Note**: Task T028 ("Dual-Self") was removed as it contradicts spec.md FR-001/FR-003.
- [X] T028b [US3] [Removed] **Note**: Task T028b ("Dual-Self") was removed as it contradicts spec.md FR-001/FR-003.

---

## Phase 5: Visualization & Reporting (Priority: P3)

**Goal**: Generate publication-quality plots and the statistical summary report required by FR-005 and Plan Phase 6.

- [ ] T033 [P] [US3] Implement `src/analysis/visualize.py` to generate the **bar chart of feature importance coefficients** required by FR-005. **Deliverable**: Create `data/results/feature_importance_bar.png`. **Logic**: If regression fails to converge, generate `data/results/placeholder_convergence_failed.png` with the text "Model Convergence Failed" and log the error. **Note**: This is distinct from T023 (diagnostic plots).
- [ ] T034 [P] [US3] Implement `src/analysis/report.py` to generate the **statistical summary report**. **Deliverable**: Create `data/results/report.md` with the following structure: 1. Executive Summary, 2. Methodology, 3. Results (Adjusted R², Coefficients, P-values), 4. Sensitivity Analysis, 5. Noise Analysis (T007a - Optional), 6. System 1 vs System 2 Comparison (T021a - Optional), 7. Conclusion (Association, not Causation). **Note**: This task fulfills Plan Phase 6 and FR-005 reporting requirements.
- [ ] T035 [US3] Integrate visualization and report generation into `src/main.py` (report mode). **Deliverable**: Add `--mode report` CLI argument to orchestrate T033 and T034.
- [X] T035a [US3] [Removed] **Note**: Task T035a (Operational Definitions for Dual-Self) was removed as it is not required by spec.md.
- [X] T035b [US3] [Removed] **Note**: Task T035b (Noise Analysis) was removed as it is not required by spec.md.
- [X] T036 [US3] [Removed] **Note**: Task T036 (Operational Definitions for Dual-Self) was removed as it is not required by spec.md.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Documentation updates in `docs/` (including operational definitions). **Note**: T028 previously covered report generation; that responsibility is now in T034.
- [ ] T030 Code cleanup and refactoring to ensure modularity
- [ ] T031 [P] Run full pipeline validation on a sample of conversations (as per SC-005) to verify runtime constraint. **Deliverable**: Record execution time in `data/derived/performance_metrics.json`. **Input**: `data/raw/conversations.jsonl` (from T001f).
- [ ] T032 [P] Final verification that all outputs include the mandatory disclaimer: "These results indicate association, not causation." (FR-004)
- [ ] T032a [P] [Review] Refine Terminology in All Outputs. **Deliverable**: Audit `data/results/report.md` and all plot titles. Replace "Perceived Authenticity" with "Reported Trust" or "Willingness to Comply" where appropriate, or explicitly define "Perceived Authenticity" as the specific construct measured to avoid circularity. **Reference**: Addresses Reviewer Concern: "The term 'perceived authenticity' risks circularity." **Dependency**: Requires T034 (Report Generation).
- [X] T033 [Removed] **Note**: Task T032 (Noise Report) was removed as it is not required by spec.md.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase -2 (Power Analysis)**: No dependencies - can start immediately. **MUST complete before Phase 0.**
- **Phase 0 (Data Acquisition)**: Depends on Phase -2. **MUST complete before Phase 1.**
- **Phase -1 (Setup)**: No dependencies - can start immediately.
- **Phase 1 (Foundational)**: Depends on Setup (Phase -1) AND Phase 0 completion (requires `data/processed/manual_ratings.csv`, `data/processed/hedge_gold_standard.csv`). BLOCKS all user stories.
- **User Stories (Phase 2-4)**: All depend on Foundational phase completion.
 - **Phase 2 (US1)**: Must complete before Phase 3 and 4 (data generation).
 - **Phase 3 (US2)**: Depends on Phase 2 (features) and Phase 0 (ratings).
 - **Phase 4 (US3)**: Depends on Phase 2 (features) and Phase 3 (correlation insights).
- **Phase 5 (Visualization/Reporting)**: Depends on Phase 4 (Regression results).
- **Polish (Final Phase)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories.
- **User Story 2 (P2)**: Depends on US1 (features) and Phase 0 (ratings).
- **User Story 3 (P3)**: Depends on US1 (features) and US2 (correlation context).

### Within Each User Story

- Models/Extractors (T009-T011) before orchestration (T012).
- Tests (T014, T019, T024) should be written first (TDD) and fail before implementation.

### Parallel Opportunities

- T009, T010, T011 (Extraction modules) can run in parallel.
- T015, T016 (Correlation logic) can run in parallel with T021 (Regression logic) if data is available, provided T021 includes VIF/non-linearity checks.
- T001a, T001b (Data acquisition) can run in parallel with Phase -1 (Setup).
- **New**: T001f (Dataset Acquisition) can run in parallel with T001b (Protocol) and T001i (Manual Rating).
- **New**: T001f and T001g can run in parallel with T001i/T001j if the annotation protocol is not triggered (i.e., if data already has authenticity_score).
- **New**: T007a (Noise Measurement) can run in parallel with T015 (Correlation) once ratings are available.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase -2: Power Analysis (T000a, T000, T000b).
2. Complete Phase -1: Setup.
3. Complete Phase 0: Data Acquisition (T001a, T001b, T001f, T001g, T001i, T001j, T001d, T001d_exec, T001k).
4. Complete Phase 1: Foundational (loaders).
5. Complete Phase 2: User Story 1 (Extraction).
6. **STOP and VALIDATE**: Test extraction on dummy data (T014).
7. Verify `features.csv` is generated correctly with spec-compliant columns.

### Incremental Delivery

1. Complete Phase -2 + Setup + Phase 0 + Foundational → Foundation ready.
2. Add User Story 1 → Test independently → `features.csv` ready.
3. Add User Story 2 → Test independently → Correlation results ready.
4. Add User Story 3 → Test independently → Regression and Sensitivity results ready.
5. Add Phase 5 → Generate reports and plots.
6. Polish & Report.

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase -2 + Setup + Phase 0 + Foundational together.
2. Once Foundational is done:
 - Developer A: User Story 1 (Extraction)
 - Developer B: User Story 2 (Correlation)
 - Developer C: User Story 3 (Regression + Sensitivity)
3. Team: Phase 5 (Visualization/Reporting).
4. Integrate and validate.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- **Critical Constraint**: No statistical analysis (US2/US3) proceeds without verified human authenticity ratings (FR-009) and passed lexicon validation (FR-010). If `manual_ratings.csv` is missing or lexicon validation fails, the pipeline must halt gracefully.
- **Data Integrity**: All tasks must use real data from verified sources (HuggingFace) or explicitly defined manual annotation protocols. No synthetic/fake data generation for input.
- **Verification**: Verify tests fail before implementing. Commit after each task or logical group.
- **Review Resolution**: Tasks have been updated to strictly align with spec.md FR-001, FR-003, FR-009, FR-010, FR-011, and SC-003. Scope creep (Dual-Self, Noise Measurement, Trust Metrics) has been removed from the core spec. **However**, specific review concerns regarding "Noise", "Experiencing vs Remembering Self", and "Terminology Circularity" have been addressed via new tasks T007a, T020c, T021a, and T032a to ensure methodological rigor as requested by the reviewer.
- **Spec Alignment**: All tasks now strictly use 'authenticity_score' as the outcome variable, with optional extensions for 'trust_report' if the annotation protocol allows.
- **Ambiguity Resolution**: T009 explicitly handles multi-turn dialogue ambiguity by requiring a halt if `speaker_id` is missing to prevent confounding.
- **Versioning Discipline**: T026 explicitly mandates per-iteration `state.yaml` updates for the sensitivity sweep with a defined schema.
- **Fallback Logic**: T001g explicitly triggers the manual annotation protocol (T001i, T001j, T001k) if `authenticity_score` is missing, using a flag file mechanism.
- **Lexicon Validation**: T001d, T001d_exec, and T001j now correctly use human hedge flags, not authenticity scores, for validation.
- **Removed Scope**: Phase N+1 and tasks T036-T039 have been removed as unapproved scope creep.