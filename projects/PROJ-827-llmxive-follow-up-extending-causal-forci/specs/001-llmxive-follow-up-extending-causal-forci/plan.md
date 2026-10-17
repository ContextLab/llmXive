# Implementation Plan: llmXive Follow-up: Physics-Teacher Distillation

**Branch**: `002-llmxive-physics-teacher-distillation` | **Date**: 2026-10-24 (revised in place) | **Spec**: [/specs/001-llmxive-follow-up-extending-causal-forci/spec.md](../specs/001-llmxive-follow-up-extending-causal-forci/spec.md)

## Summary
The core hypothesis is that a deterministic, CPU‑only physics engine can serve as a "teacher" signal for distilling a lightweight autoregressive diffusion student model (≈ 50 M parameters, per FR‑002). We will (1) generate synthetic multi‑frame video sequences together with exact state‑vector trajectories using Box2D, (2) train a **neural‑teacher baseline** (a ConvLSTM video‑prediction model) on the **same synthetic physics dataset** as the physics‑teacher model, (3) train the student model on the physics‑teacher data, (4) evaluate both models on a shared held‑out test set using SSIM, PSNR, LPIPS, and **FID** (interpreted as distributional similarity), (5) perform paired statistical tests with a priori power analysis and Bonferroni correction, (6) conduct an ablation study over physics parameters with sufficient levels and replicates, (7) monitor runtime and memory to satisfy SC‑005, and (8) produce reproducible artifacts.

**Scope Note (data‑availability gap, surfaced per planning rules)**: FR‑007 requires training the baseline on the original Causal Forcing++ dataset. **No verified, openly downloadable source for that dataset exists** in the verified‑datasets block, and access‑gated data cannot be fetched by the CI runner. Consequently, the neural‑teacher baseline is trained on the **same synthetic physics dataset** as the physics‑teacher model. This isolates the teacher‑type comparison (physics vs. neural) on a shared data distribution, which remains scientifically meaningful. The original‑dataset arm of FR‑007 is therefore **flagged for spec revision** rather than fabricated.

## Anti‑Fabrication Commitment (addresses kicked‑back concern)
The prior round flagged a self‑declared *fabricated metric* placeholder in a tasks document. This plan and every artifact it produces are bound to the following rules, which the Implementer Agent **MUST** carry into `tasks.md` verbatim:

