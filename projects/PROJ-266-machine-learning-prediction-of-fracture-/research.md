# Research: Machine Learning Prediction of Fracture Toughness from Microstructure Images

## Introduction
This project investigates the feasibility of predicting fracture toughness ($K_{IC}$) of metallic alloys directly from microstructure images using deep learning. The core hypothesis is that predictive features such as grain boundaries, precipitate distributions, and phase morphology contain sufficient signal to estimate mechanical properties without explicit feature engineering.

## Methodology
The methodology employs a supervised learning pipeline. Input data consists of grayscale microstructure images (128x128 pixels) paired with ground-truth $K_{IC}$ values. The ground truth is generated synthetically using a physics-informed model defined in Section 3.2, as real-world labeled datasets of sufficient size and consistency are currently unavailable.

### 3.2 Synthetic Ground Truth Generation
To ensure reproducibility and control over the data distribution, $K_{IC}$ values are generated using a deterministic formula based on microstructural parameters:

$$K_{IC} = \text{base\_value} + \alpha \cdot \text{grain\_size} + \beta \cdot \text{precipitate\_density} + \text{noise}$$

Where:
- `base_value`: A baseline toughness constant specific to the alloy family.
- `grain_size`: The average grain diameter in microns (derived from image analysis).
- `precipitate_density`: The number of precipitates per unit area.
- `alpha`, `beta`: Coefficients representing the influence of grain size and precipitates on toughness (Hall-Petch and precipitation hardening effects).
- `noise`: Gaussian noise ($\sigma$) to simulate experimental uncertainty.

This synthetic ground truth is strictly derived from the Plan's methodology and serves as a proxy for real measurements during model training and validation. The generation logic is implemented in `code/data/synthetic_gen.py`.

### Sample Preparation Protocol
The synthetic generation includes metadata to simulate real sample preparation variance:
- **Magnification Calibration**: Modeled as a random uniform distribution $[L, U]$ pixels/micron to account for varying microscope settings.
- **Section Thickness**: Modeled as a random uniform distribution $[L_{thick}, 50]$ nm, serving as a proxy for TEM section thickness or SEM depth of field.
- **Surface Preparation**: Variance in surface finish is simulated by adding noise to the generated microstructure textures.

## Resolution Limits
The imaging resolution is defined by the synthetic generator's `min_feature_size_pixels` parameter (default 4 pixels). Features smaller than this threshold cannot be resolved and are effectively blurred. The imaging resolution is approximately 0.5 microns/pixel for the standard 128x128 output size, limiting the detection of sub-micron precipitates.

### Variance Analysis
The model's predictions account for variance in feature extraction across different synthetic preparation batches by training on data that includes randomized magnification calibration and section thickness parameters. This forces the CNN to learn invariant features rather than artifacts of specific preparation settings.

## Results
The generated dataset targets a sample size defined in `CONFIG['target_sample_size']` (default 500). We enforce a minimum of 200 images to ensure statistical power for the Wilcoxon signed-rank test used in model comparison. This sample size is justified by the compute feasibility constraints of the current research environment while providing sufficient data to validate the hypothesis that microstructure images contain predictive signal for fracture toughness.

## Discussion
While the synthetic nature of the data limits direct physical extrapolation, the pipeline demonstrates the architectural capability to learn structure-property relationships. Future work must validate these findings against real experimental datasets with verified $K_{IC}$ measurements.

## Limitations
The primary limitation is the reliance on synthetic ground truth. The model's ability to detect specific grain boundary characters is constrained by the imaging resolution (pixels per micron) defined in the generator. Features smaller than the minimum resolvable feature size are not represented in the training data, potentially leading to underestimation of their contribution to fracture toughness.