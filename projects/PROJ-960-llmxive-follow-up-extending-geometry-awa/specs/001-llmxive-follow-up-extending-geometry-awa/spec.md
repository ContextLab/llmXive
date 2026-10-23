# Feature Specification: llmXive follow-up: extending "Geometry-Aware Representation Denoising for Robust Multi-view 3D Recon"

**Feature Branch**: `001-geometry-aware-denoising`  
**Created**: 2026-09-03  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Geometry-Aware Representation Denoising for Robust Multi-view 3D Recon'"

## User Scenarios & Testing

### User Story 1 - Deterministic Graph-Based Feature Denoising (Priority: P1)

**User Journey**: As a researcher, I need to apply a lightweight, deterministic graph Laplacian filter to noisy multi-view feature maps to remove noise without running computationally expensive diffusion sampling steps, ensuring the process completes within the 6-hour CI time limit on CPU-only hardware.

**Why this priority**: This is the core mechanism of the research. Without a functioning deterministic filter, the comparison against diffusion baselines is impossible. It directly addresses the "computational bottleneck" motivation.

**Independent Test**: The filter can be executed on a single noisy feature map, producing a denoised output in a computationally efficient timeframe on a standard CPU, with no GPU dependencies or CUDA calls.

**Acceptance Scenarios**:

1. **Given** a set of feature maps extracted from the GARD encoder for a noisy input sequence, **When** the system applies the deterministic k-NN graph Laplacian filter with parameters optimized on a CPU, **Then** the output feature maps are produced without any CUDA errors or out-of-memory exceptions within 30 minutes.
2. **Given** a noisy feature map and the corresponding ground-truth reconstruction from held-out test scenes, **When** the filter is applied to the noisy map and the filtered features are passed through the GARD decoder and reconstruction head, **Then** the resulting denoised maps achieve a lower Chamfer Distance against ground truth than the raw noisy input, as measured on held-out test scenes.

---

### User Story 2 - Structural Property Identification and Validation (Priority: P2)

**User Journey**: As a researcher, I need to compute and analyze the spectral properties (Laplacian eigenvalues) and curvature estimates of the feature graph to identify which specific structural signatures correlate with robustness in clean data, enabling the hypothesis that static geometry suffices for denoising.

**Why this priority**: This validates the scientific hypothesis. It determines *which* properties to preserve in the filter. It is the "investigation" phase of the methodology.

**Independent Test**: The system can process a batch of clean scenes, extract the feature graph, compute the top‑k eigenvalues and curvature, and output a statistical report identifying correlations between specific eigenmodes and low reconstruction error.

**Acceptance Scenarios**:

1. **Given** a batch of clean multi-view scenes from the DA3 benchmark, **When** the system constructs the feature graph and computes the Laplacian eigen-spectrum, **Then** the system outputs a list of the top eigenvalues and their corresponding eigenvectors for each scene.
2. **Given** the computed spectral properties and the known reconstruction error of each scene, **When** a correlation analysis is performed with Bonferroni correction for ~10+ tests (threshold p < 0.005), **Then** the system performs the correlation analysis and reports the p-value (Bonferroni-corrected for ~10+ tests) for each eigenmode–robustness pair, with null results (no eigenmode meeting the corrected threshold) recorded as acceptable outcomes per Edge Cases.

---

### User Story 3 - Comparative Performance Benchmarking (Priority: P3)

**User Journey**: As a researcher, I need to compare the reconstruction accuracy (Chamfer Distance) and inference latency of the deterministic graph filter against a diffusion-based baseline to quantify if the deterministic approach recovers ≥85% of the robustness with orders-of-magnitude speedup.

**Why this priority**: This provides the final empirical evidence for the "Expected Results." It confirms whether the trade-off between accuracy and efficiency is favorable.

**Independent Test**: The system runs both the deterministic filter and the diffusion baseline on the same 50 degraded scenes, recording metrics, and produces a summary table showing the deterministic method's latency is at least 100x lower while maintaining ≥85% of the baseline's robustness.

**Acceptance Scenarios**:

1. **Given** 50 degraded test scenes and the outputs of both the deterministic filter and the diffusion baseline, **When** the system computes the Chamfer Distance for both methods against the ground truth, **Then** the deterministic method achieves Chamfer Distance within the range [noisy_baseline, diffusion_baseline], operationalizing ≥85% of the baseline's robustness recovery as CD ≤ noisy_baseline + 0.15 × (diffusion_baseline - noisy_baseline).
2. **Given** the same 50 scenes, **When** the system measures inference time on a single CPU core, **Then** the deterministic method completes the full pipeline in ≤1% of the time taken by the diffusion baseline (≥100x speedup).

---

### Edge Cases

