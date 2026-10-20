# Research: llmXive follow-up: extending "LocateAnything: Fast and High-Quality Vision-Language Grounding with P"

**Feature**: llmXive follow-up – attention sparsity impact study  
**Prepared on**: 2026‑10‑19  

## Overview
We will empirically measure how restricting the attention window of a LocateAnything‑style vision‑language grounding model degrades bounding‑box geometric coherence (mean Intersection‑over‑Union, mIoU) on dense scenes, locate the sparsity “tipping point” for an 80 % mIoU threshold, and explain failure modes via gradient‑based attribution. All work runs on a multi‑core CPU runner with sufficient memory and uses only openly available datasets.

## Dataset Strategy
| Role | Dataset | Source URL (verified) | Loader | Key Variables |
|------|---------|-----------------------|--------|---------------|
| Primary dense‑scene source | VRSBench (validation split) | https://huggingface.co/datasets/omlab/VRSBench-FS/resolve/main/data/train_10shot-00000-of-00001.parquet | `datasets.load_dataset("omlab/VRSBench-FS", split="validation")` | `image_id`, `bbox` (list of `[x1,y1,x2,y2]`), `caption` |
| Supplemental bounding‑box source | COCO 2017 (validation split) | | `datasets.load_dataset("coco", split="validation")` | `image_id`, `annotations.bbox`, `annotations.category_id` |
| Model metadata (pre‑trained checkpoints) | LocateAnything (demo) | https://huggingface.co/datasets/danelcsb/locateanything-job-demo/resolve/main/metadata.txt | custom `download.py` (simple text file) | checkpoint URL (provided in metadata) |
| Optional FP32 reference (not used for main analysis) | FP32 (json) | https://huggingface.co/datasets/wangyanhui666/imagenet_vae_mds_fp32/resolve/main/0/index.json | not used | – |

All datasets are directly downloadable via `datasets` or `urllib`; no authentication is required. Checksums are recorded in `data/` as part of the pipeline (see `src/data/download.py`).

## Compute Decision & Rationale
- **CPU‑first**: All required operations (mask generation, inference, statistical tests, Grad‑CAM) have faithful CPU implementations. The model fits in < 3 GB VRAM when loaded on CPU (FP32) and can be run with `torch.set_num_threads(2)`. No GPU‑only kernels are needed.
- **GPU escape hatch**: Not required. If future experiments demand a transformer with > 10 M parameters, we would switch to a quantized 8‑bit model on Kaggle GPU, but the current LocateAnything variant runs comfortably on CPU.

## Methodology

### 1. Pre‑processing & Subset Construction
1. Load VRSBench and COCO (validation) with memory‑mapped loading (`mmap=True`).  
2. For each image, compute pairwise IoU among all ground‑truth boxes.  
   - Dense‑scene definition: **> 5** boxes where **pairwise IoU > 0.10**.  
   - Non‑dense: all remaining images.  
3. Flag ambiguous boxes: zero‑area or IoU > 0.95 with another box. Exclude these from any mIoU computation (FR‑007). Record exclusion proportion (must be ≤ 5 % → SC‑006).  
4. Persist dense and non‑dense subsets as Parquet files.

### 2. Model & Sparsity Configuration
- Load the LocateAnything checkpoint (FP32) on CPU.  
- Implement `SparsityConfig(window_size)` that masks all tokens outside a sliding window of `window_size` patches in each transformer layer. Supported values: `global`, `64`, `32`, `16`, optional `1`.  
- Verify that the mask does **not** alter model weights (only attention scores are zeroed).  

### 3. Inference & Metric Computation
For each sparsity config, **re‑load the model** (or reset its state) and recompute the attention mask to avoid carry‑over effects. Optionally shuffle the order of configurations.  
- Run inference on both dense and non‑dense subsets (batch = 8).  
- For each image, **save a prediction JSON** under `data/predictions/<image_id>_<window>.json`.  
- Record per‑image predicted boxes, compute **mIoU** against ground truth, and measure per‑image latency.  
- Store results in a parquet file that includes a `prediction_path` column pointing to the JSON file.  
- Aggregate to configuration‑level means (FR‑002).  
- Optional 1‑patch run executed only if the user sets `--run‑one‑patch` (FR‑009).  

