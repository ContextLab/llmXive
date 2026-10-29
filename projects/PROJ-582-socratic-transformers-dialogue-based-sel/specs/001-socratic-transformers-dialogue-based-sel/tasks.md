# Tasks: Socratic Transformers (Negative Selection on Belief)

**Inputs**: `spec.md`, `plan.md`, existing artifacts.  
All paths are relative to the project root `projects/PROJ-582-socratic-transformers-dialogue-based-sel/`.

---

## Success Criteria

- **SC-001**: LoRA configuration (`src/train/lora_config.py`) must define `batch_size=2`, `gradient_accumulation_steps=4`, `learning_rate=2e-4`, enable 4‑bit quantisation flags, and enforce a total effective batch size ≤ 8 and an estimated memory footprint ≤ 6 GB. Verification must be an executable command that imports the module and asserts these constraints.

- **SC-002**: The shared training loop (`src/train/train_loop.py`) must enforce a hard timeout (default 3 h) and an OOM fallback. On timeout it must exit with code 1 and log the token “TIMEOUT”. On a `MemoryError` it must write a partial checkpoint file and exit with code 1. Verification must run dedicated unit tests and assert the correct exit codes and side‑effects.

---

## Phase 0 – Project bootstrap (must complete before any research work)

- [~] **T001** [P] Create the canonical project directory tree  
  `code/`, `code/src/`, `code/data/raw/`, `code/data/processed/`, `code/data/results/`, `code/tests/`, `code/state/`.  
  **Verification**:  
  ```bash
  cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code && \
  python - <<'PY'
  import pathlib, sys
  dirs = ["src","data/raw","data/processed","data/results","tests","state"]
  missing = [d for d in dirs if not pathlib.Path(d).is_dir()]
  sys.exit(0 if not missing else 1)
  PY
  ```

- [~] **T002** Create the core Python packaging files  
  * `code/requirements.txt` – must list `transformers`, `peft`, `bitsandbytes`, `datasets`, `scikit-learn`, `pandas`, `pytest`, `ruff`, `black`.  
  * `code/pyproject.toml` – minimal project metadata plus `[tool.black]` and `[tool.ruff]` sections.  
  * `code/ruff.toml` – configure ruff to target `src/` and `tests/`.  
  **Verification**:  
  ```bash
  grep -q "transformers" code/requirements.txt && \
  test -f code/pyproject.toml && test -f code/ruff.toml
  ```

  **Note**: Must run after **T001** (directory creation).

---

## Phase 1 – Real data acquisition & integrity (CPU‑first)

- [ ] **T003** Implement `src/data/download.py` to fetch **GSM8K**, **MATH**, and **MMLU‑STEM** via `datasets.load_dataset(..., streaming=False)`.   <!-- FAILED-IN-EXECUTION: code/src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 -->
  Write the raw files into `data/raw/` (preserving original filenames) and generate a SHA‑256 manifest `state/artifact_hashes.yaml` that records a hash for every file written.  
  **Verification**:  
  ```bash
  cd code && python src/data/download.py && \
  test -f data/raw/gsm8k.parquet && \
  test -f state/artifact_hashes.yaml && \
  grep -q "gsm8k" state/artifact_hashes.yaml
  ```

- [ ] **T004** Implement `src/data/verify_datasets.py` which reads `state/artifact_hashes.yaml` and recomputes SHA‑256 hashes for all files under `data/raw/`.  Exit code 0 only if every checksum matches.  
  **Verification**:  
  ```bash
  cd code && python src/data/verify_datasets.py && echo $?
  ```

---

## Phase 2 – Core utilities (shared across all user stories)

