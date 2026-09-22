# Research Documentation

## Overview

This project investigates the topological properties of early trajectory spans in deep-research agents to predict collapse. The core hypothesis is that agents with low connectivity and branching in their early reasoning spans are more likely to collapse.

## Methodology

### Data Source
- **Dataset**: TELBench (NJU-LINK/TELBench)
- **Sampling**: First 30% of spans (cutoff_depth=0.30)
- **Graph Construction**: Directed Acyclic Graph (DAG) based on co-reference and citation detection

### Metrics
1. **Global Connectivity**: Ratio of actual edges to possible edges
2. **Average Branching Factor**: Mean out-degree of nodes

### Prediction Model
- **Threshold**: 20th percentile of the success class (Spec FR-004)
- **Decision Rule**: If connectivity < threshold, predict collapse

### Evaluation
- **Metrics**: Precision, Recall, F1, Accuracy
- **Correlation**: Pearson correlation between connectivity and collapse
- **Significance**: Permutation test (p < 0.05)
- **Power Analysis**: Cohen's d and post-hoc power calculation

### Sensitivity Analysis
- **Threshold Sweep**: {0.01, 0.05, 0.1}
- **Percentile Sweep**: {10, 20, 30}

## Results

The pipeline produces a comprehensive report (`data/processed/results_report.json`) containing:
- Baseline connectivity of success class
- Optimal threshold (20th percentile)
- Prediction performance metrics
- Correlation significance
- Power analysis results
- Sensitivity analysis matrices

## Limitations

- **Construct Validity**: Graph construction relies on heuristic co-reference detection
- **Dataset Size**: Power analysis may flag insufficient samples
- **CPU Only**: All computations are performed on CPU

## Reproducibility

- All seeds are configurable in `code/config.py`
- The pipeline is deterministic when run with the same seed
- Raw data is cached with checksums for verification

## Future Work

- Improve co-reference detection
- Extend to later trajectory spans
- Investigate other topological metrics
- Explore multi-modal reasoning patterns
