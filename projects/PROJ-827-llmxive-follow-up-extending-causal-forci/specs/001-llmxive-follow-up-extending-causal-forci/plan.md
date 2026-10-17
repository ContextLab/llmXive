# Implementation Plan: llmXive Follow-up: Physics-Teacher Distillation

**Branch**: `002-llmxive-physics-teacher-distillation` | **Date**: 2026-10-17 | **Spec**: [/specs/002-llmxive-physics-teacher-distillation/spec.md](../specs/002-llmxive-physics-teacher-distillation/spec.md)  
**Input**: Feature specification from `/specs/002-llmxive-physics-teacher-distillation/spec.md`

## Summary
The core hypothesis is that a deterministic, CPU‑only physics engine can serve as a “teacher” signal for distilling a lightweight autoregressive diffusion student model (~10 M parameters). We will (1) generate synthetic multi‑frame video sequences together with exact state‑vector trajectories using Box2D, (2) train a neural‑teacher baseline on the original Causal Forcing++ dataset **and** a control baseline on the same synthetic physics data, (3) train the student model on the physics‑teacher data, (4) evaluate both models on a shared held‑out test set using SSIM, PSNR, LPIPS, FID, and the new Trajectory‑Pixel Correlation metric, (5) perform paired statistical tests with a priori power analysis and Bonferroni correction, (6) conduct an ablation study over physics parameters, (7) monitor runtime and memory to satisfy SC‑005, and (8) produce reproducible artifacts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pybox2d`, `torch==2.2.0`, `torchvision`, `diffusers`, `numpy`, `pandas`, `scikit-image`, `lpips`, `torchmetrics`, `scipy`, `statsmodels`, `tqdm`, `hydra-core`, `torch_fidelity`  
- **Storage**: Files on disk (`data/`, `outputs/`) – no external DB.  
- **Testing**: `pytest`, `pytest-contracts` (schema validation)  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Performance Goals**: Full pipeline ≤ 6 h wall‑clock, peak RAM ≤ 7 GB, CPU‑only (no CUDA).  
- **Constraints**: Deterministic physics (Principle VI), reproducibility (Principle I), data hygiene (Principle III).  
- **Scale/Scope**: Generate a few thousand training sequences, along with comparable numbers of validation and test sequences.; student model ≈ a few M parameters; training ≤ 6 epochs with gradient accumulation & activation checkpointing.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All random seeds are fixed in `code/`, data is downloaded from canonical URLs, and every script is runnable end‑to‑end on a fresh runner. |
| II. Verified Accuracy | All external citations (Box2D, SSIM/PSNR datasets, FID datasets) are drawn from the verified URLs list. |
| III. Data Hygiene | Raw Box2D metadata is checksummed; derived videos and trajectories are written to new files with provenance metadata. |
| IV. Single Source of Truth | Every figure/table is generated directly from `outputs/` files; no manual transcription. |
| V. Versioning Discipline | All artifacts are hashed; `state/projects/PROJ-827-...yaml` is updated automatically by the pipeline. |
| VI. Deterministic Physics Fidelity | Physics engine runs with a fixed seed and fixed time‑step; trajectories are stored alongside rendered frames. |
| VII. Generative Richness vs. Physical Plausibility Trade‑off | Metrics (SSIM, PSNR, LPIPS, FID, Trajectory‑Pixel Correlation) and paired t‑tests are computed as required. |

## Project Structure
```text
specs/002-llmxive-physics-teacher-distillation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── physics_trajectory.schema.yaml
│   ├── evaluation_results.schema.yaml
│   └── video_sequence.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

```text
src/
├── data_generation/
│   ├── generate.py          # Box2D simulation & rendering
│   └── utils.py
├── models/
│   ├── student_diffusion.py # 2‑step autoregressive diffusion (~10 M params)
│   └── neural_teacher.py    # baseline architecture
├── evaluation/
│   ├── metrics.py           # SSIM, PSNR, LPIPS, FID, Trajectory‑Pixel Correlation
│   └── statistical.py       # power analysis, paired t‑test, regression
├── ablation/
│   └── run_ablation.py
└── cli/
    └── main.py              # entry point orchestrating the pipeline
tests/
├── contract/
│   └── test_schemas.py
└── unit/
    └── test_*.py
```

## Phase & Task Mapping (covers all FR/SC)

