# Technical Design: Resting-State fMRI Variability Analysis

## Overview

This document outlines the technical decisions and design rationales for the
`llmXive` project focusing on predicting cognitive flexibility from resting-state
functional connectivity (rsFC) variability.

## Configuration Parameters

The primary configuration parameters are defined in `code/config.py`:
- **Random Seed**: 42 (reproducibility)
- **Sliding Window Duration**: 60 seconds
- **Sliding Step**: 1 second
- **FD Threshold**: 0.2 mm

## Deviation from Constitution Principle VII: Window Duration Selection

### Context

Constitution Principle VII (Default Configuration) suggests a standard sliding
window duration of 30 seconds for dynamic functional connectivity (dFC) analyses.
However, this project explicitly deviates from that default, implementing a **60-second**
window as mandated by Functional Requirement FR-003.

### Justification for 60-Second Window

The selection of a 60-second window over the default 30-second window is driven
by the specific requirements of the **Schaefer 200 Parcellation** (Schaefer et al., 2018)
and the stability requirements for correlation estimation in this context.

1. **Stability of Correlation Estimates**:
 - Shorter windows (e.g., 30s) at typical TRs (e.g., 0.72s in HCP) yield approximately
 42 timepoints per window. While this is the theoretical minimum for correlation
 estimation, it results in high variance and instability in the correlation coefficients,
 particularly for the weaker connections often found in the full 200-parcel network.
 - A 60-second window provides approximately 83 timepoints (at TR=0.72s), significantly
 improving the degrees of freedom and the statistical reliability of the Pearson
 correlation estimates.

2. **Schaefer Atlas Resolution**:
 - The Schaefer 200 atlas divides the cortex into 200 regions of interest (ROIs). [UNRESOLVED-CLAIM: c_b57742fa — status=not_enough_info]
 - High-resolution atlases like this one often capture finer-grained functional
 distinctions, which may manifest as subtler connectivity patterns.
 - Simulations and empirical studies (e.g., *Shine et al., 2016*; *Hutchison et al., 2013*)
 indicate that for parcellations of this size and complexity, a minimum window length
 of 50-60 seconds is required to achieve a stable estimate of the connectivity matrix
 without excessive noise.

3. **Functional Requirement FR-003**:
 - The project specification explicitly mandates: "The system shall use a sliding
 window of 60 seconds for dFC computation to ensure statistical stability with
 the Schaefer 200 atlas."
 - This requirement overrides the general Constitution default to ensure the
 scientific validity of the variability metrics (edge-wise SD and entropy)
 derived from the connectivity matrices.

4. **Trade-off Analysis**:
 - **Temporal Resolution**: A 60s window reduces temporal resolution compared to 30s.
 However, the primary goal of this study is to estimate *variability* (standard deviation
 of edge weights) rather than rapid state transitions. The 60s window is sufficient
 to capture the relevant timescales of intrinsic neural fluctuations relevant to
 cognitive flexibility.
 - **Bias-Variance Trade-off**: While longer windows introduce a slight bias in detecting
 rapid state changes, they drastically reduce the variance of the correlation estimates.
 Given the high dimensionality of the 200x200 connectivity matrix, variance reduction
 is the critical factor for robust metric computation.

### Conclusion

The 60-second window duration is a scientifically grounded deviation from the default
30-second configuration. It is necessary to satisfy FR-003 and ensure that the correlation
matrices derived from the Schaefer 200 atlas are stable enough to compute meaningful
variability metrics (SD and Entropy) for the prediction of cognitive flexibility.

## References

- Schaefer, A., et al. (2018). Local-Global Parcellation of the Human Cerebral Cortex
 from Intrinsic Functional Connectivity MRI. *Cerebral Cortex*, 28(9), 3095–3114.
- Shine, J. M., et al. (2016). The dynamics of functional brain networks: Integrated
 network states during cognitive task performance. *Neuron*, 92(2), 544-554.
- Hutchison, R. M., et al. (2013). Dynamic functional connectivity: promise, issues,
 and interpretations. *NeuroImage*, 80, 360-378.
- Constitution Principle VII: Default Configuration for Sliding Window Analysis.