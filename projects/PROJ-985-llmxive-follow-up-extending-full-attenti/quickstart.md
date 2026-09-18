# llmXive Quick Start Guide

## Overview

This project implements a research pipeline to evaluate static sparsification heuristics against learned attention-based methods (RTPurbo) on the RULER dataset. The goal is to determine if simple, deterministic rules can approximate the performance of complex learned models for token selection in long-context scenarios.

## Prerequisites

- Python 3.11+
- 16GB+ RAM (for full dataset processing)
- CPU-only execution (no GPU required)
- ~20GB disk space for intermediate data

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd llmXive-follow-up-extending-full-attenti
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Install spaCy model** (for POS tagging):
 ```bash
 python -m spacy download en_core_web_sm
 ```

5. **Install KenLM** (for perplexity calculation):
 ```bash
 pip install kenlm
 # Note: You may need to build KenLM from source if the wheel fails:
 # git clone https://github.com/kpu/kenlm.git
 # mkdir kenlm/build && cd kenlm/build
 # cmake.. && make -j4
 # pip install../kenlm
 ```

## Project Structure

```
.
├── code/
│ ├── data/ # Data processing and feature extraction
│ ├── lib/ # Core utilities (data loader, entities)
│ ├── models/ # Model training and rule derivation
│ └── evaluation/ # Baseline execution and statistical analysis
├── data/
│ ├── intermediate/ # Intermediate processing results (H5, CSV)
│ ├── logs/ # Execution logs and anomaly reports
│ └── results/ # Final aggregated metrics and reports
├── tests/ # Unit and integration tests
├── quickstart.md # This file
└── research.md # Detailed research methodology
```

## Execution Workflow

The pipeline is designed to run in sequential phases. Each phase produces artifacts required by the next.

### Phase 1: Data Preparation (User Story 1)

1. **Download RULER Dataset** (streaming):
 ```bash
 python code/data/download.py
 ```
 *Output*: Data streamed directly to memory; no local storage of raw dataset.

2. **Extract Ground Truth (RTPurbo indices)**:
 ```bash
 python code/data/extract_ground_truth.py
 ```
 *Output*: `data/intermediate/attention_maps.h5`, `data/logs/anomalies.csv`

3. **Compute Static Features**:
 ```bash
 python code/data/compute_features.py
 ```
 *Output*: `data/intermediate/static_features.csv`

4. **Merge Datasets**:
 ```bash
 python code/data/merge_datasets.py
 ```
 *Output*: `data/intermediate/merged_dataset.csv`

### Phase 2: Model Training & Rule Derivation (User Story 2)

1. **Train Static Classifiers** (multiple seeds):
 ```bash
 python code/models/train_static.py
 ```
 *Output*: `data/intermediate/models/seeds/`

2. **Evaluate Static Models**:
 ```bash
 python code/models/evaluate_static.py
 ```
 *Output*: `data/intermediate/static_eval_scores.json`

3. **Aggregate Static Results**:
 ```bash
 python code/models/aggregate_static_results.py
 ```
 *Output*: `data/results/static_aggregated.json`

4. **Derive Heuristic Rules**:
 ```bash
 python code/models/derive_rules.py
 ```
 *Output*: `data/intermediate/heuristic_rules.json`

### Phase 3: Evaluation & Statistical Analysis (User Story 3)

1. **Run Learned Baseline** (multiple seeds):
 ```bash
 python code/evaluation/run_learned_baseline.py
 ```
 *Output*: `data/intermediate/baseline_seeds/`

2. **Aggregate Learned Results**:
 ```bash
 python code/models/aggregate_learned_results.py
 ```
 *Output*: `data/results/baseline_aggregated.json`

3. **Run Static Heuristic Evaluation**:
 ```bash
 python code/evaluation/run_baselines.py
 ```
 *Output*: `data/results/static_metrics.json`

4. **Statistical Analysis**:
 ```bash
 python code/evaluation/stats_analysis.py
 ```
 *Output*: Statistical test results (p-values)

5. **Falsifiability Check**:
 ```bash
 python code/evaluation/falsifiability_check.py
 ```
 *Output*: `data/results/metrics.csv`

6. **Timing Instrumentation**:
 ```bash
 python code/evaluation/timing_instrumentation.py
 ```
 *Output*: `data/results/timing_report.json`

7. **Generate Final Report**:
 ```bash
 python code/evaluation/generate_final_report.py
 ```
 *Output*: `data/results/final_report.md`

## Verification

Run the full test suite to ensure system integrity:

```bash
pytest tests/ -v
```

Specific contract tests verify output formats:
- `tests/contract/test_stats_output.py`
- `tests/integration/test_baselines.py`

## Troubleshooting

- **Memory Errors**: The pipeline is designed to stream data. If you encounter OOM, reduce the sample size in `download.py` or ensure `streaming=True` is used.
- **KenLM Installation**: If `pip install kenlm` fails, build from source as described in Installation.
- **Missing Models**: Ensure `en_core_web_sm` is downloaded before running feature extraction.

## Next Steps

For detailed methodology, statistical definitions, and theoretical background, see `research.md`.
