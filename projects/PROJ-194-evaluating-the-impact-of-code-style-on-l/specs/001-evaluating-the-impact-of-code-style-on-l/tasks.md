# Tasks: Evaluating the Impact of Code Style on LLM Code Understanding and Generation

**Input**: Design documents from `/specs/001-evaluating-the-impact-of-code-style-on-l/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are included as requested by the specification's "Independent Test" scenarios for each User Story.

**Organization**: Tasks are grouped by User Story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/`, `data/`, `results/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, environment setup, and dependency management for the CPU-only CI runner.

- [ ] T001 Create project structure per `plan.md` (directories: `code/`, `data/`, `results/`, `tests/`, `contracts/`)
- [ ] T002 Initialize `requirements.txt` with CPU-safe versions of `datasets`, `transformers`, `scikit-learn`, `statsmodels`, `black`, `rouge-score`, `codebleu`, `pytest`
- [ ] T003 [P] Configure `pytest` and linting tools (`ruff` or `flake8`) in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, data contracts, and seed management that MUST be complete before any user story.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Define data contracts in `contracts/dataset.schema.yaml` (Base Function), `contracts/style_variant.schema.yaml` (8-way factorial), `contracts/task_result.schema.yaml`, `contracts/statistical_result.schema.yaml`, and `contracts/analysis_output.schema.yaml`
- [ ] T005 Implement `code/validation/verify_accuracy.py` to enforce Constitution Principle II (verify citations, check data URLs, validate schemas) before any inference
- [ ] T006 [P] Implement `code/transform/seed_manager.py` to log `transform_seed` AND the SHA256 hash of the identifier mapping dictionary for every variant generation to ensure reproducibility (Constitution Principle VI)
- [~] T007 Create `code/main.py` entry point with CLI argument parsing for pipeline stages (transform, evaluate, analyze)
- [~] T008 Implement `code/transform/validator.py` to parse generated Python variants and ensure syntax correctness (FR-002) before LLM submission

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Style-Aware Code Transformation (Priority: P1) 🎯 MVP

**Goal**: Systematically transform a base corpus of Python functions into 8 distinct style variants (formatting, naming, commenting) using a controlled, orthogonal design.

**Independent Test**: Run on a sample of functions; verify multiple variants per function, correct application of Black/Minified, Generic/Meaningful, Stripped/Present, and valid Python syntax.

### Tests for User Story 1

- [~] T009 [P] [US1] Unit test for `code/transform/generator.py` verifying 8-way factorial output on a mock function in `tests/unit/test_transform_generator.py`
- [~] T010 [P] [US1] Unit test for `code/transform/generator.py` verifying "strip comments" removes `#` lines and docstrings but preserves logic in `tests/unit/test_transform_comments.py`
- [~] T011 [P] [US1] Unit test for `code/transform/generator.py` verifying "generic naming" replaces identifiers with `var1`, `func2` without syntax errors in `tests/unit/test_transform_naming.py`
- [~] T012 [P] [US1] Integration test: Run full pipeline on 10 sample functions and assert 80 output files exist with valid syntax in `tests/integration/test_us1_full_pipeline.py`

### Implementation for User Story 1

- [~] T013a [US1] Implement `code/transform/formatters/black_formatter.py` to apply Black formatting to Python code
- [~] T013b [US1] Implement `code/transform/formatters/minified_formatter.py` to apply minified formatting (remove whitespace, compact code)
- [~] T014a [US1] Implement `code/transform/renamer/ast_renamer.py` to parse code via AST and replace identifiers with deterministic generic tokens (e.g., `var1`, `func2`)
- [~] T015a [US1] Implement `code/transform/stripper/comment_stripper.py` to remove comments and docstrings from input code while preserving the original docstring for ground truth
- [~] T016a [US1] Implement `code/transform/generator.py` to orchestrate the 2x2x2 factorial design by calling formatters, renamer, and stripper
- [~] T016b [US1] Implement `code/transform/generator.py` to tag each variant with boolean flags: `is_generic_naming`, `is_stripped_comments`, `is_minified`, and specifically `is_semantic_opacity` (true if generic AND stripped)
- [~] T016c [US1] Implement `code/transform/generator.py` to save variants to `data/derived/` with metadata JSON files containing the flags and seeds
- [~] T012a [US1] Implement `code/transform/metrics.py` class to aggregate validation results from T008
- [~] T012b [US1] Implement aggregation logic in `code/transform/metrics.py` to calculate the proportion of successfully generated and syntactically valid style variants
- [~] T012c [US1] Implement recording logic in `code/transform/metrics.py` to save the metric to `results/transformation_success_rate.json` (SC-001)

**Checkpoint**: User Story 1 fully functional; 8 variants generated per function with syntax validation and explicit metadata flags.

---

## Phase 4: User Story 2 - LLM Task Execution & Metric Collection (Priority: P2)

