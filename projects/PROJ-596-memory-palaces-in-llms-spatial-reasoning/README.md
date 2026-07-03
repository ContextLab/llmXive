# Memory Palaces in LLMs: Spatial Reasoning for Enhanced Episodic Recall

**Project ID**: PROJ-596

## Overview

This project investigates whether explicit spatial organization of memory slots within Large Language Models (LLMs) can enhance episodic recall performance compared to standard attention mechanisms. Inspired by the human "method of loci" (Memory Palace) and biological place cells in the hippocampus, we implement a spatial memory architecture and evaluate it against baselines on standard reasoning and story completion benchmarks.

## Research Questions

1. Does enforcing a 2D spatial grid for memory slot assignment improve exact-match recall on episodic tasks?
2. What is the measurable cost (compute, memory) of spatial indexing versus baseline attention?
3. How does interference distance correlate with recall accuracy in spatially organized vs. non-spatial models?

## Repository Structure

```
projects/PROJ-596-memory-palaces-in-llms-spatial-reasoning/
├── code/ # Source code for models, training, and evaluation
│ ├── models/ # Model architectures (Spatial Transformer, Baselines)
│ ├── training/ # Training loops and memory monitoring
│ ├── evaluation/ # Metrics and statistical analysis
│ ├── data/ # Data download and preprocessing scripts
│ └── utils/ # Logging and utility functions
├── data/ # Data artifacts (raw, processed)
├── artifacts/ # Experimental results, logs, and reports
├── tests/ # Unit and integration tests
├── specs/ # Project specifications and design documents
├── docs/ # Documentation (quickstart, research notes)
├──.gitignore
└── README.md
```

## Prerequisites

- Python 3.10+
- PyTorch 2.0+
- CUDA 11.8+ (recommended for training)

## Quick Start

1. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

2. **Download Datasets**:
 ```bash
 python code/data/download.py
 ```

3. **Run Training & Evaluation**:
 ```bash
 python code/main.py
 ```

## Key Artifacts

- `artifacts/results/run_summary.json`: Summary of training runs across random seeds.
- `artifacts/results/statistical_summary.json`: Statistical comparison of spatial vs. baseline models.
- `artifacts/results/interference_distance.json`: Quantitative metric for spatial organization efficacy.

## Reviewer Notes

This project addresses concerns raised by simulated reviewers regarding:
- **Measurable Structural Correlates**: (Rosalind Franklin) Quantified via interference distance and slot occupancy metrics.
- **Spatial vs. Logical Addressing**: (John von Neumann) Explicit mapping of spatial coordinates to transformer attention heads.
- **Biological Plausibility**: (Eric Kandel) Implementation of consolidation-like mechanisms via slot occupancy logging.

## License

MIT License