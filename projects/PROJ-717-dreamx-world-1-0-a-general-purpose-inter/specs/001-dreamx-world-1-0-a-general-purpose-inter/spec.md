# Feature Specification: DreamX-World 1.0: A General-Purpose Interactive World Model

**Feature Branch**: `001-dreamx-world-1-0`  
**Created**: 2026-06-30  
**Status**: Draft  
**Input**: User description: "DreamX-World 1.0: A General-Purpose Interactive World Model"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dataset Correlation Quantification (Priority: P1)

The system MUST compute and report the statistical coupling between visual texture frequencies and motion vectors in the training datasets (RealEstate10K, DL3DV) to establish the baseline "texture-motion entanglement" metric.

**Why this priority**: This is the foundational predictor variable. Without quantifying the correlation in the training data, the subsequent analysis of zero-shot failure cannot be attributed to texture bias. It is the independent variable of the study.

**Independent Test**: The system can be fully tested by running the correlation analysis pipeline on a small, static subset of the RealEstate10K dataset and outputting a single scalar value (Canonical Correlation) with a 95% confidence interval.

**Acceptance Scenarios**:

1. **Given** a subset of 500 video frames from RealEstate10K, **When** the system computes the Laplacian pyramid texture components and optical flow vectors, **Then** it outputs a Canonical Correlation coefficient ($r_{texture-motion}$) with a standard error < 0.05.
2. **Given** a dataset where textures and motion are artificially decorrelated (synthetic control), **When** the analysis runs, **Then** the reported Canonical Correlation coefficient must be statistically indistinguishable from zero ($p > 0.05$).

---

### User Story 2 - Zero-Shot Physical Law Simulation (Priority: P2)

The system MUST generate video sequences on a "physics-shift" synthetic test set (altered gravity/friction) without fine-tuning, conditioned on specific physical law prompts, to evaluate the model's generalization capability.

**Why this priority**: This is the core dependent variable measurement. It tests the hypothesis that high texture-motion correlation in training leads to failure in simulating novel physics.

**Independent Test**: The system can be tested by generating 10 video clips using the trained model with prompts like "low gravity" and comparing the resulting object trajectories against ground-truth physics simulations.

**Acceptance Scenarios**:

1. **Given** a trained DiT model and a prompt "simulate low gravity", **When** the model generates a video of a falling object, **Then** the vertical acceleration of the object in the video (derived via pixel-to-meter scaling using known object height, 30fps frame rate, and center-of-mass tracking) must deviate from Earth-standard gravity ($9.8 m/s^2$) by at least 15% (indicating the model attempted the shift).
2. **Given** a test clip with altered friction parameters (mass=1.0kg, friction=0.5, initial velocity=0 in PyBullet), **When** the generated video is analyzed, **Then** the sliding object's stopping distance must be within 2 standard deviations of the ground-truth physics engine simulation if the model generalizes correctly.

---

### User Story 3 - Statistical Significance of Texture-Bias Constraint (Priority: P3)

The system MUST perform bootstrap permutation tests to determine if the distribution of sample-level consistency scores differs significantly between the high-entanglement training set and the decorrelated control set ($p < 0.05$).

**Why this priority**: This validates the research question. It moves from observation to statistical inference, confirming whether the texture-motion coupling is a genuine constraint on generalization.

**Independent Test**: The system can be tested by running the statistical analysis module on the collected consistency scores, outputting a p-value and confidence interval.

**Acceptance Scenarios**:

1. **Given** 1,000 bootstrap samples of consistency scores from the high-entanglement set and the decorrelated control set, **When** the system computes the 95% confidence interval of the difference in means, **Then** the interval must be finite and not contain zero if the effect is significant.
2. **Given** paired data points of (training correlation, test error) across multiple samples, **When** a bootstrap permutation test is executed, **Then** the system must output a p-value; if $p < 0.05$, the hypothesis of texture-bias constraint is supported.

---

### Edge Cases

