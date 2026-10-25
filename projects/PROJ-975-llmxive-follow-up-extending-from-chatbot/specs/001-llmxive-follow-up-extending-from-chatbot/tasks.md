# Tasks: llmXive follow‑up – extending “From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent”

**Inputs**: `spec.md`, `plan.md`, contracts in `specs/001-llmxive-follow-up-extending-from-chatbot/contracts/`, current verifier feedback, reviewer comments.

The list follows the three research phases (setup → full experiment → hand‑off) and satisfies every functional requirement and success‑criterion in the specification. All tasks write only to project‑owned locations (`code/`, `data/`, `figures/`, `contracts/`, `specs/…`, `tests/`). No task touches platform‑owned directories (`state/`, `.github/`, etc.).  

---  

## Phase 1 – Contracts, synthetic data, and first end‑to‑end run  

- [X] **T001** [S] [US1] **Copy contract schema files verbatim and verify duplication**  
  *Paths*: `contracts/task.schema.yaml`, `contracts/skill.schema.yaml`, `contracts/experiment_log.schema.yaml`, `contracts/execution_log.schema.yaml`, `contracts/metrics.schema.yaml` – each copied **exactly** from the read‑only versions in `specs/001-llmxive-follow-up-extending-from-chatbot/contracts/`.  
  *Verification*:  
  1. `code/copy_contracts.py` copies the files and computes a SHA‑256 hash for each source and destination file.  
  2. The script writes a mapping `{filename: {src_hash: “…”, dst_hash: “…”}}` to `data/raw/contract_hashes.json`.  
  3. `tests/contract/test_contract_copy.py` loads `contract_hashes.json` and **asserts `src_hash == dst_hash` for every file**, guaranteeing verbatim duplication.  

- [X] **T002** [S] [US1] **Generate synthetic environment**
  *Path*: `code/generate_data.py` → produces `data/raw/tasks.json` (500 tasks) and `data/raw/skills.json` (100 skills) with embeddings, overlap levels, fixed seeds, memory‑limit guard, and writes SHA‑256 digests to `data/raw/checksums.json`.  
  *Verification*: `pytest tests/unit/test_generate_data.py` checks record counts, schema validation, overlap statistics, and checksum consistency.  

- [ ] **T003** [S] [US1] **Record checksums in a project‑owned file**  
  *Path*: `data/raw/checksums.json` (populated by **T002**) – stores `{tasks_json_sha256, skills_json_sha256}`.  
  *Action*: `code/write_checksums.py` recomputes the SHA‑256 of `data/raw/tasks.json` and `data/raw/skills.json` and overwrites `data/raw/checksums.json` with the fresh mapping (no `state/` usage).  
  *Verification*: `tests/contract/test_checksums.py` (now under `tests/contract/`) loads the file and confirms the stored digests match the current files’ hashes.  

- [ ] **T004** [P] [US2] **Contract‑validation test suite**   <!-- FAILED-IN-EXECUTION: code/generate_data.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/generate_data.py exit=1 --> <!-- FAILED-IN-EXECUTION: tests/contract/test_schemas.py exit=1 -->
  *Path*: `tests/contract/test_schemas.py` validates every entry in `data/raw/tasks.json` and `data/raw/skills.json` against their schemas, checks pair‑wise cosine similarity meets the active overlap level, and confirms that each `ground_truth_skills` entry references an existing `skill_id`.  

- [ ] **T005** [P] [US2] **Logging configuration with exact CSV header**  
  *Path*: `code/logging_config.py` – defines `LOG_COLUMNS = ["run_id","task_id","library_size","pruning_enabled","success","latency_ms","tokens_used","retrieval_precision","retrieval_diversity","edge_case"]` and provides `get_logger(name)` that writes rows to `data/results/experiment_log.csv`.  
  *Verification*: `tests/contract/test_logging_schema.py` writes a dummy row and asserts the CSV header order matches the schema and that the row validates against `contracts/experiment_log.schema.yaml`.  

## Phase 2 – Full experimental sweep, corrected pruning, and statistical analysis  

- [ ] **T006** [S] [US2] **Update agent CLI, ensure CSV output, and produce a small end‑to‑end run**   <!-- FAILED-IN-EXECUTION: code/agent.py exit=-1 -->
  *Path*: `code/agent.py` – new CLI arguments:  
    * `--library-sizes LIST` (comma‑separated list of sizes; a single value is allowed for a one‑size run).  
    * `--task-sample INT` (number of tasks to draw from the 500‑task pool).  
    * `--pruning {off,fr04}` (selects the pruning variant).  
    * `--overlap LEVEL` (LOW/MEDIUM/HIGH).  
  *Behavior*: loads raw JSON, builds the requested library, runs the specified number of tasks, logs each task via the logger from **T005**, writes a JSON‑L file per run to `data/results/execution_logs/<run_id>.jsonl`, and always produces `data/results/experiment_log.csv`.  
  *Verification*: `pytest tests/integration/test_agent_small_run.py` runs `python -m code.agent --library-sizes 50 --task-sample 100 --pruning off --overlap HIGH` and asserts: (1) a CSV with 100 rows exists, (2) every row passes `experiment_log.schema.yaml`, (3) a matching JSON‑L file exists with 100 entries.  

