# Implementation Plan: MobileForge Logic Distillation

**Branch**: `930-logic-distillation` | **Date**: 2026-10-15 | **Spec**: `specs/930-logic-distillation/spec.md`  
**Input**: Feature specification from `specs/930-logic-distillation/spec.md`

## Summary
Create a CPU‑only pipeline that (1) extracts high‑quality `(UI_state, Corrective_Hint, Action)` triples, (2) trains a T5‑small Encoder‑Decoder model within a 6‑hour wall‑clock limit, (3) evaluates it against TinyLlama on a power‑analysis‑driven sample of AndroidWorld tasks using McNemar’s paired test, (4) conducts a Levenshtein‑based sensitivity sweep, and (5) runs a hint‑specific ablation. All steps produce **project‑owned** artifacts under `outputs/` that can be verified by the platform’s contract tests.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers==4.41.0`, `datasets==2.18.0`, `torch==2.2.2`, `scikit-learn==1.5.0`, `pandas==2.2.2`, `pytest==8.2.2`, `ruff==0.4.2`, `black==24.4.2`  
- **Storage**: Local filesystem (`data/`, `outputs/`)  
- **Testing**: `pytest` (unit, integration, contract)  
- **Target Platform**: GitHub Actions Linux runner (2 CPU cores, ~7 GB RAM)  
- **Constraints**: CPU‑only execution (CUDA abort), training ≤ 6 h, ≤ 100 M parameters, no synthetic data, reproducibility (seeded runs).  

## Complexity Tracking (FR/SC → Phase/Task)
| FR/SC | Phase / Task |
|------|--------------|
| FR‑001 | Phase 2 – `pipeline/extract.py` |
| FR‑002 | Phase 3 – `pipeline/train.py` |
| FR‑003 | Phase 4 – `pipeline/evaluate.py` (sample selection) |
| FR‑004 | Phase 4 – paired inference (same task IDs) |
| FR‑005 | Phase 4 – McNemar’s test implementation |
| FR‑006 | Phase 5 – Sensitivity sweep (`--mode sensitivity`) |
| FR‑007 | Phase 1 – `utils/power_analysis.py` |
| FR‑008 | Phase 3 – CUDA guard |
| SC‑001 | Phase 0 – `code/requirements.txt` (pinned) |
| SC‑002 | Phase 2 – loader raises on missing/corrupt data |
| SC‑003 | Phase 3 – watchdog (`signal.alarm`) |
| SC‑004 | Phase 4 – one‑tailed `p < 0.05` check |
| SC‑005 | Phase 5 – variance reporting only |
| SC‑006 | Phase 1 – documented a‑priori parameters |
| SC‑007 | Phase 6 – hint‑ablation (`--mode ablation`) |

## Implementation Phases

### Phase 0 – Bootstrap
1. **Create `code/requirements.txt`** with exactly 11 pinned lines (no unpinned `numpy`).  
2. **Create `code/.ruff.toml`** and `pyproject.toml` for formatting/linting.  
3. **Run `pip install -r code/requirements.txt`** and capture install logs (CI will store them).  

### Phase 1 – A‑Prior Power Analysis (FR‑007, SC‑006)
- **Task P001** – Execute `utils/power_analysis.py`.  
  - Performs a pilot run of TinyLlama on a small random subset of tasks to estimate the discordant proportion.  
  - Uses a **McNemar‑specific power calculation** based on the binomial distribution of discordant pairs (implemented with `statsmodels.stats.proportion.proportion_effectsize` and `statsmodels.stats.power.NormalIndPower`).  
  - Writes **project‑owned** `outputs/power_analysis.json` (schema `contracts/power_analysis.schema.yaml`).  
  - Logs a human‑readable report `outputs/power_report.md`.  
- **Contingency** – If pilot discordance < 0.05, recompute `N` with a conservative 0.05 estimate and log a warning.

### Phase 2 – Data Extraction & Validation (FR‑001, SC‑002)
- **Task D001** – `pipeline/extract.py` loads the verified ExtractionDataset via `datasets.load_dataset('OSTShushack/ExtractionDataset', ...)`.  
- Verify SHA‑256 against `data/checksums.json`; abort on mismatch.  
- Filter `trajectory_status == "failed_then_success"` and ensure `corrective_hint` contains no coordinate regex `\[\d+,\d+\]`.  
- Append a modest proportion (e.g., a small fraction) of `initial_success` rows for balance.  
- Write **project‑owned** `outputs/train_split.parquet` (the majority of the data) and `outputs/test_split.parquet` (the remaining portion). and a metadata JSON `outputs/extraction_meta.json`.  
- Validate `train_split.parquet` and `test_split.parquet` against `contracts/dataset.schema.yaml`. (No schema validation is performed on `extraction_meta.json`.)

### Phase 3 – CPU‑Tractable Model Training (FR‑002, FR‑008, SC‑003)
1. **CUDA Guard** – Early exit if `torch.cuda.is_available()`.  
2. **Watchdog** – Register `signal.alarm(6*60*60)`; on alarm, log and exit with non‑zero status.  
3. **Training Subset** – Randomly sample at most **20 k** triples from `outputs/train_split.parquet` (fixed seed).  
4. **Training** – Fine‑tune `t5-small` (`transformers`) on the sampled data:  
   - Batch size ≤ 8, gradient accumulation to keep RAM < 7 GB.  
   - Learning rate = 3e‑4, epochs ≤ 3, early‑stopping patience = 1.  
5. **Save Model** – Write checkpoint to `outputs/distilled_t5/` (weights, config).  
6. **Provenance Log** – Write `outputs/training_log.json` containing epoch times, final loss, and hyper‑parameters (no contract validation required).  

### Phase 4 – Evaluation & Statistical Validation (FR‑003‑005, FR‑004, SC‑004)
1. Load `outputs/power_analysis.json` → retrieve required `N`.  
2. Sample **N** disjoint tasks from AndroidWorld (`datasets.load_dataset('google-deepmind/androidworld', split='test')`). Store IDs in `outputs/eval_tasks.json`.  
3. **Deterministic & Randomized Inference** –  
   - Set `torch.manual_seed(RANDOM_SEED)`.  
   - Randomly shuffle the order of model execution per task (distilled first or baseline first) to eliminate systematic bias.  
4. Run both distilled T5 and TinyLlama on each task (identical UI state & hint).  
5. Execute generated action sequences in the Android emulator (`utils/emulator.py`). Binary outcome = Success/Fail.  
6. Build 2×2 contingency table (a,b,c,d) and apply `scipy.stats.mcnemar` (exact binomial when `b + c < 25`).  
7. Compute one‑tailed p‑value (`p/2` if `b > c`). Declare significance if `p < 0.05`.  
8. Write **project‑owned** `outputs/evaluation_results.json` conforming to `contracts/evaluation.schema.yaml`.  

### Phase 5 – Sensitivity Sweep (FR‑006)
- Iterate thresholds `{0,1,2,3}` (Levenshtein distance).  
- For each threshold, recompute success flags for both models (emulator + distance ≤ threshold).  
- Record per‑threshold success rates in `outputs/sensitivity_report.json` (schema `contracts/evaluation.schema.yaml` subset).  
- No binary pass/fail decision; report variance across thresholds.

### Phase 6 – Hint‑Specific Ablation (Constitution VII)
- Replace every `Corrective_Hint` with the literal `"retry"` in `outputs/eval_tasks.json`.  
- Re‑run deterministic, randomized evaluation (same code path as Phase 4, `--mode ablation`).  
- Store results in `outputs/ablation_report.json` (same schema as evaluation).  

### Phase 7 – Verification & CI
1. Run `pytest tests/` – includes unit, integration, and contract tests.  
2. Contract suite validates every file under `outputs/` against the schemas in `contracts/`.  
3. CI fails if any contract violation or if the watchdog terminates training early.  

---

