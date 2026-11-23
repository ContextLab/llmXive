# Implementation Plan: Dream-State Learning: Implementing REM-like Consolidation in Language Models

**Branch**: `001-dream-state-learning-rem-consolidation` | **Date**: 2026-10-19 | **Spec**: `spec.md`  
**Input**: Feature specification from `specs/001-dream-state-learning-rem-consolidation/spec.md`

## Summary
Implement an oscillatory training pipeline for a small transformer (DistilBERT‑base‑uncased) that alternates **wake** (standard supervised fine‑tuning on GLUE‑MNLI) and **dream** (generative replay with masked reconstruction) phases with a **4:1 wake/dream ratio** and a **20‑step warm‑up**.  

*Primary hypothesis* is tested with a **fixed temperature = 1.0**. A **temperature sweep** `[0.5, 1.0, 1.5, 2.0]` is performed only as a **secondary, optional** analysis to assess sensitivity (FR‑006).  

Run a parallel continuous‑training baseline with identical **real‑token exposure** (including dummy wake steps when dream steps are skipped).  

Evaluate few‑shot generalization on GLUE‑QNLI, compute **relative accuracy improvement** (SC‑001) and a **paired two‑tailed t‑test** (SC‑002, SC‑005).  

All experiments execute on a **2‑CPU, ≤7 GB RAM GitHub Actions runner**, respecting a **hard memory cap of a few GB RSS** and a **wall‑clock limit of several hours** per full experiment (including optional ablations).  

The study is framed as a **pilot** (3 seeds, power ≈ 0.45 for d = 0.8); results are reported with effect sizes, confidence intervals, and explicit power caveats rather than definitive significance claims.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers>=4.40.0`, `datasets>=2.18.0`, `torch>=2.2.0` (CPU‑only), `accelerate>=0.28.0`, `scikit-learn>=1.4.0`, `scipy>=1.12.0`  
- **Target Platform**: Linux (`ubuntu-latest` GitHub Actions runner)  
- **Constraints**: CPU‑only execution, hard memory abort at 6.3 GB RSS, wall‑clock limit 5 h per full experiment (including optional ablations).  

## Constitution Check
| Principle | Status | How Implemented |
|-----------|--------|-----------------|
| I. Reproducibility | PASS | Random seeds pinned in `code/config.py`; `requirements.txt` pins exact versions; datasets fetched via deterministic `datasets.load_dataset` calls. |
| II. Verified Accuracy | PASS | All citations limited to verified GLUE dataset loaders (see `research.md`). |
| III. Data Hygiene | PASS | Raw GLUE files stored under `data/raw/` with SHA‑256 checksums; all transformations write new files under `data/processed/`. |
| IV. Single Source of Truth | PASS | **All reported metrics (accuracy, reconstruction error, correlation, statistical tests) are stored exclusively in `data/results/experiment_summary.json`.** No other result files are used as source for figures or tables. |
| V. Versioning Discipline | PASS | Content hashes recorded in `state/projects/PROJ-589-dream-state-learning-implementing-rem-li/artifact_hashes.yaml` using `artifact_hashes.schema.yaml`. |
| VI. Oscillatory Training Protocol | PASS | Training loop enforces 4 wake : 1 dream ratio, 20‑step warm‑up, dummy wake steps when dream steps are skipped, and logs any deviation as an ablation variant. |
| VII. Few‑Shot Generalization Validation | PASS | Evaluation on GLUE‑QNLI (different task from MNLI) with 3 seeds; paired t‑test (α = 0.05) reported in `statistical_report_schema.yaml`. |

## Project Structure
```text
specs/001-dream-state-learning-rem-consolidation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── dream_sample_schema.schema.yaml
│   ├── experiment_result_schema.schema.yaml
│   ├── evaluation_result.schema.yaml
│   ├── statistical_report_schema.schema.yaml
│   ├── training_config.schema.yaml
│   ├── training_result.schema.yaml
│   ├── dream_event.schema.yaml
│   └── artifact_hashes.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

