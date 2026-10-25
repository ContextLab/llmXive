# Implementation Plan: llmXive follow-up: extending "LocateAnything: Fast and High-Quality Vision-Language Grounding with P"

**Branch**: `001-llmxive-follow-up` | **Date**: 2026-10-24 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-llmxive-follow-up/spec.md`

## Summary
The project will (1) quantify how limiting the attention window of a LocateAnything‑style vision‑language grounding model degrades geometric coherence (mean Intersection‑over‑Union, mIoU) on dense scenes, (2) locate the sparsity “tipping point” where dense‑scene mIoU first drops below 80 %, (3) optionally run a ±8‑patch sensitivity sweep around the tipping point, and (4) explain failure modes with gradient‑based attribution. All steps are fully reproducible on the free‑tier GitHub Actions CPU runner (2 cores, ≤ 7 GB RAM, ≤ 6 h wall‑clock).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `torchvision`, `transformers`, `datasets`, `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `opencv-python`, `grad-cam` (or `captum`), `tqdm`  
- **Storage**: Files under `data/` (raw downloads, processed subsets, intermediate parquet/CSV, prediction JSONs, figures)  
- **Testing**: `pytest` + contract validation (`contracts/inference_results.schema.yaml`)  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM, no GPU)  
- **Constraints**: CPU‑only (`torch.set_num_threads(2)`) and memory‑mapped loading; total runtime ≤ 6 h per CI job  

## Constitution Check

| Principle | How the plan satisfies it |
|-----------|--------------------------|
| **I. Reproducibility** | Fixed random seeds (`numpy`, `torch`, `random`). All external data fetched from the exact URLs listed in the Verified Datasets block. |
| **II. Verified Accuracy** | No new citations are introduced; all dataset sources are pre‑verified. |
| **III. Data Hygiene** | Raw files are checksum‑verified; each transformation writes a new file with a provenance log. |
| **IV. Single Source of Truth** | The master inference table `data/results/master_inference.parquet` (merged across all sparsity windows) serves as the definitive source for every downstream table and figure. |
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
│   ├── download.py          # robust download + checksum verification
│   ├── preprocess.py        # dense‑scene filtering, ambiguous‑box exclusion
│   └── sparsity.py          # attention‑mask generator (window sizes)
├── model/
│   ├── locateany.py         # wrapper for LocateAnything with sparsity knob
│   └── attribution.py       # Grad‑CAM / attention‑rollout utilities
├── analysis/
│   ├── metrics.py           # mIoU, latency, exclusion flags
│   ├── stats.py             # ANOVA/Friedman, power analysis, correlation, tipping‑point logic
│   └── reporting.py         # tables & figures generation
└── cli/
    └── run_experiment.py    # end‑to‑end driver (configurable phases)
tests/
├── contract/
│   └── test_contracts.py
└── unit/
    └── test_metrics.py
