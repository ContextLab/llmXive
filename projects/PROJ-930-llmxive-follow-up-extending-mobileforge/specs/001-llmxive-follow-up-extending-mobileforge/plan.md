# Implementation Plan: MobileForge Logic Distillation

**Branch**: `930-logic-distillation` | **Date**: 2026-10-25 | **Spec**: `specs/930-logic-distillation/spec.md`  
**Input**: Feature specification from `specs/930-logic-distillation/spec.md`

## Summary
We will (1) stream and rigorously filter MobileForge logs to produce a high‑quality `(UI_state, Corrective_Hint, Action)` dataset, (2) fine‑tune a CPU‑only encoder‑only model (DistilBERT, ≤ 66 M parameters) on ≤ 20 k training triples within a A few hours of wall‑clock time. on a standard CPU runner, (3) evaluate the distilled model on **500** unseen AndroidWorld tasks against two baselines (Random‑policy & pre‑computed Full MobileForge visual policy) using a **primary McNemar test** for paired binary outcomes and a **supplemental paired two‑tailed t‑test** (Bonferroni‑adjusted) to satisfy SC‑004, (4) conduct a Levenshtein‑based inconsistency‑tolerance sensitivity sweep, (5) run the required hint‑ablation study (statistically significant improvement required, p < 0.05) per SC‑007, and (6) execute a **Reproducibility Checklist**. All steps respect the 6 h CPU wall‑clock for training, and full evaluation is performed offline; CI runs only a pilot subset of tasks..

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers==4.41.0`, `datasets==2.18.0`, `torch==2.2.2`, `scikit-learn==1.5.0`, `pandas==2.2.2`, `numpy==1.26.4`, `pytest==8.2.2`, `jsonschema==4.22.0`, `statsmodels==0.14.2`, `python-Levenshtein==0.25.0`  
- **Storage**: Local filesystem under `data/` (raw logs) and `outputs/` (artifacts).  
- **Testing**: `pytest` (unit, integration, contract).  
- **Target Platform**: GitHub Actions Linux runner (2 CPU cores, ~7 GB RAM, ~14 GB disk).  
- **Constraints**: CPU‑only execution; any CUDA detection aborts per FR‑008. Training ≤ 6 h, model ≤ 100 M parameters.  
- **Scale/Scope**: ≤ 20 k training triples; 500 evaluation tasks (full run performed offline), pilot run on 50 tasks in CI.

## Constitution Check
| Principle | Reference | Compliance |
|-----------|-----------|------------|
| I. Reproducibility | § I | Phase 0 runs `scripts/check_reproducibility.sh`; seeds pinned; CI can re‑run entire pipeline. |
| II. Verified Accuracy | § II | No new citations; only internal references. |
| III. Data Hygiene | § III | Checksums recorded in `data/checksums.json`; raw files never overwritten. |
| IV. Single Source of Truth | § IV | `outputs/evaluation_results.json` is the sole source for all reported numbers. |
| V. Versioning Discipline | § V | Artifact hashes stored in `state/projects/...yaml`; any change updates timestamp. |
| VI. CPU‑Only Inference | § VI | CUDA guard aborts; no GPU escape hatch needed. |
| VII. Hint‑Specific Ablation | § VII | Ablation mode (`--mode ablation`) replaces hints with `"retry"`; significance (p < 0.05) required. |

## Project Structure

```text
specs/930-logic-distillation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── evaluation.schema.yaml          # supplemental paired t‑test schema
    ├── evaluation_result.schema.yaml   # primary McNemar schema
    ├── extraction_dataset.schema.yaml
    ├── power_analysis.schema.yaml
    ├── state_artifacts.schema.yaml
    ├── statistical_report.schema.yaml
    └── training_input.schema.yaml
