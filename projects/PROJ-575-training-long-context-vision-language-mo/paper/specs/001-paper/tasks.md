# Tasks: Reproduce & Validate Long-Context VLM Training with MMLongBench

**Input**: Design documents from `specs/575-reproduce-long-context-vlm/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/`, `paper/` at repository root
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Paper Infrastructure)

**Purpose**: Initialize the LaTeX project structure, bibliography, and data schemas required for the paper generation pipeline.

- [ ] T001 [P] Initialize LaTeX project structure at `paper/source/` including `main.tex`, `references.bib`, and `figures/` directory [kind:latex-build]
- [ ] T002 [P] Scaffold `paper/source/references.bib` with entries for the target paper, `yubo2333/MMLongBench-Doc`, and `Qwen2.5-VL-7B` model [kind:reference-verification]
- [ ] T002b [P] Populate `state/citations/PROJ-575-training-long-context-vision-language-mo.yaml` with citation entries and set `verification_status=verified` [kind:reference-verification]
- [ ] T003 [P] Create data schemas in `contracts/` for `figure-data.schema.yaml` and `bibliography.schema.yaml` to ensure artifact validity [kind:data-model]
- [ ] T004 [P] Initialize `data/manifest.json` structure to hold dataset checksums and provenance metadata (calculate SHA-256) [kind:system]
- [ ] T004b [P] Generate the 'Data Provenance' string referencing `manifest.json` checksums and insert it into `paper/source/main.tex` Methods section [kind:prose]

---

## Phase 2: Foundational (Data Validation & Schemas)

**Purpose**: Establish the data contracts and validation logic that ensure the evaluation artifacts can be correctly consumed by the paper generation engine.

**⚠️ CRITICAL**: No paper drafting work can begin until this phase is complete.

- [ ] T005 [P] Implement schema validation logic in `src/eval/utils.py` to verify `results/sample_results.json` contains required columns (`context_length`, `task_type`, `model_baseline_score`, `model_target_score`) [kind:statistics]
- [ ] T006a [P] Implement logic in `src/eval/validate_results.py` to detect data unavailability or corruption in `yubo2333/MMLongBench-Doc` and write failure report [kind:statistics]
- [ ] T006b [P] Draft Claim 5 text based on failure report from T006a [kind:prose]
- [ ] T007 [P] Create `src/eval/scaling_analysis.py` to fit regression models and generate `results/scaling_report.json` with `slope_coefficient`, `r_squared`, and `trend_classification` [kind:statistics]
- [ ] T008 [P] Implement logic in `src/eval/validate_results.py` to calculate retention rates and generate `results/validation_report.md` [kind:statistics]
- [ ] T009 [US1/US2/US3] Create `src/eval/report_generator.py` to aggregate `sample_results.json`, `scaling_report.json`, and `validation_report.md` into `results/final_report.md` [kind:statistics]

---

## Phase 3: User Story 1 - Reproduce Core Evaluation Results (Priority: P1) 🎯 MVP

**Goal**: Generate the raw evaluation data and the primary reproduction deviation metric required for the Abstract and Results.

**Independent Test**: Execute `src/eval/run_cpu_eval.py` with `--sample-size=10` on a CPU-only environment and verify `results/sample_results.json` is generated with valid data.

### Implementation for User Story 1

- [ ] T010 [P] [US1] Implement 4-bit quantization logic for `Qwen2.5-VL-7B` in `src/eval/run_cpu_eval.py` ensuring memory usage stays under 7GB. Logic MUST: Attempt standard 4-bit quantization; if OOM or CUDA error, automatically switch to `llama.cpp` or CPU-optimized `bitsandbytes` and log the fallback [kind:system]
- [ ] T011 [US1] Implement the main evaluation loop in `src/eval/run_cpu_eval.py` to process `yubo2333/MMLongBench-Doc` test split and output `results/sample_results.json` [kind:statistics]
- [ ] T012 [P] [US1] Implement logic to capture execution metadata (commit hash, data seed, environment versions) into `results/evaluation_run.json` [kind:system]
- [ ] T013 [US1] Implement the "Fail Fast" validation in `src/eval/run_cpu_eval.py` to detect OOM or missing dataset fields and trigger Claim 5 [kind:statistics]
- [ ] T014 [P] [US1] Generate the "Reproduction Delta" calculation in `src/eval/report_generator.py` to determine the exact deviation % (Claim 1) [kind:statistics]
- [ ] T014b [P] [US1] Format and insert the measured deviation percentage into the Abstract and Results text as required by FR-006 [kind:prose]
- [ ] T014c [P] [US1] Define and retrieve the 'original paper's claimed scores' from configuration to calculate the delta for Figure 3 [kind:logic]
- [ ] T015 [P] [US1] Draft the "Methods" section content in `paper/source/main.tex` with placeholders for dynamic insertion of `evaluation_run.json` metadata [kind:prose]
- [ ] T015b [P] [US1] Ensure the Methods text generation includes the specific strings 'yubo2333/MMLongBench-Doc' and 'test' split [kind:prose]

