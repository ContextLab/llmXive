# Implementation Plan: MobileForge Logic Distillation

**Branch**: `930-logic-distillation` | **Date**: 2026-10-17 | **Spec**: `specs/930-logic-distillation/spec.md`  
**Input**: Feature specification from `specs/930-logic-distillation/spec.md`

## Summary
Build a fully reproducible, CPU‑only pipeline that (1) downloads an open MobileForge logs dataset, (2) validates and filters `(UI_state, Corrective_Hint, Action)` triples, (3) performs an a‑priori McNemar‑specific power analysis, (4) fine‑tunes a T5‑small encoder‑decoder model within a 6 h wall‑clock limit, (5) evaluates the distilled model against a TinyLlama baseline on a power‑analysis‑driven sample of AndroidWorld tasks using a deterministic paired McNemar’s test, (6) conducts a Levenshtein‑based sensitivity sweep embedded in the final evaluation results, and (7) runs a hint‑specific ablation. All artifacts are stored under `outputs/` and validated against JSON‑Schema contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers==4.41.0`, `datasets==2.18.0`, `torch==2.2.2`, `scikit-learn==1.5.0`, `pandas==2.2.2`, `numpy==1.26.4`, `pytest==8.2.2`, `ruff==0.4.2`, `black==24.4.2`  
- **Storage**: Local filesystem (`data/`, `outputs/`)  
- **Testing**: `pytest` (unit, integration, contract)  
- **Target Platform**: GitHub Actions Linux runner (multiple CPU cores, ~7 GB RAM)  
- **Constraints**: CPU‑only execution (any CUDA detection aborts), training ≤ 6 h, ≤ 100 M parameters, deterministic seeds, no synthetic data, full reproducibility.  

## Constitution Check
| Principle | Reference | Compliance |
|-----------|-----------|------------|
| I. Reproducibility | § I of constitution | All scripts are deterministic, seeds pinned, and CI‑run from scratch. |
| II. Verified Accuracy | § II | Only the verified MobileForge logs URL is used; no invented citations. |
| III. Data Hygiene | § III | Checksums, immutable raw files, derived outputs under `outputs/`. |
| IV. Single Source of Truth | § IV | **SSoT Artifact**: `outputs/evaluation_results.json` is the authoritative source for all figures and tables. |
| V. Versioning Discipline | § V | All artifacts are content‑hashed; `state/projects/...yaml` will be updated automatically. |
| VI. CPU‑Only Inference | § VI | CUDA guard in training/evaluation; watchdog enforces CPU. |
| VII. Hint‑Specific Ablation | § VII | Dedicated ablation mode replaces hints with `"retry"` and re‑evaluates. |

## Project Structure

### Repository Layout
```text
specs/930-logic-distillation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── evaluation.schema.yaml
    └── power_analysis.schema.yaml

code/
├── __init__.py
├── requirements.txt
├── .ruff.toml
├── pyproject.toml
├── utils/
│   ├── power_analysis.py
│   ├── emulator.py
│   └── validate_extraction_dataset.py
├── pipeline/
│   ├── download.py          # downloads verified MobileForge logs dataset
│   ├── extract.py           # filtering & split creation
│   ├── train.py             # T5‑small fine‑tuning
│   └── evaluate.py          # paired evaluation, sensitivity, ablation
├── models/                  # placeholder for saved checkpoints
│   └── distilled_t5/
└── tests/
    ├── unit/
    │   ├── test_download.py
    │   ├── test_extract.py
    │   └── test_train.py
    └── integration/
        └── test_evaluate.py

data/
├── raw/
│   └── mobileforge_logs.parquet   # downloaded by pipeline/download.py
├── checksums.json                  # SHA‑256 for raw files
└── processed/                      # generated splits (train/test)

