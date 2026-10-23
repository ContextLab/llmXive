# Tasks: Dream-State Learning – Implementing REM‑like Consolidation in Language Models  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, all contract schemas in `specs/001-dream-state-learning-implementing-rem-li/contracts/`  

The checklist below follows the canonical `- [ ] T### [P?] [USx?] description …` format.  
Each task lists the primary artifact(s) it creates or modifies and the concrete verification step(s) that a reviewer will run.

---

## Phase 1 – Setup and first end‑to‑end analysis  

| Goal | Run a thin, reproducible wake/dream training‑evaluation cycle on real GLUE data to prove that the pipeline works on the CPU‑only GitHub‑Actions tier. |
|------|----------------------------------------------------------------------------------------------------------------------------------------------------|

- [ ] T001 [US1] **Create project layout, pin exact dependencies, and add a CPU‑only config with a hard RSS cap (6.3 GB).**  
  - Files: `code/requirements.txt`, `code/config.py`  
  - Verification: `pip install -r code/requirements.txt` succeeds; `python -c "import code.config; assert code.config.MAX_MEMORY_MB == 6300"` runs without error.

- [ ] T002 [US1] **Implement the core Wake/Dream training loop** (20‑step warm‑up, 4 wake : 1 dream ratio, random BERT‑style masking, DAE reconstruction loss, entropy‑retry (≤3) and perplexity‑skip (threshold 50), dummy‑wake insertion for token‑parity).  
  - Files: `code/models/trainer.py`, `code/data/augment.py`  
  - Verification: Unit tests in `tests/unit/test_trainer.py` assert (a) warm‑up length, (b) low‑entropy batches trigger retries, (c) high‑perplexity batches cause dream‑step skip and dummy wake, (d) total real‑token count matches the baseline for a fixed seed.

- [ ] T003 [US1] **Add a CLI entry point (`code/train.py`) that wires the config, trainer, and memory monitor; on OOM abort it saves a checkpoint and logs peak RSS.**   <!-- FAILED-IN-EXECUTION: code/train.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/train.py exit=1 -->
  - Files: `code/train.py`, `code/utils/memory_monitor.py`  
  - Verification: Running `python code/train.py --seed 0 --total_steps 20 --mode debug` finishes within 5 min, writes `checkpoints/debug_seed0.pt` and a structured log `logs/debug_seed0.json` containing a `"peak_rss_mb"` field ≤ 6300.

- [ ] T004 [US2] **Implement few‑shot QNLI evaluation and result logging** (accuracy, loss, peak memory, duration, reconstruction‑difficulty average).  
  - Files: `code/eval.py`, `code/eval/metrics.py`  
  - Verification: `python code/eval.py --checkpoint checkpoints/debug_seed0.pt` produces `data/results/evaluation_result_debug_seed0.json` that validates against `contracts/evaluation_result.schema.yaml`.

