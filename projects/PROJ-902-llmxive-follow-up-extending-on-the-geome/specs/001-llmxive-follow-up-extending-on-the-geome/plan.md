# Implementation Plan: llmXive follow-up – extending “On the Geometry of On‑Policy Distillation”

**Branch**: `001-llmxive-geometry-extension` | **Date**: 2026‑08‑11 | **Spec**: `specs/001-llmxive-geometry-extension/spec.md`  
**Input**: Feature specification from `/specs/001-llmxive-geometry-extension/spec.md`

## Summary
The project must (1) download and verify the GSM8K dataset, (2) run a full‑parameter On‑Policy Distillation (OPD) baseline on a **TinyLlama‑430M** model using **8‑bit CPU‑compatible quantization**, (3) derive a low‑rank subspace mask from **10** independent “mask‑derivation” seeds using layer‑wise randomized SVD, (4) train **Frozen‑Subspace OPD**, **Frozen‑Subspace SFT**, and **Random‑Mask SFT** models under the derived mask, (5) log detailed loss‑landscape metrics (per‑epoch loss, ΔL, plateau epoch), (6) conduct power analyses, equivalence (TOST) and difference (paired t‑test) statistical tests (with normality diagnostics and non‑parametric fall‑backs), (7) enforce all limits on a free‑tier GitHub Actions runner, and (8) produce a single authoritative `state.yaml` artifact validated against **both** `contracts/experiment.schema.yaml` **and** `contracts/experiment_results.schema.yaml`.

All functional requirements (FR‑001 → FR‑021) and success criteria (SC‑001 → SC‑006) are addressed by the phases below.

## Technical Context
| Item | Detail |
|------|--------|
| **Language/Version** | Python 3.11 |
| **Primary Dependencies** | `datasets==2.19.0`, `torch==2.3.0`, `bitsandbytes==0.43.1` (8‑bit CPU quantization), `scipy==1.13.0`, `statsmodels==0.14.2`, `pyyaml==6.0.2`, `tqdm`, `numpy`, `pandas` |
| **Storage** | Filesystem‑based `data/` and `results/` directories (no DB) |
| **Testing** | `pytest`, `jsonschema` for contract validation |
| **Target Platform** | Linux (Ubuntu‑latest) GitHub Actions runner (2 CPU cores, ~7 GB RAM, ~ modest‑size storage disk) |
| **Constraints** | CPU‑only execution; bitsandbytes 8‑bit works on CPU without CUDA. |
| **Scale/Scope** | **30** evaluation seeds per condition, split into **2** CI jobs of **≤ 15** seeds each; **2** epochs per run; model TinyLlama‑large (≈ several hundred M parameters). |

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | All random seeds are listed in `src/config.py`; dataset download is deterministic; CI matrix enumerates every condition and seed. |
| **II. Verified Accuracy** | Citations (He 2023, Halko 2011) are pre‑validated; dataset URLs are taken from the verified block. |
| **III. Data Hygiene** | `data/checksums.txt` stores SHA‑256 hashes; `src/data/download_gsm8k.py` validates them; no in‑place mutation. |
| **IV. Single Source of Truth** | All metrics, figures, and tables are written to `state.yaml`; contracts enforce that every downstream artifact derives from it. |
| **V. Versioning Discipline** | `state.yaml` includes a content hash; any change triggers CI re‑run; `requirements.txt` pins exact versions. |
| **VI. Geometric Subspace Validation** | Implements paired‑seed TOST equivalence (OPD) and paired t‑tests (SFT) with proper controls, including a random‑mask baseline. |
| **VII. Extreme Resource Constraints Verification** | RAM and wall‑clock are measured via `src/utils/logging.py`; CI fails any job exceeding 7 GB or 6 h. |

