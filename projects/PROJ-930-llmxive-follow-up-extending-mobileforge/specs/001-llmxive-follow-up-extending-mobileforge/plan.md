# Implementation Plan: MobileForge Logic Distillation

**Branch**: `930-logic-distillation` | **Date**: 2026-10-15 | **Spec**: `specs/930-logic-distillation/spec.md`  
**Input**: Feature specification from `specs/930-logic-distillation/spec.md`

## Summary
Implement a CPU‑tractable logic‑distillation pipeline that extracts `(UI_state, Corrective_Hint, Action)` triples, trains a T5‑small Encoder‑Decoder model, and rigorously evaluates it against a TinyLlama baseline using a priori power analysis and McNemar’s test. All non‑functional constraints (training ≤ 6 h, CPU‑only, reproducibility, sensitivity analysis, ablation) are explicitly enforced.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers==4.41.0`, `datasets==2.18.0`, `torch==2.2.2`, `scikit-learn==1.5.0`, `pandas==2.2.2`, `pytest==8.2.2`, `ruff==0.4.2`, `black==24.4.2`  
- **Storage**: Local filesystem under `data/` and `state/`  
- **Testing**: `pytest` (unit, integration, contract)  
- **Target Platform**: Linux CI runner (GitHub Actions, 2 CPU cores, ~7 GB RAM)  
- **Constraints**: CPU‑only execution (CUDA abort), training ≤ 6 h, ≤ 100 M parameters, no synthetic data, strict reproducibility.

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Random seeds pinned; deterministic loaders; `requirements.txt` ensures identical library versions. |
| II. Verified Accuracy | PASS | All dataset URLs are from the verified list; no invented citations. |
| III. Data Hygiene | PASS | Raw data immutable, checksums stored in `data/checksums.json`; transformations produce new files with documented provenance. |
| IV. Single Source of Truth | PASS | All metrics flow from `utils/metrics.py` to `state/evaluation_results.json`. |
| V. Versioning Discipline | PASS | `state/artifact_hashes.json` records SHA‑256 for every generated artifact. |
| VI. CPU‑Only Inference | PASS | `pipeline/train.py` aborts on CUDA detection; enforced via environment guard. |
| VII. Hint‑Specific Ablation | PASS | Evaluation includes a dedicated “retry” ablation run. |

## Project Structure
```
specs/930-logic-distillation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── extraction_dataset.schema.yaml
│   ├── evaluation.schema.yaml
│   ├── power_analysis.schema.yaml
│   ├── state_artifacts.schema.yaml
│   └── training_input.schema.yaml
│   └── ... (other schemas)
└── tasks.md               # generated later