**Checkpoint**: Raw evaluation data is available, and the primary deviation metric (Claim 1) is calculable.

---

## Phase 4: User Story 2 - Verify Generalization Claims (Priority: P2)

**Goal**: Generate the retention rate analysis and the corresponding visualization to support the "Generalization" claim.

**Independent Test**: Run `src/eval/validate_results.py` and verify `results/validation_report.md` explicitly states the retention rate and compares it against the 80% threshold.

### Implementation for User Story 2

- [ ] T016 [P] [US2] Implement retention rate calculation in `src/eval/validate_results.py` (Performance@256K / Performance@128K) [kind:statistics]
- [ ] T016b [P] [US2] Ensure raw retention values are passed to the figure generator in a structured format suitable for plotting [kind:logic]
- [ ] T017a [US2] Implement logic to flag "Generalization Hypothesis Not Supported" if retention rate < 80% and link to Primary Claim Selection Logic [kind:statistics]
- [ ] T017b [US2] Draft text stating "Generalization Hypothesis Not Supported" if retention rate < 80% [kind:prose]
- [ ] T018 [P] [US2] Generate `paper/source/figures/fig2_retention.pdf` (Bar Chart) using `matplotlib`/`seaborn` based on structured retention data [kind:figure]
- [ ] T019 [US2] Draft the "Results" section content in `paper/source/main.tex` for the Generalization subsection, including placeholders for the retention rate and Figure 2 [kind:prose]
- [ ] T020 [P] [US2] Update `references.bib` to ensure the dataset citation matches the specific version used in the evaluation [kind:reference-verification]

**Checkpoint**: Generalization retention rates are calculated, and the corresponding figure is generated.

---

## Phase 5: User Story 3 - Analyze Scaling Trends (Priority: P3)

**Goal**: Generate the scaling analysis (regression) and the "Scaling Curve" figure, while explicitly handling the "inconclusive" case due to small sample size.

**Independent Test**: Execute `src/eval/scaling_analysis.py` and verify `results/scaling_report.json` contains a valid trend classification (including "inconclusive" if R² < 0.1).

### Implementation for User Story 3

- [ ] T021 [P] [US3] Implement linear regression of `score` vs `log(context_length)` in `src/eval/scaling_analysis.py` [kind:statistics]
- [ ] T021b [P] [US3] Extract and pass raw per-sample data points to the figure generator for Figure 1 [kind:logic]
- [ ] T022 [US3] Implement trend classification logic: "sublinear", "superlinear", "linear", or "inconclusive" (if R² < 0.1 or high variance). MUST explicitly suppress specific trend claims in generated text if R² < 0.1 [kind:statistics]
- [ ] T022b [P] [US3] Implement guardrail to suppress any p-value claims or significance language in the Discussion if R² < 0.1 [kind:logic]
- [ ] T023 [P] [US3] Generate `paper/source/figures/fig1_scaling.pdf` (Scaling Curve) using `matplotlib`/`seaborn` based on `results/scaling_report.json` and raw data points [kind:figure]
- [ ] T025a [P] [US3] Implement logic in `src/eval/report_generator.py` to generate "Discrepancy Analysis" text if deviation > 1.0% [kind:statistics]
- [ ] T025b [US3] Implement logic to insert "Discrepancy Analysis" text into Discussion [kind:logic]
- [ ] T024 [US3] Draft the "Discussion" section content in `paper/source/main.tex` for the "Limitations" subsection, explicitly stating n=10 and lack of multiple-comparison correction (if n < 30). MUST incorporate output from T025a [kind:prose]

**Checkpoint**: Scaling trends are analyzed, figures generated, and limitations explicitly documented.

---

## Phase 6: Paper Assembly & Validation (Cross-Cutting)

**Purpose**: Assemble the final paper text, verify all claims, and ensure the LaTeX build succeeds.

