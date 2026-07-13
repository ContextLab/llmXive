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

- **Single project**: `code/`, `data/raw/`, `data/processed/`, `data/metrics/`, `results/`, `state/` at repository root
- **Tests**: `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure: `code/`, `data/raw/`, `data/processed/`, `data/metrics/`, `results/`, `state/`, placeholder `README.md`, and empty `specs/` folder.
- [X] T002 Initialize Python 3.11 package: add `code/__init__.py` and create `code/requirements.txt` pinned to specific versions of `datasets`, `radon`, `pylint`, `scipy`, `matplotlib`, `pandas`, `numpy`, `pyyaml`.
- [X] T003 Configure linting and formatting: add `pyproject.toml` with Black, isort, Flake8 settings; create `.flake8` config file.

---

## Phase 2: Foundational (Blocking Prerequisites & Constitutional Amendments)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **⚠️ CRITICAL**: Research is BLOCKED until Constitutional Amendment tasks (T008-T010) are approved or resolved.

- [X] T004 Implement seed management module in `code/seeds.py` with documented seed value **42** for `numpy`, `random`, and (optional) `torch`.
- [X] T005 Implement checksum utilities in `code/checksum.py` to compute SHA‑256 for downloaded datasets and write `data/checksums.json`.
- [X] T006 Implement state‑tracking utilities in `code/state_tracker.py` to compute artifact hashes and update `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml` with `updated_at` timestamps.
- [X] T007 Setup logging infrastructure in `code/logging_config.py` with snippet‑ID aware logger (INFO level, console + file).
- [X] T008 Create data model definitions in `code/data_model.py`:
 - `CodeSnippet` (id, source, code, length, language)
 - `MetricScore` (snippet_id, metric_type, score, timestamp)
 - `DatasetGroup` (label, snippets, aggregates)
 - `MetricResult` schema for CSV output.
- [X] T009 Draft amendment PR to **Principle VI** permitting use of **CodeParrot/CodeGen** as the LLM‑generated code source; include justification and impact analysis in `docs/amendment-vi.md`. **Proposed text**: "Allow LLM-generated code from verified training corpora (e.g., CodeParrot/CodeGen) when HumanEval/MBPP lack sufficient sample size (n≥1000) for statistical power." **BLOCKS Phase 3-5**.
- [X] T010 Draft amendment PR to **Principle VII** permitting use of **radon** and **pylint** for metric extraction; include CPU‑feasibility argument in `docs/amendment-vii.md`. **Proposed text**: "Allow CPU-tractable static analysis tools (radon, pylint) with documented justification when lightweight LLM inference exceeds runtime constraints (≤6h on 2-core CPU)." **BLOCKS Phase 3-5**.
- [X] T011 Submit both PRs, record their URLs in `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml` amendment_status map, and update the amendment‑status section after review. **BLOCKS Phase 3-5**. <!-- FAILED: unspecified -->

---

## Phase 3: User Story 1 – Dataset Ingestion and Preprocessing (Priority: P1)

**Goal**: Download and preprocess human‑written (CodeSearchNet) and LLM‑generated (CodeParrot/CodeGen) code datasets, filter to Python functions with comparable sizes.

- [X] T012 [US1] Implement HuggingFace download for **CodeSearchNet** in `code/data_ingestion.py` using `datasets.load_dataset('code_search_net',...)`, with exponential backoff (≥3 retries, 60 s intervals) and robust error handling.
- [X] T013 [US1] Implement HuggingFace download for **CodeParrot/CodeGen** in the same module using `datasets.load_dataset('codeparrot/codegen',...)`, recording SHA‑256 checksums to `data/checksums.json`.
- [X] T014 [US1] Implement dataset verification workflow: confirm that both datasets are listed in `data/verified_sources.json`; abort with **error 101** if a dataset is not verified.
- [X] T015 [US1] Implement streaming and sampling to ensure total snippets ≤ 10,000 to comply with 14 GB disk limit; use `datasets.load_dataset(..., streaming=True)` with [deferred] sample fraction.
- [ ] T016 [US1] Implement Python‑only filtering: keep snippets where `language == "python"` and extract top‑level functions using `ast`.
- [ ] T017 [US1] Implement function‑length filtering to achieve median length difference ≤ 20 % between groups (binary search algorithm, max 5 iterations, abort with **error 103** after max attempts).
- [ ] T018 [US1] Implement AST parsing validation: parse each snippet, log invalid IDs, require ≥95% successful parses; abort with **error 102** if threshold not met.
- [~] T019 [US1] Verify snippet count: ensure ≥ 1000 valid Python snippets per group; abort with **error 104** if not met.

---

## Phase 4: User Story 2 – Static Analysis Metric Extraction (Priority: P2)

**Goal**: Run radon for complexity and pylint for bug indicators on each code snippet, aggregate into metric distributions per dataset group.

- [~] T020 [US2] Implement radon complexity extraction (cyclomatic complexity, LOC, maintainability index) in `code/metric_extraction.py`.
- [~] T021 [US2] Implement pylint bug‑indicator extraction (potential bugs, style issues) in the same file.
- [~] T022 [US2] Validate extracted scores: detect NaN or out‑of‑range values; if ≥5% of snippets fail, abort with **error 102** and generate diagnostic report.
- [~] T023 [US2] Aggregate metrics per group and write CSV files to `data/metrics/` (one file per metric type) including mean, median, variance.
- [~] T024 [US2] Ensure metric output conforms to `MetricResult` schema defined in `code/data_model.py`.
- [~] T025 [US2] Add CPU‑only execution guard: verify `torch` is not used for inference; ensure `radon` and `pylint` execute without CUDA device assignment.

---

## Phase 5: User Story 3 – Statistical Comparison and Visualization (Priority: P3)

**Goal**: Apply Mann‑Whitney U tests with Cliff's delta, generate boxplots, produce review guideline recommendations, and verify statistical power and independence assumptions.

- [ ] T026 [US3] [SC-003] Implement power‑analysis module in `code/statistical_analysis.py` to compute achieved power given observed effect size and sample size; enforce ≥ 0.8 power and log warnings otherwise.
- [ ] T027 [US3] [SC-003] Implement independence mitigation: subsample to at most one snippet per original repository (using metadata) **OR** apply cluster‑robust standard errors; prefer subsampling if repository metadata available, else use cluster‑robust SE; document approach in `results/independence.md`.
- [ ] T028 [US3] Implement Mann‑Whitney U test for each metric comparison (human vs LLM) and store raw p‑values.
- [ ] T029 [US3] Compute Cliff's delta effect size with magnitude labels (small/medium/large) for each metric.
- [ ] T030 [US3] Apply Benjamini‑Hochberg multiple‑comparison correction across all metrics; store adjusted p‑values.
- [ ] T031 [US3] Generate boxplot visualizations for each metric in `code/visualization.py`; save figures to `results/figures/` with clear median and IQR labels.
- [ ] T032 [US3] Generate review guideline recommendations in `code/guideline_generator.py` for any metric with adjusted p < 0.05 **and** |Cliff's delta| ≥ 0.1; write to `results/guidelines.md`.
- [ ] T033 [US3] Perform sensitivity analysis across significance thresholds {0.01, 0.05, 0.1}; record how headline rates vary in `results/sensitivity.md`.
- [ ] T034 [US3] Conduct pilot‑study validation OR cite peer‑reviewed source per FR‑011: (A) Load external human‑reviewed snippet set (CodeReviewDataset from HuggingFace, n≥50), compute Pearson r between static metric and recorded review effort; require r ≥ 0.5; OR (B) cite peer‑reviewed source establishing correlation, then run Reference‑Validator Agent verification per Constitution Principle II (title overlap ≥0.7). Record results in `results/pilot_study.md`.
- [ ] T035 [US3] Document community‑standard justification for all thresholds (significance level, effect‑size interpretation) in `results/justification.md` (covers FR‑008).

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Final refinements, documentation, and state management.

- [ ] T036 Update `README.md` with installation steps, execution commands, and a note about amendment status (must be approved before running the pipeline).
- [ ] T037 Update `quickstart.md` to provide a one‑command end‑to‑end run guide, checking that amendment PRs are merged before proceeding.
- [ ] T038 Implement artifact‑hash tracking: after each major output (datasets, metrics, stats, figures) compute SHA‑256 and record in `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml`.
- [ ] T039 Update the state YAML with `updated_at` timestamps after each pipeline stage via `code/state_tracker.py`.
- [ ] T041 Run full end‑to‑end validation script (`code/main.py --run-all`) and assert that all tests pass; log results to `results/pipeline_validation.log`.
- [ ] T042 Create contracts/ directory structure in `code/contracts/` with placeholder files for data contracts (input/output schemas), API contracts (CLI interface), and validation contracts (pre/post conditions) as specified in plan.md Phase 1 output.

---

## Dependencies & Execution Order

- **Setup (Phase 1)** → **Foundational (Phase 2)** (Amendment tasks T009-T011 MUST be resolved) → **User Stories (Phases 3‑5)** → **Polish (Phase 6)**.
- Within each phase, tasks are ordered to respect data flow (e.g., data model before ingestion, schema before extraction, statistical analysis before visualization).
- Parallelizable tasks are marked `[P]` only when they operate on distinct files.
- **Blocking Warning**: Do not proceed to Phase 3 until T011 is complete and Constitutional Amendment status is approved in `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml`.