```text
projects/PROJ-589-dream-state-learning-implementing-rem-li/
├── code/
│   ├── __init__.py
│   ├── config.py                # hyper‑parameters, seeds, paths
│   ├── train.py                 # orchestrates wake/dream cycles (FR‑001, FR‑002, FR‑007)
│   ├── eval.py                  # few‑shot evaluation & stats (FR‑004, SC‑001, SC‑002)
│   ├── data_loader.py           # streaming GLUE download
│   └── utils/
│       ├── logging.py
│       ├── memory_monitor.py   # RSS check & abort (FR‑005)
│       └── stats.py            # entropy, perplexity, reconstruction error, correlation
├── data/
│   ├── raw/                     # GLUE parquet files
│   └── processed/               # masked samples, eval subsets, reconstruction_error.json
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── docs/
    └── architecture.md
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| Oscillatory Loop | Core hypothesis (FR‑001, SC‑001) | Continuous training alone cannot isolate consolidation effect. |
| Memory Monitor | Guarantees CPU‑tier feasibility (FR‑005) | Relying on CI timeout would cause abrupt OOM failures. |
| Warm‑up Protocol | Prevents early garbage generation (Edge Case) | Skipping warm‑up leads to garbage pseudo‑samples and training collapse. |
| Reconstruction Error Tracking | Provides construct validity for “consolidation” (FR‑002) | Omitting it leaves the construct unvalidated. |
| Paired‑seed design | Enables statistical rigor (SC‑002) | Single‑seed runs lack effect‑size estimation. |
| Temperature Sweep (secondary) | Addresses FR‑006 while avoiding confound in primary hypothesis. |
| Token‑balance handling | Ensures token‑exposure parity when dream steps are skipped (addresses methodology‑fc66a14b). |
| Abort handling | Prevents biased comparison if one run aborts (methodology‑fe6e93e4). |

## Implementation Phases
| Phase | Tasks (mapped to FR/SC) |
|-------|--------------------------|
| **0 – Dataset Verification** | Verify GLUE MNLI & QNLI availability (SC‑001, SC‑003, SC‑004). |
| **1 – Schema & Contract Definition** | Create JSON‑Schema files: `dataset.schema.yaml`, `dream_sample_schema.schema.yaml`, `dream_event.schema.yaml`, `training_config.schema.yaml`, `training_result.schema.yaml`, `evaluation_result.schema.yaml`, `experiment_result_schema.schema.yaml`, `statistical_report_schema.schema.yaml`, `artifact_hashes.schema.yaml`. |
| **2 – Core Training Engine** | Implement wake/dream alternation (FR‑001, FR‑007) **and** pseudo‑sample generation with temperature and random masking (FR‑002). Log entropy, perplexity, and reconstruction error for each dream step (construct validity). If entropy < 0.5 bits or perplexity > 50, retry up to 3 times; on failure, **skip dream step and insert a dummy wake step** to keep token exposure equal (addresses methodology‑fc66a14b). |
| **3 – Baseline Engine** | Continuous training with identical **real‑token** exposure; when experimental run inserts dummy wake steps (due to skipped dreams), baseline adds matching wake steps to preserve token parity (methodology‑fc66a14b). |
| **4 – Sensitivity Sweep (Secondary)** | Loop over temperatures `[0.5, 1.0, 1.5, 2.0]` **only if** remaining compute budget permits after primary runs. Results are logged as ablation variants, not used for the primary hypothesis. |
| **5 – Evaluation & Statistics** | Run few‑shot QNLI evaluation (FR‑004). Compute **relative accuracy improvement** against baseline (SC‑001) and a **paired two‑tailed t‑test** (`scipy.stats.ttest_rel`) (SC‑002, SC‑005). Also compute **Pearson correlation** between average reconstruction error (logged in Phase 2) and final accuracy (construct validation). All output validated against `evaluation_result.schema.yaml` and `statistical_report_schema.yaml`. |
| **6 – Resource Auditing** | Record peak RSS, wall‑clock; abort if >6.3 GB or >5 h (FR‑005, SC‑003, SC‑004). Aborted runs are flagged, excluded from primary analysis, and automatically re‑run with reduced step count (methodology‑fe6e93e4). |
| **7 – Artifact Hashing & Versioning** | Generate SHA‑256 hashes for all result files using `artifact_hashes.schema.yaml`. |
| **8 – Documentation & Quickstart** | Produce `quickstart.md` and architecture notes. |

Each phase produces a deterministic artifact (e.g., `data/results/experiment_summary.json` validated against its schema), ensuring verifiable outputs for the reviewer.

---



## projects/PROJ-589-dream-state-learning-implementing-rem-li/specs/001-dream-state-learning-implementing-rem-li/research.md
# Research: Dream-State Learning: Implementing REM-like Consolidation in Language Models

## Executive Summary
We investigate whether an oscillatory **wake/dream** training schedule—mirroring REM‑like consolidation—improves few‑shot generalization of a small transformer (DistilBERT‑base‑uncased) relative to continuous supervised fine‑tuning. Consolidation is operationalized as the model’s ability to **reconstruct masked, self‑generated pseudo‑samples** (a denoising auto‑encoder objective). The study is a **pilot**: 3 random seeds for the primary analysis (temperature = 1.0) and an optional temperature sweep as a secondary ablation, each run both experimental (wake/dream) and baseline (continuous) regimes. All experiments run on a 2‑CPU, ≤7 GB RAM GitHub Actions runner.

## Theoretical Background & Logical Depth
- **Digital Consolidation**: In biology, REM sleep stabilizes synaptic changes via replay. Here, the model **replays its own predictions**, then learns to reconstruct the original inputs, creating a closed loop of “prediction → noisy reconstruction → correction.” This loop adds *logical depth*: the model must internalize a representation that survives self‑generated perturbations, akin to synaptic stabilization.
- **Hypothesis**: The wake/dream loop yields a **lower reconstruction error** after each cycle, which correlates with improved downstream few‑shot accuracy on an unseen task.

## Dataset Strategy
Verified GLUE datasets are accessed via the HuggingFace `datasets` library (programmatic loading; no direct verified URLs required).

| Role | GLUE Subset | Loader | Verified Source |
|------|-------------|--------|-----------------|
| Wake‑phase training | **MNLI** (train split) | `datasets.load_dataset('glue', 'mnli', split='train', streaming=True)` | HuggingFace `datasets` library |
| Few‑shot evaluation | **QNLI** (validation split) | `datasets.load_dataset('glue', 'qnli', split='validation', streaming=True)` | HuggingFace `datasets` library |

*Streaming* is employed when the full split exceeds RAM; otherwise a deterministic random sample (≤2000 examples) is cached under `data/raw/`. No gated datasets are required.

## Methodology

### Experimental Design
| Variable | Values |
|----------|--------|
| **Training Regime** | `wake_dream` (4 wake : 1 dream) vs. `baseline` (continuous) |
| **Warm‑up Steps** | 20 wake‑only steps before first dream |
| **Dream Temperature** | Fixed **1.0** for primary analysis; optional sweep `[0.5, 1.0, 1.5, 2.0]` as secondary |
| **Random Seeds** | 0, 1, 2 (primary); 3, 4 optional if resources allow |
| **Total Gradient Steps** | 100 (fixed across all runs) |
| **Batch Size** | 4 (CPU‑friendly) |
| **Memory Cap** | 6.3 GB RSS (hard abort) |
| **Wall‑clock Cap** | 5 h per full experiment |

### Training Loop (high‑level pseudocode)
```
for step in range(total_steps):
    if step < warmup_steps:
        run_wake_step()
    elif (step - warmup_steps) % (wake_steps + dream_steps) < wake_steps:
        run_wake_step()
    else:
        pseudo = generate_pseudo_sample(temperature=current_temp)
        if entropy(pseudo) < 0.5:
            retry up to 3 times; if still low → skip dream step (log)
        if perplexity(pseudo) > 50:
            skip dream step (log)
        if dream step skipped:
            run_dummy_wake_step()   # preserves real‑token exposure
        else:
            run_dream_step(pseudo)   # masked reconstruction + distillation loss
        # Record reconstruction error for later correlation analysis
