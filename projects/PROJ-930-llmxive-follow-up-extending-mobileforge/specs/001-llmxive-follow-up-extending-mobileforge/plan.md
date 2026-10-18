# Implementation Plan: MobileForge Logic Distillation

**Branch**: `930-logic-distillation` | **Date**: 2026-10-17 | **Spec**: `specs/930-logic-distillation/spec.md`  
**Input**: Feature specification from `specs/930-logic-distillation/spec.md`

## Summary
The study aims to **distill logical reasoning** from MobileForge “failed‑then‑success” trajectories into a lightweight **encoder‑only** model that can be trained and evaluated on a CPU‑only runner within a 6 h wall‑clock budget. The plan now respects all functional requirements (FR‑001 – FR‑010) and non‑functional constraints (SC‑001 – SC‑006) **as far as current open resources allow**. Where the specification demands data or baselines that cannot be obtained or executed under CPU‑only constraints, the plan explicitly flags the mismatch and requests a scope revision rather than fabricating substitutes.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers==4.41.0`, `datasets==2.18.0`, `torch==2.2.2`, `scikit-learn==1.5.0`, `pandas==2.2.2`, `numpy==1.26.4`, `pytest==8.2.2`, `jsonschema==4.22.0`, `statsmodels==0.14.2`  
- **Storage**: Local filesystem (`data/`, `outputs/`)  
- **Testing**: `pytest` (unit, integration, contract)  
- **Target Platform**: GitHub Actions Linux runner (2 CPU cores, ~7 GB RAM, ~14 GB disk)  
- **Constraints**: CPU‑only execution (any CUDA detection aborts), training ≤ 6 h, ≤ 100 M parameters, deterministic seeds, no synthetic fallbacks, full reproducibility.

## Constitution Check
| Principle | Reference | Compliance |
|-----------|-----------|------------|
| I. Reproducibility | § I | All scripts are deterministic; seeds are pinned; CI runs from scratch. |
| II. Verified Accuracy | § II | No new citations added; the baseline visual‑policy URL is omitted because it cannot be executed under CPU‑only constraints. |
| III. Data Hygiene | § III | Checksums recorded in `data/checksums.json`; raw files never overwritten. |
| IV. Single Source of Truth | § IV | `outputs/evaluation_results.json` is the sole source for every figure/table. |
| V. Versioning Discipline | § V | All artifacts are content‑hashed; `state/projects/...yaml` will be updated automatically. |
| VI. CPU‑Only Inference | § VI | CUDA guard aborts; no GPU fallback required. |
| VII. Hint‑Specific Ablation | § VII | Ablation mode replaces hints with `"retry"` and re‑evaluates. |

## Project Structure

```text
specs/930-logic-distillation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── evaluation.schema.yaml
    ├── evaluation_result.schema.yaml
    ├── extraction_dataset.schema.yaml
    ├── power_analysis.schema.yaml
    ├── state_artifacts.schema.yaml
    ├── statistical_report.schema.yaml
    └── training_input.schema.yaml

code/
├── __init__.py
├── requirements.txt
├── bootstrap.py                     # creates all required directories
├── pipeline/
│   ├── download.py                  # placeholder for MobileForge log download (to be provided)
│   ├── extract.py                   # filtering & split creation
│   ├── train.py                     # DistilBERT fine‑tuning
│   └── evaluate.py                  # paired evaluation, sensitivity, ablation
├── data/
│   ├── raw/                         # **expected** MobileForge log files (not currently available)
│   ├── processed/
│   └── evaluation/
├── models/
│   └── distilled_distilbert/        # checkpoint folder (populated at runtime)
├── utils/
│   ├── power_analysis.py
│   └── emulator.py
└── tests/
    ├── unit/
    │   ├── test_download.py
    │   ├── test_extract.py
    │   └── test_train.py
    └── integration/
        └── test_evaluate.py

data/
├── raw/                             # placeholder for MobileForge logs
├── checksums.json
└── processed/                       # empty until extraction step

