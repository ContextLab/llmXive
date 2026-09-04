# Quickstart: llmXive follow-up: extending "Guava: An Effective and Universal Harness for Embodied Manipulation"

## Prerequisites

- Python +
- Substantial RAM (CPU-only mode) or sufficient VRAM (GPU escape hatch)
- Access to the Guava dataset (see `data/download_guava.py`)
- Hugging Face account (for model access)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Data Preparation

1. **Download Guava Dataset**:
   ```bash
   python code/data/download_guava.py
   ```
   *Note: This script checks for the dataset. If unavailable, it will raise an error.*

2. **Transform to Symbolic-Guava**:
   ```bash
   python code/data/transform_symbolic.py \
     --input data/raw/guava \
     --output data/processed/symbolic_guava \
     --model yolo-tiny-onnx
   ```
   *This generates `SymbolicObservation` JSONs and logs perception latency.*

3. **Validate Perception (Critical)**:
   ```bash
   python code/data/validate_perception.py \
     --input data/processed/symbolic_guava \
     --gt data/raw/guava/annotations
   ```
   *This computes precision/recall. If recall < 90%, the pipeline halts.*

## Model Training

1. **Fine-tune Phi-3-mini**:
   ```bash
   python code/models/train_llm.py \
     --data data/processed/symbolic_guava \
     --model microsoft/Phi-3-mini-4k-instruct \
     --output checkpoints/symbolic_guava_llm
   ```
   *If this exceeds a predefined computational time threshold on CPU, the script will automatically trigger the GPU escape hatch. (if configured) or pause for manual intervention.*

## Evaluation

1. **Run Evaluation on Held-out Tasks**:
   ```bash
   python code/models/inference.py \
     --model checkpoints/symbolic_guava_llm \
     --data data/raw/guava/holdout_50 \
     --output results/evaluation.json
   ```

2. **Run Oracle-Symbolic Baseline**:
   ```bash
   python code/models/inference.py \
     --model oracle_symbolic \
     --data data/raw/guava/holdout_50 \
     --output results/oracle_evaluation.json
   ```

3. **Statistical Analysis**:
   ```bash
   python code/analysis/stats_test.py \
     --results results/evaluation.json \
     --baseline results/oracle_evaluation.json \
     --iterations a sufficient number to ensure convergence
   ```
   *Outputs p-value and conclusion comparing Symbolic vs. Oracle.*

## Verification

- **Check Data Integrity**:
  ```bash
  python code/data/checksums.py --verify
  ```
- **Run Tests**:
  ```bash
  pytest tests/
  ```

## Troubleshooting

- **Dataset Not Found**: Ensure the Guava dataset is accessible. If not, the project cannot proceed.
- **OOM Error**: Reduce batch size in `train_llm.py` or enable GPU escape hatch.
- **Latency > 150ms**: Check ONNX runtime version or switch to a lighter model (e.g., YOLO-nano).
- **Perception Recall < 90%**: The YOLO-tiny model is failing to detect objects. Check domain adaptation or switch to a different perception model.