# Research: llmXive Follow-up: Physics-Teacher Distillation

**Feature**: llmXive Follow-up: Physics-Teacher Distillation  
**Branch**: `002-llmxive-physics-teacher-distillation`  
**Date**: 2026-10-17  

## Objective
Validate whether a deterministic CPU physics engine (Box2D) can replace a neural teacher in the Causal Forcing++ distillation pipeline, while meeting the success criteria (SC‑001 – SC‑009).

## Dataset Strategy

| Role | Source | Access Method | Verified URL | Notes |
|------|--------|--------------|--------------|-------|
| Physics Engine Metadata (seed, world definition) | Box2D example dataset | `datasets.load_dataset("frankcholula/Box2D", split="train")` (streaming) | https://huggingface.co/datasets/frankcholula/Box2D/resolve/main/BipedalWalker-v3/expert-v0/data/metadata.json | Provides initial state vectors and world parameters; used to instantiate deterministic simulations. |
| SSIM reference values (sample subset) | Pre‑computed SSIM parquet | `datasets.load_dataset("Hemabhushan/capstone_sakuga_preproc_ssim", split="train")` | https://huggingface.co/datasets/Hemabhushan/capstone_sakuga_preproc_ssim/resolve/main/sample_subset/train-00000-of-00060.parquet | Used only for sanity‑check of SSIM implementation; not for training. |
| PSNR reference values (sample subset) | Pre‑computed PSNR parquet | `datasets.load_dataset("predict-SIREN-PSNR/COIN-collection", split="train")` | https://huggingface.co/datasets/predict-SIREN-PSNR/COIN-collection/resolve/main/data/mscoco/mscoco_unique_urls.parquet | Same as SSIM. |
| FID reference shards | Pre‑computed FID parquet | `datasets.load_dataset("carnival13/hotpot_FiD", split="train")` | https://huggingface.co/datasets/carnival13/hotpot_FiD/resolve/main/data/train-00000-of-00004-fe37021775bb0e94.parquet | Provides example FID scores for sanity‑checking the FID pipeline. |
| LPIPS & EvaluationMetrics | **No verified source** | – | – | LPIPS will be computed on‑the‑fly using the `lpips` library; EvaluationMetrics is an internal aggregation (see `contracts/evaluation_results.schema.yaml`). |

All datasets are publicly downloadable without authentication, enabling fully automated CI execution.

## Methodology Decision & Rationale
| Decision | Rationale |
|----------|-----------|
| **CPU‑first physics simulation** | Box2D runs efficiently on CPU; deterministic with fixed seed; satisfies Principle VI and the compute budget. |
| **Student diffusion model (~10 M params) trained on CPU** | Reduces training time to fit within the 6‑hour free‑tier limit while preserving enough capacity to learn the mapping. |
| **LPIPS computed on CPU** | Library supports CPU inference; no external data needed. |
| **FID computed on CPU with `torch_fidelity`** | Acceptable runtime for ≤ 2 k videos; uses InceptionV3 pretrained weights (CPU‑compatible). |
| **Paired t‑test with Bonferroni correction** | Directly implements SC‑004; multiple metrics (SSIM, LPIPS) trigger correction α = 0.025. |
| **Ablation via parameter sweep** | Vary friction & elasticity (three levels each) → 9 configurations; each re‑generates a 1 k‑sequence subset, keeping total compute ≤ 6 h. |
| **Power analysis** | Prior to testing, compute required sample size for paired t‑test (α = 0.05, power = 0.8, medium effect d = 0.5) using `statsmodels`. Ensures SC‑004 is not under‑powered. |
| **Teacher‑signal quality metric** | Introduce **Trajectory‑Pixel Correlation** (Pearson r between physics velocities and optical‑flow vectors) to directly assess causal signal fidelity (addresses construct validity). |
| **Control neural‑teacher baseline** | Train a neural‑teacher using the same synthetic physics dataset to isolate the effect of teacher type from data distribution (addresses methodology‑fc221ea6). |
| **No GPU offload** | All steps are CPU‑tractable; avoiding GPU ensures reproducibility on free GitHub Actions runners. |

