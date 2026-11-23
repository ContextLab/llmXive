# Quickstart: llmXive Follow-up: Semantic Divergence Diagnostic

## 1. Prerequisites

- Python 3.11+
- `datasets` library
- `sentence-transformers` (CPU wheels)
- `rank_bm25`
- `scikit-learn`
- `pandas`
- `pyyaml`

## 2. Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-849-llmxive-follow-up-extending-agent-explor
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install ruff and black** (for linting):
    ```bash
    pip install ruff black
    ```

## 3. Data Preparation

1.  **Download MathVista**:
    The system automatically downloads the dataset on first run. Ensure you have sufficient free disk space.

2.  **Create Tool Mappings**:
    Ensure `data/tool_mappings/mathvista_tool_map.json` exists. If not, create a minimal version:
    ```json
    {
      "problem_id_1": ["calculator", "search_engine"],
      "problem_id_2": ["image_cropper", "text_summarizer"]
    }
    ```

3.  **Cache AXPO Outcomes** (Optional):
    If you have cached results from the AXPO agent, place them in `data/cache/axpo_simulated_outcomes.jsonl`. If missing, the system will use a heuristic fallback.

## 4. Running the Diagnostic

Run the main pipeline:

```bash
python -m src.cli.run_diagnostic
```

**Expected Output**:
- Logs showing dataset loading, embedding, and scoring.
- A summary report printed to stdout:
  ```
  Total Records: A substantial corpus of records was selected for analysis.
  Mean Divergence Score: Moderate levels of divergence are expected.
  Pearson Correlation: -0.32 (p < 0.05)
  Logistic Regression AUC-ROC: The model is expected to achieve a moderate level of discriminative performance.
  ```
- Output files in `data/processed/`.

## 5. Troubleshooting

- **Memory Error**: The system automatically downsamples to a manageable number of records. Check logs for `MemoryLimitExceededError` -> `Downsampling` message.
- **Timeout**: If the job exceeds 5 hours, it will abort with `TimeoutExceededError`.
- **Missing Tool Mapping**: Ensure `data/tool_mappings/mathvista_tool_map.json` exists and contains valid JSON.
- **No Thinking Traces**: The system will skip records without thinking prefixes. Check the log for `Skipping record: missing_thinking_prefix`.

## 6. Verification

Run the test suite:

```bash
pytest tests/
```

Ensure all tests pass, especially `test_metrics.py` and `test_pipeline.py`.
