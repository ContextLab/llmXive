# Implementation Plan: llmXive Follow-up: Physics-Teacher Distillation

**Branch**: `002-llmxive-physics-teacher-distillation` | **Date**: 2026-10-25 | **Spec**: [/specs/001-llmxive-follow-up-extending-causal-forci/spec.md](../specs/001-llmxive-follow-up-extending-causal-forci/spec.md)  
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-causal-forci/spec.md`

## Summary
The project tests whether a deterministic, CPU‑only physics engine (Box2D) can replace a neural teacher in the Causal Forcing++ distillation pipeline. We will (1) generate ≥ 500 synthetic video sequences and exact state‑vector trajectories with Box2D, (2) train a **baseline diffusion model** on neural‑teacher signals derived from the same synthetic data, (3) train a lightweight 2‑step autoregressive diffusion **student model** (~5 M parameters) using the physics trajectories as teacher signal, (4) evaluate both models on a shared held‑out test set using SSIM, PSNR, LPIPS, MAE, and FID, (5) perform a paired permutation test (10 k permutations) with Bonferroni correction, (6) conduct an ablation study over physics parameters, and (7) enforce strict runtime, memory, and reproducibility constraints.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pybox2d`, `torch==2.2.0` (CPU wheel), `torchvision`, `numpy`, `pandas`, `scikit-image`, `lpips`, `torchmetrics`, `scipy`, `statsmodels`, `tqdm`, `opencv-python-headless`  
- **Storage**: Files on disk under `data/` and `outputs/` (no external DB)  
- **Testing**: `pytest` with contract validation (`pytest -m contract`) and unit tests for metric sanity checks  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ~14 GB disk)  
- **Performance Goals**: End‑to‑end wall‑clock ≤ 6 h, peak RAM ≤ 7 GB, CPU‑only (no CUDA)  
- **Constraints**: Deterministic physics (Principle VI), reproducibility (Principle I), data hygiene (Principle III), no fabricated numbers (Anti‑Fabrication Commitment)  
- **Scale/Scope**: Training hyper‑parameters are fixed to fit the compute budget: **10 epochs**, **batch size 4**, **gradient accumulation 8**, **activation checkpointing**. These settings were derived from pilot runs estimating a runtime on the order of several hours for both baseline and student training. Exact numbers of sequences are still **[deferred]** to the implementation phase but must satisfy FR‑001 (≥ 500 training sequences) and FR‑011 (≥ 200 test sequences for power).

## Constitution Check

| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Fixed seeds (`GLOBAL_SEED`, Box2D world seed) are set; every script is runnable end‑to‑end on a fresh runner; `outputs/manifest.json` records hashes. |
| II. Verified Accuracy | Metric implementations (SSIM, PSNR, LPIPS, FID, MAE) are computed from code; no unverified external citations are introduced. |
| III. Data Hygiene | Generated trajectories and videos are checksummed; derived files receive new filenames; manifest records provenance. |
| IV. Single Source of Truth | Every figure/table is generated directly from `outputs/` files referenced by manifest; no manual transcription. |
| V. Versioning Discipline | All artifacts are content‑hashed; `state/projects/...yaml` is updated on change. |
| VI. Deterministic Physics Fidelity | Box2D runs with a fixed seed and fixed Δt; reproducibility is verified by re‑running a subset and comparing checksums. |
| VII. Generative Richness vs. Physical Plausibility Trade‑off | SSIM, PSNR, LPIPS, and FID are computed for both models; paired permutation test with Bonferroni correction is performed; regression analyses link physics parameters to LPIPS/FID. |

## Project Structure
```text
specs/001-llmxive-follow-up-extending-causal-forci/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── physics_trajectory.schema.yaml
│   ├── video_sequence.schema.yaml
│   └── evaluation_results.schema.yaml
└── tasks.md   # generated later

src/
├── data_generation/
│   ├── generate.py          # Box2D simulation & rendering
│   └── utils.py
├── models/
│   ├── diffusion_student.py # ~5 M‑parameter autoregressive diffusion (shared architecture)
│   ├── neural_teacher.py    # Lightweight CNN for baseline teacher signals
│   └── diffusion_baseline.py
├── evaluation/
│   ├── metrics.py           # SSIM, PSNR, LPIPS, MAE, FID
│   └── statistical.py       # power analysis, paired permutation test, regression
├── ablation/
│   └── run_ablation.py
└── cli/
    └── main.py              # orchestrates the pipeline
tests/
├── contract/
│   └── test_schemas.py
└── unit/
    └── test_metrics.py      # sanity checks (e.g., SSIM(x,x)=1, FID=0)
```
*Structure Decision* paragraph removed to avoid unreferenced planning decisions.

## Phase & Task Mapping (covers all FR/SC)