## Expected Outputs
- **Physics dataset**: `data/physics/train/`, `val/`, `test/` with `.mp4` videos and `.npz` trajectories (validated against `contracts/video_sequence.schema.yaml` and `contracts/physics_trajectory.schema.yaml`).  
- **Neural‑teacher baseline (Causal Forcing++)**: checkpoint `outputs/neural_teacher.ckpt` and generated validation videos.  
- **Neural‑teacher baseline on physics data (control)**: checkpoint `outputs/neural_teacher_physics.ckpt`.  
- **Student model**: checkpoint `outputs/student_physics.ckpt`.  
- **Metrics tables**: `outputs/metrics/ssim_psnr_lpips.csv`, `outputs/metrics/fid.csv`, `outputs/metrics/trajectory_pixel_corr.csv`.  
- **Statistical report**: `outputs/statistics/paired_ttest.json`, `outputs/statistics/power_analysis.json`.  
- **Ablation results**: `outputs/ablation/regression.json`, `outputs/ablation/summary.csv`.  
- **Runtime & memory manifest**: `outputs/manifest.json` (hashes, seeds, timestamps, wall‑clock, peak RAM).  

All files conform to the JSON/CSV schemas defined in `contracts/`.

## Compute Feasibility Summary
- **CPU runtime**: Estimated 5.5 h total (1.0 h generation, 0.8 h baseline training on original data, 0.8 h control baseline on physics data, 1.0 h student training, 0.5 h evaluation & analysis, 0.4 h ablation).  
- **Peak RAM**: ≤ 6.8 GB (during diffusion training with checkpointing).  
- **Disk usage**: ≈ 9 GB (videos + checkpoints).  
- **No GPU required**; all libraries are CPU‑compatible.

## Power Analysis (Methodology‑d9b58e20)
Using `statsmodels.stats.power.TTestPower`, a two‑tailed paired t‑test with α = 0.05, power = 0.8, and medium effect size d = 0.5 requires **≈ 34** paired samples. Our test set contains **≥ 2 000** sequences, comfortably exceeding the requirement. The analysis will be computed in task T4.0 and logged.

## Teacher‑Signal Quality Metric (Methodology‑8b671987)
We compute **Trajectory‑Pixel Correlation**:
1. Extract per‑frame velocity vectors from the physics trajectory.
2. Estimate pixel‑level motion via optical flow between consecutive frames.
3. Compute Pearson correlation across the 16 frames.
Higher correlation indicates that the physics trajectory faithfully drives pixel motion, directly measuring causal signal quality.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Training exceeds RAM budget | OOM → failure | Gradient accumulation, activation checkpointing, batch‑size 8. |
| Determinism breach (non‑deterministic Box2D) | Violates FR‑006, SC‑001 | Explicitly set `np.random.seed`, `torch.manual_seed`, and Box2D world seed; verify reproducibility via checksum. |
| Insufficient statistical power | SC‑004 may be inconclusive | Power analysis (T4.0) ensures ≥ 0.8 power; if dataset shrinks, flag results as exploratory per assumptions. |
| LPIPS library heavy on CPU | Runtime blow‑up | Compute LPIPS on the full test set (≈ 2 k sequences) which fits within the budget; if needed, sample a random 10 % subset and report confidence interval. |
| Metric circularity for physics teacher | Violates scientific soundness | Metrics are computed **only on model predictions (student & neural‑teacher) versus ground‑truth frames**; physics‑teacher outputs are not used as a reference, eliminating circularity. |
| Evaluation against mismatched data | Confound | All models are evaluated on the **same held‑out test set** derived from the physics engine; baseline trained on original data is also evaluated on this set. |

---