- [ ] T026 [P] [US1/US2/US3] Implement the "Primary Citation Claim" selection logic (Claim 5 if failure [defined as OOM, Data Unavailable, or Inconclusive Scaling], else Claim 1) in `src/eval/report_generator.py`. MUST select the Claim 5 text generated by T006b or generate it based on T006a's report [kind:logic]
- [ ] T026b [P] [US1/US2/US3] Verify that the final Abstract text contains exactly one "Primary Citation Claim" sentence matching the selected claim [kind:logic]
- [ ] T027 [P] [US1/US2/US3] Generate `paper/source/figures/fig3_delta.pdf` (Reproduction Delta Plot) based on `results/sample_results.json` and baseline scores [kind:figure]
- [ ] T028 [P] [US1/US2/US3] Populate `paper/source/main.tex` with all dynamic content from `results/final_report.md` and generated figures [kind:prose]
- [ ] T028a [P] [US1/US2/US3] Explicitly insert the 'Data Provenance' string referencing `manifest.json` checksums into the Methods section [kind:prose]
- [ ] T029 [P] [US1/US2/US3] Verify `references.bib` entries against `state/citations/PROJ-575-training-long-context-vision-language-mo.yaml`. MUST verify that entries match `verification_status=verified` [kind:reference-verification]
- [ ] T032 [P] [US1/US2/US3] Perform final proofread of the generated `main.tex` text for flow, jargon discipline, and claim consistency [kind:proofread]
- [ ] T030 [P] [US1/US2/US3] Run `pdflatex` on `paper/source/main.tex` to generate `paper/build/main.pdf` and capture any compilation errors [kind:latex-build]
- [ ] T031 [P] [US1/US2/US3] If compilation fails, analyze logs, generate `paper/source/latex_fixes.md` with specific fixes, apply fixes, and re-run T032 (Proofread) before next build [kind:latex-fix]

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories (Data validation must exist before generation)
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (P1)**: Must be completed first to establish the baseline and primary claim.
 - **US2 (P2)**: Can run in parallel with US1 once data schemas are ready, but relies on US1's data output.
 - **US3 (P3)**: Can run in parallel with US1/US2 once data schemas are ready.
- **Assembly (Phase 6)**: Depends on all desired user stories being complete.

### Parallel Opportunities

- **Phase 1**: All tasks (T001-T004b) can run in parallel.
- **Phase 2**: T005-T008 can run in parallel as they are distinct module implementations. T009 must wait for T005-T008.
- **Phase 3-5**:
 - T010 (Quantization) and T013 (Fail Fast) are critical path for US1.
 - T016 (Retention Calc) and T018 (Figure 2) can run in parallel for US2.
 - T021 (Regression) and T023 (Figure 1) can run in parallel for US3.
- **Phase 6**:
 - T032 (Proofread) must precede T030 (Build).
 - T026 and T027 must precede T028 (Assembly).
 - T031 (Fix) is conditional on T030 (Build) failure and must trigger T032.

---

## Implementation Strategy

### MVP First (Reproduction Only)

1. Complete Phase 1 & 2 (Setup + Foundational).
2. Complete Phase 3 (US1 - Core Reproduction).
3. **STOP and VALIDATE**: Ensure `results/sample_results.json` is valid and Claim 1 is calculable.
4. If Claim 5 (Failure) is triggered, proceed to Phase 6 to assemble the "Negative Result" paper.

### Incremental Delivery

1. Complete Setup + Foundational.
2. Add US1 (Reproduction) -> Test -> Deploy/Demo (MVP!).
3. Add US2 (Generalization) -> Test -> Deploy/Demo.
4. Add US3 (Scaling) -> Test -> Deploy/Demo.
5. Complete Phase 6 (Assembly) to generate the full paper.

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 1 & 2 together.
2. Once Foundational is done:
 - Developer A: US1 (Reproduction & Claim 1).
 - Developer B: US2 (Generalization & Figure 2).
 - Developer C: US3 (Scaling & Figure 1).
3. All developers converge on Phase 6 for Assembly and Build.

---

## Notes

- [P] tasks = different files, no dependencies.
- [Story] label maps task to specific user story for traceability.
- **CRITICAL**: Every task MUST include a `[kind:...]` token.
- **CRITICAL**: If `yubo2333/MMLongBench-Doc` is unavailable, T006a must trigger Claim 5, and the paper MUST reflect this failure in the Abstract.
- **CRITICAL**: If R² < 0.1, T022 MUST classify the trend as "inconclusive" or "highly variable" (Claim 3) and suppress specific trend claims.
- **CRITICAL**: The "Primary Citation Claim" in the Abstract (T026) MUST be dynamically selected based on the logic: Claim 5 (Failure) > Claim 1 (Reproduction).
- Verify tests fail before implementing (if tests were included).
- Commit after each task or logical group.
- Stop at any checkpoint to validate story independently.