projects/PROJ-930-llmxive-follow-up-extending-mobileforge/
├── data/
│   ├── raw/
│   ├── processed/
│   └── checksums.json
├── code/
│   ├── __init__.py
│   ├── config.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── power_analysis.py        # T009 – creates state/validated_n.json
│   │   ├── metrics.py               # T006 – SuccessRate, StepEfficiency
│   │   ├── emulator.py              # T005 – launch_emulator, send_action, etc.
│   │   └── emulator_test_helpers.py
│   ├── pipeline/
│   │   ├── extract.py               # FR‑001
│   │   ├── train.py                 # FR‑002, includes timeout enforcement (SC‑003)
│   │   └── evaluate.py              # FR‑003‑005, sensitivity, ablation
│   ├── models/
│   │   └── distilled_t5.py
│   └── main.py
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
│       ├── test_emulator.py        # T005a
│       └── test_metrics.py         # T006 tests
├── state/
│   ├── artifact_hashes.json
│   └── validated_n.json            # output of T009
├── requirements.txt                # T001/T002
├── pyproject.toml                  # T003 – black/ruff config
└── .ruff.toml                      # T003
```

## Complexity Tracking
| FR/SC | Corresponding Phase/Task |
|------|--------------------------|
| FR‑001 | Phase 2 – Data Extraction (`pipeline/extract.py`) |
| FR‑002 | Phase 3 – Model Training (`pipeline/train.py`) |
| FR‑003 | Phase 4 – Evaluation (`pipeline/evaluate.py`) |
| FR‑004 | Phase 4 – Paired evaluation (identical task instances) |
| FR‑005 | Phase 4 – McNemar’s test implementation |
| FR‑006 | Phase 5 – Sensitivity sweep |
| FR‑007 | Phase 1 – Power Analysis (McNemar‑specific) |
| FR‑008 | Phase 3 – CUDA guard |
| SC‑001 | Phase 0 – `requirements.txt` pins |
| SC‑002 | Phase 2 – Loader fails loudly on missing data |
| SC‑003 | **Phase 3 – Hard Timeout Watchdog** (Task T020) aborts after 6 h |
| SC‑004 | Phase 4 – One‑tailed p < 0.05 requirement |
| SC‑005 | Phase 5 – Variance reporting, no hard pass/fail |
| SC‑006 | Phase 1 – Documented a‑priori parameters (McNemar‑specific) |
| SC‑007 | Phase 6 – Hint‑specific ablation (Constitution VII) |

## Implementation Phases

### Phase 0 – Project Bootstrap
1. **Create `requirements.txt`** (T001/T002) with exact pinned versions.  
2. **Create `pyproject.toml` and `.ruff.toml`** (T003) for Black/Ruff configuration.  
3. **Initialize `state/` directory** and empty `state/artifact_hashes.json`.  
4. **Verify dataset URLs** (ExtractionDataset and AndroidWorld) are reachable.  

### Phase 1 – A‑Priori Power Analysis (FR‑007, SC‑006)
1. **Task T009 – Power Analysis Generation**:  
   - Run `utils/power_analysis.py` which:
     - Executes a pilot run of TinyLlama on a representative set of random tasks to estimate discordant proportion.  
     - Uses `statsmodels.stats.power.GofChisquarePower` (McNemar‑specific) with `power=0.8`, `effect_size=0.2`, `alpha=0.05`.  
     - Writes `state/validated_n.json` containing `{ "n_required": N, "parameters": {...} }`.  
   - Logs a human‑readable report `state/power_report.md` for audit (SC‑006).  
2. **Contingency**: If pilot discordance < 0.05, recompute `N` with a conservative estimate and log a warning.

### Phase 2 – Data Extraction & Validation (FR‑001)
1. Download `ExtractionDataset` parquet via `datasets.load_dataset('OSTShushack/ExtractionDataset', ...)`.  
2. Verify SHA‑256 against `data/checksums.json`.  
3. Filter rows where `trajectory_status == "failed_then_success"` and ensure `corrective_hint` lacks coordinate patterns (`\[\d+,\d+\]`).  
4. Add a modest control subset of “initial_success” trajectories to avoid over‑fitting to error‑recovery only.  
5. **Schema Validation**:  
   - Validate raw file against `contracts/dataset.schema.yaml`.  
   - Validate filtered output against `contracts/extraction_dataset.schema.yaml`.  
6. Split into train/test (90/10) and write Parquet files to `data/processed/`.  
7. Record metadata (source URL, filter criteria, record count) in the output file.

### Phase 3 – CPU‑Tractable Model Training (FR‑002, FR‑008, SC‑003)
1. **CUDA Guard**: Early check `torch.cuda.is_available()` → `sys.exit(1)` with clear error message.  
2. **Task T020 – Hard Timeout Watchdog**:  
   - `pipeline/train.py` registers `signal.alarm(6 * 60 * 60)` (6 h).  
   - On alarm, a signal handler logs “Training exceeded 6 h limit – aborting” and exits with non‑zero status, causing CI failure.  
3. **Reduced Training Subset**: To stay within CPU budget, use at most **20 k** filtered triples (fixed‑seed random sample).  
4. Train T5‑small on the processed training split:  
   - Batch size ≤ 8, gradient accumulation to keep RAM < 7 GB.  
   - Learning rate 3e‑4, epochs ≤ 3 (empirically completes < 5 h on the runner).  
   - Early‑stopping based on validation loss with patience = 1 epoch.  
5. Save model weights to `models/distilled_t5/` and record SHA‑256 in `state/artifact_hashes.json`.

### Phase 4 – Evaluation & Statistical Validation (FR‑003‑005, FR‑004)
1. Load `state/validated_n.json` to obtain `N`. Sample exactly `N` tasks from AndroidWorld, ensuring disjointness from training data.  
2. **Deterministic Inference**:  
   - Set `torch.manual_seed(RANDOM_SEED)`.  
   - Greedy decoding (`num_beams=1`, `do_sample=False`, `temperature=0`).  
3. Run both distilled T5 and TinyLlama on the same task instances (identical seeds, UI state, hint).  
4. **Functional Success Definition**:  
   - Execute generated action sequences in the Android emulator (`utils/emulator.py`).  
   - Binary outcome = **Success** if the emulator reports task completion; otherwise **Fail**.  
5. Assemble the 2×2 contingency table (a, b, c, d) and apply `scipy.stats.mcnemar` (exact binomial when `b + c < 25`).  
   - One‑tailed p‑value = `p/2` if `b > c`; significance declared at **p < 0.05** (SC‑004).  
6. Store results in `state/evaluation_results.json` adhering to `contracts/evaluation.schema.yaml`.

### Phase 5 – Sensitivity Sweep (FR‑006)
1. Vary “inconsistency tolerance” thresholds `{0, 1, 2, 3}` (character‑level Levenshtein).  
2. For each threshold, recompute functional success (emulator + Levenshtein ≤ threshold) for both models.  
3. Record variance across thresholds; no binary pass/fail decision (SC‑005).  
4. Optionally re‑run power analysis with observed discordance and log any recommended `N` update.

### Phase 6 – Hint‑Specific Ablation (Constitution VII)
1. Replace every `Corrective_Hint` with the generic prompt `"retry"` for all evaluation tasks.  
2. Re‑run deterministic evaluation; compare `hint_success_rate` vs. `retry_success_rate` in the final report.

### Phase 7 – Post‑Implementation Verification
1. Execute `pytest tests/` – includes unit, integration, and contract tests.  
2. **Contract Validation**:  
   - Validate `data/processed/*.parquet` against `contracts/dataset.schema.yaml`.  
   - Validate extraction output against `contracts/extraction_dataset.schema.yaml`.  
   - Validate `state/artifact_hashes.json` against `contracts/state_artifacts.schema.yaml`.  
   - Validate `state/evaluation_results.json` against `contracts/evaluation.schema.yaml`.  
3. Confirm training log contains a timestamped entry indicating total wall‑clock time ≤ 6 h; otherwise CI fails due to the watchdog.  

---



