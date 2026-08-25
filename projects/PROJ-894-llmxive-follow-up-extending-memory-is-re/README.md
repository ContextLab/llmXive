# llmXive Follow-up: Extending "Memory is Reconstructed, Not Retrieved"

This project implements an automated research pipeline to evaluate graph-based memory reconstruction strategies for LLM agents, specifically testing the hypothesis that memory is reconstructed rather than retrieved.

## Overview

The pipeline processes the **LoCoMo** benchmark dataset to:
1. Extract knowledge graphs (triples) from task contexts.
2. Inject controlled noise to simulate retrieval errors.
3. Execute three traversal strategies: **Full** (baseline), **Lazy**, and **Greedy**.
4. Perform statistical analysis on accuracy, node traversal counts, and robustness.

## Prerequisites

- Python 3.9+
- `pip` (Python package installer)
- Access to Hugging Face Hub (for LoCoMo dataset)
- `en_core_web_sm` spaCy model (automatically installed during setup)

## Installation

1. **Clone and Navigate**:
 ```bash
 cd projects/PROJ-894-llmxive-follow-up-extending-memory-is-re
 ```

2. **Install Dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

3. **Download spaCy Model**:
 The pipeline requires the `en_core_web_sm` model for NER and dependency parsing.
 ```bash
 python -m spacy download en_core_web_sm
 ```

## Quickstart Guide

The pipeline is designed to run in a specific sequence to generate intermediate artifacts required by downstream tasks.

### Step 1: Data Ingestion & Graph Construction

Download the LoCoMo dataset, extract triples, and build the initial memory graphs.
This step also generates the noisy graph dataset for robustness testing.

```bash
# Download data and build graphs (Clean + Noisy)
python code/data_loader.py --download
```

*Expected Output*:
- `data/raw/locomo.jsonl`
- `data/intermediate/triples_raw.jsonl`
- `data/intermediate/graphs_raw.json`
- `data/processed/graphs/graph_noise_42.json`

### Step 2: Strategy Execution (Streaming & Robustness)

Run the traversal strategies. The runner now supports **streaming** (memory-efficient) and **robustness** handling (timeouts, degenerate graphs).

**Baseline (Full Strategy)**:
```bash
python code/runner.py --strategy full --graph data/processed/graphs/graph_clean.json --output data/processed/baseline_results.csv
```

**Heuristics (Lazy & Greedy)**:
```bash
# Lazy Strategy (with evidence threshold)
python code/runner.py --strategy lazy --graph data/processed/graphs/graph_clean.json --output data/processed/lazy_results.csv --threshold 0.7

# Greedy Strategy (with top-k)
python code/runner.py --strategy greedy --graph data/processed/graphs/graph_clean.json --output data/processed/greedy_results.csv --topk 5
```

**Noisy Variants** (for robustness testing):
```bash
python code/runner.py --strategy full --graph data/processed/graphs/graph_noise_42.json --output data/processed/noisy_baseline_results.csv
python code/runner.py --strategy lazy --graph data/processed/graphs/graph_noise_42.json --output data/processed/noisy_lazy_results.csv --threshold 0.7
python code/runner.py --strategy greedy --graph data/processed/graphs/graph_noise_42.json --output data/processed/noisy_greedy_results.csv --topk 5
```

*Streaming Mode*:
To process large datasets without loading everything into RAM, add the `--streaming` flag:
```bash
python code/runner.py --strategy full --graph data/processed/graphs/graph_clean.json --output data/processed/baseline_results.csv --streaming --chunk-size 10
```

### Step 3: Statistical Analysis

Once all result CSVs are generated, run the analysis scripts to compute significance, correlations, and thresholds.

```bash
# Statistical significance (Clean vs Noisy)
python code/analysis/stats.py
python code/analysis/noisy_stats.py

# Correlation Analysis (Nodes visited vs Accuracy)
python code/analysis/correlation_analysis.py

# Threshold & Inflection Point Analysis
python code/analysis/threshold_analysis.py
```

*Expected Output*:
- `data/processed/statistical_results.json`
- `data/processed/correlation_results.json`
- `data/processed/threshold_analysis.json`

### Step 4: Report Generation

Generate the final research report aggregating all findings.

```bash
python code/report/generate_report.py
```

*Output*: `docs/research_report.md`

## Project Structure

```text
.
├── code/
│ ├── data_loader.py # Data fetching, NER, graph construction
│ ├── runner.py # Main execution engine (streaming, timeout, robustness)
│ ├── graph_utils.py # Graph manipulation, noise injection
│ ├── strategies/ # Traversal algorithms (full, lazy, greedy)
│ ├── analysis/ # Statistical analysis scripts
│ └── report/ # Report generation
├── data/
│ ├── raw/ # Downloaded LoCoMo dataset
│ ├── intermediate/ # Extracted triples, raw graphs
│ └── processed/ # Execution results, noisy graphs
├── tests/ # Unit and integration tests
└── docs/ # Final research report
```

## Robustness Features

This implementation includes specific handling for edge cases:
- **Timeouts**: Configurable hard timeouts per task (via `--timeout` flag in `runner.py`).
- **Degenerate Graphs**: Automatic detection of single-node or disconnected components; flagged as `DEGENERATE` or `UNRESOLVED` in results.
- **Streaming**: Low-memory processing for large datasets via `stream_locomo_tasks()`.

## Reproducibility

To verify the reproducibility of noise injection:
```bash
python code/utils/verify_seeds.py
```
This compares the SHA-256 hash of the generated noisy graph against the stored state.

## License

Research implementation for llmXive.