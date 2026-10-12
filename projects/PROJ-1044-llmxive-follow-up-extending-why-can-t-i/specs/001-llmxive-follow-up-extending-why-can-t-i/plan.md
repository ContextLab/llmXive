# Implementation Plan: llmXive follow-up: extending "Why Can't I Open My Drawer? Mitigating Object-Driven Shortcuts in Zero"

**Branch**: `001-llmxive-counterfactual-consistency` | **Date**: 2026-10-11 | **Spec**: [spec.md](../specs/001-llmxive-counterfactual-consistency/spec.md)  
**Input**: Feature specification from `/specs/001-llmxive-counterfactual-consistency/spec.md`

## Summary
The project must (1) generate **counterfactual video pairs** from the open‑source **Something‑Something V2** dataset by swapping the primary object while preserving motion, (2) train a lightweight linear classifier with a combined cross‑entropy + counterfactual‑consistency loss, and (3) evaluate robustness via accuracy drop (`ΔAcc`) and statistically validated improvements. All steps run on **CPU‑only** resources using pre‑computed optical‑flow features and respect the free‑tier GitHub Actions constraints.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `torchvision`, `opencv-python`, `numpy`, `pandas`, `scikit-learn`, `tqdm`, `datasets`, `pyyaml`, `scipy`, `matplotlib`  
- **Storage**: File‑system under `data/` (raw videos, counterfactual videos, optical‑flow `.npy` files, metadata CSV)  
- **Testing**: `pytest` for unit tests; contract validation via `jsonschema`/`pyyaml`  
- **Target Platform**: Linux GitHub Actions runner (CPU‑only)  
- **Project Type**: Research library / CLI utilities under `src/`  
- **Performance Goals**: Whole pipeline ≤ 6 h wall‑clock, peak RAM ≤ 7 GB, disk ≤ 14 GB  
- **Constraints**: CPU‑only (FR‑006), optical‑flow divergence ≤ 0.15, reproducible random seeds, full provenance per Constitution VI & VII.  

## Constitution Check
| Principle | How the Plan Satisfies |
|-----------|------------------------|
| I. Reproducibility | All scripts are deterministic (seeded RNGs), data fetched/created programmatically, no manual steps. |
| II. Verified Accuracy | No external citations are introduced beyond the open‑source Something‑Something V2 dataset accessed via HuggingFace (verified open source). |
| III. Data Hygiene | Every transformation writes a new file; checksums recorded in `state/projects/...yaml`. |
| IV. Single Source of Truth | All figures/tables are generated from the CSVs produced by the pipeline; no hand‑typed numbers. |
| V. Versioning Discipline | Each artifact’s SHA‑256 hash is stored; `state/...yaml` updated automatically. |
| VI. Counterfactual Integrity | Counterfactual metadata (original bbox, patch source, divergence, feature similarity) is saved in `data/counterfactuals/metadata.csv`. |
| VII. Temporal Disentanglement Validation | Evaluation reports include `ΔAcc` and paired‑t (or bootstrap) p‑values, satisfying the statistical validation requirement. |

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
└── tasks.md   # (generated later)
```

### Source Code

```
src/
├── data/
│   ├── something_something_loader.py   # streams Something‑Something V2 videos
│   ├── counterfactual.py               # object‑swap & motion validation
│   └── optical_flow.py                 # wrapper around pre‑computed FlowNet features
├── model/
│   ├── linear_classifier.py            # lightweight linear head on frozen flow features
│   └── loss.py                         # CE + CC (KL‑divergence) loss
├── train/
│   └── trainer.py                      # training loop with hyper‑parameter λ sweep
├── eval/
│   ├── evaluator.py                    # computes Acc, ΔAcc, paired‑t & bootstrap CI
│   └── report.py                       # generates CSV/PNG figures for the paper
└── utils/
    ├── logger.py
    └── seed.py                         # deterministic seed handling