- [ ] **T005** Create the **configuration & loading utilities**:  
  * `src/utils/config.py` – defines `BASE_MODEL_ID`, `CRITIC_MODEL_ID`, `ADVERSARIAL_PROMPT_TEMPLATE`, `SELECTION_THRESHOLD`, `RANDOM_SEED`, etc. (all as non‑empty strings or numbers).  
  * `src/utils/model_loader.py` – `load_base_model()` loads `BASE_MODEL_ID` with 4‑bit quantisation via `bitsandbytes` (CPU fallback).  
  * `src/data/critic_loader.py` – `load_frozen_critic()` loads `CRITIC_MODEL_ID` (4‑bit, `requires_grad=False`).  
  * `src/utils/logging.py` – simple JSON‑line logger `log_event(event_type, details)`.  
  **Verification**: each import must succeed and return a non‑`None` object:  
  ```bash
  cd code && python - <<'PY'
  from src.utils.config import BASE_MODEL_ID, CRITIC_MODEL_ID
  from src.utils.model_loader import load_base_model
  from src.data.critic_loader import load_frozen_critic
  assert BASE_MODEL_ID and CRITIC_MODEL_ID
  assert load_base_model() is not None
  assert load_frozen_critic() is not None
  PY
  ```

  **Note**: Depends on **T001** (directory creation).

---

## Phase 3 – Data‑generation (US 1)

- [ ] **T006** Implement deterministic question mapper `src/data/question_mapper.py` with function  
  `map_index_to_question(dataset_name: str, index: int, seed: int) -> str`.  
  It loads the requested dataset (downloaded by **T003**) and returns the question at the given index; the same `(dataset,index,seed)` must always yield the same string.  
  **Verification**:  
  ```bash
  cd code && python - <<'PY'
  from src.data.question_mapper import map_index_to_question
  q1 = map_index_to_question("gsm8k", 0, seed=42)
  q2 = map_index_to_question("gsm8k", 0, seed=42)
  assert q1 == q2 and q1
  print("Pass")
  PY
  ```

- [ ] **T007** Implement static‑QA extractor `src/data/static_extractor.py` (FR‑001).  
  It reads the raw datasets and writes `data/processed/static_tuples.jsonl` with records containing `question` and `initial_answer` (the ground‑truth answer).  
  **Verification**:  
  ```bash
  cd code && python src/data/static_extractor.py --seed 0 && \
  test -s data/processed/static_tuples.jsonl && \
  head -n1 data/processed/static_tuples.jsonl | grep -q '"question"'
  ```

- [ ] **T008** Implement the **dialogue generator** `src/data/generate_dialogue.py` (FR‑001 & FR‑002).  
  For each deterministic question (via **T006**) it:  
  1. Generates an **initial answer** with the base model (`temperature=0.7`).  
  2. Calls the frozen critic (from **T005**) to produce a **critique** text.  
  3. Generates *K = 5* candidate revised answers, computes TF‑IDF cosine similarity between each candidate and the critique (using `scikit‑learn`).  
  4. **Negative selection**: rejects candidates whose similarity > `SELECTION_THRESHOLD`; keeps the candidate with the *lowest* similarity.  
  5. Runs the **quality gate** (minimum length > 20 tokens, no BLEU ≥ 0.8 with the initial answer, critique confidence ≥ 0.6).  
  6. Writes accepted tuples to `data/processed/dialogue_tuples.jsonl` with fields `question`, `initial_answer`, `critique`, `revised_answer`, `condition="selection"`, `quality_score`.  
  **Verification** (run on a tiny limit):  
  ```bash
  cd code && python src/data/generate_dialogue.py --limit 5 --seed 42 && \
  test -s data/processed/dialogue_tuples.jsonl && \
  head -n1 data/processed/dialogue_tuples.jsonl | grep -q '"critique"'
  ```