code/
├── __init__.py
├── requirements.txt
├── bootstrap.py                     # creates all required directories
├── scripts/
│   └── check_reproducibility.sh     # Reproducibility Checklist
├── pipeline/
│   ├── download_mobileforge.py      # streams logs from $MOBILEFORGE_LOGS_URL
│   ├── extract.py                  # filters, validates, splits dataset
│   ├── train.py                    # CPU‑only DistilBERT fine‑tuning
│   └── evaluate.py                 # paired evaluation, sensitivity, ablation
├── data/
│   ├── raw/                         # MobileForge logs (must be provided)
│   ├── processed/                   # filtered splits (train / test)
│   └── evaluation/                  # task‑ID list, baseline predictions
├── models/
│   └── distilled_distilbert/        # checkpoint folder (populated at runtime)
├── utils/
│   ├── power_analysis.py           # a‑priori McNemar power calc (odds‑ratio)
│   └── validate.py                 # regex filter for linguistic hints
└── tests/
    ├── unit/
    │   ├── test_download_mobileforge.py
    │   ├── test_extract.py
    │   ├── test_train.py
    │   └── test_validate.py
    └── integration/
        └── test_evaluate.py
```

## Phase‑by‑Phase Task List (covers every FR/SC)

| Phase | Goal | FR / SC | Key Script(s) | Output |
|-------|------|---------|----------------|--------|
| **0 – Reproducibility Checklist** | Run `scripts/check_reproducibility.sh` to verify seeds, hashes, and that re‑running the pipeline yields identical success rates (≤ 1 % variance). | SC‑001 | `scripts/check_reproducibility.sh` | Log file `outputs/repro_check.log`. |
| **1 – Data Acquisition** | Stream MobileForge logs from `$MOBILEFORGE_LOGS_URL`. Abort with clear error if the variable is unset (the logs are internal; no public URL exists). | FR‑001, SC‑002, SC‑003 | `pipeline/download_mobileforge.py` (uses `datasets.load_dataset(..., streaming=True)`) | `data/raw/*.zip`, `data/checksums.json`. |
| **2 – Validation** | Ensure all hints are purely linguistic (zero flagged). The validator exits with error on any non‑linguistic hint. | FR‑001, SC‑002 | `utils/validate.py` (regex filter) | Pass/Fail status; abort on any flagged hint. |
| **3 – Extraction & Split** | Filter for `failed_then_success` trajectories, produce train/test splits (80/20). | FR‑001, FR‑003 | `pipeline/extract.py` | `outputs/train_split.parquet`, `outputs/test_split.parquet`, `outputs/extraction_meta.json`. |
| **4 – Baseline Construction** | Prepare Random‑policy (fixed seed = 42) and load pre‑computed visual‑policy predictions for the **exact same 500 task IDs**. This guarantees a paired design. | FR‑004 | `pipeline/evaluate.py --prepare-baselines` | `outputs/baselines/random_policy.json`, `data/baselines/visual_policy_predictions.json`. |
| **5 – Power Analysis** | Compute a‑priori sample size for a **McNemar** test with odds‑ratio = 1.5 (medium effect), α = 0.05, power ≥ 0.8. | FR‑007, SC‑006 | `utils/power_analysis.py` | `outputs/power_analysis.json`. |
| **6 – Model Training** | Fine‑tune DistilBERT on ≤ 20 k training triples (CPU only) with watchdog (6 h) and CUDA guard (`if torch.cuda.is_available(): raise RuntimeError`). | FR‑002, FR‑008, SC‑003 | `pipeline/train.py` | `code/models/distilled_distilbert/`, `outputs/training_log.json`. |
| **7 – Evaluation Task Construction** | Sample **500** disjoint task IDs from the test split (seed = 123). Store IDs. | FR‑003, FR‑010 | `pipeline/evaluate.py --prepare-tasks` | `outputs/eval_tasks.json`. |
| **8 – Paired Evaluation (Primary McNemar, Supplemental t‑test)** | For each of the 500 tasks **three independent emulator runs** are executed for distilled model, Random‑policy, and visual‑policy using the same seed sequence (`EMULATOR_SEED=12345 + run_index`). Binary success flags are recorded per run (no majority‑vote). Compute: <br>• **Primary**: McNemar test (`statsmodels.stats.contingency_tables.mcnemar`). <br>• **Supplemental**: Paired two‑tailed t‑test on the same binary differences, Bonferroni‑adjusted for the two baselines. | FR‑003‑005, FR‑010, SC‑004 | `pipeline/evaluate.py --mode standard` | `outputs/evaluation_results.json` (validated against `contracts/evaluation_result.schema.yaml` **and** `contracts/evaluation.schema.yaml`). |
| **9 – Pilot CI Evaluation** | Runs the full evaluation pipeline on a reduced set of **50** tasks (3 runs each) to verify CI feasibility. | – | `pipeline/evaluate.py --mode pilot` | `outputs/pilot_evaluation.json`. |
| **10 – Sensitivity Sweep** | Apply Levenshtein thresholds `{0,1,2,3,4,5}` to each per‑run edit distance; recompute binary success flags and report variance across thresholds. | FR‑006, SC‑005 | Integrated in `pipeline/evaluate.py` (mode = sensitivity) | `sensitivity_report` field in `evaluation_results.json`. |
| **11 – Hint Ablation** | Replace every hint with `"retry"` while keeping UI state and emulator seeds unchanged. Re‑run Phase 8. **Requirement**: McNemar p‑value < 0.05 (statistically significant drop) to satisfy SC‑007. | FR‑009, VII | `pipeline/evaluate.py --mode ablation` | `ablation_report` field in `evaluation_results.json`. |
| **12 – Verification** | Run full test suite, including JSON‑Schema contract checks (`contracts/evaluation_result.schema.yaml`, `contracts/power_analysis.schema.yaml`). | – | `pytest tests/` | Pass/Fail CI status. |

All phases are ordered so that data is downloaded before consumption, models are trained before evaluation, and figures/tables are generated only after evaluation.

## Decision Rationale
| Decision | Rationale |
|----------|-----------|
| `distilbert-base-uncased` (encoder‑only) | ≤ 66 M params, CPU‑tractable, meets FR‑002 & VI. |
| Primary **McNemar** test | Statistically appropriate for paired binary outcomes; fulfills methodological rigor. |
| Supplemental paired t‑test (Bonferroni) | Provides a secondary check while satisfying SC‑004. |
| A‑priori McNemar power analysis (odds‑ratio = 1.5) | Guarantees ≥ 0.8 power per FR‑007 & SC‑006. |
| Three emulator runs recorded separately (no majority‑vote) | Preserves within‑task variability per FR‑010 and scientific soundness. |
| Identical seed schedule for all baselines | Eliminates confound identified in methodology‑3da92bdd. |
| Offline full evaluation + CI pilot | Meets FR‑003 while respecting free‑compute limits (addresses data_resources‑46795cb6). |
| Reproducibility Checklist script | Directly satisfies SC‑001. |
| Explicit abort if `$MOBILEFORGE_LOGS_URL` unset + demo dataset note | Addresses data_resources‑bf88c5ad and clarifies dataset availability. |
| Hint‑ablation significance requirement (p < 0.05) | Meets SC‑007. |
| Contract usage: `evaluation_result.schema.yaml` (McNemar) as primary, `evaluation.schema.yaml` (paired t‑test) as secondary | Ensures every contract is exercised (plan_consistency‑adc9c9f4). |
| Power analysis description aligned with `power_analysis.schema.yaml` (odds‑ratio) | Resolves plan_consistency‑9bcce6f3. |
| Directory bootstrap and explicit sub‑directory list | Fixes T001 missing directories. |
| Download script located at `code/pipeline/download_mobileforge.py` | Provides required script location (addresses T008). |
| Validation script exits with error on any non‑linguistic hint | Fixes T009. |
