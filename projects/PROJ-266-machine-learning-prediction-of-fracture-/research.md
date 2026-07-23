# Research Protocol: Machine Learning Prediction of Fracture Toughness from Microstructure Images

## Introduction

This project investigates the feasibility of predicting fracture toughness ($K_{IC}$) in metallic alloys (Steel, Aluminum, Titanium) directly from microstructure images. While traditional empirical models rely on hand-crafted features (grain size, volume fraction), this research leverages Convolutional Neural Networks (CNNs) to learn hierarchical representations of microstructural patterns—grain boundaries, precipitate distributions, and phase morphology—that correlate with mechanical performance.

The primary hypothesis is that deep learning models can capture non-linear interactions between microstructural features that are difficult to quantify manually, potentially surpassing baseline regression models. This protocol addresses critical gaps identified in initial review, specifically regarding imaging resolution limits, sample preparation metadata, and statistical confidence in feature extraction.

## Methodology

### Data Generation and Acquisition
Due to the scarcity of labeled experimental datasets linking specific micrographs to $K_{IC}$ values, this study utilizes a physics-informed synthetic data generator (`code/data/synthetic_gen.py`). The generator produces 2,000+ microstructure images simulating grain structures for three alloy families:
- **Steel**: Ferritic/pearlitic morphologies.
- **Aluminum**: Equiaxed grains with varying precipitate distributions.
- **Titanium**: Alpha-beta phase mixtures.

Each synthetic sample is paired with a calculated $K_{IC}$ value derived from established micromechanics models (Hall-Petch relationship and inclusion toughness models). Metadata including `magnification`, `resolution_um` (pixels per micron), and `preparation_protocol` (SEM/TEM simulation flags) are embedded in JSON sidecars to ensure traceability.

### Preprocessing Pipeline
Images are standardized to 128x128 grayscale to ensure uniform input dimensions for the CNN. The preprocessing pipeline (`code/data/preprocess.py`) enforces:
1. **Resolution Validation**: Samples with `resolution_um` below the theoretical detection limit for the target feature size are flagged or excluded.
2. **Stratified Splitting**: Data is split into train/validation/test sets (70/15/15) stratified by alloy family to prevent distributional shift.
3. **Normalization**: Pixel intensities are normalized to $[0, 1]$ using global min-max scaling.

### Model Architecture
The primary model is a lightweight 3-block CNN (Conv-ReLU-BatchNorm-MaxPool) designed for CPU inference efficiency. Baselines include Linear Regression and Random Forest models trained on hand-crafted texture features (GLCM, power spectra) to establish a performance floor.

### Evaluation Metrics
Performance is assessed using:
- **$R^2$ Score**: Coefficient of determination.
- **MAE / RMSE**: Mean Absolute and Root Mean Squared Errors in $MPa\sqrt{m}$.
- **Permutation Testing**: A non-parametric test is used to determine the statistical significance of the CNN's improvement over baselines (rejecting the null hypothesis that model performance is due to chance).

## Resolution Limits

A critical constraint in microstructure-based prediction is the imaging resolution relative to the physical feature size. The minimum resolvable feature size ($d_{min}$) is governed by the Nyquist-Shannon sampling theorem:
$$ d_{min} \approx 2 \times \text{pixel\_size} = \frac{2}{\text{resolution\_um}} $$

For this study, the synthetic generator enforces a minimum resolution of 0.5 $\mu m$/pixel, ensuring that grain boundaries and precipitates larger than 1.0 $\mu m$ are resolvable. Images with lower effective resolution (simulating poor SEM conditions) are excluded during the preprocessing phase (T013) to prevent the model from learning artifacts of undersampling.

The resolution limit directly impacts the "physics-informed" nature of the $K_{IC}$ calculation; features smaller than $d_{min}$ cannot contribute to the fracture process zone in the simulation, potentially biasing predictions for ultra-fine-grained alloys. This limitation is explicitly documented in the metadata for every sample.

## Results

*Note: This section is a placeholder for empirical results. Initial runs on the synthetic dataset are expected to show:*

1. **Baseline Performance**: Linear Regression on GLCM features typically achieves $R^2 \approx 0.4-0.5$, limited by the inability to capture complex grain boundary networks.
2. **CNN Performance**: The 3-block CNN is expected to achieve $R^2 \approx 0.7-0.8$, demonstrating the ability to learn hierarchical texture patterns.
3. **Statistical Significance**: Permutation tests (1,000 permutations) are anticipated to yield $p < 0.01$, confirming the CNN's superiority is not due to random initialization.
4. **Feature Attribution**: Grad-CAM heatmaps are expected to highlight grain boundaries and triple junctions as the primary regions of interest, aligning with fracture mechanics theory.

*Detailed results will be populated upon execution of `code/train/train_cnn.py` and `code/explain/stability.py`.*

## Discussion

The transition from hand-crafted features to end-to-end deep learning offers a promising avenue for microstructure-property prediction. However, the reliance on synthetic data introduces a "reality gap." While the physics-informed generator captures fundamental relationships (e.g., Hall-Petch), it may not fully replicate the stochastic complexity of real-world alloy processing (e.g., segregation, texture anisotropy).

Future work must address the domain shift by fine-tuning the model on limited experimental data (transfer learning). Additionally, the stability analysis (IoU of heatmaps across augmentations) will determine if the model relies on robust physical features or spurious correlations. The explicit documentation of resolution limits and preparation protocols is essential for interpreting model failures and establishing the boundary of applicability for the predictor.

This protocol satisfies the requirements for reproducibility by mandating fixed random seeds (42 for splits), versioned synthetic generators, and strict metadata validation, ensuring that any reported results can be independently verified.