# Research Documentation: Where Do Deep-Research Agents Go Wrong?

## Abstract

This research investigates whether early-stage topological patterns in deep-research
agent trajectories can predict eventual collapse. By analyzing the co-reference and
citation structure of the first 30% of agent trajectories from the TELBench dataset,
we compute Global Connectivity and Average Branching Factor metrics to identify
predictors of failure.

## Introduction

Deep-research agents often exhibit "collapse" behaviors where they fail to complete
complex tasks. This study hypothesizes that early-stage graph topology—specifically
low connectivity and low branching—correlates with eventual failure.

## Methodology

### Data Source
- **Dataset**: TELBench (`NJU-LINK/TELBench`) from HuggingFace
- **Selection**: All trajectories with sufficient span length
- **Filtering**: Only the first `int(len(spans) * 0.30)` spans are analyzed

### Graph Construction
1. **Parsing**: Extract spans from JSON trajectories
2. **Co-reference Resolution**:
 - URL matches (regex)
 - Verbs like "see"/"refer" + number (e.g., "see Fig 1")
 - Shared Named Entities (NER)
3. **DAG Building**: Construct a directed graph excluding ground-truth labels

### Metrics
- **Global Connectivity**: `edges / (nodes * (nodes - 1) / 2)`
- **Average Branching Factor**: `sum(out-degrees) / N`
- **Linear Reasoning Index**: Ratio of nodes with in-degree=1, out-degree=1, and edges=nodes-1

### Prediction Strategy
- **Primary Threshold**: 20th percentile of the success class (FR-004)
- **Comparative Analysis**: F1-max threshold (for reporting only)
- **Sensitivity Analysis**: Sweeps over {0.01, 0.05, 0.1} and percentile ranges

## Results

The pipeline generates the following key artifacts:

- `results_report.json`: Comprehensive summary including metrics, thresholds, and conclusions
- `evaluation_results.json`: Precision, Recall, F1, and Confusion Matrix
- `sc_002_result.json`: Pearson/Spearman correlation significance test
- `linear_reasoning_report.json`: Analysis of chain-like reasoning patterns
- `sensitivity_heatmap.png`: Visual robustness check

## Limitations

- **Construct Validity**: Graph construction relies on heuristic co-reference rules;
 automated spot-checks are performed (T042a).
- **Dataset Size**: If the success class has < 5 samples, the pipeline halts to
 prevent statistical invalidity.
- **CPU-Only**: All algorithms are designed to run on CPU; no GPU acceleration is used.

## Reproducibility

- **Seeds**: All RNG seeds are read from `code/config.py`
- **Data Caching**: Raw data is cached with checksums in `data/raw/`
- **Determinism**: The pipeline produces identical outputs for identical inputs

## References

- TELBench Dataset: `NJU-LINK/TELBench` on HuggingFace
- Spec: `specs/001-gene-regulation/spec.md`
- Plan: `plan.md`
