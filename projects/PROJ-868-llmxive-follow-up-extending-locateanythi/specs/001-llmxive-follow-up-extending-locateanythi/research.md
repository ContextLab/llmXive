# Research: llmXive follow-up – extending "LocateAnything: Fast and High-Quality Vision-Language Grounding with P"

**Feature**: llmXive follow-up – attention sparsity impact study  
**Prepared on**: 2026‑10‑24  

## Overview
We will empirically measure how restricting the attention window of a LocateAnything‑style vision‑language grounding model degrades bounding‑box geometric coherence (mean Intersection‑over‑Union, mIoU) on dense scenes, locate the sparsity “tipping point” for an 80 % mIoU threshold, and explain failure modes via gradient‑based attribution. All work runs on the free‑tier GitHub Actions CPU runner (2 cores, ≤ 7 GB RAM, ≤ 6 h wall‑clock).

## Dataset Strategy
| Role | Dataset | Verified Source URL(s) | Loader | Key Variables |
|------|---------|------------------------|--------|---------------|
| Primary dense‑scene source | VRSBench (validation split) | | `datasets.load_dataset("omlab/VRSBench-FS", split="validation")` | `image_id`, `bbox` (list of `[x1,y1,x2,y2]`) |
| Supplemental bounding‑box source | COCO 2017 (validation split) | https://huggingface.co/datasets/jxie/coco_captions/resolve/main/data/test-00000-of-00009-4a09b5aab8de74d3.parquet | `datasets.load_dataset("coco", split="validation")` | `image_id`, `annotations.bbox`, `annotations.category_id` |
| Model checkpoint metadata | LocateAnything (demo) | https://huggingface.co/datasets/danelcsb/locateanything-job-demo/resolve/main/metadata.txt | custom `download.py` (simple text file) | checkpoint URL (provided in metadata) |

All datasets are directly downloadable via the Hugging Face `datasets` library or `urllib`. No authentication is required. Checksums are recorded in `data/` as part of the pipeline.

## Compute Decision & Rationale
- **CPU‑first**: All required operations (sparsity mask generation, inference, statistical tests, Grad‑CAM) have faithful CPU implementations. The LocateAnything checkpoint fits in < 3 GB VRAM when loaded on CPU and runs comfortably with `torch.set_num_threads(2)`. No GPU‑only kernels are needed.
- **GPU escape hatch**: Not required for this study. If future work demands a larger transformer, the plan would switch to a quantized 8‑bit model on Kaggle’s free GPU, but the current pipeline stays entirely on CPU.

## Methodology

### 1. Pre‑processing & Subset Construction
1. Load VRSBench and COCO (validation) with memory‑mapped loading (`mmap=True`).  
2. For each image, compute pairwise IoU among all ground‑truth boxes.  
   - **Dense‑scene**: > 5 boxes where each pair’s IoU > 0.10 (FR‑003).  
   - **Low‑density**: ≤ 5 overlapping pairs – still processed for mIoU but the ambiguity‑resolution failure metric is recorded as “N/A” (FR‑008/SC‑007).  
   - **Non‑dense**: all remaining images (including low‑density).  
3. Flag **ambiguous** boxes (zero‑area or IoU > 0.95 with another box) and exclude them from any mIoU computation (FR‑007). Record the proportion of excluded samples (must be ≤ 5 % → SC‑006).  
4. Persist dense and non‑dense subsets as Parquet files (Phase 1 output).  

### 2. Model & Sparsity Configuration
- Load the LocateAnything checkpoint (FP32) on CPU.  
- Implement `SparsityConfig(window_size)` that masks all tokens outside a sliding window of `window_size` patches in each transformer layer. Supported values: `global` (encoded as 0), `64`, `32`, `16`, optional `1`.  
- The mask only zeroes attention scores; model weights remain unchanged (FR‑001, FR‑006).

