# Feature Specification: The Binding Problem in LLMs: Implementing Synchronized Oscillations for Feature Integration

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-06-05  
**Status**: Draft  
**Input**: User description: "The Binding Problem in LLMs: Implementing Synchronized Oscillations for Feature Integration"

## User Scenarios & Testing

### User Story 1 - Implement CPU-Tractable Oscillatory Attention Mechanism (Priority: P1)

The research team must be able to modify a pre-trained transformer architecture (e.g., DistilBERT) to inject phase-locked sinusoidal gating at a target relative frequency (scaled to token processing rate) into the attention head computations without requiring GPU acceleration or large-model inference resources.

**Why this priority**: This is the foundational intervention. Without a working, CPU-tractable implementation of the oscillatory mechanism, no downstream analysis of spectral power or behavioral performance is possible. It directly addresses the "Implementation" gap identified in the literature review.

**Independent Test**: Can be fully tested by running a forward pass of a single batch (size 8) through the modified model on a CPU-only environment, recording the raw attention activation time-series, and verifying the presence of the injected frequency component via a simple FFT.

**Acceptance Scenarios**:

1. **Given** a pre-trained DistilBERT model loaded in CPU-only mode, **When** the oscillatory gating layer is injected at a relative frequency corresponding to a high gamma range (scaled to token rate) and a forward pass is executed on a sequence of 50 tokens, **Then** the recorded attention head activations must exhibit a spectral peak within the 38-42Hz band (relative to the token processing rate) with a signal-to-noise ratio (SNR) ≥ 3.0 dB. The SNR is calculated as the ratio of the peak power in the 38-42Hz band to the median power in the adjacent 10-20Hz and 60-80Hz bands.
2. **Given** the modified model, **When** the system is run on a GitHub Actions free-tier runner (2 CPU cores, 7GB RAM), **Then** the forward pass for a batch of 8 sequences must complete within 300 seconds per batch to ensure feasibility within the 6-hour job limit.

---

### User Story 2 - Quantify Neural Alignment with Human MEG/EEG Signatures (Priority: P2)

The system must compute a quantitative similarity metric between the phase-locking dynamics of the oscillatory-transformer's attention activations and published human MEG/EEG binding-task signatures (specifically the 40Hz gamma-band response).

**Why this priority**: This addresses the core "Validation" aspect of the research question. It tests whether the artificial mechanism mimics the biological phenomenon, distinguishing this project from simple performance benchmarks.

**Independent Test**: Can be fully tested by taking the processed activation time-series from User Story 1, computing the Phase Locking Value (PLV) using a sliding window, and comparing it against a reference phase-locking profile derived from the OpenNeuro MEG dataset.

**Acceptance Scenarios**:

1. **Given** the Phase Locking Value (PLV) time-series of attention activations from the oscillatory model and a reference PLV profile from the OpenNeuro ds000246 dataset (binding task), **When** the system computes the cross-correlation over the 30-50Hz frequency band, **Then** the resulting correlation coefficient must be calculated and reported, with a baseline comparison against a non-oscillatory control model showing a difference of at least 0.15, which must be statistically significant (p < 0.05) via a permutation test.
2. **Given** the requirement for methodological rigor regarding inference framing, **When** the alignment metric is computed, **Then** the output must be explicitly labeled as an "Associational Similarity Score" rather than a causal claim, and the analysis must include a permutation test (with a sufficient number of permutations) where model-reference pair labels are shuffled to establish a p-value < 0.05 for the observed similarity against the null hypothesis of no association.

---

### User Story 3 - Evaluate Compositional Reasoning Performance (Priority: P3)

The system must evaluate the oscillatory-transformer model on standard compositional reasoning benchmarks (CLUTRR, bAbI) to determine if the injected dynamics improve multi-feature integration tasks compared to a baseline.

**Why this priority**: This tests the functional utility of the mechanism. While neural alignment is the theoretical goal, improved performance on reasoning tasks provides the practical evidence that the mechanism aids "binding" in a computational sense.

**Independent Test**: Can be fully tested by running the model on the CLUTRR dataset (small subset, e.g., a representative sample) and comparing the accuracy and F1-score against the baseline model.

**Acceptance Scenarios**:

1. **Given** the oscillatory model and a baseline model, **When** both are evaluated on the CLUTRR task (100 samples, 3-hop relations) across 5 random seeds (values: 42, 123, 456, 789, 101), **Then** the system must report the accuracy and F1-score for both, and perform a paired t-test across these seeds to determine if the difference is statistically significant (p < 0.05).
2. **Given** the constraint of multiple hypothesis testing (frequency sweep + performance metrics), **When** the results are aggregated, **Then** the system must apply a Bonferroni correction (or similar family-wise error rate control) to the reported p-values to prevent false positives.

---

### Edge Cases

