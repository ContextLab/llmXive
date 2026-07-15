# Cognitive Fatigue Prediction Pipeline

## Overview
This pipeline predicts cognitive fatigue from resting-state EEG complexity metrics.
It implements a three-stage process: data retrieval/preprocessing, complexity feature
extraction, and statistical correlation analysis.

## Pipeline Architecture

### Phase 1: Data Retrieval (User Story 1)
- **Source**: Sleep-EDF dataset from PhysioNet (fallback: SHHS)
- **Preprocessing**: 1-40Hz bandpass filtering, artifact rejection (±100µV threshold)
- **Output**: Cleaned EEG segments in `data/processed/`

### Phase 2: Feature Extraction (User Story 2)
- **Metrics**: Lempel-Ziv Complexity (LZC) and Permutation Entropy (PE)
- **Granularity**: Per-channel calculation for each resting-state segment
- **Output**: `data/processed/lzc_metrics.csv`, `data/processed/pe_metrics.csv`

### Phase 3: Analysis (User Story 3)
- **Methods**: Pearson/Spearman correlation, Benjamini-Hochberg correction
- **Modes**: Paired (delta vs delta) or cross-sectional (baseline vs baseline)
- **Output**: Statistical reports in `data/analysis/`

## Configuration

Parameters are defined in `code/config.yaml`:

```yaml
filtering:
 low_cutoff: 1.0 # Hz
 high_cutoff: 40.0 # Hz
artifacts:
 amplitude_threshold_uv: 100 # microvolts
 min_segment_duration_sec: 120
datasets:
 primary: sleep-edf
 fallback: shhs
statistics:
 correlation_method: spearman
 alpha_level: 0.05
 fdr_method: benjamini-hochberg
```

## Data Sources

### Primary: Sleep-EDF (PhysioNet)
- **URL**: https://physionet.org/content/sleep-edf/
- **ID**: `sleep-edf`
- **Content**: 153 subjects with EEG recordings and fatigue ratings
- **Validation**: Requires both resting-state EEG and paired pre/post fatigue scores

### Fallback: SHHS (Sleep Heart Health Study)
- **URL**:
- **ID**: `shhs`
- **Content**: Large-scale sleep study with EEG and clinical measures
- **Usage**: Activated if Sleep-EDF lacks required variables or N < 30

## Statistical Interpretation Guidelines

### Lempel-Ziv Complexity (LZC)
- **Range**: 0.0 to 1.0 (normalized)
- **Interpretation**:
 - **Higher LZC**: More complex, less predictable signal patterns
 - **Lower LZC**: More regular, predictable patterns
- **Fatigue Context**:
 - **Adaptive Simplification**: Decreased LZC may indicate efficient resource allocation
 - **Degenerative Noise**: Increased LZC may indicate system instability

### Permutation Entropy (PE)
- **Range**: 0.0 to log2(order!) ({{claim:c_fb3cf25e}})
- **Interpretation**:
 - **Higher PE**: Greater randomness/complexity in ordinal patterns
 - **Lower PE**: More deterministic structure
- **Fatigue Context**: Complementary to LZC; robust to amplitude variations

### Correlation Analysis
- **Method**: Spearman rank correlation (default) for non-parametric robustness
- **Multiple Comparisons**: Benjamini-Hochberg FDR correction across electrodes
- **Significance Thresholds**:
 - Primary: p ≤ 0.05 (FDR-corrected)
 - Secondary: p ≤ 0.01 (FDR-corrected)
- **Effect Size**: Cohen's d reported for significant correlations

### Sensitivity Analysis
- **Purpose**: Assess robustness across significance thresholds
- **Output**: `data/analysis/sensitivity_table.csv`
- **Interpretation**: Consistent significance across thresholds indicates robust findings

## Execution

### Prerequisites
- Python 3.11+
- Virtual environment with dependencies from `code/requirements.txt`

### Running the Pipeline
```bash
# Download and validate data
python code/download.py

# Preprocess EEG data
python code/preprocess.py

# Extract complexity features
python code/features.py

# Run correlation analysis
python code/analysis.py

# Generate final report
python code/report.py
```

## Output Files

| File | Description |
|------|-------------|
| `data/processed/lzc_metrics.csv` | Per-channel LZC values |
| `data/processed/pe_metrics.csv` | Per-channel permutation entropy |
| `data/analysis/correlation_results.csv` | Correlation coefficients and p-values |
| `data/analysis/sensitivity_table.csv` | Results at multiple significance thresholds |
| `data/analysis/final_report.md` | Comprehensive analysis report |
| `logs/pipeline.log` | Execution and rejection logs |

## Limitations and Considerations

1. **Dataset Constraints**: Reliance on public datasets may limit demographic diversity
2. **Signal Quality**: Artifact rejection thresholds (±100µV) may exclude valid data
3. **Complexity Metrics**: LZC and PE capture different aspects of signal dynamics
4. **Causal Inference**: Correlation does not imply causation; fatigue mechanisms remain complex
5. **Computational Limits**: Streaming implementation targets <6GB RAM usage

## References

- **Sleep-EDF Dataset**: Kemp et al. (2000), PhysioNet
- **Lempel-Ziv Complexity**: Lempel & Ziv (1976)
- **Permutation Entropy**: Bandt & Pompe (2002)
- **Benjamini-Hochberg**: Benjamini & Hochberg (1995)
