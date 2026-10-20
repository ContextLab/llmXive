# Tasks: llmXive follow‑up – extending “From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent”

**Inputs**: `spec.md`, `plan.md`, data‑model and contracts in `specs/001-llmxive-follow-up-extending-from-chatbot/contracts/`, verifier rejections for T007/T011/T012/T015, reviewer feedback on the pruning heuristic, and the current artifact set.

This revision consolidates the previous 15‑task list into 12 substantive tasks. The four verifier‑rejected items (truncated `logging_config.py`, incomplete contract tests, missing schema files, missing data‑generation output) are folded into the reopened tasks below. On the reviewer's pruning objection: FR‑004 in the active specification is authoritative and is implemented exactly as written (min cosine < 0.70); the reviewer‑suggested redundancy variant (remove unused skills with a highly similar neighbor) is retained as a **comparison condition** so the study empirically tests both directions rather than silently rewriting the spec. All tasks write only to project‑owned paths (`code/`, `data/`, `figures/`, `specs/…`); none touch `state/` or platform‑owned paths.

---

## Phase 1 – Contracts, synthetic data, and first end‑to‑end run

- [ ] T001 [P] [US1] **Create root‑level contract schema files and presence tests**
  *Files*: `contracts/task.schema.yaml`, `contracts/skill.schema.yaml`, `contracts/experiment_log.schema.yaml`, `contracts/execution_log.schema.yaml`, `contracts/metrics.schema.yaml` – each an exact copy of the read‑only schemas in `specs/001-llmxive-follow-up-extending-from-chatbot/contracts/`.
  *Verification*:
  &nbsp;&nbsp;• `tests/contract/test_schema_presence.py` loads each file with `yaml.safe_load` and asserts the required top‑level keys (`properties`, `required`) exist.
  &nbsp;&nbsp;• `jsonschema.validate` passes for one minimal valid dummy instance per schema.
  &nbsp;&nbsp;• This task directly repairs the verifier rejection that the schema files were missing, which blocked contract validation in the previous round.

- [ ] T002 [P] [US1] **Implement and execute `code/generate_data.py`** – synthetic dataset generator producing the real raw data files (reopens rejected T015).
  *Behavior*:
  &nbsp;&nbsp;• Generates exactly 500 task objects into `data/raw/tasks.json` satisfying `contracts/task.schema.yaml` (FR‑001): unique `task_id`, 3–5 step `solution_path` and `ground_truth_skills` constructed independently of any retrieval logic.
  &nbsp;&nbsp;• Generates exactly 100 skill objects into `data/raw/skills.json` satisfying `contracts/skill.schema.yaml` (FR‑002), with 768‑dimensional embeddings from the CPU‑only `sentence-transformers` model `all-MPNet-base-v2`.
  &nbsp;&nbsp;• Overlap level (`LOW`, `MEDIUM`, `HIGH`) enforced per FR‑002 by iteratively adjusting skill descriptions/embeddings until mean pairwise cosine statistics meet the thresholds (LOW < 0.30; MEDIUM > 0.50 with ≥30% of pairs > 0.50; HIGH > 0.80 with ≥30% of pairs > 0.80); printed report includes the achieved statistics.
  &nbsp;&nbsp;• Memory guard: estimate embedding RAM before computation; if it would exceed 2 GB, raise `MemoryError("Memory Limit Exceeded")` — no silent fallback, no sampling substitution without an explicit tag.
  &nbsp;&nbsp;• After writing both JSON files, compute SHA‑256 digests and store them in `data/raw/checksums.json` (project‑owned; do NOT write to `state/`).
  &nbsp;&nbsp;• Random seeds (`random`, `numpy`) pinned (`SEED=12345`) for reproducibility.
  *Verification*:
  &nbsp;&nbsp;• `python -m code.generate_data --overlap HIGH` creates both files; record counts are exactly 500 and 100.
  &nbsp;&nbsp;• Every object in both files validates against the corresponding root‑level schema.
  &nbsp;&nbsp;• Printed overlap statistics satisfy the selected level's thresholds.
  &nbsp;&nbsp;• Re‑computed digests match `checksums.json`.
  &nbsp;&nbsp;• The file is complete and runnable end‑to‑end (the previous rejection was for a truncated script that never produced the outputs).