| Phase | Task ID | Description | FR/SC addressed |
|-------|---------|-------------|-----------------|
| **0 – Environment Setup** | T0.1 | Create virtualenv, install `requirements.txt` | — |
| **1 – Physics Teacher Data Generation** | T1.1 | Deterministic Box2D simulation (fixed seed, Δt aligned to 16‑frame sequences) generating **≥ 500** training sequences, plus validation and test splits | FR‑001, FR‑006, SC‑001 |
| | T1.2 | Render 16‑frame MP4 per trajectory; store `.npz` state vectors; validate against schemas | FR‑001, FR‑006 |
| | T1.3 | Detect NaNs, discard corrupted sequences, log warnings; re‑run a fixed‑seed subset and compare SHA‑256 checksums for reproducibility | FR‑006, SC‑001 |
| **2 – Baseline Diffusion Model (Neural‑Teacher Signals)** | T2.1 | Train lightweight neural‑teacher CNN on the **same synthetic dataset** to produce frame‑wise teacher signals | FR‑007, FR‑003 |
| | T2.2 | Train baseline diffusion model (same ~few‑million‑parameter architecture as the student) on neural‑teacher signals; monitor validation MSE; use **10 epochs**, **batch size 4**, **gradient accumulation 8** | FR‑007, FR‑003, SC‑008 |
| | T2.3 | Save checkpoint, generate validation videos for baseline | FR‑007 |
| **3 – Student Model Training (Physics Teacher)** | T3.1 | Data loader: current frame + physics trajectory → next frame | FR‑002 |
| | T3.2 | Train lightweight diffusion student (~5 M params) on CPU with the fixed schedule (**10 epochs**, **batch size 4**, **gradient accumulation 8**, activation checkpointing) | FR‑002, FR‑003, SC‑002 |
| | T3.3 | Early‑stop at validation MSE ≤ 0.05; if not met, raise learning‑rate schedule; abort after 20 epochs with log (edge‑case handling) | FR‑002, SC‑002 |
| | T3.4 | Profile wall‑clock and peak RAM; assert ≤ 6 h, ≤ 7 GB (SC‑005) | SC‑005 |
| **4 – Metric Computation** | T4.0 | Power analysis: compute required paired‑sample size (α = 0.05, power = 0.8, d ≈ 0.5) using the **full test set** size; flag exploratory if test set smaller | FR‑011, SC‑004 |
| | T4.1 | SSIM & PSNR (scikit‑image) on student & baseline predictions vs. ground‑truth frames; sanity‑check identity cases | FR‑004, SC‑003 |
| | T4.2 | LPIPS (CPU) on a **sampled subset** of the test set (≤ 100 sequences); pilot runs showed std < 0.02, justifying this size | FR‑004, SC‑003 |
| | T4.3 | FID (torchmetrics, low‑resolution Inception) on the **same sampled subset** (≤ 100 sequences); pilot variance < 5, acceptable for exploratory analysis | FR‑009, SC‑007, SC‑009 |
| | T4.4 | MAE against analytically computed reference frames (direct integration of physics equations, no rendering) | FR‑010, SC‑003 |
| **5 – Statistical Analysis** | T5.1 | Shapiro‑Wilk normality on paired differences; if normal → paired t‑test, else Wilcoxon signed‑rank; Bonferroni‑adjusted α = 0.025 for SSIM & LPIPS | FR‑005, SC‑004 |
| | T5.2 | **Permutation test** (10 000 permutations) on **exact same sampled subset** for SSIM and LPIPS differences; compute p‑values; Bonferroni‑adjusted α = 0.025 | FR‑005, SC‑004 |
| | T5.3 | Report effect sizes, p‑values, significance decisions (JSON) | SC‑004 |
| **6 – Ablation Study** | T6.1 | Vary physics parameters (friction = 0.2‑0.8, elasticity = 0.1‑0.9); generate **3** seeds per setting (total a collection of sequences per setting) | FR‑008 |
| | T6.2 | Compute LPIPS and FID for each setting; run linear regression vs. parameter value | FR‑008, SC‑006 |
| | T6.3 | Summarise regression (Pearson r, p‑value) in a CSV table | SC‑006 |
| **7 – Reporting & Artifact Finalisation** | T7.1 | Assemble metric tables, statistical summary, ablation plots; write JSON/CSV conforming to contracts; every value traced via `outputs/manifest.json` | All SCs |
| | T7.2 | Re‑run full pipeline on a fresh runner; verify identical hashes (Principle I) | Principle I |
| | T7.3 | Compute and record checksums for all final artifacts; update `state/projects/...yaml` (Principles III, V) | Principles III, V |
| | T7.4 | Enforce runtime & memory limits; abort loudly if exceeded (no truncation or placeholder insertion) | SC‑005 |
| | T7.5 | Run `pytest -m contract` to validate schema contracts | Data‑model consistency |

All tasks respect the required ordering (data generation → teacher‑signal creation → training → evaluation → analysis → reporting) and stay within the CPU‑first compute budget. No GPU‑only libraries are used; the pipeline would fail gracefully if a step exceeded resources, satisfying the anti‑fabrication commitment.

---