outputs/
├── power_analysis.json
├── extraction_meta.json
├── train_split.parquet
├── test_split.parquet
├── training_log.json
├── distilled_distilbert/ (model checkpoint)
├── eval_tasks.json
├── evaluation_results.json   # **SSoT** for all reported numbers
└── (no separate sensitivity_report.json)
```

### Directory Creation (addresses **T001**, **plan_consistency‑bc494354**)
`code/bootstrap.py` creates **all** nested directories listed above, including:
- `code/data/raw/`, `code/data/processed/`, `code/data/evaluation/`
- `code/models/` (the checkpoint directory for the distilled model)
- `code/tests/unit/` and `code/tests/integration/`
- `data/raw/`, `data/processed/`

### Data Acquisition (addresses **FR‑001**, **data_resources‑8c90e7fe**, **spec_coverage‑907db54b**)
- **Script Path**: `code/pipeline/download.py` (currently a placeholder).  
- **Intended Source**: MobileForge instrumentation logs (the only permissible source per FR‑001).  
- **Current Status**: No open MobileForge log dataset exists; the plan therefore **flags this data‑availability mismatch** and requests a specification revision. No proxy dataset is used.

### Validation (addresses **SC‑002**)
- Loaders will verify SHA‑256 checksums recorded in `data/checksums.json`. Missing or corrupted files cause a hard failure.

## Complexity Tracking (FR / SC → Phase / Task)

| FR / SC | Phase / Task |
|--------|--------------|
| FR‑001 | Phase 2 – `pipeline/download.py` (placeholder) & `pipeline/extract.py` |
| FR‑002 | Phase 3 – `pipeline/train.py` (DistilBERT encoder‑only) |
| FR‑003 | Phase 4 – `pipeline/evaluate.py` (evaluation tasks to be sourced from MobileForge logs; currently unavailable) |
| FR‑004 | Phase 4 – **paired inference on exact same task instances** for the two feasible baselines (TinyLlama and random‑policy). The full MobileForge visual‑policy baseline is omitted because it cannot be run under CPU‑only constraints; this limitation is documented and a spec revision is requested. |
| FR‑005 | Phase 4 – Paired two‑tailed **t‑test** on continuous success proportions |
| FR‑006 | Phase 5 – Sensitivity sweep on Levenshtein thresholds |
| FR‑007 | Phase 1 – `utils/power_analysis.py` (a‑priori power analysis) |
| FR‑008 | Phase 3 – CUDA guard in `pipeline/train.py` |
| FR‑009 | Phase 6 – Hint‑ablation mode in `pipeline/evaluate.py` |
| FR‑010 | Phase 4 – Emulator determinism control (three runs, majority‑vote for binary outcome; continuous mean retained for t‑test) |
| SC‑001 | Phase 0 – `code/requirements.txt` (pinned) |
| SC‑002 | Phase 2 – loader aborts on missing/corrupt data |
| SC‑003 | Phase 3 – watchdog (`signal.alarm`) |
| SC‑004 | Phase 4 – significance threshold `p < 0.05` (two‑tailed) |
| SC‑005 | Phase 5 – variance‑only reporting |
| SC‑006 | Phase 1 – documented a‑priori power parameters (target power = 0.8, d = 0.5, α = 0.05) |
| SC‑007 | Phase 6 – ablation compliance with Constitution VII |

## Implementation Phases

### Phase 0 – Bootstrap & Directory Creation
```bash
python code/bootstrap.py
# Confirms that all required directories exist.
```

### Phase 1 – A‑Prior Power Analysis (FR‑007, SC‑006)
`utils/power_analysis.py` computes the required **N** for a paired‑t‑test given:
- Target power = 0.8
- Effect size = Cohen’s d = 0.5
- α = 0.05  
Outputs `outputs/power_analysis.json` conforming to `contracts/power_analysis.schema.yaml`.

### Phase 2 – Data Download & Validation (FR‑001)
1. `pipeline/download.py` (placeholder) is intended to fetch MobileForge logs from the official instrumentation repository (requires specification update).  
2. SHA‑256 recorded in `data/checksums.json`.  
3. `pipeline/extract.py` filters rows where `trajectory_status == "failed_then_success"` and where `corrective_hint` contains no coordinate regex. Generates `outputs/train_split.parquet`, `outputs/test_split.parquet`, and `outputs/extraction_meta.json`.

### Phase 3 – CPU‑Tractable Model Training (FR‑002, FR‑008, SC‑003)
- **Model**: `distilbert-base-uncased` (≈ 66 M parameters, encoder‑only).  
- **CUDA Guard** at the top of `pipeline/train.py`.  
- **Watchdog** (`signal.alarm(6*60*60)`).  
- Sample ≤ 20 k triples from `outputs/train_split.parquet` (seed = 42).  
- Fine‑tune via `transformers.Trainer` (batch = 8, grad‑acc = 4, lr = 3e‑4, max epochs = 3, early‑stop = 1).  
- Save checkpoint to `code/models/distilled_distilbert/`.  
- Log to `outputs/training_log.json`.

### Phase 4 – Paired Evaluation & Paired t‑Test (FR‑003‑005, FR‑010, SC‑004)
1. Load `outputs/power_analysis.json` → retrieve required **N** (once data become available).  
2. **Evaluation Task Construction**: When MobileForge logs are supplied, sample exactly **N** disjoint tasks, ensuring no overlap with training data; store IDs in `outputs/eval_tasks.json`.  
3. For each task and each **feasible** model (distilled DistilBERT, TinyLlama baseline, random‑policy baseline):
   - Run emulator three times with fixed `EMULATOR_SEED=12345`.  
   - Record the **continuous success proportion** across the three runs (values 0, 1/3, 2/3, 1).  
4. Compute per‑model mean success probability across tasks.  
5. Perform a **paired two‑tailed t‑test** comparing distilled model vs. each baseline on the continuous success proportions (`scipy.stats.ttest_rel`).  
6. Write `outputs/evaluation_results.json` (conforms to `contracts/evaluation.schema.yaml`) containing `metrics`, `statistical_test`, `power_analysis`, `sensitivity_report`, and `ablation_report`.

*Note*: The full MobileForge visual‑policy baseline is omitted due to infeasibility under CPU‑only constraints; this limitation is documented and a spec revision is requested.

### Phase 5 – Sensitivity Sweep (FR‑006)
Iterate Levenshtein thresholds `{0,1,2,3}`; for each threshold recompute binary success flags (using the continuous proportion as the underlying metric) for both models. Record per‑threshold success rates inside the `sensitivity_report` object of `outputs/evaluation_results.json`. No binary pass/fail; only variance is reported.

### Phase 6 – Hint‑Specific Ablation (Constitution VII)
Replace every `Corrective_Hint` with the literal `"retry"` for all evaluation tasks, keeping UI state and seed identical. Re‑run Phase 4 (`pipeline/evaluate.py --mode ablation`). Merge results into the `ablation_report` field of `outputs/evaluation_results.json`. Demonstrates that gains stem from the specific hint content.

### Phase 7 – Verification
`pytest tests/` runs unit, integration, and contract tests. Contract suite validates every file under `outputs/` against the schemas in `contracts/`. CI fails on any contract violation, watchdog timeout, or CUDA detection.

---


