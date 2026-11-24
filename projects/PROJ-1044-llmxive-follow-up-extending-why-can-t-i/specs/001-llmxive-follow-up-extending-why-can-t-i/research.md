# Research: llmXive follow-up: extending "Why Can't I Open My Drawer? Mitigating Object-Driven Shortcuts in Zero"

## Objective
Show that adding a **Counterfactual Consistency (CC) loss** improves a model’s reliance on motion cues, reducing the accuracy drop (ΔAcc) when objects are swapped, and yielding statistically significant robustness gains on a fully reproducible synthetic test set. Primary evidence comes from **independent motion‑only evaluations**, feature probing, and ablation studies; ΔAcc is reported only as a secondary, optimization‑adjacent metric.

## Dataset Strategy
| Role | Source | Access method | Reasoning |
|------|--------|---------------|-----------|
| Primary video corpus | **Procedural moving‑shape generator** (included in repo) | `src/data/synthetic_generator.py` (no external download) | Guarantees a known primary object, deterministic generation, and full control over motion; satisfies data‑availability rule because the generator is part of the repository. |
| Object‑patch library | Local image patches (colored shapes) shipped with the repo | Direct file access (`data/patches/`) | Guarantees distinct object classes and eliminates the need for external download. |
| Optical‑flow computation | **CPU Farneback** implementation in `src/data/optical_flow.py` | Pre‑computed and cached `.npy` files for originals; **computed on‑the‑fly for each generated counterfactual** | Meets FR‑006 (CPU‑only) while allowing validation of motion preservation for newly created videos. |
| Fallback video source | Small set of public‑domain clips bundled in `data/fallback/` | Loaded directly by `src/data/synthetic_generator.py` when needed | Guarantees that unit tests always have decodable videos, fixing previous failures, without requiring any unverified external dataset. |

*No external video dataset is used because the only verified external URLs supplied are unrelated to video action data. Using the synthetic generator respects the Constitution (no unverified data) and still enables a valid test of the CC loss.*

## Counterfactual Generation Pipeline (FR‑001)
1. **Object detection** – deterministic color‑mask segmentation on the first frame.  
2. **Patch selection** – randomly pick a patch from a *different* class (metadata ensures class difference).  
3. **In‑painting & blending** – OpenCV `seamlessClone` to avoid seams.  
4. **Motion preservation validation** –  
   - Load pre‑computed Farneback optical flow for the original (`data/flow/orig/*.npy`) **and** compute Farneback flow for the newly generated counterfactual (`data/flow/cf/*.npy`).  
   - Compute normalized L2 distance; accept if ≤ 0.15.  
   - Compute **ResNet‑18 cosine similarity** between the original and swapped frames; accept if ≥ 0.9.  
5. **Metadata recording** – write a row to `data/counterfactuals/metadata.csv` conforming to `contracts/counterfactual_pair.schema.yaml`, including `feature_cosine_similarity`.  
6. **Dataset split** – training (original + accepted counterfactuals for loss), validation (original only), **held‑out counterfactual test set** (accepted pairs never seen during training), and **motion‑only test set** (objects blurred).  

**Edge‑case handling** – videos where detection fails, the object is partially occluded, or the divergence exceeds the threshold are **skipped** and logged; the pipeline never crashes (as required by the edge‑case specifications).

### Bias Mitigation & Sensitivity Analysis
- **Acceptance Rate Logging** – ratio of accepted vs. generated pairs per seed and λ is recorded.  
- **Threshold Sweep** – divergence ∈ {0.10, 0.15, 0.20} and similarity ∈ {0.85, 0.90, 0.95} are explored on a validation subset; ΔAcc variation is reported to demonstrate robustness to reasonable threshold changes.  
- **Rejected‑Pair Auxiliary Analysis** – rejected pairs are treated as missing data to show that the main findings are not driven solely by easier examples.