**Goal**: Execute completion, bug detection, and summarization tasks on all variants using a CPU-tractable model (CodeGen-2B) and collect metrics.

**Independent Test**: Run on a set of pre-defined functions with known outputs; verify metrics (Exact Match, CodeBLEU, P/R/F1, ROUGE-L) are calculated correctly and saved to CSV.

### Implementation for User Story 2

- [~] T022 [US2] Implement `code/mutation/generator.py` to load clean variants from `data/derived/variants.json` (generated by US1), clone them, **inject bugs using `code/mutation/mutator.py`** (AST operators: `variable_swap`, `operator_flip`), and save to `data/derived/mutated.json`. Output: List of JSON objects with keys `mutation_type`, `modified_code`, `original_id`.
- [~] T022b [US2] Implement `code/evaluate/dataset_balancer.py` to define the ground truth logic: `is_buggy = True` if the sample contains a `mutation_type` from T022, `is_buggy = False` otherwise.
- [~] T022a [US2] Implement `code/evaluate/dataset_balancer.py` to load `data/derived/baseline.json` (clean) and `data/derived/mutated.json` (from T022), filter variants, and construct a balanced dataset (50/50 clean/mutated) saved to `data/derived/balanced_dataset.csv`. Depends on T022 and T022b.
- [~] T022c [US2] Implement `code/evaluate/config/token_threshold.yaml` to define the config structure for token threshold `T` with `T: null` (placeholder to be updated by empirical findings) (FR-007).
- [~] T024 [US2] Implement `code/evaluate/metrics.py` to calculate Exact Match, CodeBLEU, Precision, Recall, F1, ROUGE-L, and BLEU.
- [ ] T027 [US2] Implement `code/evaluate/metrics.py` to count tokens per variant and store the calculated `token_count` in the `TaskResult` object before saving to CSV (FR-007).
- [ ] T022d [US2] Implement `code/evaluate/metrics.py` to include logic that flags a result as "potentially confounded" if the token count change delta exceeds the threshold `T` defined in T022c. Depends on T027.
- [ ] T023a [US2] Implement `code/evaluate/loader.py` to load CodeGen-2B on CPU with memory-efficient settings
- [ ] T023b [US2] Implement `code/evaluate/retry_logic.py` to handle inference timeouts and implement retry logic with a bounded maximum number of attempts
- [ ] T025a [US2] Implement `code/evaluate/task_prompts.py` to construct prompts for completion, bug detection, and summarization tasks
- [ ] T026 [US2] Implement `code/evaluate/runner.py` to: 1) Load the balanced dataset (from T022a), 2) Execute tasks (completion, bug detection, summarization), 3) Tag samples with `is_semantic_opacity` (using logic from T016b), 4) Log mutation types (from T022), 5) Save intermediate results to `results/metrics_raw.csv` with columns including `token_count`. Depends on T022a.

**Checkpoint**: All LLM tasks executed; metrics collected; mutation types logged; semantic opacity flagged; dataset balanced.

---

## Phase 5: User Story 3 - Statistical Analysis & Reporting (Priority: P3)

**Goal**: Perform robust statistical analysis (mixed-effects modeling) with normality checks, multiple comparison corrections, and report generation.

**Independent Test**: Run on synthetic dataset with known effect sizes; verify correct model selection (LMM/GLMM), Shapiro-Wilk check, and Bonferroni correction.

### Tests for User Story 3

- [ ] T030 [P] [US3] Unit test for `code/analyze/normality_check.py` verifying Shapiro-Wilk implementation in `tests/unit/test_normality.py`
- [ ] T031 [P] [US3] Unit test for `code/analyze/mixed_effects.py` verifying model selection logic (LMM vs GLMM) based on metric type in `tests/unit/test_mixed_effects.py`
- [ ] T032 [P] [US3] Unit test for `code/analyze/report_gen.py` verifying Bonferroni correction application in `tests/unit/test_report_gen.py`
- [ ] T033 [P] [US3] Integration test: Run analysis on synthetic data with known effects and verify p-values and effect sizes in `tests/integration/test_us3_stats.py`

### Implementation for User Story 3

- [ ] T034 [US3] Implement `code/analyze/normality_check.py` to perform Shapiro-Wilk test on residuals
- [ ] T035a [US3] Implement `code/analyze/mixed_effects.py` to fit LMM (Gaussian) for continuous metrics (CodeBLEU, ROUGE) and GLMM (Binomial) for binary metrics (Exact Match)
- [ ] T035b [US3] Implement `code/analyze/mixed_effects.py` to include logic that checks the Shapiro-Wilk result from T034; if residuals are non-normal (p < 0.05), switch to the permutation test from T035c instead of the parametric model
- [ ] T035c [US3] Implement `code/analyze/permutation_test.py` to perform non-parametric permutation tests as a robust alternative when normality assumptions are violated (FR-005). Use 1000 iterations and alpha=0.05.
- [ ] T036 [US3] Implement `code/analyze/mixed_effects.py` to include fixed effects for formatting, naming, commenting and random intercepts for function ID
- [ ] T037 [US3] Implement `code/analyze/report_gen.py` to perform post-hoc pairwise comparisons with Bonferroni correction
- [ ] T038 [US3] Implement `code/analyze/report_gen.py` to: 1) Generate visualizations (interaction plots), 2) Generate summary tables (Factor, Estimate, SE, t-value, p-value), 3) Include a dedicated section comparing "Semantic Opacity" group vs. baseline (US-4), 4) Generate correlation report for token count vs. performance drop (FR-007)
- [ ] T041 [US3] Save final analysis report to `results/analysis_report.pdf` and `results/statistical_summary.csv`