```
All loss values are logged; dream‑step skips are recorded in `dream_event.schema.yaml`. When a dream step is skipped, a **dummy wake step** is inserted so that the **total number of real tokens** processed matches the baseline (addresses token‑parity requirement).

### Baseline
Identical total steps and real‑token count; dream steps are replaced by additional wake steps. If the experimental run inserts dummy wake steps (due to skipped dreams), the baseline adds matching wake steps to preserve token parity.

### Evaluation
- After training, load the final checkpoint, evaluate on **QNLI** (few‑shot: 5 examples per class) and compute **accuracy**.
- Repeat for each seed and regime.
- Perform a **paired two‑tailed t‑test** (`scipy.stats.ttest_rel`) across the 3 seed pairs.
- Compute **Cohen’s d** for effect size.
- Additionally, compute the **Pearson correlation** between average reconstruction error (logged during training) and final accuracy to validate the consolidation construct.
- Record **relative accuracy improvement** (experimental – baseline) as required by SC‑001.

### Statistical Rigor
- **Multiple Comparisons**: Only one evaluation set is used for the primary hypothesis; no correction needed. The temperature sweep is a secondary analysis and reported separately.
- **Power**: With `n = 3` seed pairs, power to detect `d = 0.8` is ≈ 0.45. The study is explicitly framed as a **pilot**; we report effect size, 95 % confidence interval, and note the limited power rather than asserting definitive significance.
- **Assumptions**: Observational (no randomization beyond seed); claims limited to *associational* improvements.

## Edge‑Case Handling
1. **Low‑Entropy Collapse** – average token entropy < 0.5 bits ⇒ retry up to 3 times; if still low, discard batch and **skip dream step**, inserting a dummy wake step to keep token balance.
2. **High Perplexity** – perplexity > 50 ⇒ skip dream step, log reason, insert dummy wake step.
3. **Insufficient Evaluation Samples** – if the few‑shot QNLI subset contains < 5 examples for a seed, the paired t‑test is omitted; the result file will contain `"note": "insufficient power"` per `statistical_report_schema.yaml`.
4. **Resource Overrun** – `memory_monitor.py` aborts with status `oom_abort`; `train.py` tracks wall‑clock and aborts with `timeout` status if > 5 h. Aborted runs are **flagged and excluded** from the primary analysis; they may be automatically re‑run with a reduced step count.

## Decision Rationale
| Decision | Reason |
|----------|--------|
| **DistilBERT‑base‑uncased** | ≤ 100 M params, fits CPU memory budget, matches FR‑001 requirement for a “small” model. |
| **4:1 Wake/Dream Ratio** | Implements the *theta‑like* oscillation mandated by Constitution Principle VI. |
| **20‑step Warm‑up** | Prevents early garbage generation (Edge Case). |
| **Fixed Temperature = 1.0 for Primary Analysis** | Avoids confounding temperature with the core hypothesis (methodology‑320f1153). |
| **Temperature Sweep as Secondary** | Satisfies FR‑006 while keeping primary analysis clean. |
| **3 Seeds (Pilot)** | Keeps total compute within the 5 h wall‑clock budget (methodology‑d17abfbb). |
| **Token‑balance Handling** | Guarantees identical real‑token exposure despite dream‑step skips (methodology‑fc66a14b). |
| **Abort Handling & Re‑run** | Prevents biased comparisons if one regime aborts early (methodology‑fe6e93e4). |
| **Reconstruction Error Correlation** | Provides construct validity for “consolidation” (methodology‑c0a928d2). |
| **Pilot framing** | Honest acknowledgement of limited power (methodology‑83598387). |

---



## projects/PROJ-589-dream-state-learning-implementing-rem-li/specs/001-dream-state-learning-implementing-rem-li/data-model.md
# Data Model: Dream-State Learning

## Overview
Defines all persistent artifacts produced by the experiment, each validated against a JSON Schema in `contracts/`. All files are immutable once written; new derivations receive fresh filenames and corresponding hashes.

## Data Flow
1. **Raw Ingestion** – GLUE parquet files (`data/raw/`) fetched via the HuggingFace `datasets` library.  
2. **Pre‑processing** – No modification of raw files; masked pseudo‑samples generated on‑the‑fly during training and logged to `data/processed/dream_samples/`.  
3. **Training Artifacts** – Checkpoints (`checkpoints/`) and per‑step logs (`logs/`).  
4. **Evaluation Results** – JSON files under `data/results/` adhering to `evaluation_result.schema.yaml`.  
5. **Aggregated Experiment Summary** – **All** reported metrics (final accuracy, reconstruction error, correlation, relative improvement, paired‑test statistics, resource usage) are stored in a single file `data/results/experiment_summary.json` adhering to `experiment_result_schema.schema.yaml` **and** `statistical_report_schema.yaml`.  
6. **Versioning** – SHA‑256 hashes recorded in `state/projects/PROJ-589-dream-state-learning-implementing-rem-li/artifact_hashes.yaml` using `artifact_hashes.schema.yaml`.

## Schemas (see `contracts/`)

| Schema File | Purpose |
|-------------|---------|
| `dataset.schema.yaml` | Raw record from the GLUE suite used for wake‑phase training or evaluation. |
| `dream_sample_schema.schema.yaml` | Pseudo‑sample generated during a dream step (entropy, perplexity, masking). |
| `dream_event.schema.yaml` | Diagnostics of each dream‑step execution (entropy, retries, discard flag). |
| `training_config.schema.yaml` | Hyper‑parameter configuration for a run. |
| `training_result.schema.yaml` | Aggregated run metrics (accuracy, memory, wall‑clock, status). |
| `evaluation_result.schema.yaml` | Single evaluation run output (accuracy, loss, resource usage). |
| `experiment_result_schema.schema.yaml` | Summary per seed & regime (final accuracy, steps, memory, reconstruction error, correlation, relative improvement). |
| `statistical_report_schema.schema.yaml` | Paired t‑test outcome, effect size, power estimate, notes. |
| `artifact_hashes.schema.yaml` | Content‑hash tracking for reproducibility. |

## Data Hygiene Rules
1. **Immutability** – Raw files never overwritten; derived files receive new names (`*_v{hash}.json`).  
2. **Checksums** – Every file in `data/raw/` has a `.sha256` side‑car; verification occurs at start of each CI run.  
3. **PII** – GLUE is pre‑scrubbed; no additional PII may be introduced.  
4. **Logging** – All wake/dream transitions, entropy, reconstruction error, and memory metrics logged in structured JSON (`logs/`).  
5. **Schema Validation** – `tests/contract/` runs `jsonschema` validation on every artifact before the next pipeline stage.  
6. **Versioning** – After each artifact is written, its SHA‑256 is recorded in `state/projects/PROJ-589-dream-state-learning-implementing-rem-li/artifact_hashes.yaml` using `artifact_hashes.schema.yaml`.  

## Single Source of Truth (SSoT) Mapping
- **Metrics** (accuracy, loss, peak memory, reconstruction error, correlation, relative improvement, paired‑test statistics) → **solely** in `data/results/experiment_summary.json`.  
- **Figures** (training loss curves, reconstruction error vs. accuracy scatter, statistical summary) → generated from the data in `experiment_summary.json`.  
- **Logs** → `logs/` (referenced by the JSON summary for reproducibility but not used as source for reported statistics).

---



## projects/PROJ-589-dream-state-learning-implementing-rem-li/specs/001-dream-state-learning-implementing-rem-li/quickstart.md
# Quickstart: Dream-State Learning

## Prerequisites
- Python 3.11 or newer  
- Git  
- A Linux environment (local VM or GitHub Actions runner) with **≥ 8 GB RAM** (allows headroom for the 7 GB limit)  

## Installation
```bash
# 1️⃣ Clone the repository
git clone <repository-url>
cd projects/PROJ-589-dream-state-learning-implementing-rem-li

