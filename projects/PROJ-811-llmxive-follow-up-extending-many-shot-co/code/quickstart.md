# llmXive Follow-up: Logical Dependency vs. Semantic Curvature in Many-Shot ICL
## Quickstart Guide

This guide walks you through the end-to-end execution of the research pipeline.

## Prerequisites

- Python 3.11+
- pip
- Virtual environment (recommended)

## Setup

1. Clone the repository and navigate to the project directory:
 ```bash
 cd projects/PROJ-811-llmxive-follow-up-extending-many-shot-co
 ```

2. Create and activate a virtual environment:
 ```bash
 python -m venv code/.venv
 source code/.venv/bin/activate # On Windows: code\\.venv\\Scripts\\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Data Preparation

4. Download the dataset (if not already present):
 ```bash
 python code/src/data_loader.py --download
 ```

5. Generate the gold standard template (if human annotations are missing):
 ```bash
 python code/scripts/generate_gold_standard_template.py
 ```

6. Generate the DAG manifest from raw traces:
 ```bash
 python code/scripts/generate_dag_manifest.py
 ```

## Validation

7. Validate DAG correlation with gold standard:
 ```bash
 python code/scripts/validate_dag_correlation.py
 ```

8. Filter invalid DAGs:
 ```bash
 python code/scripts/filter_invalid_dags.py
 ```

## Prompt Generation

9. Generate prompts for all strategies and seeds:
 ```bash
 python code/scripts/run_batch_strategies.py
 ```

10. Generate prompt manifest:
 ```bash
 python code/scripts/generate_prompt_manifest.py
 ```

## Inference

11. Run inference on generated prompts:
 ```bash
 python code/src/inference.py --model-class reasoning --seed 0
 ```
 (Repeat for different seeds and model classes)

## Analysis

12. Run statistical analysis:
 ```bash
 python code/src/analysis.py --input data/results/inference_log.csv
 ```

13. Generate final report:
 ```bash
 python code/src/update_state.py update
 ```

## Verification

14. Verify all artifacts:
 ```bash
 python code/src/update_state.py verify-all
 ```

## Testing

Run the test suite:
```bash
pytest code/tests/
```

## Notes

- Ensure `data/raw/cot_traces.json` exists before running the DAG manifest generation.
- The `gold_standard_annotations.json` file must be present or generated via the template script.
- Inference requires `llama.cpp` to be installed and accessible.
- Adjust seed values and model paths in `.env` or `config.yaml` as needed.