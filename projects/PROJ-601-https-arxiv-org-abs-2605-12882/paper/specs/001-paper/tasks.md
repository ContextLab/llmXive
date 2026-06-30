# Tasks: CiteVQA Reproduction & Validation Paper

**Input**: `paper/spec.md`, `paper/plan.md`, `research_reviewer_*` feedback, `figure_inventory`, `claim_inventory`
**Prerequisites**: Research-stage artifacts (pipeline code, `outputs/` directory with `evaluation_report.json`, `validation_log.json`, `infer_results.jsonl`), `contracts/figure-data.schema.yaml`.

**Tests**: The examples below include test tasks. Tests are **OPTIONAL** - only include them if explicitly requested in the feature specification (e.g., schema validation for artifacts).

**Organization**: Tasks are grouped by paper section/phase to enable independent drafting, figure generation, and verification.

**Format**: `[ID] [P?] [Story] Description [kind:<value>]`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story/section this task belongs to (e.g., US1, US2, US3, Setup, Figures, Claims)
- Include exact file paths in descriptions
- **MANDATORY**: Every task line MUST include a `[kind:...]` token.

---

## Phase 1: Setup (LaTeX Infrastructure & Reproducibility)

**Purpose**: Initialize the paper repository structure, LaTeX configuration, and bibliography scaffolding.

- [ ] T001 [P] [Setup] Initialize `projects/PROJ-601-https-arxiv-org-abs-2605-12882/paper/source/main.tex` with standard conference template (e.g., ACM/IEEE) and required packages (tikz, pgfplots, hyperref) [kind:latex_build]
- [ ] T002 [P] [Setup] Create `projects/PROJ-601-https-arxiv-org-abs-2605-12882/paper/source/bib/references.bib` and scaffold entries for CiteVQA original paper, Transformers library, and WYSIATI literature [kind:paper_writing]
- [ ] T003 [P] [Setup] Create `projects/PROJ-601-https-arxiv-org-abs-2605-12882/paper/source/figures/` directory structure for auto-generated assets [kind:latex_build]
- [ ] T004 [P] [Setup] Draft `projects/PROJ-601-https-arxiv-org-abs-2605-12882/docs/reproducibility/pipeline_validation.md` with the exact command sequence for `reproduce.sh` and environment variables [kind:paper_writing]

---

## Phase 2: Foundational (Data Validation & Artifact Verification)

**Purpose**: Ensure the research artifacts (`evaluation_report.json`, `validation_log.json`) are valid and match the spec before drafting results.

**⚠️ CRITICAL**: No Results section drafting can begin until this phase is complete.

- [ ] T005 [P] [US3] Implement schema validation script `scripts/validate_artifacts.py` against `contracts/figure-data.schema.yaml` to verify `outputs/evaluation_report.json` and `outputs/validation_log.json`. Note: T006 and T007 logically depend on T005 success; while marked [P] for parallel execution, the engine should treat T005 as a prerequisite for meaningful execution of T006/T007. [kind:paper_statistics]
- [ ] T006 [P] [US3] Verify `outputs/validation_log.json` contains explicit `skipped_count` and `skipped_reasons` (e.g., "missing_bbox", "missing_image") as per FR-005 [kind:paper_statistics]
- [ ] T007 [P] [US3] Verify `outputs/evaluation_report.json` contains `saa_score`, `standard_accuracy` (or data to calculate it), `region_only_correct`, `answer_only_correct`, `both_correct`, `both_wrong`, `total_samples`, AND explicitly verify the presence of the denominator (`total_samples` or `total_correct_answers`) required for Claim 3 calculation [kind:paper_statistics]

**Checkpoint**: Artifacts validated; Data Integrity section ready.

---

## Phase 3: User Story 1 - Reproducibility & Execution Transparency (Priority: P1) 🎯 MVP

**Goal**: Draft the Abstract, Introduction, and Reproducibility Appendix to establish trust and execution transparency.

**Independent Test**: A reader can follow the Appendix instructions and verify the pipeline runs on a CPU-only machine.

### Implementation for User Story 1

- [ ] T009 [P] [US1] Draft **Abstract**: Summarize CPU-only reproduction, SAA vs. Standard Accuracy delta, and key bias finding [kind:paper_writing]
- [ ] T010 [P] [US1] Draft **Introduction**: Contextualize WYSIATI bias, limitations of standard accuracy, and contribution of SAA [kind:paper_writing]
- [ ] T011 [P] [US1] Draft **Reproducibility Appendix**: Detail `reproduce.sh` usage, random seed configuration, `transformers`/`torch` versions, memory constraints (<7 GB), environment variables, and explicit link to `docs/reproducibility/pipeline_validation.md` [kind:paper_writing]
- [ ] T012 [P] [US1] Verify Appendix includes explicit reference to `docs/reproducibility/pipeline_validation.md`, `outputs/evaluation_report.json`, AND explicitly verifies the presence of 'random seed configuration' and 'exact transformers/torch versions' in the draft [kind:paper_writing]