- [ ] T003 [P] [US1] **Implement complete contract‑validation tests** against the real data files (reopens rejected T011/T012).
  *Files*: `tests/contract/test_schemas.py`.
  *Scope*:
  &nbsp;&nbsp;• Loads the actual `data/raw/tasks.json` (not hard‑coded samples) and validates every entry against `contracts/task.schema.yaml`.
  &nbsp;&nbsp;• Loads the actual `data/raw/skills.json` and validates every entry against `contracts/skill.schema.yaml`, including the 768‑item embedding constraint.
  &nbsp;&nbsp;• Computes the mean pairwise cosine similarity of the generated skill embeddings and asserts it meets the active `OVERLAP_LEVEL` environment variable's FR‑002 thresholds.
  &nbsp;&nbsp;• Asserts every task's `ground_truth_skills` are disjoint from the retrieval logic (i.e., reference skill IDs that exist in `skills.json`).
  *Verification*:
  &nbsp;&nbsp;• `pytest tests/contract/test_schemas.py` fails if either JSON file is missing, malformed, schema‑violating, or off‑target on overlap; passes after T002 runs successfully.

- [ ] T004 [P] [US2] **Implement `code/logging_config.py` completely** (reopens rejected T007).
  *Features*:
  &nbsp;&nbsp;• A `get_logger(name)` factory returning a logger that writes CSV rows to `data/results/experiment_log.csv`.
  &nbsp;&nbsp;• The CSV header includes **all** columns required by `contracts/experiment_log.schema.yaml`, including `edge_case`: `run_id,task_id,library_size,pruning_enabled,success,latency_ms,tokens_used,retrieval_precision,retrieval_diversity,edge_case`.
  &nbsp;&nbsp;• Flushes after each write; the function body is complete (the previous rejection was for a truncated function ending mid‑construction).
  &nbsp;&nbsp;• Uses the platform helper `llmxive_toolkit.get_logger` for consistent formatting.
  *Verification*:
  &nbsp;&nbsp;• A smoke script writes one row; the created CSV header contains every required column name including `edge_case`.
  &nbsp;&nbsp;• `tests/contract/test_logging_schema.py` validates the written row against `contracts/experiment_log.schema.yaml`.

- [ ] T005 [P] [US2] **Implement `code/agent.py`** – core retrieval‑execution loop with edge‑case handling, and run a small end‑to‑end case.
  *Responsibilities*:
  &nbsp;&nbsp;• Reads `data/raw/tasks.json` and `data/raw/skills.json`; for a configuration (`--library-size`, `--pruning`, `--overlap LEVEL`) builds the active library as a sub‑sample of the 100‑skill set.
  &nbsp;&nbsp;• For each task, retrieves top‑k=5 skills by cosine similarity to the task‑description embedding; executes the retrieved sequence and compares against `solution_path` to record `success`.
  &nbsp;&nbsp;• Logs per‑task metrics via T004's logger: `latency_ms`, `tokens_used` (deterministic estimate from description/skill lengths — not a hard‑coded placeholder), `retrieval_precision` (Jaccard@5 vs ground truth, FR‑006), `retrieval_diversity` (inverse variance of the five cosine scores, FR‑006), and `edge_case` tags.
  &nbsp;&nbsp;• Writes one JSON‑L entry per task to `data/results/execution_logs/<run_id>.jsonl` conforming to `contracts/execution_log.schema.yaml`.
  &nbsp;&nbsp;• Edge cases (per spec): maximal overlap (mean pairwise ≥ 0.95) → tie‑break deterministically, report `retrieval_precision = 0.0` if no ground‑truth skill retrieved, tag `maximal_overlap`; missing ground‑truth skill → `success = false`, tag `missing_skill`, no hallucinated solution; memory‑guard trigger → propagate `MemoryError`, tag `memory_limit`.
  *Verification*:
  &nbsp;&nbsp;• `python -m code.agent --library-size 50 --pruning off --overlap HIGH --task-sample 100` produces exactly 100 CSV rows and 100 JSON‑L entries, each validating against its schema.
  &nbsp;&nbsp;• Spot‑check: a task with an absent ground‑truth skill gets `edge_case = "missing_skill"` and `success = false`.
  &nbsp;&nbsp;• This small run constitutes the first real end‑to‑end result rows under `data/results/`.

