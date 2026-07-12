# Quickstart: llmXive follow-up: extending "ABot-Earth 0.5: Generative 3D Earth Model"

## Prerequisites

- Python 3.11+
- Git
- Access to Microsoft Planetary Computer (Sentinel-2) and USGS 3DEP/NYC Open Data (LiDAR).
- Sufficient RAM (for local testing; CI uses comparable resources).

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-988-llmxive-follow-up-extending-abot-earth-0/code/
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    Ensure `onnxruntime` and `torch` are CPU-only:
    ```bash
    python -c "import torch; import onnxruntime; print('CPU Ready:', torch.cuda.is_available() == False)"
    ```

## Running the Pipeline

The pipeline is designed to run sequentially. For the full study, use the distributed runner script. For a quick test, run a single sample.

### Step 1: Data Curation (Single Sample)
Download and align one sample to verify the pipeline.
```bash
python 01_data_curation.py --sample-id "test_sample_01" --force-download
```
*Expected Output*: `data/processed/aligned_pairs/test_sample_01.json`

### Step 2: Mask Validation
Validate synthetic masks against real masks (FR-006).
```bash
python b_validate_masks.py --sample-size 10
```
*Expected Output*: `data/results/mask_similarity_report.txt`

### Step 3: Degradation
Apply synthetic degradation.
```bash
python 02_degradation_pipeline.py --scene-id "test_sample_01" --mode "mixed" --nnf 0.5
```
*Expected Output*: `data/processed/degraded_scenes/test_sample_01_mixed.npy`

### Step 4: 3DGS Generation (CPU)
Run the reconstruction.
```bash
python *_3dgs_cpu_inference.py --scene-id "test_sample_01" --method "inpaint"
```
*Expected Output*: `data/processed/reconstructions/test_sample_01_inpaint.ply` (within 45 mins).

### Step 5: Metrics Evaluation
Calculate fidelity.
```bash
python 04_metrics_evaluation.py --scene-id "test_sample_01" --method "inpaint"
```
*Expected Output*: Appended row to `data/results/metrics.csv`.

### Step 6: Threshold Analysis
Run the statistical sweep (requires a dataset of at least 10 samples).
```bash
python 05_threshold_analysis.py --nnf-steps 0.05 --alpha 0.05
```
*Expected Output*: `data/results/threshold_plot.png`, `data/results/statistical_report.txt`.

## Configuration

Edit `config.yaml` (if present) or pass arguments to modify:
- `--nnf-steps`: Step size for threshold sweep (default 0.05).
- `--max-gaussians`: Limit for 3DGS to control memory (default a substantial volume).
- `--timeout`: Max seconds per scene (default).
- `--city-list`: Path to `city_list.txt` (default `data/city_list.txt`).

## Troubleshooting

- **ERR_OOM_CPU**: Reduce `--max-gaussians` or `--patch-size`.
- **CUDA Error**: Ensure `torch` is the CPU version. Check `torch.cuda.is_available()`.
- **Alignment Error > 2m**: Check CRS alignment between Sentinel-2 and LiDAR.
- **Temporal Confound**: Check `temporal_gap_months` in `metrics.csv`; exclude if > 12.