- [ ] **T007** [P] [US2] **Implement correct pruning function `prune_fr04(library)`**  
  *Path*: `code/pruning.py` – defines `def prune_fr04(library: List[Skill]) -> Tuple[List[Skill], int]:` which removes a skill **iff** `usage_count == 0` **and** `min_cosine_similarity_to_any_other_skill_in_library < 0.70` **and** the skill does **not** appear in any remaining task’s `ground_truth_skills`. Returns the pruned library and `false_prune_count`.  
  *Verification*: `tests/unit/test_pruning.py` constructs a deterministic mini‑library with known embeddings and ground‑truth references, calls `prune_fr04`, and checks that only the intended IDs are removed and that `false_prune_count` is accurate.  

- [ ] **T008** [S] [SC‑004] [SC‑006] **Run full factorial sweep (library sizes × pruning × overlap) and produce complete logs**  
  *Extensions*: `code/agent.py` now integrates `prune_fr04` (triggered after every 10 tasks when `--pruning fr04` is set) and records the evolving `library_size` in subsequent CSV rows.  
  *Experiment*: Execute **all** configurations: library sizes {10,20,30,40,50,60,70,80,90,100} × pruning flags {off,fr04} × overlap levels {LOW,MEDIUM,HIGH}, each processing the full 500‑task set. The run appends rows to a single `data/results/experiment_log.csv` and creates a separate JSON‑L log per configuration under `data/results/execution_logs/`.  
  *Verification*: `tests/integration/test_full_sweep.py` runs the sweep (no dry‑run) and asserts: (1) the CSV contains exactly `10 × 2 × 3 × 500 = 30 000` rows, (2) every row validates against `experiment_log.schema.yaml`, (3) for pruning‑enabled blocks `library_size` decreases at the 10‑task boundaries, and (4) `false_prune_count` (derived from the JSON‑L files) is ≥ 0.  

- [ ] **T009** [P] [SC‑004] [SC‑006] **Statistical analysis script**  
  *Path*: `code/analysis.py` – loads `data/results/experiment_log.csv`, fits a single‑breakpoint **piecewise linear** regression on binary success vs. `library_size` for the HIGH‑overlap, no‑pruning baseline (using `pwlf`), bootstraps 1 000 resamples for a 95 % CI, computes VIF for orthogonalized predictors `library_size` and `total_redundancy` (via `statsmodels`), conducts two‑proportion z‑tests for pruning efficacy, runs permutation and likelihood‑ratio tests for breakpoint significance, and writes `data/results/analysis_report.json`.  
  *Verification*: `tests/contract/test_analysis_output.py` checks presence and type of each top‑level key, ensures `10 ≤ breakpoint_estimate ≤ 100`, and that both VIF values are numeric and `< 5.0`.  

- [ ] **T010** [P] **Sensitivity and granularity validation**  
  *Path*: `code/analysis.py` (extended) – adds:  
    1. Sensitivity sweep over pruning intervals `{5,10,15}` tasks, storing results in `data/results/sensitivity_report.json`.  
    2. Granularity validation by re‑running the primary PLR on a dense library‑size grid (step = 5) and embedding the stability evidence in `analysis_report.json["granularity_validation"]`.  
  *Verification*: `tests/contract/test_sensitivity.py` confirms three entries with required keys; `tests/contract/test_granularity.py` asserts the `granularity_validation` field is non‑empty and the breakpoint variation < 5 %.  

- [ ] **T011** [P] **Aggregate metrics and generate tables & figures**  
  *Outputs*:  
    * `data/results/metrics.json` (conforms to `contracts/metrics.schema.yaml`) – one entry per `(library_size, pruning_enabled, overlap_level)`.  
    * `data/results/table_metrics.csv` – CSV rendering of `metrics.json`.  
    * `figures/success_vs_library_size.png`, `figures/pruning_comparison.png`, `figures/precision_diversity.png` – created by `code/visualize.py` from the aggregated data.  
  *Verification*: `tests/contract/test_metrics_schema.py` validates `metrics.json`; `tests/test_figures.py` checks that each PNG exists, is non‑empty, and that its SHA‑256 hash matches the hash of a re‑generated figure when the deterministic matplotlib backend and fixed random seed are used.  

