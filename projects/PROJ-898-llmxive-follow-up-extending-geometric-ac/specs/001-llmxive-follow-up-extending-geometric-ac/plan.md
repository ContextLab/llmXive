# Implementation Plan: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

**Branch**: `001-llmxive-gam-symbolic-planner` | **Date**: 2026-07-14 | **Spec**: `specs/001-llmxive-follow-up-extending-geometric-ac/spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-geometric-ac/spec.md`

## Summary

This feature implements a "Symbolic-Latent" planner that replaces the neural predictor in the Geometric Action Model (GAM) with a differentiable convex optimization solver. The system generates a synthetic "topology-shift" test set (novel kinematic chains and deformable materials) using PyBullet, freezes the original Geometric Foundation Model (GFM) encoder/decoder, and executes a constraint-satisfaction solver in physical 3D space. The implementation targets a CPU-only GitHub Actions runner, verifying zero-shot generalization via statistical comparison (Fisher's Exact Test for success rates, Log-Rank Test for censored latency) against the baseline GAM.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pybullet` (CPU physics), `torch` (frozen GFM, CPU inference), `cvxpy` (symbolic solver), `scipy` (statistical tests), `datasets` (Hugging Face data loading), `pandas`, `lifelines` (survival analysis).  
**Storage**: Local file system (`data/raw`, `data/generated`, `data/results`).  
**Testing**: `pytest` (unit, integration, contract tests).  
**Target Platform**: Linux (GitHub Actions x86_64 runner).  
**Project Type**: Research pipeline / Computational experiment.  
**Performance Goals**: Complete 50 trials per condition within 6 hours; inference latency < 300s/step (timeout enforced).  
**Constraints**: No GPU/CUDA; < 7 GB RAM; < 14 GB disk; strict reproducibility (pinned seeds).  
**Scale/Scope**: novel topologies; A moderate number of timesteps per trial.; A series of total trials (a baseline set and a symbolic set) will be conducted..

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned seeds in `code/`, canonical data sources (Hugging Face), and `requirements.txt` for isolated env. Phase 0.1 explicitly acquires GFM weights. |
| **II. Verified Accuracy** | **PASS** | All citations (GFM, PyBullet) mapped to verified URLs in `research.md`. No fabricated metrics. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of generated synthetic data; raw data preserved; derivations in new files. |
| **IV. Single Source of Truth** | **PASS** | All results trace to `data/results/trial_log.csv`; figures generated programmatically from this source. |
| **V. Versioning** | **PASS** | Artifacts (code, data, plan) will carry content hashes; `state` file updated on change. |
| **VI. Latent-Space Symbolic Fidelity** | **PASS** | **Critical Fix:** Plan explicitly forbids backpropagation through decoder. Gradient verification is a *numerical check* (finite differences on solver params only) on the composite map, not a `requires_grad=True` on frozen weights. Phase 2.5 defines this protocol with a relative error threshold (< 1e-4). |
| **VII. Zero-Shot Topology Generalization** | **PASS** | Test set generation (PyBullet) explicitly targets topologies *absent* from training data; overlap check enforced via isomorphism, geometric distance (>0.15), and latent Mahalanobis distance (>2.0) (Phase 1.3). |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-geometric-ac/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-898-llmxive-follow-up-extending-geometric-ac/
├── code/
│   ├── __init__.py
│   ├── config.py              # Hyperparameters, timeouts, seeds
│   ├── data/
│   │   ├── generator.py       # PyBullet topology-shift generation
│   │   └── loader.py          # Hugging Face data fetching
│   ├── models/
│   │   ├── gfm_wrapper.py     # Frozen GFM encoder/decoder (no_grad)
│   │   └── symbolic_solver.py # Differentiable convex solver (CVXPY)
│   ├── eval/
│   │   ├── runner.py          # Trial execution loop (baseline vs. symbolic)
│   │   └── stats.py           # Fisher's Exact, Log-Rank, Wilcoxon, Censored handling
│   └── utils/
│       ├── logging.py         # Structured logging to JSON/CSV
│       └── validation.py      # Topology uniqueness, checksum verification
├── data/
│   ├── raw/                   # Downloaded weights, original GAM data, reference stats
│   ├── generated/             # Synthetic topology-shift test set
│   └── results/               # Trial logs, stats, reports, gradient logs
├── tests/
│   ├── contract/              # Schema validation tests
│   ├── integration/           # End-to-end pipeline tests
│   └── unit/                  # Solver, generator unit tests
├── requirements.txt
└── .gitignore
```

**Structure Decision**: The structure follows a standard research pipeline: `data/` for artifacts, `code/` for modular components (generator, model, solver, eval), and `tests/` for validation. This separation ensures `data/` is immutable after generation and `code/` is purely functional, satisfying Constitution I (Reproducibility).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Symbolic Solver + Frozen GFM** | Required by Spec (FR-003) and Constitution VI to test the "Symbolic-Latent" hypothesis. | Replacing with a neural predictor would invalidate the core research question (zero-shot generalization via constraints). |
| **Survival Analysis (Log-Rank)** | Required by Spec (Edge Cases) and Plan (Methodology) to handle censored latency data (timeouts). | Simple T-test on raw latency ignores censored data, producing invalid statistics. |
| **Numerical Gradient Check** | Required by Constitution VI to verify solver differentiability without backpropagating through frozen weights. | Backpropagation through frozen weights is mathematically invalid and violates the "frozen" constraint. |
| **Synthetic Topology Generation** | Required by Spec (US-1) to create a "topology-shift" test set. | Using existing benchmarks (e.g., EuroSAT) lacks the specific kinematic/deformable topologies needed for the hypothesis. |

## Methodology

### Phase 0.1: GFM Weight Acquisition (FR-002)
1.  **Source Identification**: Fetch GFM weights from the verified source `GFM-Bench/3D-Robotics` (URL: `https://huggingface.co/GFM-Bench/3D-Robotics`).
2.  **Download & Verify**: Use `code/data/loader.py` to download `gfm_weights.pt`. Compute SHA256 checksum and verify against the manifest in `data/raw/`.
3.  **Freeze**: Load weights into `torch` with `requires_grad=False` and `eval()` mode.
4.  **Artifact**: `data/raw/gfm_weights.pt` (checksummed).

### Phase 0.2: Pilot Latency Study (New)
1.  **Purpose**: Empirically measure solver latency on complex deformable topologies to validate feasibility.
2.  **Execution**: Run multiple trials on a subset of the most complex generated topologies (high hinge count, low stiffness).
3.  **Decision Rule**:
    *   If median step time > 15s: Reduce total trial count (N) to fit 6-hour window or tighten solver timeout.
    *   If median step time < 15s: Proceed with N=50.
4.  **Artifact**: `data/results/pilot_latency_report.json`.

### Phase 1: Synthetic Test Set Generation (US-1)
1.  **Environment Setup**: Initialize PyBullet with a fixed random seed to ensure reproducibility.
2.  **Topology Generation**: Procedurally generate a diverse set of unique kinematic chains. (varying hinge counts, link lengths) and deformable meshes (ropes, cloth) that are **strictly absent** from the original GAM training distribution.
3.  **Overlap Check (Phase 1.3)**:
    *   **Metric 1 (Topological)**: Compute **topological graph isomorphism** against training set. Must be **False**.
    *   **Metric 2 (Geometric)**: Compute Euclidean distance of parameter vectors `[link_count, hinge_count, stiffness, damping]`. Must be **> 0.15**.
    *   **Metric 3 (Latent)**: Compute Mahalanobis distance of latent representation from training centroid. Must be **> 2.0 sigma**.
    *   **Action**: If ANY metric fails, **HALT** and generate `data/results/generation_failure_report.json` (Phase 1.4).
4.  **Simulation**: For each topology, generate a sequence of manipulation tasks. Record latent inputs and ground-truth actions.
5.  **Uniqueness Failure Reporting (Phase 1.4)**: If <50 unique topologies are found, log specific reasons (e.g., "collision with training set topology 004") and generate `data/results/generation_failure_report.json`.
6.  **Reference Stats Generation (Phase 1.4 - New)**:
    *   Compute mean and covariance of latent vectors from the training set (or a representative subset).
    *   Save to `data/raw/gam_reference_stats.json` for use in Phase 2 (Drift Detection) and Phase 1.3 (Latent Overlap).

### Phase 2: Symbolic Latent Planner Execution (US-2)
1.  **Model Loading**: Load frozen GFM encoder and decoder weights from `data/raw/gfm_weights.pt`.
2.  **Decoder Fidelity Validation (Phase 2.5)**:
    *   **Purpose**: Break the circular validation by ensuring the frozen decoder's output for novel topologies matches ground-truth physics.
    *   **Method**: Select a diverse set of novel topologies. Decode latent states to physical space. Compare decoded positions/velocities against PyBullet ground-truth states for the same inputs.
    *   **Threshold**: Mean Squared Error (MSE) < 0.05. If MSE > 0.05, flag as "Decoder Hallucination" and exclude from symbolic trials.
3.  **Symbolic Solver**: Implement a differentiable convex optimization layer (using `cvxpy`) that operates on the decoded 3D physical state.
    *   **Constraints**: Rigid-body (non-penetration, joint limits), soft-body (vertex elasticity).
    *   **Differentiability (Phase 2.5 - Gradient Verification)**:
        *   **Method**: **Numerical Finite Differences**.
        *   **Protocol**: Perturb **only** the solver's internal parameters (e.g., slack variables) by $\epsilon = 10^{-6}$. Hold the frozen decoder input constant. Measure the change in the constraint violation loss.
        *   **Validation Metric**: Compute relative error between numerical gradient and the solver's internal analytical gradient (if available) or check for non-zero gradient flow where expected. **Threshold**: Relative error < 1e-4.
        *   **Distinction**: A gradient norm near zero is acceptable only if the analytical gradient is also near zero (flat region). If analytical > 0 and numerical ~ 0, it indicates a broken path.
4.  **Execution Loop**: For each test case:
    *   Encode observation to latent space.
    *   Solve for action in physical space (decoded latent).
    *   Simulate action in PyBullet.
    *   Record success/failure and latency.
    *   **Timeout Handling**: Enforce a time limit per step. If exceeded, record as censored data (timeout failure).
    *   **Artifact**: `data/results/gradient_flow_log.json` (Phase 2.5 output).

### Phase 3: Comparative Statistical Analysis (US-3)
1.  **CI Timeout Enforcement (Phase 3.1)**:
    *   Implement a hard timeout for the entire experiment run.
    *   If the run exceeds 6 hours, record all incomplete trials as "timeout" and log `timeout_reason: "ci_limit"`.
2.  **Conditional Statistical Test Selection (Phase 3.2)**:
    *   **Success Rate**: Compare binary outcomes (Success/Failure) using **Fisher's Exact Test** (appropriate for low counts/small samples). Report p-value and confidence interval.
    *   **Latency**:
        *   **Check Censoring**: If >0% of trials are censored (timeout), **MUST** use **Log-Rank Test** (primary) or **Wilcoxon Signed-Rank Test** (secondary) for latency comparison.
 * **No Censoring**: If [deferred] censored, use **Paired T-Test**.
        *   **Note**: The plan explicitly **FORBIDS** using a Paired T-Test on censored data.
3.  **Null Hypothesis**: Reject if p < 0.05.
4.  **Reporting**: Generate `data/results/stats_report.json` with p-values, confidence intervals, effect sizes, and the specific test used.

## Feasibility & Compute Strategy

**CPU-First Approach**:
*   **Physics**: PyBullet runs efficiently on CPU.
*   **Inference**: The frozen GFM (likely a small CNN/Transformer) is run on CPU (`torch.no_grad()`).
*   **Solver**: `cvxpy` solvers (ECOS, OSQP) are CPU-native and efficient for small-scale convex problems.
*   **Memory**: The pipeline streams data; no full dataset is loaded into RAM.
*   **Time**: 50 trials x 12 steps = 600 steps. The feasibility of N=50 is **validated by Phase 0.2 Pilot Study**. If pilot median time > 15s, N is reduced dynamically.

**GPU Escape Hatch**:
*   **Not Required**: The plan explicitly avoids GPU-heavy tasks (fine-tuning, large model inference). If the frozen GFM inference proves too slow on CPU, the plan will be revised to use a smaller quantized model, but no GPU offload is currently planned.

## Risk Mitigation

*   **Latent Drift**: If the frozen encoder produces out-of-distribution latents for novel topologies, the decoder may fail.
    *   *Mitigation*: Monitor Mahalanobis distance of latent vectors (using stats from `gam_reference_stats.json`). Flag trials with high drift (>2.0 sigma) for manual review (Edge Cases).
*   **Decoder Hallucination**: If the frozen decoder was trained on a distribution that does not include the novel topologies, its output may be physically invalid.
    *   *Mitigation*: **Phase 2.5 (Decoder Fidelity Validation)** explicitly validates decoded states against PyBullet ground truth. If MSE > 0.05, the trial is flagged and excluded.
*   **Solver Infeasibility**: If constraints are too tight, the solver may return "infeasible".
    *   *Mitigation*: Record as failure; do not crash. Log specific constraint violation.
*   **Timeout**: If the solver takes too long.
    *   *Mitigation*: Enforce hard timeout; record as censored data; use appropriate statistical test (Log-Rank/Wilcoxon). Pilot study (Phase 0.2) ensures sample size is adjusted to fit time budget.
