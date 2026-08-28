# Research: Virtual Tactile Zero-Shot Adaptation

## Problem Statement

Current dexterous hand manipulation policies (e.g., PICA) often rely on static reward schedules that assume a fixed contact stiffness or friction environment. When deployed on novel articulated objects with randomized friction (e.g., a stiff drawer vs. a slippery lever), these static policies fail to adapt, leading to high failure rates (slipping, overshooting, or excessive force). This research investigates whether a "Virtual Tactile" estimator—deriving stiffness proxies from kinematic and torque derivatives—can enable zero-shot adaptation, improving success rates on unseen high-friction objects by >15% without retraining.

**Note on Scientific Validity**: The hypothesis is not that $k_{est}$ "discovers" friction (which is known in simulation), but that using $k_{est}$ as a **real-time control signal** allows the policy to adapt to friction-induced dynamics in a way a static policy cannot. The "zero-shot" claim refers to adaptation without prior knowledge of the specific friction coefficient or distribution during the trial, simulating a real-world scenario where tactile sensors are absent.

## Theoretical Background

### Virtual Tactile Estimator
The core hypothesis is that contact stiffness ($k$) can be inferred from the ratio of the temporal derivative of hand joint torques ($\Delta \tau_{hand}$) to the temporal derivative of object velocity ($\Delta v_{object}$) during the sliding regime:
$$ k_{est} = \frac{|\Delta \tau_{hand}|}{|\Delta v_{object}|} $$
This approach leverages the physical relationship where higher friction (stiffness) results in larger torque fluctuations for a given velocity change. To handle simulation noise and stiction (zero velocity), the estimator applies a moving average filter (window=5) and a small epsilon ($\epsilon = 10^{-4}$) to the denominator, as mandated by FR-006 and FR-007.

### Adaptive Reward Scheduler
The scheduler dynamically adjusts the PICA reward weights based on $k_{est}$:
- If $k_{est} > 1.0$ (High Stiffness): Increase detachment penalty ($r_{detach}$) by $\ge 20\%$ to encourage firmer grip.
- If $k_{est} < 0.2$ (Low Stiffness): Decrease contact maintenance reward ($r_{contact}$) by $\le 15\%$ to prevent overshooting.

## Dataset Strategy