# 2️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate

# 3️⃣ Install pinned dependencies
pip install -r code/requirements.txt
```

## Step‑by‑Step Run

### 1. Download GLUE data (once)
```bash
python code/data_loader.py --download
# Data will appear under data/raw/
```

### 2. Run a **debug** experiment (fast sanity check)
```bash
python code/train.py \
  --seed 42 \
  --total_steps 20 \
  --warmup_steps 5 \
  --ratio 4:1 \
  --mode debug
```
*Expected*: Logs show wake → dream transitions, entropy checks, and a checkpoint saved to `checkpoints/debug.pt`.

### 3. Run the **pilot** experiment (primary analysis)
```bash
python code/train.py \
  --seeds 0,1,2 \
  --total_steps 100 \
  --warmup_steps 20 \
  --ratio 4:1 \
  --temp 1.0 \
  --baseline
```
- This launches **3** experimental runs (wake/dream) and **3** baseline runs, each respecting the memory/timeout caps.  
- Checkpoints are stored under `checkpoints/seed_{N}_{regime}.pt`.

### 4. (Optional) Run the **temperature sweep** ablation (if compute budget permits)
```bash
python code/train.py \
  --seeds 3,4 \
  --total_steps 100 \
  --warmup_steps 20 \
  --ratio 4:1 \
  --temp_sweep 0.5 1.0 1.5 2.0 \
  --baseline