- **Every reported number is a REAL measurement** produced by executing the code in `src/` on real generated data. No placeholder, simulated, hardcoded, or `random.*`‑derived metric values may appear in any output file, table, figure, or report.
- If a computation cannot be completed within the compute budget, the run **fails loudly** (non‑zero exit, logged error) — it never substitutes a synthetic or approximate stand‑in value.
- Metric implementations are validated against **analytic ground truths** (e.g., SSIM of an image with itself = 1.0; PSNR of identical images = infinity, capped and reported as such; FID of a set with itself = 0) before being applied to model outputs. These validation checks are tests, not reported results.
- `outputs/manifest.json` records, for every reported metric file, the producing script, input checksums, seed, and wall‑clock time, so every number traces to one code block and one data row (Constitution Principle IV).
- **All generated task specifications (e.g., `tasks.md`) will be produced without any fabricated or placeholder metric values.** The pipeline explicitly enforces this rule; any attempt to insert a placeholder will cause the run to abort with an error, ensuring that only real measurements appear in the final artifacts.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pybox2d`, `torch==2.2.0` (CPU wheel), `torchvision`, `numpy`, `pandas`, `scikit-image`, `lpips`, `torchmetrics`, `scipy`, `statsmodels`, `tqdm`, `opencv-python-headless` (optical flow), `pytest`
- **Storage**: Files on disk (`data/`, `outputs/`) – no external DB.
- **Testing**: `pytest` (contract schema validation via `jsonschema`)
- **Target Platform**: Linux (GitHub Actions free‑tier runner, 2 CPU cores)
- **Performance Goals**: Full pipeline ≤ 6 h wall‑clock, peak RAM ≤ 7 GB, CPU‑only (no CUDA) — SC‑005.
- **Constraints**: Deterministic physics (Principle VI), reproducibility (Principle I), data hygiene (Principle III), no fabricated results (see Anti‑Fabrication Commitment).
- **Scale/Scope**: Number of train/val/test sequences is **[deferred]** to implementation, chosen to fit the 6 h / 7 GB budget; student model ≈ tens of millions of parameters trained at reduced spatial resolution with gradient accumulation and activation checkpointing; epochs **[deferred]**.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All random seeds are fixed in `code/`, data is generated from a deterministic engine with a pinned seed, and every script is runnable end‑to‑end on a fresh runner. |
| II. Verified Accuracy | All external dataset citations are drawn ONLY from the verified URLs list; the original Causal Forcing++ dataset has no verified source and is therefore not cited or used. |
| III. Data Hygiene | Generated Box2D metadata and trajectories are checksummed; derived videos and metrics are written to new files with provenance metadata in `outputs/manifest.json`. |
| IV. Single Source of Truth | Every figure/table is generated directly from `outputs/` files traced via the manifest; no manual transcription; no placeholder values. |
| V. Versioning Discipline | All artifacts are hashed; `state/projects/PROJ-827-...yaml` is updated with `updated_at` on every artifact change. |
| VI. Deterministic Physics Fidelity | Physics engine runs with a fixed seed and fixed time‑step; trajectories are stored alongside rendered frames; reproducibility verified by checksum comparison on a re‑run subset. |
| VII. Generative Richness vs. Physical Plausibility Trade‑off | SSIM, PSNR, LPIPS, FID, and **Trajectory‑Pixel Correlation** (on student‑generated frames) are computed for both models on the same held‑out test set, with paired t‑tests (Bonferroni‑adjusted α = 0.025). |

## Project Structure
```text
specs/001-llmxive-follow-up-extending-causal-forci/
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
│   ├── student_diffusion.py # 2‑step autoregressive diffusion (~50M params, per FR‑002)
│   └── neural_teacher.py    # ConvLSTM video‑prediction baseline (neural teacher)
├── evaluation/
│   ├── metrics.py           # SSIM, PSNR, LPIPS, FID, Trajectory‑Pixel Correlation
│   └── statistical.py       # power analysis, paired t‑test, regression, normality check
├── ablation/
│   └── run_ablation.py
└── cli/
    └── main.py              # entry point orchestrating the pipeline
tests/
├── contract/
│   └── test_schemas.py
└── unit/
    └── test_*.py            # includes analytic metric ground‑truth tests (anti‑fabrication)
