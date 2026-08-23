# Project Plan: llmXive Follow-up - Extending FashionChame to DeepFashion2

## 1. Executive Summary

This project adapts the FashionChame benchmark pipeline to utilize the **DeepFashion2**
dataset instead of Human3.6M. The primary motivation is to evaluate text-driven garment
attribute fidelity in a real-world fashion context where skeletal data is unavailable.
Consequently, motion analysis will rely on **optical flow magnitude**.

## 2. Project Scope

### In Scope
- Implementation of data loaders for DeepFashion2 using `datasets` library with streaming.
- Adaptation of motion label derivation to use optical flow magnitude.
- Stratified sampling based on DeepFashion2 garment attributes (color, pattern, texture).
- Execution of fidelity benchmarks (LPIPS, SSIM) on CPU.
- Statistical analysis of results across garment feature classes.

### Out of Scope
- Use of Human3.6M dataset.
- Skeletal joint velocity calculations.
- GPU-accelerated inference (CPU-only requirement).

## 3. Technical Approach

### 3.1 Data Pipeline
- **Source**: DeepFashion2 via Hugging Face `datasets`.
- **Loading Strategy**: Streaming mode (`streaming=True`) to handle large dataset size.
- **Filtering**:
 1. Filter by `GarmentFeatureClass` using DeepFashion2 metadata.
 2. VLM verification using `blip-large` to ensure prompt-image consistency.
 3. Exclude low-confidence samples.

### 3.2 Motion Analysis
- **Method**: Optical Flow Magnitude.
- **Implementation**: Compute flow between consecutive frames using OpenCV or similar.
- **Labeling**: Assign 'High' or 'Low' motion labels based on magnitude threshold.

### 3.3 Benchmark Execution
- **Baseline**: Image-driven adapter.
- **Target**: Text-driven adapter (CLIP embeddings).
- **Metrics**: LPIPS, SSIM, Inference Latency.
- **Statistical Tests**: ANOVA, Bonferroni correction.

## 4. Implementation Phases

### Phase 1: Setup
- Initialize project structure (`code/`, `data/`, `tests/`).
- Configure dependencies and linting tools.

### Phase 2: Foundational
- Implement citation validation and manifest generation.
- Configure settings for DeepFashion2 and optical flow parameters.
- **Critical**: Update spec and plan to reflect DeepFashion2 and optical flow changes (Task T042).

### Phase 3: User Story 1 - Feature-Stratified Fidelity Benchmarking
- Implement `feasibility_filter.py` for DeepFashion2 attribute tagging.
- Implement VLM verification step.
- Create stratified subset logic.
- Execute baseline and text-driven adapter.
- Generate fidelity report with relative loss per class.

### Phase 4: User Story 2 - Real-Time Latency Verification
- Measure inference latency per frame.
- Verify 50ms threshold on CPU.
- Implement streaming/batched mode with memory trigger.

### Phase 5: User Story 3 - Statistical Significance & Sensitivity
- Perform ANOVA on fidelity scores.
- Implement sensitivity sweep for optical flow threshold.
- Generate sensitivity analysis report.

### Phase N: Polish & Cross-Cutting Concerns
- Run full benchmark.
- Generate final manifests.
- Update documentation.

## 5. Risk Management

- **Risk**: DeepFashion2 dataset size may exceed memory limits.
 - **Mitigation**: Use streaming mode and chunked processing.
- **Risk**: Optical flow computation may be slow on CPU.
 - **Mitigation**: Optimize flow calculation and use subsampling if necessary.
- **Risk**: Garment attribute annotations may be noisy.
 - **Mitigation**: Implement VLM verification to filter low-confidence samples.

## 6. Dependencies

- **External**: DeepFashion2 dataset (Hugging Face).
- **Internal**: None (Phase 1 and 2 must be completed first).

## 7. Success Criteria

- System successfully loads and processes DeepFashion2 data via streaming.
- Motion labels are correctly derived from optical flow magnitude.
- Fidelity report shows distinct scores for color, pattern, and texture classes.
- Latency measurements meet the 50ms threshold.
- Statistical significance is established for observed fidelity differences.