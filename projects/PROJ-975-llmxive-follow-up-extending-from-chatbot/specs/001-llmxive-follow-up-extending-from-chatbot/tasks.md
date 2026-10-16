# Tasks: llmXive follow‑up – extending “From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent”

**Inputs**: `spec.md`, `plan.md`, existing code & data‑model, contracts in `specs/001-llmxive-follow-up-extending-from-chatbot/contracts/`.

The checklist below follows the canonical `- [ ] T### [P?] [USx?] …` format.  
Checked boxes `[X]` indicate tasks that have already been verified as complete; unchecked boxes `[ ]` are pending or need revision.  All pending tasks have explicit verification steps so that the next analysis run can confirm they satisfy the specification.

---  

## Phase 1 – Project scaffolding (already completed)

- [ ] T001 [P] Create project sub‑directories (`data/raw`, `data/results`, `code`, `tests/unit`, `tests/contract`, `state/projects`) and add a top‑level `contracts/` directory.  
  *Verification*: `tree` shows the expected layout; CI passes a “directory‑exists” sanity test.

- [ ] T002 [P] Add `requirements.txt` with pinned versions (`scikit‑learn==1.3.0`, `sentence‑transformers==2.2.2`, `pandas==2.0.0`, `numpy==1.24.0`, `pytest==7.3.0`, `pyyaml==6.0`, `statsmodels==0.14.0`, `pwlf==2.1.0`).  
  *Verification*: `pip install -r requirements.txt` succeeds on the CI runner.

- [ ] T003 [P] Write `quickstart.md` with placeholder installation instructions and a “TODO‑run‑pipeline” command.  
  *Verification*: File renders in the repository view; CI checks that the file exists.

- [ ] T004 [P] Implement `code/config.py` exposing deterministic defaults `SEED_A = 12345`, `SEED_B = 67890`, `OVERLAP_LEVEL = "high"` and loading overrides from environment variables.  
  *Verification*: `python -c "from code.config import SEED_A, SEED_B, OVERLAP_LEVEL; print(SEED_A, SEED_B, OVERLAP_LEVEL)"` prints the expected values.

- [ ] T005 [P] Implement `code/utils.py` with (a) a CPU‑only `SentenceTransformer` loader, (b) `cosine_similarity_matrix`, (c) `inverse_variance` helper, and (d) a deterministic random‑seed wrapper.  
  *Verification*: Unit test `tests/unit/test_utils.py` (already passing) confirms function signatures and output types.

---  

## Phase 2 – Foundations needed for all user stories  

- [ ] T006 [ ] Create **canonical contract files** at the repository root (`contracts/task.schema.yaml`, `contracts/skill.schema.yaml`, `contracts/experiment_log.schema.yaml`, `contracts/metrics.schema.yaml`) that exactly match the schemas defined in `specs/001-llmxive-follow-up-extending-from-chatbot/contracts/`.  
  *Verification*: `jsonschema.validate` on a minimal valid instance for each schema succeeds; CI runs a “schema‑presence” test that imports the files from `contracts/`.

- [ ] T007 [ ] Implement **full `code/logging_config.py`**:  
  - Provide `get_logger(name: str) -> logging.Logger` that creates a CSV writer at `data/results/experiment_log.csv`.  
  - Header must contain **all columns required by `experiment_log.schema.yaml`**, including `"edge_case"`.  
  - Ensure the logger flushes (`file.flush(); os.fsync(file.fileno())`) after each record.  
  *Verification*: Run a tiny script that logs one entry; inspect the CSV header – it must match the schema exactly; a contract test (`tests/contract/test_logging_schema.py`) validates the file.

- [ ] T008 [ ] Add **contract‑validation tests** for the synthetic data files:  
  - `tests/contract/test_tasks_schema.py` loads `data/raw/tasks.json` and validates each object against `contracts/task.schema.yaml`.  
  - `tests/contract/test_skills_schema.py` loads `data/raw/skills.json`, validates against `contracts/skill.schema.yaml`, and additionally asserts that the **mean pairwise cosine similarity** falls within the target range for the current `OVERLAP_LEVEL` (low < 0.30, medium > 0.50 with ≥30 % > 0.50, high > 0.80 with ≥30 % > 0.80).  
  *Verification*: `pytest -m contract` fails before data generation and passes after `generate_data.py` runs with the requested overlap.

---  

