# Implementation Plan: llmXive follow-up: extending "LocateAnything: Fast and High-Quality Vision-Language Grounding with P"

**Branch**: `001-llmxive-follow-up` | **Date**: 2026-10-19 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-llmxive-follow-up/spec.md`

## Summary
The project must quantify how restricting the attention window of a LocateAnything‑style vision‑language grounding model degrades geometric coherence (mIoU) on dense scenes, locate the sparsity “tipping point” where mIoU falls below 0.80, and attribute failure modes to structural visual features. The plan proceeds through deterministic phases that each satisfy a functional requirement (FR‑001 – FR‑011) and produce the success criteria (SC‑001 – SC‑007).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `torchvision`, `transformers`, `datasets`, `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `opencv-python`, `grad-cam` (or `captum`), `tqdm`  
- **Storage**: Files under `data/` (raw downloads, filtered subsets, intermediate CSV/Parquet)  
- **Testing**: `pytest` + contract validation (see `contracts/`)  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM, no GPU)  
- **Constraints**: CPU‑only (`torch.set_num_threads(2)`), memory‑mapped loading, total wall‑clock ≤ 6 h per CI job  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| **I. Reproducibility** | All random seeds are fixed (`numpy.random.seed`, `torch.manual_seed`). External datasets are fetched from the exact URLs listed in the Verified Datasets block. |
| **II. Verified Accuracy** | No external citation is added beyond the verified dataset sources. |
| **III. Data Hygiene** | Raw files are checksum‑verified; every transformation writes a new file with a derived filename and a provenance log. |
| **IV. Single Source of Truth** | Every figure/table draws directly from the CSV/Parquet artifacts produced in Phase 2–5. |
| **V. Versioning Discipline** | All artifacts are stored under `data/` with content‑hash filenames; the `state/projects/...yaml` will be updated automatically by the platform. |
| **VI. Attention Sparsity and Geometric Coherence** | Dense‑scene definition, tipping‑point definition, and mIoU metric are implemented exactly as required. |
| **VII. Resource‑Constrained Validation** | All code runs with `torch.set_num_threads(2)` and memory‑mapped dataset loading; attribution runs on the same CPU constraints. |

## Project Structure
```text
specs/001-llmxive-follow-up/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── inference_results.schema.yaml
└── tasks.md          # generated later by /speckit-tasks
```

```text
src/
├── data/
│   ├── download.py          # dataset download & checksum
│   ├── preprocess.py        # dense‑scene filtering, ambiguous‑box exclusion
│   └── sparsity.py          # attention‑mask generator
├── model/
│   ├── locateany.py         # wrapper for LocateAnything model with sparsity knob
│   └── attribution.py       # Grad‑CAM / attention‑rollout utilities
├── analysis/
│   ├── metrics.py           # mIoU calculation, latency measurement
│   ├── stats.py             # ANOVA / Friedman, correlation, tipping‑point logic
│   └── reporting.py         # tables & figures generation
└── cli/
    └── run_experiment.py    # end‑to‑end driver (configurable phases)
tests/
├── contract/
│   └── test_contracts.py
└── unit/
    └── test_metrics.py
```

## Complexity Tracking
No constitution violations identified; all requirements are satisfied with the baseline pipeline.