| Phase | Task ID | Description | FR/SC addressed |
|-------|---------|-------------|-----------------|
| **0 – Setup** | T0.1 | Create virtualenv, install pinned `requirements.txt` | – |
| **1 – Physics Teacher Data Generation** | T1.1 | Implement deterministic Box2D simulation (fixed seed, fixed Δt) | FR‑001, FR‑006, SC‑001 |
| | T1.2 | Render 16‑frame video per trajectory; store as `.mp4` and `.npz` state vectors; validate against `contracts/video_sequence.schema.yaml` | FR‑001, FR‑006 |
| | T1.3 | Verify no NaNs, log and discard any corrupted sequences | FR‑006 |
| **2 – Neural‑Teacher Baseline** | T2.1 | Load original Causal Forcing++ dataset (public HuggingFace) | FR‑007 |
| | T2.2 | Train identical diffusion model on that dataset (CPU‑only) | FR‑007, SC‑008 |
| | T2.3 | Save baseline checkpoint and generate validation videos | FR‑007 |
| | **T2.4** | **Control baseline:** Train the same neural‑teacher architecture on the synthetic physics dataset (identical data distribution to physics‑teacher) | Addresses methodology‑fc221ea6 confound; FR‑007 |
| **3 – Student Model Training (Physics Teacher)** | T3.1 | Prepare training loader that feeds current frame + trajectory → next frame | FR‑002 |
| | T3.2 | Train student model (~10 M params) for ≤ 6 epochs with batch‑size 8, gradient accumulation, activation checkpointing | FR‑002, SC‑002 |
| | T3.3 | Early‑stop if validation MSE ≤ 0.05; otherwise apply higher LR schedule (edge‑case handling) | FR‑002, SC‑002 |
| | T3.4 | Profile runtime and peak RAM; assert ≤ 6 h and ≤ 7 GB (SC‑005) | SC‑005 |
| **4 – Evaluation & Metric Computation** | T4.0 | **Power analysis:** compute required sample size for paired t‑test (α=0.05, power = 0.8, d=0.5) and verify dataset meets it | methodology‑d9b58e20, SC‑004 |
| | T4.1 | Compute SSIM & PSNR on **model predictions vs ground‑truth frames** (shared held‑out test set) | FR‑004, SC‑003 |
| | T4.2 | Compute LPIPS (CPU) on the same test set | FR‑004, SC‑003 |
| | T4.3 | Compute FID (CPU) between physics‑teacher generated videos and neural‑teacher baseline videos | FR‑009, SC‑007, SC‑009 |
| | **T4.4** | Compute **Trajectory‑Pixel Correlation** (Pearson r between physics velocities and optical‑flow vectors) as a direct teacher‑signal quality metric | methodology‑8b671987 |
| **5 – Statistical Analysis** | T5.1 | Perform paired t‑test on SSIM & LPIPS scores (Bonferroni‑adjusted α = 0.025) | FR‑005, SC‑004 |
| | T5.2 | Report p‑values, effect sizes, significance decisions (SC‑004) | SC‑004 |
| **6 – Ablation Study** | T6.1 | Vary physics parameters (friction ∈ {0.2,0.5,0.8}, elasticity ∈ {0.1,0.5,0.9}) and regenerate a subset of data | FR‑008 |
| | T6.2 | For each setting compute LPIPS, FID, and Trajectory‑Pixel Correlation; run linear regression vs parameter value | FR‑008, SC‑006 |
| | T6.3 | Summarise regression results (Pearson r, p‑value) in a table | SC‑006 |
| **7 – Reporting & Artifacts** | T7.1 | Assemble metric tables, statistical summary, ablation plots; write JSON/CSV outputs conforming to `contracts/` schemas | All SCs |
| | T7.2 | Verify reproducibility: re‑run the full pipeline on a fresh runner, compare hashes | Principle I, II |
| | T7.3 | Clean up intermediate files, checksum final artifacts, update `state/projects/...yaml` | Principle III, V |
| | **T7.4** | **Runtime & Memory Check:** Assert total wall‑clock ≤ 6 h and peak RAM ≤ 7 GB; fail the run if limits exceeded (updates manifest) | SC‑005 |
| | T7.5 | **Contract Validation:** Run `pytest -m contract` to ensure all schema contracts (including new video_sequence) pass | Data‑model consistency |

All tasks are ordered to respect data dependencies (download → generate → train → evaluate → analyze → report) and stay within the 6‑hour, 7 GB RAM budget on a free GitHub Actions runner. No GPU‑only libraries are used; all computation is CPU‑first.

---

