# llmXive Follow-up: Extending PlanBench-XL

This project implements a comparative study of LLM tool-use agents on the PlanBench-XL dataset, focusing on long-horizon planning capabilities. It introduces a "synthetic implicit failure" subset to evaluate how agents handle silent tool errors and whether a signature-based retrieval mechanism improves recovery rates.

## Overview

The project compares two agent architectures:
1. **Baseline Agent**: Operates using internal LLM reasoning only, with no access to external failure signatures.
2. **Augmented Agent**: Equipped with a failure signature index to detect known error patterns and trigger recovery strategies (e.g., replanning).

The study uses the real PlanBench-XL dataset, with a deterministic subset of success tasks modified to include silent tool failures. Statistical significance (Fisher's Exact or Z-test) is used to compare success rates.

## Project Structure

```
projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/
├── code/
│ ├── agents/
│ │ ├── base.py # Abstract base agent class
│ │ ├── baseline.py # Baseline agent implementation
│ │ └── augmented.py # Augmented agent with signature retrieval
│ ├── dataset/
│ │ ├── loader.py # Downloads PlanBench-XL from HuggingFace
│ │ ├── injector.py # Injects deterministic failure patterns
│ │ └── indexer.py # Builds failure signature index
│ ├── analysis/
│ │ ├── log_parser.py # Parses execution logs for stats
│ │ ├── stats.py # Statistical significance testing
│ │ └── report.py # Generates final report
│ ├── utils/
│ │ ├── config.py # Configuration loader
│ │ └── logger.py # JSONL logging utility
│ ├── run_baseline.py # Executes baseline agent
│ ├── run_augmented.py # Executes augmented agent
│ └── setup_dirs.py # Directory initialization scripts
├── data/
│ ├── raw/ # Raw downloaded dataset
│ ├── derived/ # Injected failures and signatures
│ ├── logs/ # Execution logs
│ └── results/ # Final analysis reports
├── tests/
│ ├── unit/ # Unit tests for components
│ └── integration/ # Integration tests for pipelines
├── requirements.txt # Python dependencies
├──.gitignore # Git ignore rules
├── README.md # This file
└── quickstart.md # Step-by-step execution guide
```

## Prerequisites

- Python 3.9+
- pip
- Access to HuggingFace (for PlanBench-XL download)
- CPU-only environment (optimized for <7GB RAM)

## Installation

1. Clone the repository and navigate to the project directory.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

### Quick Start
Refer to `quickstart.md` for a complete end-to-end execution guide.

### Step-by-Step Execution

1. **Initialize Directories**:
 ```bash
 python code/setup_dirs.py
 ```

2. **Download Dataset**:
 ```bash
 python code/dataset/loader.py
 ```

3. **Inject Synthetic Failures**:
 ```bash
 python code/dataset/injector.py
 ```

4. **Build Failure Index**:
 ```bash
 python code/dataset/indexer.py
 ```

5. **Run Baseline Agent**:
 ```bash
 python code/run_baseline.py
 ```

6. **Run Augmented Agent**:
 ```bash
 python code/run_augmented.py
 ```

7. **Generate Report**:
 ```bash
 python code/analysis/report.py
 ```

Or run the full experiment pipeline:
```bash
python run_experiment.py
```

## Configuration

Configuration is managed via `code/utils/config.py`. Key parameters include:
- `SEED`: Random seed for reproducibility (default: 42)
- `MODEL_NAME`: LLM model identifier (e.g., `Llama-3-8B-Quantized`)
- `MAX_TOKENS`: Token limit for agent responses
- `TEMPERATURE`: Sampling temperature

## Testing

Run unit and integration tests:
```bash
pytest tests/ -v
```

## Output Artifacts

- `data/derived/implicit_failure_subset.jsonl`: Synthetic failure dataset
- `data/derived/failure_signatures.json`: Failure pattern index
- `data/logs/baseline_execution.jsonl`: Baseline agent logs
- `data/logs/augmented_execution.jsonl`: Augmented agent logs
- `data/results/final_report.json`: Statistical analysis results

## License

This project is for research purposes. See the repository root for license details.
