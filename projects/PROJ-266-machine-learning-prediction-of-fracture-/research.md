# Machine Learning Prediction of Fracture Toughness from Microstructure Images

## Introduction

This project investigates the feasibility of predicting fracture toughness ($K_{IC}$) from microstructure images using deep learning and explainable AI (XAI) techniques. The primary goal is to establish a pipeline that correlates visual microstructural features—such as grain boundaries, precipitate distributions, and phase morphology—with mechanical properties.

**Critical Note on Data Source**: This project uses a **Synthetic Microstructure Generator** because no verified real-world dataset exists that pairs high-resolution microstructure images with precise $K_{IC}$ measurements for the specific alloy families of interest (Steel, Aluminum, Titanium). Consequently, the results presented in this study validate the **pipeline methodology** and the statistical robustness of the model architecture, rather than claiming direct real-world physical prediction accuracy.

## Methodology

### 3.1 Data Generation Strategy

To address the lack of real-world labeled data, we employ a deterministic synthetic generation process. This process creates realistic-looking microstructure images (128x128 pixels) and assigns corresponding $K_{IC}$ values based on a physics-informed formula. The generation process ensures that the relationship between microstructure and properties is consistent, allowing the model to learn the underlying mapping.

### 3.2 Synthetic $K_{IC}$ Deterministic Logic

The ground truth $K_{IC}$ values for the synthetic dataset are generated using a linear additive model with Gaussian noise. This formula approximates the contribution of key microstructural features to fracture toughness.

The deterministic logic is defined as follows:

$$K_{IC} = \text{base\_value} + \alpha \cdot \text{grain\_size} + \beta \cdot \text{precipitate\_density} + \text{noise}$$

Where:
- **`base_value`** (float): The baseline fracture toughness for the specific alloy family (e.g., Steel, Al, Ti) in MPa$\sqrt{m}$. This value represents the intrinsic toughness of the matrix material.
- **`grain_size`** (float): A normalized metric representing the average grain diameter (in microns) extracted from the synthetic image. According to the Hall-Petch relationship, smaller grains generally increase strength but may affect toughness differently depending on the material; here, $\alpha$ captures the specific sensitivity for our synthetic model.
- **`precipitate_density`** (float): A normalized metric (0.0 to 1.0) representing the area fraction of precipitates in the image. Precipitates often act as crack initiation sites or barriers; $\beta$ quantifies this effect.
- **`alpha`** (float): The coefficient for the grain size effect.
- **`beta`** (float): The coefficient for the precipitate density effect.
- **`noise`** (float): A random variable drawn from a normal distribution $\mathcal{N}(0, \sigma^2)$, where $\sigma$ is the standard deviation representing unmodeled microstructural variations and experimental uncertainty.

This formula is implemented in the codebase at `code/data/synthetic_gen.py` within the `calculate_physics_informed_k_ic` function. The parameters ($\alpha, \beta, \sigma$) are fixed constants defined in the configuration to ensure reproducibility across runs.

**Traceability**: The implementation of this logic is located in `code/data/synthetic_gen.py`. The generated values serve as the regression target for the CNN and baseline models.

### 3.3 Sample Preparation Protocol (Synthetic)

To simulate the variance found in real experimental data, the synthetic generator incorporates parameters for sample preparation:
- **Magnification Calibration**: Randomly sampled from a uniform distribution $[lower\_bound, upper\_bound]$ (pixels/micron) to simulate different microscope settings.
- **Section Thickness**: Randomly sampled from a uniform distribution $[low, 50]$ nm, acting as a proxy for TEM sample thickness or SEM depth of field effects, influencing the visibility of features.

## Results

(Results will be populated after execution of the training pipeline.)

## Discussion

### 4.1 Synthetic Data Limitations

This project validates the **pipeline methodology** using synthetic data. **No real-world dataset verification is performed** due to the unavailability of a public, high-quality dataset pairing microstructure images with $K_{IC}$ values for the target alloy families. The synthetic generator provides a controlled environment to test the model's ability to learn complex non-linear mappings and to evaluate the stability of XAI methods (Grad-CAM).

The findings should be interpreted as a proof-of-concept for the data processing and modeling pipeline. Future work must involve the acquisition of real-world data to validate the physical accuracy of the predictions.

### 4.2 Variance Analysis

The model's predictions account for variance introduced by the synthetic preparation batches through the inclusion of the `noise` term in the $K_{IC}$ generation formula. The stability of the model across different seeds is evaluated to ensure that the learned features are robust to these synthetic variations.

### 4.3 Resolution Limits

The synthetic generator enforces a minimum resolvable feature size defined by `min_feature_size_pixels` in the configuration. Features smaller than this threshold are not rendered, simulating the physical limits of optical or electron microscopy. This limitation affects the model's ability to detect sub-pixel grain boundary characters, which is a known constraint in experimental materials science.