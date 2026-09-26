# Quickstart: Evaluating the Impact of Prompt Complexity on LLM Code Generation Performance

## Prerequisites

- Python 3.11+
- `pip`
- Access to the HuggingFace Hub (for `human-eval` package)
- (Optional) API Key for LLM inference (if not using local model)

## Installation

1.  **Clone the repository** (assuming standard structure):
    ```bash
    git clone <repo-url>
    cd projects/PROJ-527-evaluating-the-impact-of-prompt-complexi
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` includes `human-eval`, `tiktoken`, `statsmodels`, `pandas`, `ruff`.*

## Running the Pipeline

The pipeline is executed via the main entry point.

1.  **Initialize Data & Structure**:
    This step creates the required directories and downloads the HumanEval dataset.
    ```bash
    python code/main.py --action init
    ```
    *This verifies the dataset source and populates `data/raw/`.*

2.  **Generate Prompts**:
    Generates the complexity variants for all problems in the dataset.
    ```bash
    python code/main.py --action generate
    ```

3.  **Execute & Analyze**:
    Queries the LLM (API or local), runs unit tests, performs static analysis, and fits the LMM.
    ```bash
    python code/main.py --action run
    ```
    *Note: If a local GPU model is configured, this may trigger the GPU escape hatch logic.*

4.  **Review Results**:
    Check the generated artifacts:
    - `data/results/execution_results.parquet`
    - `data/results/analysis_summary.json`
    - `data/results/manual_review_queue.csv` (Flagged samples)

## Configuration

Edit `code/config.py` to set:
- `LLM_MODEL`: e.g., "gpt-4", "meta-llama/Llama-2-7b-hf"
- `API_KEY`: Your LLM provider key.
- `SEED`: Random seed for reproducibility.
- `MAX_WORKERS`: Parallelism for execution.

## Troubleshooting

- **Dataset Loading Error**: Ensure `human-eval` is installed (`pip install human-eval`).
- **CUDA Error**: If using a local model, ensure the GPU escape hatch is triggered or switch to CPU mode in `config.py`.
- **Timeout**: Increase `TIMEOUT_SECONDS` in `config.py` if code execution hangs.
