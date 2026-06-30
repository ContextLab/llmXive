# Quickstart: Evaluating the Impact of LLM-Generated Code on Code Coverage

## Prerequisites

-   **Python**: 3.10 or higher.
-   **Dependencies**: `pip install -r requirements.txt`.
-   **API Key (Optional)**: Set `LLM_API_KEY` environment variable for GPT-4 access. If not set, the system uses the CPU fallback model (Phi-2 or Gemma-2B in 4-bit).
-   **Disk Space**: ~2GB free space for models and data.

## Installation

1.  **Clone the repository** and navigate to the project directory.
    ```bash
    git clone <repo-url>
    cd projects/PROJ-306-evaluating-the-impact-of-llm-generated-c
    ```

2.  **Install dependencies**.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure the environment** (Optional).
    ```bash
    export LLM_API_KEY="your-openai-key-here"
    # If no key is set, the pipeline will automatically use the CPU fallback model (Phi-2/Gemma-2B 4-bit).
    ```

## Running the Pipeline

The entire pipeline can be executed via the main CLI entry point.

```bash
# Run the full pipeline (Ingest -> Transform -> Generate -> Measure -> Analyze)
python code/main.py --num-tasks 100 --output-dir data/processed
```

### Parameters
-   `--num-tasks`: Number of tasks to process (default: 100).
-   `--model`: Force a specific model (e.g., `phi-2`). Default is auto-detect.
-   `--output-dir`: Directory for final reports.

## Expected Outputs

After successful execution, the following files will be generated in `data/processed/`:

1.  **`coverage_pairs.csv`**: The master dataset containing paired coverage metrics.
    -   Columns: `task_id`, `line_coverage_llm`, `line_coverage_human`, `branch_coverage_llm`, `branch_coverage_human`, `diff`, `model_used`, `benchmark_source`.
2.  **`stats_summary.csv`**: Statistical test results (LMM/GLMM).
    -   Columns: `effect_size`, `ci_lower`, `ci_upper`, `p_value`, `test_type`, `significance_flag`.
3.  **`sensitivity_report.csv`**: Bootstrap sensitivity analysis (multiple iterations).
4.  **`outputs/*.png`**: Visualizations (box-plots, bar-charts).

### Example Output Snippet (`stats_summary.csv`)
```csv
effect_size,ci_lower,ci_upper,p_value,test_type,significance_flag
-0.12,-0.18,-0.06,0.003,LMM_MarginalMeans,True
```

## Troubleshooting

-   **Memory Error**: If the process crashes with OOM, ensure you are not running other heavy applications. The pipeline defaults to a small `phi` model (4-bit).
-   **Rate Limit**: If you see `429 Too Many Requests`, the pipeline will automatically back off. If it persists, reduce `--num-tasks`.
-   **Dataset Missing**: If the pipeline logs `WARNING: Dataset not found`, it means the HuggingFace loader failed. The pipeline will proceed with available data and report the exclusion rate.
-   **Gate Warning**: If the pipeline logs `GATE BLOCKED: Unverified Dataset`, it means the Reference-Validator has not confirmed the dataset sources. The pipeline will run in sandbox mode, but research conclusions cannot be accepted.
