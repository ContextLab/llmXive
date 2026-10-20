# Tasks: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

**Inputs**: Active `spec.md`, `plan.md`, and existing artifacts under `specs/001-llmxive-follow-up-extending-memory-is-re/`.
**Re-plan note**: The prior tasks.md was rejected for format (no canonical checkbox items detected). This revision preserves all scientific requirements, paths and verification steps while emitting the complete task list as canonical `- [ ] T###` checkbox items with unique IDs.

## Phase 0: Project setup

- [ ] T000 [P1] [US0] Create a pinned `code/requirements.txt` enumerating all Python dependencies (including exact versions of `datasets`, `pandas`, `networkx`, `sentence-transformers`, `transformers`, `bitsandbytes`, `llama-cpp-python`, `scipy`, `numpy`, `pytest`, `timeout-decorator`). This satisfies the Constitution's reproducibility requirement and the plan's project‑structure expectation. <!-- FAILED: unspecified -->
    - Verification: `pip install -r code/requirements.txt` succeeds in a fresh virtualenv; `tests/unit/test_requirements_pin.py` confirms no version conflicts.

## Phase 1: Data preparation & graph construction (FR‑001, FR‑007)

- [ ] T001 [P1] [US1] Download the LoCoMo benchmark subset via a strict loader with no synthetic fallback, producing `data/raw/locomo.csv`. <!-- FAILED: unspecified -->
    - Implement `code/data/download_locomo.py` calling `load_locomo_strict()` which uses `datasets.load_dataset(..., split=..., streaming=True)` (streaming to stay within RAM limits); on failure it MUST raise — never fall back to synthetic/mock data.
    - Verify presence of expected columns (`task_id`, `question`, `context`, `ground_truth`); raise `ValueError("Dataset schema mismatch")` if missing.
    - Compute SHA‑256 of `data/raw/locomo.csv` and record it in the project state file `state/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re.yaml` under `artifact_hashes`.
    - Verification: run `python code/data/download_locomo.py`; assert `data/raw/locomo.csv` exists, is non‑empty, and `tests/integration/test_data_loader_audit.py` passes.

- [ ] T002 [P1] [US1] Construct immutable per‑task memory graphs and generate noisy variants (FR‑001, plan Phase 1). <!-- FAILED: unspecified -->
    - Implement `code/models/embedding_utils.py` providing Model A (`all-MiniLM-L6-v2`) for graph construction and Model B (`all-mpnet-base-v2`) for edge scoring.
    - Implement `code/data/generate_graphs.py`: parse each task context into sentence nodes; select the top‑K (K=50) most relevant sentences by similarity to the question using Model A; build directed edges via Model A similarity; write `data/intermediate/graphs_raw.json` keyed by `task_id`.
    - Compute edge‑coherence scores and write `data/intermediate/graph_validation_scores.json`; flag tasks below the coherence threshold as `invalid_graph` and exclude them from strategy runs.
    - Implement `code/data/generate_noisy_graphs.py`: apply `inject_noise` that **replaces** a reproducible proportion (5 %) of existing edges with random edges (seed 42) per FR‑001; output a single file `data/processed/noisy_graphs.json`. The replacement semantics are aligned with FR‑001; the spec's "adding edges" description is flagged for amendment.
    - Verification: `tests/unit/test_graph_utils.py::test_serialization` and `test_noise_reproducibility` pass (same seed → identical noisy graph); schema validation against `contracts/noisy_graphs.schema.yaml` passes.

- [ ] T003 [P1] [US1] Implement the three traversal strategies (Full, Lazy, Greedy) with degenerate‑input handling (FR‑002, FR‑003, FR‑004, US‑4 edge cases). <!-- FAILED: unspecified -->
    - Implement `code/models/graph_traversal.py`:
        * **Full** – traverses all nodes of the constructed sampled graph.
        * **Lazy** – expands edges only when Model B score > evidence threshold; hard cap 50 nodes.
        * **Greedy** – selects top‑k edges by Model B score; hard cap 50 nodes.
    - All strategies load the SAME `data/intermediate/graphs_raw.json` instance per `task_id`.
    - Handle disconnected graphs (unreachable target → flag `unresolved`), zero‑edge/single‑node graphs (no division‑by‑zero; flag `degenerate`), and self‑loops.
    - Verification: `tests/unit/test_traversal.py` passes on known graph structures including degenerate cases; `tests/unit/test_degenerate_graphs.py` passes.

