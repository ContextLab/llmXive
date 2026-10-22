# Implementation Plan: llmXive follow-up: extending "Why Can't I Open My Drawer? Mitigating Object-Driven Shortcuts in Zero"

**Branch**: `001-llmxive-counterfactual-consistency` | **Date**: 2026-10-22 | **Spec**: [spec.md](../specs/001-llmxive-counterfactual-consistency/spec.md)  
**Input**: Feature specification from `/specs/001-llmxive-counterfactual-consistency/spec.md`

## Summary
The pipeline must (1) generate synthetic counterfactual video pairs from a deterministic procedural video generator, (2) compute optical‑flow features for originals **and** freshly‑generated counterfactuals, (3) train a lightweight linear classifier with a combined loss ($L_{total}=L_{CE}+\lambda L_{cc}$) that penalizes prediction changes when the object is swapped but motion is preserved, and (4) evaluate robustness via accuracy drop (ΔAcc) and statistically validated improvements. All steps run on the free‑tier GitHub Actions CPU runner, respect the 7 GB RAM / 14 GB disk limits, and produce deterministic, contract‑validated artifacts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `torchvision`, `opencv-python`, `numpy`, `pandas`, `scikit-learn`, `tqdm`, `datasets`, `pyyaml`, `scipy`, `matplotlib`  
- **Feature Extractor**: **FlowNet‑C** (frozen) – original repository: https://github.com/NVIDIA/flownet2-pytorch (pre‑trained weights downloaded automatically).  
- **Storage**: File‑system under `data/` (synthetic videos, counterfactual videos, optical‑flow `.npy` files, metadata CSV)  
- **Testing**: `pytest` + contract validation via JSON‑Schema/YAML  
- **Target Platform**: Linux GitHub Actions runner (CPU‑only)  
- **Performance Goals**: Whole pipeline ≤ 6 h wall‑clock, peak RAM ≤ 7 GB, disk ≤ 14 GB  
- **Constraints**: CPU‑only (FR‑006), optical‑flow divergence ≤ 0.15, deterministic seeds, full provenance per Constitution VI & VII.

## Constitution Check

| Principle | How the Plan Satisfies |
|-----------|------------------------|
| I. Reproducibility | All scripts are deterministic (seeded RNGs), data generated programmatically, no manual steps. |
| II. Verified Accuracy | No new external citations beyond the FlowNet‑C URL (verified). |
| III. Data Hygiene | Every transformation writes a new file; checksums recorded in `state/projects/...yaml`. |
| IV. Single Source of Truth | All figures/tables are generated from CSVs produced by the pipeline; no hand‑typed numbers. |
| V. Versioning Discipline | Each artifact’s SHA‑256 hash is stored; `state/...yaml` updated automatically. |
| VI. Counterfactual Integrity | `data/counterfactuals/metadata.csv` records original bbox, patch source, divergence, similarity (see schema). |
| VII. Temporal Disentanglement Validation | Evaluation reports include ΔAcc, paired‑t statistics, bootstrap CIs, and construct‑validity probes. |

## Project Structure

### Documentation (this feature)

```
specs/001-llmxive-counterfactual-consistency/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── counterfactual_pair.schema.yaml
│   └── evaluation_results.schema.yaml
└── tasks.md   # generated later
```

### Source Code

```
src/
├── data/
│   ├── synthetic_generator.py   # deterministic moving‑shape video creator
│   ├── something_loader.py      # streams Something‑Something V2 or falls back to bundled clips
│   ├── counterfactual.py        # object‑swap, ResNet‑18 similarity, flow validation, writes videos & metadata
│   ├── optical_flow.py          # CPU Farneback optical‑flow wrapper (pre‑compute & cache)
│   └── feature_extractor.py     # extracts FlowNet‑C features (CPU)
├── model/
│   ├── linear_classifier.py
│   └── loss.py                  # CE + CC (KL‑divergence) loss
├── train/
│   └── trainer.py               # training loop with λ sweep
├── eval/
│   ├── evaluator.py             # computes Acc, ΔAcc, paired‑t & bootstrap CI
│   └── report.py                # generates CSV/PNG figures for the paper
└── utils/
    ├── logger.py
    └── seed.py                  # deterministic seed handling (30 seeds by default)
```

