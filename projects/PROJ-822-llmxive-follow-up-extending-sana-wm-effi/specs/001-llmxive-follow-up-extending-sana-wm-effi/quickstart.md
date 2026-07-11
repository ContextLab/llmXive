# Quickstart: llmXive follow-up: extending "SANA-WM: Efficient Minute-Scale World Modeling with Hybrid Linear Diff"

## Prerequisites

- **Python**: 3.11+
- **System**: Linux (Ubuntu 22.04 recommended for COLMAP compatibility).
- **Disk**: Sufficient free space (for model weights, synthetic data, and video outputs).
- **RAM**: Sufficient memory is recommended for setup. (runtime requires substantial memory resources).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-822-llmxive-follow-up-extending-sana-wm-effi
    ```

2.  **Create a virtual environment**:
    ```bash
    python3.11 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: Ensure `torch` is installed with CPU support only (`torch==2.x+cpu`).*

4.  **Verify COLMAP installation**:
    ```bash
    colmap --version
    ```
    If not installed, follow the official COLMAP installation guide for your OS.

## Running the Experiment

### 1. Pilot Phase (Feasibility Check)
Generates a set of trajectories to measure runtime and select model/resolution.
```bash
python code/main.py --mode pilot --count 10
```
*Output: `data/results/pilot_report.json` with projected runtime and memory usage. If >6h projected, the script suggests fallback parameters.*

### 2. Generate Synthetic Trajectories
Generates a set of ground-truth trajectories (with procedural textures).
```bash
python code/main.py --mode generate --count 500
```
*Output: `data/synthetic/` directory with JSON files.*

### 3. Run Inference (Symbolic Encoder)
Generates videos using the symbolic encoder and NVFP4 weights.
```bash
python code/main.py --mode infer --encoder symbolic --quantization nvfp4 --batch 500
```
*Output: `data/generated/symbolic/` directory with MP4 files.*
*Note: This step includes runtime monitoring. If projected time > 6h, it aborts.*

### 4. Run Inference (Learned Baseline)
Generates videos using the learned text-to-image encoder (with hard-coded text templates).
```bash
python code/main.py --mode infer --encoder learned --quantization nvfp4 --batch 500
```
*Output: `data/generated/learned/` directory with MP4 files.*

### 5. Evaluate Geometric Consistency
Computes pose errors (with Procrustes alignment) and runs the statistical test.
```bash
python code/main.py --mode evaluate --test paired_t
```
*Output: `data/results/statistical_test.json` containing p-value, t-statistic, and conclusion.*

## Verifying Results

Check the final report:
```bash
cat data/results/statistical_test.json
```
Expected keys: `p_value`, `t_statistic`, `degrees_ofFreedom`, `conclusion`, `failure_handling_method`.

## Troubleshooting

- **OOM Error**: If the process crashes with "Out of Memory", reduce the resolution in `config.py` to 360p or reduce the sequence duration to 10s.
- **COLMAP Failure**: If `PoseEstimationResult` shows many `invalid_low_conf` frames, check the synthetic data generation for sufficient texture/noise (Perlin noise seed).
- **Quantization Error**: If `ERR_QUANT_UNSUPPORTED` is raised, the NVFP4 format is not supported by the current `torch`/`transformers` version. Check `requirements.txt` for compatible versions or fallback to a smaller model.
- **Runtime Limit**: If the pilot phase projects >6h, reduce `--duration` to 10s or `--resolution` to 360p in `config.py`.