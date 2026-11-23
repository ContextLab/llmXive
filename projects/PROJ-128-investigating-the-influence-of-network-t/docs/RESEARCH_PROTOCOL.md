# Research Protocol Documentation

## Research Question

**Do topological properties of structural brain networks derived from diffusion MRI predict the prevalence, stability, and switching speed of recurrent activity patterns?**

**Important Clarification**: This study investigates **associational relationships** only. The term "predict" is used in a statistical sense (correlation/regression), not causal inference. All conclusions are framed as associations, not causation.

## Methodological Framework

### Data Sources

- **Structural Data**: Human Connectome Project (HCP) diffusion MRI (dMRI)
 - Tractography-based connectivity matrices
 - 180 cortical regions (HCP-MMP atlas)
- **Functional Data**: HCP resting-state fMRI
 - 1200 subjects (or subset)
 - 1200 time points per subject
 - TR = 0.72 seconds

### Preprocessing Pipeline

#### 1. Structural Network Construction

**Input**: dMRI tractography data
**Process**:
- Generate structural connectivity matrix (180x180)
- Apply proportional density threshold
- Exclude subjects with sparsity >90%

**Output Metrics**:
- Global Efficiency
- Average Clustering Coefficient
- Modularity (Louvain algorithm)

**Reference**: T015 in `code/preprocess/structural.py`

#### 2. Dynamic Functional State Extraction

**Input**: fMRI time series
**Process**:
- Sliding-window correlation (30 TR window, 1 TR step)
- **Leave-One-Out (LOO) K-Means**:
 - For subject i: Compute centroids from subjects N-1 (excluding i)
 - Assign subject i's windows to LOO centroids
 - Ensures statistical independence

**Output Metrics**:
- Dwell Time (mean time per state)
- Number of Visited States
- State Transition Frequency

**Reference**: T016-T018 in `code/preprocess/functional.py`

### Statistical Analysis

#### 1. Correlation Testing

**Process**:
- Normality check (Shapiro-Wilk, α=0.05)
- Pearson (normal) or Spearman (non-normal) correlation
- Correlate each structural metric with each dynamic metric

**Output**: Correlation matrix (r-values, p-values)

**Reference**: T024-T025 in `code/analysis/correlation.py`

#### 2. Multiple Comparison Correction

**Process**:
- Benjamini-Hochberg FDR correction (q=0.05)
- Flag significant findings after correction

**Output**: FDR-corrected significance flags

**Reference**: T026 in `code/analysis/correlation.py`

#### 3. Robustness Analysis

**Window Length Sensitivity** (T031):
- Baseline: 30 TR
- Sensitivity: 20 TR
- Metric: Absolute difference in correlation coefficients

**Density Threshold Sensitivity** (T032):
- Baseline: Configured density
- Variation: ±5%
- Metric: Stability of graph metrics

**Reference**: `code/analysis/robustness.py`

### Quality Control

#### Exclusion Criteria

Subjects are excluded and logged if:
- Graph convergence fails (K-means does not converge)
- Sparsity >90% (structural network too sparse)
- Data loading errors

**Output**: `data/logs/exclusion_log.json`

**Reference**: T020 in `code/main.py`

#### Associational Language Audit

**Process**:
- Scan all reports for causal language (e.g., "causes", "leads to", "determines")
- Flag violations
- Ensure "associational" framing throughout

**Output**: `data/reports/associational_language_audit.json`

**Reference**: `code/reports/audit_associational_language.py`

## Statistical Assumptions

### Independence

- **LOO K-Means**: Ensures subject i's data never influences their own state assignment
- **Cross-validation**: Not applicable (LOO is the validation strategy)

### Normality

- Shapiro-Wilk test (α=0.05) determines correlation method
- Non-normal distributions use Spearman rank correlation

### Multiple Comparisons

- FDR correction controls false discovery rate at q=0.05
- All metric pairs tested, not just "significant" ones

## Limitations

### Methodological

1. **Tractography Uncertainty**: dMRI tractography has known limitations (false positives/negatives)
2. **Temporal Resolution**: fMRI TR=0.72s limits detection of fast dynamics
3. **K-Means Assumptions**: Assumes spherical clusters of equal variance

### Statistical

1. **Associational Only**: No causal inference; correlations do not imply causation
2. **Sample Size**: Power depends on cohort size (HCP 1200 subjects)
3. **Multiple Testing**: FDR correction may be conservative

### Computational

1. **CPU-Only**: No GPU acceleration; processing time may be long
2. **Memory Constraints**: ~7GB RAM limit; chunked processing for large datasets
3. **Disk Space**: ~14GB required for full cohort

## Reproducibility

### Random Seeds

All random operations use fixed seeds (defined in `code/config.py`):
- K-Means initialization
- Data shuffling (if applicable)
- Sampling (if applicable)

### Data Versioning

- HCP dataset version documented
- Preprocessing parameters logged
- All code version-controlled

### Validation

- Schema validation (`contracts/output.schema.yaml`)
- Quickstart validation (`code/validate_quickstart.py`)
- Unit and integration tests (`tests/`)

## Ethical Considerations

### Data Privacy

- HCP data is de-identified
- No personal identifiers stored or processed
- Compliance with HCP data use agreement

### Reporting Bias

- All findings reported, including null results
- FDR correction applied uniformly
- Exclusion criteria pre-specified

## References

### Primary Literature

1. Van Essen, D. C., et al. (2013). The WU-Minn Human Connectome Project: an overview. NeuroImage.
2. Hutchison, R. M., et al. (2013). Dynamic functional connectivity: promise, issues, and interpretations. NeuroImage.
3. Baker, A. T., et al. (2014). Dynamic functional connectivity analysis reveals transient states of cooperation and competition in the human brain. NeuroImage.

### Methodological References

1. Rubin, D. B. (1974). Estimating causal effects of treatments in randomized and nonrandomized studies. Journal of Educational Psychology.
2. Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate: a practical and powerful approach to multiple testing. Journal of the Royal Statistical Society.
3. Newman, M. E. J. (2006). Modularity and community structure in networks. PNAS.

## Version History

- **v1.0**: Initial protocol (T001-T035 complete)
- **Documentation**: Updated T050 (README, architecture, contributing, quickstart)

## Contact

For questions about this protocol, contact the project maintainers.
