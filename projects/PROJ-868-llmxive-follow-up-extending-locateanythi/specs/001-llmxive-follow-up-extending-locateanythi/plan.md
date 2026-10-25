# Implementation Plan: llmXive follow‑up – extending “LocateAnything: Fast and High‑Quality Vision‑Language Grounding with P”

**Branch**: `001-llmxive-follow-up` | **Date**: 2026‑10‑24 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-llmxive-follow-up/spec.md`

## Summary
The plan quantifies how limiting the attention window of a LocateAnything‑style vision‑language grounding model degrades geometric coherence (mean Intersection‑over‑Union, mIoU) on dense scenes, identifies the sparsity “tipping point” where dense‑scene mIoU first falls below 80 %, optionally runs a ±8‑patch sensitivity sweep, and explains failure modes with gradient‑based attribution. All steps are fully reproducible on the free‑tier GitHub Actions CPU runner (2 CPU cores, ≤ 7 GB RAM, ≤ 6 h wall‑clock).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `torchvision`, `transformers`, `datasets`, `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `opencv-python`, `captum` (for Grad‑CAM), `tqdm`  
- **Storage**: Files under `data/` (raw downloads, processed subsets, intermediate parquet/CSV, prediction JSONs, figures)  
- **Testing**: `pytest` + contract validation (`contracts/inference_results.schema.yaml`)  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM, no GPU)  
- **Constraints**: CPU‑only (`torch.set_num_threads(2)`) and memory‑mapped loading; total runtime ≤ 6 h per CI job  

## Constitution Check

| Principle | How the plan satisfies it |
|-----------|--------------------------|
| **I. Reproducibility** | All random seeds are fixed (`numpy`, `torch`, `random`). External datasets are fetched via the Hugging Face `datasets` library from the exact URLs listed in the “Verified datasets” block; no manual steps. |
| **II. Verified Accuracy** | No new citations are added; every dataset URL is pre‑verified. |
| **III. Data Hygiene** | Raw files are checksum‑verified (SHA‑256) immediately after download; transformations write new files with provenance logs. |
| **IV. Single Source of Truth** | The master inference table `data/results/master_inference.parquet` is the sole source for every downstream statistic and figure. |
| **V. Versioning Discipline** | All artifacts are stored under `data/` with content‑hash filenames; the platform’s state file will be updated automatically. |
| **VI. Attention Sparsity and Geometric Coherence** | Dense‑scene definition, tipping‑point definition, and mIoU metric are implemented exactly as required. |
| **VII. Resource‑Constrained Validation** | All code runs with `torch.set_num_threads(2)` and memory‑mapped dataset loading; attribution runs also respect the CPU constraint. |

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
│   ├── download.py          # robust download + 3‑retry + checksum verification (uses HF datasets where possible)
│   ├── preprocess.py        # dense‑scene filtering, ambiguous‑box exclusion, streaming parquet processing
│   └── sparsity.py          # `SparsityConfig(num_patches)` with `get_mask()` API
├── model/
│   ├── locateany.py         # wrapper `LocateAnythingSparsityWrapper(sparsity_config)`; imports torch
│   └── attribution.py       # Captum‑based Grad‑CAM utilities
├── analysis/
│   ├── metrics.py           # mIoU, latency, exclusion flags
│   ├── stats.py             # ANOVA/Friedman, power analysis, Jonckheere‑Terpstra, Kendall’s τ, tipping‑point logic
│   └── reporting.py         # tables & figures generation
└── cli/
    └── run_experiment.py    # end‑to‑end driver (configurable phases, robust arg parsing, deterministic ordering)
tests/
├── contract/
│   └── test_contracts.py
├── unit/
│   ├── test_sparsity.py    # checks constructor signature and mask correctness
│   └── test_locateany.py   # imports torch, checks thread limit, forward‑pass API
└── integration/
    └── test_full_pipeline.py