```

## Complexity Tracking
No constitution violations identified; all required functionalities fit within CPU limits and the real‑data approach respects the data‑availability rule.

## Implementation Phases (mapped to Functional & Success Criteria)

| Phase | Tasks (brief) | FR addressed | SC addressed |
|------|----------------|--------------|--------------|
| **0 – Setup & Data Generation** | 0.1 Install deps; 0.2 Stream Something‑Something V2 via `datasets.load_dataset(..., streaming=True)`; 0.3 Randomly sample a representative set of videos (ensuring each has a clear primary object); 0.4 Detect primary object using a lightweight CPU‑friendly detector (`torchvision.models.detection.fasterrcnn_resnet50_fpn` with `torch.no_grad`); 0.5 Select a distinct object patch from `data/patches/`; 0.6 Replace object region with OpenCV `seamlessClone`; 0.7 Compute optical‑flow (pre‑computed FlowNet‑C) for original & swapped; 0.8 **Validate motion preservation**: (a) normalized L2 flow divergence ≤ 0.15 **and** (b) cosine similarity of FlowNet‑C feature vectors ≥ 0.9; 0.9 Record metadata CSV; 0.10 Split data: **training** ([deferred] of originals + accepted counterfactuals for loss), **validation** (original only), **test** (held‑out counterfactuals, never seen during training). | FR‑001, FR‑006 | SC‑005 (manual inspection subset) |
| **1 – Feature Extraction** | 1.1 Load videos, extract frozen FlowNet‑C features (saved as `.npy`); 1.2 Verify feature size fits RAM. | FR‑001 (ensures motion preserved) | SC‑003 (wall‑clock & memory profiling) |
| **2 – Model Training** | 2.1 Build linear classifier; 2.2 Implement `L_total = CE + λ·L_cc`; 2.3 Sweep λ ∈ {0.1, 0.5, 1.0}; 2.4 Train multiple random seeds (seed list in `src/utils/seed.py`) to achieve >80 % power for detecting a medium effect (Cohen’s d≈0.5); 2.5 Save best checkpoint per λ. | FR‑002, FR‑003 | SC‑004 (λ‑sweep) |
| **3 – Baseline Training** | 3.1 Same architecture, λ = 0 (pure CE) → baseline model. | FR‑003 (baseline) | – |
| **4 – Robustness Evaluation** | 4.1 Evaluate both models on **validation** set → `Acc_orig`; 4.2 Evaluate on **held‑out counterfactual test set** → `Acc_swapped`; 4.3 Compute ΔAcc; 4.4 Evaluate on **motion‑only test set** (objects blurred) → `Acc_motion`; 4.5 Repeat for all 10 seeds. | FR‑004 | SC‑001, SC‑002 |
| **5 – Statistical Validation** | 5.1 Perform **paired t‑test** on ΔAcc across seeds (proposed vs baseline). 5.2 Additionally compute **bootstrap 95 % confidence intervals** (10 000 resamples) as a non‑parametric check. 5.3 Record p‑value, t‑statistic, and bootstrap CI; flag significance (`p < 0.05`). | FR‑005 | SC‑002 |
| **6 – Reporting & Artifacts** | 6.1 Generate CSV tables, PNG plots (ΔAcc vs λ, bootstrap CI, example frames with SSIM > 0.95); 6.2 Serialize contracts (`counterfactual_pair.schema.yaml`, `evaluation_results.schema.yaml`); 6.3 Write `quickstart.md`. | – | SC‑003 |

---


## projects/PROJ-1044-llmxive-follow-up-extending-why-can-t-i/specs/001-llmxive-follow-up-extending-why-can-t-i/research.md

# Research: llmXive follow-up: extending "Why Can't I Open My Drawer? Mitigating Object-Driven Shortcuts in Zero"

## Objective
Demonstrate that adding a **Counterfactual Consistency (CC) loss** improves a model’s reliance on motion cues, reducing the accuracy drop (`ΔAcc`) when objects are swapped, and yielding statistically significant robustness gains on a **real** Something‑Something V2 test set.

## Dataset Strategy
| Role | Source | Access method | Reasoning |
|------|--------|---------------|-----------|
| Primary video corpus | **Something‑Something V2** (HuggingFace identifier `something-something-v2`) | `datasets.load_dataset("something-something-v2", "full", streaming=True)` | Open, programmatic, and contains realistic action videos. |
| Object‑patch library | Embedded image patches (colored shapes) shipped with the repo | Local files (`data/patches/`) | Guarantees distinct object classes and eliminates external download. |
| Pre‑computed optical flow | FlowNet‑C (trained on FlyingThings3D) weights bundled in repo | Loaded via `src/data/optical_flow.py` | CPU‑friendly, stored as `.npy`; conforms to FR‑006. |

*All generated files are checksummed and version‑controlled per Constitution III.*

## Counterfactual Generation Pipeline (FR‑001)
1. **Object detection** – lightweight Faster‑RCNN (CPU‑friendly) on a single representative frame per video; fallback to colour‑mask if detection fails.  
2. **Patch selection** – randomly pick a patch from a *different* class (ensured by metadata).  
3. **In‑painting & blending** – OpenCV `seamlessClone` to avoid seams.  
4. **Motion preservation validation** –  
   - Compute normalized L2 distance between original and swapped optical‑flow fields; accept if ≤ 0.15.  
   - Compute cosine similarity between frozen FlowNet‑C feature vectors; accept if ≥ 0.9.  
5. **Metadata recording** – write a row to `data/counterfactuals/metadata.csv` conforming to `contracts/counterfactual_pair.schema.yaml`.  
6. **Dataset split** – training (a majority of originals + accepted counterfactuals for loss), validation (original only), **held‑out counterfactual test set** ([deferred] of accepted pairs, never used during training).

**Edge‑case handling** – videos where detection fails or divergence / similarity thresholds are not met are **skipped** and logged; the pipeline never crashes (FR‑001, edge cases).

## Model & Loss (FR‑002, FR‑003)
- **Feature extractor**: frozen FlowNet‑C outputs a 1024‑dim vector per video.  
- **Classifier**: single linear layer → softmax over action labels.  
- **Loss**:  
  - `L_CE` = cross‑entropy on original videos.  
  - `L_CC` = KL‑divergence between softmax outputs of original vs counterfactual pair.  
  - `L_total = L_CE + λ·L_CC` (λ ∈ {0.1, 0.5, 1.0}).  

Training runs for **10 random seeds** (seed values listed in `src/utils/seed.py`). Early stopping based on validation CE loss; maximum 30 epochs (≈ 2 h total on CPU).

## Evaluation & Statistical Validation (FR‑004, FR‑005)
1. Compute `Acc_orig` and `Acc_swapped` for each seed → `ΔAcc = Acc_orig - Acc_swapped`.  
2. Compute `Acc_motion` on the **motion‑only test set** (objects blurred via Gaussian blur).  
3. Perform **paired t‑test** across the 10 seeds comparing ΔAcc of CC‑model vs baseline (λ = 0).  
   - Null hypothesis: no reduction in ΔAcc.  
   - Significance threshold `p < 0.05`.  
4. **Bootstrap validation** – 10 000 resamples of the seed‑level ΔAcc differences to obtain a 95 % confidence interval; report alongside the t‑test.  
5. Record effect size (Cohen’s d) for completeness.  

All statistical calculations use `scipy.stats.ttest_rel` and a custom bootstrap routine.

## Compute Feasibility Decision (CPU‑first)
- **Feature extraction**: FlowNet‑C inference on 200 videos ≈ a few GB RAM, < 30 min CPU.  
- **Training**: Linear classifier – negligible memory, < 1 h per seed (total ≈ a few hours wall‑clock, but parallelizable; we run seeds sequentially within the 6 h CI limit by limiting λ‑sweep to two values in CI and using a reduced epoch count; full run is feasible locally).  
- **Evaluation**: < 15 min total.  
- **Total wall‑clock (CI)**: ≈ 5 h, below the 6 h limit.  
- No GPU required; all libraries have CPU‑only implementations (FR‑006).  

**Rationale**: The scientific question concerns the effect of the CC loss on motion reliance, not state‑of‑the‑art video modeling, so a lightweight CPU‑friendly pipeline suffices and respects the free‑tier constraints.

## Expected Deliverables
- `data/counterfactuals/metadata.csv` (validated against `counterfactual_pair.schema.yaml`).  
- Trained checkpoints for each λ and baseline.  
- `results/evaluation.csv` (accuracy, ΔAcc, p‑values, bootstrap CI) conforming to `evaluation_results.schema.yaml`.  
- Plots: ΔAcc vs λ, bootstrap CI distribution, example video frames (SSIM > 0.95).  
- `quickstart.md` with one‑command end‑to‑end run.  

All results will be **associational** (Constitution I & DC‑001) – we do not claim causal learning mechanisms.

---

