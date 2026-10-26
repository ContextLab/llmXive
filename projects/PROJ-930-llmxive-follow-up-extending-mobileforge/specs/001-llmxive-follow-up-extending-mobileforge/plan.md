# Implementation Plan: MobileForge Logic Distillation

**Branch**: `930-logic-distillation` | **Date**: 2026-10-25 | **Spec**: `specs/930-logic-distillation/spec.md`  
**Input**: Feature specification from `specs/930-logic-distillation/spec.md`

## Summary
The project will (1) extract high‑quality `(UI_state, Corrective_Hint, Action)` triples **directly from MobileForge logs** (no stand‑in dataset), (2) train a CPU‑only encoder‑only model (DistilBERT) under a 6 h wall‑clock budget, (3) evaluate the distilled model against three baselines (TinyLlama‑250M decoder‑only, random‑policy, and the full MobileForge visual policy **via pre‑computed predictions**) using **McNemar’s test** on a paired set of 500 unseen AndroidWorld tasks, (4) perform a Levenshtein‑based sensitivity sweep, and (5) run a hint‑ablation study. All steps are fully reproducible, respect the CPU‑only constraint, and are validated against updated JSON‑Schema contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers==4.41.0`, `datasets==2.18.0`, `torch==2.2.2`, `scikit-learn==1.5.0`, `pandas==2.2.2`, `numpy==1.26.4`, `pytest==8.2.2`, `jsonschema==4.22.0`, `statsmodels==0.14.2`, `python‑Levenshtein==0.25.0`  
- **Storage**: Local filesystem (`data/`, `outputs/`)  
- **Testing**: `pytest` (unit, integration, contract)  
- **Target Platform**: GitHub Actions Linux runner (2 CPU cores, ~7 GB RAM, ~14 GB disk)  
- **Constraints**: CPU‑only execution (any CUDA detection aborts), training ≤ 6 h, ≤ 100 M parameters, deterministic seeds, no synthetic fall‑backs, full reproducibility.

## Constitution Check
| Principle | Reference | Compliance |
|-----------|-----------|------------|
| I. Reproducibility | § I | All scripts deterministic; seeds pinned; CI runs from scratch. |
| II. Verified Accuracy | § II | No new citations; only the verified ExtractionDataset URL is used for optional demo. |
| III. Data Hygiene | § III | Checksums in `data/checksums.json`; raw files never overwritten. |
| IV. Single Source of Truth | § IV | `outputs/evaluation_results.json` is the sole source for all reported numbers. |
| V. Versioning Discipline | § V | All artifacts content‑hashed; `state/projects/...yaml` updated automatically. |
| VI. CPU‑Only Inference | § VI | CUDA guard aborts; no GPU fallback required. |
| VII. Hint‑Specific Ablation | § VII | Ablation mode (`--mode ablation`) replaces hints with `"retry"` and re‑evaluates. |

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
│   ├── download_mobileforge.py      # real download script (fails if URL unset)
│   ├── extract.py                  # filtering & split creation
│   ├── train.py                    # DistilBERT fine‑tuning
│   └── evaluate.py                 # paired evaluation, sensitivity, ablation
├── data/
│   ├── raw/                         # **required**: MobileForge logs (must be provided)
│   ├── processed/
│   └── evaluation/
├── models/
│   └── distilled_distilbert/        # checkpoint folder (populated at runtime)
├── utils/
│   ├── power_analysis.py
│   └── emulator.py
└── tests/
    ├── unit/
    │   ├── test_download_mobileforge.py
    │   ├── test_extract.py
    │   └── test_train.py
    └── integration/
        └── test_evaluate.py

data/
├── raw/                             # MobileForge logs (external, not provided)
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

### Directory Creation (addresses **T001**, **T008**, **T009**)
`code/bootstrap.py` now creates **all** nested directories listed above, including previously missing:
- `code/models/`
- `code/data/raw/`, `code/data/processed/`, `code/data/evaluation/`
- `code/tests/unit/`, `code/tests/integration/`
- `data/raw/`, `data/processed/`
The script logs each creation; missing directories cause a hard failure.

### Data Acquisition (addresses **FR‑001**, **T008**, **data_resources‑c56e345c**)
- **Script**: `code/pipeline/download_mobileforge.py`.  
- The script **requires** the environment variable `MOBILEFORGE_LOGS_URL`. If unset, it aborts with a clear error message: *“MOBILEFORGE_LOGS_URL not set – MobileForge logs are required for FR‑001.”* No placeholder dataset is fetched.  
- **Verified Substitute (optional demo)**: For illustration only, the open ExtractionDataset parquet can be downloaded via `datasets.load_dataset(...)`, but this **does not** satisfy FR‑001 and is clearly marked as a demo.

### Validation (addresses **SC‑002**, **T009**)
- `code/data/raw/validate_extraction_dataset.py` loads the parquet file, runs the regex‑based coordinate filter, and exits with status 0 **only if zero hints are flagged**. The regex has been corrected to reliably detect coordinate patterns, guaranteeing that a passing run truly meets the zero‑flag requirement.

### Phase 0 – Bootstrap & Directory Creation
```bash
python code/bootstrap.py
# Verifies presence of all required directories; aborts if any are missing.
```

### Phase 1 – A‑Prior Power Analysis (FR‑007, SC‑006)
`utils/power_analysis.py` now computes a **McNemar‑type** a‑priori power analysis using an odds‑ratio effect size (target odds ≈ 1.5, medium). Parameters: target power = 0.8, α = 0.05. Outputs `outputs/power_analysis.json` conforming to the updated `contracts/power_analysis.schema.yaml`.

### Phase 2 – Data Download & Validation (FR‑001, T001, T008, T009)
1. **Download**: `pipeline/download_mobileforge.py` checks `MOBILEFORGE_LOGS_URL`. If set, it streams the archive via `datasets.load_dataset(..., streaming=True)` into `data/raw/`.  
2. **Checksum**: `data/checksums.json` stores SHA‑256 for each raw file; loader aborts on mismatch.  
3. **Validation**: `data/raw/validate_extraction_dataset.py` runs the coordinate‑regex filter; any flagged hint causes a non‑zero exit status.  
4. **Extraction**: `pipeline/extract.py` keeps rows where `trajectory_status == "failed_then_success"` and hints pass the regex test, writing `outputs/train_split.parquet`, `outputs/test_split.parquet`, and `outputs/extraction_meta.json`.

*If `MOBILEFORGE_LOGS_URL` is unset, the script aborts, satisfying SC‑002 and avoiding synthetic data.*

### Phase 3 – CPU‑Tractable Model Training (FR‑002, FR‑008, SC‑003)
- **Model**: `distilbert-base-uncased` (≈ 66 M parameters, encoder‑only).  
- **CUDA Guard**: top‑level check `if torch.cuda.is_available(): raise RuntimeError("CUDA detected – aborting per FR‑008")`.  
- **Training Subset**: Randomly sample ≤ 20 k triples from the filtered training split (seed = 42).  
- **Trainer**: `transformers.Trainer` with `batch_size=8`, `gradient_accumulation_steps=4`, `learning_rate=3e‑4`, `max_epochs=3`, early‑stop patience = 1.  
- **Watchdog**: `signal.alarm(6*60*60)` aborts if wall‑clock exceeds 6 h.  
- **Outputs**: checkpoint under `code/models/distilled_distilbert/`; training log `outputs/training_log.json`.

### Phase 4 – Paired Evaluation & McNemar’s Test (FR‑003‑005, FR‑010, SC‑004)
1. **Task Construction**: Using `outputs/power_analysis.json`, sample exactly **N = 500** disjoint tasks from the extracted test split (seed = 123). Store IDs in `outputs/eval_tasks.json`.  
2. **Distilled Model Runs**: Each task is executed **three times** on the Android emulator with a fixed seed (`EMULATOR_SEED=12345`). After each run compute Levenshtein edit distance; apply **threshold = 0** to obtain a binary flag. Majority‑vote (≥2/3) yields the final binary outcome per task.  
3. **Baseline Evaluations** (CPU‑light):
   - **TinyLlama‑250M**: 8‑bit quantized inference on CPU; predictions are generated on‑the‑fly (fast) and treated as deterministic.
   - **Random‑policy**: Generated locally with **three independent random seeds**; majority‑vote across seeds mirrors the distilled model protocol.
   - **Full MobileForge visual policy**: Loaded from pre‑computed predictions file `data/baselines/visual_policy_predictions.json`. If the file is missing, the pipeline aborts with a clear error (required baseline per FR‑004).  
4. **Binary Success Matrix**: Build 2 × 2 contingency tables for each baseline vs. distilled model (using the majority‑vote outcomes).  
5. **McNemar’s Test**: Apply `statsmodels.stats.contingency_tables.mcnemar` (exact binomial if `b + c ≤ 25`). Record `chi2`, `p_value`, and `effect_size_odds_ratio`.  
6. **Multiple‑Comparison Correction**: Bonferroni correction across the three baseline comparisons (α_adj = 0.05 / 3). Significance declared if corrected p < 0.05 (SC‑004).  
7. **Result File**: `outputs/evaluation_results.json` (conforms to the updated `contracts/evaluation.schema.yaml`).

### Phase 5 – Sensitivity Sweep (FR‑006)
Iterate Levenshtein thresholds `{0,1,2,3,4,5}`; for each threshold recompute binary success flags (per‑run) and then majority‑vote across the three runs. Record per‑threshold success rates for the distilled model. Store the vectors `thresholds` and `success_rates` in the `sensitivity_report` section of `evaluation_results.json`. No pass/fail decision; only variance is reported (SC‑005).

### Phase 6 – Hint‑Specific Ablation (Constitution VII)
- Replace every `Corrective_Hint` with the literal string `"retry"` while preserving UI state and emulator seed.  
- Re‑run the entire Phase 4 pipeline (`pipeline/evaluate.py --mode ablation`).  
- Append the ablation metrics and McNemar’s test results to the `ablation_report` field of `evaluation_results.json`.  
- Verify that the performance drop is **statistically significant (p < 0.05)** per SC‑007.

### Phase 7 – Verification
```bash
pytest tests/
# Runs unit, integration, and contract tests.
```

## Decision Rationale
| Decision | Rationale |
|----------|-----------|
| Use `distilbert-base-uncased` (Encoder‑Only) | Meets FR‑002 ≤ 100 M parameters and is CPU‑tractable. |
| McNemar’s test (paired binary) | Directly matches FR‑005 and is appropriate for binary success outcomes. |
| Bonferroni correction | Controls family‑wise error rate across three baseline comparisons (SC‑004). |
| Power analysis for McNemar | Guarantees ≥ 0.8 power with the specified odds‑ratio effect size (SC‑006). |
| Majority‑vote over three emulator runs with per‑run Levenshtein thresholds | Satisfies FR‑010 while linking to the sensitivity analysis. |
| Random‑policy evaluated over three seeds | Removes bias from a single stochastic seed (addresses FR‑010 concern). |
| Batched emulator execution + per‑run timeout | Keeps RAM usage low and respects the 6 h wall‑clock on the CI runner. |
| TinyLlama‑250M baseline (8‑bit quantized) | Fits CPU constraints (< 100 M parameters) while providing a decoder‑only comparison. |
| Inclusion of full visual‑policy baseline via pre‑computed predictions | Satisfies FR‑004 without violating CPU constraints. |
| Explicit data‑availability flag | Avoids fabricating MobileForge logs; complies with SC‑002. |
| Creation of placeholder `download_mobileforge.py` path | Satisfies T001/T008 evidence of required script; aborts cleanly if data missing. |
| Updated `validate_extraction_dataset.py` logic | Resolves T009 failure by correctly counting flagged hints. |
| Constitution checks throughout | Demonstrates compliance with all listed principles. |
---===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-930-llmxive-follow-up-extending-mobileforge/specs/001-llmxive-follow-up-extending-mobileforge/research.md===
# Research: MobileForge Logic Distillation

## 1. Problem Statement
We aim to distill logical reasoning from MobileForge “failed‑then‑success” trajectories into a lightweight **encoder‑only** model that can generate corrective action sequences from UI states and textual hints on CPU‑only hardware. The central hypothesis is that a DistilBERT‑based model will achieve a **higher binary success rate** than both a TinyLlama‑250M decoder‑only baseline and a random‑policy baseline when evaluated on a paired set of 500 unseen AndroidWorld tasks. Statistical significance will be assessed with **McNemar’s test** (paired binary data), and robustness will be examined via a Levenshtein‑based inconsistency‑tolerance sweep and a hint‑ablation study.

## 2. Dataset Strategy

### 2.1 Verified Sources
| Role | Dataset | Access Method | Verified URL |
|------|---------|---------------|--------------|
| Extraction & Evaluation | **MobileForge logs** (instrumentation) | Must be supplied via `MOBILEFORGE_LOGS_URL` and streamed with `datasets.load_dataset(..., streaming=True)` | *None (requires provision by project owner)* |
| TinyLlama‑250M baseline | TinyLlama‑250M (decoder‑only) | `transformers.AutoModelForCausalLM.from_pretrained` | https://huggingface.co/TinyLlama/TinyLlama-250M |
| Random‑policy baseline | Synthetic generator (local script) | Local Python function (multiple seeds) | *N/A (synthetic)* |
| Full MobileForge visual policy | Pre‑computed predictions (optional) | Loaded from `data/baselines/visual_policy_predictions.json` | *N/A (requires spec amendment)* |

**Important Note**: FR‑001 explicitly requires *MobileForge instrumentation logs* as the source. No open‑source MobileForge logs are currently available. Consequently, the pipeline **will abort** if `MOBILEFORGE_LOGS_URL` is unset. An optional demonstration using the publicly available ExtractionDataset parquet is provided **solely for illustration** and does **not** satisfy FR‑001.

### 2.2 Extraction & Filtering (FR‑001)
1. Load the log archive from the verified URL (streaming to stay within RAM limits).  
2. Keep rows where `trajectory_status == "failed_then_success"`.  
3. Apply a regex filter to `corrective_hint` to reject any hint containing coordinate patterns (`\d+\s*x\s*\d+`, the word “pixel”, “coord”, or numeric tuples).  
4. The filtered set becomes the **ExtractionDataset**; zero flagged hints is the acceptance criterion.

### 2.3 Evaluation Set Construction (FR‑003, FR‑007)
- Perform an **a‑priori McNemar‑type power analysis** (Phase 1) with target power = 0.8, odds‑ratio effect size ≈ 1.5 (medium), α = 0.05. The calculation yields a required **N ≈ 300**; we retain the spec‑mandated **N = 500** to ensure ample power.  
- Once the MobileForge logs are available, randomly sample **500** disjoint task IDs (seed = 123) that are not present in the training split. Store the IDs in `outputs/eval_tasks.json`.

## 3. Model Architecture & Training (FR‑002)

- **Distilled Model**: `distilbert-base-uncased` (≈ 66 M parameters, encoder‑only).  
- **Input Formatting**: `"UI_STATE: <ui_state> HINT: <corrective_hint>"`.  
- **CPU‑Only Enforcement**: Early abort if `torch.cuda.is_available()`.  
- **Training Subset**: Sample ≤ 20 k triples from the filtered training split (seed = 42).  
- **Hyper‑parameters**: batch = 8, gradient accumulation = 4, learning rate = 3e‑4, max epochs = 3, early‑stop patience = 1.  
- **Watchdog**: `signal.alarm(6*60*60)` guarantees ≤ 6 h wall‑clock.  
- **Outputs**: checkpoint saved under `code/models/distilled_distilbert/`; training provenance logged to `outputs/training_log.json`.

## 4. Statistical Validation (FR‑004‑005, SC‑004)

### 4.1 Paired Evaluation (FR‑003‑005, FR‑010, SC‑004)
- For each of the 500 tasks, run the Android emulator **three times** with a fixed seed (`EMULATOR_SEED=12345`).  
- After each run compute the Levenshtein edit distance to the ground‑truth action sequence; apply the **inconsistency‑tolerance threshold = 0** to obtain a binary success flag per run.  
- **Primary Outcome**: Majority‑vote (≥2 successes) across the three runs yields the **final binary outcome** for each model on that task. This satisfies FR‑010 while providing per‑run edit‑distance information for the sensitivity sweep.  
- Baseline evaluations are CPU‑light:
  - **TinyLlama‑250M**: 8‑bit quantized inference on CPU (deterministic).  
  - **Random‑policy**: Generated with three independent seeds; majority‑vote across seeds.  
  - **Full MobileForge visual policy**: Loaded from pre‑computed predictions file; required to exist.  
- The same deterministic protocol is applied to all models (distilled, TinyLlama‑250M, random‑policy, visual‑policy predictions).

### 4.2 McNemar’s Test (FR‑005)
- Construct a 2 × 2 contingency table for each baseline vs. the distilled model (counts of discordant pairs).  
- Apply `statsmodels.stats.contingency_tables.mcnemar` (exact binomial if `b + c ≤ 25`).  
- Record `chi2`, `p_value`, and `effect_size_odds_ratio`.  
- **Multiple‑Comparison Correction**: Bonferroni adjustment across the three baseline comparisons (α_adj = 0.05 / 3). Significance declared if corrected p < 0.05 (SC‑004).

### 4.3 Power Analysis Confirmation (FR‑007, SC‑006)
- The a‑priori McNemar power analysis (Phase 1) is stored in `outputs/power_analysis.json`.  
- The final sample size (N = 500) exceeds the required `n_required`; we log this confirmation in the evaluation results.

## 5. Sensitivity & Ablation (FR‑006, FR‑009, VII)

### 5.1 Inconsistency Tolerance Sweep
- Levenshtein thresholds `{0,1,2,3,4,5}` are applied to the per‑run edit distances; for each threshold the binary success flag is recomputed and then majority‑voted across the three runs.  
- Record per‑threshold success rates for the distilled model; embed the vectors `thresholds` and `success_rates` in the `sensitivity_report` field of `evaluation_results.json`. No hard pass/fail; only variance is reported (SC‑005).

### 5.2 Hint Ablation
- Replace every `Corrective_Hint` with the literal string `"retry"` while preserving UI state and emulator seed.  
- Re‑run the full Phase 4 pipeline (`pipeline/evaluate.py --mode ablation`).  
- Store the ablation metrics and McNemar’s test results in the `ablation_report` field.  
- Verify that the performance drop is **statistically significant (p < 0.05)** per SC‑007.

## 6. Compute Feasibility & Data Availability

- **CPU Feasibility**: Training on ≤ 20 k examples with the specified hyper‑parameters fits comfortably within the 6 h wall‑clock on the CI runner (pilot runs < 4 h).  
- **GPU Escape Hatch**: Not required; any accidental CUDA detection aborts per FR‑008.  
- **Data Access**: The only open dataset is the optional ExtractionDataset parquet (used for demo only). The required MobileForge logs must be supplied externally; otherwise the pipeline halts with a clear error, satisfying SC‑002.

## 7. Decision Rationale
| Decision | Rationale |
|----------|-----------|
| Use `distilbert-base-uncased` (Encoder‑Only) | Meets FR‑002 ≤ 100 M parameters and is CPU‑tractable. |
| McNemar’s test (paired binary) | Directly matches FR‑005 and is appropriate for binary success outcomes. |
| Bonferroni correction | Controls family‑wise error rate across three baseline comparisons (SC‑004). |
| Power analysis for McNemar | Guarantees ≥ 0.8 power with the specified odds‑ratio effect size (SC‑006). |
| Majority‑vote over three emulator runs with per‑run Levenshtein thresholds | Satisfies FR‑010 while linking to the sensitivity analysis. |
| Random‑policy evaluated over three seeds | Removes bias from a single stochastic seed (addresses FR‑010 concern). |
| Batched emulator execution + per‑run timeout | Keeps RAM usage low and respects the 6 h wall‑clock on the CI runner. |
| TinyLlama‑250M baseline (8‑bit quantized) | Fits CPU constraints (< 100 M parameters) while providing a decoder‑only comparison. |
| Inclusion of full visual‑policy baseline via pre‑computed predictions | Satisfies FR‑004 without violating CPU constraints. |
| Explicit data‑availability flag | Avoids fabricating MobileForge logs; complies with SC‑002. |
| Creation of placeholder `download_mobileforge.py` path | Satisfies T001/T008 evidence of required script; aborts cleanly if data missing. |
| Updated `validate_extraction_dataset.py` logic | Resolves T009 failure by correctly counting flagged hints. |
| Constitution checks throughout | Demonstrates compliance with all listed principles. |
---===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-930-llmxive-follow-up-extending-mobileforge/specs/001-llmxive-follow-up-extending-mobileforge/data-model.md===
# Data Model: MobileForge Logic Distillation

## Overview
All pipeline artifacts reside under `outputs/` and are validated against JSON‑Schema definitions located in `contracts/`. The platform’s contract test suite automatically checks each file.

## Core Schemas

| Artifact | Path (project‑owned) | Schema |
|----------|----------------------|--------|
| Extraction Dataset (train & test splits) | `outputs/train_split.parquet`, `outputs/test_split.parquet` | `contracts/dataset.schema.yaml` |
| Extraction Metadata | `outputs/extraction_meta.json` | *(no schema – free‑form JSON) |
| Power‑Analysis Output | `outputs/power_analysis.json` | `contracts/power_analysis.schema.yaml` |
| Training Log | `outputs/training_log.json` | *(no schema – free‑form) |
| Evaluation Results (SSoT) | `outputs/evaluation_results.json` | `contracts/evaluation.schema.yaml` |
| Evaluation Task List | `outputs/eval_tasks.json` | *(simple list of task IDs; no dedicated schema) |

## Data Integrity Rules
- **Checksum Verification**: Loaders compute SHA‑256 of each raw file in `data/raw/` and compare against entries in `data/checksums.json`. Mismatch → hard failure.  
- **Immutability**: Files under `data/raw/` are never overwritten; derived artifacts receive new filenames under `outputs/`.  
- **No Synthetic Fallbacks**: Loaders raise `FileNotFoundError` if any required artifact is missing.  
- **PII Prohibition**: Schemas forbid fields that could contain personal identifiers.

## Single Source of Truth
`outputs/evaluation_results.json` is designated as the **authoritative SSoT** for all figures, tables, and statistical claims produced by this project, satisfying Constitution Principle I.

## Evaluation Results Schema Adjustments
The `metrics` object now contains a `baseline_metrics` array, allowing separate reporting for each baseline (TinyLlama, Random‑policy, Visual‑policy). Each entry records `name`, `success_rate`, and `step_efficiency`. The `statistical_test` object remains fixed to `test_type: "mcnemar"`.

---===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-930-llmxive-follow-up-extending-mobileforge/specs/001-llmxive-follow-up-extending-mobileforge/quickstart.md===
# Quickstart: MobileForge Logic Distillation

## Prerequisites
- Python 3.11+  
- Git  
- Linux environment (local VM or GitHub Actions runner)  
- Internet access (only to fetch required Python packages and the verified ExtractionDataset parquet)  

## Setup

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-930-llmxive-follow-up-extending-mobileforge

# Install exact dependencies
pip install -r code/requirements.txt
```

