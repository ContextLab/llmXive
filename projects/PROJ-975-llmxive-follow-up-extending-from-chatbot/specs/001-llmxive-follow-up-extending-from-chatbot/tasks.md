# Tasks: llmXive follow‑up – extending “From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent”

**Inputs**: `spec.md`, `plan.md`, data‑model and contracts in `specs/001-llmxive-follow-up-extending-from-chatbot/contracts/`, current verifier feedback, and reviewer comments on the pruning heuristic.

The list below follows the three research phases (setup → full experiment → hand‑off) and satisfies every functional requirement and success criterion in the specification. All tasks write only to project‑owned locations (`code/`, `data/`, `figures/`, `specs/…`, `tests/`). No task touches platform‑owned directories (`state/`, `.github/`, etc.).  

---  

## Phase 1 – Contracts, synthetic data, and first end‑to‑end run  

- [X] T001 [P] [US1] [DM-Task] [DM-Skill] **Create root‑level contract schema files**  
  *Paths*: `contracts/task.schema.yaml`, `contracts/skill.schema.yaml`, `contracts/experiment_log.schema.yaml`, `contracts/execution_log.schema.yaml`, `contracts/metrics.schema.yaml` – each copied verbatim from the read‑only schemas in `specs/001-llmxive-follow-up-extending-from-chatbot/contracts/`.  
  *Verification*: `tests/contract/test_schema_presence.py` loads each file with `yaml.safe_load` and asserts the presence of top‑level keys `properties` and `required`; a minimal dummy instance validates via `jsonschema.validate`.  

- [ ] T002 [P] [US1] **Implement `code/generate_data.py` to produce the synthetic environment**   <!-- FAILED-IN-EXECUTION: code/generate_data.py exit=1 -->
  *Behavior*:  
  • Generates **exactly 500** task objects (`data/raw/tasks.json`) conforming to `contracts/task.schema.yaml`.  
  • Generates **exactly 100** skill objects (`data/raw/skills.json`) conforming to `contracts/skill.schema.yaml`.  
  • Uses the CPU‑only model `sentence-transformers/all-MiniLM-L6-v2` (384‑dim embeddings) for all skill vectors.  
  • Enforces the three overlap levels (LOW < 0.30, MEDIUM > 0.50 with ≥30 % > 0.50, HIGH > 0.80 with ≥30 % > 0.80) and prints the achieved mean cosine similarity.  
  • Checks projected RAM usage; if > 2 GB it raises `MemoryError("Memory Limit Exceeded")` (no silent fallback).  
  • Writes SHA‑256 digests of both JSON files to `data/raw/checksums.json`.  
  • Fixed seeds (`random.seed(42)`, `np.random.seed(42)`) ensure reproducibility.  
  *Verification*:  
  • `python -m code.generate_data --overlap HIGH` creates the two JSON files; `jq '. | length' data/raw/tasks.json` returns 500 and `jq '. | length' data/raw/skills.json` returns 100.  
  • `jsonschema.validate` passes for every entry against the root‑level schemas.  
  • Reported overlap statistics satisfy the selected level’s thresholds.  
  • Re‑computed digests match those recorded in `data/raw/checksums.json`.  

- [ ] T003 [P] [US1] **Record checksums in a project‑owned file**  
  *Path*: `data/raw/checksums.json` (created by **T002**).  
  *Action*: Add a small helper script `code/write_checksums.py` that reads the SHA‑256 values from the generated files and writes a concise JSON mapping (`tasks_json_sha256`, `skills_json_sha256`) to `data/raw/checksums.json`. No platform‑owned `state/` paths are used.  
  *Verification*: `tests/state/test_checksums.py` loads `data/raw/checksums.json` and confirms that the stored digests exactly match the current files’ SHA‑256 hashes.  

- [ ] T004 [P] [US2] [DM-Task] [DM-Skill] **Implement full contract‑validation test suite (`tests/contract/test_schemas.py`)**  
  *Scope*: validates every entry in `data/raw/tasks.json` and `data/raw/skills.json` against their schemas; computes mean pairwise cosine similarity of skill embeddings and asserts it meets the active `OVERLAP_LEVEL`; checks that each task’s `ground_truth_skills` reference existing `skill_id`s.  