## Phase 2 – Full experimental sweep, pruning variants, and statistical analysis

- [ ] T006 [P] [US2] **Create `code/pruning.py` with both heuristic variants** (addresses the reviewer's contradiction concern).
  *Functions*:
  &nbsp;&nbsp;• `prune_fr04(library) -> (pruned_library, false_prune_count)`: implements FR‑004 exactly as specified — remove a skill if `usage_count == 0` AND `min_cosine_similarity_to_any_other_skill_in_library < 0.70`, triggered after every 10 tasks.
  &nbsp;&nbsp;• `prune_redundancy(library) -> (pruned_library, false_prune_count)`: the reviewer‑suggested variant — remove an unused skill whose **maximum** cosine similarity to any retained skill ≥ 0.70 (removes redundant near‑duplicates, retains unique capabilities).
  &nbsp;&nbsp;• `false_prune_count` counts removals of skills that appear in any remaining task's ground truth (false prunes).
  *Verification*:
  &nbsp;&nbsp;• `tests/unit/test_pruning.py` builds a deterministic mini‑library with known embeddings and asserts each function removes exactly the expected skill set and reports the correct `false_prune_count`.
  &nbsp;&nbsp;• A docstring/comment notes the spec‑vs‑reviewer tension and that the empirical comparison (T007/T008) resolves which direction helps.

- [ ] T007 [P] [US2] **Add pruning support to the agent and execute the full factorial sweep** (FR‑003, FR‑004).
  *Steps*:
  &nbsp;&nbsp;• Extend `code/agent.py` to accept `--pruning {off,fr04,redundancy}` and invoke the selected pruning function after every 10 tasks.
  &nbsp;&nbsp;• Log the current `library_size` after pruning; add a `pruning_variant` column (values `off`, `fr04`, `redundancy`) alongside the contract columns.
  &nbsp;&nbsp;• Execute all configurations: library sizes {10, 30, 50, 100} × pruning variants {off, fr04, redundancy} × overlap levels {LOW, MEDIUM, HIGH}, 500 tasks each, appending to `data/results/experiment_log.csv` (append‑only).
  *Verification*:
  &nbsp;&nbsp;• The CSV contains rows for all 36 configuration blocks; every row validates against `contracts/experiment_log.schema.yaml`.
  &nbsp;&nbsp;• In pruning‑enabled blocks, `library_size` shows stepwise decreases at 10‑task boundaries; `false_prune_count` ≥ 0 is recorded per block.

- [ ] T008 [P] [US3] **Implement `code/analysis.py`** – statistical pipeline (FR‑005, FR‑006, FR‑007).
  *Operations*:
  &nbsp;&nbsp;1. Load the full `experiment_log.csv`.
  &nbsp;&nbsp;2. **Primary PLR**: fit a single‑breakpoint piecewise linear regression (`pwlf`) on task‑level binary success vs `library_size` for the primary configuration (OVERLAP = HIGH, pruning = off, sizes 10/30/50/100), with 1,000 bootstrap resamples for a 95% CI on `x0` — the tipping point reported per SC‑004.
  &nbsp;&nbsp;3. **VIF**: compute the Variance Inflation Factor for `library_size` and `total_redundancy` (sum of pairwise cosines in the active library) via `statsmodels`; report both values (SC‑006 requires VIF < 5.0 for valid interpretation — report, do not silently drop a predictor).
  &nbsp;&nbsp;4. **Pruning efficacy**: for each variant (fr04, redundancy), compare success rates against the pruning‑off baseline at each library size with a two‑proportion test; record p‑values and deltas (SC‑003).
  &nbsp;&nbsp;5. Write the single source of truth `data/results/analysis_report.json` with keys: `breakpoint`, `breakpoint_ci`, `vif`, `pruning_results` (per‑variant `p_value`, `delta_success`), and `granularity_validation`.
  *Verification*:
  &nbsp;&nbsp;• `python -m code.analysis` exits 0 and produces the JSON.
  &nbsp;&nbsp;• `tests/contract/test_analysis_output.py` asserts presence/type of each top‑level key, `10 ≤ breakpoint ≤ 100`, and both VIF values present and finite.

- [ ] T009 [P] [US3] **Add sensitivity and granularity‑validation analyses** to `code/analysis.py`.
  *Details*:
  &nbsp;&nbsp;• Pruning‑interval sweep {5, 10, 15} tasks: re‑fit the primary PLR per interval; record `{interval, breakpoint, vif}` entries in `data/results/sensitivity_report.json`.
  &nbsp;&nbsp;• Granularity validation: run a random task subset across a denser library‑size grid (10‑unit increments: 10…100) for the primary configuration and verify breakpoint stability; results recorded as supplemental in `analysis_report.json["granularity_validation"]`.
  &nbsp;&nbsp;• The primary `analysis_report.json` reports only the baseline interval = 10 value as the official tipping point.
  *Verification*:
  &nbsp;&nbsp;• `sensitivity_report.json` contains three entries with the correct keys; `interval` values ∈ {5, 10, 15}.
  &nbsp;&nbsp;• Granularity run rows appear in `experiment_log.csv` with grid library sizes and validate against the schema.

- [ ] T010 [P] [US2] **Aggregate metrics and produce tables and figures from validated outputs**.
  *Artifacts*:
  &nbsp;&nbsp;• `data/results/metrics.json` conforming to `contracts/metrics.schema.yaml`: per‑configuration `library_size`, `pruning_enabled`, `total_tasks`, `success_rate`, `avg_latency_ms`, `precision_at_5`, `false_prune_count`, `breakpoint_estimate` (matching `analysis_report.json`).
  &nbsp;&nbsp;• `data/results/table_metrics.csv` – CSV rendering of `metrics.json`.
  &nbsp;&nbsp;• `figures/success_vs_library_size.png` – success rate vs library size with PLR breakpoint and 95% CI ribbon.
  &nbsp;&nbsp;• `figures/pruning_comparison.png` – success‑rate deltas for fr04 vs redundancy across library sizes.
  &nbsp;&nbsp;• `figures/precision_diversity.png` – Retrieval Precision vs Retrieval Diversity scatter, colored by overlap level.
  &nbsp;&nbsp;• All figures produced by `code/visualize.py` reading only the canonical JSON/CSV files — no hard‑coded numbers.
  *Verification*:
  &nbsp;&nbsp;• `tests/contract/test_metrics_schema.py` validates `metrics.json` against `contracts/metrics.schema.yaml`.
  &nbsp;&nbsp;• `tests/test_figures.py` asserts each figure exists and is non‑empty; re‑running `code/visualize.py` reproduces byte‑identical files.
  &nbsp;&nbsp;• Total pipeline runtime < 6 h and peak memory < 2 GB, recorded in the run log.

- [ ] T011 [P] [US3] **Write the methods & results narrative** in `specs/001-llmxive-follow-up-extending-from-chatbot/research.md`.
  *Content*:
  &nbsp;&nbsp;• Synthetic data generation (FR‑001, FR‑002) with achieved overlap statistics.
  &nbsp;&nbsp;• Experimental design: sizes × pruning variants × overlap levels; the primary‑configuration rule for the official tipping point.
  &nbsp;&nbsp;• Primary findings: breakpoint with CI, VIF diagnostics, pruning efficacy per variant (p‑values, deltas) — including an honest comparison of the spec's FR‑004 heuristic against the redundancy variant, per the reviewer's concern.
  &nbsp;&nbsp;• Sensitivity sweep and granularity‑validation summaries.
  &nbsp;&nbsp;• Explicit limitations: synthetic environment, CPU‑only embeddings, deterministic token estimates, causal claims bounded to the simulation.
  *Verification*:
  &nbsp;&nbsp;• A validation script cross‑checks every numeric claim in the narrative against `analysis_report.json` / `sensitivity_report.json` within 1e‑4.
  &nbsp;&nbsp;• The markdown links to the generated figures and tables.

## Phase 3 – Reproducible results and paper hand‑off

- [ ] T012 [P] [US3] **Document reproducibility and the paper‑stage handoff** in `specs/001-llmxive-follow-up-extending-from-chatbot/quickstart.md` and `reproducibility.md`.
  *Quickstart must contain*:
  &nbsp;&nbsp;1. `python -m code.generate_data --overlap LOW` (repeat for MEDIUM, HIGH).
  &nbsp;&nbsp;2. `python -m code.agent --library-size 50 --pruning off --overlap HIGH --task-sample 500` (and the fr04/redundancy variants).
  &nbsp;&nbsp;3. `python -m code.analysis`.
  &nbsp;&nbsp;4. Expected output locations (JSON, CSV, figures).
  &nbsp;&nbsp;5. Reproducibility notes: `OVERLAP_LEVEL` environment variable, `SEED=12345`, pinned `code/requirements.txt`.
  *Reproducibility checklist must contain*:
  &nbsp;&nbsp;• Fixed seeds; pinned package versions; SHA‑256 digests of `tasks.json`, `skills.json`, `metrics.json` (from `data/raw/checksums.json` and recomputation); the exact command sequence; a statement of the paper‑stage handoff (layout, PDF compilation, publication belong to the paper pipeline, with `analysis_report.json`, `metrics.json`, and `figures/` as the handoff artifacts).
  *Verification*:
  &nbsp;&nbsp;• On a fresh checkout, following the quickstart commands produces all artifacts and `pytest tests/` passes.
  &nbsp;&nbsp;• A checklist‑parsing test fails if any required entry is missing or a digest mismatches.

---

## Dependencies and requirement coverage

| Spec requirement | Satisfying task(s) | Demonstrating command |
|------------------|--------------------|----------------------|
| FR‑001 (500 tasks) | T002, T003 | `python -m code.generate_data --overlap HIGH` |
| FR‑002 (100 skills, overlap levels) | T002, T003 | overlap statistics report + `pytest tests/contract/test_schemas.py` |
| FR‑003 (sizes 10/30/50/100, metrics) | T005, T007, T010 | full sweep; `experiment_log.csv` row counts |
| FR‑004 (pruning heuristic) | T006, T007 | `pytest tests/unit/test_pruning.py` |
| FR‑005 (PLR breakpoint) | T008, T009 | `python -m code.analysis` → `analysis_report.json` |
| FR‑006 (precision & diversity) | T005, T010 | CSV columns validated by schema tests |
| FR‑007 (VIF) | T008 | `analysis_report.json["vif"]` |
| Edge cases (maximal overlap, missing skill, memory) | T002, T005 | spot‑checks in T005 verification |
| SC‑001–SC‑006 | T005, T007, T008, T010, T011 | analysis report + narrative cross‑check |
| Reviewer pruning‑direction concern | T006, T007, T008, T011 | comparative pruning results |

**Execution order**: T001 → T002 → T003 & T004 (parallel) → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012.

All tasks write only to project‑owned directories (`code/`, `data/`, `figures/`, `tests/`, `specs/…`). No task modifies `state/`, `.github/`, or platform‑owned paths; the platform derives artifact hashes at verification time.
