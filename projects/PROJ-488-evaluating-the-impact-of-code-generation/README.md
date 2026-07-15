# Evaluating the Impact of Code Generation

This project analyzes the differences in code quality and complexity between human-written code (CodeSearchNet) and LLM-generated code (CodeParrot/CodeGen) using static analysis metrics.

## ⚠️ Critical Pre-requisite: Constitutional Amendments

**This pipeline will NOT run until Constitutional Amendment PRs are approved and merged.**

The following amendments are required to proceed:
1. **Amendment to Principle VI**: Permitting use of CodeParrot/CodeGen as an LLM-generated code source.
2. **Amendment to Principle VII**: Permitting use of `radon` and `pylint` for metric extraction.

**Current Status**:
- Check `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml` for the `amendment_status` field.
- If the status is not `approved`, do not run the pipeline.
- Once approved, the state file will reflect `approved` and the pipeline can be executed.

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-488-evaluating-the-impact-of-code-generation
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
 *Note: Ensure Python 3.11+ is used.*

4. **Verify environment**:
 ```bash
 python -c "import datasets, radon, pylint, pandas, numpy, matplotlib, yaml; print('All dependencies installed successfully.')"
 ```

## Execution

### Running the Full Pipeline

The main entry point is `code/main.py`. It orchestrates data ingestion, metric extraction, statistical analysis, and visualization.

```bash
python code/main.py --run-all
```

This command performs the following steps:
1. **Amendment Check**: Verifies that amendment PRs are approved in the state file.
2. **Data Ingestion**: Downloads CodeSearchNet and CodeGen datasets (with caching).
3. **Preprocessing**: Filters for Python functions and normalizes length.
4. **Metric Extraction**: Runs `radon` and `pylint` on the code snippets.
5. **Statistical Analysis**: Performs Mann-Whitney U tests, Cliff's Delta, and power analysis.
6. **Visualization**: Generates boxplots and guideline recommendations.
7. **State Update**: Records hashes and timestamps in the state file.

### Running Individual Stages

You can run specific stages by invoking the corresponding modules directly:

- **Ingestion & Preprocessing**:
 ```bash
 python code/data_ingestion.py
 python code/data_filtering.py
 ```

- **Metric Extraction**:
 ```bash
 python code/metric_extraction.py
 ```

- **Statistical Analysis**:
 ```bash
 python code/statistical_analysis.py
 ```

- **Visualization**:
 ```bash
 python code/visualization.py
 ```

### Running Tests

```bash
python -m pytest tests/ -v
```

## Project Structure

- `code/`: Source code modules for the pipeline.
- `data/raw/`: Raw downloaded datasets (managed by `data_ingestion.py`).
- `data/processed/`: Filtered and preprocessed code snippets.
- `data/metrics/`: Aggregated metric results (CSV files).
- `results/`: Final analysis outputs, figures, and reports.
- `state/`: Project state tracking (YAML files with hashes and timestamps).
- `specs/`: Design documents and requirements.
- `tests/`: Unit and integration tests.

## Output Artifacts

Upon successful completion, the following artifacts are generated:

- `data/processed/snippets.json`: Filtered code snippets.
- `data/metrics/*.csv`: Metric distributions per group.
- `results/figures/*.png`: Boxplot visualizations.
- `results/guidelines.md`: Code review guideline recommendations.
- `results/pilot_study.md`: Pilot study validation results.
- `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml`: Updated state with artifact hashes.

## License

This project is part of the llmXive automated science pipeline.