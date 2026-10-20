# Tasks: llmXive follow‑up – extending “From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent”

**Inputs**: `spec.md`, `plan.md`, data‑model and contracts in `specs/001-llmxive-follow-up-extending-from-chatbot/contracts/`, reviewer comments, and the current (un‑checked) artifact set.

The list below follows the three‑phase research workflow (setup → full study → hand‑off).  
All tasks use the canonical checkbox format and include explicit verification steps.  
Unchecked boxes indicate work that still needs to be produced or verified.

---

## Phase 1 – Contracts, synthetic data, and first end‑to‑end run

- [ ] T001 [P] [US1] **Create root‑level contract schema files**  
  *Files*: `contracts/task.schema.yaml`, `contracts/skill.schema.yaml`, `contracts/experiment_log.schema.yaml`, `contracts/execution_log.schema.yaml`, `contracts/metrics.schema.yaml` – each must be an exact copy of the read‑only schemas located in `specs/001-llmxive-follow-up-extending-from-chatbot/contracts/`.  
  *Verification*:  
  &nbsp;&nbsp;• A pytest module (`tests/contract/test_schema_presence.py`) imports each file and parses it with `yaml.safe_load` – import must succeed without errors.  
  &nbsp;&nbsp;• `jsonschema.validate` against a minimal valid instance (one dummy object) for each schema passes.

- [ ] T002 [P] [US1] **Implement `code/generate_data.py`** – synthetic dataset generator.  
  *Behavior*:  
  &nbsp;&nbsp;• Generates exactly 500 task objects (`data/raw/tasks.json`) satisfying `task.schema.yaml`.  
  &nbsp;&nbsp;• Generates exactly 100 skill objects (`data/raw/skills.json`) satisfying `skill.schema.yaml`.  
  &nbsp;&nbsp;• Embeddings are computed with the CPU‑only `sentence‑transformers` model (`all‑MPNet‑base‑v2`).  
  &nbsp;&nbsp;• Overlap level (`LOW`, `MEDIUM`, `HIGH`) is enforced per FR‑002 by iteratively adjusting embeddings until the required mean pairwise cosine statistics are met (report printed).  
  &nbsp;&nbsp;• Before embedding, the script estimates RAM usage; if it would exceed 2 GB it raises `MemoryError("Memory Limit Exceeded")`. No silent fallback.  
  &nbsp;&nbsp;• After writing the two JSON files, compute SHA‑256 digests and store them in `data/raw/checksums.json`.  
  *Verification*:  
  &nbsp;&nbsp;• Running `python -m code.generate_data --overlap HIGH` creates the files; `wc -l` confirms 500 and 100 records respectively.  
  &nbsp;&nbsp;• `jsonschema.validate` on every object in both files passes against the corresponding schema.  
  &nbsp;&nbsp;• Printed overlap statistics satisfy the thresholds for the selected level.  
  &nbsp;&nbsp;• Re‑computing the digests matches the values saved in `checksums.json`.

- [ ] T003 [P] [US1] **Add contract‑validation tests** (`tests/contract/test_schemas.py`).  
  *Scope*:  
  &nbsp;&nbsp;• Loads `data/raw/tasks.json` and validates each entry against `contracts/task.schema.yaml`.  
  &nbsp;&nbsp;• Loads `data/raw/skills.json` and validates each entry against `contracts/skill.schema.yaml`.  
  &nbsp;&nbsp;• Computes the mean pairwise cosine similarity of the generated skill embeddings and asserts it meets the active `OVERLAP_LEVEL` (environment variable).  
  *Verification*:  
  &nbsp;&nbsp;• `pytest tests/contract/` fails if the JSON files are missing, malformed, or violate the overlap constraint, and passes when `generate_data.py` has run successfully.

- [ ] T004 [P] [US2] **Complete `code/logging_config.py`** with a functional `get_logger(name)` factory.  
  *Features*:  
  &nbsp;&nbsp;• Returns a `logging.Logger` that writes CSV rows to `data/results/experiment_log.csv`.  
  &nbsp;&nbsp;• CSV header includes **all** columns required by `contracts/experiment_log.schema.yaml`: `run_id,task_id,library_size,pruning_enabled,success,latency_ms,tokens_used,retrieval_precision,retrieval_diversity,edge_case`.  
  &nbsp;&nbsp;• Flushes after each write to guarantee durability.  
  &nbsp;&nbsp;• Uses the platform helper `llmxive_toolkit.get_logger` for consistent formatting.  
  *Verification*:  
  &nbsp;&nbsp;• A tiny script (`python -c "from code.logging_config import get_logger; get_logger('test').info({...})"`) creates a CSV file whose first line exactly matches the required header (order does not matter but all names present).  
  &nbsp;&nbsp;• `tests/contract/test_logging_schema.py` loads the CSV and validates the single row against `contracts/experiment_log.schema.yaml`.