## Project Structure
```text
specs/001-llmxive-geometry-extension/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── experiment.schema.yaml
    ├── experiment_results.schema.yaml
    └── results.schema.yaml

src/
├── __init__.py
├── config.py                # seed lists, hyper‑params
├── data/
│   └── download_gsm8k.py
├── models/
│   └── tinyllama.py         # 8‑bit CPU quantized TinyLlama‑430M
├── training/
│   ├── opd.py               # full‑parameter OPD
│   ├── frozen_opd.py        # frozen‑subspace OPD
│   ├── sft_frozen.py        # frozen‑subspace SFT
│   └── sft_random.py        # random‑mask SFT
├── utils/
│   ├── logging.py           # RAM, wall‑time, loss logging
│   └── svd.py               # layer‑wise randomized SVD
└── analysis/
    └── stats.py             # power, TOST, t‑test, normality diagnostics

tests/
├── contract/
│   └── test_experiment_schema.py
└── unit/
    └── test_svd.py

data/
├── checksums.txt
└── gsm8k/                  # cached dataset files

results/
├── logs/
└── state.yaml

.github/
└── workflows/
    └── ci.yml

README.md
requirements.txt
pyproject.toml
.ruf​f.toml      # linting configuration

## Phases

### Phase 0 – Environment & Data Setup
1. Install dependencies from `requirements.txt`.
2. Run `python -m src.data.download_gsm8k` – downloads GSM8K via `datasets.load_dataset("openai/gsm8k")`, validates SHA‑256 against `data/checksums.txt`, caches locally.

### Phase 1 – Full‑Parameter OPD Baseline
* Load TinyLlama‑430M with bitsandbytes 8‑bit CPU quantization (`bnb.nn.Linear8bit`).
* Train for **2 epochs** (batch = 8) using KL‑divergence OPD loss.
* Record per‑epoch loss, ΔL, plateau epoch (ΔL < 0.001 for two consecutive epochs) via `src/utils/logging.py`.
* Save metrics to `results/opd_full_<seed>.json` (conforms to `experiment_results.schema.yaml`).

### Phase 2 – Subspace Mask Derivation
* For each of **10** mask‑derivation seeds, collect per‑layer weight deltas `Δθ` after every OPD update step in the first **2** epochs.
* Apply layer‑wise **randomized SVD** (`scipy.sparse.linalg.svds`) with streaming to keep peak RAM ≤ 7 GB.
* Increase target rank until cumulative variance ≥ 95 % (primary) and also evaluate at 90 % and 99 % for sensitivity (SC‑006).
* Build a **binary mask** (`mask.json`) where entries belonging to the selected singular vectors are `true`; all others `false`. Store mask under `results/mask.json`.

### Phase 3 – Frozen‑Subspace Training
* **Frozen‑Subspace OPD**: Apply mask, train OPD loss for 2 epochs, same hyper‑parameters as Phase 1.
* **Frozen‑Subspace SFT**: Same mask, train with standard cross‑entropy SFT loss.
* **Random‑Mask SFT**: Generate a random binary mask of identical dimensionality (seeded), train with SFT loss.

All runs use the **same data shuffling** and **identical initialization** across seeds. Each condition is executed in CI matrix jobs with **≤ 15 seeds** per job (splitting the required 30 seeds across two parallel jobs per condition).

### Phase 4 – Evaluation
* Evaluate each trained model on the **held‑out generalization subset** of GSM8K (stratified by difficulty, fixed seed). Compute **accuracy** (exact‑match) per seed.
* Log peak RAM (`peak_ram_gb`) and total wall‑clock (`wall_time_sec`) via `logging.py`.

### Phase 5 – Loss‑Landscape Logging (FR‑010)
* `src/utils/logging.py` writes a JSON‑lines file per run containing:
  * `loss_per_epoch` (list of loss values)
  * `delta_loss` (ΔL per epoch)
  * `plateau_epoch` (first epoch where ΔL < 0.001 for two consecutive epochs, or `null`)
* These fields are included in `state.yaml` and validated against `experiment_results.schema.yaml`.

### Phase 6 – Statistical Analysis
| Test | Comparison | Metric | Method |
|------|------------|--------|--------|
| **Normality diagnostics** | All seed‑wise accuracy differences | Shapiro‑Wilk, QQ‑plot | If p > 0.05 → assume normal; else use Wilcoxon signed‑rank. |
| **TOST Equivalence** | Frozen‑Subspace OPD vs. Full‑Parameter OPD (paired) | Accuracy difference | Paired TOST, Δ = 0.02, α = 0.05; fallback to Wilcoxon‑based equivalence if non‑normal. |
| **Paired t‑test / Wilcoxon** | Frozen‑Subspace SFT vs. Full‑Parameter OPD | Accuracy drop | Paired t‑test (α = 0.05) or Wilcoxon if normality fails. |
| **Paired t‑test / Wilcoxon** | Random‑Mask SFT vs. Full‑Parameter OPD | Accuracy drop | Same as above. |
| **Sensitivity sweep** | Across variance thresholds {0.90, 0.95, 0.99} | Accuracy difference | Apply Bonferroni correction (α/3). |

*Power analysis*: Prior to each test, compute required N using `statsmodels.stats.power.TTestPower` with effect size δ (0.02 for OPD, 0.03 for SFT), σ = 0.015 (He 2023), α = 0.05. With **N = 30** seeds, report achieved power; if power < 0.80 (the conventional target), flag the result as **“inconclusive”** (FR‑009, FR‑011, FR‑021).

### Phase 7 – CI & Reproducibility
* `.github/workflows/ci.yml` creates a matrix:
  - Conditions: `opd_full`, `frozen_opd`, `frozen_sft`, `random_sft`
  - Seeds per job: **≤ 15** (two jobs per condition to cover 30 seeds)
* Each job runs the full pipeline for its assigned seeds, validates the resulting JSON against **both** `contracts/experiment.schema.yaml` **and** `contracts/experiment_results.schema.yaml`. Failures abort the job.
* After all jobs finish, a aggregation step merges all per‑run JSON files into a single `state.yaml` artifact and uploads it.

## Compute Feasibility Decision
All heavy computations are **CPU‑first** using 8‑bit quantization on TinyLlama‑430M, which fits comfortably within 7 GB RAM. No GPU is required; the plan therefore stays on the free‑tier runner. If any step unexpectedly exceeds limits, CI will fail and the design will be revisited.

## Expected Deliverables
* `state.yaml` containing:
  * Per‑seed accuracies, RAM, time, loss metrics, plateau epoch.
  * Subspace mask summary (`k`, variance explained).
  * Power analysis results.
  * Statistical test outcomes (p‑values, decisions, “inconclusive” flags).
* Figures (accuracy distributions, loss trajectories, variance‑explained sweep) under `results/figures/`.
* Fully validated CI workflow and contract schemas.

--- 

## Constitution Check (re‑affirmed)

| Principle | Satisfaction |
|-----------|---------------|
| I. Reproducibility | Deterministic seeds, dataset download, CI matrix. |
| II. Verified Accuracy | Citations pre‑validated; dataset URLs from verified block. |
| III. Data Hygiene | Checksums, no in‑place mutation. |
| IV. Single Source of Truth | All metrics in `state.yaml`. |
| V. Versioning Discipline | Content hashes, pinned dependencies. |
| VI. Geometric Subspace Validation | Paired‑seed TOST and controls with random mask. |
| VII. Extreme Resource Constraints Verification | RAM & time logged; CI enforces limits. |