outputs/
├── power_analysis.json
├── extraction_meta.json
├── train_split.parquet
├── test_split.parquet
├── training_log.json
├── distilled_t5/ (model checkpoint)
├── eval_tasks.json
├── evaluation_results.json   # **SSoT**: contains metrics, statistical_test, power_analysis, sensitivity_report, ablation_report
└── (no separate sensitivity_report.json)
```

All directories above are created explicitly by the bootstrap script (`code/bootstrap.py`), which now also creates `code/models/`, `code/data/raw`, `code/data/processed`, `code/data/evaluation`, `code/tests/unit`, `code/tests/integration`, `data/raw`, and `data/processed`.

## Complexity Tracking (FR/SC → Phase/Task)

| FR / SC | Phase / Task |
|--------|--------------|
| FR‑001 | Phase 2 – `pipeline/extract.py` |
| FR‑002 | Phase 3 – `pipeline/train.py` |
| FR‑003 | Phase 4 – `pipeline/evaluate.py` (sample selection) |
| FR‑004 | Phase 4 – paired inference (same task IDs) |
| FR‑005 | Phase 4 – McNemar’s test implementation |
| FR‑006 | Phase 5 – Sensitivity sweep (embedded) |
| FR‑007 | Phase 1 – `utils/power_analysis.py` (McNemar‑specific) |
| FR‑008 | Phase 3 – CUDA guard |
| SC‑001 | Phase 0 – `code/requirements.txt` (pinned) |
| SC‑002 | Phase 2 – loader aborts on missing/corrupt data |
| SC‑003 | Phase 3 – watchdog (`signal.alarm`) |
| SC‑004 | Phase 4 – one‑tailed `p < 0.05` check |
| SC‑005 | Phase 5 – variance reporting only |
| SC‑006 | Phase 1 – documented a‑priori parameters |
| SC‑007 | Phase 6 – hint‑ablation (`--mode ablation`) |

## Implementation Phases

### Phase 0 – Bootstrap & Directory Creation
1. `code/bootstrap.py` creates the full directory tree listed above, **including** `code/models/`, `code/data/raw`, `code/data/processed`, `code/data/evaluation`, `code/tests/unit`, `code/tests/integration`, `data/raw`, and `data/processed`.  
2. Generates an empty `data/checksums.json` placeholder (will be filled after download).  
3. Commits a deterministic `RANDOM_SEED=42` into `code/__init__.py`.

### Phase 1 – A‑Prior Power Analysis (FR‑007, SC‑006)
- **Task P001** – `utils/power_analysis.py`  
  - Runs a tiny pilot of TinyLlama on a 200‑example subset to estimate the **expected discordant proportion** ( (b + c)/N ) and the **odds ratio** between models.  
  - Uses `statsmodels.stats.power.McNemarPower` (or equivalent validated implementation) with parameters: target power = 0.8, α = 0.05, expected discordant proportion, and odds ratio.  
  - Writes `outputs/power_analysis.json` conforming to `contracts/power_analysis.schema.yaml`.  
  - Logs a human‑readable `outputs/power_report.md`.  
  - If the pilot discordance is < 0.05, recomputes **N** with a conservative discordance of 0.05 and logs a warning.

### Phase 2 – Data Download & Validation (FR‑001, SC‑002)
1. **Download Script** – `pipeline/download.py`  
   - Calls `datasets.load_dataset('mobileforge/mobileforge-logs', split='train')` (verified HuggingFace URL).  
   - Saves the parquet to `data/raw/mobileforge_logs.parquet`.  
   - Computes SHA‑256, updates `data/checksums.json`.  
2. **Validation Script** – `utils/validate_extraction_dataset.py`  
   - Loads the parquet, validates schema against `contracts/dataset.schema.yaml` using `jsonschema`.  
   - Exits with status 0 on success; any mismatch aborts CI with a clear error.  
3. **Extraction & Split** – `pipeline/extract.py`  
   - Filters `trajectory_status == "failed_then_success"` and ensures `corrective_hint` contains no coordinate regex `\[\d+,\d+\]`.  
   - Balances with a small (`[deferred]`) sample of `initial_success` rows to avoid extreme class imbalance.  
   - Writes `outputs/train_split.parquet` and `outputs/test_split.parquet` (both validated against `contracts/dataset.schema.yaml`).  
   - Generates `outputs/extraction_meta.json` (source URL, checksum, record counts).

### Phase 3 – CPU‑Tractable Model Training (FR‑002, FR‑008, SC‑003)
1. **CUDA Guard** – top‑level check in `pipeline/train.py`; aborts if `torch.cuda.is_available()`.  
2. **Watchdog** – `signal.alarm(6*60*60)`; on timeout logs and exits non‑zero.  
3. **Training Subset** – Randomly sample **≤ 20 k** triples from `outputs/train_split.parquet` (fixed seed).  
4. **Fine‑Tuning** – Use `transformers.Trainer` with:
   - Model: `t5-small` (≈ 60 M params).  
   - Batch size = 8, gradient accumulation = 4 (≈ 2 GB RAM).  
   - Learning rate = 3e‑4, max epochs = 3, early‑stopping patience = 1.  
   - Deterministic decoding (`torch.manual_seed`).  
5. **Checkpoint** – Save to `outputs/distilled_t5/` (weights + config).  
6. **Provenance Log** – `outputs/training_log.json` (epoch times, final loss, hyper‑params).

### Phase 4 – Paired Evaluation & McNemar Test (FR‑003‑005, FR‑004, SC‑004)
1. Load `outputs/power_analysis.json` → retrieve **N**.  
2. Sample **N** disjoint tasks from AndroidWorld (`datasets.load_dataset('google-deepmind/androidworld', split='test')`). Store IDs in `outputs/eval_tasks.json`.  
3. **Deterministic Inference** – For each task, run **three** independent emulator executions per model with a fixed emulator seed (`EMULATOR_SEED=12345`).  
   - Record success/fail per run; apply **majority vote** to obtain a deterministic binary outcome for each model, eliminating emulator stochasticity.  
   - Randomly decide whether distilled or baseline runs first (seeded) to avoid order effects.  
4. Run both models on the identical UI state & hint, decode greedily.  
5. Execute generated action sequences in the Android emulator (`utils/emulator.py`). Binary outcome = Success/Fail (post‑majority‑vote).  
6. Build 2×2 contingency table (a,b,c,d).  
7. Apply `scipy.stats.mcnemar` (exact binomial if `b + c < 25`). Compute one‑tailed p‑value (`p/2` if `b > c`).  
8. **Sensitivity Sweep** (see Phase 5) is run here and its results are stored inside the `sensitivity_report` field of the same JSON file.  
9. Write `outputs/evaluation_results.json` conforming to `contracts/evaluation.schema.yaml`. This file is the **SSoT** for all downstream reporting.

### Phase 5 – Sensitivity Sweep (FR‑006)
- Iterate thresholds `{0,1,2,3}` (Levenshtein edit distance).  
- For each threshold, recompute success flags for both models using the majority‑vote outcomes plus the distance criterion (`≤ threshold`).  
- Record per‑threshold success rates inside the `sensitivity_report` object of `outputs/evaluation_results.json`.  
- No binary pass/fail; only variance across thresholds is reported.

### Phase 6 – Hint‑Specific Ablation (Constitution VII)
- Replace every `Corrective_Hint` with the literal `"retry"` in a copy of `outputs/eval_tasks.json`.  
- Re‑run the deterministic paired evaluation (same Phase 4 pipeline, `--mode ablation`).  
- Store results in the `ablation_report` field of `outputs/evaluation_results.json`.

### Phase 7 – Verification & CI
1. `pytest tests/` runs unit, integration, and contract tests.  
2. Contract suite validates every file under `outputs/` against the schemas in `contracts/`.  
3. CI fails if any contract violation, watchdog termination, or CUDA detection occurs.  

---