- [ ] T005 [P] [US2] **Implement `code/agent.py`** – core experimental loop.  
  *Responsibilities*:  
  &nbsp;&nbsp;• Reads `data/raw/tasks.json` and `data/raw/skills.json`.  
  &nbsp;&nbsp;• For a given configuration (`--library-size`, `--pruning {false,fr04,redundancy}`, `--overlap LEVEL`) builds the active skill library (sub‑sample of the full 100‑skill set).  
  &nbsp;&nbsp;• For each task, retrieves the top‑k=5 skills by cosine similarity to the task description embedding.  
  &nbsp;&nbsp;• Executes the retrieved skills in order, compares the resulting sequence to the task’s `solution_path`, and records `success`.  
  &nbsp;&nbsp;• Logs per‑task metrics to the CSV logger from T004: latency (ms), deterministic token count (`tokens_used = 42` per call as a placeholder), `retrieval_precision` (Jaccard@5), `retrieval_diversity` (inverse variance of the five cosine scores), and `edge_case` tags (`missing_skill`, `maximal_overlap`, `memory_limit`, `null`).  
  &nbsp;&nbsp;• Writes a JSON‑L execution log entry per task to `data/results/execution_logs/<task_id>.jsonl` conforming to `contracts/execution_log.schema.yaml`.  
  &nbsp;&nbsp;• Edge‑case handling:  
  &nbsp;&nbsp;&nbsp;&nbsp;• If `OVERLAP_LEVEL` is **HIGH** and mean pairwise similarity ≥ 0.95, set `retrieval_precision = 0.0` and tag `edge_case = "maximal_overlap"`.  
  &nbsp;&nbsp;&nbsp;&nbsp;• If a required ground‑truth skill is absent from the active library, set `success = false`, `edge_case = "missing_skill"` and do **not** attempt hallucination.  
  &nbsp;&nbsp;&nbsp;&nbsp;• If the memory guard from T002 triggers during embedding, propagate the `MemoryError` and log `edge_case = "memory_limit"`.  
  *Verification*:  
  &nbsp;&nbsp;• Running `python -m code.agent --library-size 50 --pruning false --task-sample 100` produces exactly 100 rows in `experiment_log.csv` and 100 JSON‑L files; each row validates against `experiment_log.schema.yaml`, each JSON‑L entry validates against `execution_log.schema.yaml`.  
  &nbsp;&nbsp;• Manual spot‑check confirms that a task whose ground‑truth skill is missing receives the correct `edge_case` tag and `success = false`.

---

## Phase 2 – Full experimental sweep, pruning variants, and statistical analysis

- [ ] T006 [P] [US2] **Create `code/pruning.py`** with two heuristic functions.  
  *Functions*:  
  &nbsp;&nbsp;• `prune_fr04(library) -> (pruned, false_prune_count)`: implements FR‑004 exactly (remove skill if `usage_count == 0` **and** `min_cosine_similarity_to_any_other_skill < 0.70`).  
  &nbsp;&nbsp;• `prune_redundancy(library) -> (pruned, false_prune_count)`: removes an unused skill whose **maximum** cosine similarity to any other skill in the library ≥ 0.70 (the reviewer‑suggested variant).  
  *Verification*:  
  &nbsp;&nbsp;• `tests/unit/test_pruning.py` builds a deterministic mini‑library, calls each function, and asserts that the set of removed skill IDs matches the expected list and that `false_prune_count` is correct.

- [ ] T007 [P] [US2] **Add pruning support to the agent and run the full factorial sweep**.  
  *Steps*:  
  &nbsp;&nbsp;• Extend `code/agent.py` to accept `--pruning {off,fr04,redundancy}` and invoke the selected pruning function after every 10 tasks.  
  &nbsp;&nbsp;• Log the current `library_size` **after** pruning, and include a new column `pruning_variant` in the CSV (values: `off`, `fr04`, `redundancy`).  
  &nbsp;&nbsp;• Execute all configurations: library sizes {10, 30, 50, 100} × pruning variants {off, fr04, redundancy} × overlap levels {LOW, MEDIUM, HIGH}.  
  &nbsp;&nbsp;• Append every run to `data/results/experiment_log.csv` (append‑only).  
  *Verification*:  
  &nbsp;&nbsp;• After the sweep, `experiment_log.csv` contains rows for **all** 4 × 3 × 3 = 36 configuration blocks.  
  &nbsp;&nbsp;• Each row validates against `experiment_log.schema.yaml`.  
  &nbsp;&nbsp;• For any pruning‑enabled block, the `library_size` column shows a stepwise decrease at the 10‑task boundaries, and `false_prune_count` ≥ 0.

