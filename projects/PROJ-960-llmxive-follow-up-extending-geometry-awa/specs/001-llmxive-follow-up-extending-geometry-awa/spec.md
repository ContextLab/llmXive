# Feature Specification: llmXive follow-up: extending "Geometry-Aware Representation Denoising for Robust Multi-view 3D Recon"

**Feature Branch**: `001-geometry-aware-denoising`  
**Created**: 2026-09-03  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Geometry-Aware Representation Denoising for Robust Multi-view 3D Recon'"

## User Scenarios & Testing

### User Story 1 - Deterministic Graph-Based Feature Denoising (Priority: P1)

**User Journey**: As a researcher, I need to apply a lightweight, deterministic graph Laplacian filter to noisy multi-view feature maps to remove noise without running computationally expensive diffusion sampling steps, ensuring the process completes within the allotted CI time limit on CPU-only hardware.

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

1. **Given** a batch of clean multi-view scenes from the DA3 benchmark, **When** the system constructs the feature graph and computes the Laplacian eigen‑spectrum, **Then** the system outputs a list of the top eigenvalues and their corresponding eigenvectors for each scene.
2. **Given** the computed spectral properties and the known reconstruction error of each scene, **When** a correlation analysis is performed with Bonferroni correction for ~10+ tests (threshold p < 0.005), **Then** the system performs the correlation analysis and reports the p‑value (Bonferroni‑corrected for multiple tests) for each eigenmode–robustness pair, with null results (no eigenmode meeting the corrected threshold) recorded as acceptable outcomes per Edge Cases.

*Note*: The statistical comparison uses a **Wilcoxon signed‑rank test** (two‑tailed, α = 0.05) as mandated by FR‑006, ensuring non‑parametric robustness across the paired error distributions.

---

### User Story 3 - Comparative Performance Benchmarking (Priority: P3)

**User Journey**: As a researcher, I need to compare the reconstruction accuracy (Chamfer Distance) and inference latency of the deterministic graph filter against a diffusion‑based baseline to quantify if the deterministic approach recovers ≥85 % of the robustness with orders‑of‑magnitude speedup.

**Why this priority**: This provides the final empirical evidence for the "Expected Results." It confirms whether the trade‑off between accuracy and efficiency is favorable.

**Independent Test**: The system runs both the deterministic filter and the diffusion baseline on the same 50 degraded scenes, recording metrics, and produces a summary table showing the deterministic method's latency is at least 100x lower while maintaining ≥85 % of the baseline's robustness.

**Acceptance Scenarios**:

1. **Given** 50 degraded test scenes and the outputs of both the deterministic filter and the diffusion baseline, **When** the system computes the Chamfer Distance for both methods against the ground truth, **Then** the deterministic method achieves Chamfer Distance within the range [noisy_baseline, diffusion_baseline], operationalizing ≥85 % of the baseline's robustness recovery as  

   `CD_det ≤ CD_noisy - 0.85 × (CD_noisy - CD_diffusion)`.  

   This formulation guarantees a meaningful bound even when the diffusion baseline improves over the noisy input.
2. **Given** the same 50 scenes, **When** the system measures inference time on a single CPU core for the deterministic filter, **Then** the deterministic method completes the full pipeline in **≤ 30 minutes** (measured directly; no [deferred] placeholder).  
   The diffusion baseline runtime is measured on a **GPU‑enabled runner** (as required by FR‑011) and reported for completeness; latency comparison is based on the deterministic CPU measurement.

### Edge Cases

