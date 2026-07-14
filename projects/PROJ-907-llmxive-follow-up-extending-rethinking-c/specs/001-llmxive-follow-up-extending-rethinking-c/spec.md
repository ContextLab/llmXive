# Feature Specification: llmXive follow-up: extending "Rethinking Cross-Layer Information Routing in Diffusion Transformers"

**Feature Branch**: `001-llmxive-static-routing`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Rethinking Cross-Layer Information Routing in Diffusion Transformers'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Trace Dynamic Routing and Identify Canonical Map (Priority: P1)

**As a** researcher, **I want** to execute the pre-trained SiT-XL/2 model with Dynamic Adaptive Routing (DAR) on a subset of validation images and record the routing weight matrices at every timestep, **so that** I can analyze the temporal evolution of information flow and determine if distinct, input-independent routing phases exist.

**Why this priority**: This is the foundational step. Without empirical evidence of the routing patterns, no static approximation can be constructed. It validates the core hypothesis that routing is driven by the noise schedule rather than content.

**Independent Test**: Can be fully tested by running the tracing script on a sample of 100 images and verifying that the output contains a complete tensor of routing weights for every block and timestep, and that clustering these weights reveals distinct modes or a valid fallback.

**Acceptance Scenarios**:

1. **Given** a pre-trained SiT-XL/2 model with DAR enabled and a subset of 100 ImageNet validation images, **When** the system runs inference with a fixed 100-timestep schedule, **Then** the system MUST record the routing weight matrices (softmax distributions over history) for every block at every timestep for all images.
2. **Given** the recorded routing vectors, **When** the system applies k-means clustering to group timesteps, **Then** the system MUST report the number of clusters identified (k) and the silhouette score; if k < 2 or the silhouette score < 0.25, the system MUST flag this as a null result for the phase-separation hypothesis.
3. **Given** the clustering results, **When** the system computes a single static routing weight vector per block, **Then** the system MUST output a "canonical routing map" derived from the dominant cluster if one exists, OR a global average of all timesteps if the clustering fails to identify distinct phases (null hypothesis case).

---

### User Story 2 - Benchmark Static Approximation vs. Dynamic Baseline (Priority: P2)

**As a** researcher, **I want** to replace the dynamic DAR module in the model architecture with the computed static routing weights and benchmark the inference latency and generation quality against the dynamic baseline, **so that** I can quantify the efficiency gains (latency reduction) and the cost in generation quality (FID degradation).

**Why this priority**: This validates the practical utility of the static approximation. It directly addresses the research question of whether the overhead can be eliminated without significant quality loss.

**Independent Test**: Can be fully tested by running the modified static model and the original dynamic model on the same 100-image subset on a CPU-only runner and comparing the resulting inference times and FID scores.

**Acceptance Scenarios**:

1. **Given** the static routing map derived from User Story 1 and the original dynamic model, **When** both models generate 100 images from the same noise seeds on a standard CPU (e.g., Intel Xeon or Apple M2), **Then** the system MUST measure the time-to-solution for 100 timesteps for both models.
2. **Given** the generated samples from both models, **When** the system computes the Fréchet Inception Distance (FID) using a pre-trained Inception network with fixed weights, **Then** the system MUST report the FID score for both the static approximation and the dynamic baseline.
3. **Given** the latency and FID results, **When** the system calculates the percentage reduction in latency and the absolute difference in FID, **Then** the system MUST report the calculated percentage reduction and absolute FID difference (e.g., "Latency reduction: X%, FID difference: Y").

---

### User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

**As a** researcher, **I want** to perform a statistical significance test on the FID scores across multiple random seeds and a sensitivity analysis on the clustering threshold, **so that** I can ensure the observed improvements are not due to chance and that the static map is robust to minor variations in the clustering parameters.

**Why this priority**: This ensures the scientific rigor of the findings. It prevents false positives from random variation and validates the stability of the "canonical" map construction.

**Independent Test**: Can be fully tested by re-running the benchmark 5 times with different seeds and varying the clustering distance threshold, then verifying the reported statistics and variance in FID scores.

**Acceptance Scenarios**:

1. **Given** FID scores for the static and dynamic models generated across 5 random seeds, **When** the system analyzes the distribution, **Then** the system MUST report the mean and standard deviation of the FID scores for both models; if a significance test is performed, it MUST use a non-parametric bootstrap (1000 resamples) or explicitly state the limitation of low power (N=5) for parametric tests.
2. **Given** the clustering distance threshold used to define the "dominant cluster," **When** the system sweeps the threshold over a small concrete set (e.g., {0.01, 0.05, 0.1}), **Then** the system MUST report how the headline FID score varies across these thresholds to confirm robustness.
3. **Given** the results of the sensitivity analysis, **When** the system compares the FID scores at different thresholds, **Then** the system MUST report the range of FID degradation observed across the sweep.

