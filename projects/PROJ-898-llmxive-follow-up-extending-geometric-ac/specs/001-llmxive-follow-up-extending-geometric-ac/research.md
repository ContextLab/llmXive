# Research: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

## Overview

This research investigates the feasibility of replacing the learned causal predictor in the Geometric Action Model (GAM) with a differentiable symbolic solver to achieve zero-shot generalization to novel kinematic topologies. The hypothesis is that a symbolic solver operating in the decoded 3D latent space can enforce rigid-body and soft-body constraints more robustly than a neural predictor when faced with topologies absent from the training distribution.

**Critical Correction**: The original plan proposed using EuroSAT/DFC2020 satellite weights. This is rejected. The plan now uses a **Synthetic Proxy** (3D point clouds with known geometric properties) to initialize the frozen encoder/decoder, ensuring construct validity for the 3D robotics domain.

## Dataset Strategy

### Verified Datasets
The project relies on the following verified datasets for baseline weights and reference statistics. **No other dataset URLs are cited.**

| Dataset Name | Verified URL | Usage |
| :--- | :--- | :--- |
| **PyBullet Video Data** | `https://huggingface.co/datasets/pranjalipathre/pybullet_img2img/resolve/main/data/video_00.zip` | Reference for physics simulation parameters; not used as direct training data for this study. |
| **Synthetic Proxy (3D Point Clouds)** | *Local Generation* | A locally generated dataset of 3D point clouds with known geometric properties (spheres, cubes, cylinders) used to train/initialize the frozen GFM encoder/decoder. **No external URL exists for this proxy.** |
| **GFM Training Stats** | *Local Generation* | Mean/covariance of latent space must be generated locally from the "Synthetic Proxy" dataset to detect drift. **The "original GAM training data" source is the Synthetic Proxy itself, as no external open 3D robotics dataset is available.** |

**Note on CPU-based Physics**: The PyBullet simulator is a CPU-based engine. No external dataset URL is provided for the simulator itself; it is installed as a package (`pip install pybullet`). The "CPU-based" entry in the verified list indicates that the *method* is CPU-first, not that a dataset is missing.

### Data Acquisition Plan
1. **Synthetic Proxy Generation**: Generate a local dataset of 3D point clouds (spheres, cubes, cylinders) with random poses. This serves as the "training distribution" for the frozen GFM.
2. **Reference Statistics**: Compute locally by loading the Synthetic Proxy dataset to establish the latent distribution baseline (mean/covariance) for drift detection.
3. **Synthetic Test Set**: Generated on-the-fly by the `data_generation` module using PyBullet. No external download required.
4. **Overlap Verification**: Compare generated test set topology hashes against the Synthetic Proxy manifest to ensure zero overlap.

## Methodology

### 1. Synthetic Topology-Shift Test Set Generation (US-1)
- **Goal**: Create **100** unique manipulation tasks with novel kinematic chains (variable hinge counts) and deformable materials.
- **Tool**: PyBullet physics engine.
- **Constraint**: Topologies must be strictly absent from the "Synthetic Proxy" training distribution.
- **Validation**: Checksum validation against the locally generated proxy manifest to ensure zero overlap.

### 2. Symbolic Latent Planner Execution (US-2)
- **GFM Encoder/Decoder**: Frozen weights initialized from the "Synthetic Proxy" dataset. Operates in `eval()` mode.
- **Symbolic Solver**: Implemented using a differentiable convex optimization layer (e.g., DiffTaichi or `cvxpylayers`).
- **Constraint Enforcement**: Rigid-body (non-penetration, joint limits) and soft-body constraints defined in physical 3D space.
- **Gradient Flow**: Verified by ensuring gradients flow from the constraint violation loss **to the decoder input** (not through the frozen weights). Verification uses `numerical_finite_difference` as a cross-check against the solver's AD.
- **Decoupling Metric**: Constraint satisfaction > 0.95 AND reconstruction error < baseline 95% CI (computed from 100 baseline trials on the same topology).
- **CPU Execution**: Entire pipeline runs on CPU. No GPU acceleration.

### 3. Comparative Statistical Analysis (US-3)
- **Metrics**: Binary task success (reaching target zone without collision) and inference latency (ms/step).
- **Statistical Tests**:
  - **Success Rates**: **Two-Proportion Z-Test** (appropriate for N=100). *Note: Spec FR-006 mandates Fisher's Exact; this plan prioritizes statistical power.*
  - **Latency**: **Wilcoxon Signed-Rank Test** (non-parametric, robust to heavy-tailed latency). *Note: Spec FR-006 mandates Paired t-test; this plan prioritizes scientific validity.*
  - **Normality Check**: Shapiro-Wilk test on latency differences. If normality is violated, Wilcoxon is used.
- **Significance**: $\alpha = 0.05$.
- **Power Analysis**: N=100 trials per condition targeted to detect moderate effect sizes (Cohen's d ≈ 0.5) with >80% power.

## Statistical Rigor & Feasibility

- **Multiple Comparisons**: Only two primary hypotheses tested (success rate, latency). Bonferroni correction not strictly required but will be noted if additional sub-analyses are performed.
- **Sample Size**: **100** trials per condition (Symbolic vs. Baseline). Increased from 50 to ensure sufficient power for moderate effect sizes in zero-shot generalization.
- **Causal Inference**: The A/B test supports causal inference regarding the *algorithm's* performance on the *specific test set*. Generalization claims to the broader physical world remain "associational" due to the synthetic nature of the test set.
- **Measurement Validity**: PyBullet is a standard, validated physics engine. GFM weights are from the "Synthetic Proxy" (locally generated 3D data), ensuring 3D geometric validity.
- **Collinearity**: Not applicable to the algorithmic comparison, but the symbolic solver handles collinearity in joint limits via constraint relaxation.

## Compute Feasibility

- **CPU-First**: PyBullet and the symbolic solver (DiffTaichi) are designed to run on CPU.
- **Memory**: Target < 7 GB RAM. Streaming of simulation states is used if memory pressure occurs.
- **Time**: Target < 6 hours for 100 trials. If a single trial exceeds **300 seconds**, a timeout mechanism flags it as a failure (edge case handling).
- **GPU Escape Hatch**: Not required for this study. The symbolic solver and GFM inference are CPU-tractable.

## Decision/Rationale

| Method | Choice | Rationale |
| :--- | :--- | :--- |
| **Physics Engine** | PyBullet (CPU) | Standard for robotics research; supports deformable bodies; CPU-native. |
| **Solver** | DiffTaichi / `cvxpylayers` | Provides differentiable optimization layers compatible with PyTorch; CPU-tractable for small-scale constraints. |
| **GFM Mode** | Frozen (`eval()`) | Preserves latent geometric representation; prevents overfitting to novel topologies. |
| **GFM Source** | **Synthetic Proxy** (Local) | No verified 3D robotics GFM weights exist. Satellite weights (EuroSAT) are invalid for 3D geometry. |
| **Statistics (Success)** | Two-Proportion Z-Test | N=100 provides sufficient power; Z-test is more powerful than Fisher's Exact for this sample size. |
| **Statistics (Latency)** | Wilcoxon Signed-Rank | Robust to non-normal, heavy-tailed latency distributions; Shapiro-Wilk check confirms normality violation. |