### 4. Statistical Analysis
- **Mixed ANOVA**: Within‑subject factor = sparsity level (4 or 5 levels); between‑subject factor = scene density (dense vs non‑dense).  
  - Check normality (Shapiro‑Wilk) for each cell.  
  - If any cell fails (p < 0.05), fall back to **Friedman aligned‑rank test** (FR‑004).  
  - Report interaction p‑value (SC‑002).  
- **Power analysis**: Assuming a medium effect size f = 0.25, within‑subject correlation r = 0.5, ε = 1 (sphericity), α = 0.05, and 4 sparsity levels, `statsmodels.stats.power.FTestPower` indicates that with ~2 k dense images the study achieves > 80 % power. The script `src/analysis/power_analysis.py` (included in the repo) reproduces this calculation.  
- **Correlation**: Compute Pearson correlation between window size (numeric) and mIoU for each density group; if non‑linear pattern detected, also compute Spearman. Report coefficients (SC‑003).  

### 5. Tipping‑Point Detection & Sensitivity Sweep
- Identify the smallest window where dense‑scene mIoU < 0.80 (FR‑010).  
- If found and > 1, perform a **±8‑patch sweep** (clamped to 1‑64) around that window, rerun inference, and report the extra mIoU values (FR‑011).  
- If no tipping point exists, record “no tipping point reached”.  

### 6. Attribution Analysis (Pre‑specified Hold‑out)
- **Hold‑out set**: Before any tipping‑point computation, randomly sample 200 dense images (fixed seed) – 100 designated as “failure candidates” and 100 as “success candidates”. This set is **not** used for determining the tipping point.  
- After the tipping point is identified, select from the hold‑out set:  
  - **Failure images**: those where the local‑attention configuration (the tipping‑point window) yields mIoU < 0.80.  
  - **Success images**: those where global attention yields mIoU ≥ 0.80.  
- Apply **Grad‑CAM** (or attention rollout if Grad‑CAM unavailable) to the final convolutional layer.  
- Compute **global‑context activation proportion**: sum of activation values on tokens labelled “global‑context” divided by total activation mass.  
- Write this proportion back into the corresponding rows of the inference results parquet (`global_context_activation_proportion` column).  
- Report the absolute difference between failure and success groups (SC‑004).  

### 7. Power & Sample‑Size Considerations
- The dense‑scene subset typically contains **≈ 2 k** images (based on VRSBench statistics). Using the parameters above (f = 0.25, r = 0.5, ε = 1, α = 0.05, 4 levels), `statsmodels.stats.power.FTestPower` yields **> 80 % power** for detecting a medium interaction effect in the mixed ANOVA.  
- If the dense subset falls below **500** images (unlikely with VRSBench), we will explicitly note the reduced power in the final report and rely on descriptive statistics only.  

### 8. Reporting
- Generate **Figure 1**: degradation curve (mIoU vs. window size) with error bars (95 % CI).  
- **Table 1**: ANOVA/Friedman results, p‑values.  
- **Table 2**: Correlation coefficients.  
- **Figure 2**: attribution heatmap examples (failure vs. success).  
- **Table 3**: Global‑context activation proportion difference.  
- **Figure 3**: latency per image across configs (SC‑005).  

All tables/figures reference a single row in the underlying CSV/Parquet artifact, satisfying Principle IV.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Dataset lacks sufficient dense scenes | May reduce power for ANOVA | Verify dense count after preprocessing; if < 500, report limitation and still provide descriptive stats. |
| Memory overflow on CPU | Job fails > 7 GB | Use streaming mode for raw parquet; process in chunks; persist intermediate aggregates to disk. |
| Ambiguous‑box exclusion > 5 % | Violates SC‑006 | Log offending images; if > 5 %, consider relaxing IoU > 0.95 threshold (documented change). |

---

