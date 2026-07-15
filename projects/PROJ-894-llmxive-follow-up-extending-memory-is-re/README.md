# llmXive Follow-up: Extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

This project implements a research pipeline to evaluate graph-based memory reconstruction strategies for LLM agents, using the LoCoMo benchmark. It compares a "Full" traversal baseline against "Greedy" and "Lazy" heuristic strategies, both on clean and synthetically noisy graphs.

## Project Structure

```text
projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/
├── code/
│ ├── analysis/ # Statistical analysis and report generation
│ │ ├── stats.py
│ │ └── report_generator.py
│ ├── strategies/ # Traversal strategies and runners
│ │ ├── full.py
│ │ ├── greedy.py
│ │ ├── lazy.py
│ │ ├── baseline_runner.py
│ │ ├── greedy_runner.py
│ │ ├── lazy_runner.py
│ │ ├── noisy_greedy_runner.py
│ │ └── noisy_lazy_runner.py
│ ├── utils/
│ │ └── validate_results.py
│ ├── config.py
│ ├── data_loader.py
│ ├── graph_utils.py
│ ├── inference.py
│ └── runner.py
├── data/
│ ├── raw/ # Downloaded LoCoMo dataset
│ └── processed/ # Execution results (CSVs) and stats reports (JSON)
├── docs/
│ └── results.md # Auto-generated results report
├── tests/ # Pytest unit and integration tests
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.9+
- pip (package manager)
- Access to Hugging Face Hub (for dataset and model downloads)

## Installation

1. **Clone the repository** (if applicable) and navigate to the project root:
 ```bash
 cd projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Configure the environment** (optional):
 - Set the `HF_HOME` environment variable to control Hugging Face cache directory.
 - The `code/config.py` module handles model paths. By default, it attempts to download `TheBloke/Llama-2-7B-Chat-GGUF` (Q4_K_M) if no local path is provided.

## Execution Workflow

The pipeline consists of three main phases: Data Preparation, Execution (Strategies), and Analysis.

### 1. Data Preparation

Download the LoCoMo benchmark dataset and generate synthetic noisy graphs.

```bash
python code/data_loader.py
```

**Outputs:**
- `data/raw/locomo_dataset.json` (or similar format from HF)
- `data/processed/noisy_graphs.json` (generated with fixed seed)

### 2. Strategy Execution

Run the traversal strategies. Each runner processes the tasks and logs results to CSV.

**Baseline (Full Traversal):**
```bash
python code/strategies/baseline_runner.py
# Outputs: data/processed/baseline_results.csv
```

**Noisy Baseline:**
```bash
python code/strategies/baseline_runner.py --noisy
# Outputs: data/processed/noisy_baseline_results.csv
```

**Heuristic Strategies:**
```bash
python code/strategies/greedy_runner.py
# Outputs: data/processed/greedy_results.csv

python code/strategies/lazy_runner.py
# Outputs: data/processed/lazy_results.csv
```

**Noisy Heuristics:**
```bash
python code/strategies/noisy_greedy_runner.py
# Outputs: data/processed/noisy_greedy_results.csv

python code/strategies/noisy_lazy_runner.py
# Outputs: data/processed/noisy_lazy_results.csv
```

**Sensitivity Analysis (Lazy Strategy):**
```bash
python code/strategies/lazy.py --sweep
# Outputs: data/processed/sweep_results.csv
```

### 3. Statistical Analysis & Reporting

Validate results, perform statistical tests, and generate the final report.

**Validate Results:**
```bash
python code/utils/validate_results.py
```

**Run Statistical Analysis:**
```bash
python code/analysis/stats.py
```
**Outputs:**
- `data/processed/stats_report.json`
- `data/processed/noisy_stats_report.json`

**Generate Documentation:**
```bash
python code/analysis/report_generator.py
```
**Outputs:**
- `docs/results.md` (Auto-generated from `stats_report.json`)

## Testing

Run the test suite using `pytest`:

```bash
pytest tests/ -v
```

## Configuration

- **Model Path**: Controlled via `code/config.py`. Defaults to downloading `TheBloke/Llama-2-7B-Chat-GGUF` (Q4_K_M) from Hugging Face if not specified.
- **Timeouts**: Enforced by `code/runner.py` to prevent hanging tasks.
- **Logging**: All scripts use Python's `logging` module. Logs are printed to stdout/stderr.

## Research Hypotheses

This project validates the following hypotheses:
1. **Reconstruction vs. Retrieval**: Full graph traversal (reconstruction) yields higher accuracy than heuristic retrieval.
2. **Efficiency Trade-off**: Heuristic strategies (Greedy/Lazy) reduce inference time and nodes visited with minimal accuracy loss.
3. **Robustness**: Performance degradation on noisy graphs quantifies the resilience of each strategy.
4. **Complexity Threshold**: There exists a graph complexity threshold where heuristic accuracy drops significantly below baseline.

## License

MIT License. See `LICENSE` for details.

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Commit changes with clear messages.
4. Submit a pull request.