- **Dataset-variable fit**: **Given** the OpenNeuro MEG datasets (ds, ds004229) do not contain a clean, isolated 40Hz gamma-band signature for the specific "feature binding" condition, **When** the analysis detects this absence (e.g., signal-to-noise ratio < 2.0 in the target band), **Then** the system MUST fall back to analyzing the broader 30-50Hz gamma-band engagement and record this fallback status in the results.
- **Threshold sensitivity**: If the 40Hz frequency assumption proves arbitrary (as noted by reviewer rosalind-franklin-simulated), the system must support a sensitivity sweep where the frequency is varied across a range of representative values to identify if the alignment is specific to 40Hz or a broader gamma phenomenon.
- **Resource exhaustion**: If the full MEG dataset exceeds the 7GB RAM limit of the free-tier runner, the system must automatically subsample the data to a size that fits and record this as a power limitation.

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement a sinusoidal gating mechanism in transformer attention heads that modulates activation values at a target relative frequency (scaled to token processing rate) consistent with established neural oscillation patterns (e.g., gamma band) without requiring GPU hardware or 8-bit quantization libraries. (See US-1)
- **FR-002**: System MUST compute Power Spectral Density (PSD) of attention head activations using Welch's method with a window size of 512 samples and [deferred] overlap to extract frequency-domain features. (See US-1)
- **FR-003**: System MUST calculate a Phase Locking Value (PLV) metric between the model's 30-50Hz spectral phase dynamics and reference human MEG/EEG phase signatures from the OpenNeuro ds000246 dataset. (See US-2)
- **FR-004**: System MUST execute a permutation test (≥1000 permutations) on the similarity metric to generate a p-value, framing the result as an associational finding rather than a causal claim. (See US-2)
- **FR-005**: System MUST evaluate the modified model on the CLUTRR and bAbI compositional reasoning benchmarks and report accuracy, F1-score, and a paired t-test result against a baseline model. (See US-3)
- **FR-006**: System MUST apply a multiple-comparison correction (e.g., Bonferroni) to all statistical tests performed across frequency sweeps and benchmark tasks to control the family-wise error rate. (See US-3)

### Key Entities

- **OscillatoryAttentionModule**: A modified transformer layer that accepts a frequency parameter and applies a time-varying sinusoidal mask to the attention weights.
- **ActivationTimeSeries**: The raw output of attention heads recorded during forward passes, serving as the input for spectral analysis.
- **NeuralReferenceSignature**: The pre-processed spectral profile derived from human MEG/EEG binding tasks, used as the ground truth for alignment comparison.
- **ReasoningBenchmarkResult**: Structured data containing accuracy, F1, and statistical significance metrics for CLUTRR/bAbI tasks.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The presence of a spectral peak in the 30-50Hz band in attention activations is measured against the injected relative frequency target to verify mechanism implementation. (See US-1)
- **SC-002**: The similarity between model and human spectral signatures is measured against a permutation-based null distribution to establish statistical significance (p < 0.05). (See US-2)
- **SC-003**: The compositional reasoning performance (accuracy/F1) is measured against the baseline non-oscillatory model to determine if the oscillatory mechanism provides a functional advantage. (See US-3)
- **SC-004**: The robustness of the frequency claim is measured by sweeping the frequency parameter over a range of {20, 30, 40, 50, 60} Hz and reporting the peak-to-peak amplitude of the variation in similarity scores. (See US-2)
- **SC-005**: The validity of the statistical inference is measured by confirming that all p-values have been corrected for multiple comparisons using a standard method (e.g., Bonferroni). (See US-3)

## Assumptions

- The OpenNeuro datasets contain sufficient trials and a distinct 30-50Hz gamma-band signature associated with feature binding tasks that can be isolated from general task-evoked responses.
- The "40Hz" frequency in the idea refers to the biological gamma-band; in the computational model, this is implemented as a relative frequency scaled to the token processing rate (e.g., 1 cycle per N tokens) rather than absolute Hertz. **Mapping Hypothesis**: For the purpose of comparison with physical MEG data, we assume 1 token processing step corresponds to 10ms of physical time.
- The pre-trained DistilBERT model (or similar) can be modified to include oscillatory gating without breaking the model's ability to converge or produce meaningful outputs on standard benchmarks.
- The GitHub Actions free-tier runner (standard CPU, 7GB RAM) is sufficient to run the forward pass, spectral analysis, and benchmark evaluation on a subsampled dataset (e.g., 100-500 samples) within the 6-hour limit.
- The human MEG/EEG data provided by OpenNeuro is pre-processed (artifact removed, filtered) and available in a format (e.g., MNE-Python compatible) that allows for direct spectral comparison without extensive re-processing that would exceed CPU limits.
- The "binding" capability in the CLUTRR/bAbI tasks is sufficiently sensitive to detect improvements from oscillatory dynamics, assuming such dynamics exist.
- **Constitution Principle VI Revision**: The implementation MUST strictly test the 40Hz gamma-band frequency hypothesis, but is not required to achieve adherence if the data suggests a different frequency is optimal, preserving the ability to falsify the hypothesis.