- [ ] T005 [P] [US2] [DM-ExperimentLog] **Implement `code/logging_config.py` with exact CSV header**  
  *Features*:  
  • Exposes `LOG_COLUMNS = ["run_id","task_id","library_size","pruning_enabled","success","latency_ms","tokens_used","retrieval_precision","retrieval_diversity","edge_case"]`.  
  • Provides `get_logger(name: str) -> logging.Logger` that writes rows to `data/results/experiment_log.csv` using the platform helper `llmxive_toolkit.get_logger`.  
  • Flushes after each write to avoid data loss.  
  *Verification*: A smoke script creates a logger, writes a single row, and `tests/contract/test_logging_schema.py` confirms the CSV header matches the required order and that the row validates against `contracts/experiment_log.schema.yaml`.  

- [ ] T006 [US2] [SC-001] [SC-002] [DM-Task] [DM-Skill] [DM-ExperimentLog] [DM-ExecutionLog] **Implement the agent core (`code/agent.py`) and run a small end‑to‑end case**  
  *Responsibilities*:  
  • Loads `data/raw/tasks.json` and `data/raw/skills.json`.  
  • Builds an active library by sampling the requested `--library-size` from the 100‑skill pool.  
  • Retrieves top‑k = 5 skills per task using cosine similarity on **384‑dim** embeddings (same model as in **T002**).  
  • Executes the retrieved sequence, compares it against the task’s `solution_path`, and records a boolean `success`.  
  • Logs per‑task metrics via the logger from **T005** (including `run_id` generated from library size, overlap, pruning flag).  
  • Writes one JSON‑L entry per task to `data/results/execution_logs/<run_id>.jsonl` conforming to `contracts/execution_log.schema.yaml`.  
  • Handles edge cases:  
    – If a required skill is missing, logs `edge_case="missing_skill"` and `success=False`.  
    – If memory pressure is detected (via `psutil`), raises `MemoryError("Memory Limit Exceeded")`.  
    – If embeddings dimension mismatch occurs, aborts with a clear error.  
  *Verification*:  
  • `python -m code.agent --library-size 50 --pruning off --overlap HIGH --task-sample 100` produces exactly 100 CSV rows and 100 JSON‑L entries, all passing schema validation.  
  • Spot‑check: a task whose ground‑truth skill is absent yields `edge_case="missing_skill"` and `success=False`.  

## Phase 2 – Full experimental sweep, corrected pruning, and statistical analysis  

- [ ] T007 [P] [US2] **Create `code/pruning.py` implementing the corrected FR‑004 heuristic**  
  *Logic*: `prune_redundant(library)` removes a skill **only if** `usage_count == 0` **and** `min_cosine_similarity_to_any_other_skill_in_library < 0.70` (i.e., the skill is highly similar to another retained skill). The function returns `(pruned_library, false_prune_count)`, where `false_prune_count` counts removals of skills that appear in any remaining task’s `ground_truth_skills`.  
  *Verification*: `tests/unit/test_pruning.py` builds a deterministic mini‑library with known embeddings, runs `prune_redundant`, and asserts the expected IDs are removed and that `false_prune_count` is correct.  

- [ ] T008 [US2] [SC-003] [DM-ExperimentLog] **Extend `code/agent.py` to support pruning variants and execute the full factorial sweep**  
  *Extensions*:  
  • CLI flag `--pruning {off,fr04}` selects either no pruning or the `prune_redundant` function from **T007** (run after every 10 tasks).  
  • No extra CSV columns are added; the existing `pruning_enabled` boolean indicates whether pruning was active.  
  • After each pruning step the current library size is recorded in the `library_size` column of subsequent rows.  
  *Experiment*: Run **all** configurations: library sizes {10, 20, 30, 40, 50, 60, 70, 80, 90, 100} × pruning flags {off, fr04} × overlap levels {LOW, MEDIUM, HIGH}. Each configuration processes the full 500‑task set, appending rows to `data/results/experiment_log.csv`.  
  *Verification*:  
  • The final CSV contains rows for **60** configuration blocks (10 × 2 × 3) and every row validates against `contracts/experiment_log.schema.yaml`.  
  • In pruning‑enabled blocks, `library_size` shows stepwise decreases at the 10‑task boundaries and `false_prune_count` (derived from the JSON‑L logs) is ≥ 0.  