```

**Structure Decision**: single‑project layout (`src/` + `tests/`), matching the repository's existing Python package convention; no scaffolding beyond what the research question requires.

## Phase & Task Mapping (covers all FR/SC)

| Phase | Task ID | Description | FR/SC addressed |
|-------|---------|-------------|-----------------|
| **0 – Setup** | T0.1 | Create virtualenv, install pinned `requirements.txt` | – |
| **1 – Physics Teacher Data Generation** | T1.1 | Implement deterministic Box2D simulation (fixed seed, fixed Δt aligned to the 16‑frame duration) | FR‑001, FR‑006, SC‑001 |
| | T1.2 | Render a fixed‑length video per trajectory; store as `.mp4` and `.npz` state vectors; validate against `contracts/video_sequence.schema.yaml` and `contracts/physics_trajectory.schema.yaml` | FR‑001, FR‑006 |
| | T1.3 | Verify no NaNs, log and discard any corrupted sequences; verify determinism by re‑running a fixed‑seed subset and comparing checksums | FR‑006, SC‑001 |
| **2 – Neural‑Teacher Baseline** | T2.1 | Construct the neural‑teacher baseline: a ConvLSTM video‑prediction model trained on the **same synthetic physics dataset** using raw frames as targets (no explicit trajectory input). | FR‑007 (re‑interpreted), FR‑003 |
| | T2.2 | Train the baseline (CPU‑only), monitoring validation MSE | FR‑007, FR‑003, SC‑008 |
| | T2.3 | Save baseline checkpoint and generate validation videos | FR‑007 |
| **3 – Student Model Training (Physics Teacher)** | T3.1 | Prepare training loader that feeds current frame + physics trajectory → next frame | FR‑002 |
| | T3.2 | Train student model (≈ 50 M params per FR‑002) on CPU with gradient accumulation and activation checkpointing; epochs **[deferred]** | FR‑002, FR‑003, SC‑002 |
| | T3.3 | Early‑stop if validation MSE ≤ 0.05; otherwise apply higher LR schedule for the remaining epochs; abort and log if convergence still fails | FR‑002, SC‑002 |
| | T3.4 | Profile runtime and peak RAM; assert ≤ 6 h and ≤ 7 GB | SC‑005 |
| **4 – Evaluation & Metric Computation** | T4.0 | **Power analysis:** compute required sample size for paired t‑test (α = 0.05, power = 0.8, d = 0.5) with `statsmodels` and verify the test set meets it; if not, flag results as exploratory | SC‑004 |
| | T4.1 | Compute SSIM & PSNR on model predictions vs ground‑truth frames (shared held‑out test set), using `scikit-image`; validate implementations against analytic ground truths first | FR‑004, SC‑003 |
| | T4.2 | Compute LPIPS (CPU, `lpips` library) on the same test set | FR‑004, SC‑003 |
| | T4.3 | Compute **FID** (CPU, `torchmetrics` with InceptionV3 weights) between physics‑teacher generated videos and neural‑teacher baseline videos. **Interpretation:** measures distributional similarity, not generative richness; reported as a descriptive statistic with a small‑sample caveat. | FR‑009, SC‑007, SC‑009 |
| | T4.4 | Compute **Trajectory‑Pixel Correlation (TPC)** on **student‑generated** frames: extract per‑frame velocities from the physics trajectory, compute optical flow on the student’s predicted frames, and calculate Pearson r. This serves as a fidelity check of motion consistency. | Supports Principle VI/VII |
| **5 – Statistical Analysis** | T5.1 | Perform Shapiro‑Wilk normality test on paired differences; if normal, run paired t‑test on SSIM & LPIPS scores (Bonferroni‑adjusted α = 0.025); otherwise use Wilcoxon signed‑rank test. Report effect sizes and p‑values. | FR‑005, SC‑004 |
| | T5.2 | Report p‑values, effect sizes, significance decisions | SC‑004 |
| **6 – Ablation Study** | T6.1 | Vary physics parameters (friction coefficient = 0.2, 0.35, 0.5, 0.65, 0.8; elasticity = 0.1, 0.3, 0.5, 0.7, 0.9) and regenerate **3 random seeds** per configuration (total 15 sequences per setting). | FR‑008 |
| | T6.2 | For each setting compute LPIPS, FID, and Trajectory‑Pixel Correlation; run linear regression vs parameter value | FR‑008, SC‑006 |
| | T6.3 | Summarise regression results (Pearson r, p‑value) in a table | SC‑006 |
| **7 – Reporting & Artifacts** | T7.1 | Assemble metric tables, statistical summary, ablation plots; write JSON/CSV outputs conforming to `contracts/` schemas; **every value must be a real measurement traced via `outputs/manifest.json`** (Anti‑Fabrication Commitment) | All SCs |
| | T7.2 | Verify reproducibility: re‑run the full pipeline on a fresh runner, compare hashes | Principle I |
| | T7.3 | Checksum final artifacts, update `state/projects/...yaml` | Principle III, V |
| | T7.4 | **Runtime & Memory Check:** Assert total wall‑clock ≤ 6 h and peak RAM ≤ 7 GB; fail the run if limits exceeded (updates manifest) | SC‑005 |
| | T7.5 | **Contract Validation:** Run `pytest -m contract` to ensure all schema contracts pass | Data‑model consistency |

All tasks are ordered to respect data dependencies (generate → train → evaluate → analyze → report) and stay within the 6‑hour, 7 GB RAM budget on a free GitHub Actions runner. No GPU‑only libraries are used; all computation is CPU‑first.

---



## projects/PROJ-827-llmxive-follow-up-extending-causal-forci/specs/001-llmxive-follow-up-extending-causal-forci/research.md
# Research: llmXive Follow-up: Physics-Teacher Distillation

**Feature**: llmXive Follow-up: Physics-Teacher Distillation  
**Branch**: `002-llmxive-physics-teacher-distillation`  
**Date**: 2026-10-24 (revised in place)

## Objective
Validate whether a deterministic CPU physics engine (Box2D) can replace a neural teacher in the Causal Forcing++ distillation pipeline, while meeting the success criteria (SC‑001 – SC‑009).

## Dataset Strategy

| Role | Source | Access Method | Verified URL | Notes |
|------|--------|--------------|--------------|-------|
| Synthetic physics data (generated internally) | Generated by deterministic Box2D simulation using a fixed seed and fixed Δt | Programmatic generation via `src/data_generation/generate.py` | – | Provides initial state vectors, world parameters, and rendered short‑duration video sequences. No external download required. |
| SSIM / PSNR / LPIPS / FID reference values | **No verified source** | – | – | All metrics are computed on‑the‑fly from real model outputs using `scikit-image` (SSIM, PSNR), the `lpips` library (LPIPS), and `torchmetrics` (FID). Metric implementations are validated against analytic ground truths (identity cases) as unit tests, NOT against external pre‑computed score files. |
| Original Causal Forcing++ dataset (for FR‑007) | **No verified source** | – | – | **Explicit gap:** no open, directly‑downloadable source for the original dataset exists in the verified block. The neural‑teacher baseline is therefore trained on the **same synthetic physics dataset** (teacher‑type comparison). The original‑dataset comparison in FR‑007 is flagged for spec revision; no fabricated mirror is used. |

All used datasets are publicly downloadable without authentication, enabling fully automated CI execution.

## Methodology Decision & Rationale
| Decision | Rationale |
|----------|-----------|
| **CPU‑first physics simulation** | Box2D runs efficiently on CPU; deterministic with fixed seed; satisfies Principle VI and the compute budget. |
| **Neural‑teacher baseline** | Implemented as a ConvLSTM video‑prediction model trained on the synthetic physics dataset using raw frames as targets (no explicit trajectory input). This provides a neural teacher signal that shares the same underlying data distribution but encodes it via learned parameters, enabling a clean teacher‑type contrast. |
| **Student diffusion model (≈ tens of millions of parameters per FR‑002) trained on CPU** | Fits within the 6‑hour free‑tier limit at reduced spatial resolution with gradient accumulation and activation checkpointing, while preserving the architecture scale the spec requires. |
| **LPIPS computed on CPU** | Library supports CPU inference; no external data needed. |
| **FID computed on CPU with `torchmetrics`** | Acceptable runtime for the test‑set size; **interpreted as a descriptive measure of distributional similarity** between the two generated video sets, not as a richness metric. A small‑sample caveat is noted. |
| **Paired t‑test with Bonferroni correction** | Directly implements SC‑004; two metrics (SSIM, LPIPS) trigger correction to α = 0.025. |
| **Power analysis** | Prior to testing, compute required sample size for paired t‑test (α = 0.05, power = 0.8, medium effect d ≈ 0.5) using `statsmodels`. Ensures SC‑004 is not under‑powered; if the test set is smaller than required, results are flagged exploratory. |
| **Trajectory‑Pixel Correlation (TPC) on student frames** | Compute Pearson r between physics velocities and optical‑flow vectors derived **from the student‑generated frames**. This serves as a genuine fidelity check of motion consistency, avoiding circularity. |
| **Neural‑teacher baseline on the same physics data** | Isolates the effect of teacher type from data distribution. The original Causal Forcing++ dataset has no verified open source, so the original‑dataset arm of FR‑007 cannot be executed; this is stated rather than worked around with unverifiable data. |
| **No GPU offload** | All steps are CPU‑tractable; avoiding GPU ensures reproducibility on free GitHub Actions runners. |
| **Real‑measurement‑only policy** | Every reported metric is a real computation on real generated data; metric code is validated against analytic identity cases (SSIM(x,x)=1, FID(S,S)=0) as tests. No placeholder or simulated values (addresses the fabrication concern from the prior round). |

## Expected Outputs
- **Physics dataset**: `data/physics/train/`, `val/`, `test/` with `.mp4` videos and `.npz` trajectories (validated against `contracts/video_sequence.schema.yaml` and `contracts/physics_trajectory.schema.yaml`).
- **Neural‑teacher baseline (trained on physics data)**: checkpoint `outputs/neural_teacher.ckpt` and generated validation videos.
- **Student model**: checkpoint `outputs/student_physics.ckpt`.
- **Metrics tables**: `outputs/metrics/ssim_psnr_lpips.csv`, `outputs/metrics/fid.csv`, `outputs/metrics/trajectory_pixel_corr.csv` — all real measurements.
- **Statistical report**: `outputs/statistics/paired_ttest.json`, `outputs/statistics/power_analysis.json`.
- **Ablation results**: `outputs/ablation/regression.json`, `outputs/ablation/summary.csv`.
- **Runtime & memory manifest**: `outputs/manifest.json` (hashes, seeds, timestamps, wall‑clock, peak RAM, producing‑script provenance for every metric file).

All files conform to the JSON/CSV schemas defined in `contracts/`.

## Compute Feasibility Summary
- **CPU runtime**: Budgeted within the 6 h limit; exact split across generation, training, evaluation, and ablation is **[deferred]** and enforced by the T7.4 runtime assertion (the run fails loudly if exceeded — no truncation or substitution).
- **Peak RAM**: Must stay ≤ 7 GB (enforced by the T7.4 memory assertion).
- **Disk usage**: Must stay ≤ ~14 GB (videos + checkpoints; dataset sizes **[deferred]**).
- **No GPU required**; all libraries are CPU‑compatible.

## Power Analysis (Methodology)
Using `statsmodels.stats.power.TTestPower`, a two‑tailed paired t‑test with α = 0.05, power = 0.8, and medium effect size d ≈ 0.5 requires a minimum paired‑sample size that is computed at task T4.0 (numeric value **[deferred]** to execution). If the held‑out test set is smaller than the requirement, results are interpreted as exploratory per the spec's statistical‑power assumption.

## Teacher‑Signal Quality Metric
We compute **Trajectory‑Pixel Correlation (TPC)**:
1. Extract per‑frame velocity vectors from the physics trajectory.
2. Estimate pixel‑level motion via optical flow between consecutive **student‑generated** frames.
3. Compute Pearson correlation across the 16 frames.
Higher correlation indicates that the student model respects the underlying physics motion, providing a direct fidelity check beyond pixel‑wise losses.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Training exceeds RAM budget | OOM → failure | Gradient accumulation, activation checkpointing, small batch size. |
| Determinism breach (non‑deterministic Box2D) | Violates FR‑006, SC‑001 | Explicitly set `np.random.seed`, `torch.manual_seed`, and Box2D world seed; verify reproducibility via checksum comparison on a re‑run subset. |
| Insufficient statistical power | SC‑004 may be inconclusive | Power analysis (T4.0); if the test set is under‑sized, flag results as exploratory. |
| LPIPS library heavy on CPU | Runtime blow‑up | Compute LPIPS on a fixed‑seed random sample of the test set and report the sample size alongside the scores; never substitute a placeholder value. |
| Metric circularity for physics teacher | Violates scientific soundness | TPC is computed on **student‑generated** frames, not on the deterministic rendering, removing circularity. |
| Evaluation against mismatched data | Confound | All models are trained and evaluated on the **same synthetic physics dataset** splits, isolating the teacher‑type comparison. |
| Fabricated/placeholder results | Fatal integrity flaw (prior-round concern) | Anti‑Fabrication Commitment in plan.md: real measurements only, analytic ground‑truth validation of metric code, manifest provenance for every number, loud failure instead of substitution. |

---



## projects/PROJ-827-llmxive-follow-up-extending-causal-forci/specs/001-llmxive-follow-up-extending-causal-forci/data-model.md
# Data Model: llmXive Follow-up: Physics-Teacher Distillation

## Overview
The project manipulates three primary data entities:

1. **PhysicsTrajectory** – deterministic state‑vector sequence produced by Box2D.
2. **VideoSequence** – rendered 16‑frame MP4 aligned with a PhysicsTrajectory.
3. **EvaluationResults** – per‑sequence metrics and aggregated statistical outputs, **including** an optional `trajectory_pixel_corr` field for the student‑frame TPC metric.

All entities are versioned, checksummed, and validated against the contracts below. The **VideoSequence** schema is defined in `contracts/video_sequence.schema.yaml` and is enforced during data generation (see T1.2). Every metric value in `EvaluationResults` is a real measurement traced through `outputs/manifest.json` (Anti‑Fabrication Commitment); no placeholder values are permitted in any field.

## Data Flow Diagram (textual)

```
Box2D metadata (generated internally) → generate.py → PhysicsTrajectory (.npz) + VideoSequence (.mp4)
Training loader (student) reads both → student_diffusion.py → student checkpoint
Neural‑teacher baseline loader reads the SAME physics data → neural_teacher.py → baseline checkpoint
Evaluation/metrics.py consumes videos + trajectories → per‑sequence EvaluationResults (real measurements)
Statistical analysis aggregates EvaluationResults → JSON/CSV reports
outputs/manifest.json records provenance (script, input checksums, seed) for every output file
```

All intermediate files are stored under `data/` (raw) or `outputs/` (derived) and referenced by checksum in the manifest.

---



## projects/PROJ-827-llmxive-follow-up-extending-causal-forci/specs/001-llmxive-follow-up-extending-causal-forci/quickstart.md
# Quickstart: Physics-Teacher Distillation

The following commands run the entire end‑to‑end experiment on a fresh GitHub Actions runner (or a local Linux environment with the same resources).

## Prerequisites
- Python 3.11 installed.
- `git clone` the repository.
- Internet access (to download the verified Box2D metadata JSON **if needed**; the current pipeline generates worlds internally, so this step can be omitted).

## Step‑by‑Step

1. **Create and activate the virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt   # pins all versions
   ```

