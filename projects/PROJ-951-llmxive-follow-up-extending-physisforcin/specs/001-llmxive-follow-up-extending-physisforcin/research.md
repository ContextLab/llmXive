# Research: llmXive follow-up: extending "PhysisForcing: Physics Reinforced World Simulator for Robotic Manipula"

## 1. Problem Statement & Hypothesis

**Problem**: Training physics-informed robotic policies (e.g., PhysisForcing) is computationally expensive due to joint optimization of generation and physics constraints.
**Hypothesis**: Applying a lightweight, post-generation physics-consistency filter to synthetic videos (using a fixed absolute threshold) yields physical consistency in downstream policy learning comparable to that achieved by training-time physics-informed joint optimization.
**Mechanism**: By discarding videos with a physics score < 60.0 (fixed threshold), the remaining dataset acts as a "curated prior" that allows a standard diffusion model to learn physical laws without explicit physics loss during training.

## 2. Dataset Strategy

The project relies on **open, directly-downloadable datasets** to ensure CI feasibility. No access-gated data is used.

| Dataset Role | Source Name | Verified URL / Loader | Justification |
| :--- | :--- | :--- | :--- |
| **Prompts & Video Seeds** | RoboTIPS | `datasets.load_dataset("RoboTIPS/roboset")` | Verified source for robotic manipulation prompts and video pairs. |
| **Model Weights** | Wan2.1 | `huggingface_hub.hf_hub_download("Wan-AI/Wan2.1-T2V-14B")` | Verified source for the Wan2.1 model weights. |
| **Validation Data** | Robotics-Video-Text | `datasets.load_dataset("robotics-video-text/robotics_video_text")` | Used for real-world proxy validation of filter scores. |

**Note on "CPU-based" and "CuratedDataset"**: These are **not** external datasets. They are internal artifacts generated during the pipeline. "CPU-based" refers to the execution environment. "CuratedDataset" is the output of the filtering step. No external URL exists for these; they are created by `src/generation/` and `src/filters/`.

### Data Feasibility & Streaming
- **Streaming**: The `datasets` library will be used with `streaming=True` to process video data shards without loading the full dataset into RAM.
- **Sample Size**: Initial generation will target a representative set of videos. If the retained count is < 30, FR-009 (data augmentation) will be triggered to reach n ≥ 30 for statistical power.

## 3. Methodology

### 3.1 Video Generation (FR-001)
- **Model**: Wan2.1 (Text-to-Video).
- **Constraint**: CPU-only inference. If the model architecture strictly requires CUDA (e.g., specific attention kernels), the execution agent will offload to Kaggle (GPU escape hatch) using a quantized (8-bit) version of the model on a small batch.
- **Output**: MP4 videos saved to `data/raw/`.

### 3.2 Physics Filtering (FR-002, FR-003)
- **Engine**: PyBullet (Headless mode).
- **Reconstruction**: A computer vision pipeline (`src/filters/reconstruction.py`) converts MP4 frames to 3D state vectors (using depth estimation and object detection) before simulation.
- **Metrics**: 
  1. **Trajectory Continuity**: Smoothness of object positions over time.
  2. **Contact Conservation**: Detection of impossible penetrations.
  3. **Dynamic Consistency**: Force-torque balance (Newtonian violation check).
- **Scoring**: Each video receives a score $S \in [0, 100]$.
- **Cutoff**: Discard videos where $S < 60.0$ (Fixed absolute threshold, Source: 2506.09162). This ensures the curated data possesses actual physical validity regardless of batch quality.
- **Failure Handling**: If PyBullet crashes on a video (corrupted frame), score = 0, video excluded.

### 3.3 Model Training (FR-004, FR-007)
- **Architecture**: Distilled Diffusion Model (50M parameters).
- **Optimization**: CPU-tractable (e.g., `torch.optim.Adam` on CPU).
- **Baseline Protocol**: The PhysisForcing baseline is **re-trained from scratch** on the *same* raw (unfiltered) dataset using joint optimization. This ensures the comparison isolates the effect of the curation strategy vs. the training strategy.
- **Constraint**: If the model requires CUDA for stability, the GPU escape hatch (Kaggle) will be used with a scaled-down batch size and epochs.
- **Duration**: Target < 4 hours.

### 3.4 Evaluation & Statistics (FR-005, FR-006, FR-008)
- **Benchmarks**: R-Bench and PAI-Bench.
- **Downstream Task**: Train a lightweight policy on each dataset; measure success rate on a separate control task (e.g., 'reach target'). This proves utility beyond the filter's definition.
- **Validation**: Independent check using MuJoCo (FR-008) to ensure PyBullet scores are not circularly correlated (Target correlation < 0.95).
- **Real-World Proxy**: Compare filter scores against a subset of real-world robotic telemetry (from `Robotics-Video-Text`) to ensure the filter measures actual physical correctness.
- **Statistical Test**: Two One-Sided Tests (TOST) with a predefined equivalence margin.
  - Null Hypothesis ($H_0$): Difference > 15% (Not equivalent).
  - Alternative Hypothesis ($H_1$): Difference ≤ 15% (Equivalent).
  - Power: Target ≥ 0.80 at effect size $d=0.5$. If $n < 30$, augmentation (FR-009) is applied.
  - **Power Analysis**: A pilot run (n=20) will estimate the variance of R-Bench scores to calculate the required sample size for TOST, rather than assuming a speculative effect size.

## 4. Statistical Rigor & Limitations

- **Multiple Comparisons**: TOST is a single composite test for equivalence; no family-wise error correction needed for the primary hypothesis.
- **Power Limitation**: If the curated dataset yields $n < 30$ even after augmentation, the plan explicitly reports a power limitation and refrains from claiming statistical equivalence, instead reporting effect sizes with confidence intervals.
- **Causal Claims**: The study is observational regarding the generated data. Claims are limited to "association between filtering and downstream performance" unless the generation process is randomized (which it is, via prompts).
- **Collinearity**: PyBullet and MuJoCo are independent engines; no definitional collinearity exists between the filter and the validator.

## 5. Compute Feasibility (CPU vs. GPU)

- **CPU-First**: All steps are designed for CPU. PyBullet runs natively on CPU. Diffusion training on a moderate number of parameters is feasible on CPU cores if batch size is small (e.g., 1-2) and epochs are limited.
- **GPU Escape Hatch**: If `torch` fails to initialize on CPU or the model architecture (Wan2.1) requires CUDA kernels, the execution agent will detect the error and re-run the specific training step on a Kaggle GPU (GB VRAM) with `device="cuda"` and `load_in_8bit`.
- **Decision**: Plan assumes CPU-first. The GPU escape hatch is a contingency for specific library constraints, not a default.

## 6. Risk Mitigation

- **Data Scarcity**: If < 30 videos pass filtering, FR-009 (augmentation) is triggered.
- **Training Divergence**: NaN loss check included; retry with lower learning rate (max a limited number of attempts).
- **Simulation Crashes**: Robust error handling in PyBullet filter assigns score 0 and logs the failure.
- **Circular Validation**: Real-world proxy validation ensures the filter measures actual physical correctness, not just simulation stability.