# Quickstart: llmXive follow-up: extending "Active Learners as Efficient PRP Rerankers"

## Prerequisites

- Python 3.11+
- `pip`
- 7GB+ RAM available (for local testing)
- 14GB+ disk space

## Installation

1. **Clone the repository** (or navigate to the project root).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` includes `beir`, `sentence-transformers`, `datasketch`, `scikit-learn`, `torch`, `llama-cpp-python`, `pytest`.*

## Running the Pipeline

The full pipeline can be executed end-to-end via the main script. This will:
1. Download BEIR datasets (if not present).
2. Inject synthetic redundancy.
3. Run MinHash-LSH clustering.
4. Execute the active ranker.
5. Compute metrics and statistical significance.

```bash
python code/main.py --dataset scifact --redundancy 0.4 --seeds 30
```

### Arguments

- `--dataset`: Name of the BEIR dataset (`scifact`, `nfcorpus`, `trec-covid`).
- `--redundancy`: Target redundancy level (0.0 to 1.0).
- `--seeds`: Number of random seeds to run for statistical significance (default: 30).
- `--skip-llm`: (Optional) Skip the LLM consensus validation step to save time/memory (uses proxy only).
- `--threshold-sweep`: (Optional) Run threshold sensitivity sweep (0.85, 0.90, 0.95, 0.98).

## Expected Outputs

After successful execution, the following files will be generated:

- `data/processed/injected_datasets.json`: The synthetic datasets.
- `data/processed/comparison_log.jsonl`: Log of all pairwise comparisons.
- `data/processed/resource_log.json`: Resource usage log.
- `data/results/final_report.json`: The final report with NDCG, wasted ratios, p-values, and threshold sweep results.

## Verifying Results

To verify the statistical significance:
```bash
python -m pytest tests/integration/test_full_pipeline.py -v
```

## Troubleshooting

- **Memory Error**: If you encounter `MemoryError`, the LLM consensus step may have exceeded the 7GB limit. Rerun with `--skip-llm` to use the proxy-only fallback.
- **Dataset Not Found**: Ensure you have internet access for the initial BEIR download. Subsequent runs will use the cached data in `data/raw/`.
- **Slow Execution**: The MinHash step is CPU-bound. Ensure you are not running other heavy processes.