# Research: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

## Summary

This research investigates whether replacing the learned neural predictor in the Geometric Action Model (GAM) with a differentiable symbolic solver operating in the frozen 3D latent space of the Geometric Foundation Model (GFM) enables zero-shot generalization to novel object topologies. The study generates a synthetic test set of manipulation tasks with unseen kinematic chains (variable hinges) and deformable materials (ropes, cloth) using PyBullet. It compares the symbolic approach against the baseline GAM using Fisher's Exact Test for success rates and a Log-Rank Test (or Wilcoxon Signed-Rank) for inference latency (handling censored data).

## Dataset Strategy

The study relies on two primary data sources: a synthetic test set generated in-house and the original GFM weights/datasets for initialization and baseline comparison.

| Dataset | Source / Access Method | Usage | Verification Status |
|:--- |:--- |:--- |:--- |
| **Synthetic Topology-Shift Test Set** | **Generated** via `code/data/generator.py` using PyBullet. No external URL. Contains novel kinematic chains (e.g., multi-link hinges) and soft bodies. | Primary evaluation data for US-1 and US-2. | **Verified**: Generated programmatically with pinned seeds; uniqueness verified against original GAM metadata (Phase 1.3) using three metrics (Isomorphism, Geo Dist > 0.15, Mahalanobis > 2.0). |
| **GFM Weights & Training Data** | **Hugging Face**: `GFM-Bench/3D-Robotics` (URL: `https://huggingface.co/GFM-Bench/3D-Robotics`). | Used to load frozen encoder/decoder weights (FR-002) and for baseline comparison. | **Verified**: URL provided in `# Verified datasets` block. 3D geometric model, not 2D imagery. |
| **PyBullet Physics Simulator** | **PyPI**: `pip install pybullet` (Official GitHub: `). | Used as the physics engine for simulation and data generation. | **Verified**: Official PyPI package and GitHub repository cited. Not a Hugging Face task bundle. |

**Note on Data Availability**: The study does **not** use access-gated datasets (e.g., ADNI, HCP). All data is either self-generated (synthetic) or publicly available via Hugging Face programmatic loaders or PyPI, ensuring compatibility with the GitHub Actions free-tier runner.

## Methodology

### Phase 0.1: GFM Weight Acquisition
1. **Download**: Fetch `gfm_weights.pt` from `https://huggingface.co/GFM-Bench/3D-Robotics`.
2. **Verify**: Check SHA256 checksum against the manifest.
3. **Freeze**: Load with `requires_grad=False`.

### Phase 0.2: Pilot Latency Study (New)
1. **Execution**: Run multiple trials on complex topologies.
2. **Decision**: If median time > 15s, reduce N (total trials) to fit 6-hour window.
3. **Output**: `data/results/pilot_latency_report.json`.

### Phase 1: Synthetic Test Set Generation (US-1)
1. **Environment Setup**: Initialize PyBullet with a fixed random seed.
2. **Topology Generation**: Procedurally generate a diverse set of unique kinematic chains and deformable meshes.
3. **Uniqueness Check (Phase 1.3)**:
 * **Metric 1**: Topological graph isomorphism (Must be False).
 * **Metric 2**: Geometric similarity (Euclidean distance of parameters > 0.15).
 * **Metric 3**: Latent space distance (Mahalanobis distance > 2.0 sigma).
 * **Action**: If overlap > 0 (any metric fails), generate `data/results/generation_failure_report.json` and halt.
4. **Reference Stats (Phase 1.4)**: Compute mean/covariance of training latent vectors. Save to `data/raw/gam_reference_stats.json`.

### Phase 2: Symbolic Latent Planner Execution (US-2)
1. **Model Loading**: Load frozen GFM weights.
2. **Decoder Fidelity Validation (Phase 2.5)**:
 * Validate decoded states against PyBullet ground truth for a set of novel topologies.
 * Threshold: MSE < 0.05.
3. **Symbolic Solver**: Implement differentiable convex optimization (CVXPY).
4. **Gradient Verification (Phase 2.5)**:
 * **Method**: Numerical Finite Differences.
 * **Protocol**: Perturb solver parameters only; hold decoder input constant.
 * **Goal**: Confirm solver differentiability without backpropagating through frozen weights.
 * **Threshold**: Relative error < 1e-4.
5. **Execution Loop**: Run trials with a configurable timeout per step. Record censored data.
6. **Artifact**: `data/results/gradient_flow_log.json`.

### Phase 3: Comparative Statistical Analysis (US-3)
1. **CI Timeout Enforcement (Phase 3.1)**: Enforce a fixed time limit; record incomplete trials.
2. **Conditional Test Selection (Phase 3.2)**:
 * **Success Rate**: Fisher's Exact Test.
 * **Latency**:
 * If censored > 0%: **Log-Rank Test** (primary) or Wilcoxon Signed-Rank.
 * If censored = 0%: Paired T-Test.
 * **Prohibition**: Do NOT use Paired T-Test on censored data.
3. **Null Hypothesis**: Reject if p < 0.05.

## Feasibility & Compute Strategy

**CPU-First Approach**:
* **Physics**: PyBullet runs efficiently on CPU.
* **Inference**: The frozen GFM is run on CPU (`torch.no_grad()`).
* **Solver**: `cvxpy` solvers are CPU-native.
* **Memory**: The pipeline streams data.
* **Time**: Validated by Phase 0.2 Pilot Study. If pilot time > 15s, N is reduced.

**GPU Escape Hatch**:
* **Not Required**: The plan explicitly avoids GPU-heavy tasks.

## Risk Mitigation

* **Latent Drift**: Monitor Mahalanobis distance (using `gam_reference_stats.json`).
* **Decoder Hallucination**: **Phase 2.5** validates decoder output against ground truth.
* **Solver Infeasibility**: Record as failure; log constraint violation.
* **Timeout**: Enforce hard timeout; use Log-Rank/Wilcoxon for analysis.
