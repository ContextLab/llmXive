# Quickstart: llmXive follow-up: extending "PhysisForcing: Physics Reinforced World Simulator for Robotic Manipula"

## 1. Prerequisites

- **Python**: 3.11+
- **System**: Linux (Ubuntu 22.04 recommended) or WSL2.
- **Dependencies**: `git`, `ffmpeg` (for video processing), `libgl1-mesa-glx` (for PyBullet headless mode).
- **GPU (Optional)**: For video generation (Kaggle GPU offload). If running generation locally, a CUDA-compatible GPU is required.

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify environment
python -c "import pybullet; print('PyBullet OK')"
python -c "import torch; print('Torch OK')"
python -c "import mujoco; print('MuJoCo OK')"
```

## 3. Configuration

Edit `config.yaml` to set:
- `generation`: Number of videos to generate (default: 1000).
- `filtering`: Discard percentage (default: 40).
- `training`: Epochs (default: 10), Learning rate.
- `benchmarks`: R-Bench and PAI-Bench thresholds.
- `sample_size`: Target sample size for statistical power (default: 50).

## 4. Running the Pipeline

### Step 1: Generate Videos
```bash
# Note: If running on CPU, this will be extremely slow. 
# For production, use the Kaggle offload script.
python src/cli/main.py --stage generation
```

### Step 2: Filter Videos & Create Control
```bash
python src/cli/main.py --stage filtering
```

### Step 3: Validate Filter (MuJoCo)
```bash
python src/cli/main.py --stage validation
```

### Step 4: Train Models
```bash
python src/cli/main.py --stage training
```

### Step 5: Evaluate & Benchmark
```bash
python src/cli/main.py --stage evaluation
```

## 5. Verification

Check `data/eval/results.json` for the benchmark scores and p-values.
Check `data/validation/mujo_co_validation_result.json` for the filter validity.
Run `pytest tests/` to verify unit and integration tests.

## 6. Troubleshooting

- **PyBullet Crash**: Ensure `libgl1-mesa-glx` is installed. Run in headless mode: `export PYBULLET_USE_NUMPY=1`.
- **OOM Error**: Reduce `batch_size` in `config.yaml`.
- **NaN Loss**: Reduce learning rate in `config.yaml`.
- **MuJoCo Error**: Ensure MuJoCo license is set or use the free version.
