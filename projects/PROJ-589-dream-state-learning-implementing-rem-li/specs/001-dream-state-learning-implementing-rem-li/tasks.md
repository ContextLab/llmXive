# Tasks: Dream-State Learning: Implementing REM-like Consolidation in Language Models  

**Input**: `spec.md`, `plan.md`, `data-model.md`, contract schemas in `specs/001-dream-state-learning-implementing-rem-li/contracts/`  

---

## Phase 1 – Project Setup (already completed)

- [ ] T001 Create project skeleton (`code/`, `tests/`, `data/`, `data/raw/`, `data/checkpoints/`, `data/results/`, `data/logs/`, `tests/unit/`, `tests/integration/`, `tests/contract/`).  
- [ ] T001b Add `__init__.py` to all Python package directories (except `data/raw/`).  
- [ ] T002a Add `code/requirements.txt` with base dependencies (`torch`, `transformers`, `datasets`, `scikit-learn`, `accelerate`, `pytest`, `scipy`).  
- [ ] T002b Pin exact versions in `requirements.txt` (e.g., `torch==2.2.0`).  
- [ ] T003 Configure linting (`ruff`) and formatting (`black`).  

---

## Phase 2 – Core Infrastructure (already completed)

- [ ] T004 Add `code/config.py` – hyper‑parameters, path helpers, **CPU‑only device enforcement**, seed handling, **max_memory_mb default = 6400 (6.4 GB)**, **max_wall_clock_hours default = 5**.  
- [ ] T005 Add `code/utils/memory_monitor.py` – reads `/proc/self/status`, aborts if RSS > `max_memory_mb`, writes checkpoint on abort (FR‑005).  
- [ ] T006 Add `code/data/loader.py` – streams GLUE/SuperGLUE subsets via `datasets.load_dataset(..., streaming=True)`, verifies SHA‑256 checksums, raises on mismatch.  
- [ ] T007 Add `code/models/__init__.py` with DistilBERT‑base‑uncased loader (CPU‑optimized).  
- [ ] T008 Add `code/utils/logger.py` – structured JSON logging to `data/logs/`.  
- [ ] T009 Add schema‑validation tests in `tests/contract/` for **all** contract schemas:
  - `training_config.schema.yaml`
  - `evaluation_result.schema.yaml`
  - `dataset.schema.yaml`
  - `dataset_schema.schema.yaml`
  - `dream_event.schema.yaml`
  - `dream_sample_schema.schema.yaml`
  - `experiment_result_schema.schema.yaml`
  - `statistical_report_schema.schema.yaml`
  - `training_result.schema.yaml`
  - `artifact_hashes.schema.yaml`
- [ ] T017a Add `code/utils/exceptions.py` with `LowEntropyWarning` exception (used by dream‑phase logic).  
- [ ] T057 Update `spec.md` FR‑002 to explicitly require a Denoising Auto‑Encoder (DAE) reconstruction step during the dream phase.  

---

## Phase 3 – Core Wake/Dream Training Cycle (P1)