```

## Phase‑by‑Phase Roadmap (covers every FR and SC)

| Phase | Description | FR(s) Covered | SC(s) Covered | Key Outputs |
|------|-------------|---------------|---------------|-------------|
| **0 – Data Acquisition & Checksum** | Download VRSBench validation split, COCO 2017 validation split, and LocateAnything checkpoint metadata using the exact URLs from the Verified Datasets block. Compute SHA‑256 checksums and abort on mismatch. Implements a three‑retry mechanism for robustness. | – | – | `data/raw/vrsbench.parquet`, `data/raw/coco_val.parquet`, `data/raw/locateanything_metadata.txt` |
| **1 – Pre‑processing** | (a) Load datasets with `datasets.load_dataset(..., mmap=True)`. (b) Compute pairwise IoU per image. (c) Flag **dense‑scene** images (> 5 overlapping pairs, IoU > 0.10). (d) Flag **low‑density** images (≤ 5 overlapping pairs) – mIoU still computed, ambiguity‑resolution metric recorded as “N/A”. (e) Exclude ambiguous boxes (zero‑area or IoU > 0.95). (f) Record exclusion proportion (must be ≤ 5 %). (g) Persist dense and non‑dense subsets as streaming parquet files (process in chunks to stay within RAM). | FR‑003, FR‑007, FR‑008 | SC‑006, SC‑007 | `data/processed/dense_subset.parquet`, `data/processed/non_dense.parquet`, `data/processed/exclusion_log.json` |
| **2 – Model & Sparsity Knob** | Load LocateAnything checkpoint (FP32) on CPU. Implement `SparsityConfig(num_patches)` that stores the patch count and provides a **no‑argument** `get_mask()` returning a binary mask of shape `[num_tokens]`. Supported values: `0` (global), `64`, `32`, `16`, optional `1`. The mask logic automatically yields a full‑global mask when the requested window covers the entire token grid. Enforce FR‑001 and FR‑006. | FR‑001, FR‑006 | – | `src/model/sparsity.py` |
| **3 – Inference & mIoU Calculation** | For each sparsity configuration **global, 64, 32, 16, optional 1**: <br>  a. **Randomize** the order of configurations using a fixed seed (`np.random.RandomState(42)`) to avoid warm‑up or caching bias. <br>  b. Reset model state. <br>  c. Apply mask via `LocateAnythingSparsityWrapper(sparsity_config)`. <br>  d. Run inference on both dense and non‑dense subsets (batch = 8). <br>  e. Save per‑image prediction JSON under `data/predictions/<image_id>_<window>.json`. <br>  f. Compute per‑image **mIoU**, latency, and flag `excluded`. <br>  g. Append a row to `inference_<window>.parquet`. | FR‑002, FR‑009 (optional) | SC‑001, SC‑003, SC‑005 | `data/results/inference_32.parquet`, `data/predictions/*.json` |
| **4 – Statistical Analysis** | a. Mixed two‑way ANOVA (within‑subject: sparsity; between‑subject: density). Test normality (Shapiro‑Wilk); if any cell fails (p < 0.05) fall back to **Friedman aligned‑rank test** (FR‑004). <br>b. Power analysis (effect size f = 0.25, α = 0.05, within‑subject r = 0.5) using `statsmodels`; report > 80 % power or note limitation. <br>c. **Trend analysis**: perform a **Jonckheere‑Terpstra** test for ordered sparsity levels against mIoU (primary SC‑003). Additionally compute **Kendall’s τ** as an ordinal‑compatible correlation coefficient and report its value. This respects the categorical nature of the sparsity predictor while still providing a correlation‑type metric. | FR‑004 | SC‑002, SC‑003 | `data/analysis/anova_results.json`, `data/analysis/trend_test.json`, `data/analysis/power_report.txt` |
| **5 – Tipping‑Point Detection & ±8‑Patch Sweep** | Identify the smallest window where dense‑scene **mean** mIoU < 0.80 (FR‑010). If such a window exists and > 1, run a **±8‑patch sweep** (clamped to 1‑64) around it, re‑run inference, and record the extra mIoU values (FR‑011). Optional 1‑patch run executed only when `--run-one-patch` flag present (FR‑009). | FR‑010, FR‑011, FR‑009 | SC‑001 | `data/analysis/tipping_point.json`, `data/analysis/sweep_results.parquet` |
| **6 – Attribution on Failure / Success Cases** | a. Hold‑out 200 dense images (seed = 0) **before** any tipping‑point computation (100 failure candidates, 100 success candidates). <br>b. After tipping point is known, select from the hold‑out set: failure images where the tipping‑point window yields mIoU < 0.80, success images where global attention yields mIoU ≥ 0.80. <br>c. Run Captum‑based Grad‑CAM on the final convolutional layer; generate heatmaps. <br>d. Compute **global‑context activation proportion** for each image; store in inference parquet. <br>e. Summarize absolute difference between failure and success groups (SC‑004). | FR‑005, FR‑003 (selection) | SC‑004 | `data/attribution/failure_<id>.png`, `data/attribution/success_<id>.png`, `data/analysis/attribution_summary.json` |
| **7 – Reporting & Artifact Generation** | **7‑a. Consolidation**: Concatenate all `inference_*.parquet` files into a single `master_inference.parquet` (addresses plan_consistency‑fb7470e4). <br>**7‑b.** Assemble: <br>  - Degradation curve (Figure 1). <br>  - ANOVA/Friedman table (Table 1). <br>  - Trend test results (Table 2). <br>  - Tipping‑point table (Table 3). <br>  - Attribution collage (Figure 2). <br>  - Latency bar chart (Figure 3). <br>All tables/figures draw directly from `data/results/master_inference.parquet` to satisfy the SSoT requirement. Write `docs/results.md` for downstream paper pipeline. | All | SC‑001 – SC‑007 | `docs/results.md`, `figures/*.png`, `tables/*.csv` |
| **8 – Contract Validation** | Run `pytest -q tests/contract/` against `contracts/inference_results.schema.yaml`. CI fails if any result file violates the schema. | – | – | CI pass/fail |

All phases respect the data dependency order (download → preprocess → model → inference → analysis → reporting) and stay within the CPU‑only compute budget; no GPU escape hatch is required.