- **What happens when** the feature graph construction results in a disconnected graph due to extreme noise? **The system MUST** default to a local smoothing kernel or a fallback nearest-neighbor strategy to ensure the Laplacian remains invertible or solvable.
- **How does the system handle** datasets where the DA3 benchmark provides incomplete multi-view sequences? **The system MUST** skip the specific scene or apply a view-interpolation step (if available in the GARD repo) before graph construction to avoid index errors.
- **What happens when** the spectral analysis reveals no significant correlation between any eigenmode and robustness? **The system MUST** flag the hypothesis as unsupported and record the null result in the final report, rather than forcing a fit.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST implement a deterministic k-nearest neighbor (k-NN) graph construction where edge weights are a function of feature similarity and geometric proximity, explicitly excluding stochastic components. (See US-1)
- **FR-002**: The system MUST compute the spectral properties (Laplacian eigenvalues) and curvature estimates of the constructed feature graph for every input scene. (See US-2)
- **FR-003**: The system MUST implement a graph Laplacian filter parameterized to preserve identified robust structural signatures while suppressing noise frequencies, optimized on held-out validation scenes using Chamfer Distance. (See US-1)
- **FR-004**: The system MUST calculate reconstruction accuracy metrics (Chamfer Distance and F-score) by passing filtered features through the original GARD decoder and a standard 3D reconstruction head. (See US-3)
- **FR-005**: The system MUST measure and record inference latency and peak memory usage for both the deterministic filter and the diffusion baseline on a single CPU core. (See US-3)
- **FR-006**: The system MUST perform a Wilcoxon signed-rank test (non-parametric alternative to paired t-test, suitable for non-normal distributions) on reconstruction errors across a set of degraded test scenes to determine if the deterministic filter and diffusion baseline produce statistically significantly different errors (two-tailed test, α=0.05). (See US-3)
- **FR-007**: The system MUST include a sensitivity analysis for the filter's decision cutoffs (e.g., number of neighbors k, frequency threshold), sweeping values over a concrete set (k ∈ {5, 10, 15}) and reporting the variation in Chamfer Distance and MSE across the sweep to ensure results are not artifacts of arbitrary threshold choices. (See US-1, US-3)
- **FR-008**: The system MUST handle disconnected feature graphs (resulting from extreme noise) by applying a local smoothing kernel or fallback nearest-neighbor strategy to ensure the Laplacian remains invertible or solvable. (See Edge Cases)
- **FR-009**: The system MUST handle incomplete multi-view sequences in the DA3 dataset by either skipping the specific scene or applying a view-interpolation step (if available in the GARD repo) before graph construction to avoid index errors. (See Edge Cases)
- **FR-010**: The system MUST flag the spectral-analysis hypothesis as unsupported and record null results in the final report when no eigenmode–robustness correlation meets the Bonferroni-corrected p-threshold (p < 0.005). (See US-2, Edge Cases)

### Key Entities

- **Feature Map**: A tensor representing the geometry-aware features extracted from the GARD encoder, containing spatial and semantic information for a specific view.
- **Feature Graph**: A graph structure where nodes represent feature vectors and edges represent similarity/proximity, used for spectral analysis and filtering.
- **Robustness Metric**: A quantitative measure (e.g., Chamfer Distance) comparing the reconstructed geometry against ground truth to evaluate noise resilience.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The reconstruction error (Chamfer Distance) of the deterministic filter is measured against the noisy baseline to verify that the filtered output achieves lower error on held-out test scenes, demonstrating that the filter recovers robustness from noise corruption. (See US-1)
- **SC-002**: The reconstruction error (Chamfer Distance) of the deterministic filter is measured against the diffusion baseline to verify if it recovers ≥85% of the baseline's robustness. This is operationalized as: CD_deterministic ≤ CD_noisy + 0.15 × (CD_diffusion − CD_noisy), where CD_noisy is the error of the raw noisy input and CD_diffusion is the error of the diffusion baseline. This interpolation-based criterion grounds the '[deferred] recovery' in the actual error landscape between the noisy input and the diffusion reference. (See US-3)
- **SC-003**: The statistical significance of the performance difference between the deterministic filter and diffusion baseline is measured using a Wilcoxon signed-rank test (two-tailed, α=0.05) on the reconstruction errors of 50 scenes to confirm the results are not due to random chance. (See US-3)
- **SC-004**: The sensitivity of the filter's performance is measured by reporting the variation in Chamfer Distance and MSE across a sweep of cutoff parameters (k ∈ {5, 10, 15}) to ensure the results are not artifacts of a single arbitrary threshold choice. (See US-1, US-3)
- **SC-005**: The correlation between specific Laplacian eigenmodes and robustness is measured using Pearson's correlation coefficient with Bonferroni correction (threshold p < 0.005 for ~10 tests) to identify which structural properties correlate with low reconstruction error; null results (no eigenmode meeting the corrected threshold) are acceptable outcomes. (See US-2)

## Assumptions

- The Depth Anything 3 (DA3) benchmark dataset and the GARD repository's synthetic degradation scripts are accessible and provide sufficient noisy multi-view sequences for the 50-scene test set.
- The GARD encoder and decoder models can be loaded and run in default precision (float32) on a CPU-only environment without requiring CUDA or 8-bit quantization.
- The feature graphs constructed from the DA3 dataset will fit within the limited RAM capacity of the GitHub Actions free-tier runner when processed in batches.
- The "geometry-awareness" of the GARD model is sufficiently captured by the extracted feature maps to allow spectral analysis to reveal robust structural signatures.
- The diffusion baseline used for comparison is the standard implementation provided in the GARD repository or a compatible public reference, ensuring a fair comparison.
- The time limit for the GitHub Actions job is sufficient to complete the full pipeline (feature extraction, graph construction, filtering, reconstruction, and benchmarking) for 50 scenes.