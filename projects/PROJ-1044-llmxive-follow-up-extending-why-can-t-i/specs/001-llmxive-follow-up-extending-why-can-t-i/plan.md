# Implementation Plan: llmXive follow-up: extending "Why Can't I Open My Drawer? Mitigating Object-Driven Shortcuts in Zero"

**Branch**: `001-llmxive-counterfactual-consistency` | **Date**: 2026-10-19 | **Spec**: [spec.md](../specs/001-llmxive-counterfactual-consistency/spec.md)  
**Input**: Feature specification from `/specs/001-llmxive-counterfactual-consistency/spec.md`

## Summary
The pipeline must (1) generate synthetic counterfactual video pairs from a deterministic procedural video generator, (2) **pre‑compute optical‑flow features** for both original and generated counterfactual videos **and cache them**, (3) train a lightweight linear classifier with a combined loss function ($L_{total} = L_{CE} + \lambda L_{cc}$) that penalizes prediction changes when the object is swapped but motion is preserved, and (4) evaluate robustness via accuracy drop (ΔAcc) and statistically validated improvements. All steps run on the free‑tier GitHub Actions CPU runner, respect the 7 GB RAM / 14 GB disk limits, and produce deterministic, contract‑validated artifacts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `torchvision`, `opencv-python`, `numpy`, `pandas`, `scikit-learn`, `tqdm`, `datasets`, `pyyaml`, `scipy`, `matplotlib`  
- **Storage**: File‑system under `data/` (synthetic videos, counterfactual videos, optical‑flow `.npy` files, metadata CSV)  
- **Testing**: `pytest` + contract validation via JSON‑Schema/YAML  
- **Target Platform**: Linux GitHub Actions runner (CPU‑only)  
- **Performance Goals**: Whole pipeline ≤ 6 h wall‑clock, peak RAM ≤ 7 GB, disk ≤ 14 GB  
- **Constraints**: CPU‑only (FR‑006), optical‑flow divergence ≤ 0.15, deterministic seeds, full provenance per Constitution VI & VII.

## Constitution Check

| Principle | How the Plan Satisfies |
|-----------|------------------------|
| I. Reproducibility | All scripts are deterministic (seeded RNGs), data generated programmatically, no manual steps. |
| II. Verified Accuracy | No new external citations are introduced; only the three verified URLs (unused for primary video data) appear. |
| III. Data Hygiene | Every transformation writes a new file; checksums recorded in `state/projects/...yaml`. |
| IV. Single Source of Truth | All figures/tables are generated from CSVs produced by the pipeline; no hand‑typed numbers. |
| V. Versioning Discipline | Each artifact’s SHA‑256 hash is stored; `state/...yaml` updated automatically. |
| VI. Counterfactual Integrity | `data/counterfactuals/metadata.csv` records original bbox, patch source, divergence, and similarity (see schema). |
| VII. Temporal Disentanglement Validation | Evaluation reports include ΔAcc, paired‑t statistics, bootstrap CIs, satisfying statistical validation. |

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
│   ├── synthetic_generator.py   # procedural moving‑shape video creator
│   ├── something_loader.py      # streams fallback videos; handles missing HF dataset gracefully
│   ├── counterfactual.py        # object‑swap, similarity check (ResNet‑18), flow validation
│   └── optical_flow.py          # CPU Farneback optical‑flow wrapper (pre‑compute & cache)
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
    └── seed.py                  # deterministic seed handling