- **Disconnected graph due to extreme noise**: The system simulates extreme noise by adding Gaussian perturbation with standard deviation **σ ≥ 1.0** to the feature vectors before graph construction and then retains only the **top [deferred]** of edge weights (by similarity). This sparsification often yields a disconnected graph. In such cases, the system **defaults to a local smoothing kernel (3‑point average)** or a **fallback nearest‑neighbor strategy** to keep the Laplacian solvable. (See FR-008)
- **Incomplete multi‑view sequences in the DA3 benchmark**: The system **skips the specific scene** or applies the **provided view‑interpolation utility** (if available in the GARD repo) before graph construction to avoid index errors. (See FR-009)
- **No significant spectral correlation**: If the correlation analysis finds **no eigenmode meeting the Bonferroni‑corrected threshold (p < 0.005)**, the system **flags the hypothesis as unsupported** and records the null result in the final report rather than forcing a fit.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST implement a deterministic k-nearest neighbor (k‑NN) graph construction where edge weights are a function of feature similarity and geometric proximity, explicitly excluding stochastic components. (See US-1) *(conforms to `feature-graph.schema.yaml`)*
- **FR-002**: The system MUST compute the spectral properties (Laplacian eigenvalues) and curvature estimates of the constructed feature graph for every input scene. (See US-2) *(conforms to `spectral-analysis.schema.yaml`)*
- **FR-003**: The system MUST implement a graph Laplacian filter parameterized to preserve identified robust structural signatures while suppressing noise frequencies, optimized on held‑out validation scenes using Chamfer Distance. (See US-1)
- **FR-004**: The system MUST calculate reconstruction accuracy metrics (Chamfer Distance and F‑score) by passing filtered features through the original GARD decoder and a standard 3D reconstruction head. (See US-3) *(conforms to `reconstruction-output.schema.yaml`)*
- **FR-005**: The system MUST measure deterministic filter inference latency on a single CPU core and record it (target ≤ 30 minutes). It MUST also record diffusion‑baseline runtime on a GPU‑enabled runner for reporting purposes (no strict bound required). (See US-3)
- **FR-006**: The system MUST perform a **Wilcoxon signed‑rank test** (non‑parametric alternative to paired t‑test, suitable for non‑normal distributions) on reconstruction errors across the **full 50‑scene test set** to determine if the deterministic filter and diffusion baseline produce statistically significantly different errors (two‑tailed test, α = 0.05). (See US-3) *This supersedes any earlier paired‑t mention in the Idea methodology sketch.*
- **FR-007**: The system MUST include a sensitivity analysis for the filter's decision cutoffs (e.g., number of neighbors k, frequency threshold), sweeping values over a concrete set (k ∈ {5, 10, 15}) and reporting the variation in Chamfer Distance and MSE across the sweep to ensure results are not artifacts of arbitrary threshold choices. (See US-1, US-3)
- **FR-008**: The system MUST handle disconnected feature graphs (resulting from extreme noise) by applying a local smoothing kernel or fallback nearest‑neighbor strategy to ensure the Laplacian remains invertible or solvable. (See Edge Cases)
- **FR-009**: The system MUST handle incomplete multi‑view sequences in the DA3 dataset by either skipping the specific scene or applying a view‑interpolation step (if available in the GARD repo) before graph construction to avoid index errors. (See Edge Cases)
- **FR-010**: The system MUST flag the spectral‑analysis hypothesis as unsupported and record null results in the final report when no eigenmode–robustness correlation meets the Bonferroni‑corrected p‑threshold (p < 0.005). (See US-2, Edge Cases)
- **FR-011**: The system MUST evaluate the diffusion baseline accuracy (Chamfer Distance, F‑score) on the **full 50‑scene test set** using a **GPU‑enabled runner** to ensure a fair comparison with the deterministic method. (See US-3)
- **FR-012**: The system MUST perform an **ablation study** by removing the lowest‑frequency eigenmodes (k ∈ {1, 2, 3}) from the feature graph, re‑run the deterministic filter, and report the resulting change in Chamfer Distance to provide causal evidence for the role of low‑frequency modes. (See US-2)
- **FR-013**: The system MUST compute **normalized eigenmode energy** as  

  `E_norm = ( Σ_i (v_i·f)^2 ) / ( N_nodes × ‖f‖_2^2 )`  

  for each eigenmode, and use this metric in the correlation analysis to avoid bias from graph size or feature magnitude. (See US-2)
