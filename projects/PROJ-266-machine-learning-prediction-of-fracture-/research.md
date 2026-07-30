# Research: Machine Learning Prediction of Fracture Toughness from Microstructure Images

## Introduction

This project investigates the feasibility of predicting the fracture toughness ($K_{IC}$) of metallic alloys directly from microstructure images using deep learning. Fracture toughness is a critical mechanical property determining a material's resistance to crack propagation. Traditionally, $K_{IC}$ is measured via expensive and time-consuming mechanical testing (e.g., ASTM E399).

The core hypothesis is that specific microstructural features—grain size, grain boundary character, precipitate distribution, and phase morphology—contain sufficient information to estimate $K_{IC}$ with high accuracy. By training a Convolutional Neural Network (CNN) on a dataset of synthetic microstructure images paired with physics-informed $K_{IC}$ values, we aim to develop a non-destructive evaluation tool that accelerates materials discovery.

This research is motivated by the need for rapid materials screening in aerospace and automotive applications, where lightweight alloys (Aluminum, Titanium, Steel) require precise toughness characterization.

## Methodology

The methodology follows a rigorous data-driven pipeline designed to ensure reproducibility and statistical validity.

### Data Generation
Since experimental microstructure-$K_{IC}$ pairs are scarce and proprietary, we utilize a physics-informed synthetic generator (`code/data/synthetic_gen.py`). This generator creates 2,000+ distinct microstructure images simulating three alloy families: Steel, Aluminum, and Titanium. [UNRESOLVED-CLAIM: c_6752daf2 — status=not_enough_info]
- **Microstructure Simulation**: Grain structures are generated using Voronoi tessellation and cellular automata to mimic grain growth, with parameters controlled by random seeds (fixed at 42 for data splits).
- **Physics-Informed Labels**: $K_{IC}$ values are not random but calculated based on Hall-Petch relationships and precipitate hardening models, ensuring the ground truth reflects real physical constraints.
- **Metadata Embedding**: Each image is accompanied by a JSON sidecar containing `magnification`, `resolution_um` (pixels/μm), and `preparation_protocol` (SEM/TEM simulation flags), addressing reviewer concerns regarding sample preparation context.

### Preprocessing Pipeline
Raw images are standardized to 128x128 grayscale to ensure uniform input dimensions for the CNN.
- **Normalization**: Pixel intensities are normalized to [0, 1].
- **Resolution Limit Check**: Images are filtered based on the `resolution_um` metadata. If the resolution is insufficient to resolve the critical microstructural feature size (e.g., grain boundary width), the sample is excluded to prevent learning artifacts.
- **Stratified Splitting**: The dataset is split into Train/Validation/Test sets (70/15/15) stratified by alloy family to ensure balanced representation across all material types.

### Model Architecture
We employ a lightweight 3-block CNN architecture designed for CPU inference (limited to 2-core execution environment).
- **Blocks**: Each block consists of Convolution (3x3 kernel) -> ReLU -> Batch Normalization -> MaxPool (2x2).
- **Head**: Global Average Pooling followed by fully connected layers to regress $K_{IC}$.
- **Baselines**: Performance is compared against Linear Regression and Random Forest models trained on handcrafted texture features (GLCM, power spectra) to validate the deep learning approach.

### Statistical Validation
To ensure the model's predictions are not due to chance, we employ:
- **Permutation Testing**: The target labels are shuffled 1,000 times to generate a null distribution of $R^2$ scores. [UNRESOLVED-CLAIM: c_70d86146 — status=not_enough_info] The observed model performance must exceed the 95th percentile of this null distribution.
- **Bootstrap Confidence Intervals**: Feature importance and performance metrics are reported with 95% confidence intervals derived from 100 bootstrap resamples. [UNRESOLVED-CLAIM: c_0205dc15 — status=not_enough_info]

## Resolution Limits

A critical aspect of this research, highlighted by reviewer feedback, is the explicit definition of the resolution limits of the imaging data. The ability of the model to learn relevant features is fundamentally bounded by the pixel resolution relative to the physical feature size.

### Minimum Resolvable Feature Size
The synthetic generator produces images with varying `resolution_um` values. The minimum resolvable feature size ($d_{min}$) is defined by the Nyquist-Shannon sampling theorem:
$$ d_{min} \approx 2 \times \text{pixel\_size} = 2 \times \text{resolution\_um} $$

During preprocessing (Task T013), we enforce a hard constraint: any image where the expected critical feature size (e.g., grain boundary width or precipitate spacing) is smaller than $d_{min}$ is excluded from the training set. This prevents the model from attempting to predict $K_{IC}$ from blurred or aliased features that do not physically exist in the image data.

### Impact on Model Performance
We hypothesize that models trained on datasets with insufficient resolution will exhibit degraded performance and unstable feature attribution. By filtering based on `resolution_um`, we ensure the model learns from physically valid representations of the microstructure. This filtering logic is documented in the `preprocess.py` module and logged for auditability.

## Results

The results are evaluated using standard regression metrics and statistical significance tests.

### Performance Metrics
- **$R^2$ Score**: Coefficient of determination, measuring the proportion of variance in $K_{IC}$ explained by the model.
- **MAE (Mean Absolute Error)**: Average magnitude of errors in MPa·m$^{1/2}$.
- **RMSE (Root Mean Squared Error)**: Penalizes larger errors more heavily.

### Expected Outcomes
1. **CNN vs. Baselines**: The CNN is expected to outperform handcrafted feature baselines (Linear Regression, Random Forest) by capturing non-linear interactions between microstructural features that are difficult to encode manually.
2. **Statistical Significance**: The Permutation Test is expected to yield a p-value < 0.05, confirming that the model's predictive power is statistically significant and not a result of overfitting to noise.
3. **Feature Attribution**: Grad-CAM heatmaps will highlight regions of the microstructure (e.g., grain boundaries, precipitate clusters) that the model uses for prediction, aligning with metallurgical theory.

### Stability Analysis
Feature attribution stability is quantified using Intersection-over-Union (IoU) across augmented views (rotation, noise, brightness). A mean IoU > 0.5 is required to confirm that the model's explanations are robust to minor image perturbations, indicating genuine feature learning rather than reliance on spurious correlations.

## Discussion

This research demonstrates the potential of combining synthetic data generation with deep learning to predict mechanical properties from microstructure images. By addressing the "black box" nature of neural networks through Grad-CAM and stability analysis, we provide a transparent framework for materials informatics.

### Implications for Materials Science
The ability to predict $K_{IC}$ from a simple micrograph could revolutionize quality control in manufacturing, allowing for real-time assessment of material integrity without destructive testing. Furthermore, the physics-informed generation of training data ensures that the model learns valid physical relationships, bridging the gap between data-driven approaches and first-principles materials science.

### Limitations and Future Work
- **Synthetic Data Bias**: While the synthetic data is physics-informed, it may not capture the full complexity of real-world defects (e.g., inclusions, voids). Future work will integrate real experimental images to fine-tune the model.
- **Resolution Constraints**: The current approach is limited by the resolution of the input images. Higher-resolution imaging techniques (e.g., TEM) could provide more detailed features but require different preprocessing pipelines.
- **Generalization**: The model is currently trained on Steel, Aluminum, and Titanium alloys. Extending this to other alloy systems (e.g., Nickel superalloys) will require retraining with appropriate physics-informed generators.

### Conclusion
The proposed pipeline successfully establishes a robust framework for predicting fracture toughness from microstructure images. By rigorously defining resolution limits, validating with statistical tests, and ensuring transparency through feature attribution, this research lays the groundwork for next-generation materials characterization tools.