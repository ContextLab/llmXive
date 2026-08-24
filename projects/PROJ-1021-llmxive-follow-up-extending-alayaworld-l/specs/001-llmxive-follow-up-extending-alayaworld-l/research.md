# Research: llmXive follow-up: extending "AlayaWorld: Long-Horizon and Playable Video World Generation"

## Research Question

How does the integration of a lightweight, CPU-tractable symbolic logic layer influence the long-horizon semantic consistency of a **CPU-tractable surrogate video world model** (StyleGAN2-ADA) compared to autoregressive generation alone?

*Note: The original AlayaWorld model is not CPU-tractable. This study uses a verified StyleGAN2-ADA surrogate to test the methodology of the hybrid correction mechanism.*

## Dataset Strategy

### Verified Datasets
- **AlayaWorld**: NO verified source found. 
  - *Strategy*: The implementation assumes the AlayaWorld model weights and a representative subset of video sequences are provided as local artifacts with a specific cryptographic checksum recorded in `data/checksums.txt`. If the checksum does not match, the run fails.
  - *Feasibility Check*: The project will proceed only if the local artifact is present and checksum-verified. If not, the run will fail gracefully with a "Data Missing" error, preventing fabrication.
  - **No Substitution**: If AlayaWorld data is unavailable, the project is paused and flagged as 'Data Missing'. A synthetic video generation pipeline is NOT an appropriate substitute as it does not possess the same architectural properties or drift behaviors as AlayaWorld (or its surrogate).
- **StyleGAN2-ADA Surrogate**: 
  - *Source*: Verified Internal Manifest (`data/verified_manifest.json`).
  - *Strategy*: The surrogate model weights are sourced from a verified internal repository (e.g., "Internal Team X, Date Y") with a recorded SHA-256 hash. The `verified_manifest.json` serves as the provenance chain required by Constitution Principle II.
  - *Feasibility Check*: The run fails if the manifest is missing or the hash does not match.

### Data Processing
- **Streaming**: To adhere to the 7 GB RAM limit, the video generation and analysis pipeline will process frames in batches (e.g., 30 frames at a time) rather than loading full 60-second sequences into memory.
- **Ground Truth Subset**: A subset of ≥50 frames will be created to validate the CV pipeline (FR-007). This will be stored in `data/ground_truth/` as JSON. The Ground Truth is derived from the **Symbolic Engine's state log** (the "true" logical state), not human observation of the video, to ensure independence and avoid circularity.
- **Calibration Subset**: A separate subset of ≥50 frames will be used for CV Calibration (Phase 0) to measure systematic biases.

## Methodology

### 0. Pre-Experiment: CV Calibration & Feasibility Check
- **Feasibility Check**: Verify that the **StyleGAN2-ADA surrogate** supports dynamic prompt re-conditioning (required for correction tokens). If not, abort experiment (Scientific Soundness Concern).
- **CV Calibration**: Run the CV pipeline on a **Calibration Set** (50 frames) where the Symbolic Ground Truth is known.
  - Measure systematic biases (e.g., false negatives for specific object types).
  - Compute **Bias Correction Factors** to adjust the "Safety Filter" thresholds.
  - **Gate**: If calibration accuracy < 85%, the experiment is "Inconclusive" (SC-006).

### 1. Baseline Semantic Drift Quantification (US-1)
- **Symbolic Engine**: A deterministic Python class that tracks object states (HP, existence, position) based on a sequence of discrete user actions (e.g., "hit", "summon"). The output log is hashed (SHA-256) at each timestep and at the end to prove immutability (Constitution Principle VI).
- **Visual Analysis**: 
  - *Static Objects*: Template matching (OpenCV `matchTemplate`) to detect object presence.
  - *Motion*: Optical flow (OpenCV `calcOpticalFlowPyrLK`) to track movement.
- **Drift Score**: Calculated as the normalized difference between the symbolic state vector and the visual state vector over time.
  - **Deconvolution Formula**: $D_{intrinsic} = (D_{total} - \text{Expected Noise}) / (1 - \text{Noise Bias})$, where Expected Noise is calculated from the CV confusion matrix (TP, FP, FN rates) measured against the **Symbolic Ground Truth**. This correctly scales the noise component.
- **Validation**: Ground Truth Validation (FR-007) ensures the visual analysis accuracy is ≥85% before calculating the final score. The Ground Truth is derived from the **Symbolic Engine's state**, ensuring independence from the video generation.

