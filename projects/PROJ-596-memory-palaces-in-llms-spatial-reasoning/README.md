# Memory Palaces in LLMs: Spatial Reasoning for Enhanced Episodic Recall

**Project ID**: PROJ-596

## Overview

This project investigates whether explicit spatial organization of latent representations (a "Memory Palace" architecture) improves episodic recall in Large Language Models compared to standard attention mechanisms.

## Research Questions

1. Can LLMs be trained to utilize a 2D grid-based memory slot system for episodic storage?
2. Does spatial indexing reduce interference between similar episodic traces compared to standard transformer attention?
3. What are the measurable structural correlates (interference distance, slot occupancy) of this organization?

## Methodology

- **Datasets**: bAbI Task 3, LAMBADA, Story Cloze Test.
- **Models**: GPT-2 Medium (4-bit quantized) with a spatial memory adapter vs. standard baseline.
- **Metrics**: Exact-match recall, interference distance, slot occupancy distribution.
- **Statistical Analysis**: Paired t-tests across 5 random seeds with Bonferroni correction.

## Project Structure

```
code/
├── data/ # Data download and processing scripts
├── models/ # Model definitions (Baseline, Spatial, Fallback)
├── training/ # Training loops and memory monitoring
├── evaluation/ # Metrics and statistical analysis
└── utils/ # Logging and utilities
data/
├── raw/ # Downloaded datasets and checksums
└── processed/ # Preprocessed data
artifacts/
├── results/ # Training logs, metrics, and reports
└── schemas/ # Configuration schemas
docs/ # Documentation, specs, and research notes
```

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

## Key Personnel & Reviewers

- **Project Lead**: [Lead Name]
- **Reviewers**:
 - Rosalind Franklin (Structural Metrics & Quantitative Support)
 - John von Neumann (Formal Mapping & Addressing Costs)
 - Eric Kandel (Biological Plausibility & Synaptic Stability)

## License

Research use only.