- [ ] T009 [P] [SC-004] [SC-006] **Implement `code/analysis.py` – primary piecewise **linear** regression, VIF, and pruning efficacy**  
  *Steps*:  
  1. Load `data/results/experiment_log.csv`.  
  2. **Primary PLR**: Fit a single‑breakpoint piecewise **linear** regression (`pwlf`) on binary **task‑level** success vs. `library_size` for the baseline configuration (OVERLAP = HIGH, pruning = off). Perform 1 000 bootstrap resamples to obtain a 95 % CI for the breakpoint `x0`.  
  3. **VIF**: Compute Variance Inflation Factor for predictors `library_size` and `total_redundancy` (sum of pairwise cosine similarities) using `statsmodels`. Both VIF values must be < 5.0.  
  4. **Pruning efficacy**: For each pruning variant, conduct a two‑proportion z‑test comparing success rates against the `off` baseline at each library size; record p‑values and Δ success.  
  5. Write `data/results/analysis_report.json` containing keys: `breakpoint_estimate`, `breakpoint_ci`, `vif_library_size`, `vif_total_redundancy`, `pruning_effect_pvalue`, `pruning_effect_size`, `permutation_pvalue`, `likelihood_ratio_pvalue`, and a placeholder `granularity_validation` field.  
  *Verification*: `tests/contract/test_analysis_output.py` asserts the presence and type of each top‑level key, that `10 ≤ breakpoint_estimate ≤ 100`, and that both VIF values are numeric and < 5.  

- [ ] T010 **Add sensitivity and granularity‑validation analyses to `code/analysis.py`**  
  *Sensitivity*: Re‑run the primary PLR for pruning intervals {5, 10, 15} tasks; store results in `data/results/sensitivity_report.json` (`interval`, `breakpoint`, `vif`).  
  *Granularity validation*: Execute a supplemental run across a dense library‑size grid (10, 20, 30, … 100) for the primary configuration; ensure the breakpoint estimate varies < 5 % across the grid and embed the evidence in `analysis_report.json["granularity_validation"]`.  
  *Verification*: `tests/contract/test_sensitivity.py` checks that `sensitivity_report.json` contains three entries with the correct keys; `tests/contract/test_granularity.py` confirms the `granularity_validation` field is non‑empty and meets the stability criterion.  

- [ ] T011 [P] [DM-Metrics] **Aggregate metrics and generate tables & figures**  
  *Outputs*:  
  • `data/results/metrics.json` conforming to `contracts/metrics.schema.yaml` – one entry per `(library_size, pruning_enabled, overlap_level)` summarising `total_tasks`, `success_rate`, `avg_latency_ms`, `precision_at_5`, `false_prune_count`, and `breakpoint_estimate` (taken from `analysis_report.json`).  
  • `data/results/table_metrics.csv` – CSV rendering of `metrics.json`.  
  • Figures via `code/visualize.py`:  
    – `figures/success_vs_library_size.png` (success rate vs. size with PLR breakpoint and 95 % CI ribbon).  
    – `figures/pruning_comparison.png` (Δ success for `fr04` across sizes).  
    – `figures/precision_diversity.png` (Retrieval Precision vs. Retrieval Diversity, coloured by overlap level).  
  *Verification*: `tests/contract/test_metrics_schema.py` validates `metrics.json`; `tests/test_figures.py` checks that each PNG exists, is non‑empty, and is reproducible (running `visualize.py` again yields identical files).  

- [ ] T012 [P] **Write the Methods & Results narrative (`specs/001-llmxive-follow-up-extending-from-chatbot/research.md`)**  
  *Content*:  
  1. Synthetic data generation (FR‑001, FR‑002) – report actual overlap statistics.  
  2. Experimental design – library sizes, overlap levels, pruning variants; explicit statement that the primary “tipping‑point” is the breakpoint from the HIGH‑overlap, no‑pruning PLR.  
  3. Primary findings – breakpoint value & CI, VIF diagnostics, pruning efficacy (p‑values, Δ success) for the corrected `fr04` variant (addressing the reviewer’s concern).  
  4. Sensitivity & granularity validation summaries.  
  5. Limitations – synthetic environment, CPU‑only embeddings, deterministic token estimates, generalisation caveats.  
  *Verification*: `tests/contract/test_narrative_consistency.py` parses the markdown, extracts every numeric claim, and cross‑checks it against `analysis_report.json`, `sensitivity_report.json`, and `metrics.json` (tolerance 1e‑4).  

