# Research: llmXive follow-up: extending "PhysisForcing: Physics Reinforced World Simulator for Robotic Manipula"

## Problem Statement & Hypothesis

**Problem**: Training physics-informed robotic manipulation policies often requires expensive joint optimization during the training phase (e.g., PhysisForcing). This raises the question: can a simpler, computationally cheaper approach of generating synthetic videos and filtering them *post-generation* based on physics consistency yield comparable policy performance?

**Hypothesis**: Applying a lightweight, post-generation physics-consistency filter to synthetic robotic manipulation videos yields physical consistency in downstream policy learning comparable to that achieved by training-time physics-informed joint optimization (with a minimal performance gap).

## Dataset Strategy

The project relies on the following verified datasets and sources. No fabricated URLs are used.

| Dataset/Source | Verified URL | Usage in Project | Notes |
|----------------|--------------|------------------|-------|
| **Wan2.1 (Model Weights)** | `https://huggingface.co/Wan-AI/Wan2.1-T2V-14B` | Model weights/architecture reference | Used to generate synthetic robotic manipulation videos. Official source. |
| **RobotBench (Prompts)** | `https://huggingface.co/datasets/robotbench/robotbench-prompts` | Prompt generation reference | Provides domain-specific prompts for grasping, pushing, lifting. |
| **PyBullet (Synthetic Calibration)** | N/A (Self-Generated) | Filter training/validation | Canonical simulations generated from prompts serve as the independent ground truth. |
| **R-Bench / PAI-Bench** | ` | Evaluation metrics | Standardized benchmarks for physical consistency. |

**Note on Missing Sources**:
- **CPU-based physics engine**: No verified source URL found. The project will use the `pybullet` Python package (installed via `pip`) in headless mode, which is standard for CPU-based physics simulation.
- **VideoSamples**: No verified source URL found. These will be generated *de novo* by the Wan2.1 model within the pipeline.
- **TrainedModel (predictions)**: No verified source for the *final* trained model; it will be produced by the pipeline.
- **Prompt-to-Scene Assets**: No specific robotic manipulation dataset is used. Instead, standard PyBullet primitive shapes (cubes, spheres, planes) are mapped to prompt keywords (e.g., "cup" -> cube) via a simple lookup table to generate the canonical simulation. **Limitation**: This is a simplification of the target domain (robotic manipulation) and may not capture fine-grained object dynamics. The filter is designed to detect gross inconsistencies (e.g., clipping) rather than fine-grained dynamics.

## Methodology

### Phase 1: Synthetic Video Generation
1. **Model**: Use the Wan2.1 model (weights downloaded from verified HuggingFace sources) to generate robotic manipulation videos.
2. **Prompts**: Use prompts derived from **RobotBench** to ensure diversity in manipulation tasks (grasping, pushing, lifting).
3. **Output**: Generate a batch of videos. (MP4 format).
4. **Constraints**: Generation must run on CPU. If the model requires GPU for inference, a distilled/quantized CPU-compatible version or a smaller subset of prompts will be used. *Decision*: The plan assumes a CPU-tractable inference path for Wan2.1; if not feasible, the generation step will be simulated with a smaller, verified CPU-capable diffusion model (e.g., Stable Video Diffusion 1.1 in CPU mode) to maintain the pipeline structure while adhering to compute constraints.

### Phase 2: Physics Consistency Filtering
1. **Prompt-to-Scene Translation**:
 - Parse text prompts to identify action verbs (grasp, push) and object nouns.
 - Map these to standard PyBullet assets (e.g., "cup" -> cube, "table" -> plane).
 - Define initial poses (e.g., object at (0,0,0.5), hand at (0,0,1.0)).
2. **Canonical Simulation**:
 - Run a deterministic PyBullet simulation using the mapped assets and poses to generate the "intended" trajectory (ground truth) for each prompt.
 - This serves as the *independent ground truth* derived from the text, not the video.
3. **Computer Vision Pipeline**:
 - **Segmentation**: Use **SAM2** to segment objects in each video frame.
 - **Depth Estimation**: Use **ZoeDepth** to estimate depth maps for each frame.
 - **3D Reconstruction**: Combine segmentation and depth to extract 3D object trajectories (position, velocity) over time. **Assumption**: Fixed camera intrinsics (e.g., focal length 50mm) and static camera pose are used for 3D projection.
 - **Smoothing**: Apply a Kalman Filter to smooth the extracted trajectory and reduce noise.
4. **Scoring**:
 - **Trajectory Continuity**: Measure deviation between the *extracted 3D trajectory* (from video) and the *canonical simulation* (independent ground truth).
 - **Contact Conservation**: Detect and penalize instances where the reconstructed trajectory shows objects passing through surfaces (clipping) relative to the canonical simulation.
 - Assign a consistency score (0.0 to 1.0) to each video. **Note**: This is a *proxy* metric for physical consistency, limited by the accuracy of the CV pipeline and the simplification of the canonical simulation.
5. **Filtering**: Discard the bottom **[deferred]** of videos based on the score distribution. A percentile-based threshold will be used as the cutoff.
6. **Output**: A `CuratedDataset` containing only high-consistency videos.

### Phase 2.5: Data Augmentation (FR-009)
1. **Trigger**: If the curated set size < 30.
2. **Action**: Apply **Temporal Jittering** (random frame skipping/duplication) and **Geometric Flipping** (horizontal/vertical flips) to generate synthetic variations.
3. **Goal**: Reach a minimum sample size sufficient for statistical validity.
4. **Record**: Log augmentation parameters in metadata.

### Phase 3: Model Training
1. **Model**: Train a distilled diffusion model with a parameter count in the range suitable for efficient deployment on the `CuratedDataset`.
2. **Optimization**: Use standard CPU-tractable optimization (AdamW, default precision).
3. **Constraints**: Training must complete within 4 hours on a 2-core CPU runner.
4. **Fallback**: If the target model is too large for the RAM limit, the plan will switch to a smaller parameter model or use aggressive data sampling (e.g., 1 frame per 10 frames) to fit the memory.

### Phase 4: Evaluation & Statistical Testing
1. **Baseline Reproduction**:
 - Reproduce the **PhysisForcing baseline** by training a **Physics-Informed Training Proxy**. This proxy is a standard diffusion model trained with an *additional* physics-informed loss term (using the same PyBullet canonical simulation) during training. This mimics the "joint optimization" concept (training-time physics) vs. the proposed "post-generation filtering" (inference-time curation).
 - If the original code is unavailable, this proxy baseline is the best CPU-tractable approximation of the PhysisForcing paradigm.
2. **Multi-Batch Statistical Design**:
 - Generate **three independent batches** (Batch A, B, C) of videos.
 - Draw the evaluation set (n=30) by **stratified sampling** from all three batches combined.
 - **Statistical Test**: Perform a **Linear Mixed Model (LMM)** analysis with 'Batch' as a random effect to account for batch-specific generation artifacts.
3. **Benchmarks**: Evaluate the trained model on R-Bench and PAI-Bench.
4. **Sample Size & Power**:
 - Ensure n ≥ 30 for the evaluation set.
 - **Power Analysis**: Conduct a power analysis (effect size 0.5, α=0.05, power=0.8) to justify n=30. If power is insufficient, the result will be reported as "inconclusive" rather than forcing a false positive.
 - **Interpretation**: If power is low, the result will be reported as "inconclusive" rather than forcing a false positive.
5. **Success Criteria**: Performance gap ≤ 15% and p-value ≥ 0.05 (indicating no significant difference, i.e., comparability).

### Phase 5: Independent Validation (FR-008)
1. **MuJoCo Simulation**: Run the curated videos through **MuJoCo** using the *same* CV-extracted trajectories and prompt-derived initial conditions.
2. **Correlation Analysis (SC-006)**: Calculate the correlation coefficient between PyBullet scores and MuJoCo scores.
3. **Independence Verification**: Verify that the correlation coefficient is < 0.95 (distinct metric distribution) to confirm that the two engines are not validating the exact same reconstruction artifact. This validates the *engine independence*, not the video ground truth (which is acknowledged as a limitation).

## Decision Log & Rationale

| Decision | Rationale |
|----------|-----------|
| **CPU-only execution** | Mandatory due to GitHub Actions free-tier constraints. GPU methods are excluded. |
| **Post-generation filtering** | Directly tests the hypothesis that sample curation can replace expensive training-time optimization. |
| **PyBullet for filtering** | Lightweight, CPU-native, and sufficient for detecting gross physical inconsistencies (e.g., clipping). |
| **SAM2/ZoeDepth for CV** | Required to extract 3D trajectories from 2D video frames, enabling the physics comparison. |
| **Canonical Simulation (Ground Truth)** | Breaks circularity by providing an independent ground truth (prompt-derived) rather than validating the video against itself. **Limitation**: Simplified representation of the video content. |
| **Prompt-to-Scene Translation** | Necessary to generate a ground truth trajectory from text prompts without a robotic manipulation dataset. |
| **Distilled 50M model** | Balances model capacity with CPU training feasibility. Larger models would exceed RAM/time limits. |
| **Linear Mixed Model (LMM)** | Required to account for batch effects in multi-batch generation, ensuring valid statistical inference. |
| **Data Augmentation (FR-009)** | Ensures statistical power (n ≥ 30) even if the filtered dataset is small. **Limitation**: Does not increase independent information content. |
| **MuJoCo Validation (FR-008)** | Ensures independent validation of the physics engine, not the video ground truth. |

## Limitations & Risks

- **Compute Feasibility**: Generating high-quality videos and training diffusion models on CPU is slow. The plan mitigates this by using a smaller batch size and potentially a distilled model.
- **Dataset Size**: If the filtered dataset is too small (< 30 samples), statistical power will be low. Mitigation: Data augmentation or explicit reporting of power limitations.
- **Physics Engine Fidelity**: PyBullet is less accurate than MuJoCo for fine-grained physics. The plan uses PyBullet for filtering (speed) but mandates MuJoCo or real-world data for final validation (FR-008) to avoid circularity.
- **Model Availability**: If Wan2.1 cannot run on CPU, the generation step will be substituted with a verified CPU-capable video generation model, and the results will be qualified accordingly.
- **Reconstruction Error**: The physics score is a proxy for physical consistency, limited by the accuracy of the CV pipeline (SAM2/ZoeDepth) and the fixed camera assumption. The plan acknowledges this as the primary source of error and treats the score as a proxy. A subset of videos will be manually reviewed to estimate reconstruction accuracy.
- **Prompt-to-Scene Ambiguity**: The mapping of text prompts to 3D assets is simplified. Complex prompts may not map correctly, leading to inaccurate ground truth. This is a known limitation of the symbolic approach.
- **Simplification Limitation**: The canonical simulation uses primitive shapes (cubes, planes) as a proxy for complex objects. The filter is designed to detect gross inconsistencies (e.g., clipping) rather than fine-grained object dynamics.