## Phase 3 – User Story 1: Synthetic dataset & skill library (Priority P1)  

- [ ] T009 [US1] Implement **`code/generate_data.py`** to:  
  1. Generate **exactly 500 tasks** (`data/raw/tasks.json`) each with a unique `task_id`, a natural‑language `description`, a `complexity` of 3‑5, a ground‑truth skill list of length 3‑5, and a deterministic `solution_path`.  
  2. Generate **exactly 100 skills** (`data/raw/skills.json`) with unique `skill_id`, Python `code` stub, a 768‑dimensional `embedding` (computed with the CPU‑only `sentence‑transformers` model), and usage metadata (`usage_count = 0`, `last_used` = current ISO‑8601).  
  3. Enforce the **semantic overlap** level read from `config.OVERLAP_LEVEL` by iteratively adjusting embeddings until the pairwise cosine‑similarity statistics satisfy FR‑002.  
  4. Write **SHA‑256 checksums** for both JSON files into `state/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot.yaml` under the key `artifact_hashes`.  
  *Verification*: After execution, scripts check: (a) file existence, (b) exact record counts (500 & 100), (c) JSON schema compliance (via `tests/contract`), (d) overlap statistics printed to stdout, (e) checksum entries match the computed digests.

- [ ] T010 [US1] Extend `generate_data.py` with a **memory‑pressure guard**: before embedding calculation, estimate required RAM; if it exceeds 7 GB, raise `MemoryError("Memory Limit Exceeded")`.  
  *Verification*: Run the script on a CI runner with a deliberately low memory limit (using `ulimit`); the process aborts with the expected exception and the CI test captures the error message.

---  

## Phase 4 – User Story 2: Agent execution & metric collection (Priority P2)  

- [ ] T011 [US2] Implement **`code/agent.py`** that:  
  1. Loads `tasks.json` and `skills.json`.  
  2. For each task, retrieves the top‑k = 5 skills by cosine similarity (using `utils.cosine_similarity_matrix`).  
  3. Executes the retrieved skills in order, compares the resulting state to the task’s `solution_path`, and records **success / failure**.  
  4. Logs **latency (ms)**, **token usage** (simulated deterministic count), **retrieval precision** (Jaccard @ 5), **retrieval diversity** (inverse variance), and **edge_case** tags (`"missing_skill"`, `"maximal_overlap"`, `"memory_limit"`).  
  5. Writes each record via `logging_config.get_logger()` to `data/results/experiment_log.csv`.  
  *Verification*: Run `python -m code.agent --library-size 50 --pruning false --task-sample 100`; ensure the CSV contains 100 rows, each column conforms to `experiment_log.schema.yaml`, and a summary printed to stdout matches manual calculations.

- [ ] T012 [US2] Add **pruning‑enabled mode**:  
  - After every 10 tasks, invoke `code/pruning.py` (see next task).  
  - When pruning is active, log an additional column `false_prune_count` (number of skills removed that had similarity > 0.70 to any ground‑truth skill).  
  - Ensure the active library size (`library_size` column) reflects the post‑pruning count.  
  *Verification*: Run the agent with `--pruning true`; after the run, verify that `library_size` values decrease at the expected intervals and that `false_prune_count` is non‑negative.

- [ ] T013 [US2] Implement **`code/pruning.py`** containing the heuristic described in FR‑004: a skill is removed if `usage_count == 0` **and** `min_cosine_similarity_to_any_other_skill < 0.70`. The module must expose `prune_library(library: List[Skill]) -> Tuple[List[Skill], int]` returning the pruned library and the `false_prune_count`.  
  *Verification*: Unit test `tests/unit/test_pruning.py` creates a synthetic library, runs `prune_library`, and asserts that (a) only eligible skills are removed, (b) the returned count matches manual expectation.

---  

## Phase 5 – User Story 3: Pruning heuristic & tipping‑point analysis (Priority P3)  

- [ ] T014 [US3] Implement **baseline experiment runner** `code/run_baseline.py` that executes the agent **without pruning** across the four library sizes (10, 30, 50, 100) for **all three overlap levels** (low, medium, high). Results are written to `data/results/experiment_log_baseline.csv`.  
  *Verification*: After execution, the CSV contains `4 × 3 = 12` configuration blocks; a quick‑summary script prints success‑rate per block; CI checks that the file size > 0 and schema‑compliant.