- [ ] T008 [P] [US3] **Implement `code/analysis.py`** – statistical pipeline.  
  *Operations*:  
  &nbsp;&nbsp;1. Load the full `experiment_log.csv`.  
  &nbsp;&nbsp;2. **Primary PLR**: Fit a piecewise linear regression with a single breakpoint (`x0`) on the binary success outcome vs. `library_size` for the **primary** configuration (OVERLAP = HIGH, pruning = off, sizes = 10/30/50/100). Use `pwlf` with 1 000 bootstrap resamples to obtain a 95 % CI for `x0`.  
  &nbsp;&nbsp;3. **VIF**: Compute the Variance Inflation Factor for the predictors “library_size” and “total_redundancy” (sum of pairwise cosines in the active library) using `statsmodels`. Ensure VIF < 5.0.  
  &nbsp;&nbsp;4. **Pruning efficacy**: For each pruning variant (fr04, redundancy) compare success rates against the baseline (pruning off) at each library size using a paired proportion test; record p‑values.  
  &nbsp;&nbsp;5. Write a single source‑of‑truth JSON file `data/results/analysis_report.json` containing:  
  ```json
  {
    "breakpoint": <float>,
    "breakpoint_ci": [<low>, <high>],
    "vif": {"library_size": <float>, "total_redundancy": <float>},
    "pruning_results": {
      "fr04": {"p_value": <float>, "delta_success": <float>},
      "redundancy": {"p_value": <float>, "delta_success": <float>}
    },
    "granularity_validation": {"supplemental": true, "details": "..."}
  }
  ```  
  *Verification*:  
  &nbsp;&nbsp;• Running `python -m code.analysis` exits with status 0 and produces the JSON file.  
  &nbsp;&nbsp;• `tests/contract/test_analysis_output.py` loads the JSON and asserts presence and type of each top‑level key, and asserts that `breakpoint` lies between 10 and 100 and that both VIF entries are < 5.0.

- [ ] T009 [P] [US3] **Add sensitivity sweep (pruning interval)** to `analysis.py`.  
  *Details*:  
  &nbsp;&nbsp;• For pruning intervals `{5, 10, 15}` tasks, re‑run the PLR on the same primary configuration and record the estimated breakpoint and VIF.  
  &nbsp;&nbsp;• Store results in `data/results/sensitivity_report.json` as a list of objects `{interval, breakpoint, vif}`.  
  &nbsp;&nbsp;• The primary `analysis_report.json` must still contain only the baseline interval = 10 (as required by the plan).  
  *Verification*:  
  &nbsp;&nbsp;• The sensitivity JSON exists and contains three entries with the correct keys; a sanity check script confirms that the `interval` field matches one of the three values.

- [ ] T010 [P] [US2] **Execute the full end‑to‑end pipeline and produce aggregated metrics**.  
  *Workflow*:  
  &nbsp;&nbsp;1. Run `generate_data.py` (T002) for each overlap level.  
  &nbsp;&nbsp;2. Run the full agent sweep (T007).  
  &nbsp;&nbsp;3. Run `analysis.py` (T008 + T009).  
  &nbsp;&nbsp;4. Aggregate per‑configuration metrics (total tasks, success_rate, avg_latency_ms, precision_at_5, false_prune_count, breakpoint_estimate) into `data/results/metrics.json` that conforms to `contracts/metrics.schema.yaml`.  
  *Verification*:  
  &nbsp;&nbsp;• `pytest tests/contract/` includes `test_metrics_schema.py` which validates the JSON file against `metrics.schema.yaml`.  
  &nbsp;&nbsp;• The reported `breakpoint_estimate` matches the value in `analysis_report.json`.  
  &nbsp;&nbsp;• Total runtime (measured via `time`) stays below 6 h on the CI runner and peak memory stays under 2 GB (recorded in CI logs).

- [ ] T011 [P] [US3] **Generate tables and figures** from `analysis_report.json` and raw logs.  
  *Artifacts*:  
  &nbsp;&nbsp;• `figures/success_vs_library_size.png` – line plot with PLR breakpoint and 95 % CI ribbon.  
  &nbsp;&nbsp;• `figures/pruning_comparison.png` – bar chart of success‑rate delta for fr04 vs. redundancy variant across sizes.  
  &nbsp;&nbsp;• `figures/precision_diversity.png` – scatter of Retrieval Precision vs. Retrieval Diversity colored by overlap level.  
  &nbsp;&nbsp;• `data/results/table_metrics.csv` – CSV rendering of `metrics.json`.  
  *Verification*:  
  &nbsp;&nbsp;• Each figure is produced by a script in `code/visualize.py` that reads only the canonical JSON/CSV files (no hard‑coded numbers).  
  &nbsp;&nbsp;• Re‑running the script reproduces identical files (pixel‑wise hash match).  
  &nbsp;&nbsp;• A pytest `test_figures.py` checks that the files exist and that their sizes are > 0 KB.