**Checkpoint**: US1 (Reproducibility) complete; Reader can verify setup.

---

## Phase 4: User Story 2 - Attribution Hallucination Diagnosis (Priority: P2)

**Goal**: Generate figures and draft the Methods/Results sections to diagnose and visualize the bias.

**Independent Test**: Figures render correctly from `evaluation_report.json` and `validation_log.json` with correct legends and captions.

### Figure Generation Tasks

- [ ] T013 [P] [US2] Generate **Figure 1**: SAA Calculation Workflow (Flowchart) using `scripts/plot_workflow.py` (TikZ/Mermaid) based on `eval/saa_scoring.py` logic. **MUST** include a self-contained legend defining SAA, IoU, and Attribution Hallucination without requiring reference to the Methods section. **MUST** visually highlight the branching logic for "Answer Correct/Region Wrong" vs "Answer Wrong". [kind:paper_figure_generation]
- [ ] T014 [P] [US2] Generate **Figure 2**: Error Distribution Bar Chart using `scripts/plot_error_distribution.py` (seaborn) from `outputs/evaluation_report.json` (`both_correct`, `answer_only_correct`, `region_only_correct`, `both_wrong`). **MUST** caption explicitly state the implication of the 'region_only_correct' bar for the paper's main claim (e.g., "demonstrating that standard accuracy overestimates truthfulness by ignoring spatial context"). [kind:paper_figure_generation]
- [ ] T015 [P] [US2] Generate **Figure 3**: Dataset Integrity Stacked Bar Chart using `scripts/plot_integrity.py` from `outputs/validation_log.json` (`skipped_reasons`). **MUST** show total `skipped_count`. Note: Stacked Bar Chart is chosen over spec's 'pie chart' option to ensure precision, satisfying the 'pie chart or table' clause. [kind:paper_figure_generation]
- [ ] T014b [P] [US2] Finalize all figure captions (T013, T014, T015) to ensure they meet mandatory requirements before insertion. [kind:paper_writing]
- [ ] T016 [P] [US2] Convert all generated figures to PDF/SVG and place in `projects/PROJ-601-https-arxiv-org-abs-2605-12882/paper/source/figures/` [kind:latex_build]

### Methods & Results Drafting

- [ ] T017a [P] [US2] Calculate 'Standard Accuracy' from breakdown fields (`both_correct` + `answer_only_correct`) / `total_samples` if not present in `evaluation_report.json`, and record the value [kind:paper_statistics]
- [ ] T017 [P] [US2] Draft **Methods**: Detail CPU environment, quantization, `validate_dataset.py` logic, SAA formula (IoU=0.5), and error categorization logic (Answer Correct/Region Wrong vs Answer Wrong) [kind:paper_writing]
- [ ] T018 [P] [US2] Draft **Results (Part 1)**: Present SAA score and delta vs. Standard Accuracy (Claim 1) using data from `evaluation_report.json` and T017a calculation [kind:paper_writing]
- [ ] T018b [P] [US2] Verify that the drafted text for Claim 1 explicitly includes the specific delta value found in results, not just the calculation. [kind:paper_writing]
- [ ] T019 [P] [US2] Draft **Results (Part 2)**: Calculate and present `attribution_hallucination_rate` (Claim 3) derived from the ratio of `region_only_correct` / `total_correct_answers` (or similar denominator) if not pre-calculated; explicitly state the calculation method if derived [kind:paper_writing]
- [ ] T019b [P] [US2] Verify that the drafted text for Claim 3 explicitly replaces the placeholder '[INSERT_SPECIFIC_VALUE]' with the actual calculated value or a clearly framed hypothesis statement [kind:paper_writing]
- [ ] T020 [P] [US2] Draft **Results (Part 3)**: Present memory usage metrics (Claim 2) and `skipped_count` (Data Integrity) [kind:paper_writing]
- [ ] T008 [P] [US3] Draft "Dataset Integrity" subsection in `paper/source/main.tex` reporting the `skipped_count` and percentage of excluded data (Moved from Phase 2 to align with Figure 3 generation) [kind:paper_writing]
- [ ] T021 [P] [US2] Insert Figure 1, 2, and 3 into `main.tex` with correct cross-references and mandatory captions (ensure captions finalized in T014b) [kind:latex_build]

**Checkpoint**: US2 (Bias Diagnosis) complete; Figures generated and Results drafted.

