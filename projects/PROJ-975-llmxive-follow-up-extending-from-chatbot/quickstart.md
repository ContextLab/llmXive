# Quickstart Guide: llmXive

This guide provides instructions for setting up and running the llmXive automated science pipeline.

## Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <repository-name>
 ```

2. Create a virtual environment and activate it:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Project Structure

- `code/`: Source code for the pipeline.
- `data/`: Raw and processed data.
- `tests/`: Unit and contract tests.
- `contracts/`: JSON schemas for data validation.
- `specs/`: Design documents.

## Running the Pipeline

### 1. Setup Project Structure

Ensure the directory structure is created:
```bash
python code/setup_directories.py
```

### 2. Generate Data

Generate the synthetic dataset (User Story 1):
```bash
python code/generate_data.py
```
This creates `data/raw/tasks.json` and `data/raw/skills.json`.

### 3. Run Experiments

Execute the agent across varying library sizes (User Story 2):
```bash
python code/run_experiment.py
```
Results are saved to `data/results/experiment_log.csv` and `data/results/metrics.json`.

### 4. Analyze Results

Perform statistical analysis (User Story 3):
```bash
python code/analyze.py
```
Outputs include `data/results/final_analysis.json` and `data/results/tipping_point.json`.

## Verification

To verify the logging configuration (T007):
```bash
python code/verify_logging.py
```

## Testing

Run unit tests:
```bash
pytest tests/unit/
```

Run contract tests:
```bash
pytest tests/contract/
```

## Reproducibility

Seeds are pinned in `code/config.py`. To ensure reproducibility, do not modify the seed values unless necessary.

## Troubleshooting

- **Memory Errors**: If you encounter memory errors during data generation, reduce the number of skills or tasks in `code/config.py`.
- **Schema Errors**: Ensure all generated JSON files match the schemas in `contracts/`.

For more details, refer to `README.md`.
