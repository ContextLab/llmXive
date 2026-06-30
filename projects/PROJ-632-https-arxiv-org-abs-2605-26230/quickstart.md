# Quickstart: GARD CPU Adaptation

This script runs a CPU-tractable adaptation of the GARD paper, replacing the heavy diffusion model with a tiny MLP denoiser on a small sample of real depth data.

## Prerequisites
Ensure you have the required packages installed:
```bash
pip install torch datasets torchvision matplotlib scikit-learn pandas tqdm
```

## Run Command
Execute the following command to run the full pipeline (data loading, training, evaluation, and artifact generation):

```bash
python code/main.py
```

## Expected Outputs
After completion, the following files will be generated in the `data/` and `figures/` directories:
- `data/denoised_results.json`: Quantitative metrics (RMSE, MAE) comparing noisy vs. denoised depth.
- `data/noisy_depths.csv`: A sample of pixel values (GT, Noisy, Denoised).
- `figures/denoising_comparison.png`: Visual comparison of the depth maps.

## Notes
- **Time**: Should complete in under 5 minutes on a standard CPU.
- **Approximation**: The original diffusion process is replaced by a 3-layer MLP to ensure CPU compatibility.
- **Data**: Uses a 50-image sample from the NYU Depth V2 dataset (real data).