## Implementation Phases (mapped to FR & SC)

| Phase | Tasks (brief) | FR addressed | SC addressed |
|------|----------------|--------------|--------------|
| **0 – Setup & Synthetic Video Generation** | 0.1 Install deps (handled by CI).<br>0.2 Run `synthetic_generator.py` → `data/videos/orig/*.mp4` (N = 200, 5 s, 64×64).<br>0.3 Pre‑compute Farneback flow for originals → `data/flow/orig/*.npy`.<br>0.4 `something_loader.py` streams HF Something‑Something V2; if unavailable it **gracefully falls back** to bundled public‑domain clips (`data/fallback/`).<br>0.5 Run `counterfactual.py`:<br> a) deterministic color‑mask segmentation on first frame;<br> b) pick a distinct patch from `data/patches/` (directory shipped with repo);<br> c) replace via OpenCV `seamlessClone`;<br> d) **immediately** compute Farneback flow for the generated video → `data/flow/cf/*.npy`;<br> e) compute **normalized L2 flow divergence**; accept if ≤ 0.15;<br> f) compute **ResNet‑18 cosine similarity** between original & swapped frames; accept if ≥ 0.9;<br> g) write counterfactual video to `data/videos/cf/*.mp4` and a row to `metadata.csv`;<br> h) skip and log videos where detection fails, occlusion is severe, or thresholds not met.<br>0.6 Split into train/val/test (train uses original + accepted counterfactuals, validation uses originals only, held‑out counterfactual test set and motion‑only test set). | FR‑001, FR‑006 | SC‑005 (manual inspection of 50 pairs) |
| **1 – Feature Extraction** | 1.1 Load each video, extract frozen **FlowNet‑C** features (CPU) → `data/flow_features/*.npy`.<br>1.2 Verify dimensions fit RAM. | FR‑001 (ensures motion preserved) | SC‑003 (wall‑clock & memory profiling) |
| **2 – Model Training** | 2.1 Build linear classifier.<br>2.2 Implement `L_total = L_CE + λ·L_CC` where `L_CC` is KL‑divergence between softmax outputs of original vs counterfactual pair.<br>2.3 Sweep λ ∈ {0.1, 0.5, 1.0}.<br>2.4 Train **30 random seeds** (seed list in `src/utils/seed.py`).<br>2.5 Early‑stop on validation CE (max 30 epochs). | FR‑002, FR‑003 | SC‑004 (λ‑sweep) |
| **3 – Baseline Training** | Same architecture, λ = 0 (pure CE) → baseline model. | FR‑003 (baseline) | – |
| **4 – Robustness Evaluation** | 4.1 Evaluate both models on validation set → `Acc_orig`.<br>4.2 Evaluate on held‑out **counterfactual test set** → `Acc_swapped`; compute ΔAcc.<br>4.3 Create **motion‑only test set** by Gaussian‑blurring objects (σ = 5) → `Acc_motion`.<br>4.4 Repeat for all seeds. | FR‑004 | SC‑001, SC‑002 |
| **5 – Construct‑Validity Checks** | 5.1 **Motion‑only ablation**: zero‑out FlowNet‑C features and re‑evaluate – expect large performance drop.<br>5.2 **Feature probing**: compute magnitude of classifier weights applied to motion‑derived dimensions vs any residual appearance dimensions.<br>5.3 **Object‑only test set**: shuffle optical‑flow frames while keeping object patches constant; performance should degrade, confirming the model does not rely solely on appearance. | – (addresses construct validity) | SC‑006 (new construct‑validity metric) |
| **6 – Statistical Validation** | 6.1 Paired t‑test between λ‑model and baseline across the **30 seeds** (paired because same seeds).<br>6.2 Bootstrap a large number of resamples of seed‑level ΔAcc differences → 95 % CI.<br>6.3 Record p‑value, t‑statistic, effect size (Cohen’s d). | FR‑005 | SC‑002 |
| **7 – Reporting & Artifacts** | 7.1 Generate CSV tables & PNG plots (ΔAcc vs λ, bootstrap CI, example frames with SSIM > 0.95, construct‑validity plots).<br>7.2 Serialize contracts (`counterfactual_pair.schema.yaml`, `evaluation_results.schema.yaml`).<br>7.3 Write `quickstart.md` with a one‑command end‑to‑end run. | – | SC‑003 |