- [ ] T012 [P] [US3] **Write the methods & results narrative** in `specs/001-llmxive-follow-up-extending-from-chatbot/research.md`.  
  *Content*:  
  &nbsp;&nbsp;• Concise description of synthetic data generation (FR‑001, FR‑002).  
  &nbsp;&nbsp;• Detailed experimental design (library sizes, pruning variants, overlap levels).  
  &nbsp;&nbsp;• Primary findings: breakpoint value with CI, VIF diagnostics, pruning efficacy (p‑values, delta success).  
  &nbsp;&nbsp;• Supplementary sensitivity sweep summary.  
  &nbsp;&nbsp;• Explicit limitation statement about the synthetic environment and CPU‑only embeddings.  
  *Verification*:  
  &nbsp;&nbsp;• Every numeric claim (e.g., “breakpoint = 42.3”) is programmatically cross‑checked by a small validation script that loads `analysis_report.json` and asserts equality within 1e‑4.  
  &nbsp;&nbsp;• The markdown file includes hyperlinks to the generated figures and tables.

- [ ] T013 [P] [US3] **Update `specs/001-llmxive-follow-up-extending-from-chatbot/quickstart.md`** with reproducible command sequence.  
  *Must contain*:  
  &nbsp;&nbsp;1. `python -m code.generate_data --overlap LOW` (repeat for MEDIUM and HIGH).  
  &nbsp;&nbsp;2. `python -m code.agent --library-size 50 --pruning off --overlap HIGH --task-sample 500`.  
  &nbsp;&nbsp;3. `python -m code.agent --library-size 50 --pruning fr04 --overlap HIGH …` (similarly for redundancy).  
  &nbsp;&nbsp;4. `python -m code.analysis`.  
  &nbsp;&nbsp;5. Expected output locations (paths to JSON, CSV, figures).  
  &nbsp;&nbsp;6. Note on reproducibility: environment variable `OVERLAP_LEVEL`, random seed `SEED=12345`.  
  *Verification*:  
  &nbsp;&nbsp;• On a fresh checkout, following the markdown commands from start to finish produces all artifacts and `pytest` passes.  
  &nbsp;&nbsp;• The quickstart file is parsed by a CI lint step that checks for the presence of the three required commands and the seed definition.

---

## Phase 3 – Reproducible hand‑off to the paper pipeline

- [ ] T014 [P] [US3] **Create a reproducibility checklist** (`specs/001-llmxive-follow-up-extending-from-chatbot/reproducibility.md`).  
  *Checklist items*:  
  1. Fixed random seeds (`SEED`).  
  2. Exact package versions (`requirements.txt` pinned).  
  3. SHA‑256 hashes of `tasks.json`, `skills.json`, `metrics.json`.  
  4. Command‑line invocation logs (captured via `tee` during quickstart).  
  5. CI artifact URLs (if CI publishes them).  
  *Verification*:  
  &nbsp;&nbsp;• The CI job runs a script that parses this checklist and fails if any entry is missing or mismatched.

- [ ] T015 [P] [US3] **Archive the full experimental bundle** (`archive/experiment_bundle.zip`).  
  *Contents*: all source code, data files, logs, analysis JSON, figures, and the checklist.  
  *Verification*:  
  &nbsp;&nbsp;• A post‑run script computes the zip’s SHA‑256 and writes it to `archive/checksum.txt`.  
  &nbsp;&nbsp;• The checksum is referenced in `reproducibility.md`; a CI test confirms the two match.

---

### Dependency matrix (spec → task)

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| FR‑001 (500 tasks) | T002, T003 |
| FR‑002 (100 skills, overlap) | T002, T003 |
| FR‑003 (library sizes, metrics) | T005, T007, T010 |
| FR‑004 (pruning heuristic) | T006, T007 |
| FR‑005 (PLR breakpoint) | T008, T009 |
| FR‑006 (precision & diversity) | T005, T010 |
| FR‑067 (VIF) | T008 |
| Edge‑case handling | T002, T005 |
| SC‑001–SC‑006 (success, precision, pruning effect, VIF, compute budget) | T005, T008, T010, T011 |
| Reviewer‑raised heuristic contradiction | T006 (redundancy variant) & T007 (comparative runs) |

**Execution order**: T001 → T002 → T003 & T004 (parallel) → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015.  

All tasks write only to project‑owned directories (`code/`, `data/`, `figures/`, `specs/…`, `archive/`). No task modifies `state/` or platform‑owned paths.
