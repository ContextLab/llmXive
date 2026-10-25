# Implementation Plan: llmXive follow‑up – extending “LocateAnything: Fast and High‑Quality Vision‑Language Grounding with P”

**Branch**: `001-llmxive-follow-up` | **Date**: 2026‑10‑24 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-llmxive-follow-up/spec.md`

## Summary
The plan quantifies how limiting the attention window of a LocateAnything‑style vision‑language grounding model degrades geometric coherence (mean Intersection‑over‑Union, mIoU) on dense scenes, identifies the sparsity “tipping point” where dense‑scene mIoU first falls below 80 %, optionally runs a ±8‑patch sensitivity sweep, and explains failure modes with gradient‑based attribution. All steps are fully reproducible on the free‑tier GitHub Actions CPU runner (2 CPU cores, ≤ 7 GB RAM, ≤ 6 h wall‑clock). The pipeline uses a **distilled LocateAnything‑mini** checkpoint (≈1 GB) and processes at most **2 000 dense images** (sampled with a fixed seed) to stay within compute limits.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `torchvision`, `transformers`, `datasets`, `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `opencv-python`, `captum`, `tqdm`  
- **Storage**: Files under `data/` (raw downloads, processed subsets, intermediate parquet/CSV, prediction JSONs, figures)  
- **Testing**: `pytest` + contract validation (`contracts/inference_results.schema.yaml`)  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM, no GPU)  
- **Constraints**: CPU‑only (`torch.set_num_threads(2)`) and memory‑mapped loading; total runtime ≤ 6 h per CI job  

## Constitution Check

| Principle | How the plan satisfies it |
|-----------|--------------------------|
| **I. Reproducibility** | Fixed random seeds (`numpy`, `torch`, `random`). Datasets fetched via Hugging Face `datasets` from the exact URLs listed in the “Verified datasets” block; no manual steps. |
| **II. Verified Accuracy** | No new citations are added; every dataset URL is pre‑verified. |
| **III. Data Hygiene** | Raw files are checksum‑verified (SHA‑256) immediately after download; transformations write new files with provenance logs. |
| **IV. Single Source of Truth** | The master inference table `data/results/master_inference.parquet` is the sole source for every downstream statistic and figure. |
| **V. Versioning Discipline** | All artifacts are stored under `data/` with content‑hash filenames; the platform’s state file will be updated automatically. |
| **VI. Attention Sparsity and Geometric Coherence** | Dense‑scene definition, tipping‑point definition, and mIoU metric are implemented exactly as required. |
| **VII. Resource‑Constrained Validation** | All code runs with `torch.set_num_threads(2)` and memory‑mapped dataset loading; attribution runs also respect the CPU constraint. A lightweight model and sampling keep runtime ≤ 6 h. |

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
│   └── sparsity.py          # `SparsityConfig(num_patches, window_size=None)` with `get_mask()` API
├── model/
│   ├── locateany.py         # wrapper `LocateAnythingSparsityWrapper(sparsity_config)`; imports torch
│   └── attribution.py       # Captum‑based Grad‑CAM utilities
├── analysis/
│   ├── metrics.py           # mIoU, latency, exclusion flags
│   ├── stats.py             # ANOVA/Friedman, beta‑GLMM fallback, power analysis, Jonckheere‑Terpstra, Kendall’s τ, tipping‑point logic
│   └── reporting.py         # tables & figures generation
└── cli/
    └── run_experiment.py    # end‑to‑end driver (configurable phases, robust arg parsing, deterministic ordering)
tests/
├── contract/
│   └── test_contracts.py
├── unit/
│   ├── test_sparsity.py    # checks constructor signature and mask correctness
│   └── test_locateany.py   # checks thread limit, forward‑pass API
└── integration/
    └── test_full_pipeline.py