2. **Set deterministic seeds (once per run)**
   ```bash
   export GLOBAL_SEED=12345
   ```

3. **Generate physics‑teacher data**
   ```bash
   python -m src.data_generation.generate \
       --seed $GLOBAL_SEED \
       --num-train <N_TRAIN> \
       --num-val <N_VAL> \
       --num-test <N_TEST> \
       --output-dir data/physics
   ```
   - Sequence counts are **[deferred]** to implementation, chosen to fit the 6 h / 7 GB budget.
   - Produces `data/physics/train/`, `val/`, `test/` with `.mp4` videos and `.npz` trajectories.
   - The script logs any NaN‑containing sequences and discards them (fulfilling the relevant functional requirement), and re‑runs a fixed‑seed subset to verify determinism by checksum comparison (as defined in the functional specification).

4. **Train the neural‑teacher baseline**
   ```bash
   python -m src.models.neural_teacher \
       --dataset physics \
       --data-dir data/physics/train \
       --epochs <EPOCHS> \
       --batch-size 8 \
       --output-dir outputs/neural_teacher
   ```
   - This ConvLSTM video‑prediction model learns to predict the next frame from the current frame **without** explicit trajectory input, providing the neural teacher signal.

5. **Train the student model on physics data**
   ```bash
   python -m src.models.student_diffusion \
       --train-dir data/physics/train \
       --val-dir data/physics/val \
       --epochs <EPOCHS> \
       --batch-size 8 \
       --gradient-accumulation-steps 4 \
       --checkpoint-activation \
       --output-dir outputs/student_physics
   ```