**Checkpoint**: Statistical analysis complete; report generated with effect sizes and corrected p-values; robust fallback implemented.

---

## Phase 6: User Story 4 - Semantic Opacity Control (Priority: P3)

**Goal**: Explicitly measure and report the impact of the "generic naming + stripped comments" condition as a confounding variable.

**Independent Test**: Run summarization on "Semantic Opacity" variants and compare performance drop against "clean naming + stripped comments" variants.

### Tests for User Story 4

- [ ] T042 [P] [US4] Unit test for `code/analyze/report_gen.py` verifying specific flagging of "Semantic Opacity" samples in `tests/unit/test_us4_control.py`
- [ ] T043 [P] [US4] Integration test: Verify report includes specific comparison of "Semantic Opacity" vs. baseline in `tests/integration/test_us4_control.py`

**Note**: The implementation logic for tagging and analyzing "Semantic Opacity" is handled in Phase 4 (T016b, T026, T038) to ensure data flow integrity. This phase is reserved for verification and reporting.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and cleanup.

- [ ] T047 [P] Run `code/validation/verify_accuracy.py` (FR-010) as a final gate before research completion
- [ ] T048 Update `README.md` with execution instructions for the pilot study
- [ ] T049 [P] Add `quickstart.md` with instructions to run the full pipeline on a subset
- [ ] T050 [P] Run full integration test suite on the CI runner to ensure -hour runtime limit is met
- [ ] T051 Code cleanup and removal of debug logs

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately.
- **Foundational (Phase 2)**: Depends on Setup. **BLOCKS all user stories**.
- **User Stories (Phase 3-6)**: All depend on Foundational.
 - US1 (P1) must complete before US2 (P2) because US2 requires the generated variants.
 - US2 (P2) must complete before US3/US4 (P3) because analysis requires the metrics.
- **Polish (Phase 7)**: Depends on all user stories.

### User Story Dependencies

- **US1 (P1)**: Generates the data. No dependencies on other stories.
- **US2 (P2)**: Consumes US1 output. Depends on US1.
- **US3 (P3)**: Consumes US2 output. Depends on US2.
- **US4 (P3)**: Consumes US2 output and refines US3 analysis. Depends on US2 and US3.

### Parallel Opportunities

- **Setup**: T002 and T003 can run in parallel.
- **Foundational**: T004 (contracts) can run in parallel with T005 (validation) and T006 (seeds).
- **Testing**: All unit tests (T009-T012, T018-T021, etc.) can run in parallel within their respective stories.
- **Analysis**: Normality checks and model fitting can be parallelized per metric type if implemented.

---

## Implementation Strategy

### MVP First (US1 + US2 Core)

1. Complete Phase 1 & 2.
2. Complete Phase 3 (US1) to generate variants.
3. Complete Phase 4 (US2) core (completion task only) to get initial metrics.
4. **STOP and VALIDATE**: Ensure data flows from US1 -> US2 correctly.

### Incremental Delivery

1. Add US1 (Full 8-way generation).
2. Add US2 (All 3 tasks + metrics).
3. Add US3 (Statistical analysis).
4. Add US4 (Semantic opacity control).
5. Polish and final validation.

### Parallel Team Strategy

- **Dev A**: Focus on Phase 2 (Contracts, Validation, Seeds) and Phase 3 (Transformation).
- **Dev B**: Focus on Phase 4 (LLM Inference, Metrics, Mutation, Balancing).
- **Dev C**: Focus on Phase 5 & 6 (Statistics, Reporting, Opacity Control).
- **Integration**: Run full pipeline test after all phases complete.

---

## Notes

- **[P]** tasks = different files, no dependencies.
- **[Story]** label maps task to specific user story for traceability.
- **CPU Constraint**: All tasks must be designed to run on a modest CPU configuration with sufficient RAM resources. No GPU, no 8-bit quantization.
- **Data Integrity**: Use `code/validation/verify_accuracy.py` to ensure all data sources are real and verified.
- **Reproducibility**: `seed_manager.py` must log every seed and mapping hash used in transformation and inference.
- **Stop at Checkpoints**: Validate each User Story independently before proceeding.