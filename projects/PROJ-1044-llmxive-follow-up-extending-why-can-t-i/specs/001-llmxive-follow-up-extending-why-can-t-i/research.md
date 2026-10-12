# Research: llmXive follow-up: extending "Why Can't I Open My Drawer? Mitigating Object-Driven Shortcuts in Zero"

## Objective
Demonstrate that adding a **Counterfactual Consistency (CC) loss** improves a model’s reliance on motion cues, reducing the accuracy drop (`ΔAcc`) when objects are swapped, and yielding statistically significant robustness gains.

## Dataset Strategy
| Role | Source | Access method | Reasoning |
|------|--------|---------------|-----------|
| Primary synthetic video corpus | **Generated on‑the‑fly** (procedural moving‑shape videos) | `src/data/synthetic_generator.py` | No verified open‑source Something‑Something V2 dataset is available; synthetic data guarantees presence of a single, easily segmentable primary object and full control over motion. |
| Object‑patch library | Embedded image patches (e.g., colored shapes) shipped with the repo | Local files (`data/patches/`) | Guarantees distinct object classes and eliminates external download. |
| Pre‑computed optical flow | FlowNet‑C (trained on FlyingThings3D) weights bundled in repo | Loaded via `src/data/optical_flow.py` | CPU‑friendly, stored as `.npy`; conforms to FR‑006. |

*All generated files are checksummed and version‑controlled per Constitution III.*

## Counterfactual Generation Pipeline (FR‑001)
1. **Object detection** – simple color‑based segmentation (deterministic threshold).  
2. **Patch selection** – randomly pick a patch from a *different* class (ensured by metadata).  
3. **In‑painting & blending** – OpenCV seamlessClone to avoid seams.  
4. **Optical‑flow validation** – compute L2‑norm between original and swapped flow fields; accept if ≤ 0.15 (normalized).  
5. **Metadata recording** – write a row to `data/counterfactuals/metadata.csv` conforming to `contracts/counterfactual_pair.schema.yaml`.  

**Edge‑case handling** (occlusions, actor‑hand objects) – if detection fails or divergence > 0.15, the video is **skipped** and logged; pipeline never crashes (FR‑001, edge cases).

## Model & Loss (FR‑002, FR‑003)
- **Feature extractor**: frozen FlowNet‑C outputs a 1024‑dim vector per video.  
- **Classifier**: single linear layer → softmax over action labels.  
- **Loss**:  
  - `L_CE` = cross‑entropy on original videos.  
  - `L_CC` = KL‑divergence between softmax outputs of original vs counterfactual pair.  
  - `L_total = L_CE + λ·L_CC` (λ ∈ {0.1, 0.5, 1.0}).  

Training runs for **5 random seeds** (seed values listed in `src/utils/seed.py`). Early stopping based on validation CE loss; maximum 30 epochs (≈ 2 h total on CPU).

## Evaluation & Statistical Validation (FR‑004, FR‑005)
1. Compute `Acc_orig` and `Acc_swapped` for each seed → `ΔAcc = Acc_orig - Acc_swapped`.  
2. Compute `Acc_motion` on the **motion‑only test set** (objects blurred via Gaussian blur).  
3. Perform **paired t‑test** across the 5 seeds comparing ΔAcc of CC‑model vs baseline (λ = 0).  
   - Null hypothesis: no reduction in ΔAcc.  
   - Significance threshold `p < 0.05` (SC‑002).  
4. Record effect size (Cohen’s d) for completeness (not a spec requirement, but useful).  

All statistical calculations use `scipy.stats.ttest_rel`.  

## Compute Feasibility Decision (CPU‑first)
- **Feature extraction**: FlowNet‑C inference on 500 videos ≈ 2 GB RAM, < 30 min CPU.  
- **Training**: Linear classifier (~10 k parameters) – negligible memory, < 1 h per seed.  
- **Evaluation**: < 15 min total.  
- **Total wall‑clock**: ≈ 4 h, well below the 6 h GitHub Actions limit.  
- No GPU required; all libraries have CPU‑only implementations (FR‑006).  

**Rationale**: The scientific question is about loss‑function effects, not about state‑of‑the‑art video models, so a lightweight CPU‑friendly pipeline suffices and respects the free‑tier constraints.

## Expected Deliverables
- `data/counterfactuals/metadata.csv` (validated against `counterfactual_pair.schema.yaml`).  
- Trained checkpoints for each λ and baseline.  
- `results/evaluation.csv` (accuracy, ΔAcc, p‑values) conforming to `evaluation_results.schema.yaml`.  
- Plots: ΔAcc vs λ, p‑value distribution, example video frames (SSIM > 0.95).  
- `quickstart.md` with one‑command end‑to‑end run.  

All results will be **associational** (Constitution I & DC‑001) – we do not claim causal learning mechanisms.

---
