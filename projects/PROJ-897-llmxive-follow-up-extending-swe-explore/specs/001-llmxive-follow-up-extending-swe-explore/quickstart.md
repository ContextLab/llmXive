# Quickstart: llmXive follow-up: extending "SWE-Explore: Benchmarking How Coding Agents Explore Repositories"

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (free-tier) or local machine with similar constraints (2 CPU, 7GB RAM).
- Internet access to download datasets from HuggingFace.

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repository-url>
    cd projects/PROJ-897-llmxive-follow-up-extending-swe-explore
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins CPU-only versions of `torch`, `transformers`, and `llama-cpp-python`.*

## Data Preparation

1.  **Download Raw Data**:
    Run the download script to fetch the SWE-Explore dataset.
    ```bash
    python code/data/download.py
    ```
    *This will save the raw JSONL to `data/raw/` and generate a checksum.*

2.  **Derive Ground Truth**:
    Parse solution patches to generate line-level ground truth.
    ```bash
    python code/data/derive_gt.py
    ```

3.  **Curate Dataset**:
    Generate the "hard" (high complexity), "easy", and synthetic subsets.
    ```bash
    python code/data/curate.py
    ```
    *Outputs: `data/curated/hard_subset.jsonl`, `data/curated/easy_subset.jsonl`, `data/curated/synthetic_subset.jsonl`.*

4.  **Validate Hard Subset (FR-010)**:
    Generate a report for manual inspection.
    ```bash
    python code/data/validate_hard.py
    ```
    *Output: `data/curated/validation_report.md`.*

## Running the Benchmark

Execute the full benchmark (Static Multi-Query + Iterative Agent) on the curated dataset.

```bash
python code/main.py --mode full
```

**Options**:
- `--mode full`: Run both static_multi and iterative agents on all curated issues.
- `--mode static_multi`: Run only the static multi-query baseline.
- `--mode iterative`: Run only the iterative agent.
- `--limit N`: Limit execution to N issues (default: all curated).
- `--turns N`: Set max turns for iterative agent (default: 3).
- `--sweep`: Run the turn limit sweep (3 vs 4) on a subset.

## Analyzing Results

1.  **View Metrics**:
    The script automatically generates `data/results/metrics.csv`.
    ```bash
    head data/results/metrics.csv
    ```

2.  **Run Statistical Tests**:
    Perform the Wilcoxon signed-rank test and Survival Analysis (Cox).
    ```bash
    python code/analysis/stats.py --input data/results/metrics.csv
    ```
    *Output: `data/results/stats_summary.json`.*

3.  **Visualize**:
    Generate coverage and efficiency plots.
    ```bash
    python code/analysis/plots.py --input data/results/stats_summary.json --output docs/figures/
    ```

## Verification

To verify the setup:
```bash
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/contract/ -v
```

## Troubleshooting

- **Out of Memory**: Reduce the `--limit` flag or ensure no other heavy processes are running.
- **Slow Execution**: The 6-hour limit is strict. If the run exceeds 4 hours, the script will log a warning and suggest reducing the sample size.
- **Dataset Download Fails**: Ensure network access to `huggingface.co`. The script retries 3 times.
- **Model Not Found**: If using `llama-cpp-python`, ensure the model file is downloaded to `data/models/`.