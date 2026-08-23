# Project Plan: llmXive Follow-Up - Extending FashionChame

## 1. Executive Summary
This project extends the FashionChame framework to evaluate text-driven garment generation fidelity. We replace the original Human3.6M dependency with **DeepFashion2** and adapt motion labeling from skeletal velocity to **optical flow magnitude** to align with available data modalities.

## 2. Dataset Strategy
- **Primary Dataset**: DeepFashion2 (via HuggingFace).
- **Rationale**: Rich garment annotations and high-resolution images suitable for texture/pattern analysis.
- **Data Loading**: Implemented via `datasets.load_dataset(..., streaming=True)` to manage memory constraints.
- **Motion Proxy**: Since DeepFashion2 lacks skeletal annotations, we derive motion labels from **optical flow magnitude** calculated between consecutive frames.

## 3. Implementation Phases

### Phase 1: Setup
- Initialize project structure (`code/`, `data/`, `tests/`).
- Configure dependencies (torch-cpu, transformers, datasets, etc.).
- Set up linting (ruff) and formatting (black).

### Phase 2: Foundational
- Implement citation validation for DeepFashion2 references.
- Create content hashing for artifacts.
- Configure `settings.yaml` with DeepFashion2 specific paths and thresholds.
- **Spec Amendment (T042)**: Update `spec.md` and `plan.md` to reflect the switch from Human3.6M to DeepFashion2 and skeletal velocity to optical flow.

### Phase 3: User Story 1 - Fidelity Benchmarking
- Implement `FeasibilityFilter` for DeepFashion2 metadata.
- Generate text prompts from garment attributes.
- Compute LPIPS/SSIM for text-driven vs. image-driven baselines.
- Stratify results by `GarmentFeatureClass`.

### Phase 4: User Story 2 - Latency Verification
- Measure end-to-end inference time on CPU.
- Verify < 50ms per frame threshold.
- Identify bottlenecks in text encoding and adapter layers.

### Phase 5: User Story 3 - Statistical Significance
- Perform ANOVA on fidelity scores across feature classes.
- Analyze sensitivity of optical flow thresholds.
- Generate final statistical report.

## 4. Risk Management
- **Risk**: DeepFashion2 metadata may be incomplete for certain attributes.
 - **Mitigation**: Implement `FeasibilityFilter` to exclude ambiguous samples.
- **Risk**: Optical flow calculation may be computationally expensive.
 - **Mitigation**: Use efficient CPU-based flow algorithms and stream processing.
- **Risk**: Text-to-image fidelity may be low for complex textures.
 - **Mitigation**: Quantify loss via LPIPS and report relative degradation.

## 5. Success Criteria
- Successfully generate a stratified benchmark subset from DeepFashion2.
- Produce a fidelity report showing relative loss by garment feature class.
- Verify text-driven adapter meets latency requirements on CPU.
- Confirm statistical significance of observed fidelity differences.