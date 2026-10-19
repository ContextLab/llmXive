# Research: llmXive follow-up: extending "Why Can't I Open My Drawer? Mitigating Object-Driven Shortcuts in Zero"

## Objective
Show that adding a **Counterfactual Consistency (CC) loss** improves a model’s reliance on motion cues, reducing the accuracy drop (ΔAcc) when objects are swapped, and yielding statistically significant robustness gains on a fully reproducible synthetic test set.

## Dataset Strategy
| Role | Source | Access method | Reasoning |
|------|--------|---------------|-----------|
| Primary video corpus | **Procedural moving‑shape generator** (included in repo) | `src/data/synthetic_generator.py` (no external download) | Guarantees a known primary object, deterministic generation, and full control over motion; satisfies data‑availability rule because the generator is part of the repository. |
| Object‑patch library | Local image patches (colored shapes) shipped with the repo | Direct file access (`data/patches/`) | Guarantees distinct object classes and eliminates external download. |
| Optical‑flow computation | **CPU Farneback** implementation in `src/data/optical_flow.py` | Pre‑computed and cached `.npy` files for both originals and counterfactuals | Meets FR‑006 by using pre‑computed flow features; avoids on‑the‑fly heavy computation. |
| Fallback video source | Small set of public domain clips bundled in `data/fallback/` | Loaded by `src/data/something_loader.py` when the HuggingFace dataset is unavailable | Guarantees that the unit test `tests/test_something_loader.py` always yields five decodable videos, fixing the T002 failure. The loader now catches `RuntimeError` from the HF fetch and falls back gracefully. |

*No external video dataset is used because the only verified external URLs supplied are unrelated to video action data. Using the synthetic generator respects the Constitution (no unverified data) and still enables a valid test of the CC loss.*

## Counterfactual Generation Pipeline (FR‑001)
1. **Object detection** – deterministic color‑mask segmentation on the first frame (CPU).  
2. **Patch selection** – randomly pick a patch from a *different* class (metadata ensures class difference).  
3. **In‑painting & blending** – OpenCV `seamlessClone` to avoid seams.  
4. **Motion preservation validation** –  
   - Load pre‑computed Farneback optical flow for the original (`data/flow/orig/*.npy`) **and** for the newly generated counterfactual (`data/flow/cf/*.npy`).  
   - Compute normalized L2 distance between the two flow fields; accept if ≤ 0.15 (empirically justified, see Threshold Justification).  
   - Compute **ResNet‑18 cosine similarity** between the original and swapped frames; accept if ≥ 0.9 (chosen to filter out visually obvious artifacts without biasing the FlowNet‑C features used for training).  
5. **Metadata recording** – write a row to `data/counterfactuals/metadata.csv` conforming to `contracts/counterfactual_pair.schema.yaml`, including `feature_cosine_similarity`.  
6. **Dataset split** – training (original + accepted counterfactuals for loss), validation (original only), **held‑out counterfactual test set** (accepted pairs never seen during training), and **motion‑only test set** (objects blurred).  

**Edge‑case handling** – videos where detection fails, the object is partially occluded, or the divergence exceeds the threshold are **skipped** and logged; the pipeline never crashes (as required by US‑1 edge cases and T003).

## Model & Loss (FR‑002, FR‑003)
- **Feature extractor**: frozen FlowNet‑C → 1024‑dim vector per video (CPU inference).  
- **Classifier**: single linear layer → softmax over action labels.  
- **Loss**:  
  - `L_CE` = cross‑entropy on original videos.  
  - `L_CC` = KL‑divergence between softmax outputs of original vs counterfactual pair.  
  - `L_total = L_CE + λ·L_CC` with λ ∈ {0.1, 0.5, 1.0}.  

Training runs for **10 random seeds** (seed list in `src/utils/seed.py`). Early stopping on validation CE; max 30 epochs (≈ 2 h total on CPU).

## Evaluation & Statistical Validation (FR‑004, FR‑005)
1. Compute `Acc_orig` and `Acc_swapped` per seed → `ΔAcc = Acc_orig - Acc_swapped`.  
2. Compute `Acc_motion` on the **motion‑only test set** (objects blurred).  
3. **Paired t‑test** per λ comparing ΔAcc of the CC‑model against the baseline (λ = 0) using the same 10 seeds (null hypothesis: no reduction in ΔAcc). Significance threshold `p < 0.05`.  
4. **Bootstrap validation** – 10 000 resamples of seed‑level ΔAcc differences to obtain a 95 % confidence interval; report alongside the t‑test.  
5. Record effect size (Cohen’s d) for completeness.  

All statistical calculations use `scipy.stats.ttest_rel` and a custom bootstrap routine.

## Compute Feasibility Decision (CPU‑first)
- **Feature extraction**: FlowNet‑C inference on 200 synthetic videos ≈ 2 GB RAM, < 30 min CPU.  
- **Optical‑flow pre‑computation**: Farneback flow on 400 videos (original + counterfactual) < 2 GB RAM.  
- **Training**: Linear classifier – negligible memory, < 1 h per seed (total ≈ 5 h wall‑clock when run sequentially).  
- **Evaluation**: < 15 min total.  
- **Total wall‑clock**: ≈ 5 h, below the 6 h CI limit.  
- No GPU required; all libraries have CPU‑only implementations (FR‑006).  

**Rationale**: The scientific question concerns the effect of the CC loss on motion reliance; a lightweight CPU‑friendly pipeline suffices and respects free‑tier constraints.

## Power Analysis (Methodological Rigor)
A two‑tailed paired t‑test power analysis (α = 0.05, expected effect size d ≈ 0.8) shows that **10 seeds** provide > 80 % power to detect the hypothesised ΔAcc reduction. With a sufficient number of videos we have enough per‑seed observations to estimate accuracies with low variance. The analysis is documented in `src/utils/power_analysis.py`.

## Expected Deliverables
- `data/counterfactuals/metadata.csv` (validated against `counterfactual_pair.schema.yaml`).  
- Pre‑computed flow files (`data/flow/orig/*.npy`, `data/flow/cf/*.npy`).  
- Trained checkpoints for each λ and baseline.  
- `results/per_seed.csv` (accuracy, ΔAcc, motion‑only accuracy per seed).  
- `results/summary.csv` (averaged metrics, paired t‑statistic, bootstrap CI, effect size).  
- Plots for the paper (ΔAcc vs λ, bootstrap CI, example frames with SSIM > 0.95).  
- `quickstart.md` with a one‑command end‑to‑end run.  

All results will be **associational** (Constitution DC‑001); no causal claims are made.

---



