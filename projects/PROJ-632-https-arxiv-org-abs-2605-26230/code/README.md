# GARD Adaptation: Geometry-Aware Representation Denoising (CPU-Scaled)

## Original Paper Scope
The original paper proposes **GARD**, a diffusion-based framework operating in the feature space of a feed-forward 3D reconstructor. It:
1.  Takes degraded multi-view images.
2.  Extracts geometry-aware features.
3.  Uses a **diffusion model** to denoise these features.
4.  Reconstructs 3D geometry and restores RGB images.
5.  Evaluated on the **Depth Anything 3 (DA3)** benchmark (large-scale, GPU-heavy).

## Adaptation Strategy (CPU-Tractable)
To fit the 2 CPU / 7GB RAM / 25-min constraint, we make the following honest approximations:

1.  **Model Replacement**: The original diffusion backbone and 3D reconstructor are too large for CPU. We replace the "Diffusion-based Feature Denoising" with a **Classical Denoising Autoencoder (DAE)** using a tiny MLP (3 layers) trained on CPU. This preserves the *logic* of "learning a mapping from noisy features to clean features" without the computational cost of iterative diffusion sampling.
2.  **Data Subsampling**: We do not use the full DA3 benchmark. Instead, we download a **tiny sample (50 images)** from the **NYU Depth V2** dataset (a standard proxy for indoor multi-view depth/RGB tasks) using the Hugging Face `datasets` library.
3.  **Feature Extraction**: Instead of a heavy 3D reconstructor, we use **Depth Anything V1 (Tiny)** in CPU mode to extract the "geometry-aware" depth maps. These are treated as the "features" to be denoised.
4.  **Degradation Simulation**: We synthetically add Gaussian noise to the *real* depth maps (simulating the "degraded conditions" mentioned in the abstract) to create the input for our denoiser.
5.  **Metric**: We compute **RMSE** and **MAE** between the ground truth depth, the noisy input, and the denoised output.

## What is NOT Included
-   No actual diffusion sampling (too slow for CPU).
-   No full multi-view 3D reconstruction pipeline (no NeRF/3DGS).
-   No high-resolution RGB restoration (focus is on the geometry feature denoising core).

## Outputs
-   `data/noisy_depths.csv`: Summary of noisy depth statistics.
-   `data/denoised_results.json`: RMSE/MAE metrics comparing Noisy vs. Clean vs. Denoised.
-   `figures/denoising_comparison.png`: Visual comparison of Ground Truth, Noisy, and Denoised depth maps.
