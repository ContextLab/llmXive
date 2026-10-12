# Research: llmXive follow-up: extending "Why Can't I Open My Drawer? Mitigating Object-Driven Shortcuts in Zero"

## Objective
Demonstrate that adding a **Counterfactual Consistency (CC) loss** improves a model’s reliance on motion cues, reducing the accuracy drop (`ΔAcc`) when objects are swapped, and yielding statistically significant robustness gains on a **real, fully reproducible synthetic test set**.

## Dataset Strategy
| Role | Source | Access method | Reasoning |
|------|--------|---------------|-----------|
| Primary video corpus | **Synthetic moving‑shape generator** (procedurally created) | `src/data/synthetic_generator.py` (no external download) | Guarantees a known primary object, deterministic generation, and full control over motion; satisfies data‑availability rule because the generator is part of the repository. |
| Object‑patch library | Local image patches (colored shapes) shipped with the repo | Direct file access (`data/patches/`) | Guarantees distinct object classes and eliminates external download. |
| Pre‑computed optical flow | FlowNet‑C weights bundled in the repo (trained on FlyingThings3D) | Loaded via `src/data/optical_flow.py` | CPU‑friendly, stored as `.npy`; conforms to FR‑006. |

*No external video dataset is used because the only verified external URLs supplied in the user message are unrelated to video action data. Using the synthetic generator respects the Constitution (no unverified data) and still enables a valid test of the CC loss.*

## Counterfactual Generation Pipeline (FR‑001)
1. **Object detection** – deterministic color‑mask segmentation on the first frame (fast CPU).  
2. **Patch selection** – randomly pick a patch from a *different* class (metadata ensures class difference).  
3. **In‑painting & blending** – OpenCV `seamlessClone` to avoid seams.  
4. **Motion preservation validation** –  
   - Compute normalized L2 distance between original and swapped optical‑flow fields; accept if ≤ 0.15.  
   - Compute cosine similarity between frozen FlowNet‑C feature vectors; accept if ≥ 0.9.  
5. **Metadata recording** – write a row to `data/counterfactuals/metadata.csv` conforming to `contracts/counterfactual_pair.schema.yaml`.  
6. **Dataset split** – training (original + accepted counterfactuals for loss), validation (original only), **held‑out counterfactual test set** (accepted pairs never seen during training), and **motion‑only test set** (objects blurred).  

**Edge‑case handling** – videos where detection fails or divergence exceeds the threshold are **skipped** and logged; the pipeline never crashes (as required by US‑1 edge cases).

## Model & Loss (FR‑002, FR‑003)
- **Feature extractor**: frozen FlowNet‑C → 1024‑dim vector per video.  
- **Classifier**: single linear layer → softmax over action labels.  
- **Loss**:  
  - `L_CE` = cross‑entropy on original videos.  
  - `L_CC` = KL‑divergence between softmax outputs of original vs counterfactual pair.  
  - `L_total = L_CE + λ·L_CC` with λ ∈ {0.1, 0.5, 1.0}.  

Training runs for **10 random seeds** (seed list in `src/utils/seed.py`). Early stopping on validation CE; max 30 epochs (≈ 2 h total on CPU).

## Evaluation & Statistical Validation (FR‑004, FR‑005)
1. Compute `Acc_orig` and `Acc_swapped` per seed → `ΔAcc = Acc_orig - Acc_swapped`.  
2. Compute `Acc_motion` on the **motion‑only test set** (objects blurred).  
3. **Paired t‑test** across the 10 seeds comparing ΔAcc of CC‑model vs baseline (λ = 0).  
   - Null hypothesis: no reduction in ΔAcc.  
   - Significance threshold `p < 0.05`.  
4. **Bootstrap validation** – 10 000 resamples of seed‑level ΔAcc differences to obtain a 95 % confidence interval; report alongside the t‑test.  
5. Record effect size (Cohen’s d) for completeness.  

All statistical calculations use `scipy.stats.ttest_rel` and a custom bootstrap routine.

## Compute Feasibility Decision (CPU‑first)
- **Feature extraction**: FlowNet‑C inference on 200 synthetic videos ≈ 2 GB RAM, < 30 min CPU.  
- **Training**: Linear classifier – negligible memory, < 1 h per seed (total ≈ 5 h wall‑clock when run sequentially).  
- **Evaluation**: < 15 min total.  
- **Total wall‑clock**: ≈ 5 h, below the 6 h CI limit.  
- No GPU required; all libraries have CPU‑only implementations (FR‑006).  

**Rationale**: The scientific question concerns the effect of the CC loss on motion reliance; a lightweight CPU‑friendly pipeline suffices and respects free‑tier constraints.

## Expected Deliverables
- `data/counterfactuals/metadata.csv` (validated against `counterfactual_pair.schema.yaml`).  
- Trained checkpoints for each λ and baseline.  
- `results/per_seed.csv` (accuracy, ΔAcc, p‑value per seed).  
- `results/summary.csv` (averaged metrics, paired‑t statistic, bootstrap CI).  
- Plots: ΔAcc vs λ, bootstrap CI distribution, example frames (SSIM > 0.95).  
- `quickstart.md` with a one‑command end‑to‑end run.  

All results will be **associational** (Constitution I & DC‑001); no causal claims are made.

---