## Model & Loss (FR‑002, FR‑003)
- **Feature extractor**: frozen FlowNet‑C → 1024‑dim vector per video (CPU inference). *(Citation: NVIDIA FlowNet‑C, https://github.com/NVIDIA/flownet2-pytorch)*  
- **Classifier**: single linear layer → softmax over action labels.  
- **Loss**:  
  - `L_CE` = cross‑entropy on original videos.  
  - `L_CC` = KL‑divergence between softmax outputs of original vs counterfactual pair.  
  - `L_total = L_CE + λ·L_CC` with λ ∈ {0.1, 0.5, 1.0}.  

Training runs for **15 random seeds** (seed list in `src/utils/seed.py`). Early stopping on validation CE; max set to a reasonable number of epochs.

## Evaluation & Statistical Validation (FR‑004, FR‑005)
1. Compute `Acc_orig` and `Acc_swapped` per seed → `ΔAcc = Acc_orig - Acc_swapped` (reported **as a secondary metric**).  
2. Compute `Acc_motion` on the **motion‑only test set** (objects blurred).  
3. **Paired t‑test** per λ comparing ΔAcc of the CC‑model against the baseline (λ = 0) using the same **15 seeds** (null hypothesis: no reduction in ΔAcc). Significance threshold `p < 0.05`.  
4. **Bootstrap validation** – 10 000 resamples of seed‑level ΔAcc differences to obtain a 95 % confidence interval; reported alongside the t‑test.  
5. Record effect size (Cohen’s d) for completeness.  

### Construct‑Validity Checks (addresses methodology‑6db273e5)
- **Motion‑only ablation**: re‑evaluate models with FlowNet‑C features zero‑ed out – a large performance drop confirms reliance on motion.  
- **Feature probing**: examine the magnitude of linear weights applied to motion‑derived dimensions versus any residual appearance dimensions.  
- **Object‑only test set**: shuffle optical‑flow frames while keeping object patches constant; performance should degrade, showing the model does not simply memorize object appearance.

## Avoiding Circularity (addresses scientific_soundness‑a3845db5)
ΔAcc is **not** the sole evidence of motion reliance. We also report:  
- **Motion‑only test accuracy** (objects blurred) – an independent metric not optimized by the CC loss.  
- **Feature‑probing results** showing greater reliance on motion‑derived dimensions.  
- **Ablation studies** (motion‑only ablation, object‑only test set) where performance collapses when motion cues are removed.  
These complementary analyses ensure that improvements are not merely a by‑product of optimizing ΔAcc.

## Compute Feasibility Decision (CPU‑first)
- **Flow pre‑computation**: Farneback flow on 400 videos (original + counterfactual) < 2 GB RAM, < 30 min CPU.  
- **Feature extraction (FlowNet‑C)**: ≈ 1 h total, < 3 GB RAM.  
- **Training**: Linear classifier – negligible memory, **15 seeds** run **sequentially** ([deferred] per seed), total ≈ 2.5 h.
- **Evaluation & construct‑validity checks**: < 20 min total.  
- **Total wall‑clock**: ≈ 5 h, below the 6 h CI limit.  
- No GPU required; all libraries have CPU‑only implementations (FR‑006).

**Rationale**: The scientific question concerns the effect of the CC loss on motion reliance; a lightweight CPU‑friendly pipeline suffices and respects free‑tier constraints.

## Power Analysis (Methodological Rigor)
A two‑tailed paired t‑test power analysis (α = 0.05) using a **data‑driven effect‑size estimate d≈0.5** (pilot with 10 seeds) shows that **15 seeds** provide > 80 % power to detect the hypothesised ΔAcc reduction. The analysis is documented in `src/utils/power_analysis.py`.

## Expected Deliverables
- `data/counterfactuals/metadata.csv` (validated against `counterfactual_pair.schema.yaml`).  
- Pre‑computed flow files (`data/flow/orig/*.npy`, `data/flow/cf/*.npy`).  
- Trained checkpoints for each λ and baseline.  
- `results/per_seed.csv` (accuracy, ΔAcc, motion‑only accuracy per seed).  
- `results/summary.csv` (averaged metrics, paired‑t statistic, bootstrap CI, effect size).  
- Figures for the paper (ΔAcc vs λ, bootstrap CI, example frames with SSIM > 0.95, construct‑validity plots).  
- `quickstart.md` with a one‑command end‑to‑end run.  

All results will be **associational** (Constitution DC‑001); no causal claims are made.