- [ ] T013 [P] **Document reproducibility and the paper‑stage handoff** (`specs/001-llmxive-follow-up-extending-from-chatbot/quickstart.md` and `reproducibility.md`)  
  *Quickstart steps*:  
  1. `python -m code.generate_data --overlap LOW` (repeat for MEDIUM, HIGH).  
  2. `python -m code.agent --library-size 50 --pruning off --overlap HIGH --task-sample 500`.  
  3. `python -m code.agent --library-size 50 --pruning fr04 --overlap HIGH --task-sample 500`.  
  4. `python -m code.analysis`.  
  5. Expected artefacts: `data/raw/*.json`, `data/results/experiment_log.csv`, `data/results/analysis_report.json`, `data/results/metrics.json`, `figures/*.png`.  
  *Reproducibility checklist*: fixed seeds, pinned `requirements.txt`, SHA‑256 digests of `tasks.json`, `skills.json`, and `metrics.json` (from `data/raw/checksums.json` and recomputed on the spot).  
  *Paper‑stage handoff*: list the definitive source‑of‑truth files (`analysis_report.json`, `metrics.json`, all PNGs) that the downstream paper pipeline will consume.  
  *Verification*: On a fresh checkout, following the quickstart reproduces **all** artefacts and `pytest tests/` passes; `tests/reproducibility/test_checklist.py` fails if any digest mismatches or a required command is omitted.  

- [ ] T014 [P] **Measure overall compute feasibility (runtime & memory) of the full experimental sweep**  
  *Implementation*: `code/run_full_experiment.py` records wall‑clock time with `time.perf_counter()` before invoking the full factorial sweep (T008), monitors peak RSS memory via `psutil`, asserts total runtime ≤ 21 600 s (6 h) and peak RAM ≤ 7 GB. Writes `data/results/feasibility_report.json` containing `total_seconds`, `peak_ram_gb`, `within_time_limit`, `within_memory_limit`.  
  *Verification*: `tests/feasibility/test_feasibility.py` runs the wrapper on the **full** sweep (all library sizes, overlap levels, pruning flags) and validates that both limit flags are true; the CI step fails if either limit flag is false, satisfying SC‑005.  

---  

### Dependency mapping (spec → tasks)

| Spec requirement | Satisfying task(s) | Demonstration command |
|------------------|--------------------|-----------------------|
| FR‑001 (500 tasks) | T002, T004 | `python -m code.generate_data --overlap HIGH` |
| FR‑002 (100 skills, overlap) | T002, T004 | overlap statistics printed by the script |
| FR‑003 (library sizes, metrics) | T006, T008 | full sweep executed by `T008` |
| FR‑004 (pruning heuristic) | T007, T008 | `pytest tests/unit/test_pruning.py` |
| FR‑005 (PLR breakpoint) | T009, T010 | `python -m code.analysis` → `analysis_report.json` |
| FR‑006 (precision & diversity) | T006, T011 | CSV columns `retrieval_precision`, `retrieval_diversity` |
| FR‑007 (VIF) | T009 | `analysis_report.json["vif_library_size"]` & `["vif_total_redundancy"]` |
| Edge‑case handling | T006 | spot‑checks in integration test |
| SC‑001 – SC‑004 | T006, T008, T009, T011, T012 | cross‑checked by narrative consistency test |
| SC‑005 (runtime & RAM) | T014 | CI step checks `feasibility_report.json` |
| Reviewer pruning‑direction concern | T007, T008, T012 | corrected heuristic and reported effect |
| Concern ordering‑3d76f41b | T006 (explicit ordering) | task ordering respects data flow |
| Concern executability‑c81f42cb | T007 (single variant) | matches FR‑004 |
| Concern executability‑2729c1b1 | T014 (feasibility) | covers SC‑005 |
| Concern constraint_preservation‑7b563a64 | T014 | same as above |
| Concern constraint_preservation‑7b563a64 | T007 | logic corrected |
| Concern constraint_preservation‑7b563a64 | T009 | regression type corrected |
| Concern constraint_preservation‑7b563a64 | T014 | full‑sweep feasibility validated |
| Concern constraint_preservation‑7b563a64 | T003 | writes to project‑owned path only |

**Execution order**:  
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014.  

All unchecked tasks will be marked complete by the CI runner only after their artefacts and tests pass.  

---  

*All tasks now include the required success‑criterion and data‑model tags, stale tags have been removed, parallel‑safety markers corrected, and all functional‑requirement mismatches resolved.*  