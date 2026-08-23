# Research Documentation

## Predicting Cognitive Flexibility from Resting-State Functional Connectivity Variability

### Overview

This research project investigates the relationship between dynamic functional connectivity patterns in the brain and cognitive flexibility, measured using the NIH Toolbox Dimensional Change Card Sort task.

### Research Question

Does variability in resting-state functional connectivity (RSFC) predict individual differences in cognitive flexibility?

### Hypothesis

Higher variability in RSFC patterns (measured as edge-wise standard deviation and Shannon entropy of sliding-window correlations) is positively associated with better cognitive flexibility scores.

### Methodology

#### Data Source
- **Population**: HCP 1200 Subjects Release
- **Imaging**: Resting-state fMRI (multi-band EPI)
- **Behavioral**: NIH Toolbox Dimensional Change Card Sort (DCCS) scores
- **Covariates**: Age, Sex, Head Motion (Mean FD), Total Scan Time

#### Preprocessing Pipeline
1. Download raw NIfTI and behavioral data from HCP
2. Apply minimal preprocessing (fMRIPrep outputs)
3. Parcellate using Schaefer 200 Parcels (7 Networks) atlas [UNRESOLVED-CLAIM: c_79e20ab6 — status=not_enough_info]
4. Calculate Mean Framewise Displacement (FD) for motion assessment
5. Exclude subjects with Mean FD > 0.2mm [UNRESOLVED-CLAIM: c_94a0082a — status=not_enough_info]

#### Feature Extraction
1. **Sliding-Window Correlation**:
 - Window size: 60 seconds [UNRESOLVED-CLAIM: c_553bd5fa — status=not_enough_info] (mandated by FR-003 for Schaefer 200 stability)
 - Step size: 1 second [UNRESOLVED-CLAIM: c_4fcfb24a — status=not_enough_info]
 - Method: Pearson correlation
2. **Edge-wise Metrics**:
 - Standard deviation of correlations across windows
 - Shannon entropy of correlation distributions
3. **Subject-level Aggregation**:
 - Mean edge standard deviation as primary `Variability_Metric`
 - Mean entropy as secondary metric

#### Statistical Analysis
1. **Linear Regression**:
 - Dependent variable: Flexibility Score (DCCS)
 - Independent variable: Variability_Metric
 - Covariates: Age, Sex, Mean FD, Total Scan Time
2. **Permutation Testing**:
 - 10,000 iterations for stable null distribution [UNRESOLVED-CLAIM: c_94bb7fc1 — status=not_enough_info]
 - Phase-shuffled surrogates for validation
3. **Multiple Comparison Correction**:
 - Benjamini-Hochberg FDR (q ≤ 0.05) for network-specific analyses [UNRESOLVED-CLAIM: c_80a5388d — status=not_enough_info]

### Technical Design Decisions

#### Window Size Selection (60s vs 30s)
- **Default**: Constitution Principle VII suggests 30s windows
- **Decision**: 60s windows mandated by FR-003
- **Rationale**: Schaefer 200 atlas requires longer windows for stable correlation estimation; 30s windows produce unreliable estimates for this resolution

#### Null Model Selection
- **Requirement**: FR-008 mandates phase-shuffling
- **Rationale**: Phase-shuffling preserves temporal autocorrelation while destroying phase relationships, providing a more appropriate null for dynamic connectivity than AR-surrogates

### Expected Outcomes

1. Identification of significant association between RSFC variability and cognitive flexibility
2. Quantification of effect size (Beta coefficient)
3. Validation of metric significance against phase-shuffled surrogates
4. Network-specific patterns (if post-hoc analyses are performed)

### Success Criteria

- **SC-001**: Processing success rate > 80% after exclusions
- **SC-002**: Metric significance (p < 0.05) against null model
- **SC-003**: Permutation test with 10,000 iterations for stable p-value estimation

### Limitations

- Computational constraints (7GB RAM, 6h processing time)
- Dependence on HCP data access and API availability
- Assumption of linear relationships in regression model
- Potential confounding effects of head motion despite exclusion criteria

### References

- Schaefer, A., et al. (2018). Local-Global Parcellation of the Human Cerebral Cortex. *Cerebral Cortex*.
- HCP Consortium. (2013). The Human Connectome Project: A data acquisition perspective. *NeuroImage*.
- Smith, S. M., et al. (2013). Resting-state fMRI in the Human Connectome Project. *NeuroImage*.

### Version History

- v1.0: Initial research documentation
- v1.1: Added technical design decisions and success criteria
