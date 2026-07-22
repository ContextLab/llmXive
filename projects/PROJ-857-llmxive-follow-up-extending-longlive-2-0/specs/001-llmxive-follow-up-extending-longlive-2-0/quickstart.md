# Quickstart: llmXive follow-up: extending "LongLive-2.0: An NVFP4 Parallel Infrastructure for Long Video Generation"

## Prerequisites

- Python 3.11+
- Git
- Access to HuggingFace Hub (for dataset/model download)

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-857-llmxive-follow-up-extending-longlive-2-0/code
    ```

2.  **Create a virtual environment** and install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Verify HuggingFace access** (if required for private datasets, though Kinetics-400 is public):
    ```bash
    huggingface-cli login
    ```

## Running the Simulation

### 1. Download and Downsample Dataset
This step extracts 4-second clips from Kinetics-400 and saves them to `data/derived/`.

```bash
python data/downsampler.py --num-clips 500 --output data/derived/kinetics_4s_subset_v1.parquet
```
*Output*: `data/derived/kinetics_4s_subset_v1.parquet` and a checksum file.

### 2. Run the Training Simulation
Execute the full experimental suite (varying bit-widths) with 3 seeds each.

```bash
python main.py --config config.py
```
*Output*: Logs in `data/results/` and a summary CSV.

### 3. Run the Evaluation
If not included in `main.py`, run the evaluator separately:

```bash
python evaluation/clip_evaluator.py --input data/results/generated_clips/ --output data/results/consistency_scores.json
```

### 4. Analyze Thresholds
Generate the precision-consistency curve and identify the degradation threshold.

```bash
python analysis/threshold_finder.py --input data/results/aggregated.csv --output data/results/threshold_analysis.png
```

## Verification

To verify the setup:

1.  **Check Memory**: Ensure the simulation completes without OOM errors (target < 7GB).
2.  **Check Noise**: Verify that the KL-divergence between simulated noise and uniform distribution is < 5% (check `data/results/kl_divergence_per_bitwidth.json`).
3.  **Check Consistency**: Ensure the CLIP-ViT scores are numeric and not NaN (unless "Collapse" is expected for 2-bit).

## Troubleshooting

- **OOM Error**: Reduce `--num-clips` in the downsampler or increase batch size in `config.py`.
- **CUDA Error**: The simulation is CPU-only. If you see CUDA errors, check that `torch` was installed with CPU support or that no GPU-specific code was inadvertently imported.
- **Dataset Download Failed**: Ensure internet connection and HuggingFace token (if required).
