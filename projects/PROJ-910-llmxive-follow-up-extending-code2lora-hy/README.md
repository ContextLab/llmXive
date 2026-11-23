# llmXive: Code2LoRA Follow-up

**Project**: PROJ-910-llmxive-follow-up-extending-code2lora-hy

**Status**: Research Implementation in Progress

## Overview

This project extends the "Code2LoRA: Hypernetwork-Generated Adapters for Code Language Models under Software Evolution" research. It implements an **AST-based adapter generation** pipeline that replaces the original neural encoder with a lightweight, static-analysis-driven hypernetwork.

The goal is to generate repository-specific LoRA adapters using only static AST features (cyclomatic complexity, inheritance depth, token histograms, import graph centrality) while maintaining performance comparable to the neural baseline, but with significantly reduced generation latency and resource requirements.

## Key Features

- **AST-Based Feature Extraction**: Extracts static code metrics without executing code or requiring a GPU.
- **Lightweight MLP Hypernetwork**: Projects AST feature vectors into LoRA adapter weights.
- **Resource-Constrained Execution**: Enforces 2-core CPU limit and 7 GB RAM limit.
- **Comprehensive Evaluation**: Compares AST-based adapters against the original Code2LoRA neural baseline on the RepoPeftBench dataset.
- **Sensitivity Analysis**: Identifies the minimal feature set required to maintain >80% of baseline accuracy.

## Prerequisites

- Python 3.9+
- CUDA-capable GPU (optional, for evaluation; generation runs on CPU)
- 8 GB+ RAM recommended

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd PROJ-910-llmxive-follow-up-extending-code2lora-hy

# Install dependencies
pip install -r requirements.txt
```

## Data Setup

Real data must be downloaded before running the pipeline.

```bash
# Download RepoPeftBench (Python subset)
python code/data/download_repopeftbench.py

# Download a sample repository for adapter generation
python code/data/download_sample_repo.py
```

## Usage

The pipeline is controlled via `code/main.py`.

### Generate Adapter

Generate a repository-specific LoRA adapter using AST features:

```bash
python code/main.py generate --repo-path data/raw/sample_repo --output data/adapters/my_adapter.safetensors
```

### Evaluate Adapter

Evaluate the generated adapter on RepoPeftBench:

```bash
python code/main.py evaluate --adapter data/adapters/my_adapter.safetensors --output data/results/ast_scores.csv
```

### Sensitivity Analysis

Run sensitivity analysis to determine the minimal feature set:

```bash
python code/main.py sensitivity --output data/results/sensitivity_summary.csv
```

### Baseline Latency Comparison

Measure and compare generation latency against the neural baseline:

```bash
python code/main.py baseline-latency
python code/main.py latency-compare
```

## Project Structure

```
.
├── code/
│ ├── main.py # CLI entry point
│ ├── data/ # Data download scripts
│ ├── feature_extractor/ # AST parsing and graph building
│ ├── hypernetwork/ # MLP projection and adapter generation
│ ├── evaluation/ # Evaluation, comparison, and stats
│ └── utils/ # Logging, config, resource monitoring
├── data/
│ ├── raw/ # Downloaded datasets
│ ├── processed/ # Processed data artifacts
│ └── adapters/ # Generated LoRA adapters
├── tests/ # Unit and integration tests
├── specs/ # Design documents
├── requirements.txt
└── README.md
```

## Resources

- **CPU Limit**: 2 cores (enforced via `taskset`)
- **RAM Limit**: 7 GB (enforced via `resource` module)
- **Timeout**: 6 hours (enforced via `signal` module)

## Contributing

This is a research project. Please refer to `specs/001-ast-based-adapter-generation/` for detailed design documents and user stories.

## License

Research use only. See LICENSE file for details.
