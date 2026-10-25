# Research: llmXive Follow-up: Physics-Teacher Distillation

**Feature**: llmXive Follow-up: Physics-Teacher Distillation  
**Branch**: `002-llmxive-physics-teacher-distillation`  
**Date**: 2026-10-25

## Objective
Determine whether a deterministic CPU physics engine (Box2D) can serve as a teacher signal for distilling a lightweight autoregressive diffusion student model, and compare its performance against a **baseline diffusion model** trained on neural‑teacher signals generated from the *same synthetic* data.

## Dataset Strategy

| Role | Source | Access Method | Verified URL | Notes |
|------|--------|--------------|--------------|-------|
| Synthetic physics data (generated internally) | Deterministic Box2D simulation (fixed seed, fixed Δt) | `src/data_generation/generate.py` | – | Produces `.npz` trajectories and `.mp4` videos; no external download required. |
| Neural‑teacher signal generation | Internal `neural_teacher.py` (lightweight CNN) trained on the **same synthetic dataset** | `src/models/neural_teacher.py` | – | Generates frame‑wise predictions that act as teacher signals for the baseline diffusion model. |
| SSIM / PSNR reference implementations | **No verified source** | – | – | Computed on‑the‑fly from model outputs using `scikit-image`. Unit tests confirm analytic identities (e.g., SSIM(x,x)=1). |
| LPIPS implementation | **No verified source** | – | – | Computed on‑the‑fly via the `lpips` library (CPU). Validated against identity case (LPIPS(x,x)=0). |
| FID implementation | **No verified source** | – | – | Computed on‑the‑fly via `torchmetrics` (CPU, low‑resolution Inception). Validated against identity case (FID=0). |
| Original Causal Forcing++ dataset (for FR‑007) | **No verified source** | – | – | No open download exists; therefore the neural‑teacher baseline is trained on the *synthetic* physics dataset (same distribution as the physics‑teacher). This resolves the data‑distribution mismatch highlighted by reviewers. |

All datasets are openly accessible and can be fetched without authentication, ensuring full CI automation.

## Methodology Decision & Rationale

| Decision | Rationale |
|----------|-----------|
| **CPU‑first deterministic Box2D simulation** | Guarantees reproducibility (Principle VI), runs comfortably on the free‑tier runner, and provides exact state vectors required by FR‑001 and FR‑006. |
| **Baseline diffusion model using the **same architecture** as the student** | Eliminates capacity confound identified by reviewers; any performance gap can be attributed to the teacher signal (physics vs. neural). |
| **Student diffusion model (~several M parameters) trained on CPU** | Meets FR‑002 while staying within the 6 h / 7 GB budget via gradient accumulation and activation checkpointing. |
| **LPIPS and FID computed on a sampled subset (≤ 100 sequences)** | Provides reliable estimates while respecting CPU compute limits; sample size is recorded for transparency. |
| **Paired t‑test with Bonferroni correction** | Implements SC‑004 (α = 0.025 after correcting for SSIM & LPIPS). |
| **Power analysis before hypothesis testing** | Guarantees that the paired test is adequately powered (SC‑004). If the test set is smaller than required, results are flagged as exploratory. |
| **Trajectory‑Pixel Correlation (TPC) on student frames** | Provides a direct motion‑fidelity metric that does not rely on the deterministic rendering, avoiding circularity. |
| **No GPU offload** | All steps are CPU‑tractable; this ensures reproducibility on free GitHub Actions runners. |
| **Real‑measurement‑only policy (Anti‑Fabrication Commitment)** | Every metric is computed from actual model outputs; analytic sanity checks are enforced via unit tests. No placeholder values are ever emitted. |

## Expected Outputs
- **Synthetic dataset** (`data/physics/train/`, `val/`, `test/`) containing `.mp4` videos and matching `.npz` trajectories, validated against `contracts/video_sequence.schema.yaml` and `contracts/physics_trajectory.schema.yaml`.
- **Neural‑teacher baseline** checkpoint (`outputs/baseline_diffusion/checkpoint.pt`) and generated validation videos.
- **Student model** checkpoint (`outputs/student_physics/checkpoint.pt`).
- **Metric tables** (`outputs/metrics/ssim_psnr_lpips.csv`, `outputs/metrics/fid.csv`, `outputs/metrics/trajectory_pixel_corr.csv`).
- **Statistical report** (`outputs/statistics/paired_ttest.json`, `outputs/statistics/power_analysis.json`).
- **Ablation results** (`outputs/ablation/regression.json`, `outputs/ablation/summary.csv`).
- **Runtime & memory manifest** (`outputs/manifest.json`) recording hashes, seeds, timestamps, wall‑clock time, and peak RAM for every output file.

All files conform to the JSON/CSV schemas defined in `contracts/`.

## Compute Feasibility Summary
- **CPU runtime**: Planned to stay ≤ 6 h; each phase includes a runtime assertion (T7.4).  
- **Peak RAM**: Must stay ≤ 7 GB (enforced by T7.4).  
- **Disk usage**: ≤ 14 GB (videos + checkpoints); dataset sizes are chosen accordingly.  
- **No GPU required**; all libraries are CPU‑compatible.

## Power Analysis (Methodology)
Using `statsmodels.stats.power.TTestPower`, a two‑tailed paired t‑test with α = 0.05, power = 0.8, and medium effect size (d ≈ 0.5) requires a minimum of **[deferred]** paired samples. Task T4.0 will compute the exact number; if the held‑out test set is smaller, the analysis will be labeled exploratory.

## Teacher‑Signal Quality Metric
**Trajectory‑Pixel Correlation (TPC)**:
1. Extract per‑frame velocity vectors from the physics trajectory.  
2. Compute dense optical flow between consecutive **student‑generated** frames (`opencv` implementation).  
3. Calculate Pearson correlation across the set of frames.  

Higher TPC indicates that the student respects the underlying physics motion, providing an additional fidelity check beyond pixel‑wise losses.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| OOM due to batch size | Run failure | Gradient accumulation, activation checkpointing, small batch size (≤ 8). |
| Non‑deterministic Box2D output | Violates FR‑006, SC‑001 | Explicitly set Box2D world seed; checksum reproducibility check on a subset. |
| Insufficient statistical power | Inconclusive SC‑004 | Pre‑run power analysis (T4.0); flag exploratory if under‑powered. |
| LPIPS CPU cost | Excess runtime | Compute LPIPS on a fixed‑seed random sample of **≤ 100** test sequences; report sample size. |
| FID CPU cost | Excess runtime / RAM | Compute FID on the same sampled subset using low‑resolution Inception features; report sample size. |
| Metric circularity | Invalid claim | TPC computed on *student* frames, not on deterministic rendering. |
| Mismatched data distributions | Confounded comparison | Baseline trained on the same synthetic dataset (addressed). |
| Fabricated numbers | Integrity breach (prior‑round issue) | Anti‑Fabrication Commitment: all numbers are real measurements; analytic sanity tests; loud failure on missing data. |

---