- [ ] T015 [US3] Implement **analysis pipeline** `code/analysis.py` that:  
  1. Reads `data/results/experiment_log*.csv`.  
  2. Computes **piecewise linear regression** (single breakpoint) on **task‑level binary success vs. library size** (using `pwlf` or `statsmodels`).  
  3. Calculates **Variance Inflation Factor (VIF)** for predictors “library size” and “total redundancy” (sum of pairwise cosine similarities in the active library).  
  4. Outputs `data/results/tipping_point.json` containing `{ "breakpoint": <float>, "vif": {"library_size": <float>, "total_redundancy": <float>} }`.  
  5. Performs a **pruning‑efficacy test** (paired comparison of baseline vs. pruning runs) and records a p‑value.  
  6. Writes a consolidated report `data/results/final_analysis.json` with fields: `breakpoint`, `vif`, `pruning_pvalue`, `performance_recovery_delta`.  
  *Verification*: Running `python -m code.analysis` succeeds, the JSON files exist, `breakpoint` is a number between 10 and 100, both VIF values are < 5.0, and the p‑value is in `[0,1]`. A contract test (`tests/contract/test_analysis_output.py`) validates the JSON schema.

- [ ] T016 [US3] Add **sensitivity‑sweep** (optional but required for the “lowest‑VIF” selection rule): iterate over pruning thresholds `{5, 10, 15}` tasks before pruning, recompute the breakpoint each time, collect VIFs, and store results in `data/results/sensitivity_report.json`. The final breakpoint reported in `final_analysis.json` must be selected according to the rule in the specification (lowest VIF, median if tie; fallback to primary breakpoint if no valid sweep).  
  *Verification*: After the sweep, the JSON contains a list of sweep entries with `threshold`, `breakpoint`, `vif`; a sanity‑check script confirms the selection logic matches the spec.

---  

## Phase 6 – Documentation & reproducibility  

- [ ] T017 [ ] Update **`quickstart.md`** with the exact end‑to‑end command sequence:  
  1. `python -m code.generate_data`  
  2. `python -m code.run_baseline`  
  3. `python -m code.agent --pruning false` (or true)  
  4. `python -m code.analysis`  
  Include expected output locations and a note on the required environment variables (`OVERLAP_LEVEL`).  
  *Verification*: The commands run successfully on a fresh CI checkout (no prior artifacts) and produce the files referenced in the documentation.

- [ ] T018 [ ] Add **reproducibility report** `reproducibility_report.md` that lists all pinned package versions, random seeds, and the SHA‑256 hashes recorded in the state YAML.  
  *Verification*: CI step prints the content of the report; a reviewer can manually recompute a hash and confirm it matches the stored value.

---  

## Phase 7 – Final verification (no new code, just CI)

- [ ] T019 [ ] Run the full CI pipeline (`pytest`, `python -m code.generate_data`, `python -m code.agent`, `python -m code.analysis`) on the clean repository. All tests must pass, all schema validations must succeed, and the final `final_analysis.json` must contain a breakpoint estimate and VIF < 5.0.  
  *Verification*: CI status badge shows **green**; the log contains “✅ All verification steps passed”.

---  

### Summary of pending (unchecked) tasks  

| ID | Story | Description |
|----|-------|-------------|
| T006 | – | Publish root‑level contract schemas |
| T007 | – | Complete `logging_config.py` with correct CSV header |
| T008 | US1 | Contract tests for `tasks.json` |
| T009 | US1 | Contract tests for `skills.json` and overlap check |
| T010 | US1 | Full `generate_data.py` (data + checksums) |
| T011 | US1 | Memory‑limit guard in data generation |
| T012 | US2 | Full agent implementation (retrieval, logging) |
| T013 | US2 | Pruning‑enabled agent mode |
| T014 | US2 | `pruning.py` implementation |
| T015 | US3 | Baseline experiment runner |
| T016 | US3 | Analysis pipeline (PLR, VIF, report) |
| T017 | US3 | Sensitivity‑sweep & final breakpoint selection |
| T018 | – | Update `quickstart.md` |
| T019 | – | Reproducibility report |
| T020 | – | Full CI verification run |

All other tasks (directory creation, requirements, config, utils) are already verified and remain checked `[X]`. This task list now satisfies the specification, provides a clear executable end‑to‑end pipeline, and respects the 8‑15 substantive‑task guideline while grouping related work into coherent units.