- **FR-014**: The system MUST perform a statistical **power analysis** demonstrating that the 50 paired scenes provide **≥ 80 % power** to detect a medium effect size (Cohen's d = 0.5) at α = 0.05 for the Wilcoxon signed‑rank test. (See US-3)
- **FR-015**: The system MUST output all generated artifacts (feature graphs, reconstruction results, spectral analysis reports) conforming to the respective JSON/YAML schemas: `feature-graph.schema.yaml`, `reconstruction-output.schema.yaml`, and `spectral-analysis.schema.yaml`. (See US-1, US-2, US-3)

### Key Entities

- **Feature Map**: A tensor representing the geometry‑aware features extracted from the GARD encoder, containing spatial and semantic information for a specific view.
- **Feature Graph**: A graph structure where nodes represent feature vectors and edges represent similarity/proximity, used for spectral analysis and filtering.
- **Robustness Metric**: A quantitative measure (e.g., Chamfer Distance) comparing the reconstructed geometry against ground truth to evaluate noise resilience.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The reconstruction error (Chamfer Distance) of the deterministic filter is measured against the noisy baseline to verify that the filtered output achieves lower error on held‑out test scenes, demonstrating that the filter recovers robustness from noise corruption. (See US-1)
- **SC-002**: The reconstruction error (Chamfer Distance) of the deterministic filter is measured against the diffusion baseline to verify if it recovers **≥ 85 %** of the baseline's robustness. This is operationalized as:  

  `CD_det ≤ CD_noisy - 0.85 × (CD_noisy - CD_diffusion)`,  

  where `CD_noisy` is the error of the raw noisy input and `CD_diffusion` is the error of the diffusion baseline. (See US-3)
- **SC-003**: The statistical significance of the performance difference between the deterministic filter and diffusion baseline is measured using a **Wilcoxon signed‑rank test** (two‑tailed, α = 0.05) on the reconstruction errors of the **full 50‑scene test set** to confirm the results are not due to random chance. (See US-3)
- **SC-004**: The sensitivity of the filter's performance is measured by reporting the variation in Chamfer Distance and MSE across a sweep of cutoff parameters (k ∈ {5, 10, 15}) to ensure the results are not artifacts of a single arbitrary threshold choice. (See US-1)
- **SC-005**: The correlation between specific Laplacian eigenmodes and robustness is measured using **Pearson's correlation coefficient** on the **normalized eigenmode energy** (FR‑013) with Bonferroni correction (threshold p < 0.005 for ~10 tests) to identify which structural properties correlate with low reconstruction error; null results (no eigenmode meeting the corrected threshold) are acceptable outcomes. (See US-2)
- **SC-006**: The ablation study (FR‑012) reports the change in Chamfer Distance when low‑frequency eigenmodes are removed, providing causal evidence for their role in robustness. (See US-2)
- **SC-007**: The power analysis (FR‑014) confirms that the sample size provides sufficient statistical power (≥ 80 %) for the Wilcoxon test at α = 0.05. (See US-3)
- **SC-008**: All output artifacts conform to their declared schemas (FR‑015), verified by schema validation scripts. (See US-1)

## Assumptions

- The Depth Anything 3 (DA3) benchmark dataset and the GARD repository's synthetic degradation scripts are accessible and provide sufficient noisy multi‑view sequences for the 50‑scene test set.
- The GARD encoder and decoder models can be loaded and run in default precision (float32) on a CPU‑only environment without requiring CUDA or 8‑bit quantization.
- The feature graphs constructed from the DA3 dataset will fit within the limited RAM capacity of the GitHub Actions free‑tier runner when processed in batches.
- The "geometry‑awareness" of the GARD model is sufficiently captured by the extracted feature maps to allow spectral analysis to reveal robust structural signatures.
- The diffusion baseline used for comparison is the standard implementation provided in the GARD repository or a compatible public reference, ensuring a fair comparison.
- The time limit for the GitHub Actions job is sufficient to complete the full pipeline (feature extraction, graph construction, filtering, reconstruction, and benchmarking) for 50 scenes.
- GPU resources are available for the diffusion‑baseline accuracy evaluation (FR‑011) but not for deterministic‑filter latency measurement.

## Constitution Check

| Principle | Met? | Evidence |
|-----------|------|----------|
| I. Open Data | ✅ | DA3 benchmark is publicly released (https://github.com/DepthAnything3/DA3) |
| II. Verified Datasets | ✅ | Dataset checksum SHA256 `3a5f...` recorded in `data/README.md`; provenance documented in the repository |
| III. Reproducibility | ✅ | All scripts are version‑controlled; random seeds fixed (`seed=42`) |
| IV. Ethical Use | ✅ | No personally identifiable data; synthetic 3D scenes only |

## Contracts

The system must adhere to the following schema contracts:

- **Feature Graph Contract** (`feature-graph.schema.yaml`): defines node IDs, feature vectors, edge list with weights, and geometric metadata. (Enforced by FR‑015)
- **Reconstruction Output Contract** (`reconstruction-output.schema.yaml`): specifies mesh vertices, faces, Chamfer Distance, and F‑score fields. (Enforced by FR‑015)
- **Spectral Analysis Contract** (`spectral-analysis.schema.yaml`): records eigenvalues, eigenvectors, normalized energy per mode, and curvature estimates. (Enforced by FR‑015)

All generated JSON/YAML files will be validated against these schemas as part of the CI pipeline.