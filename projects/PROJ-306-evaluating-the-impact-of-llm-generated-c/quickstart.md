# Quickstart Guide: Evaluating the Impact of LLM-Generated Code on Code Coverage

## Prerequisites

- Python 3.9+
- `datasets` library (installed via requirements.txt)
- API Key for LLM (optional, falls back to local models if `LLM_API_KEY` is not set)

## Setup

1. **Clone and Install**
 ```bash
 pip install -r requirements.txt
 ```

2. **Environment Variables** (Optional)
 ```bash
 export LLM_API_KEY="your_api_key_here"
 ```

## Execution

Run the full pipeline (Generation -> Coverage -> Analysis -> Sensitivity):

```bash
python code/main.py --dataset all --model bigcode/starcoderbase-3b --batch-size 100 --output-dir data
```

**Note**: The `--num-tasks` argument has been removed. Use `--batch-size` to control the number of tasks processed.

## Output Artifacts

Upon successful completion, the following files will be generated in `data/processed/`:

- `stats_summary.csv`: Statistical summary of LLM vs Human coverage.
- `corrected_pvalues.csv`: Family-wise error corrected p-values.
- `sensitivity_report.csv`: Sensitivity analysis across thresholds (Task T029).
- `stratified_*.csv`: Stratified reports by difficulty and code patterns.

Visualizations will be saved in `outputs/`.

## Troubleshooting

- **Missing Data**: Ensure `data/benchmarks/processed/catalog.json` exists. If not, run the dataset loader first.
- **API Errors**: If using cloud models, check your API key and rate limits. The system will retry with backoff.
- **Memory Errors**: If using local models, ensure you have sufficient RAM. The fallback model uses 4-bit quantization.