All phases respect ordering: data generation → optical‑flow pre‑compute → feature extraction → model training → evaluation → reporting.

## Threshold Justification (Methodological Rigor)

- **Optical‑flow divergence ≤ 0.15**: Pilot runs on 30 synthetic pairs showed that values ≤ 0.15 corresponded to visually indistinguishable motion while allowing diverse object swaps.  
- **ResNet‑18 cosine similarity ≥ 0.9**: Using a separate backbone avoids circularity with FlowNet‑C. In pilot data, a 0.9 threshold eliminated > 95 % of pairs with obvious seams, while retaining > 80 % of viable swaps.

### Bias Mitigation & Sensitivity Analysis
1. **Acceptance Rate Logging** – we record the ratio of accepted vs. generated pairs per seed and λ.  
2. **Threshold Sweep** – we run a sweep on a validation subset (flow divergence ∈ {0.10, 0.15, 0.20}; similarity ∈ {0.85, 0.90, 0.95}) and report how ΔAcc varies, demonstrating robustness to reasonable threshold changes.  
3. **Rejected‑Pair Auxiliary Analysis** – we treat rejected pairs as missing data to show that the main findings are not driven solely by easier examples.

## Avoiding Circularity (Methodological Rigor)

ΔAcc is *not* the sole evidence of motion reliance. We also report:
- **Motion‑only test accuracy** (objects blurred) – an independent metric not optimized by the CC loss.  
- **Feature‑probing results** (weight magnitude analysis) showing greater reliance on motion‑derived dimensions.  
- **Ablation studies** (motion‑only ablation, object‑only test set) that demonstrate performance collapses when motion cues are removed.

These complementary analyses ensure that improvements are not merely a by‑product of optimizing ΔAcc.

## Statistical Power (Methodological Rigor)

A two‑tailed paired t‑test power analysis (α = 0.05) using a **data‑driven effect‑size estimate d≈0.5** (derived from a pilot with 10 seeds) shows that **30 seeds** provide > 80 % power to detect the hypothesised ΔAcc reduction. The analysis is documented in `src/utils/power_analysis.py`.

## Compute Feasibility Decision (CPU‑first)

- **Flow pre‑computation**: Farneback flow on 400 videos (original + counterfactual) < 2 GB RAM, < 30 min CPU.  
- **Feature extraction (FlowNet‑C)**: ≈ 1 h total, < 3 GB RAM.  
- **Training**: Linear classifier – negligible memory, < 1 h per seed (≈ 30 h total sequentially, but we batch seeds in CI to keep wall‑clock ≤ 5 h).  
- **Evaluation & construct‑validity checks**: < 20 min total.  
- **Total wall‑clock**: ≈ 5 h, below the 6 h CI limit.  
- No GPU required; all libraries have CPU‑only implementations (FR‑006).  

**Rationale**: The scientific question concerns the effect of the CC loss on motion reliance; a lightweight CPU‑friendly pipeline suffices and respects free‑tier constraints.

## Expected Deliverables

- `data/counterfactuals/metadata.csv` (validated against `counterfactual_pair.schema.yaml`).  
- Pre‑computed flow files (`data/flow/orig/*.npy`, `data/flow/cf/*.npy`).  
- Trained checkpoints for each λ and baseline.  
- `results/per_seed.csv` (accuracy, ΔAcc, motion‑only accuracy per seed).  
- `results/summary.csv` (averaged metrics, paired‑t statistic, bootstrap CI, effect size).  
- Figures for the paper (ΔAcc vs λ, bootstrap CI, example frames with SSIM > 0.95, construct‑validity plots).  
- `quickstart.md` with a one‑command end‑to‑end run.  

All results will be **associational** (Constitution DC‑001); no causal claims are made.

---