```

## Phase‑by‑Phase Roadmap (covers every FR and SC)

| Phase | Description | FR(s) Covered | SC(s) Covered | Key Outputs |
|------|-------------|---------------|---------------|-------------|
| **0 – Data Acquisition & Checksum** | Download VRSBench validation split, COCO 2017 validation split, and LocateAnything‑mini checkpoint metadata using the exact URLs from the Verified Datasets block. Compute SHA‑256 checksums and abort on mismatch. Implements a three‑retry mechanism for robustness. | – | – | `data/raw/vrsbench.parquet`, `data/raw/coco_val.parquet`, `data/raw/locateanything_metadata.txt` |
| **1 – Pre‑processing** | (a) Load datasets with `datasets.load_dataset(..., mmap=True)`. (b) Compute pairwise IoU per image. (c) Flag **dense‑scene** images (> 5 overlapping pairs, IoU > 0.10). (d) Flag **low‑density** images (≤ 5 overlapping pairs) – mIoU still computed, ambiguity‑resolution metric recorded as “N/A”. (e) Exclude ambiguous boxes (zero‑area or IoU > 0.95). (f) Record exclusion proportion (must be ≤ 5 %). (g) **Sample** at most 2 000 dense images (fixed seed = 42) to respect compute limits; if the full dense set is smaller, use all. (h) Persist dense and non‑dense subsets as streaming parquet files (process in chunks to stay within RAM). | FR‑003, FR‑007, FR‑008 | SC‑006, SC‑007 | `data/processed/dense_subset.parquet`, `data/processed/non_dense.parquet`, `data/processed/exclusion_log.json` |
| **2 – Model & Sparsity Knob** | Load the **LocateAnything‑mini** checkpoint (FP32) on CPU. Implement `SparsityConfig(num_patches, window_size=None)` that masks all tokens outside a sliding window of `num_patches` patches in each transformer layer. Supported values: `0` (global), `64`, `32`, `16`, optional `1`. The mask logic automatically yields a full‑global mask when `num_patches` ≥ total token count. Enforce FR‑001, FR‑006, and the corrected API signature (FR‑013). | FR‑001, FR‑006, FR‑013 | – | `src/model/sparsity.py` |
| **3 – Inference & mIoU Calculation** | For each sparsity configuration **global, 64, 32, 16, optional 1**: <br>  a. **Randomize** the order of configurations using a fixed seed (`np.random.RandomState(42)`). <br>  b. **Within each configuration**, shuffle the image list (same seed) before batching to eliminate systematic batch effects. <br>  c. Reset model state. <br>  d. Apply mask via `LocateAnythingSparsityWrapper(sparsity_config)`. <br>  e. Run inference on both dense and non‑dense subsets (batch = 4 to stay within RAM). <br>  f. Save per‑image prediction JSON under `data/predictions/<image_id>_<window>.json`. <br>  g. Compute per‑image **mIoU**, latency, and flag `excluded`. <br>  h. Append a row to `inference_<window>.parquet`. | FR‑002, FR‑009 (optional) | SC‑001, SC‑003, SC‑005, SC‑008 | `data/results/inference_32.parquet`, `data/predictions/*.json` |
| **4 – Statistical Analysis** | a. Mixed two‑way ANOVA (within‑subject: sparsity; between‑subject: density). Test normality per cell with Shapiro‑Wilk; if any p < 0.05, fall back to **Friedman aligned‑rank test** (FR‑004). <br>b. **Power analysis**: using `statsmodels.stats.power.FTestPower` with effect size f = 0.25, α = 0.05, power = 0.80 → required N ≈ 180 dense images. Our sampled dense set (≤ 2 000) comfortably exceeds this; report the calculated N. <br>c. **Beta‑GLMM fallback**: if residuals from ANOVA/Friedman remain non‑normal or heteroscedastic, fit a beta mixed‑effects model (`statsmodels` GLM with `family=Beta()`) treating sparsity as an ordered factor. <br>d. **Trend analysis**: perform a **Jonckheere‑Terpstra** test for ordered sparsity levels against mIoU (primary SC‑003). Additionally compute **Kendall’s τ** and report its p‑value. | FR‑004 | SC‑002, SC‑003 | `data/analysis/anova_results.json`, `data/analysis/trend_test.json`, `data/analysis/power_report.txt` |
| **5 – Tipping‑Point Detection & ±8‑Patch Sweep** | Identify the smallest window where the **upper bound of the 95 % confidence interval** of dense‑scene mean mIoU is **< 0.80** (statistical tipping point). If the CI criterion is not met, report “no tipping point reached”. <br>When a tipping point is found and the window > 1, run a **±8‑patch sweep** (clamped to 1‑64) around it, re‑run inference, and record the extra mIoU values. The sweep results are **exploratory**; apply a **Bonferroni correction** for the multiple comparisons and report corrected p‑values (SC‑001, SC‑004). Optional 1‑patch run executed only when `--run-one-patch` flag present (FR‑009). | FR‑010, FR‑011, FR‑009 | SC‑001, SC‑004 | `data/analysis/tipping_point.json`, `data/analysis/sweep_results.parquet` |
| **6 – Attribution on Failure / Success Cases** | a. **Pre‑register** a hold‑out set of 200 dense images (seed = 0) **before** any tipping‑point computation. Randomly assign these images into two independent groups (“Group A” and “Group B”) **without** looking at mIoU. <br>b. After the tipping point is known, label Group A as “failure” if its mIoU under the tipping‑point window < 0.80, otherwise “success”; similarly label Group B. This avoids outcome‑based selection bias. <br>c. Run Captum‑based Grad‑CAM on the full, unmasked model for all hold‑out images; generate heatmaps. <br>d. Compute **global‑context activation proportion** for each image; store in the inference parquet. <br>e. Summarize the **absolute difference** between the failure and success groups; **verify** that the difference ≥ 0.30 as required by SC‑004. If the threshold is not met, flag the result as “SC‑004 not satisfied”. | FR‑005, FR‑003 (selection) | SC‑004 | `data/attribution/failure_<id>.png`, `data/attribution/success_<id>.png`, `data/analysis/attribution_summary.json` |
| **7 – Reporting & Artifact Generation** | **7‑a. Consolidation**: Concatenate all `inference_*.parquet` files into a single `master_inference.parquet` and compute a SHA‑256 checksum (addresses plan_consistency‑fb7470e4). <br>**7‑b.** Assemble: <br>  - Degradation curve (Figure 1). <br>  - ANOVA/Friedman table (Table 1). <br>  - Trend test results (Table 2). <br>  - Tipping‑point table (Table 3). <br>  - Attribution collage (Figure 2). <br>  - Latency bar chart (Figure 3). <br>All tables/figures draw directly from `data/results/master_inference.parquet` to satisfy the SSoT requirement. Write `docs/results.md` for downstream paper pipeline. | All | SC‑001 – SC‑008 | `docs/results.md`, `figures/*.png`, `tables/*.csv` |
| **8 – Contract Validation** | Run `pytest -q tests/contract/` against `contracts/inference_results.schema.yaml`. CI fails if any result file violates the schema. | – | – | CI pass/fail |

All phases respect the data dependency order (download → preprocess → model → inference → analysis → reporting) and stay within the CPU‑only compute budget; no GPU escape hatch is required. The combination of dataset subsampling, a lightweight model checkpoint, and reduced batch size ensures the entire pipeline completes within the ≤ 6 h wall‑clock limit on the free‑tier runner. 

---  