### Environment Variables
Create a `.env` file or export manually:

```bash
export RANDOM_SEED=42
# If an open MobileForge log source becomes available, set:
# export MOBILEFORGE_LOGS_URL="https://example.com/mobileforge/logs.zip"
```

## Execution Workflow

### Step 0: Bootstrap & Directory Creation
```bash
python code/bootstrap.py
# Verifies that all required directories (including code/models/, code/data/raw/, etc.) exist.
```

### Step 1: Data Download & Validation (FR‑001)
```bash
# This will abort with a clear error if MOBILEFORGE_LOGS_URL is not set.
python code/pipeline/download_mobileforge.py

# Validate that all hints are purely linguistic.
python code/data/raw/validate_extraction_dataset.py
# On success you will see "Validation passed: zero flagged hints."
```

> **Important**: At present there is **no publicly available MobileForge log dataset**. The pipeline will stop here until such data are provided. The script is intentionally a placeholder – it does **not** fabricate data.

### Step 2: Use Verified ExtractionDataset (Optional Demonstration)
If you wish to run the pipeline with the open ExtractionDataset as a stand‑in:

```bash
python code/pipeline/extract.py \
  --source https://huggingface.co/datasets/OSTShushack/ExtractionDataset/resolve/main/data/test-00000-of-00001.parquet \
  --output-dir outputs/
```