- **What happens when** the synthetic "physics-shift" dataset generation fails to produce valid video frames due to Blender/Unity rendering errors? The system MUST log the error, skip the specific sample, and proceed with the remaining valid samples (high sample retention rate required).
- **How does the system handle** a scenario where the lightweight DiT model fails to converge on the 2-core CPU runner due to memory overflow? The system MUST trigger a fallback to a smaller batch size (halved) and a reduced resolution (e.g., 64x64), recording this scoping decision in the assumptions log.
- **What happens when** the optical flow estimation fails on rapid motion frames? The system MUST impute missing motion vectors using linear interpolation from adjacent frames and flag these samples in the final report.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST compute the mutual information or canonical correlation between high-frequency texture components (Laplacian pyramid) and optical flow vectors for the provided training datasets. (See US-1)
- **FR-002**: The system MUST generate video sequences on the synthetic "physics-shift" test set using a lightweight Diffusion Transformer (DiT) without fine-tuning, conditioned on physical law prompts. (See US-2)
- **FR-003**: The system MUST calculate the physical consistency error by comparing generated object trajectories against ground-truth simulations from an independent physics engine (PyBullet). (See US-2)
- **FR-004**: The system MUST perform bootstrap resampling on consistency scores to compute 95% confidence intervals for all measured metrics. (See US-3)
- **FR-005**: The system MUST execute a bootstrap permutation test to determine the statistical significance ($p < 0.05$) of the difference in consistency score distributions between the high-entanglement dataset and the decorrelated control set. (See US-3)
- **FR-006**: The system MUST implement multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) if more than one hypothesis test is conducted across distinct physical parameters (e.g., gravity vs. friction). (See US-3)

### Key Entities

- **Training Dataset**: Represents the source video data (RealEstate10K, DL3DV) with computed texture-motion correlation metrics.
- **Physics-Shift Test Set**: Represents the synthetic video data generated with altered physical parameters (gravity, friction) for zero-shot evaluation.
- **Consistency Score**: A quantitative metric representing the deviation between generated video trajectories and ground-truth physics simulations.
- **Correlation Metric**: The scalar value quantifying the statistical coupling between texture frequencies and motion vectors in the training data.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The statistical significance of the texture-motion constraint is measured against the null hypothesis of no difference ($p < 0.05$) using the bootstrap permutation test on consistency scores. (See US-3)
- **SC-002**: The generalization failure rate is measured against the baseline performance of a model with the same architecture retrained on a decorrelated synthetic dataset (generated by shuffling texture-motion pairs to achieve correlation < 0.1) to quantify the degradation caused by texture bias. (See US-2)
- **SC-003**: The stability of the correlation estimate is measured against the width of the 95% confidence interval derived from bootstrap resamples. (See US-3)
- **SC-004**: The validity of the threshold for "significant failure" is measured against a sensitivity analysis sweeping the discrepancy cutoff over a range of normalized pixel distances to ensure headline rates do not vary arbitrarily. (See US-2)
- **SC-005**: The independence of the predictor and outcome is measured against a Spearman correlation test between the texture-motion metric and the consistency scores, ensuring the predictor is uncorrelated with known confounders (e.g., camera motion). (See US-1)

## Assumptions

- The RealEstate10K and DL3DV datasets contain sufficient visual texture and motion data to compute reliable mutual information/canonical correlation metrics without missing variable gaps.
- The lightweight Diffusion Transformer (DiT) architecture can be trained on a standard GPU resource (e.g., 1x A100) and inferred on a 2-core CPU runner with ~7GB RAM by using gradient checkpointing and reduced batch sizes (≤ 4).
- The synthetic "physics-shift" dataset generated via Blender/Unity provides ground-truth physics labels (gravity, friction) that are accurate enough for trajectory comparison with PyBullet.
- The "texture-motion" entanglement hypothesis is framed as associational; no causal claims about physical laws are made without randomization, which is not present in this observational study of training distributions.
- The bootstrap resampling and statistical tests will complete within the GitHub Actions free-tier limit.
- The threshold for "significant failure" (e.g., deviation from ground truth) is set to a community-standard default trajectory error, with a sensitivity analysis performed over a range of absolute differences to validate robustness.