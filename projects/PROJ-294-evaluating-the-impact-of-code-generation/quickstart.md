# Quick Start Guide for PROJ-294

This guide outlines the steps to run the full analysis pipeline.

## Prerequisites

- Python 3.8+
- `pip install -r code/requirements.txt`

## Directory Setup

Run the following to create the project structure:

```bash
python code/setup_project_structure.py
```

## Pipeline Execution

Execute the pipeline stages in order:

```bash
# 1. Download Data
python code/download_data.py

# 2. Extract Human Reference
python code/extract_human_reference.py

# 3. Generate Code (Primary Model)
python code/generate_code.py --model salesforce/codegen-mono-350M

# 4. Analyze Metrics
python code/analyze_metrics.py

# 5. Run Statistical Tests
python code/statistical_tests.py

# 6. Generate Report
python code/report_generator.py
```

## Validation

Validate the artifacts and citations:

```bash
python code/validate_citations.py
python code/validate_quickstart.py
```