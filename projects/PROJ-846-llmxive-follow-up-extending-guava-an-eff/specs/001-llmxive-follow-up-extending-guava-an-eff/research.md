# Research: llmXive follow-up: extending "Guava: An Effective and Universal Harness for Embodied Manipulation"

## 1. Problem Statement & Hypothesis

**Hypothesis**: Replacing high-fidelity multimodal vision encoders with lightweight, symbolic perception modules (object classes, 2D bounding boxes, centroids) preserves long-horizon task success rates in embodied manipulation, provided the "harness" (reasoning loops) remains intact.

**Research Question**: Does the "seeing-to-doing gap" necessitate raw pixel-level semantic grounding, or can symbolic abstractions suffice for tasks involving geometric primitives (stacking, drawer opening)?

**Methodological Correction**: To isolate the "reasoning" capability from "perception" noise, we do **not** compare the Symbolic-Guava agent against the original visual Baseline-Guava agent. Instead, we compare it against an **Oracle-Symbolic** agent (which uses the same symbolic inputs but follows the ground-truth action sequence). This ensures that any performance drop is attributed to the LLM's reasoning limitations, not the inherent superiority of visual encoders.

## 2. Dataset Strategy

### 2.1 Primary Dataset: Guava Trajectories
The study relies on the **Guava** dataset, a collection of visual trajectories for embodied manipulation.
- **Source**: The spec assumes the Guava dataset (<2,000 trajectories) is publicly available.
- **Verified Source**: *No verified URL found in the provided "# Verified datasets" block.*
- **Strategy**: The implementation will attempt to fetch Guava from its canonical public repository. If no open, programmatic source is found, the plan will **fail to execute** rather than fabricate data. The `download_guava.py` script will include a check for the existence of the dataset and raise a `DatasetUnavailableError` if the source is inaccessible.
- **Risk**: If the Guava dataset is unavailable, the project is blocked. No substitute dataset supports the *visual trajectory* nature of the task.

### 2.2 Data Transformation Strategy
1. **Ingestion**: Download raw Guava trajectories (video frames + actions).
2. **Symbolic Conversion**:
   - Use **OpenCV** for image preprocessing.
   - Use **ONNX Runtime** with a pre-trained **YOLO-tiny** model (quantized for CPU) to detect objects.
   - Generate `SymbolicObservation` JSONs: `{class, bbox, centroid, color_histogram}`.
   - **Latency Check**: Measure inference time. If > 150ms, log as "latency-induced failure" (FR-008).
3. **Perception Validation (Critical)**:
   - Before training, compute **Precision, Recall, and mAP** of the YOLO-tiny model against the Guava ground-truth annotations.
   - If **Recall < 90%**, the pipeline halts or flags the "perception failure" category as the dominant error source. This prevents conflating poor perception with poor reasoning.
4. **Storage**: Save transformed trajectories to `data/processed/symbolic_guava/`.

## 3. Model Strategy

### 3.1 Base Model
- **Model**: `Phi-3-mini` (1.5B parameters).
- **Rationale**: Small enough for potential CPU inference, large enough for complex reasoning.
- **Source**: Hugging Face (`microsoft/Phi-3-mini-4k-instruct`).
- **Fine-tuning**:
  - **Method**: LoRA (Low-Rank Adaptation) to reduce memory footprint.
  - **Input**: `SymbolicObservation` JSONs formatted as text prompts.
  - **Output**: Action abstractions (e.g., "GRAB_OBJECT").
  - **Hardware**:
    - **Primary**: CPU (2 cores, 7GB RAM). If OOM or time > 4h, trigger **GPU Escape Hatch** (Kaggle, 16GB VRAM, 8-bit quantization).
    - **Constraint**: The evaluation phase **must** run on CPU to satisfy Constitution Principle VII.

### 3.2 Baseline: Oracle-Symbolic
- **Definition**: An agent that receives the **exact same symbolic inputs** (YOLO-tiny detections) as the LLM but has access to the **ground-truth action sequence** (or a perfect policy) for the task.
- **Rationale**: This isolates the "seeing-to-doing" gap. If the LLM performs significantly worse than the Oracle-Symbolic agent, the gap is due to the LLM's reasoning limitations, not the perception module. Comparing to a visual baseline (Baseline-Guava) would be invalid because it conflates perception fidelity with reasoning capability.
- **Statistical Test**: Permutation Test (10,000 iterations) comparing Symbolic-Guava success rate vs. Oracle-Symbolic success rate.

## 4. Statistical Rigor

- **Multiple Comparisons**: Not applicable (single primary hypothesis).
- **Sample Size**: N=50 held-out tasks (per spec FR-004).
  - **Power Limitation**: N=50 is small. The study is explicitly framed as a **feasibility and effect-size estimation** study. The Permutation Test is robust, but the study acknowledges low power to detect small effect sizes (high Type II error risk). A non-significant result (p ≥ 0.05) does not prove equivalence; it may indicate insufficient power.
- **Causal Claims**: Observational (simulation). Claims limited to "associational" unless the simulation environment is randomized.
- **Measurement Validity**:
  - **YOLO-tiny**: Validity verified via the Perception Validation Phase (Recall > 90%).
  - **Success Rate**: Binary (Success/Fail) based on simulation physics.
- **Collinearity**: Not applicable (predictors are symbolic states, not derived from each other in a way that creates perfect collinearity).

## 5. Feasibility & Compute

- **CPU-First**:
  - **Perception**: OpenCV + ONNX YOLO-tiny is CPU-tractable. Target: ≤150ms/frame.
  - **Inference**: Phi-mini (4-bit quantized) on CPU is feasible for 50 tasks.
  - **Training**: Phi-3-mini LoRA on CPU is **borderline**. If >4h, the plan switches to the **GPU Escape Hatch** (Kaggle) for training only.
- **GPU Escape Hatch**:
  - **Trigger**: CPU training exceeds 4h or OOM.
  - **Method**: 8-bit quantization, small batch size, fewer epochs (scaled down to fit 9h kernel).
  - **Constraint**: Evaluation **must** be re-run on CPU for final metrics. Training time/convergence metrics are **not** reported as primary results if GPU is used.

## 6. Decision/Rationale

| Decision | Rationale |
| :--- | :--- |
| **YOLO-tiny (ONNX)** | Lightweight, CPU-optimized, sufficient for geometric primitives (blocks, drawers). |
| **Phi-3-mini** | Smallest viable LLM for complex reasoning; 1.5B fits in 7GB RAM (4-bit). |
| **Permutation Test** | Robust for small N (50) and non-normal binary data. |
| **Oracle-Symbolic Baseline** | Isolates the reasoning gap by removing the visual perception variable. |
| **GPU Escape Hatch** | Necessary to ensure training completes; evaluation remains CPU-only to satisfy edge constraints. |
| **No Synthetic Data** | Plan uses real Guava data. If unavailable, the project halts. |
| **Power Limitation Acknowledgement** | N=50 is small; results are interpreted as effect-size estimates, not definitive hypothesis tests. |