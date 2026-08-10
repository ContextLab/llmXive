# llmXive: From Chatbot to Digital Colleague
## Quickstart Guide

This guide provides instructions for setting up and running the llmXive automated science pipeline.

### Prerequisites

- Python 3.9+
- pip (Python package manager)
- A Unix-like environment (Linux, macOS) or WSL on Windows

### Installation

1. **Clone the repository** (if not already done):
 ```bash
 git clone <repository-url>
 cd PROJ-975-llmxive-follow-up-extending-from-chatbot
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

 *Note: `requirements.txt` contains pinned versions for reproducibility (see T002).*

### Project Structure

The project follows a standard data science layout:

- `code/`: Python modules for data generation, agent execution, and analysis.
- `data/`:
 - `raw/`: Generated synthetic datasets (`tasks.json`, `skills.json`).
 - `results/`: Experiment logs and analysis outputs.
- `contracts/`: JSON schemas for data validation.
- `tests/`: Unit and contract tests.
- `specs/`: Design documents and requirements.

### Running the Pipeline

The pipeline consists of three main phases: Data Generation, Agent Execution, and Analysis.

#### 1. Generate Synthetic Data (User Story 1)

This step creates the multi-step tasks and skill library.

```bash
python code/generate_data.py
```

**Outputs**:
- `data/raw/tasks.json`: 500 multi-step tasks.
- `data/raw/skills.json`: 100 Python skills with metadata.
- `data/raw/checksums.json`: SHA-256 checksums for integrity (T042).

*Verify*: Ensure the files exist and check the console output for similarity metrics.

#### 2. Run the Experiment (User Story 2)

Execute the "Digital Colleague" agent across different library sizes.

```bash
python code/run_experiment.py
```

**Outputs**:
- `data/results/experiment_log.csv`: Detailed log of every task execution (latency, tokens, success, retrieval metrics).
- `data/results/metrics.json`: Aggregated metrics per library size.

*Note*: This script iterates through `LIBRARY_SIZES` defined in `code/config.py`.

#### 3. Run Baseline (Optional - User Story 3)

Run the experiment with pruning disabled for comparison.

```bash
python code/run_baseline.py
```

**Output**:
- `data/results/experiment_log_baseline.csv`

#### 4. Analyze Results (User Story 3)

Perform statistical analysis to identify tipping points and pruning efficacy.

```bash
python code/analyze.py
```

**Outputs**:
- `data/results/tipping_point.json`: Calculated inflection point (x0) and model parameters.
- `data/results/final_analysis.json`: VIF metrics, p-values, and summary.
- `data/results/sensitivity_report.json`: Robustness check across pruning intervals.

### Verification & Testing

Run the test suite to ensure data integrity and contract compliance.

```bash
# Unit tests
python -m pytest tests/unit/ -v

# Contract tests (schema validation)
python -m pytest tests/contract/ -v
```

### Configuration

Experiment parameters are defined in `code/config.py`:
- `SEED_A`, `SEED_B`: Random seeds for reproducibility.
- `LIBRARY_SIZES`: List of library sizes to test (default: `[10, 30, 50, 100]`).
- `OVERLAP_LEVEL`: Target semantic overlap for skill generation.

Environment variables can override seeds:
```bash
export SEED_A=42
export SEED_B=123
python code/generate_data.py
```

### Troubleshooting

- **Memory Errors**: If `generate_data.py` fails with a memory error, ensure your system has at least 6GB of free RAM. The script includes a check (T017) to fail gracefully if limits are exceeded.
- **Schema Validation**: If contract tests fail, verify that `contracts/*.schema.yaml` files match the generated JSON structure.
- **Reproducibility**: If results differ between runs, check that `SEED_A` and `SEED_B` are consistent in the environment or `config.py`.

### Next Steps

- Review `specs/001-gene-regulation/` for detailed design documents.
- Read `README.md` for high-level project overview.
- Check `data/results/final_analysis.json` for the final scientific findings.