```

## Phase‑by‑Phase Roadmap (covers every FR and SC)

| Phase | Description | FR(s) Covered | SC(s) Covered | Key Outputs |
|------|-------------|---------------|---------------|-------------|
| **0 – Data Acquisition & Checksum** | Download VRSBench **validation** split, COCO 2017 validation split, and LocateAnything metadata using the exact URLs from the Verified Datasets block. Compute SHA‑256 checksums and abort on mismatch. | – | – | `data/raw/vrsbench.parquet`, `data/raw/coco_val.parquet`, `data/raw/locateanything_metadata.txt` |
| **1 – Pre‑processing** | (a) Load datasets with `datasets.load_dataset(..., mmap=True)`. (b) Compute pairwise IoU per image. (c) Flag **dense‑scene** images (> 5 overlapping pairs, IoU > 0.10). (d) Flag **low‑density** images (≤ 5 overlapping pairs) – mIoU will still be computed for them, but the ambiguity‑resolution failure metric will be recorded as “N/A” per FR‑008/SC‑007. (e) Exclude ambiguous boxes (zero‑area or IoU > 0.95). (f) Record exclusion proportion (must be ≤ 5 %). (g) Persist dense and non‑dense subsets as Parquet. | FR‑003, FR‑007, FR‑008 | SC‑006, SC‑007 | `data/processed/dense_subset.parquet`, `data/processed/non_dense.parquet`, `data/processed/exclusion_log.json` |
| **2 – Model & Sparsity Knob** | Load LocateAnything checkpoint (FP32) on CPU. Implement `SparsityConfig(window_size)` that masks all tokens outside a sliding window of `window_size` patches in each transformer layer. Supported values: `global` (0), `64`, `32`, `16`, optional `1`. Enforce FR‑001 and FR‑006. | FR‑001, FR‑006 | – | `src/model/sparsity.py` |
| **3 – Inference & mIoU Calculation** | For each sparsity config (global, 64, 32, 16, optional 1): <br>  a. Reset model state. <br>  b. Apply mask. <br>  c. Run inference on both dense and non‑dense subsets (batch = 8). <br>  d. Save per‑image prediction JSON (`data/predictions/<image_id>_<window>.json`). <br>  e. Compute per‑image **mIoU**, latency, and flag `excluded`. <br>  f. Append a row to `inference_<window>.parquet`. | FR‑002, FR‑009 (optional) | SC‑001, SC‑003, SC‑005 | `data/results/inference_32.parquet`, `data/predictions/*.json` |
| **4 – Statistical Analysis** | a. Mixed two‑way ANOVA (within‑subject: sparsity; between‑subject: density). Check Shapiro‑Wilk; if any cell fails (p < 0.05) fall back to **Friedman aligned‑rank test** (FR‑004). <br>b. Power analysis (effect size f = 0.25, α = 0.05, within‑subject r = 0.5) using `statsmodels`; report > 80 % power or note limitation. <br>c. Pearson & Spearman correlations of window size vs. mIoU per density group. Report coefficients (SC‑003). | FR‑004 | SC‑002, SC‑003 | `data/analysis/anova_results.json`, `data/analysis/correlation.csv`, `data/analysis/power_report.txt` |
| **5 – Tipping‑Point Detection & ±8‑Patch Sweep** | Identify smallest window where dense‑scene **mean** mIoU < 0.80 (FR‑010). If found and > 1, run a **±8‑patch sweep** (clamped to 1‑64) and record extra mIoU values (FR‑011). Include optional 1‑patch run if `--run-one-patch` flag present (FR‑009). | FR‑010, FR‑011, FR‑009 | SC‑001 | `data/analysis/tipping_point.json`, `data/analysis/sweep_results.parquet` |
| **6 – Attribution on Failure / Success Cases** | a. Hold‑out 200 dense images (seed = 0) before any tipping‑point computation (100 failure‑candidates, 100 success‑candidates). <br>b. After tipping point is known, select from the hold‑out set: failure images where the tipping‑point window yields mIoU < 0.80, success images where global attention yields mIoU ≥ 0.80. <br>c. Run Grad‑CAM (or attention rollout) on the final conv layer; generate heatmaps. <br>d. Compute **global‑context activation proportion** for each image, write back to inference parquet. <br>e. Summarize absolute difference between failure and success groups (FR‑005). | FR‑005, FR‑003 (selection) | SC‑004 | `data/attribution/failure_<id>.png`, `data/attribution/success_<id>.png`, `data/analysis/attribution_summary.json` |
| **7 – Reporting & Artifact Generation** | Assemble: <br>  - Degradation curve (Figure 1). <br>  - ANOVA/Friedman table (Table 1). <br>  - Correlation table (Table 2). <br>  - Tipping‑point table (Table 3). <br>  - Attribution collage (Figure 2). <br>  - Latency bar chart (Figure 3). <br>All tables/figures draw directly from the master inference table (`data/results/master_inference.parquet`) to satisfy the SSoT requirement. Write `docs/results.md` for downstream paper pipeline. | All | SC‑001 – SC‑007 | `docs/results.md`, `figures/*.png`, `tables/*.csv` |
| **8 – Contract Validation** | Run `pytest -q tests/contract/` against `contracts/inference_results.schema.yaml`. CI fails if any result file violates the schema. | – | – | CI pass/fail |

All phases respect the data dependency order (download → preprocess → model → inference → analysis → reporting) and stay within the CPU‑only compute budget; no GPU escape hatch is required.

---

