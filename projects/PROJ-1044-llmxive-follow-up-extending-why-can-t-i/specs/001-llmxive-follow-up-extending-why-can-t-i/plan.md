# Implementation Plan: llmXive follow-up: extending "Why Can't I Open My Drawer? Mitigating Object-Driven Shortcuts in Zero"

**Branch**: `001-llmxive-counterfactual-consistency` | **Date**: 2026-10-19 | **Spec**: [spec.md](../specs/001-llmxive-counterfactual-consistency/spec.md)  
**Input**: Feature specification from `/specs/001-llmxive-counterfactual-consistency/spec.md`

## Summary
The pipeline must (1) generate synthetic counterfactual video pairs from a deterministic procedural video generator, (2) compute **CPU‑friendly optical‑flow** on‑the‑fly for each pair to enforce the ≤ 0.15 divergence constraint, (3) train a linear classifier with a combined cross‑entropy + counterfactual‑consistency loss, and (4) evaluate robustness via accuracy drop (ΔAcc) and statistically validated improvements. All steps run on the free‑tier GitHub Actions CPU runner, respect the 7 GB RAM / 14 GB disk limits, and produce deterministic, contract‑validated artifacts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `torchvision`, `opencv-python`, `numpy`, `pandas`, `scikit-learn`, `tqdm`, `datasets`, `pyyaml`, `scipy`, `matplotlib`  
- **Storage**: File‑system under `data/` (synthetic videos, counterfactual videos, optical‑flow `.npy` files, metadata CSV)  
- **Testing**: `pytest` + contract validation via JSON‑Schema/YAML  
- **Target Platform**: Linux GitHub Actions runner (CPU‑only)  
- **Project Type**: Research library / CLI utilities under `src/`  
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
| VI. Counterfactual Integrity | `data/counterfactuals/metadata.csv` records original bbox, patch source, divergence, and similarity for every pair. |
| VII. Temporal Disentanglement Validation | Evaluation reports include ΔAcc, paired‑t statistics, bootstrap CIs, satisfying the statistical validation requirement. |

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
│   ├── counterfactual.py        # object‑swap, CPU optical‑flow validation
│   └── optical_flow.py          # CPU Farneback optical flow wrapper
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
| **0 – Setup & Synthetic Video Generation** | 0.1 Install deps; 0.2 Run `synthetic_generator.py` → `data/videos/orig/*.mp4` (N = 200, 5 s, 64×64); 0.3 Run `counterfactual.py`:<br> a) detect primary shape via color mask;<br> b) pick a distinct patch from `data/patches/`;<br> c) replace with OpenCV `seamlessClone`;<br> d) compute **CPU Farneback optical flow** for original & swapped videos;<br> e) calculate normalized L2 divergence; accept if ≤ 0.15 **and** cosine similarity ≥ 0.9;<br> f) write accepted pairs to `data/counterfactuals/metadata.csv`; 0.4 Split into train/val/test. | FR‑001, FR‑006 | SC‑005 (manual inspection of 50 pairs) |
| **1 – Feature Extraction** | 1.1 Load each video, compute frozen FlowNet‑C features (CPU inference) → `data/flow/*.npy`; 1.2 Verify dimensions fit RAM. | FR‑001 (ensures motion preserved) | SC‑003 (wall‑clock & memory profiling) |
| **2 – Model Training** | 2.1 Build linear classifier; 2.2 Implement `L_total = CE + λ·L_CC`; 2.3 Sweep λ ∈ {0.1, 0.5, 1.0}; 2.4 Train **10 random seeds** (list in `src/utils/seed.py`); 2.5 Early‑stop on validation CE (max 30 epochs). | FR‑002, FR‑003 | SC‑004 (λ‑sweep) |
| **3 – Baseline Training** | 3.1 Same architecture, λ = 0 (pure CE) → baseline model. | FR‑003 (baseline) | – |
| **4 – Robustness Evaluation** | 4.1 Evaluate both models on validation set → `Acc_orig`; 4.2 Evaluate on held‑out counterfactual test set → `Acc_swapped`; 4.3 Compute ΔAcc; 4.4 Create **motion‑only test set** by Gaussian‑blurring objects (σ = 5) → `Acc_motion`; 4.5 Repeat for all seeds. | FR‑004 | SC‑001, SC‑002 |
| **5 – Statistical Validation** | 5.1 Paired t‑test on ΔAcc across seeds (proposed vs baseline). 5.2 Bootstrap 95 % CI (10 000 resamples). 5.3 Record p‑value, t‑statistic, effect size (Cohen’s d). | FR‑005 | SC‑002 |
| **6 – Reporting & Artifacts** | 6.1 Generate CSV tables & PNG plots (ΔAcc vs λ, bootstrap CI, example frames with SSIM > 0.95). 6.2 Serialize contracts (`counterfactual_pair.schema.yaml`, `evaluation_results.schema.yaml`). 6.3 Write `quickstart.md`. | – | SC‑003 |

All phases respect the ordering constraint: data generation → optical‑flow validation → feature extraction → model training → evaluation → reporting.

---
