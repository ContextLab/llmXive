# llmXive: From Chatbot to Digital Colleague
## Quick Start Guide

This guide provides instructions to set up the environment and run the core experiments for the llmXive project.

### Prerequisites

- Python 3.9+
- pip (Python package installer)
- A modern web browser (for viewing results if applicable)

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
 Install the required packages listed in `requirements.txt`:
 ```bash
 pip install -r requirements.txt
 ```

4. **Set up the project structure**:
 Ensure the necessary directories exist. Run the setup script:
 ```bash
 python code/setup_directories.py
 ```

5. **Configure logging and contracts**:
 Initialize the logging configuration and contract schemas:
 ```bash
 python code/setup_contracts.py
 python code/verify_logging.py
 ```

### Running the Pipeline

The pipeline consists of three main phases: Data Generation, Agent Execution, and Analysis.

#### Phase 1: Generate Synthetic Data

Generate the skill library and task set:
```bash
python code/generate_data.py
```
**Output**:
- `data/raw/skills.json`: The generated skill library.
- `data/raw/tasks.json`: The generated task set with ground-truth paths.

#### Phase 2: Run Experiments

Execute the agent across different library sizes:
```bash
python code/run_experiment.py
```
**Output**:
- `data/results/experiment_log.csv`: Detailed logs of task execution.
- `data/results/metrics.json`: Aggregated metrics for each library size.

To run a baseline experiment (without pruning):
```bash
python code/run_baseline.py
```

#### Phase 3: Analysis

Analyze the results to identify tipping points and pruning efficacy:
```bash
python code/analyze.py
```
**Output**:
- `data/results/final_analysis.json`: Statistical analysis results including tipping point.
- `data/results/sensitivity_report.json`: Sensitivity analysis across pruning thresholds.

### Verification

To verify the setup and reproducibility:
```bash
python -c "from code.config import get_seeds; print(get_seeds())"
python code/verify_logging.py
```

### Troubleshooting

- **Memory Errors**: If you encounter memory issues during data generation, ensure your system has sufficient RAM (recommended >8GB) or reduce the `LIBRARY_SIZES` in `code/config.py`.
- **Missing Dependencies**: If `pip install` fails, ensure your Python version is 3.9 or higher.
- **Logging Issues**: If `experiment_log.csv` is not created, run `python code/verify_logging.py` to diagnose configuration issues.

### Next Steps

- Review the `README.md` for detailed architecture and design documents.
- Check `data/results/` for generated reports and metrics.
- Run `pytest` to execute the test suite (if available).