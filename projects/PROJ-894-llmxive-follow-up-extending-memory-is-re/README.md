# llmXive Follow-up: Extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

**Project ID**: PROJ-894-llmxive-follow-up-extending-memory-is-re

## Overview

This project implements a rigorous, reproducible evaluation of graph-based memory reconstruction strategies for LLM agents, following up on the findings of "Memory is Reconstructed, Not Retrieved". We compare **Full**, **Lazy**, and **Greedy** traversal strategies on the **LoCoMo** benchmark, analyzing their performance under both clean and noisy graph conditions.

## Key Features

- **Streaming Data Processing**: Efficiently handles large datasets (e.g., LoCoMo) without loading them entirely into RAM using `datasets.load_dataset(..., streaming=True)`.
- **Robustness & Edge Case Handling**: Explicitly detects and handles disconnected components, single-node graphs, and timeouts to prevent pipeline crashes.
- **Deterministic Reproducibility**: All experiments use fixed seeds; verification scripts ensure noise injection and inference results are reproducible.
- **Real Data Enforcement**: The pipeline strictly enforces the use of real data from HuggingFace (`locomo/locomo-benchmark` or `mlabonne/locomo`). Synthetic fallbacks are forbidden and will cause the script to fail loudly.

## Prerequisites

- Python 3.9+
- `pip`
- `spacy` model: `en_core_web_sm` (installed automatically via `data_loader.py`)

## Installation

1. **Clone and Setup**:
 ```bash
 cd projects/PROJ-894-llmxive-follow-up-extending-memory-is-re
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. **Install Dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

3. **Download spaCy Model** (Handled automatically by the data loader, but can be run manually):
 ```bash
 python -c "import spacy; spacy.cli.download('en_core_web_sm', version='3.7.1')"
 ```

## Quickstart: Running the Full Pipeline

The pipeline is designed to run sequentially. Follow these steps to execute the full analysis from data download to report generation.

### Step 1: Data Loading & Graph Construction

Download the LoCoMo benchmark, extract triples, build clean graphs, and generate noisy variants.

```bash
python code/data_loader.py --download
```

*This command performs the following:*
- Fetches `data/raw/locomo.jsonl`
- Extracts triples to `data/intermediate/triples_raw.jsonl`
- Builds clean graphs to `data/intermediate/graphs_raw.json`
- Generates noisy graphs (`seed=42`) to `data/processed/graphs/graph_noise_42.json`

### Step 2: Strategy Execution

Run the traversal strategies on the generated graphs.

**Baseline (Full) on Clean Graph**:
```bash
python code/runner.py --strategy full --input data/intermediate/graphs_raw.json --graph data/intermediate/graphs_raw.json --output data/processed/baseline_results.csv --timeout 60
```

**Lazy on Clean Graph**:
```bash
python code/runner.py --strategy lazy --input data/intermediate/graphs_raw.json --graph data/intermediate/graphs_raw.json --output data/processed/lazy_results.csv --threshold 0.7 --timeout 60
```

**Greedy on Clean Graph**:
```bash
python code/runner.py --strategy greedy --input data/intermediate/graphs_raw.json --graph data/intermediate/graphs_raw.json --output data/processed/greedy_results.csv --topk 5 --timeout 60
```

**Noisy Baseline (Full)**:
```bash
python code/runner.py --strategy full --input data/processed/graphs/graph_noise_42.json --graph data/processed/graphs/graph_noise_42.json --output data/processed/noisy_baseline_results.csv --timeout 60
```

**Noisy Lazy**:
```bash
python code/runner.py --strategy lazy --input data/processed/graphs/graph_noise_42.json --graph data/processed/graphs/graph_noise_42.json --output data/processed/noisy_lazy_results.csv --threshold 0.7 --timeout 60
```

**Noisy Greedy**:
```bash
python code/runner.py --strategy greedy --input data/processed/graphs/graph_noise_42.json --graph data/processed/graphs/graph_noise_42.json --output data/processed/noisy_greedy_results.csv --topk 5 --timeout 60
```

### Step 3: Statistical Analysis & Reporting

Run the analysis scripts to compute statistics, correlations, and generate the final report.

**Statistical Tests (Clean & Noisy)**:
```bash
python code/analysis/stats.py
python code/analysis/noisy_stats.py
```

**Correlation & Threshold Analysis**:
```bash
python code/analysis/correlation_analysis.py
python code/analysis/threshold_analysis.py
```

**Status Categorization (Robustness)**:
```bash
python code/report/categorize_status_counts.py
```

**Aggregate Results**:
```bash
python code/report/aggregate_results.py
```

**Extract Limitations**:
```bash
python code/report/extract_limitations.py
```

**Generate Final Report**:
```bash
python code/report/generate_report.py
```

*Output*: The final research report will be available at `docs/research_report.md`.

## Robustness & Edge Cases

The pipeline includes explicit handlers for:
- **Disconnected Graphs**: Strategies detect unreachable nodes and flag tasks as `UNRESOLVED` or traverse the connected component.
- **Degenerate Graphs**: Single-node or zero-edge graphs are detected and handled without division-by-zero errors.
- **Timeouts**: A configurable `--timeout` argument enforces a hard limit per task; timed-out tasks are logged with status `TIMEOUT`.

## Reproducibility Verification

To verify that noise injection and results are deterministic:

```bash
python code/utils/verify_seeds.py
```

This script re-runs the noise injection and inference logic and compares SHA-256 hashes against stored values in `state/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re.yaml`.

## Data Integrity

- **No Synthetic Fallbacks**: If the LoCoMo dataset cannot be fetched from HuggingFace, the `data_loader.py` script will raise an exception and halt.
- **Streaming**: For large datasets, the `--streaming` flag (enabled by default in `runner.py` for large inputs) ensures memory efficiency.

## Project Structure

```text
.
├── code/
│ ├── data_loader.py # Data fetching, extraction, graph building
│ ├── runner.py # Main execution engine with timeout handling
│ ├── strategies/ # Full, Lazy, Greedy traversal implementations
│ ├── analysis/ # Statistical tests, correlation, threshold analysis
│ ├── report/ # Report generation and aggregation scripts
│ ├── utils/ # Verification, auditing, and helper scripts
│ └── requirements.txt
├── data/
│ ├── raw/ # Downloaded LoCoMo data
│ ├── intermediate/ # Extracted triples and clean graphs
│ └── processed/ # Results CSVs, noisy graphs, analysis outputs
├── docs/
│ └── research_report.md # Final generated report
├── state/ # Reproducibility state and hashes
└── README.md
```

## License

This project is part of the llmXive research pipeline. See the root repository for licensing details.