### 2. Hybrid Correction Mechanism (US-2) - **Within-Sequence Counterfactual**
- **Experimental Design**: For every action sequence (Seed $S$), generate **two** video streams:
  - **Stream A (Baseline)**: Identical latent noise as Stream B, but **NO** correction tokens injected.
  - **Stream B (Hybrid)**: Identical latent noise as Stream A, but **deterministic** correction token injection (p=1.0) upon discrepancy detection.
- **Correction Logic**:
  - If CV detects a discrepancy (Visual State != Symbolic State) AND **Bias-Corrected Confidence** > Threshold, inject the correction token into Stream B.
  - **Safety Filter**: Uses bias-corrected confidence from Phase 0 to avoid amplifying systematic CV errors.
- **Statistical Test**: A **Paired T-Test** compares the drift scores of Stream A vs. Stream B for each seed.
  - Null Hypothesis ($H_0$): Mean difference (Drift_B - Drift_A) = 0.
  - Alternative Hypothesis ($H_1$): Mean difference < 0 (Hybrid reduces drift).
  - Significance Level: $\alpha = 0.05$.
  - **Null Result Hypothesis**: The plan explicitly acknowledges that the frozen surrogate model may ignore the correction tokens. A null result is a valid finding (the method does not work for frozen models).

## Statistical Rigor & Limitations

- **Multiple Comparisons**: Only one primary hypothesis test (Paired T-Test) is performed per seed. No family-wise error correction is needed for the primary metric.
- **Power Analysis**: With N=10 seeds, the study has [deferred] power to detect a **Large Effect Size** (d ≈ 0.85). The plan explicitly targets a [deferred] reduction (SC-001) which corresponds to a large effect. If the actual drift reduction is smaller (e.g., 10-15%), the study is **underpowered**. The plan acknowledges this limitation and will report the result as "inconclusive" if the effect size is not detected, rather than claiming a negative result.
- **Sensitivity Analysis**: A sensitivity analysis is provided to show the detectable effect size for N=10.
- **Causal Inference**: The study uses a **Within-Sequence Counterfactual Design** (Stream A vs Stream B with identical latent noise). This isolates the causal effect of the correction token by controlling for generative variance. The randomization is in the *application* of the token (deterministic in Stream B, none in Stream A), satisfying the requirement for statistical inference on the mechanism's efficacy.
- **Collinearity**: The symbolic engine's state is derived directly from the input actions. There is no collinearity between predictors as the input is a single sequence of actions.
- **Measurement Validity**: The CV pipeline's validity is ensured via FR-007 (Ground Truth Validation) and Phase 0 (CV Calibration). If accuracy < 85%, the drift score is flagged as invalid. The Ground Truth is derived from the **Symbolic Engine's state**, not human observation of the video, to ensure independence.

## Compute Feasibility (CPU-First)

- **Model**: A CPU-tractable surrogate model (StyleGAN2-ADA 256x256, 8-bit quantized) is used for generation. The original AlayaWorld is not CPU-tractable.
- **CV Primitives**: OpenCV operations are highly optimized for CPU and will run efficiently within the 7 GB RAM limit.
- **GPU Escape Hatch**: Not applicable. The research question explicitly targets CPU-tractable solutions.

## Decision/Rationale

- **Method Choice**: Classical computer vision (template matching, optical flow) is chosen over deep learning-based object detection (e.g., YOLO) to ensure CPU feasibility and deterministic behavior.
- **Dataset Strategy**: Since no verified URL for AlayaWorld exists, the plan relies on local artifacts with SHA-256 checksums. The **StyleGAN2-ADA** surrogate is sourced from a verified internal manifest (`data/verified_manifest.json`) to satisfy Constitution Principle II. No substitution is permitted.
- **Statistical Approach**: **Within-Sequence Counterfactual Design** with Paired T-Test is chosen to isolate the causal effect of the correction token. This resolves the causal inference contradiction by controlling for generative variance.
- **Ground Truth Independence**: Ground Truth is derived from the **Symbolic Engine's state**, not human observation of the video, to ensure the CV pipeline measures the video's content independently of the video's drift.
- **Null Result**: The plan explicitly acknowledges that the frozen surrogate model may ignore the correction tokens. A null result is a valid finding (the method does not work for frozen models).
- **Theoretical Distinction**: "Semantic Drift" is defined as the deviation of the visual output from the *logical* ground truth (Symbolic Engine). "Model Hallucination" is a subset of this where the model generates states not supported by the input actions. This distinction prevents conflation of 'training recall failure' with 'logic failure'.
- **CV Calibration**: Systematic CV biases are measured and corrected before the main experiment to prevent the correction mechanism from amplifying noise.
