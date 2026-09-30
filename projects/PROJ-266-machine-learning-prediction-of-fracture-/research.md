# Machine Learning Prediction of Fracture Toughness from Microstructure Images

## Introduction

This project investigates the feasibility of predicting fracture toughness ($K_{IC}$) of metallic alloys directly from microstructure images using deep learning. The core hypothesis is that microstructural features—such as grain boundaries, precipitate distributions, and phase morphology—contain sufficient information to estimate mechanical properties without explicit feature engineering.

**Synthetic Data Justification**: This project uses a **Synthetic Microstructure Generator** because no verified real-world dataset exists that pairs high-resolution microstructure images with precise $K_{IC}$ measurements for diverse alloy families. The synthetic generator implements a physics-informed model to create ground-truth labels. Consequently, the results of this pipeline validate the **methodology** and the end-to-end workflow, rather than establishing new real-world physical laws or replacing experimental testing.

## Methodology

### 2.1 Data Generation Strategy

The dataset is generated using a deterministic synthetic engine that simulates microstructures for three alloy families: Steel, Aluminum, and Titanium. The generator creates 128x128 pixel images representing grain structures and precipitate distributions.

### 2.2 Synthetic Ground Truth Logic

The $K_{IC}$ values are not measured experimentally but are derived from a parametric model that reflects known physical trends: smaller grains generally increase toughness (Hall-Petch relationship), while precipitate density and alloy composition modulate the base value.

#### 2.2.1 Deterministic Logic for $K_{IC}$ Generation

The ground truth $K_{IC}$ for each sample is calculated using the following deterministic formula:

$$ K_{IC} = \text{base\_value} + \alpha \cdot \text{grain\_size} + \beta \cdot \text{precipitate\_density} + \text{noise} $$

Where:
- `base_value`: A float representing the baseline toughness of the specific alloy family (e.g., Steel ~45 MPa√m, Al ~30 MPa√m, Ti ~60 MPa√m).
- `alpha`: The coefficient for grain size (typically negative, reflecting the Hall-Petch strengthening effect where smaller grains increase strength/toughness in specific regimes).
- `grain_size`: A scalar feature extracted from the generated image representing the average grain diameter in pixels.
- `beta`: The coefficient for precipitate density (positive, indicating precipitation hardening contributions).
- `precipitate_density`: A scalar feature representing the volume fraction or density of precipitates in the image.
- `noise`: A random variable drawn from a normal distribution $\mathcal{N}(0, \sigma)$ to simulate experimental uncertainty and microstructural variance not captured by simple metrics.

This formula is implemented in `code/data/synthetic_gen.py` within the `calculate_physics_informed_k_ic` function. The parameters (`base_value`, `alpha`, `beta`) are fixed constants defined per alloy family to ensure reproducibility across the synthetic dataset.

### 2.3 Imaging and Resolution Constraints

The synthetic images simulate Transmission Electron Microscopy (TEM) and Scanning Electron Microscopy (SEM) inputs.
- **Imaging Resolution**: The synthetic generator operates at a fixed resolution of 128x128 pixels.
- **Minimum Resolvable Feature Size**: Features smaller than `CONFIG['min_feature_size_pixels']` are not generated, simulating the physical resolution limit of the imaging system.
- **Sample Preparation Protocol**: Synthetic parameters for `magnification_calibration` (random uniform [lower, upper] pixels/micron) and `section_thickness` (random uniform [low, 50] nm) are applied to simulate variations in sample preparation.

### 2.4 Statistical Power and Sample Size

The dataset targets a sample size defined in `CONFIG['target_sample_size']` (default 500). This size is chosen to balance statistical power for training a lightweight CNN against computational feasibility, ensuring the full pipeline (preprocessing, training, attribution) completes within the 6-hour compute window.

## Discussion

### 4.1 Limitations and Scope

**Synthetic Data Limitation**: This project validates the pipeline methodology using synthetic data. No real-world dataset verification is performed due to data unavailability (Plan Summary). The results demonstrate that the proposed architecture and explainability workflow (Grad-CAM, stability analysis) function correctly on a controlled, physics-informed dataset. They do not claim to predict $K_{IC}$ for real-world alloys without further experimental calibration.

### 4.2 Variance Analysis

The model's predictions account for variance in feature extraction across different synthetic preparation batches through the inclusion of the `noise` term in the ground truth generation and the use of data augmentation during training.

### 4.3 Sample Preparation Protocol

The synthetic generation includes specific protocols for:
- **Magnification Calibration**: Simulated via random uniform distribution of pixels/micron.
- **Section Thickness**: Simulated as a proxy for TEM sample thickness (nm).
- **Surface Preparation**: Simulated via noise injection and texture variations for SEM proxies.
Expected variance in feature extraction is explicitly modeled to test the robustness of the attribution stability metrics.