# Quickstart: llmXive follow-up: extending "PhysisForcing: Physics Reinforced World Simulator for Robotic Manipula"

## Prerequisites

-   Python 3.11+
-   pip (Python package manager)
-   Git
-   Sufficient disk space (~14 GB) and RAM (~7 GB) for CPU-only execution.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd projects/PROJ-951-llmxive-follow-up-extending-physisforcin
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r code/requirements.txt
```

*Note: The `requirements.txt` includes CPU-only versions of `torch` and other dependencies.*

### 4. Verify Environment

Run the following to ensure all dependencies are installed and the environment is ready:

```bash
python -c "import torch; import pybullet; import mujoco; print('Environment OK')"
```

### 5. Run the Pipeline

#### Step 1: Generate Synthetic Videos

```bash
python code/src/generation/wan21_generator.py --batch-size 100 --output-dir data/raw --batch-id A
python code/src/generation/wan21_generator.py --batch-size 100 --output-dir data/raw --batch-id B
python code/src/generation/wan21_generator.py --batch-size 100 --output-dir data/raw --batch-id C
```

*Note: This step may take several hours on CPU. Adjust `--batch-size` to manage memory.*

#### Step 2: Filter Videos

```bash
python code/src/filtering/pybullet_filter.py --input-dir data/raw --output-dir data/curated --threshold-percentile 60
```

#### Step 3: Data Augmentation (if needed)

```bash
python code/src/training/augmentation.py --input-dir data/curated --output-dir data/curated_aug --min-samples 30
```

#### Step 4: Train the Model

```bash
python code/src/training/diffusion_trainer.py --data-dir data/curated --epochs 10 --output-dir code/models
```

*Note: Training is capped at 4 hours. If the model diverges, the script will abort and log the error.*

#### Step 5: Evaluate the Model

```bash
python code/src/evaluation/r_bench.py --model-path code/models/best.pt --output-dir data/eval
python code/src/evaluation/pai_bench.py --model-path code/models/best.pt --output-dir data/eval
python code/src/evaluation/stats.py --input-dir data/eval --output-file data/eval/results.json
```

#### Step 6: Independent Validation (FR-008)

```bash
python code/src/evaluation/mujoco_validator.py --input-dir data/curated --output-dir data/eval
```

### 6. View Results

The final results, including benchmark scores and statistical tests, are stored in `data/eval/results.json`.

```bash
cat data/eval/results.json
```

### 7. Run Tests

```bash
pytest tests/ -v
```

## Troubleshooting

-   **Out of Memory**: Reduce the `--batch-size` in the generation step or use a smaller model architecture.
-   **CUDA Errors**: Ensure you are using the CPU-only version of `torch` (installed via `pip install torch --index-url https://download.pytorch.org/whl/cpu`).
-   **Physics Filter Failures**: Check the logs in `data/curated/logs/` for specific video IDs that failed simulation.
-   **CV Pipeline Errors**: If SAM2 or ZoeDepth fail, check the video format and resolution. Ensure the video is in MP4 format with H.264 codec.
