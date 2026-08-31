# llmXive: From Chatbot to Digital Colleague

**Quick Start Guide**

This project implements an automated science pipeline to evaluate the performance of a "Digital Colleague" agent across varying library sizes and semantic overlaps.

## Prerequisites

- Python 3.9+
- pip
- (Optional) Virtual environment tool (venv, conda)

## Installation

1. **Clone the repository** (if not already done):
 ```bash
 git clone <repository-url>
 cd llmxive-follow-up-extending-from-chatbot
 ```

2. **Create and activate a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: `requirements.txt` contains pinned versions for reproducibility.*

## Project Structure

- `code/`: Source code for data generation, agent execution, and analysis.
- `data/raw/`: Generated synthetic datasets (tasks, skills).
- `data/results/`: Experiment logs, metrics, and analysis reports.
- `contracts/`: JSON/YAML schemas for data validation.
- `tests/`: Unit and integration tests.

## Quick Start Execution

Follow these steps to generate data, run the experiment, and analyze results.

### 1. Setup Project Directories
Ensure the directory structure exists:
```bash
python code/setup_directories.py
```

### 2. Generate Synthetic Data
Create the skills library and task set:
```bash
python code/generate_data.py
```
*Outputs:* `data/raw/skills.json`, `data/raw/tasks.json`, `data/raw/checksums.json`.

### 3. Run the Experiment
Execute the agent across different library sizes:
```bash
python code/run_experiment.py
```
*Outputs:* `data/results/experiment_log.csv`, `data/results/metrics.json`.

### 4. Run Baseline (No Pruning)
```bash
python code/run_baseline.py
```
*Outputs:* `data/results/experiment_log_baseline.csv`.

### 5. Analyze Results
Perform statistical analysis and generate the final report:
```bash
python code/analyze.py
```
*Outputs:* `data/results/final_analysis.json`, `data/results/tipping_point.json`, `data/results/sensitivity_report.json`.

## Configuration

- **Seeds**: Controlled via `code/config.py` (default values or environment variables).
- **Pruning Thresholds**: Configurable in `code/config.py` (default: prune every 10 tasks).
- **Overlap Level**: Set in `code/config.py` to control semantic density of the skill library.

## Validation

- **Schema Validation**: Run contract tests to ensure data compliance:
 ```bash
 pytest tests/contract/
 ```
- **Unit Tests**:
 ```bash
 pytest tests/unit/
 ```

## Troubleshooting

- **Memory Errors**: If you encounter "Memory Limit Exceeded", the script will fail gracefully. Reduce the number of skills or tasks in `config.py`.
- **Missing Files**: Ensure `data/raw/` and `data/results/` directories exist before running scripts.
- **Dependencies**: If installation fails, check that your Python version is 3.9 or higher.

## Next Steps

- Review `README.md` for detailed architecture and API documentation.
- Explore `specs/` for user stories and functional requirements.
- Modify `code/config.py` to experiment with different parameters.