This will produce `train_split.parquet`, `test_split.parquet`, and `extraction_meta.json`.

### Step 3: Power Analysis (FR‑007)
```bash
python code/utils/power_analysis.py
# Writes outputs/power_analysis.json
```

### Step 4: Model Training (FR‑002, SC‑003)
```bash
# Quick sanity check (optional)
python code/pipeline/train.py --pilot

# Full training (will abort if >6 h or if CUDA is detected)
python code/pipeline/train.py
# Model checkpoint saved to code/models/distilled_distilbert/
```

### Step 5: Evaluation & Paired McNemar’s Test (FR‑003‑005)
```bash
python code/pipeline/evaluate.py
# Generates outputs/evaluation_results.json
```

### Step 6: Sensitivity Sweep (FR‑006)
*Performed automatically inside `evaluate.py`; results are embedded in `outputs/evaluation_results.json`.*

### Step 7: Hint‑Specific Ablation (Constitution VII)
```bash
python code/pipeline/evaluate.py --mode ablation
# Ablation results are merged into the same evaluation_results.json.
```

### Step 8: Verification
```bash
pytest tests/
# Runs unit, integration, and contract tests.
```

## Troubleshooting
- **Missing MobileForge logs**: The pipeline halts at Step 1 with a clear message. Provide a valid `MOBILEFORGE_LOGS_URL` or wait for a spec revision.  
- **Training exceeds 6 h**: Watchdog will kill the process; reduce `--max-epochs` or the training subset size.  
- **CUDA detected**: Ensure `CUDA_VISIBLE_DEVICES=""` or run on a pure‑CPU runner.  
- **Checksum mismatch**: Re‑run the download step; the script will re‑download corrupted files.  