### Primary Dataset: DragMesh-2
- **Source**: Hugging Face (Verified URL: https://huggingface.co/datasets/AIGeeksGroup/DragMesh-2/resolve/main/dataset_manifest.jsonl)
- **Usage**: The `dataset_manifest.jsonl` provides the base geometry and trajectory data for articulated objects.
- **Strategy**: The implementation will download this manifest programmatically. The `object_generator.py` module will use the geometries in the manifest to create **novel** articulated object instances by randomizing friction coefficients (0.0 to 2.5) and slight geometric perturbations. This ensures the evaluation set is distinct from any training distribution, satisfying the "zero-shot" requirement.
- **Feasibility**: The manifest is a small JSONL file (<10MB), easily downloadable on CI. The heavy lifting (simulation) is performed on generated instances, not the raw dataset itself, ensuring the pipeline runs within the available RAM and time limits.

### No External Tactile Data
The research explicitly avoids external tactile sensor datasets. The "Virtual Tactile" estimator relies solely on the simulation's internal state (torques, velocities), making external tactile data unnecessary and avoiding the "access-gated data" feasibility flaw.

## Methodology

### 1. Environment Setup
- **Physics Engine**: PyBullet (CPU backend, `pybullet.DIRECT` mode).
- **Policy**: A simplified PICA baseline (static rewards) and the Adaptive Policy (dynamic rewards).
- **Randomization**: Friction coefficients sampled using **stratified sampling**:
  - **High-Friction Subset (Target for SC-001)**: A set of objects with friction uniformly sampled from [0.8, 1.2].
  - **Full-Range Subset (Target for SC-002)**: objects with friction uniformly sampled from [0.0, 2.5].
  - **Out-of-Distribution Check**: A small subset of trials will use friction > 2.0 or < 0.0 to test generalization beyond the training range.

### 2. Experiment Design
- **Trials**: A randomized set of trials per object (as per Task T021a resolution).
- **Objects**: A set of novel articulated objects generated from the DragMesh-2 base geometries.
- **Conditions**:
  - **Static Baseline**: Fixed reward weights.
  - **Adaptive**: Dynamic weights based on $k_{est}$.
- **Metrics**:
  - **Success Rate**: Binary outcome (goal reached within time limit).
 - **Improvement Metric**: **Odds Ratio (OR)** with 95% Confidence Intervals. This avoids division-by-zero issues when the static baseline success rate is [deferred].
  - **Statistical Significance**: **Generalized Linear Mixed Model (GLMM)** with binomial family and logit link. The model treats `object_id` as a random effect to account for clustering of trials within objects. This is statistically superior to a t-test on proportions.

### 3. Computational Constraints
- **CPU-First**: All simulations and inference run on CPU. No CUDA.
- **Memory Management**: Streaming simulation steps; no full trajectory storage in RAM. Peak RAM monitored via `psutil`.
- **Time Budget**: Target < 6 hours for the full sweep (Multiple trials * 50 objects). If a single trial exceeds a predefined duration threshold, the sample size or trial length will be reduced. (honest scaling).

## Decision/Rationale

### CPU vs. GPU
- **Decision**: Strictly CPU-only.
- **Rationale**: The spec (FR-004, US-3) and Constitution (Principle VI) mandate CPU execution for reproducibility on GitHub Actions free-tier runners. The method (physics simulation + heuristic estimator) is computationally light enough for 2 CPU cores. A GPU escape hatch is not needed as the method does not involve large transformer inference or diffusion models.

### Dataset Selection
- **Decision**: Use DragMesh-2 manifest as the geometry source.
- **Rationale**: It is the only verified dataset provided. It contains the necessary articulated object geometries. The "novelty" required for zero-shot testing is achieved by randomizing friction and slight geometric variations, not by using a completely different dataset. This avoids the "access-gated" pitfall of clinical datasets.

### Statistical Approach
- **Decision**: GLMM (Binomial) instead of t-test.
- **Rationale**: Success rate is a binary outcome aggregated per object. A t-test assumes continuous, normally distributed data and fails when rates are [deferred] or [deferred]. GLMM handles binary data correctly, accounts for trial clustering (random effects), and provides Odds Ratios which are well-defined even with zero successes in one group.

### Generalization Check
- **Decision**: Include Out-of-Distribution (OOD) friction values.
- **Rationale**: To address the concern that the estimator merely "reads" the simulation's friction parameter, we test on friction values outside the standard randomization range. If the adaptive policy still outperforms the static baseline in these OOD regimes, it validates the generalization capability of the proxy signal.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **Simulation Jitter**: Torque derivatives may be noisy. | Apply moving average filter (window=5) as per FR-006. |
| **Stiction (Zero Velocity)**: Division by zero in $k_{est}$. | Apply epsilon ($10^{-4}$) to denominator as per FR-007. |
| **Compute Time**: 100 trials * 50 objects may exceed 6h. | Monitor wall-clock time; if > 4.5h at [deferred] progress, reduce trial count to a manageable subset or object count to a manageable subset (honest scaling). |
| **Dataset Mismatch**: DragMesh-2 may lack required articulated objects. | Use the manifest to generate *new* geometries via parameterization; if the manifest is purely static meshes, the generator will procedurally create articulated joints. |
| **Zero Success Baseline**: Static policy fails completely on high friction. | Use Odds Ratio (GLMM) instead of percentage improvement; OR is defined even if one rate is 0. |

## References

1. DragMesh-2 Dataset Manifest: https://huggingface.co/datasets/AIGeeksGroup/DragMesh-2/resolve/main/dataset_manifest.jsonl
2. Gaussian Filter (Moving Average): https://en.wikipedia.org/wiki/Gaussian_filter (Window size = 5)
3. Generalized Linear Mixed Models: https://en.wikipedia.org/wiki/Generalized_linear_mixed_model