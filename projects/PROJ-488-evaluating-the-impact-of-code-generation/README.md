# Evaluating the Impact of Code Generation on Code Review Quality

## Project Overview

This project investigates the differences in code quality metrics between human-written code (CodeSearchNet) and LLM-generated code (CodeParrot/CodeGen). We utilize static analysis tools (radon, pylint) to extract metrics, perform statistical comparisons (Mann-Whitney U, Cliff's delta), and generate review guidelines.

## ⚠️ CRITICAL: Constitutional Amendment Status

**Before running this pipeline, you MUST verify that the following Constitutional Amendments have been approved:**

1. **Amendment to Principle VI**: Permits use of CodeParrot/CodeGen as the LLM-generated code source.
2. **Amendment to Principle VII**: Permits use of radon and pylint for metric extraction.

Check the current status in `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml` under the `amendment_status` key.
If the status is not "approved", do **not** proceed with the pipeline execution.

## Installation

1. Ensure you have Python 3.11+ installed.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Execution

### Running the Full Pipeline

To execute the entire pipeline from data ingestion to visualization:

```bash
python code/main.py --run-all
```

This will:
1. Download and preprocess datasets (CodeSearchNet, CodeParrot/CodeGen).
2. Filter for Python functions and validate AST parsing.
3. Extract static analysis metrics (radon, pylint).
4. Perform statistical analysis (Mann-Whitney U, Cliff's delta, power analysis).
5. Generate visualizations and review guidelines.

### Running Individual Modules

You can also run specific stages independently:

- **Data Ingestion**:
 ```bash
 python code/data_ingestion.py
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
- **Guideline Generation**:
 ```bash
 python code/guideline_generator.py
 ```

## Project Structure

- `code/`: Source code modules.
- `data/raw/`: Raw downloaded datasets.
- `data/processed/`: Filtered and preprocessed code snippets.
- `data/metrics/`: Extracted metric CSVs (e.g., complexity, bug indicators).
- `results/`: Final outputs including figures, guidelines, and reports.
- `state/`: State tracking and artifact hashes.
- `specs/`: Design documents and specifications.

## Logging

Logs are written to `results/pipeline_validation.log` and console output.
The logger is snippet-ID aware for traceability.

## License

This project is part of the llmXive automated science pipeline.
Refer to the project's license file for details.