| ID | Requirement | Path | Description |
|----|-------------|------|-------------|
| - [X] T010 | US1 – warm‑up logic | `tests/unit/test_trainer.py` | Unit test that the first `warmup_steps` steps contain **no** dream phase. |
| - [X] T011 | US1 – entropy‑retry | `tests/unit/test_trainer.py` | Unit test that low‑entropy batches trigger up‑to‑3 retries and raise `LowEntropyWarning` if exhausted. |
| - [X] T012 | US1 – integration | `tests/integration/test_training_loop.py` | Integration test of a 20‑step wake/dream schedule on a tiny synthetic dataset. |
| - [X] T013a | US1 – masking constant | `code/config.py` | Define `MASK_RATE = 0.15`. |
| - [X] T013b | US1 – masking logic | `code/data/augment.py` | Implement BERT‑style random token masking using `MASK_RATE`. |
| - [X] T014 | US1 – wake phase | `code/models/trainer.py` | Implement standard cross‑entropy fine‑tuning on real data (batching per `config.batch_size`). |
| - [X] T015 | US1 – dream phase | `code/models/trainer.py` | Implement DAE‑style reconstruction on masked pseudo‑samples; sample with `config.dream_temperature`. |
| - [X] T016 | US1 – warm‑up protocol | `code/models/trainer.py` | **Enforce exactly 20 wake‑only steps** before any dream step (uses constant `WARMUP_STEPS = 20`). |
| - [X] T017b | US1 – entropy check | `code/models/trainer.py` | Compute per‑token entropy (bits), retry up to 3 times, discard batch on failure, log via `logger`. |
| - [X] T018 | US1 – memory abort | `code/models/trainer.py` | Hook `memory_monitor` to abort on OOM, save checkpoint. |
| - [X] T019 | US1 – phase logging | `code/models/trainer.py` | Structured JSON logs for each phase transition, entropy, warm‑up status. |
| - [ ] T059 | **US1 – training entry‑point** | `code/train.py` | Provide a CLI that loads `config`, instantiates `Trainer`, runs the full wake/dream schedule (including warm‑up), and writes final checkpoint to `data/checkpoints/`. **Verification**: unit test checks script runs without error and checkpoint file exists. |
| - [X] T060 | US2 – evaluation entry‑point | `code/eval.py` | CLI that loads a checkpoint, runs few‑shot evaluation on the held‑out GLUE task, and writes an `evaluation_result` JSON to `data/results/`. **Verification**: unit test validates JSON schema compliance. |

---

## Phase 4 – Comparative Baseline & Statistical Analysis (P2)

- [ ] T022 Implement `code/eval/metrics.py` – compute few‑shot accuracy on held‑out GLUE subset. **Verification**: unit test imports module and asserts `compute_accuracy` returns a float in [0,1].  
- [ ] T023 Add baseline mode to `code/models/trainer.py` – continuous supervised fine‑tuning with identical **real token** exposure as the experimental run. **Verification**: unit test confirms token count equality between baseline and wake‑dream runs for a given seed.  
- [ ] T024a Create `code/main.py` – orchestrates parallel runs: experimental (wake/dream) and baseline, each with the same random seed list. **Verification**: integration test asserts both runs are launched and two `aggregated_{seed}.json` files are produced.  
- [ ] T024b Add result aggregation in `code/main.py` – collects per‑run JSONs into `data/results/aggregated_{seed}.json`. **Verification**: test validates each aggregated file conforms to `training_result.schema.yaml`.  
- [ ] T025a Prepare paired accuracy lists across seeds (experimental vs. baseline). **Verification**: unit test checks lists have matching length and aligned seed entries.  
- [ ] T025b Compute paired t‑test (`scipy.stats.ttest_rel`) with α = 0.05, calculate Cohen’s d, and write `statistical_report.json` to `data/results/`. **Verification**: test validates JSON against `statistical_report_schema.schema.yaml` and that it contains `p_value`.  
- [ ] T025c Format statistical output (p‑value, effect size, significance flag) for the final report. **Verification**: unit test confirms formatted file matches schema and includes required fields.  
- [ ] T026 Save comparative report (`data/results/comparison_report.json`). **Verification**: test asserts file exists and validates against `experiment_result_schema.schema.yaml`.  
- [ ] T079 Compute concrete power estimate for the paired t‑test using `statsmodels.stats.power.TTestPower`. **Verification**: test checks that `power_estimate` field is present in `statistical_report.json` and is a float between 0 and 1.  

---

## Phase 5 – Resource‑Constraint Verification (P3)

- [ ] T029 Unit test for `memory_monitor` abort logic (`tests/unit/test_memory_monitor.py`).  
- [ ] T031 Add wall‑clock timer in `code/main.py` – abort if `elapsed > config.max_wall_clock_hours` (default 5 h). **Verification**: unit test with mocked timer triggers abort and logs entry.  
- [ ] T032 Integrate `memory_monitor` into the main training loop (already referenced in T018).  
- [ ] [ ] T030 Integration test ensuring full pipeline respects **a 5‑hour wall‑clock limit** – redesigned to mock timing and verify abort logic without real waiting. **Verification**: test uses time‑mock to simulate over‑limit condition and checks for proper abort status.  
- [ ] T033 Create `code/scripts/verify_feasibility.sh` – dry‑run that prints expected memory/time usage and exits non‑zero if limits are exceeded. **Verification**: test runs script with artificially low limits and expects non‑zero exit code.  