- [ ] **T009** Implement the **ablation generator** `src/data/ablation.py` (FR‑007).  
  It reads the dialogue file produced by **T008**, replaces each `critique` with a neutral placeholder whose **token count** matches the original critique (using the base‑model tokenizer from `config.py`).  
  Writes `data/processed/ablation_tuples.jsonl` with `condition="ablation"` and identical `question`, `initial_answer`, `revised_answer`.  
  **Verification**:  
  ```bash
  cd code && python src/data/ablation.py && \
  test -s data/processed/ablation_tuples.jsonl && \
  python - <<'PY'
  import json, pathlib
  orig = next(json.loads(l) for l in pathlib.Path('data/processed/dialogue_tuples.jsonl').open())
  abl  = next(json.loads(l) for l in pathlib.Path('data/processed/ablation_tuples.jsonl').open())
  assert orig['critique'] and abl['critique']
  from src.utils.config import BASE_MODEL_ID
  from transformers import AutoTokenizer
  tok = AutoTokenizer.from_pretrained(BASE_MODEL_ID, use_fast=True)
  assert abs(len(tok(orig['critique'])) - len(tok(abl['critique']))) <= 1
  print("Pass")
  PY
  ```

---

## Phase 4 – Constrained fine‑tuning (US 2)

- [ ] **T010** Create LoRA configuration `src/train/lora_config.py` (FR‑003) **[SC-001]**.  
  Must define `batch_size=2`, `gradient_accumulation_steps=4`, `learning_rate=2e-4`, and enable 4‑bit quantisation flags for `bitsandbytes`.  
  **Verification**:  
  ```bash
  cd code && python - <<'PY'
  from src.train.lora_config import batch_size, gradient_accumulation_steps, learning_rate
  assert batch_size == 2
  assert gradient_accumulation_steps == 4
  assert learning_rate == 2e-4
  # effective batch size check
  assert batch_size * gradient_accumulation_steps <= 8
  # memory ceiling placeholder (ensure runner has ≤7 GB RAM)
  import psutil
  assert psutil.virtual_memory().total / (1024**3) <= 7
  print("LoRA config OK")
  PY
  ```

- [ ] **T011** Implement a **shared training loop** `src/train/train_loop.py` that respects the hard timeout and OOM fallback (FR‑008) **[SC-002]**.  
  * Uses `signal.SIGALRM` for a configurable timeout (default = 3 h).  
  * Monitors RSS via `psutil`; logs a warning if > 6.5 GB.  
  * On OOM (`MemoryError`) writes a partial checkpoint and exits with code 1.  
  **Verification**:  
  ```bash
  cd code && \
  # Timeout guard test
  pytest -q tests/unit/test_timeout.py && \
  echo "Timeout test exit code: $?" && \
  # OOM guard test
  pytest -q tests/unit/test_oom.py && \
  echo "OOM test exit code: $?" && \
  # Ensure checkpoint created on OOM
  test -f data/results/partial_checkpoint_oom.pt
  ```

- [ ] **T012** Implement three **condition‑specific trainers** that each invoke `train_loop.py` with the appropriate dataset:  
  * `src/train/run_selection_train.py` → reads `data/processed/dialogue_tuples.jsonl` and writes `data/results/checkpoint_selection.pt`.  
  * `src/train/run_ablation_train.py` → reads `data/processed/ablation_tuples.jsonl` → `checkpoint_ablation.pt`.  
  * `src/train/run_static_train.py` → reads `data/processed/static_tuples.jsonl` → `checkpoint_static.pt`.  
  All scripts accept `--seed` and forward it to the LoRA config.  
  **Verification** (example for selection):  
  ```bash
  cd code && python src/train/run_selection_train.py --seed 0 && \
  test -s data/results/checkpoint_selection.pt
  ```

---

## Phase 5 – Evaluation & statistical analysis (US 3)

- [ ] **T013** Implement `src/eval/evaluate.py` (FR‑006).  
  For a given seed it loads the three checkpoints, runs inference on the **GSM8K test split** and the **MMLU‑STEM** subset, computes accuracy (and loss), and writes `data/results/seed_<seed>/metrics.json` containing an entry for each condition (`selection`, `ablation`, `static`).  
  **Verification**: after training all three conditions for seed 0, run the script and check the JSON contains three `accuracy` fields.  

