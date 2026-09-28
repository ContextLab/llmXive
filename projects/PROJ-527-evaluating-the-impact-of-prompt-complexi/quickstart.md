# Quickstart Guide: Prompt Complexity Evaluation

This guide outlines the steps to run the full pipeline for evaluating the impact of prompt complexity on LLM code generation.

## Prerequisites

- Python 3.11+
- `pip install -r requirements.txt`

## Project Structure

- `code/`: Source code
- `data/raw/`: Raw datasets (HumanEval)
- `data/processed/`: Processed data (prompt variants, execution results)
- `data/results/`: Final analysis results and reports
- `state/`: Project state and versioning info

## Execution Steps

The pipeline is designed to be run sequentially. Each step produces artifacts required by the next.

1. **Setup**: Ensure directories exist.
 ```bash
 python code/setup_data_directories.py
 ```

2. **Fetch Data**: Download HumanEval dataset.
 ```bash
 python code/data/loader.py
 ```

3. **Generate Prompts**: Create complexity variants.
 ```bash
 python code/prompts/generator.py
 ```

4. **Tokenize**: Count tokens and validate thresholds.
 ```bash
 python code/prompts/tokenizer.py
 ```

5. **Query LLM**: Generate code for each variant.
 ```bash
 python code/llm/orchestrator.py
 ```

6. **Store Results**: Save generated code and metadata to Parquet.
 ```bash
 python code/data/storage.py
 ```

7. **Execute Tests**: Run generated code against HumanEval tests.
 ```bash
 python code/execution/write_results.py
 ```

8. **Analyze**: Perform statistical analysis and visualization.
 ```bash
 python code/analysis/stats.py
 python code/analysis/viz.py
 ```

9. **Versioning**: Update project state.
 ```bash
 python code/utils/versioning.py
 ```

## Expected Outputs

- `data/processed/prompt_variants.parquet`: Generated prompts and code.
- `data/results/execution_outcomes.csv`: Pass/fail rates per complexity.
- `data/results/analysis_summary.csv`: Statistical test results.
- `figures/`: Generated plots.

## Troubleshooting

- If `data/processed/prompt_variants.parquet` is missing, ensure `code/data/storage.py` was run after `code/llm/orchestrator.py`.
- If `data/results/execution_outcomes.csv` is missing, ensure `code/execution/write_results.py` was run.