---

## Phase 6 – Temperature Sweep Sensitivity Analysis (FR‑006, SC‑005)

- [ ] T036a Orchestrate temperature sweep in `code/main.py`: run full pipeline for each `temperature ∈ {0.5, 1.0, 1.5, 2.0}` with 5 seeds per temperature. Output files `data/results/sweep_{temp}_{seed}.json`. **Verification**: test checks that for every temperature and seed the corresponding JSON file exists.  
- [ ] T036b Ensure model, optimizer, and RNG are re‑initialized for every sweep run. **Verification**: unit test asserts RNG state differs between successive runs.  
- [ ] T036c Compute variance of final accuracies across temperatures using `numpy.var`; write `data/results/variance_report.json`. **Verification**: test validates JSON contains a numeric `variance` field.  
- [ ] T037 Add a summary JSON (`data/results/temperature_analysis.json`) containing per‑temperature mean, std, and variance. **Verification**: test confirms file matches expected schema (mean, std, variance).  

---

## Phase 7 – Finalization & Handoff (research → paper)

- [ ] T051 Update documentation (`docs/`, `quickstart.md`) with final usage instructions.  
- [ ] T052 Code cleanup & refactoring (PEP‑8 compliance, removal of dead code).  
- [ ] T053 Performance optimizations – ensure data loading uses streaming batches, confirm CPU‑only throughput stays within the 2‑core limit.  
- [ ] T054 Add any missing unit tests for newly added modules. **Verification**: test suite must pass with ≥90 % coverage for new modules.  
- [ ] T055 Security hardening – input validation, PII scan hooks already in place.  
- [ ] T056 Run quick‑start validation script to confirm end‑to‑end execution from `code/train.py` through `code/eval.py` produces the expected JSON artifacts. **Verification**: script must exit code 0 and generate checkpoint, evaluation result, statistical report, and comparison report files.  

---

## Phase 2 – Contract Validation Expansion (new)

- [ ] T080 Add schema‑validation test for `dataset.schema.yaml` in `tests/contract/test_dataset_schema.py`. **Verification**: test loads the schema and validates a minimal conforming instance.  
- [ ] T081 Add schema‑validation test for `dataset_schema.schema.yaml` in `tests/contract/test_dataset_schema_schema.py`. **Verification**: test loads the schema and validates a minimal conforming instance.  
- [ ] T082 Add schema‑validation test for `dream_event.schema.yaml` in `tests/contract/test_dream_event_schema.py`. **Verification**: test loads the schema and validates a minimal conforming instance.  
- [ ] T083 Add schema‑validation test for `dream_sample_schema.schema.yaml` in `tests/contract/test_dream_sample_schema.py`. **Verification**: test loads the schema and validates a minimal conforming instance.  
- [ ] T084 Add schema‑validation test for `experiment_result_schema.schema.yaml` in `tests/contract/test_experiment_result_schema.py`. **Verification**: test loads the schema and validates a minimal conforming instance.  
- [ ] T085 Add schema‑validation test for `statistical_report_schema.schema.yaml` in `tests/contract/test_statistical_report_schema.py`. **Verification**: test loads the schema and validates a minimal conforming instance.  
- [ ] T086 Add schema‑validation test for `training_result.schema.yaml` in `tests/contract/test_training_result_schema.py`. **Verification**: test loads the schema and validates a minimal conforming instance.  
- [ ] T087 Add schema‑validation test for `artifact_hashes.schema.yaml` in `tests/contract/test_artifact_hashes_schema.py`. **Verification**: test loads the schema and validates a minimal conforming instance.  

---  

*End of `tasks.md`.*  