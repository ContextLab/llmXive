# Quickstart: llmXive follow-up: extending "PhysisForcing: Physics Reinforced World Simulator for Robotic Manipula"

## Prerequisites

- Python 3.11+
- Git
- Access to Hugging Face (for Wan2.1 and PyBullet datasets)
- (Optional) Kaggle account for GPU offloading (if generation fails on CPU)

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note*: `requirements.txt` includes `torch` (CPU), `diffusers`, `pybullet`, `mujoco`, `pandas`, `numpy`, `scipy`.

4. **Configure Environment**:
   - Set `HF_TOKEN` if required for private datasets.
   - Ensure `config.yaml` is present in the root of `code/`.

## Running the Pipeline

### Step 1: Generate & Filter (US-1)
This step generates videos and filters them. If the generation step requires GPU, the script will attempt to offload to Kaggle (if configured) or fail gracefully.
```bash
python src/cli/run_pipeline.py --phase generate_and_filter
```
*Output*: `data/curated/` with filtered videos and `scores.parquet`.

### Step 2: Train Model (US-2)
Trains the large-scale diffusion model on the curated dataset.
```bash
python src/cli/run_pipeline.py --phase train
```
*Output*: `data/models/model_*.pt`.

### Step 3: Evaluate (US-3)
Evaluates the trained model against baselines and runs TOST.
```bash
python src/cli/run_pipeline.py --phase evaluate
```
*Output*: `data/results/evaluation.json`.

## Verifying Results

- **Check Filtration**:
  ```bash
  python -c "import pandas as pd; df = pd.read_parquet('data/curated/scores.parquet'); print(f'Retention Rate: {(df.pass_status.mean()*100):.2f}%')"
  ```
- **Check Equivalence**:
  ```bash
  cat data/results/evaluation.json | jq '.equivalence_flag'
  ```

## Troubleshooting

- **CUDA Error during Generation**: The script will log a warning. If configured for Kaggle, it will retry. If not, the user must manually run the generation step on a GPU and save the results to `data/raw/`.
- **Memory Error during Training**: Reduce `batch_size` in `config.yaml`.
- **PyBullet Crash**: Check `logs/filtering.log` for specific video IDs causing crashes. These are automatically excluded.