6. **Run evaluation (shared held‑out test set)**
   ```bash
   python -m src.evaluation.metrics \
       --test-dir data/physics.test \
       --neural-checkpoint outputs/neural_teacher/checkpoint.pt \
       --student-checkpoint outputs/student_physics/checkpoint.pt \
       --output-dir outputs/metrics
   ```

7. **Statistical analysis (includes power analysis)**
   ```bash
   python -m src.evaluation.statistical \
       --metrics-dir outputs/metrics \
       --output-dir outputs/statistics
   ```

8. **Ablation study**
   ```bash
   python -m src.ablation.run_ablation \
       --param friction 0.2 0.35 0.5 0.65 0.8 \
       --param elasticity 0.1 0.3 0.5 0.7 0.9 \
       --samples-per-config 3 \
       --output-dir outputs/ablation
   ```
   - Five levels per parameter, three random seeds per level (total 15 sequences per setting), ensuring sufficient degrees of freedom for regression.

9. **Validate contracts and metric ground truths**
   ```bash
   pytest -m contract
   pytest tests/unit   # includes analytic metric identity tests (SSIM(x,x)=1, FID(S,S)=0)
   ```

10. **Check runtime & memory compliance (SC‑005)**
    ```bash
    cat outputs/manifest.json   # contains wall_clock_seconds and peak_ram_gb
    # The run aborts automatically if limits are exceeded — it never truncates or substitutes values.
    ```