- [ ] T004 [P1] [US1] Implement the execution runner with per‑task timeout, strict data‑flow checks, and evidence‑threshold logging (FR‑007, FR‑003 logging). <!-- FAILED: unspecified -->
    - Implement `code/analysis/runner.py` with a `timeout_wrapper` using `signal` enforcing the 30‑minute per‑task cap; on timeout log `TIMEOUT` status and continue.
    - Runner depends on completed implementation of T003 (must be built before T004).
    - Before execution, assert `data/intermediate/graphs_raw.json` exists and is non‑empty; abort with descriptive error if missing. For noisy runs, assert `data/processed/noisy_graphs.json` exists first.
    - Initialize the quantized CPU LLM (e.g., Llama‑3‑8B‑4bit via `llama‑cpp‑python`) for **final answer generation ONLY**; extract `token_count` from model metadata for every execution (Constitution Principle VI).
    - Log per‑task records conforming to `contracts/execution_log.schema.yaml` (includes `strategy`, `latency_ms`, `token_count`, `evidence_threshold` for Lazy, `noise_applied`, `hard_cap_applied`, `construction_model`, `scoring_model`).
    - Verification: `tests/unit/test_timeout_handler.py` and `tests/integration/test_hard_timeout.py` pass; `tests/integration/test_pipeline_order.py` confirms correct ordering.

- [ ] T005 [P1] [US1] Run the Full baseline end‑to‑end on a small real subset, producing the first real results (US‑1). <!-- FAILED: unspecified -->
    - Implement `code/run_baseline.py` executing the Full strategy on the clean graphs for a small fixed subset (first N tasks, N documented in output), producing `data/processed/baseline_results.csv` with columns `task_id`, `strategy`, `nodes_visited`, `accuracy`, `latency_ms`, `status` (no `token_count` per `baseline_results.schema.yaml`).
    - Support a `--streaming` flag processing tasks in batches with intermediate results written to disk.
    - Verification: `tests/unit/test_baseline_schema.py::test_baseline_columns` passes; every task row has a recorded accuracy (0.0–1.0) and latency; `tests/integration/test_e2e_pipeline.py` passes on the small subset.

## Phase 2: Complete the study and validate its evidence

- [ ] T009 [P1] [US4] Run the robustness and edge‑case regression suite immediately after baseline (US‑4, FR‑007). <!-- FAILED: unspecified -->
    - Use `code/scripts/generate_edge_case_dataset.py` / `generate_mixed_robustness_dataset.py` to produce datasets with disconnected graphs, zero‑edge graphs, and timeout‑prone tasks (derived from real graphs, not fabricated).
    - Execute the runner on these datasets; ensure no crashes and that statuses (`completed`, `unresolved`, `degenerate`, `timeout`) are logged.
    - Record counts of timed‑out vs. completed tasks for SC‑005.
    - Verification: `tests/integration/test_end_to_end_robustness.py` and `tests/integration/test_edge_case_regression.py` pass; no division‑by‑zero or hangs.

- [ ] T006 [P2] [US2] Run the complete strategy comparison: Full, Lazy (with sensitivity sweep), and Greedy on the full task set, clean and noisy (FR‑002–FR‑004, SC‑001, SC‑002). <!-- FAILED: unspecified -->
    - Run Full baseline on the full task set → `data/processed/baseline_results.csv`.
    - Run Lazy via `code/run_lazy.py` with sweep thresholds `0.6,0.7,0.8` → `data/processed/lazy_results.csv` and combined `data/processed/lazy_sweep_results.csv` (includes `evidence_threshold` column). Each run logs the exact threshold used.
    - Run Greedy via `code/run_greedy.py` → `data/processed/greedy_results.csv`.
    - Run noisy variants: Full on noisy graphs → `data/processed/noisy_baseline_results.csv`; Lazy on noisy graphs → `data/processed/noisy_lazy_results.csv`.
    - Verification: Lazy/Greedy CSVs validated against `contracts/lazy_results.schema.yaml` and `contracts/greedy_results.schema.yaml` respectively (both require `latency_ms` and omit `token_count`). Full results validated against `baseline_results.schema.yaml`. No schema conflicts.

