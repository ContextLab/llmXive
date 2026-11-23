# Quickstart: llmXive follow-up: extending "LatentSkill: From In-Context Textual Skills to In-Weight Latent Skills"

## Prerequisites

*   Python 3.11+
*   GB+ RAM (for CPU execution) or access to a free Kaggle GPU.
*   Git.

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-887-llmxive-follow-up-extending-latentskill
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r code/requirements.txt
    ```

2.  **Verify Dependencies**:
    ```bash
    python -c "import torch, transformers, sentence_transformers; print('All deps OK')"
    ```

## Data Preparation

1.  **Download Weights**:
    *   The script `code/ingest/build_index.py` will automatically attempt to download the verified LoRA weights from the Hugging Face dataset repository (e.g., `peft/examples`).
    *   If the download fails (e.g., no open source), the script will exit with a clear error message.
    *   **Manual Override**: If you have local weights, place them in `data/raw/weights.npz`.

2.  **Build Index**:
    ```bash
    python code/main.py --step ingest
    ```
    *   **Output**: `data/processed/skill_index.npz`.
    *   **Verification**: Check `state/...yaml` for the checksum.

## Running the Evaluation

1.  **Execute Full Pipeline**:
    ```bash
    python code/main.py --step evaluate
    ```
    *   This runs the retrieval, synthesis, and evaluation loops.
    *   **Note**: This step is computationally intensive. On CPU, it may take 2-4 hours (reduced scale: a small number of tasks, 3 runs).
    *   **GPU Offload**: If the runner detects CUDA, it will automatically switch to GPU mode (if configured).

2.  **Generate Report**:
    ```bash
    python code/main.py --step report
    ```
    *   **Output**: `data/results/stats_report.json`.

## Validation

1.  **Check Results**:
    ```bash
    cat data/results/stats_report.json | python -m json.tool
    ```
    *   Verify `linearity_validation.valid` is `true`.
    *   Verify `comparisons` contain BH-corrected p-values.

2.  **Reproducibility Test**:
    ```bash
    python code/utils/seeds.py --verify
    ```
    *   Ensures all random seeds are pinned.

## Troubleshooting

*   **OOM (Out of Memory)**: If the base model fails to load on CPU, reduce the `batch_size` in `config.py` or enable the GPU escape hatch (if available).
*   **Missing Data**: If `data/raw/weights.npz` is missing, ensure the Hugging Face dataset is accessible. If not, the project cannot proceed (Constitution Principle III).