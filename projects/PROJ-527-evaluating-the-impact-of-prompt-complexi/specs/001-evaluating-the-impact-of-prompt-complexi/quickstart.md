# Quickstart: Evaluating the Impact of Prompt Complexity on LLM Code Generation Performance

## Prerequisites

- Python 3.11+
- Git
- HuggingFace CLI (optional, for model downloads)
- Access to a CPU-tractable LLM (API key or local GGUF model)

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r projects/PROJ-527-evaluating-the-impact-of-prompt-complexi/code/requirements.txt
    ```

## Configuration

1.  Set the `HF_TOKEN` environment variable for HuggingFace access (if required):
    ```bash
    export HF_TOKEN="your_token_here"
    ```
2.  (Optional) Configure the LLM endpoint in `code/config.py` if using a specific API.

## Running the Pipeline

To run the full analysis (generation, execution, analysis):

```bash
python projects/PROJ-527-evaluating-the-impact-of-prompt-complexi/code/main.py
```

**Note**: This may take several hours on CPU. To test with a small subset:
```bash
python projects/PROJ-527-evaluating-the-impact-of-prompt-complexi/code/main.py --sample-size 10
```

## Versioning & Checksums

After the pipeline runs, the `hash_artifacts.py` script will automatically compute SHA-256 hashes for all data artifacts and update the project state file:
```bash
python projects/PROJ-527-evaluating-the-impact-of-prompt-complexi/code/utils/hash_artifacts.py
```

## Testing

Run unit tests:
```bash
pytest tests/unit/
```

Run integration tests (requires LLM access):
```bash
pytest tests/integration/
```

## Output

- **Data**: `data/processed/results.csv`
- **Plots**: `data/figures/complexity_vs_performance.png`
- **Logs**: `logs/run_*.log`
- **State**: `state/projects/PROJ-527-...yaml` (updated with checksums)