All generated artifacts are version‑hashed; re‑running the pipeline with the same `GLOBAL_SEED` yields identical hashes, confirming reproducibility (Principle I). **Every reported metric is a real measurement** traced via `outputs/manifest.json`; the pipeline fails loudly rather than emitting placeholder values (Anti‑Fabrication Commitment).

---



## projects/PROJ-827-llmxive-follow-up-extending-causal-forci/specs/001-llmxive-follow-up-extending-causal-forci/contracts/evaluation_results.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "EvaluationResults"
description: "Per‑sequence real measurements of model fidelity. All values are computed from actual model outputs; placeholder values are prohibited."
type: object
required:
  - sequence_id
  - model_type
  - ssim
  - psnr
  - lpips
properties:
  sequence_id:
    type: string
    description: "ID linking to the original VideoSequence."
  model_type:
    type: string
    enum:
      - "student_physics_teacher"
      - "neural_teacher"
    description: "Which model generated the prediction."
  ssim:
    type: number
    minimum: 0.0
    maximum: 1.0
    description: "Structural Similarity Index (higher is better)."
  psnr:
    type: number
    minimum: 0.0
    description: "Peak Signal‑to‑Noise Ratio in dB."
  lpips:
    type: number
    minimum: 0.0
    description: "Learned Perceptual Image Patch Similarity (lower is better)."
  fid:
    type: number
    minimum: 0.0
    description: "Optional set‑level Fréchet Inception Distance against the baseline set (reported per model in outputs/metrics/fid.csv)."
  trajectory_pixel_corr:
    type: number
    description: "Pearson correlation between physics velocities and optical‑flow vectors computed on student‑generated frames."
  additional_info:
    type: object
    description: "Optional free‑form fields (e.g., friction coefficient for ablation)."
    additionalProperties: true
