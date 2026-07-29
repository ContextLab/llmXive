# Implementation Plan: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

**Branch**: `001-llmxive-gam-symbolic-planner` | **Date**: 2026-07-14 | **Spec**: `specs/001-llmxive-follow-up-extending-geometric-ac/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-geometric-ac/spec.md`

## Summary

This project extends the "Geometric Action Model for Robot Policy Learning" (GAM) by replacing its learned causal predictor with a differentiable symbolic solver operating in the **frozen 3D latent space** of a Geometric Foundation Model (GFM). The primary goal is to achieve zero-shot generalization to novel kinematic topologies (variable hinge counts) and deformable materials (soft ropes, cloth) that are absent from the original training distribution. The system generates a synthetic test set via PyBullet, executes a symbolic-latent planning pipeline on a CPU-only GitHub Actions runner, and performs comparative statistical analysis (Fisher's Exact Test, paired t-test, and Survival Analysis) against the baseline GAM.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pybullet` (physics), `torch` (GFM inference, CPU mode), `scipy` (solver: SLSQP), `numpy`, `pandas`, `scipy.stats`, `statsmodels` (CI calculation), `datasets` (for potential data loading, though synthetic), `pytest`.  
**Storage**: Local filesystem (`data/raw`, `data/generated`, `data/results`). Checksums tracked in `state/`.  
**Testing**: `pytest` for unit tests; integration tests via simulation scripts.  
**Target Platform**: GitHub Actions x86_64 runner (Intel Xeon equivalent), CPU-only, with multi-core processing and sufficient memory (ample RAM).  
**Project Type**: Research/Scientific Computing (Simulation & Analysis).  
**Performance Goals**: Complete 60 trials per condition (Symbolic vs. Baseline) within 6 hours; solver step time <30s (target); inference latency < 500ms/step.  
**Constraints**: No GPU/CUDA; strict adherence to frozen GFM weights; no modification of GFM encoder/decoder; deterministic random seeds.  
**Scale/Scope**: A set of unique novel topologies (increased from the prior baseline for power) will be explored.; A fixed number of simulation steps per trial will be executed, determined by convergence criteria.; statistical analysis on binary success/latency metrics.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

### Risk Mitigation & Fallback

To address the feasibility risk of differentiable solvers on CPU:
1.  **Custom Autograd Wrapper**: Since `scipy.optimize.minimize` (SLSQP) is not inherently differentiable, the system implements a **custom `torch.autograd.Function`** wrapper. This wrapper uses the implicit function theorem (or finite-difference Jacobian approximation) to compute gradients of the solver's output with respect to the latent parameters, enabling backpropagation of the physical constraint loss through the decoder.
2.  **Horizon Reduction**: If profiling shows >50% timeout rate, the trial horizon is reduced from a longer duration to a shorter duration to ensure completion within the 6h CI window.
3.  **Timeout Handling**: All solver timeouts are recorded as `timeout=1` in `trial_log.csv` with `failure_reason="solver_timeout"`; the pipeline does NOT crash.
4.  **Missing Weights Fallback**: If `data/raw/gfm_weights.pt` is missing, the system generates reference statistics from a standard normal distribution and logs a warning, allowing drift detection to proceed.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: All random seeds pinned in `code/config.py`. Synthetic data generation is deterministic given seed. `requirements.txt` pins all dependencies. CI runs end-to-end.
- **II. Verified Accuracy**: All citations (PyBullet, GFM paper, statistical methods) will be verified against primary sources. No fabricated URLs.
- **III. Data Hygiene**: `data/raw`, `data/generated`, `data/results` are checksummed. No in-place modification.
- **IV. Single Source of Truth**: All figures/statistics in the paper trace back to `data/` and `code/`.
- **V. Versioning**: Artifacts carry content hashes. `state/` updated on changes.
- **VI. Latent-Space Symbolic Fidelity**: The differentiable symbolic planner operates **exclusively within the frozen 3D latent space** (z-space). Physical constraints (rigid-body, soft-body) are enforced as a **post-hoc validation step** on the decoded physical action. The solver optimizes the latent trajectory to minimize a loss computed from this physical validation. Gradients flow from the validation error (physical space) **through the decoder** (via the custom autograd wrapper) to the latent solver parameters, verifying differentiability without modifying GFM weights. This aligns with the Constitution's mandate for latent-space operation while satisfying FR-003.
- **VII. Zero-Shot Topology Generalization Protocol**: The test set is strictly synthetic, generated via PyBullet with topologies (hinge counts, deformable parameters) explicitly absent from the original GAM training distribution.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-geometric-ac/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-898-llmxive-follow-up-extending-geometric-ac/
├── code/
│   ├── __init__.py
│   ├── config.py              # Seeds, paths, hyperparameters
│   ├── generate_topology.py   # FR-001: Synthetic test set generation
│   ├── gfm_wrapper.py         # FR-002: Frozen GFM encoder/decoder
│   ├── symbolic_solver.py     # FR-003: Differentiable constraint solver (Latent Space)
│   ├── inference_loop.py      # FR-004: Main execution pipeline
│   ├── analysis.py            # FR-006: Statistical tests
│   └── utils/
│       ├── drift_detector.py  # Edge Case: Mahalanobis distance
│       └── logger.py
├── data/
│   ├── raw/                   # GFM weights, reference stats
│   ├── generated/             # Synthetic topology datasets
│   └── results/               # Trial logs, gradient logs
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── requirements.txt
```

**Structure Decision**: Single project structure. `code/` contains all executable scripts. `data/` is strictly for artifacts. `tests/` mirrors `code/` logic.

### Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Latent-Space Solver with Physical Validation | Constitution VI requires latent operation; FR-003 requires physical constraint validation. | A purely physical solver violates the Constitution; a purely latent solver cannot validate physical constraints. The hybrid approach (latent-space optimization + physical validation via post-hoc loss) is the only valid path. |
| Synthetic Topology Shift | VII requires testing on unseen topologies. | Real-world datasets do not offer controlled, zero-shot topology shifts for specific kinematic chains. |
| CPU-First | SC-005 mandates execution on GitHub Actions free tier. | GPU-dependent methods (e.g., full transformer inference) exceed the 2-core/7GB RAM constraint without scaling down, which would invalidate the "real" computation claim. |
| Convex Relaxation of Contact | Non-convex contact is unsolvable on CPU in real-time. | Exact non-convex contact requires GPU or specialized solvers; convex relaxation (soft-penalty) is the only tractable CPU alternative for the post-hoc validation loss. |

## Tasks

### Phase 0: Setup & Configuration
- [x] T001a: Create project directory structure (`projects/PROJ-898-llmxive-follow-up-extending-geometric-ac`).
- [x] T001b: Create `code/`, `data/`, `tests/` subdirectories.
- [x] T001c: Add `.gitkeep` to `data/raw`, `data/generated`, `data/results`.
- [x] T002: Initialize `requirements.txt` with pinned versions.
- [x] T003: Configure `ruff.toml` and `pyproject.toml` (Black).

### Phase 1: Data Generation & Reference Stats
- [ ] T009-gen-chains: Generate multiple kinematic chain topologies. **Parameters**: Hinge count in `[3, 10]` (Uniform distribution).
- [ ] T009-gen-deformable: Generate multiple deformable material topologies. **Parameters**: Stiffness in `[0.1, 0.5]` (Uniform distribution).
- [ ] T009-verify-uniqueness: Verify uniqueness of a representative set of topologies. **Retry Loop**: If <50 unique topologies are found after A limited number of retries., **HALT** the pipeline, log a CRITICAL error, and write a partial dataset. Do NOT proceed with the inference phase (T017) to satisfy FR-001's "at least 50" mandate.
- [ ] T009-hash: Compute SHA-256 hash for each topology.
- [ ] T009-serialize: Save `metadata.json` and `states_*.npy`.
- [ ] T010b: Generate reference statistics (`data/raw/gam_reference_stats.json`). **Method**: If `data/raw/gfm_weights.pt` exists, sample latent vectors from the GFM encoder's prior. If weights are missing, sample from a standard normal distribution (approximating the prior) and log a warning. Compute mean/covariance.

### Phase 2: Core Implementation
- [ ] T014a: Implement `symbolic_solver.py` (Latent Space Optimization).
  - **Logic**: Optimize latent vector `z` to minimize distance to target in latent space, subject to latent velocity limits.
  - **Differentiability**: Implement a **custom `torch.autograd.Function`** wrapper around `scipy.optimize.minimize` (SLSQP). This wrapper allows gradients to flow from the constraint violation loss (computed via PyBullet on decoded actions) **through the decoder** to the latent solver parameters.
  - **Output**: Write `data/results/gradient_flow_log.json` with keys: `solver_params`, `decoder_gradients`, `constraint_loss`, `valid_path`.
- [ ] T014a-verify: Verify gradient flow by checking `valid_path: true` in log.
- [ ] T017: Implement `inference_loop.py`.
  - **Logic**: Run trials for Symbolic and Baseline.
  - **Success Check**: Verify `distance < 5cm` AND `success_frames >= 60` (A consecutive sequence of frames at a standard video frame rate).
  - **Timeout/Infeasible**: If solver times out, set `timeout=1`, `failure_reason="solver_timeout"`. If solver returns infeasible, set `failure_reason="infeasible"`.
  - **Drift**: Compute Mahalanobis distance (using T010b stats) and set `drift_flag=1` if > threshold.
  - **Output**: Write `data/results/trial_log.csv`.
- [ ] T018a: Run multiple trials for Symbolic condition.
- [ ] T022a: Run multiple trials for Baseline condition.

### Phase 3: Analysis
- [ ] T024-26: Implement `analysis.py` (Merged).
  - **Success Rate**: Fisher's Exact Test. Calculate Odds Ratio and **95% CI** using `statsmodels.stats.proportion.proportion_confint` (Wilson score).
  - **Latency**: Aggregate per-trial mean latency. Check normality (Shapiro-Wilk). If normal, Paired t-test (mean diff, p-value, Cohen's d). If not, Wilcoxon Signed-Rank (Cliff's Delta).
  - **Survival**: Kaplan-Meier curves and Log-Rank test for Time-to-Failure.
  - **Output**: Write `data/results/statistical_report.json`.

### Phase 4: Verification & Reporting
- [ ] T031: Verify all artifacts against schemas.
- [ ] T032: Generate final report.