# Quickstart: llmXive follow-up: extending Representation Forcing for Structured Text Generation

## 1. Prerequisites

-   Python 3.11+
-   Git
-   Sufficient disk space (for datasets and checkpoints)
-   Sufficient RAM (minimum), 4 GB recommended for training

## 2. Environment Setup

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-867-llmxive-follow-up-extending-representati

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 3. Data Download

The data download script will fetch the verified datasets from HuggingFace and store them in `data/raw/`.

```bash
# Run the data download script
python code/data/loaders.py --download
```

*Note: This will download PubLayNet. Ensure you have sufficient disk space.*

## 4. Run a Single Forward Pass (RF Token Extraction)

Test the frozen RF encoder with a single image.

```bash
python code/data/preprocessing.py --mode extract_rf --input data/raw/publaynet/sample_image.png --output data/processed/rf_tokens_test.json
```

*Expected Output: A JSON file containing the RF token sequence.*

## 5. Train the RF Model (Dry Run)

Run a minimal training loop (2 epochs) to verify the pipeline.

```bash
python code/train.py --model rf --epochs 2 --batch_size 4 --seed 42
```

*Expected Output: Training logs showing loss convergence and a saved checkpoint in `data/results/`.*

## 6. Evaluate the Model

Evaluate the trained model on the test set.

```bash
python code/evaluate.py --model rf --checkpoint data/results/rf_model_epoch_2.pt --test-set data/raw/publaynet/test.parquet
```

*Expected Output: A JSON file with `syntactic_validity_rate`, `ast_edit_distance`, and `p_value` (if baseline comparison is included).*

## 7. Full Pipeline

To run the entire experiment (RF vs. Baseline, statistical testing):

```bash
python code/main.py --full-pipeline
```

*This will download data, train both models, evaluate, and generate the final metrics report.*