---

## Phase 5: User Story 3 - Data & Methodological Transparency (Priority: P3)

**Goal**: Finalize the Discussion, verify all claims, and perform a final proofread.

**Independent Test**: All claims in the paper are explicitly supported by numerical results from `evaluation_report.json` or `validation_log.json`.

### Implementation for User Story 3

- [ ] T022 [P] [US3] Draft **Discussion**: Analyze WYSIATI bias implications, address quantization artifacts vs. general bias, and discuss CPU constraints. Explicitly reference the finalized Results text from T018-T020. [kind:paper_writing]
- [ ] T023 [P] [US3] **Claim Verification**: Verify Claim 1 (Standard Accuracy vs. SAA delta) matches `evaluation_report.json` values AND verify the drafted text explicitly includes the specific delta value [kind:paper_statistics]
- [ ] T024 [P] [US3] **Claim Verification**: Verify Claim 2 (CPU <7 GB) matches `evaluation_report.json` `memory_peak_gb` and ensure the value is derived from the JSON artifact, not separate documentation [kind:paper_statistics]
- [ ] T025 [P] [US3] **Claim Verification**: Verify Claim 3 (Hallucination %) matches calculated ratio of `region_only_correct` / `total_correct` [kind:paper_statistics]
- [ ] T026 [P] [US3] Draft **Limitations**: Explicitly discuss IoU threshold sensitivity and non-determinism (floating-point variance) [kind:paper_writing]
- [ ] T027 [P] [US3] Perform **Proofread** of full manuscript for flow, clarity, and adherence to "Results before Discussion" logic [kind:paper_proofreader]
- [ ] T028 [P] [US3] Run `pdflatex` build to ensure no compilation errors and all figures render [kind:latex_fix]

**Checkpoint**: US3 (Transparency) complete; All claims verified; Paper builds successfully.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final review and submission preparation.

- [ ] T029 [P] [Polish] Update `paper/spec.md` and `paper/plan.md` to reflect final section lengths and figure placements [kind:paper_writing]
- [ ] T030 [P] [Polish] Verify `references.bib` entries against the final bibliography and ensure all cited works are present [kind:paper_writing]
- [ ] T031 [P] [Polish] Run final `pdflatex` build and generate `projects/PROJ-601-https-arxiv-org-abs-2605-12882/paper/output/paper.pdf` [kind:latex_build]
- [ ] T032a [P] [Polish] Run `pdflatex` build for final validation [kind:latex_build]
- [ ] T032b [P] [Polish] Validate final PDF against the "12-panel review" checklist defined in the plan (Reproducibility, Metric Validity, Data Integrity, Bias Evidence, CPU Feasibility) [kind:paper_proofreader]

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Research Artifacts (`outputs/` directory) - **BLOCKS** all drafting.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
 - US1 (Reproducibility) and US2 (Bias Diagnosis) can be drafted in parallel once data is validated.
 - US3 (Transparency) depends on US1/US2 drafts being complete for final integration.
- **Polish (Phase 6)**: Depends on all user stories being complete.

### Within Each User Story
- **Figures**: Must be generated (T013-T015) and captions finalized (T014b) before being inserted into the LaTeX document (T021).
- **Claims**: Verification tasks (T023-T025) must be completed before finalizing the Discussion (T022).
- **Build**: `pdflatex` (T028, T031, T032a) must be run after all content is inserted.

### Parallel Opportunities
- **T001-T004** (Setup) can run in parallel.
- **T005-T007** (Validation) can run in parallel (with T005 dependency noted).
- **T009-T012** (US1 Drafting) and **T013-T016** (US2 Figures) can run in parallel.
- **T023-T025** (Claim Verification) can run in parallel.

---

## Notes
- **[P]** tasks = different files, no dependencies.
- **[kind:...]** is **MANDATORY** on every task line.
- **No Scope Creep**: Do not add tasks for features not explicitly requested in `spec.md` (e.g., do not add a new metric or a new figure not listed in "Required Figures").
- **Data Source**: All numerical claims in the paper MUST be derived from `outputs/evaluation_report.json` or `outputs/validation_log.json`.
- **Figure Captions**: Must strictly follow the "Mandatory Requirement" text specified in `spec.md` (e.g., explicit definition of Attribution Hallucination in Fig 2 caption).
- **Verification**: Use `kind:paper_statistics` for any task that checks a claim against a data source or bibliography, or involves data management. Use `kind:paper_writing` for drafting prose, documentation, and bibliography tasks. Use `kind:paper_proofreader` for proofreading tasks. Use `kind:latex_build` for build tasks. Use `kind:latex_fix` for repair tasks. Use `kind:paper_figure_generation` for figure generation tasks.