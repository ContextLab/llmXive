# Research Protocol: Machine Learning Prediction of Fracture Toughness from Microstructure Images

## Introduction

This research project investigates the feasibility of predicting fracture toughness ($K_{IC}$) in metallic alloys directly from microstructure images using deep learning. The primary phenomenon of interest is the relationship between microstructural features—such as grain boundaries, precipitate distributions, and phase morphology—and the macroscopic mechanical property of fracture resistance.

Current methodologies often rely on hand-crafted features or simplified analytical models that may fail to capture the complex, non-linear interactions within the microstructure. This study proposes a data-driven approach utilizing Convolutional Neural Networks (CNNs) to learn hierarchical representations of microstructure images, aiming to improve prediction accuracy and provide insights into the governing microstructural mechanisms.

The research is motivated by the need for accelerated materials design and the reduction of reliance on expensive and time-consuming physical testing. By establishing a robust predictive model, we aim to facilitate the rapid screening of alloy compositions and processing routes.

## Methodology

### Data Generation and Acquisition
To ensure reproducibility and controlled experimental conditions, this study utilizes a synthetic microstructure generator (`code/data/synthetic_gen.py`) to produce a dataset of at least 2,000 images. Each image is paired with a physics-informed $K_{IC}$ value derived from established micromechanical models.

{{claim:c_78eec61d}} (Wikidata Q16883818, https://www.wikidata.org/wiki/Q16883818). Crucially, the generation process embeds metadata including:
* **Magnification**: The scale of the image.
* **Resolution ($\mu m$/pixel)**: The physical resolution of the simulated imaging system.
* **Preparation Protocol**: Flags indicating simulated SEM or TEM preparation methods.

### Preprocessing Pipeline
Raw images undergo a standardized preprocessing pipeline (`code/data/preprocess.py`) to ensure uniformity:
1. **Grayscale Conversion**: All images are converted to single-channel grayscale.
2. **Resolution Normalization**: Images are resized to a fixed dimension of 128x128 pixels.
3. **Normalization**: Pixel intensities are normalized to the range [0, 1].
4. **Validation**: A strict validation step checks for missing metadata fields ($K_{IC}$, resolution, protocol) and excludes samples that do not meet the minimum resolution criteria defined in the Resolution Limits section.

### Model Architecture and Training
The primary model is a lightweight 3-block CNN (`code/models/cnn.py`) consisting of Convolution-ReLU-BatchNorm-MaxPool layers, designed to run efficiently on CPU-only infrastructure. The model is trained to regress $K_{IC}$ values.

Baseline comparisons are established using hand-crafted texture features (GLCM, power spectra) fed into Linear Regression and Random Forest models (`code/models/baselines.py`).

### Statistical Validation
To address concerns regarding statistical significance, a Permutation Test is employed to compare the performance of the CNN against baseline models. Additionally, bootstrap confidence intervals are calculated for all feature extraction metrics to quantify uncertainty.

## Resolution Limits

The validity of microstructure-based predictions is inherently constrained by the spatial resolution of the input images. This section defines the minimum resolvable feature size for the dataset and the implications for model generalization.

### Minimum Resolvable Feature Size
The synthetic generator simulates a range of resolutions. Based on the Nyquist-Shannon sampling theorem, the minimum resolvable feature size ($d_{min}$) is approximately twice the pixel resolution ($r$):
$$ d_{min} \approx 2 \times r $$

The dataset includes images with resolutions ranging from 0.1 $\mu m$/pixel to 0.5 $\mu m$/pixel. Consequently, the minimum resolvable feature size in the dataset ranges from 0.2 $\mu m$ to 1.0 $\mu m$. Features smaller than this threshold (e.g., nanoscale precipitates in certain aluminum alloys) are not explicitly resolved in the input images and must be inferred from their statistical influence on the surrounding matrix or are considered out-of-distribution for the model.

### Impact on Prediction Accuracy
The preprocessing pipeline (`code/data/preprocess.py`) includes a resolution limit check. Samples where the effective resolution is insufficient to resolve critical microstructural features (e.g., grain boundaries smaller than 2 pixels) are flagged and excluded from the training set. This ensures that the model is not trained on data where the signal-to-noise ratio is too low to support reliable learning.

The `research.md` artifact will be updated in Phase 6 (Task T037) with specific quantitative analysis of the generated `resolution_um` values to refine these limits based on the actual distribution of the synthetic dataset.

## Results

*Note: This section is a placeholder for the results to be generated upon execution of the training and evaluation pipelines (Tasks T023b, T024, T025b).*

Upon completion of the training phase, this section will report:
1. **Performance Metrics**: $R^2$, MAE, and RMSE for the CNN, Linear Regression, and Random Forest models.
2. **Statistical Significance**: Results of the Permutation Test comparing CNN performance against baselines.
3. **Feature Attribution**: Qualitative and quantitative analysis of Grad-CAM heatmaps indicating which microstructural regions drive the predictions.
4. **Stability Analysis**: Intersection over Union (IoU) scores for heatmaps under augmented views, validating the robustness of the attribution.

Preliminary expectations suggest that the CNN will outperform hand-crafted feature baselines by capturing non-linear interactions between grain morphology and precipitate distribution that are difficult to encode manually.

## Discussion

### Interpretation of Model Behavior
The use of Grad-CAM (Task T042) allows for the visualization of the specific microstructural features the model attends to when predicting $K_{IC}$. We anticipate the model will focus on grain boundary networks and the spatial distribution of precipitates, consistent with established fracture mechanics theories.

### Limitations and Future Work
The reliance on synthetic data is a primary limitation. While the synthetic generator incorporates physics-informed rules, it may not capture the full complexity of real-world microstructural defects (e.g., inclusions, porosity). Future work will focus on validating the model against real experimental datasets from public repositories or collaborative labs.

### Reproducibility
To ensure reproducibility, all random seeds for data splitting and model initialization are managed via `code/utils/config.py` (seed 42 for splits). The full pipeline, including data generation, preprocessing, training, and evaluation, is designed to run within 6 hours on a standard 2-core CPU, adhering to the project's computational constraints.

### Response to Reviewer Concerns
This protocol explicitly addresses the concerns raised regarding experimental specification. We have defined the imaging resolution constraints, specified the sample preparation protocols (simulated SEM/TEM), and implemented statistical confidence intervals (bootstrap) for feature extraction. These measures ensure that the derived conclusions are robust and scientifically rigorous.