# Specification: llmXive Follow-up - Extending FashionChame

## 1. Overview

This project extends the FashionChame model to evaluate text-driven garment reference fidelity against image-driven baselines, specifically adapted for the DeepFashion2 dataset. The system benchmarks visual fidelity (LPIPS, SSIM), measures inference latency on CPU, and performs statistical significance testing on garment attribute degradation.

## 2. Functional Requirements

### FR-001: Text-Driven Adapter
Implement a text-cross-attention adapter that maps frozen CLIP text embeddings to the reference key-value (KV) slots of the generation backbone.

### FR-002: Data Loading & Streaming
The system MUST load the **DeepFashion2** dataset using `datasets.load_dataset(..., streaming=True)` to handle large-scale video data without exceeding memory limits.
**Constraint**: Do NOT use Human3.6M. The dataset must be DeepFashion2.
**Motion Label Derivation**: Since skeletal joint velocity is unavailable in DeepFashion2, motion labels MUST be derived from **optical flow magnitude** calculated between video frames (see FR-010).

### FR-003: Fidelity Metrics
Compute LPIPS and SSIM scores on CPU for every generated frame against the ground truth.

### FR-004: CPU-Only Execution
All inference and metric computation MUST run on CPU. No CUDA calls are permitted.

### FR-005: Statistical Significance
Perform ANOVA on fidelity scores across garment feature classes (Color, Pattern, Texture) and apply Bonferroni correction for multiple hypothesis testing.

### FR-006: Sensitivity Analysis
Sweep the optical flow consistency threshold to evaluate robustness of motion labeling.

### FR-007: Latency Measurement
Measure frame-level inference time and verify it remains [deferred] on an 8-core CPU.

### FR-008: Prompt Generation
Generate blind metadata-to-text prompts from DeepFashion2 annotations for the text adapter.

### FR-009: Benchmark Runner
Execute both the image-driven baseline and the text-driven adapter on a stratified subset of the data.

### FR-010: Motion Labeling (Amended)
**Original Requirement**: Derive motion labels from skeletal joint velocity (Human3.6M).
**Amended Requirement**: Derive motion labels from **optical flow magnitude**.
- Calculate optical flow magnitude between consecutive frames.
- Apply a configurable threshold to classify frames as "High Motion" or "Low Motion".
- Store these labels in `data/processed/motion_labels.json`.

### FR-011: Feasibility Filtering (Amended)
**Original Requirement**: Filter Human3.6M clips based on skeletal velocity.
**Amended Requirement**: Filter **DeepFashion2** samples based on **optical flow magnitude** and garment attribute availability.
- Tag clips by `GarmentFeatureClass` (Color, Pattern, Texture).
- Use a VLM (BLIP-Large) to verify prompt confidence.
- Exclude samples with low VLM confidence (< 0.8) or conflicting attributes.

### FR-012: Memory Management
Implement a streaming processor that triggers batched processing when memory usage exceeds a predefined threshold.

### FR-013: Manifest Generation
Generate content hashes for all code and data artifacts.

### FR-014: Citation Validation
Verify DeepFashion2 URLs and model references using token-overlap logic.

## 3. Non-Functional Requirements

- **Performance**: End-to-end benchmark must complete within 6 hours on a CPU-free tier instance.
- **Reproducibility**: All experiments must use fixed seeds defined in `settings.yaml`.
- **Data Integrity**: No synthetic data fallbacks. If real data fetch fails, the system must raise an error.

## 4. Assumptions

- **Dataset**: DeepFashion2 is the sole source of video/garment data. Human3.6M is explicitly excluded.
- **Motion Proxy**: Optical flow magnitude is a valid proxy for "skeletal joint velocity" in the context of garment motion analysis for this dataset.
- **Hardware**: Evaluation is performed on a standard 8-core CPU instance with at least 16GB RAM.
- **Dependencies**: All required Python packages are available via `pip` and compatible with Python 3.11.

## 5. Data Model

- **GarmentFeatureClass**: Enum {COLOR, PATTERN, TEXTURE}
- **MotionLabel**: Enum {HIGH, LOW} (derived from optical flow magnitude)
- **FidelityScore**: Float (LPIPS, SSIM)
- **Latency**: Float (milliseconds)

## 6. Deliverables

- `data/processed/filtered_subset_manifest.json`: List of valid samples.
- `data/processed/motion_labels.json`: Optical flow derived motion labels.
- `data/processed/fidelity_report.json`: Aggregated scores by feature class.
- `data/processed/sensitivity_analysis.csv`: Threshold variation results.
- `data/processed/manifest.json`: Content hashes.
plan.md: |
# Project Plan: llmXive Follow-up - Extending FashionChame

## 1. Executive Summary

This project extends the FashionChame framework to evaluate the fidelity of text-driven garment references using the **DeepFashion2** dataset. The original plan assumed Human3.6M and skeletal velocity; this plan amends those assumptions to align with DeepFashion2's capabilities, utilizing **optical flow magnitude** as the motion proxy.

## 2. Dataset Strategy

- **Source**: DeepFashion2 (Publicly available via HuggingFace `datasets`).
- **Loading Strategy**: Streaming mode (`streaming=True`) to handle large video files without loading entirely into RAM.
- **Motion Labels**: Replaced "skeletal joint velocity" with "optical flow magnitude".
 - Implementation: Calculate optical flow between frames using OpenCV.
 - Thresholding: Configurable threshold in `settings.yaml` to binarize motion.

## 3. Implementation Phases

### Phase 1: Setup
- Initialize directory structure (`code/`, `data/`, `tests/`).
- Configure environment (Python 3.11, `requirements.txt`).
- Set up linting (ruff) and formatting (black).

### Phase 2: Foundational Infrastructure
- **Data Loading**: Implement `loader.py` for DeepFashion2 streaming.
- **Validation**: Implement `validate_citations.py` for DeepFashion2 URLs.
- **Configuration**: Update `settings.yaml` with DeepFashion2 paths and optical flow thresholds.
- **Spec Amendment**: **T042** - Update `spec.md` and `plan.md` to reflect DeepFashion2 and optical flow changes.

### Phase 3: User Story 1 - Fidelity Benchmarking
- Implement `feasibility_filter.py` using optical flow magnitude and VLM verification.
- Implement `stratified_subset.py` for balanced sampling.
- Run baseline and text-adapter pipelines.
- Generate `fidelity_report.json` with relative loss calculations.

### Phase 4: User Story 2 - Latency Verification
- Implement latency measurement in `runner.py`.
- Verify CPU-only execution and ms threshold.

### Phase 5: User Story 3 - Statistical Analysis
- Implement ANOVA and Bonferroni correction in `significance.py`.
- Perform sensitivity analysis on optical flow thresholds.

### Phase 6: Polish & Delivery
- Generate final manifests and documentation.
- Verify full pipeline execution time.

## 4. Risk Mitigation

- **Data Availability**: DeepFashion2 is stable and accessible via HuggingFace.
- **Motion Proxy Validity**: Optical flow is a standard computer vision proxy for motion when skeletal data is absent.
- **Memory Constraints**: Streaming mode and memory-triggered batch processing (configurable trigger) mitigate OOM risks.

## 5. Success Criteria

- System successfully loads and processes DeepFashion2 samples.
- Motion labels are generated via optical flow magnitude.
- Fidelity report shows statistically significant differences between text and image references.
- Inference latency remains [deferred] per frame on CPU.
- All artifacts are reproducible and manifest-verified.