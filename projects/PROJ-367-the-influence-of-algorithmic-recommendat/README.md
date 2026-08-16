# The Influence of Algorithmic Recommendations on Exploration vs. Exploitation

## Project Structure

- `code/`: Source code for the analysis pipeline.
- `data/`: Input and output data files.
- `tests/`: Unit and integration tests.
- `docs/`: Documentation and reports.

## Setup

1. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

2. Run the pipeline:
 ```bash
 python code/main.py
 ```

## Data

This project requires a real dataset with `recommended_categories` and `enrolled_categories` columns.
The dataset source is configured in `code/config.py` and loaded in `code/ingestion.py`.
**Note**: The current configuration uses a placeholder dataset ID. It will be updated in T005/T013 with a verified real source.
If the real source is not available, the pipeline will fail loudly as per project constraints.

## Running Tests

```bash
pytest tests/
```