# Quickstart: llmXive follow-up: extending "CiteVQA"

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI execution)

## Setup

1.  **Clone Repository**:
    ```bash
    git clone <repo-url>
    cd <repo-dir>
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

3.  **Download Data**:
    Ensure the `data/` directory contains the CiteVQA dataset (or the proxy `ICLR-pdfs` if CiteVQA is unavailable).
    ```bash
    # If using HuggingFace datasets
    python code/data_loader.py --download
    ```

4.  **Run Tests**:
    ```bash
    pytest tests/
    ```

## Execution

### Run Text-Only Pipeline
```bash
python code/main.py --mode text-only --model phi3-mini --retriever all-MiniLM-L6-v2
```

### Run Visual-Only Control
```bash
python code/main.py --mode visual-only --model tiny-vlm
```

### Generate Report
```bash
python code/metrics.py --aggregate --output results/report.json
```

## Troubleshooting

- **Out of Memory**: Reduce `--batch-size` to 1.
- **Dataset Not Found**: Check `data_loader.py` for the correct dataset name.
- **Timeout**: Increase the GitHub Actions runner timeout or reduce the test set size.