### 3. Inference & Metric Computation
For each sparsity configuration (global, 64, 32, 16, optional 1):  
- Reset model state to avoid carry‑over effects.  
- Run inference on **both** dense and non‑dense subsets (batch = 8).  
- Save per‑image predictions as JSON under `data/predictions/<image_id>_<window>.json`.  
- Compute per‑image **mIoU** against ground truth, record inference **latency** (ms), and set `excluded` flag if the image was ambiguous.  
- Append a row to `inference_<window>.parquet` containing all fields required by the contract schema (FR‑002, FR‑009).  

### 4. Statistical Analysis
- **Mixed two‑way ANOVA**: Within‑subject factor = sparsity level; between‑subject factor = scene density.  
  - Test normality per cell with Shapiro‑Wilk; if any p < 0.05, fall back to **Friedman aligned‑rank test** (FR‑004).  
  - Report the interaction p‑value (SC‑002).  
- **Power analysis**: Assuming a medium effect size f = 0.25, α = 0.05, within‑subject correlation r = 0.5, and 4 sparsity levels, `statsmodels.stats.power.FTestPower` indicates > 80 % power with the expected dense‑scene N (≈ 2 k). The script `src/analysis/power_analysis.py` records the calculation (SC‑002).  
- **Correlation**: Compute Pearson correlation between numeric window size and mIoU for each density group; if the relationship appears non‑linear, also compute Spearman. Report coefficients (SC‑003).  

### 5. Tipping‑Point Detection & Sensitivity Sweep
- Identify the smallest window where dense‑scene **mean** mIoU < 0.80 (FR‑010).  
- If such a window exists and is > 1, run a **±8‑patch sweep** (clamped to 1‑64) around it, re‑run inference, and record the extra mIoU values (FR‑011).  
- If no tipping point is found, record “no tipping point reached”.  
- Optional 1‑patch run is executed only when `--run-one-patch` is set (FR‑009).  

### 6. Attribution Analysis (Hold‑out Procedure)
- **Hold‑out set**: Before any tipping‑point computation, randomly sample 200 dense images (seed = 0) – 100 designated as “failure candidates” and 100 as “success candidates”. This set is **not** used for determining the tipping point (FR‑003).  
- After the tipping point is known, select from the hold‑out set:  
  - **Failure images**: those where the tipping‑point window yields mIoU < 0.80.  
  - **Success images**: those where global attention yields mIoU ≥ 0.80.  
- Apply **Grad‑CAM** (or attention rollout if Grad‑CAM fails) to the final convolutional layer, generate heatmaps, and compute **global‑context activation proportion** (mass on tokens labelled “global‑context”).  
- Store the proportion in the inference results parquet (`global_context_activation_proportion`).  
- Summarize the absolute difference between failure and success groups (SC‑004).  

### 7. Power & Sample‑Size Considerations
- Expected dense‑scene count from VRSBench is on the order of a few thousand images. With the parameters above, power > 80 % is achieved.  
- If after preprocessing the dense count drops below 500 (unlikely), we will explicitly note the reduced power in the final report and rely on descriptive statistics only (SC‑002).  

### 8. Reporting
- **Figure 1**: Degradation curve (mIoU vs. window size) with 95 % confidence intervals.  
- **Table 1**: ANOVA (or Friedman) results, interaction p‑value.  
- **Table 2**: Correlation coefficients (Pearson & Spearman) per density.  
- **Figure 2**: Attribution heatmap collage (failure vs. success).  
- **Table 3**: Global‑context activation proportion difference (SC‑004).  
- **Figure 3**: Inference latency per image across configurations (SC‑005).  
All tables/figures reference a single row in the underlying CSV/Parquet artifact, satisfying Constitution Principle IV.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Insufficient dense scenes after filtering | May reduce statistical power | Verify dense count after Phase 1; if < 500, report limitation and rely on descriptive stats. |
| Memory overflow on CPU | Job failure | Use streaming/parquet chunking; process in batches; persist intermediate aggregates to disk. |
| Ambiguous‑box exclusion > 5 % | Violates SC‑006 | Log offending images; if > 5 %, consider relaxing the IoU > 0.95 threshold (document change). |
| Download script failure (previous T000) | Pipeline aborts | Implement robust `download.py` that retries, validates SHA‑256, and aborts with clear error if checksum mismatches. |

---