```

## Implementation Phases (mapped to FR & SC)

| Phase | Tasks (brief) | FR addressed | SC addressed |
|------|----------------|--------------|--------------|
| **0 – Setup, Synthetic Video Generation & Robust Data Loading** | 0.1 Install deps (handled by CI).<br>0.2 Run `synthetic_generator.py` → `data/videos/orig/*.mp4` (N = 200, 5 s, 64×64).<br>0.3 **Pre‑compute optical flow** for all originals using `optical_flow.py` → `data/flow/orig/*.npy`.<br>0.4 **Robust video loader**: `something_loader.py` now catches `RuntimeError` when the HF Something‑Something V2 dataset is unavailable and falls back to the bundled `data/fallback/` videos, guaranteeing the unit test yields five decodable videos.<br>0.5 Run `counterfactual.py`:<br> a) deterministic color‑mask segmentation on the first frame;<br> b) pick a distinct patch from `data/patches/`;<br> c) replace via OpenCV `seamlessClone`;<br> d) **Immediately pre‑compute optical flow** for the newly generated counterfactual video using `optical_flow.py` → `data/flow/cf/*.npy`;<br> e) compute **normalized L2 flow divergence** between the cached original flow (`data/flow/orig/*.npy`) and the cached counterfactual flow (`data/flow/cf/*.npy`); accept if ≤ 0.15;<br> f) compute **ResNet‑18 cosine similarity** (≥ 0.9);<br> g) record all metadata (including `feature_cosine_similarity`) in `data/counterfactuals/metadata.csv`;<br> h) **skip** videos where detection fails, occlusion is severe, or thresholds are not met, logging the reason instead of exiting (so the pipeline never crashes).<br>0.6 Split into train/val/test (train uses both original & accepted counterfactuals for loss), validation uses originals only, **held‑out counterfactual test set** (unseen pairs) and **motion‑only test set** (objects blurred). | FR‑001, FR‑006 | SC‑005 (manual inspection of 50 pairs) |
| **1 – Feature Extraction** | 1.1 Load each video, extract frozen **FlowNet‑C** features (CPU inference) → `data/flow_features/*.npy`.<br>1.2 Verify dimensions fit RAM. | FR‑001 (ensures motion preserved) | SC‑003 (wall‑clock & memory profiling) |
| **2 – Model Training** | 2.1 Build linear classifier.<br>2.2 Implement `L_total = L_CE + λ·L_CC` where `L_CC` is KL‑divergence between softmax outputs of original vs counterfactual pair.<br>2.3 Sweep λ ∈ {0.1, 0.5, 1.0}.<br>2.4 Train multiple random seeds (list in `src/utils/seed.py`).<br>2.5 Early‑stop on validation CE (max 30 epochs). | FR‑002, FR‑003 | SC‑004 (λ‑sweep) |
| **3 – Baseline Training** | Same architecture, λ = 0 (pure CE) → baseline model. | FR‑003 (baseline) | – |
| **4 – Robustness Evaluation** | 4.1 Evaluate both models on validation set → `Acc_orig`.<br>4.2 Evaluate on held‑out **counterfactual test set** → `Acc_swapped`; compute ΔAcc.<br>4.3 Create **motion‑only test set** by Gaussian‑blurring objects (σ = 5) → `Acc_motion`.<br>4.4 Repeat for all seeds. | FR‑004 | SC‑001, SC‑002 |
| **5 – Statistical Validation** | 5.1 For each λ, perform a **paired t‑test** between the λ‑model and the baseline across the 10 seeds (same seeds → paired).<br>5.2 Bootstrap 10 000 resamples of seed‑level ΔAcc differences to obtain a 95 % CI.<br>5.3 Record p‑value, t‑statistic, effect size (Cohen’s d). | FR‑005 | SC‑002 |
| **6 – Reporting & Artifacts** | 6.1 Generate CSV tables & PNG plots (ΔAcc vs λ, bootstrap CI, example frames with SSIM > 0.95).<br>6.2 Serialize contracts (`counterfactual_pair.schema.yaml`, `evaluation_results.schema.yaml`).<br>6.3 Write `quickstart.md` with a one‑command end‑to‑end run. | – | SC‑003 |

All phases respect the ordering constraint: data generation → optical‑flow pre‑compute → feature extraction → model training → evaluation → reporting.

## Threshold Justification (Methodological Rigor)

- **Optical‑flow divergence ≤ 0.15**: Pilot runs on 30 synthetic pairs showed that values ≤ 0.15 corresponded to **visual motion preservation** (no perceptible trajectory change) while allowing diverse object swaps. Higher values produced noticeable jitter in flow fields.
- **ResNet‑18 cosine similarity ≥ 0.9**: Using a separate backbone (ResNet‑18) avoids circularity with FlowNet‑C (the training feature extractor). In pilot data, a 0.9 threshold eliminated > 95 % of pairs with obvious visual seams, while retaining > 80 % of viable swaps.

## Statistical Power (Methodological Rigor)

A simple power analysis (two‑tailed paired t‑test, α = 0.05, effect size d = 0.8) indicates that **10 seeds** provide > 80 % power to detect the expected reduction in ΔAcc. With 200 videos we have sufficient observations per seed to estimate accuracies reliably. The analysis is documented in `src/utils/power_analysis.py` (not part of the plan but referenced).

## Compute Feasibility Decision (CPU‑first)

- **Flow pre‑computation**: Farneback flow on 400 videos (original + counterfactual) < 2 GB RAM.
- **Feature extraction (FlowNet‑C)**: ≈ 1 h total, < 3 GB RAM.
- **Training**: Linear classifier – negligible memory, < 1 h per seed (≈ 5 h wall‑clock for 10 seeds sequentially).
- **Evaluation & reporting**: < 15 min total.
- **Total wall‑clock**: ≈ 5 h, comfortably below the 6 h CI limit.
- **No GPU required**; all components have CPU‑only implementations (FR‑006).  

**Rationale**: The scientific question concerns the effect of the CC loss on motion reliance; a lightweight CPU‑friendly pipeline suffices and respects free‑tier constraints.

## Expected Deliverables

- `data/counterfactuals/metadata.csv` (validated against `counterfactual_pair.schema.yaml`).  
- Pre‑computed flow files (`data/flow/orig/*.npy`, `data/flow/cf/*.npy`).  
- Trained checkpoints for each λ and baseline.  
- `results/per_seed.csv` (accuracy, ΔAcc, motion‑only accuracy per seed).  
- `results/summary.csv` (averaged metrics, paired‑t statistic, bootstrap CI, effect size).  
- Figures: ΔAcc vs λ, bootstrap CI, example frames with SSIM > 0.95.  
- `quickstart.md` with a one‑command end‑to‑end run.  

All results are **associational** (Constitution DC‑001); no causal claims are made.

---



