# Quickstart: Self-improving LLM

## Prerequisites

*   Python 3.11 installed
*   Git installed
*   Hugging Face Hub access token (optional, for faster downloads)

## Installation

```bash
git clone https://github.com/your-repo/self-improving-llm.git
cd self-improving-llm
pip install -r requirements.txt
```

## Running the Pipeline

1.  **Download Data**: The script will automatically download necessary datasets from Hugging Face Hub.
2.  **Execute the Script**:

    ```bash
    python run_pipeline.py --cycles 3
    ```

    This command runs the entire pipeline for 3 refinement cycles. You can adjust the `--cycles` parameter to control the number of iterations.

## Output

The results will be stored in the following directories:

*   `results/trajectory.json`: Performance trajectory data across all cycles, including `plateau_cycle_index` and `trade_off_metrics`.
*   `models/`: Trained model checkpoints after each cycle.
*   `logs/`: Log files for each cycle, containing detailed information about training and evaluation.

## Configuration

You can configure the pipeline by modifying the `config.py` file:

*   `base_model`: Specifies the initial GPT 124M checkpoint.
*   `training_samples`: Controls the size of the OpenWebText subset used for training (default: a configurable subset size).
*   `training_epochs`: Sets the number of epochs to train the model in each cycle (default: a baseline value).