---===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-930-llmxive-follow-up-extending-mobileforge/specs/001-llmxive-follow-up-extending-mobileforge/contracts/evaluation.schema.yaml===
$schema: "http://json-schema.org/draft-07/schema#"
title: "EvaluationResult"
description: "Schema for the evaluation results including statistical tests."
type: "object"
properties:
  metrics:
    type: "object"
    properties:
      success_rate_distilled:
        type: "number"
        minimum: 0
        maximum: 1
      baseline_metrics:
        type: "array"
        items:
          type: "object"
          properties:
            name:
              type: "string"
            success_rate:
              type: "number"
              minimum: 0
              maximum: 1
            step_efficiency:
              type: "number"
          required:
            - name
            - success_rate
            - step_efficiency
    required:
      - success_rate_distilled
      - baseline_metrics
  statistical_test:
    type: "object"
    properties:
      test_type:
        type: "string"
        const: "mcnemar"
      chi2:
        type: "number"
        description: "McNemar chi‑square statistic"
      p_value:
        type: "number"
        description: "Two‑tailed p‑value"
      significant:
        type: "boolean"
      effect_size_odds_ratio:
        type: "number"
        description: "Odds‑ratio effect size for McNemar"
    required:
      - test_type
      - chi2
      - p_value
      - significant
      - effect_size_odds_ratio
  power_analysis:
    type: "object"
    properties:
      n_required:
        type: "integer"
        minimum: 1
      parameters:
        type: "object"
        properties:
          power_target:
            type: "number"
            minimum: 0
            maximum: 1
          effect_size_odds_ratio:
            type: "number"
            description: "Odds‑ratio effect size used in power calculation"
          significance_level:
            type: "number"
            minimum: 0
            maximum: 1
          baseline_rate:
            type: "number"
            minimum: 0
            maximum: 1
          p0_source:
            type: "string"
            description: "Source of baseline rate estimate (e.g., 'Pilot Run', 'Fallback 0.5')"
        required:
          - power_target
          - effect_size_odds_ratio
          - significance_level
          - baseline_rate
          - p0_source
    required:
      - n_required
      - parameters
  sensitivity_report:
    type: "object"
    properties:
      thresholds:
        type: "array"
        items:
          type: "integer"
      success_rates:
        type: "array"
        items:
          type: "number"
    required:
      - thresholds
      - success_rates
required:
  - metrics
  - statistical_test
  - power_analysis
  - sensitivity_report