- [ ] **T014** Implement `src/eval/run_stats.py` (FR‑006).  
  It aggregates the `metrics.json` files from **five independent seeds**, performs **paired t‑tests** (`selection` vs `ablation`, `selection` vs `static`) with Bonferroni‑corrected α = 0.025, computes Cohen’s d and MDES, and writes a human‑readable `data/results/final_report.md`.  
  **Verification**: after the full pipeline the report must contain the strings “p_value”, “effect_size_cohen_d”, and a concluding sentence stating whether the selection condition is statistically significant.  

---

## Phase 6 – End‑to‑end orchestration & quickstart (research‑stage handoff)

- [ ] **T015** Create orchestration script `src/pipeline/run_all.py`.  
  It loops over seeds `0‑4`, invoking in order:  
  1. `download.py` (skip if data already present).  
  2. `static_extractor.py`, `generate_dialogue.py`, `ablation.py`.  
  3. The three training scripts (`run_*_train.py`).  
  4. `evaluate.py`.  
  After the loop it calls `run_stats.py`.  
  **Important**: Enforces CPU‑only execution; if a GPU is detected the script aborts with an error to preserve reproducibility.  
  **Verification**: running the script must finish with exit code 0 and produce `data/results/final_report.md`.  

- [ ] **T016** Add a top‑level `quickstart.sh` (placed at the project root) that installs the requirements (`pip install -r code/requirements.txt`) and then executes `src/pipeline/run_all.py`.  
  **Verification**:  
  ```bash
  bash quickstart.sh && test -f data/results/final_report.md
  ```

- [ ] **T021** Create `quickstart.md` documenting the quickstart steps, referencing `quickstart.sh` and the expected outputs.  
  **Verification**: file exists and contains the phrase “quickstart.sh”.  

---

## Phase 7 – Test suite (optional but recommended)

- [ ] **T017** Write schema‑validation tests `tests/contract/test_schemas.py` that load each JSONL file (`static_tuples.jsonl`, `dialogue_tuples.jsonl`, `ablation_tuples.jsonl`) and validate against the corresponding JSON‑Schema files in `specs/001-socratic-transformers-dialogue-based-sel/contracts/`.  
  **Verification**: before implementing the generators the test must fail; after T008/T009/T007 it must pass (`pytest -q tests/contract`).  

- [ ] **T018** Write unit tests for the timeout and OOM guards (`tests/unit/test_timeout.py`, `tests/unit/test_oom.py`).  
  Each test triggers the respective condition and asserts that the training script exits with the expected non‑zero code and writes a checkpoint or log entry.  
  **Verification**: `pytest -q tests/unit` must exit with code 0.  

- [ ] **T019** Add contract‑coverage tests `tests/contract/test_contract_coverage.py` that ensure every contract file (`*.schema.yaml`) is referenced by at least one task (by inspecting task descriptions).  
  **Verification**: test passes when all contracts are mentioned in tasks.md.  

- [ ] **T020** Add a CI linting test `tests/lint/test_lint.py` that runs `ruff` and `black --check` on the `src/` and `tests/` directories.  
  **Verification**: `pytest -q tests/lint` must exit with code 0.  

---

### Dependency graph (high‑level)

1. **Phase 0** → enables all later phases.  
2. **Phase 1** (T003, T004) must finish before any utility that accesses raw data.  
3. **Phase 2** (T005) is independent of data but required by T006, T008, T009, T011.  
4. **Phase 3** (T006‑T009) produces the three processed datasets needed by Phase 4.  
5. **Phase 4** (T010‑T012) consumes the processed datasets and produces checkpoints.  
6. **Phase 5** (T013‑T014) consumes checkpoints and produces the final statistical report.  
7. **Phase 6** (T015‑T016) orchestrates the full end‑to‑end run.  
8. **Phase 7** (T017‑T020) provides a regression test suite that validates the whole pipeline.

All tasks are unchecked (`[ ]`) because they have not yet been implemented; checking will occur automatically once the corresponding artifact is produced and passes its verification command.  