---

### Edge Cases

- What happens if the k-means clustering fails to converge or identifies only 1 cluster (indicating no distinct phases)? The system MUST flag this as a null result for the phase-separation hypothesis, report the silhouette score, and proceed to generate a "canonical map" using a global average of all timesteps.
- How does the system handle the scenario where the static model generates images with a significantly higher FID (> 0.5) than the baseline? The system MUST report the high FID difference as a valid (negative) result, indicating the static approximation is invalid for this model architecture, without halting the benchmark.
- What if the CPU memory limit (7 GB) is exceeded during the tracing of routing weights for all 100 images at once? The system MUST process images in batches of 100 to stay within memory constraints.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load a pre-trained SiT-XL/2 model with DAR enabled and run inference on a subset of 100 ImageNet validation images with a fixed 100-timestep schedule, recording routing weight matrices for every block at every timestep (See US-1).
- **FR-002**: System MUST apply k-means clustering to the recorded routing vectors; if the clustering identifies < 2 clusters or a silhouette score < 0.25, the system MUST construct the static routing map as a global average of all timesteps; otherwise, it MUST average the high-probability paths within the dominant cluster (See US-1).
- **FR-003**: System MUST replace the dynamic DAR module in the model architecture with the computed static routing weights and remove the per-timestep softmax computation overhead (See US-2).
- **FR-004**: System MUST measure the time-to-solution for 100 steps for both the dynamic baseline and the static approximation on a standard CPU (e.g., Intel Xeon or Apple M2) and report the percentage reduction (See US-2).
- **FR-005**: System MUST compute the Fréchet Inception Distance (FID) for generated samples using a pre-trained Inception network with weights fixed and independent of the routing weights being tested, and report the absolute difference (See US-2).
- **FR-006**: System MUST analyze FID scores across 5 random seeds by reporting the mean and standard deviation; if a significance test is required, it MUST use a non-parametric bootstrap (1000 resamples) or explicitly document the statistical limitations of N=5 (See US-3).
- **FR-007**: System MUST perform a sensitivity analysis by sweeping the clustering distance threshold over a concrete set (e.g., {0.01, 0.05, 0.1}) and report the variation in FID scores across the sweep (See US-3).

### Key Entities

- **Routing Weight Tensor**: A 4D tensor containing the softmax distributions over historical layers for every block, every timestep, and every image in the subset.
- **Canonical Routing Map**: A static weight vector per block derived from clustering (or global average if clustering fails), representing the average high-probability path for a specific denoising phase or the global schedule.
- **Benchmark Result**: A record containing the inference latency (seconds), FID score, percentage reduction, and statistical metrics (mean, std, p-value if applicable) for a specific model configuration (dynamic vs. static).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Inference latency reduction is measured against the dynamic DAR baseline to report the percentage reduction; **Hypothesis Target**: reduction ≥ 40% on CPU-only hardware (See FR-004, US-2).
- **SC-002**: Generation quality degradation is measured against the dynamic DAR baseline via FID to report the absolute difference; **Hypothesis Target**: difference < 0.1 points (See FR-005, US-2).
- **SC-003**: Statistical significance of the FID difference is measured by reporting mean and standard deviation across 5 random seeds, with optional non-parametric bootstrap (1000 resamples) (See FR-006, US-3).
- **SC-004**: Robustness of the static map is measured against the variation in FID scores when the clustering distance threshold is swept over {0.01, 0.05, 0.1} (See FR-007, US-3).
- **SC-005**: Memory usage during tracing is measured against the 7 GB RAM limit of the GitHub Actions free-tier runner to ensure the analysis completes without OOM errors (See FR-001, Assumptions).

## Assumptions

- The pre-trained SiT-XL/2 model with DAR enabled is available via HuggingFace or the original authors' repository and can be loaded into CPU memory without requiring GPU/CUDA acceleration (e.g., using `load_in_8bit` is not required/used; standard float32 or float16 on CPU is assumed).
- The ImageNet validation subset (100 images) fits within the ~14 GB disk limit and ~7 GB RAM limit of the GitHub Actions free-tier runner when processed in batches.
- The "canonical routing map" hypothesis assumes that the optimal information flow is primarily driven by the global noise schedule (timestep) rather than fine-grained input content, which is the core premise being tested.
- The Inception network used for FID calculation is pre-trained on ImageNet, has fixed weights, and runs efficiently on CPU without requiring GPU acceleration.
- The k-means clustering algorithm will successfully converge; if it fails to find distinct phases (k < 2 or low silhouette), the system defaults to a global average, acknowledging the null hypothesis.
- The GitHub Actions free-tier runner provides sufficient CPU cycles (≤ 6 hours) to complete the full tracing, clustering, and benchmarking pipeline for 100 images.