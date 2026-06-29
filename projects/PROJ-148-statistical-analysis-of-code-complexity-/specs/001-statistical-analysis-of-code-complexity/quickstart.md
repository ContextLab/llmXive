# Quickstart: Statistical Analysis of Code Complexity Metrics and Bug Prediction

## Prerequisites

- Python 3.11+
- Git
- Sufficient disk space (≥14GB recommended for raw data + processed artifacts)

## Installation

1.  **Clone Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-148-statistical-analysis-of-code-complexity-
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `lizard` may require system dependencies.*

3.  **Configure Environment**:
    Set random seeds in `code/utils/config.py` (Constitution Principle I).

## Execution Order

1.  **Download Data**:
    ```bash
    python code/data/download_gh.py
    ```
    *Warning: GHTorrent source is unverified (see `research.md`). Ensure network connectivity.*

2.  **Extract Metrics**:
    ```bash
    python code/data/extract_metrics.py
    ```

3.  **Preprocess**:
    ```bash
    python code/data/preprocess.py
    ```

4.  **Train Models**:
    ```bash
    python code/modeling/train.py
    ```

5.  **Evaluate & Report**:
    ```bash
    python code/modeling/evaluate.py
    ```

## Validation

- **Contract Tests**: Run `pytest tests/contract/` to verify schema compliance.
- **Data Hygiene**: Check `state/` for checksums.
- **Reproducibility**: Re-run `code/` against `data/` on fresh runner (Constitution Principle I).

## Troubleshooting

- **RAM Error**: Reduce `--max-projects` flag in `download_gh.py`.
- **Lizard Error**: Ensure Java syntax is supported by `lizard` version.
- **GHTorrent Timeout**: Retry with backoff; check network.