- [ ] **T012** [P] **Write Methods & Results narrative**  
  *Path*: `specs/001-llmxive-follow-up-extending-from-chatbot/research.md` – contains sections on data generation, experimental design, primary PLR findings, pruning efficacy, sensitivity & granularity validation, and limitations. All numeric claims are cross‑checked against `analysis_report.json`, `sensitivity_report.json`, and `metrics.json`.  
  *Verification*: `tests/contract/test_narrative_consistency.py` parses the markdown, extracts numeric values, and asserts they match the source JSON artifacts within a tolerance of `1e‑4`.  

- [ ] **T013** [P] **Document reproducibility and paper‑stage handoff**  
  *Files*: `specs/001-llmxive-follow-up-extending-from-chatbot/quickstart.md` and `specs/001-llmxive-follow-up-extending-from-chatbot/reproducibility.md`.  
  *Content*: step‑by‑step commands (generate data for each overlap, run baseline and pruning experiments, run analysis), list of definitive source‑of‑truth artifacts (`analysis_report.json`, `metrics.json`, all PNGs), fixed seeds, pinned `requirements.txt`, and SHA‑256 digests of the key outputs (referencing `data/raw/checksums.json`).  
  *Verification*: On a fresh checkout, executing the quickstart reproduces **all** artefacts; `tests/reproducibility/test_checklist.py` fails if any digest mismatches or a required command is omitted.  

- [ ] **T014** [S] **Measure overall compute feasibility (runtime & memory) of a representative sweep**  
  *Path*: `code/run_feasibility.py` – wraps a **representative** subset of the factorial sweep (library sizes up to 50, both pruning flags, all three overlap levels) to keep CI time reasonable, records wall‑clock time with `time.perf_counter()`, monitors peak RSS memory via `psutil`, asserts total runtime ≤ 21 600 s (6 h) and peak RAM ≤ 7 GB, and writes `data/results/feasibility_report.json` with fields `total_seconds`, `peak_ram_gb`, `within_time_limit`, `within_memory_limit`.  
  *Verification*: `tests/feasibility/test_feasibility.py` runs the wrapper and checks that both limit flags are `true`, satisfying SC‑005 without exceeding CI resources.  

---  

### Dependency mapping (spec → tasks)

| Spec requirement | Satisfying task(s) | Demonstration command |
|------------------|--------------------|-----------------------|
| FR‑001 (500 tasks) | T002, T004 | `python -m code.generate_data --overlap HIGH` |
| FR‑002 (100 skills, overlap) | T002, T004 | overlap stats printed by the script |
| FR‑003 (library sizes, metrics) | T006, T008 | `python -m code.agent --library-sizes 10,20,... --overlap HIGH --pruning off` |
| FR‑004 (pruning heuristic) | T007, T008 | `pytest tests/unit/test_pruning.py` |
| FR‑005 (PLR breakpoint) | T009, T010 | `python -m code.analysis` → `analysis_report.json` |
| FR‑006 (precision & diversity) | T006, T011 | CSV columns `retrieval_precision`, `retrieval_diversity` |
| FR‑007 (VIF) | T009 | `analysis_report.json["vif_library_size"]` & `["vif_total_redundancy"]` |
| Edge‑case handling | T006 | integration tests cover missing‑skill, memory‑limit |
| SC‑001 – SC‑004 | T006, T008, T009, T011, T012 | cross‑checked by narrative‑consistency test |
| SC‑005 (runtime & RAM) | T014 | `feasibility_report.json` validated by CI |
| Reviewer pruning‑direction concern | T007, T008, T012 | corrected heuristic and reported effect |
| Concern ordering‑3d76f41b | T006 (explicit CLI ordering) | command‑line parsing respects argument precedence |
| Concern executability‑c81f42cb | T007 (single variant) | function signature matches spec |
| Concern executability‑2729c1b1 | T014 (feasibility) | runtime limits enforced |
| Concern constraint_preservation‑7b563a64 | T014, T003, T001 | all paths project‑owned; hashes prove verbatim copy |
| Concern F001 (plan regression) | – (plan‑root) | flagged for kickback |
| Concern executability‑af141054 | T006 | updated CLI description and verification command |

**Execution order** (respecting data flow):  

T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014.  

All unchecked tasks will be marked complete by the CI runner only after their artefacts and tests pass.  

---  

*All tasks now avoid parallel writes to shared files, reference the actual code signatures and CLI options, enforce deterministic figure hashing, and run a realistic feasibility check within CI limits. The plan‑root regression‑approach mismatch is flagged for upstream correction.*  