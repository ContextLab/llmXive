# Tasks: 001-code-review-quality

**Input**: Design documents from `/specs/001-code-review-quality/`  
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `results/`, `state/` at repository root
- **Tests**: `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure: `code/`, `data/raw/`, `data/processed/`, `data/metrics/`, `results/`, `state/`, placeholder `README.md`, and empty `specs/` folder.
- [ ] T002 Initialize Python 3.11 package: add `code/__init__.py` and create `code/requirements.txt` pinned to specific versions of `datasets`, `radon`, `pylint`, `scipy`, `matplotlib`, `pandas`, `numpy`, `pyyaml`.
- [ ] T003 Configure linting and formatting: add `pyproject.toml` with Black, isort, Flake8 settings; create `.flake8` config file.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [ ] T004 Implement seed management module in `code/seeds.py` with documented seed value **42** for `numpy`, `random`, and (optional) `torch`.
- [ ] T005 Implement checksum utilities in `code/checksum.py` to compute SHA‑256 for downloaded datasets and write `data/checksums.json`.
- [ ] T006 Implement state‑tracking utilities in `code/state_tracker.py` to compute artifact hashes and update `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml` with `updated_at` timestamps.
- [ ] T007 Setup logging infrastructure in `code/logging_config.py` with snippet‑ID aware logger (INFO level, console + file).
- [ ] T008 Create data model definitions in `code/data_model.py`:
  - `CodeSnippet` (id, source, code, length, language)
  - `MetricScore` (snippet_id, metric_type, score, timestamp)
  - `DatasetGroup` (label, snippets, aggregates)
  - `MetricResult` schema for CSV output.

---

## Phase 3: User Story 1 – Dataset Ingestion and Preprocessing (Priority: P1)

**Goal**: Download and preprocess human‑written (CodeSearchNet) and LLM‑generated (CodeParrot/CodeGen) code datasets, filter to Python functions with comparable sizes.

- [ ] T009 [US1] Implement HuggingFace download for **CodeSearchNet** in `code/data_ingestion.py` with exponential backoff (≥3 retries, 60 s intervals) and robust error handling.
- [ ] T010 [US1] Implement HuggingFace download for **CodeParrot/CodeGen** in the same module, recording SHA‑256 checksums to `data/checksums.json`.
- [ ] T011 [US1] Implement dataset verification workflow: confirm that both datasets are listed in an internal whitelist of verified sources; abort with **error 101** if a dataset is not verified.
- [ ] T012 [US1] Implement Python‑only filtering: keep snippets where `language == "python"` and extract top‑level functions using `ast`.
- [ ] T013 [US1] Implement function‑length filtering to achieve median length difference ≤ 20 % between groups (iterative threshold adjustment, abort with **error 103** after 3 attempts).
- [ ] T014 [US1] Implement AST parsing validation: parse each snippet, log invalid IDs, require ≥95 % successful parses; abort with **error 102** if threshold not met.
- [ ] T015 [US1] Verify snippet count: ensure ≥ 1000 valid Python snippets per group; abort with **error 104** if not met.

---

## Phase 4: User Story 2 – Static Analysis Metric Extraction (Priority: P2)

**Goal**: Run radon for complexity and pylint for bug indicators on each code snippet, aggregate into metric distributions per dataset group.

- [ ] T016 [US2] Implement radon complexity extraction (cyclomatic complexity, LOC, maintainability index) in `code/metric_extraction.py`.
- [ ] T017 [US2] Implement pylint bug‑indicator extraction (potential bugs, style issues) in the same file.
- [ ] T018 [US2] Validate extracted scores: detect NaN or out‑of‑range values; if ≥5 % of snippets fail, abort with **error 102**.
- [ ] T019 [US2] Aggregate metrics per group and write CSV files to `data/metrics/` (one file per metric type) including mean, median, variance.
- [ ] T020 [US2] Add CPU‑only execution guard: assert `torch.cuda.is_available()` is **False**; raise informative error if a GPU is detected.
- [ ] T021 [US2] Ensure metric output conforms to `MetricResult` schema defined in `code/data_model.py`.

---

## Phase 5: User Story 3 – Statistical Comparison and Visualization (Priority: P3)

**Goal**: Apply Mann‑Whitney U tests with Cliff’s delta, generate boxplots, produce review guideline recommendations, and verify statistical power and independence assumptions.

- [ ] T022 [US3] Implement power‑analysis module in `code/statistical_analysis.py` to compute achieved power given observed effect size and sample size; enforce ≥ 0.8 power and log warnings otherwise.
- [ ] T023 [US3] Implement independence mitigation: subsample to at most one snippet per original repository (using metadata) **or** apply cluster‑robust standard errors; document approach in `results/independence.md`.
- [ ] T024 [US3] Implement Mann‑Whitney U test for each metric comparison (human vs LLM) and store raw p‑values.
- [ ] T025 [US3] Compute Cliff’s delta effect size with magnitude labels (small/medium/large) for each metric.
- [ ] T026 [US3] Apply Benjamini‑Hochberg multiple‑comparison correction across all metrics; store adjusted p‑values.
- [ ] T027 [US3] Generate boxplot visualizations for each metric in `code/visualization.py`; save figures to `results/figures/` with clear median and IQR labels.
- [ ] T028 [US3] Generate review guideline recommendations in `code/guideline_generator.py` for any metric with adjusted p < 0.05 **and** |Cliff’s delta| ≥ 0.1; write to `results/guidelines.md`.
- [ ] T029 [US3] Perform sensitivity analysis across significance thresholds {0.01, 0.05, 0.1}; record how headline rates vary in `results/sensitivity.md`.
- [ ] T030 [US3] Conduct pilot‑study validation: load an external human‑reviewed snippet set (≥ 50 samples), compute Pearson r between chosen static metric and recorded review effort; require r ≥ 0.5, otherwise raise **error 105** and add a citation to a peer‑reviewed source in `results/pilot_study.md`.
- [ ] T031 [US3] Document community‑standard justification for all thresholds (significance level, effect‑size interpretation) in `results/justification.md` (covers FR‑008).

---

## Phase 6: Constitutional Amendment Workflow (Blocking)

**Purpose**: Resolve the two constitutional conflicts that currently block research.

- [ ] T032 Draft amendment PR to **Principle VI** permitting use of **CodeParrot/CodeGen** as the LLM‑generated code source; include justification and impact analysis.
- [ ] T033 Draft amendment PR to **Principle VII** permitting use of **radon** and **pylint** for metric extraction; include CPU‑feasibility argument.
- [ ] T034 Submit both PRs, record their URLs in `plan.md`, and update the amendment‑status section after review.

---

## Phase 7: Polish & Cross‑Cutting Concerns

**Purpose**: Final refinements, documentation, and state management.

- [ ] T035 Update `README.md` with installation steps, execution commands, and a note about amendment status (must be approved before running the pipeline).
- [ ] T036 Update `quickstart.md` to provide a one‑command end‑to‑end run guide, checking that amendment PRs are merged before proceeding.
- [ ] T037 Implement artifact‑hash tracking: after each major output (datasets, metrics, stats, figures) compute SHA‑256 and record in `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml`.
- [ ] T038 Update the state YAML with `updated_at` timestamps after each pipeline stage via `code/state_tracker.py`.
- [ ] T039 Remove misleading `[P]` tags from tasks that share the same target file (already corrected in earlier phases).
- [ ] T040 Run full end‑to‑end validation script (`code/main.py --run-all`) and assert that all tests pass; log results to `results/pipeline_validation.log`.

---

## Dependencies & Execution Order

- **Setup (Phase 1)** → **Foundational (Phase 2)** → **Amendment (Phase 6)** (must succeed) → **User Stories (Phases 3‑5)** → **Polish (Phase 7)**.
- Within each phase, tasks are ordered to respect data flow (e.g., data model before ingestion, schema before extraction, statistical analysis before visualization).
- Parallelizable tasks are marked `[P]` only when they operate on distinct files.