- [ ] T007 [P3] [US3] Perform the statistical analysis: paired tests, Point‑Biserial correlation, binning/inflection, power analysis (FR‑005, FR‑006, SC‑003, SC‑004). <!-- FAILED: unspecified -->
    - Implement `code/analysis/stats.py`:
        * Normality check (Shapiro‑Wilk) to select paired t‑test or Wilcoxon.
        * Bonferroni correction.
        * `calc_point_biserial()` between `nodes_visited` and success.
        * `bin_tasks_by_nodes(min_bin_size=3)` with merging to enforce n ≥ 3.
        * `find_inflection_point()` reporting first bin with mean accuracy < 95 % of baseline **only when** p < 0.05; otherwise report overall trend.
        * Post‑hoc power analysis note.
    - Output clean analysis → `data/processed/stats_clean.json`; noisy robustness analysis → `data/processed/stats_noisy.json`, both conforming to `contracts/statistical_result.schema.yaml` and `contracts/stats_summary.schema.yaml`.
    - Aggregate into `data/processed/stats_final.json` via `code/scripts/generate_stats_report.py`.
    - Verification: `tests/unit/test_stats.py::test_statistical_outputs`, `tests/unit/test_binning_edge_cases.py`, `tests/unit/test_bin_merging.py` pass; tasks run only after T006 results exist.

- [ ] T008 [P2] [US2] Analyze threshold sensitivity and generate figures, also verify Constitution VI reduction target (40‑50 % node reduction). <!-- FAILED: unspecified -->
    - Implement `code/scripts/analyze_sensitivity.py` comparing accuracy and node counts across sweep thresholds → `data/processed/sensitivity_analysis.json`.
    - Implement `code/scripts/plot_sensitivity.py` producing:
        * `docs/plots/threshold_sensitivity.png` (Accuracy vs. Nodes Visited per threshold).
        * Additional PNGs for accuracy delta and node‑reduction percentage per strategy vs. baseline.
    - Verify that Lazy and Greedy achieve at least a 40 % reduction in `nodes_visited` relative to Full (asserted in the script; failure aborts the run).
    - Verification: JSON and PNG artifacts exist and are generated directly from T006/T007 outputs; `tests/unit/test_sensitivity_verification.py` checks reduction target.

- [ ] T010 [P1] [US1] Validate contracts and data integrity across all artifacts. <!-- FAILED: unspecified -->
    - Extend `tests/contract/test_schema_validation.py` to validate every results CSV and stats JSON against the schemas in `specs/001-llmxive-follow-up-extending-memory-is-re/contracts/`.
    - Run `code/scripts/audit_no_fallbacks.py` scanning `code/data/` and `code/models/` for any try/except or conditional synthetic‑data fallback; the script must raise if fallback logic is found.
    - Verify streaming vs. in‑memory loader equivalence on a small fixed subset via `tests/integration/test_streaming_integrity.py`.
    - Verification: all contract tests, the audit script (exit 0), and integrity tests pass.

- [ ] T011 [P3] [US1] Aggregate results and write the methods/results account. <!-- FAILED: unspecified -->
    - Implement `code/scripts/aggregate_results.py` → `data/processed/report_data.json` with keys `accuracy_delta`, `node_reduction_pct`, `statistical_significance`, `inflection_point` (validated by `tests/unit/test_report_data.py::test_report_schema`).
    - Write `docs/research_report.md` describing methods, actual measured results (linked to result files), sensitivity sweep, noisy‑graph robustness check, negative findings, and limitations (associational framing, fixed sample size / power limits, benchmark ground‑truth validity, top‑K sampling scope). Include a table summarizing node‑reduction percentages confirming the 40‑50 % target.
    - Verification: report cites actual values from `data/processed/` artifacts; `code/scripts/verify_docs.py` passes.

- [ ] T012 [P1] [US1] Re‑run the documented workflow end‑to‑end and document the paper‑stage handoff. <!-- FAILED: unspecified -->
    - Update `code/scripts/run_pipeline.py` to orchestrate: download → graphs → noise → baseline → lazy (sweep) → greedy → noisy runs → stats → report, with explicit dependency assertions (`validate_intermediate_artifacts()` checking `graphs_raw.json` and `noisy_graphs.json` before execution) and correct ordering (stats only after all result CSVs).
    - Re‑run the full pipeline from declared inputs; confirm all expected artifacts regenerate and `code/scripts/verify_reproducibility.py` confirms deterministic outputs (fixed seeds).
    - Document the paper‑stage handoff in `docs/research_report.md`: required tables (strategy comparison, statistical tests, sensitivity sweep), figures (`threshold_sensitivity.png`), and the limitations section — layout/PDF/publication remain with the paper pipeline.
    - Verification: `tests/integration/test_pipeline_order.py` and a clean re‑run produce all artifacts listed above.

## Phase 3: Reproducible results and paper handoff (summary)

- Dependencies and requirement coverage remain as previously listed, now including T000 for `requirements.txt`.
- Execution order (explicit): T000 → T001 → T002 → T003 → T004 → T005 → T009 → T006 → T007 → T008 → T010 → T011 → T012.