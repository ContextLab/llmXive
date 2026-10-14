# Tasks: llmXive Follow-up: Structural Mismatch Cost in Heterogeneous Retrieval

**Input**: Design documents from `specs/001-structural-mismatch-cost/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/`, `data/` at project root; feature docs under `specs/001-structural-mismatch-cost/`
- Research scripts write ONLY to project-owned paths (`data/`, `code/`, `specs/`); never to `state/` or `.github/` — the platform owns those.

---

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [P] Establish the project structure per implementation plan: create `code/` (with `code/analysis/`, `code/generators/`, `code/executors/`, `code/utils/`, `code/tests/`), `data/raw/`, `data/processed/`, `data/results/`, `tests/unit/`, `tests/integration/`, and `specs/001-structural-mismatch-cost/contracts/` with at least the source files and contract schemas referenced by other tasks. Document the runnable pipeline command (`python -m code.main`) in `specs/001-structural-mismatch-cost/quickstart.md`. **Verifier rejection to fix**: no visible directories/files existed; commit real files, not empty placeholders.
- [ ] T002 Initialize Python 3.11 project with dependencies: `pandas`, `numpy`, `scipy`, `statsmodels`, `pytest`, `pyyaml`, `rdflib`, `networkx`, `matplotlib`, `seaborn`, `requests`, `datasets` in `code/requirements.txt`.
- [ ] T003 [P] Configure linting and formatting in `code/` via `pyproject.toml` and `.ruff.toml` at the project root (ruff lint + format settings matching the plan's tooling section). **Verifier rejection to fix**: the config files did not exist; produce real, non-empty configuration files and run `ruff check code/` successfully.
- [ ] T004 [P] Create/repair data schemas in `specs/001-structural-mismatch-cost/contracts/`: `query_instance.schema.yaml`, `execution_log.schema.yaml` (CSV column contract per data-model.md, integer `complexity_level`), `analysis_result.schema.yaml`, and `statistics-result.schema.yaml` (sensitivity sweep items). **Verifier rejection to fix**: schema files were missing/empty; commit complete YAML schemas matching the data model, and validate a sample row against each with `pyyaml` + `jsonschema`.

**Checkpoint**: Structure, dependencies, tooling, and contracts exist and are checkable.

---

## Phase 2: Foundational pipeline (data, generation, execution)

Verified foundational work preserved below; reopened items are marked.

- [ ] T005 [P] Implement `code/config.py` for seeds, paths, CPU throttling configuration, and real dataset access recipes (MS MARCO via `datasets.load_dataset("microsoft/ms_marco", "v1.1")`, Spider via `datasets.load_dataset("xlangai/spider")`, DBpedia/Wikidata subset via a named, reachable source) with a FAIL-LOUDLY policy: missing data or insufficient depth raises immediately; `EXIT_CODE_THROTTLING_FAILURE = 1` defined here.
- [ ] T007 [P] Implement `code/generators/reference_engine.py` (FR-008): deterministic greedy ground-truth plan generator based on pre-computed source statistics.
- [ ] T006 Implement `code/generators/synthetic_query.py` generating queries with exact integer plan depths (1, 2, 3, 4+), calling T007 to attach `ground_truth_plan` (FR-002, FR-008). **Dependency: T007.**
- [ ] T016 Implement CPU throttling in `code/utils/cpu_throttle.py` enforcing the strict CPU time limit and memory cap of FR-001 via `cgroups` where available, falling back to `resource`-module limits (RLIMIT_CPU / RLIMIT_AS) with `throttling_mode="time_only"` recorded in the logs. **Correction (reopened)**: the previous "virtual delay" fallback is prohibited by FR-001 — latency MUST be real wall-clock engine execution time only; no `time.sleep` or proportional artificial delay may appear anywhere in the throttle or executor code. Remove any such logic.
- [ ] T016b Implement `validate_throttling_effectiveness` in `code/utils/cpu_throttle.py`, called from `code/main.py`, aborting with `EXIT_CODE_THROTTLING_FAILURE` when neither cgroups nor resource limits apply (Edge Case 3). **Dependency: T016.**
- [ ] T016c [P] Implement `code/utils/data_fetcher.py` for real dataset fetching from the recipes in T005, streaming large datasets with `datasets.load_dataset(..., streaming=True)` and chunked processing so the full real data contributes without exceeding RAM. Verify checksums of raw artifacts. Real fetch failures MUST raise (no `try/except` fallback to synthetic/mock data). If a real dataset lacks required structural depth (join keys / graph edges ≥ 3 hops), the loader either aborts (default) or, only when the explicit config flag is set, synthesizes a graph from the Spider schema with `synthetic_flag=1` traceability metadata — never silently.
- [ ] T008 Implement `code/executors/base.py`: abstract executor base class with 60-second timeout handling, using the T016 throttle. **Dependency: T016.**
- [ ] T009 [P] Implement `code/executors/text_executor.py` executing real queries against the sampled/streamed MS MARCO subset with real wall-clock measurement; logical operation count proportional to integer `complexity_level`; no `time.sleep`. **Dependency: T006.**
- [ ] T010 [P] Implement `code/executors/relational_executor.py` wrapping in-memory SQLite loaded from the Spider subset.
- [ ] T011 [P] Implement `code/executors/graph_executor.py` using NetworkX/RDFLib multi-hop traversal over the real DBpedia/Wikidata subset.
- [ ] T012 [P] Implement `code/main.py` orchestration: load config, generate queries, route to executors, log raw metrics.
- [ ] T013 [P] [US1] Contract test for `ExecutionMetric` schema validation in `tests/contract/test_execution_metric.py`.
- [ ] T014 [P] [US1] Integration test for end-to-end query execution loop with CPU throttling in `tests/integration/test_latency_pipeline.py`.
- [ ] T014b [P] [US1] Integration test for throttling validity abort in `tests/integration/test_throttling_abort.py`.
- [ ] T015 [US1] Implement `code/analysis/metrics.py` recording end-to-end latency (ms) and timeout flags (FR-003).
- [ ] T017 [US1] Integer plan-depth classification in `code/generators/synthetic_query.py` preserving exact depth (FR-002).
- [ ] T021 [US1] Implement data persistence in `code/main.py` writing raw metrics to `data/processed/execution_logs.csv` with columns exactly matching `execution_log.schema.yaml`: `query_id`, `source_type`, `complexity_level` (integer), `latency_ms`, `translation_error`, `success_flag`, `synthetic_flag`, `throttling_mode`. **Verifier rejection to fix**: the CSV and the writing logic were absent. Run the pipeline end-to-end on a small real sample (≥ 30 queries across all three source types and depths 1–4) and commit the real CSV produced. **Dependency: T015, T017, T016.**

**Checkpoint**: A thin end-to-end run on real inputs produces `data/processed/execution_logs.csv` with real measured latencies.

---

## Phase 3: Complete statistical analysis, validation, and reporting

- [ ] T018 [US1] Implement `code/analysis/stats.py` two-way ANOVA/ANCOVA (`latency ~ complexity * source_type`) reading `data/processed/execution_logs.csv`, filtering `synthetic_flag=1` rows out of the primary analysis, outputting F-statistic, p-value, 95% CI for the interaction term, slope ratio (graph vs. text, SC-001), and post-hoc Tukey results to `data/results/anova_results.json`; hypothesis flagged 'supported' only if p < 0.05. Levene/Shapiro run as diagnostics only. **Dependency: T021.**
- [ ] T020 [US1] Implement the FR-007 sensitivity sweep in `code/analysis/stats.py`: loop over cutoffs [2, 3, 4]; for each cutoff compute `spike_point` (complexity level where the absolute difference in mean latency between consecutive levels is maximized) and `slope_change` (difference of post-spike and pre-spike regression slopes); persist the full list of `{"cutoff", "spike_point", "slope_change"}` objects to `data/results/sensitivity_analysis.json` conforming to `statistics-result.schema.yaml`. **Verifier rejection to fix**: neither the sweeping function nor the output JSON existed. Execute it on the real execution logs and commit the produced JSON. **Dependency: T021.**
- [ ] T024 [US2] Binary translation-error comparison (FR-004) in `code/analysis/metrics.py` against T007 ground truth.
- [ ] T025 [US2] Error-rate aggregation (low vs. high complexity) in `code/analysis/stats.py`. **Dependency: T024.**
- [ ] T026 [US2] Translation errors logged alongside latency in `data/processed/execution_logs.csv` via `code/main.py`. **Dependency: T025.**
- [ ] T027 [US2] Validation that ground-truth plans originate from the independent reference engine (FR-008, non-circular). **Dependency: T007.**
- [ ] T022 [P] [US2] Contract test for `QueryInstance` schema in `tests/contract/test_query_instance.py`.
- [ ] T030 [US3] Implement `code/analysis/viz.py` generating interaction plots (latency vs. complexity, lines per source type) from `data/processed/execution_logs.csv`, explicitly highlighting the graph-source slope difference and the spike/threshold region (FR-006), saving `data/results/interaction_plot.png` and `data/results/interaction_plot.pdf`. **Dependency: T021, T026.**
- [ ] T033 [US3] Generate `data/results/research_summary.md` from the actual result artifacts: ANOVA interaction statistics and slope ratio (SC-001), the absolute difference in translation error rates between low and high complexity groups as a distinct top-level value (SC-002), sensitivity sweep results (SC-004), links to the plots, and an honest statement of limitations (associational framing, throttling mode, any `synthetic_flag=1` exclusions). **Dependency: T018, T020, T025, T030.**
- [ ] T036 [P] Add unit tests for generator edge cases in `tests/unit/`: depth cap with warning (not crash) when complexity exceeds generator maximum, and 60-second timeout recording as failure outlier without blocking the batch (Edge Cases 1–2), plus the timeout enforcement in `code/main.py` (T043 concern folded here).
- [ ] T037 Run the full documented workflow from `quickstart.md` on the complete 500-query set across all source types and depths 1–4+ within the CPU-only budget; confirm all pipeline stages, tests, and artifact checks pass, and record actual outcomes in `data/results/research_summary.md`. This is the reproducibility re-run and paper-stage handoff (methods, results, figures, and limitations are documented for the paper pipeline). **Dependency: all above.**

---

## Removed / corrected tasks (do not re-add)

- **T039 (state.yaml generator)** — removed: research scripts must not write `state/...`; the platform derives artifact hashes at verification time.
- **T042 (secondary synthetic fallback in query generation)** — folded into T016c: fallback logic lives only in the loader, is flagged, and defaults to abort; no second silent path.
- **T040/T041 (streaming, fail-loudly)** — already satisfied inside T016c as rewritten; no separate tasks.
- **T043 (60s timeout)** — folded into T036.
- **T044 (circularity check)** — already satisfied by T027.
- **T028–T032 fragments** — consolidated into T030 (plots) and T033 (summary).

## Dependencies and requirement coverage

- **FR-001** (real latency, throttling): T016 (corrected), T016b, T008–T011.
- **FR-002** (integer depth): T006/T017, persisted by T021.
- **FR-003** (execution log schema): T015, T021, T004, T013.
- **FR-004/FR-008** (translation error, independent ground truth): T007, T024, T025, T027, T022.
- **FR-005** (ANOVA/ANCOVA + Tukey): T018 (depends on T021).
- **FR-006** (interaction plot): T030.
- **FR-007** (sensitivity sweep): T020 (depends on T021).
- **SC-001–SC-004**: T018, T025/T033, T018, T020 respectively.
- **Execution order**: T001/T003/T004 → T016 → T016b/T008 → T021 → T018/T020 → T030 → T033 → T037. Verified tasks (T002, T005–T007, T009–T015, T017, T024–T027) are preserved as complete.

## Revision behavior

Checked tasks retain their status only where their artifacts match the current specification; the five verifier-rejected tasks (T001, T003, T004, T020, T021) and the FR-001-violating throttle fallback (T016) are reopened with precise repair instructions. No requirement was weakened and no test was removed to pass review.
