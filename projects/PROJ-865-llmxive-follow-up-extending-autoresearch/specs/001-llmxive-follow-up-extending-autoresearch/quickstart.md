# Quickstart: llmXive follow-up: extending "AutoResearchClaw"

## Prerequisites

- Python 3.11+
- Git
- HuggingFace CLI (optional, for dataset inspection)
- Limited RAM available (GitHub Actions free tier)

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-865-llmxive-follow-up-extending-autoresearch
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Verify dataset access** (optional):
    ```bash
    python -c "from datasets import load_dataset; ds = load_dataset('claw-ai-lab/arc-bench', streaming=True); print(next(iter(ds)))"
    ```

## Running the Pipeline

The pipeline is executed in three stages.

### Stage 1: Ingest, Annotate & Validate (US-1)
Downloads data, validates annotations against human gold standard, and distills rules.
```bash
python code/main.py --stage ingest_and_distill
```
*Output*: `data/derived/rules_library.json`, `data/derived/annotation_validation.json`

### Stage 2: Execute & Compare (US-2)
Runs the rule engine and baseline on the test set.
```bash
python code/main.py --stage execute_and_compare
```
*Output*: `data/derived/results.csv`, `data/derived/resource_usage.log`

### Stage 3: Analyze (US-3)
Performs statistical analysis and generates the report.
```bash
python code/main.py --stage analyze
```
*Output*: `data/derived/regression_results.json`, `paper/analysis_report.md`

## Testing

Run unit tests:
```bash
pytest tests/unit/
```

Run contract tests:
```bash
pytest tests/contract/
```

## Troubleshooting

- **OOM Error**: If the process runs out of memory, ensure `streaming=True` and `itertools.islice` fallback are active in `data/loader.py` and that the sample size is reduced in `config.py`.
- **Dataset Not Found**: Verify network access to HuggingFace. Check the `# Verified datasets` block in `research.md` for correct URLs.
- **Model Load Failure**: If the INT4 model fails on CPU, the system will abort or scale down. GPU is **not** used for primary analysis.
- **Resource Limits**: Check `data/derived/resource_usage.log` to ensure the experiment stayed within the 6-hour/7GB limits (SC-005).