- [ ] T005 [US2] **Document a runnable quick‑start command** that ties the above pieces together and demonstrates a full train‑eval cycle on a real GLUE subset.  
  - Files: `quickstart.md` (updated)  
  - Verification: A fresh environment (`python -m venv v && source v/bin/activate && pip install -r code/requirements.txt && bash -c "$(grep '^```' -A2 quickstart.md | tail -n1)"`) runs without error and produces `data/results/evaluation_result_debug_seed0.json`.

---

## Phase 2 – Complete the study and validate evidence  

| Goal | Run the full experimental protocol (wake/dream vs. continuous baseline) with statistical rigor, sensitivity analysis, and resource auditing. |
|------|---------------------------------------------------------------------------------------------------------------------------------------------------|

- [ ] T006 [US2] **Implement the continuous‑training baseline** that mirrors the experimental run’s total real‑token exposure (including dummy wake steps when the experimental run skips a dream step).  
  - Files: `code/baseline.py` (or extended `trainer.py` with `--mode baseline`)  
  - Verification: Integration test `tests/integration/test_token_parity.py` confirms identical `real_token_count` for a given seed between baseline and experimental runs.

- [ ] T007 [US1] **Orchestrate a multi‑seed experiment** (seeds 0, 1, 2, 3, 4) that runs both regimes, saves per‑seed `experiment_result.json` files, and records all runtime metrics.   <!-- FAILED-IN-EXECUTION: code/main.py exit=1 -->
  - Files: `code/main.py` (or `scripts/run_experiment.sh`)  
  - Verification: After execution, `data/results/experiment_result_seed0_wake_dream.json`, `…_baseline.json`, … up to seed 4 exist, each conforming to `contracts/experiment_result_schema.schema.yaml`.

- [ ] T008 [US2] **Compute statistical summary**: paired two‑tailed t‑test, Cohen’s d, power estimate, and flag “insufficient power” if any seed’s few‑shot set < 5 samples. Output `data/results/statistical_report.json`.  
  - Files: `code/stats.py`  
  - Verification: `pytest tests/unit/test_stats.py` checks that the JSON validates against `contracts/statistical_report_schema.yaml` and that `significant` matches the p‑value vs. α = 0.05; also ensures the test uses ≥5 seeds.

- [ ] T009 [US1] **Run the temperature sweep** (0.5, 1.0, 1.5, 2.0) as a mandatory secondary ablation for each seed. Store per‑temperature accuracy and variance in `data/results/variance_report.json`.  
  - Files: `code/sweep.py` (invoked from `code/main.py --sweep`)  
  - Verification: The variance report contains keys `"temperature"` (list) and `"accuracy_mean"` (list) for all four temperatures and passes a schema check (`tests/unit/test_sweep.py`).

- [ ] T010 [US3] **Resource audit**: enforce peak RSS ≤ 6.3 GB and total wall‑clock ≤ 5 h for every full run; generate `data/results/resource_audit.json`.  
  - Files: `code/utils/memory_monitor.py`, `scripts/verify_feasibility.sh`  
  - Verification: Running `bash scripts/verify_feasibility.sh` after an experiment exits with status 0 and the JSON contains `"peak_memory_gb"` ≤ 6.3 and `"wall_clock_hours"` ≤ 5.0.

- [ ] T011 [US3] **Validate all result artifacts against their JSON schemas** (contract tests).  
  - Files: `tests/contract/*` (one test per schema)  
  - Verification: `pytest -k contract` passes with ≥ 90 % coverage of the `contracts/` directory.

---

## Phase 3 – Reproducible results and handoff to the paper pipeline  

| Goal | Produce a single source‑of‑truth artifact, confirm reproducibility, and prepare documentation for the downstream paper stage. |
|------|-----------------------------------------------------------------------------------------------------------------------------------|

- [ ] T012 [US2] **Generate the architecture document** that formalizes the logical‑depth view of “consolidated” states (as requested by reviewers) and updates `docs/architecture.md`.  
  - Files: `docs/architecture.md`  
  - Verification: `pytest -k architecture` checks that `docs/architecture.md` exists and contains a markdown image link (`![](figures/architecture_diagram.svg)`) referencing a diagram generated from `data/results/experiment_summary.json`.

- [ ] T013 [US3] **Run a full reproducibility check** on a clean runner (no cached checkpoints) using only the commands listed in `quickstart.md`; produce `data/results/reproducibility_report.json` summarizing success/failure of each step.  
  - Files: `scripts/reproducibility_check.sh`  
  - Verification: The script exits with status 0 and the JSON reports `"all_steps_passed": true`.

- [ ] T014 [US3] **Perform a PII scan of the entire `data/` tree** and confirm zero findings; store the scan log `data/results/pii_scan.log`.  
  - Files: `scripts/pii_scan.sh` (uses `grep -R` for common PII patterns)  
  - Verification: The log contains the line `PII_SCAN: 0 violations detected`.

- [ ] T015 [US2] **Finalize the paper‑stage handoff**: add a `docs/paper_handoff.md` that lists the canonical artifact (`data/results/experiment_summary.json`), the statistical report, and the architecture diagram, and points the paper pipeline to these locations.  
  - Files: `docs/paper_handoff.md`  
  - Verification: `pytest -k handoff` checks that `docs/paper_handoff.md` contains `sha256sum:` lines for each referenced artifact and that each referenced path exists on disk.

---

### Dependency mapping (spec → task)

| Spec requirement | Satisfied by task(s) |
|------------------|----------------------|
| FR‑001 (wake/dream loop) | T002 |
| FR‑002 (pseudo‑sample generation, masking) | T002 |
| FR‑003 (baseline token parity) | T006 |
| FR‑004 (few‑shot evaluation) | T004 |
| FR‑005 (memory cap) | T003, T010 |
| FR‑006 (temperature sweep) | T009 |
| FR‑007 (warm‑up) | T002 |
| SC‑001 (relative accuracy) | T007 |
| SC‑002 (paired t‑test) | T008 |
| SC‑003 / SC‑004 (resource limits) | T010 |
| SC‑005 (temperature variance) | T009 |
| Contract validation | T011 |
| Architecture/definition of consolidation | T012 |
| Reproducibility & handoff | T013‑T015 |

---  

*All unchecked tasks are pending implementation; once a task’s verification passes the checkbox will be ticked by the CI pipeline.* 