```
- Executes up to **2** additional seeds **only if** remaining compute budget permits.  
- Results are logged as separate ablation variants, not used for the primary hypothesis.

### 5. Evaluate & compute statistics
```bash
python code/eval.py --results_dir data/results/
```
*Output*: `data/results/experiment_summary.json` containing:
- Final accuracies for each seed & regime  
- Relative accuracy improvement (wake/dream vs. baseline) (SC‑001)  
- Reconstruction error averages and Pearson correlation with accuracy (construct validation)  
- Paired t‑test, Cohen’s d, power estimate, and any notes about insufficient power (SC‑002, SC‑005).  

### 6. Verify Artifacts
```bash
pytest -k contract   # runs JSON‑schema validation on all result files
```
All artifacts must validate against their respective schemas in `contracts/`.

## Troubleshooting
| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| **OOM / MemoryError** | Batch size too large or temperature causing long generations. | Reduce `--batch_size` in `code/config.py` or switch to a lower temperature. |
| **Dream step skipped** | Entropy < 0.5 bits or perplexity > 50. | This is expected for low‑quality generations; the run will continue with a dummy wake step to keep token exposure equal. |
| **Timeout (>5 h)** | Too many seeds or steps. | Reduce `--total_steps` or run a subset of seeds (as shown above). |
| **Missing `experiment_summary.json`** | Evaluation script failed due to < 5 evaluation samples. | Verify that `data/raw/` contains at least 5 QNLI validation examples per seed; otherwise the report will contain `"note": "insufficient power"` as designed. |

## Verification Checklist
1. Run `debug` mode – confirm `logs/debug.log` contains `"phase": "wake"` and `"phase": "dream"` entries.  
2. Ensure a checkpoint file (`checkpoints/debug.pt`) loads without error (`torch.load`).  
3. After pilot run, verify that `data/results/experiment_summary.json` validates against its schema (`pytest -k contract`).  

---



## projects/PROJ-589-dream-state-learning-implementing-rem-li/specs/001-dream-state-learning-implementing-rem-li/contracts/artifact_hashes.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Artifact Hash Record"
description: "Mapping from an artifact identifier to its SHA‑256 hash for reproducibility."
type: "object"
properties:
  artifact_id:
    type: "string"
    description: "Unique identifier (e.g., 'experiment_result_seed_0')."
  hash:
    type: "string"
    description: "SHA‑256 hexadecimal digest of the artifact content."
  linked_result:
    type: "string"
    description: "Filesystem path to the artifact (relative to project root)."
  timestamp:
    type: "string"
    format: "date-time"
    description: "ISO‑8601 timestamp of when the hash was recorded."
required:
  - "artifact_id"
  - "hash"
  - "linked_result"
  - "timestamp"
additionalProperties: false