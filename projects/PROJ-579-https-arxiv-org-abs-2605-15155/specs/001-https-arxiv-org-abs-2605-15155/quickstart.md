# Quickstart: Self-Distilled Agentic Reinforcement Learning (SDAR) Reproduction

## 1. Prerequisites

- **Python**: 3.10 or higher.
- **Git**: To clone the submodule.
- **System**: Linux (Ubuntu 22.04+ recommended for ALFWorld compatibility).
- **Disk**: ~15GB (for dependencies and ALFWorld assets).
- **Memory**: 8GB+ recommended (project target is 7GB, but 8GB provides headroom).

## 2. Setup Instructions

### 2.1 Clone Repository and Submodules
```bash
git clone <repository-url>
cd <project-dir>
git submodule update --init --recursive
```

### 2.2 Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate
```

### 2.3 Install Dependencies
```bash
pip install -r code/requirements.txt
```
*Note: `requirements.txt` pins `torch` to a CPU-only version and includes `alfworld`, `ray`, `scikit-learn`, and `transformers` (distilbert).*

### 2.4 Verify Environment (Sanity Check)
Run the Ray health check to ensure CPU-only initialization:
```bash
python tests/ray_cpu/check_worker_alive/main.py
```
**Expected Output**: "Ray cluster healthy", "2 CPUs detected", no CUDA errors.

## 3. Execution Workflow

### 3.1 Run Sanity Training (Steps)
Execute a minimal SDAR training run to verify the loop:
```bash
bash code/run_training.sh --steps <variable> --env alfworld --seed 0
```
**Output**: `outputs/logs/train_log.json`, `outputs/checkpoints/step_5.pt`.

### 3.2 Run Evaluation (Multiple Tasks)

The research question remains: How does the proposed method perform across diverse evaluation tasks? The method involves executing the evaluation protocol on a set of tasks to assess performance. References: (preserve existing citations).
Evaluate the trained (or random) model on a small subset:
```bash
bash code/run_evaluation.sh --num_tasks [variable] --timeout 60 --seed 0
```
**Output**: `outputs/logs/eval_log.json`, console success rate.

### 3.3 Run Full Baseline Comparison (Multiple Seeds)
Execute the full comparative analysis (SDAR vs. PPO) with fixed tasks:
```bash
bash code/run_baseline.sh --seeds multiple --steps
```
**Output**: `data/raw/train_log_*.json`, `data/raw/eval_log_*.json`.

### 3.4 Parse and Analyze
Generate the statistical report and update state:
```bash
python code/parse_logs.py
python code/analyze_results.py
```
**Output**: `data/processed/sdar_results.csv`, `data/processed/statistical_analysis.json`.

## 4. Troubleshooting

- **CUDA Error**: Ensure `export CUDA_VISIBLE_DEVICES=""` is set before running any Python script.
- **ALFWorld Timeout/Thor Failure**: If the Thor binary fails to download or run, the script will automatically switch to `alfworld-text-only` mode or a mock environment. Check logs for "Fallback to text-only mode".
- **Memory Error**: Reduce `--steps` in `run_baseline.sh` or switch to a smaller model in `external/SDAR/config.yaml`.

## 5. Verification

To verify the reproduction:
1. Check `data/processed/statistical_analysis.json` for a valid `p_value` (diagnostic only).
2. Confirm `data/raw/` contains non-empty log files with real timestamps.
3. Ensure `outputs/checkpoints/` contains a `.pt` file from the sanity run.
4. Verify `state/projects/...yaml` has been updated with new artifact hashes.