## Phase‑by‑Phase Implementation Roadmap
| Phase | Description | FR(s) Covered | Key Outputs |
|-------|-------------|---------------|-------------|
| **0 – Data Acquisition & Checksum** | Download VRSBench validation split and **COCO 2017 validation split** using URLs in Verified Datasets; verify SHA‑256 checksums. The validation split, consisting of a modest number of images, comfortably fits within the available RAM budget. | – | `data/raw/vrsbench.parquet`, `data/raw/coco_val.parquet`, `data/raw/locateanything.csv` |
| **1 – Pre‑processing** | (a) Load datasets with `datasets.load_dataset(..., streaming=False, mmap=True)`. (b) Compute pairwise IoU per image; flag dense‑scene (>5 overlapping pairs, IoU > 0.10). (c) Exclude ambiguous boxes (zero‑area or IoU > 0.95). (d) Record exclusion proportion (must be ≤ 5 %). (e) Persist dense and non‑dense subsets as Parquet files. | FR‑003, FR‑007, FR‑008, SC‑006, SC‑007 | `data/processed/dense_subset.parquet`, `data/processed/non_dense.parquet`, `data/processed/exclusion_log.json` |
| **2 – Model & Sparsity Knob** | Load LocateAnything checkpoint (FP32) on CPU. Implement `SparsityConfig(window_size)` that masks all tokens outside a sliding window of `window_size` patches in each transformer layer. Supported values: `global`, `64`, `32`, `16`, optional `1`. | FR‑001, FR‑006 | `src/model/sparsity.py` (runtime API) |
| **3 – Inference & mIoU Computation** | For each sparsity config **(a)** **re‑load the model** (or reset its weights) to avoid any carry‑over state, **(b)** recompute the attention mask afresh, and **(c)** optionally **shuffle the order** of configurations to mitigate ordering bias. Run inference on both dense and non‑dense subsets (batch = 8). For every image: – Save the raw prediction JSON under `data/predictions/<image_id>_<window>.json`. – Compute per‑image mIoU and latency. – Write a row to `inference_{config}.parquet` that includes a `prediction_path` column pointing to the saved JSON and all other required fields. | FR‑002, FR‑009 (optional), SC‑001, SC‑003, SC‑005, **contract consistency** | `data/results/inference_{config}.parquet`, `data/predictions/*.json` |
| **4 – Statistical Analysis** | (a) Two‑way mixed ANOVA: within‑subject factor = sparsity, between‑subject factor = density. Check normality (Shapiro‑Wilk) for each cell; if any p < 0.05, fall back to **Friedman aligned‑rank test**. (b) **Power analysis**: script `src/analysis/power_analysis.py` computes power using `statsmodels.stats.power.FTestPower` with the full parameter set: effect size f = 0.25 (medium), within‑subject correlation r = 0.5, epsilon = 1 (sphericity), α = 0.05, 4 sparsity levels, and dense‑scene N is on the order of thousands. The script reports > 80 % power, which is recorded. (c) Pearson/Spearman correlation of window size vs. mIoU for each density group. Report the coefficients. | FR‑004, SC‑002, SC‑003 | `data/analysis/anova_results.json`, `data/analysis/correlation.csv` |
| **5 – Tipping‑Point Detection & Sensitivity Sweep** | Identify the smallest window where dense‑scene mIoU < 0.80 (FR‑010). If found and > 1, run a **±8‑patch sweep** (clamped to 1‑64) around that window, rerun inference, and record extra mIoU values (FR‑011). Include optional 1‑patch run if the user sets `--run-one-patch`. | FR‑010, FR‑011, SC‑001 | `data/analysis/tipping_point.json`, `data/analysis/sweep_results.parquet` |
| **6 – Attribution on Failure / Success Cases** | **Hold‑out set**: Prior to any tipping‑point computation, randomly sample 200 dense images (fixed seed) – 100 designated as “failure candidates” and 100 as “success candidates”. This set is **not** used for determining the tipping point. After the tipping point is identified, select from this hold‑out set: – **Failure images**: those where the sparsity window identified as the tipping point yields mIoU < 0.80. – **Success images**: those where global attention yields mIoU ≥ 0.80. Run Grad‑CAM (or attention rollout) to generate heatmaps. Compute **global‑context activation proportion** and **write this value back into the corresponding rows** of the inference results parquet (`global_context_activation_proportion` column). Summarize the absolute difference between failure and success groups. | FR‑005, FR‑003 (selection), SC‑004 | `data/attribution/failure_{id}.png`, `data/attribution/success_{id}.png`, `data/analysis/attribution_summary.json` |
| **7 – Reporting & Artifact Generation** | Assemble tables & figures: degradation curve, ANOVA summary, correlation plot, tipping‑point table, attribution heatmaps collage, latency bar chart. Write a concise `results.md` that can be imported by the paper pipeline. | All SCs | `docs/results.md`, `figures/*.png`, `tables/*.csv` |
| **8 – Contract Validation** | Run `pytest` against `contracts/inference_results.schema.yaml` to ensure all result files conform. | – | CI passes (`tests/contract/test_contracts.py`) |

Each phase respects data dependencies (download → preprocess → model → inference → analysis → reporting) and runs entirely on the free‑tier GitHub Actions CPU runner; no GPU is required.
