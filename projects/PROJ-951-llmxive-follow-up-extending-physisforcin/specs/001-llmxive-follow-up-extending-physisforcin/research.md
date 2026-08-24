# Research: llmXive follow-up: extending "PhysisForcing: Physics Reinforced World Simulator for Robotic Manipula"

## Hypothesis & Rationale

**Hypothesis**: Applying a lightweight, post-generation physics-consistency filter to synthetic robotic manipulation videos yields physical consistency in downstream policy learning comparable to that achieved by training-time physics-informed joint optimization.

**Rationale**: Training-time physics optimization (e.g., PhysisForcing) is computationally expensive. If a high-quality dataset can be curated by filtering out physically impossible samples (e.g., object clipping, trajectory discontinuities) using a fast CPU-based simulator (PyBullet), then a standard diffusion model trained on this "clean" data should learn the physical priors implicitly, achieving comparable performance on benchmarks (R-Bench, PAI-Bench) without the joint optimization overhead.

## Dataset Strategy

### Primary Data Source: Synthetic Generation
- **Generator**: Wan2.1 (Video-to-Video/Image-to-Video).
- **Strategy**: The system will generate a batch of videos using standard robotic manipulation prompts.
- **Verification**: The Wan2.1 model weights and architecture are available via the official **Wan-AI Hugging Face repository** (wan2.1).
- **Dataset Reference**: `wan2.1` from Hugging Face (Official).

### Filtering & Validation Data
- **Physics Filter (PyBullet)**: Uses `pybullet` library.
  - *Verified Source*: Standard `pybullet_data` package (installed via pip) containing URDFs for standard robots (UR5, KUKA) and objects (blocks, spheres).
- **Validator (MuJoCo)**: Uses `mujoco` library for independent validation.
  - *Constraint*: MuJoCo requires a license key for full features, but the open-source version is sufficient for validation.
  - *Metric Distinction*: PyBullet measures **trajectory continuity** and **contact conservation**. MuJoCo measures **final object pose error** and **energy conservation** to ensure distinct physical invariants.

### Curated Dataset
- **Target**: Top [deferred] (retaining [deferred] of the initial batch) based on physics scores.
- **Minimum Threshold**: Videos must score ≥ 60th percentile of the initial batch distribution (source: 2506.09162).
- **Augmentation**: If the curated count < 30, physics-preserving augmentation (temporal cropping, color jitter) will be applied (FR-009). **Statistical Note**: Augmented samples are used for simulation coverage but not as independent samples for TOST; a non-parametric bootstrap or permutation test will be used if unique samples < 30.

### Baseline Data
- **PhysisForcing Baseline**: The plan will attempt to run the publicly available PhysisForcing inference code on the *same* curated dataset to generate a distribution of scores.
- **Fallback Strategy**: If the code is unavailable, the plan will use the *published mean and standard deviation* from the PhysisForcing paper to generate a synthetic distribution via bootstrapping (labeled "Synthetic Baseline" in results).

## Statistical Methodology

### Equivalence Testing (TOST)
- **Method**: Two One-Sided Tests (TOST) to determine if the performance gap between the "Filtered Model" and "PhysisForcing Baseline" is within a 15% equivalence margin.
- **Parameters**:
  - Equivalence Margin (Δ): A predefined non-inferiority margin.
  - Significance Level (α):.
  - Target Power: ≥ 0.80 (requires n ≥ 30 unique samples per group, per FR-006).
- **Justification**: Standard t-tests only detect differences; TOST is required to prove *equivalence* (SC-003).
- **Sample Size & Data Type**: If R-Bench/PAI-Bench scores are binary/proportional, a **Non-Parametric Equivalence Test** (bootstrap-based TOST) or **arcsine square root transformation** will be applied to ensure validity.

### Orthogonality Check
- **Method**: Pearson/Spearman correlation between PyBullet scores (continuity) and MuJoCo scores (pose error).
- **Threshold**: Correlation coefficient < 0.95 (SC-006).
- **Purpose**: Ensures the filter (PyBullet) predicts the *downstream task* or *validator* without overfitting to the generator's specific artifacts. The check is between *different physical invariants* (continuity vs. pose), not just engines.
- **Circularity Check**: Additionally, the correlation between the *Filter Score* and *Generator Artifacts* (if available) will be measured to ensure the filter is not circularly correlated with the generator's failure modes.

## Compute Feasibility & Escape Hatch

- **CPU-First Strategy**:
  - **Generation**: Wan2.1 inference is GPU-heavy. **Resolution**: The plan triggers the **GPU Escape Hatch** (Kaggle) for the **Generation Phase** (US-1) only. The `run_pipeline.sh` script detects the CUDA requirement and offloads that specific step to Kaggle.
  - **Filtering**: PyBullet runs efficiently on CPU.
  - **Training**: A 50M parameter diffusion model trained on *static frames* (not video sequences) is small enough for CPU training (scikit-learn/torch CPU) within 4 hours on 2 cores.
  - **Evaluation**: R-Bench/PAI-Bench scoring is lightweight and CPU-tractable, but if it requires the generator model, it may also trigger the GPU escape hatch.

- **GPU Escape Hatch (Kaggle)**:
  - Triggered if `torch.cuda.is_available()` is required for Wan2.1 generation or evaluation.
  - Configuration: Run on Kaggle free GPU (T4/P100) for generation only. The filtered dataset is then saved and passed to the CPU runner for training.
  - **Constraint**: The plan does *not* fabricate a CPU approximation of the video generation. It uses the real model on the real GPU (scaled down if necessary) and then processes the output on CPU.

## Risk Assessment

1. **Dataset Mismatch**: The spec requires "robotic manipulation videos." If the Wan2.1 model cannot generate specific robotic tasks (e.g., precise grasping) with sufficient fidelity, the physics filter may reject [deferred] of samples.
   - *Mitigation*: Use a diverse set of prompts; if rejection rate > 95%, adjust prompts or acknowledge the limitation in the report.
2. **Compute Limits**: Large-scale model training on 2 CPU cores might exceed 6 hours.
   - *Mitigation*: Use mixed-precision (if CPU supports AVX512), reduce batch size, or use a smaller model if the standard size is too slow, noting the power limitation.
3. **Baseline Unavailability**: If the PhysisForcing baseline is not publicly available.
   - *Mitigation*: Use the published scores from the PhysisForcing paper to generate a synthetic distribution via bootstrapping, clearly stating this in the report.
