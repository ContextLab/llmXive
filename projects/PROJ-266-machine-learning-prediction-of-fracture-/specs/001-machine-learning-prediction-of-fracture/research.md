# Research: Machine Learning Prediction of Fracture Toughness from Microstructure Images

## Introduction
This research investigates whether microstructural images of metallic alloys (steel, aluminum, titanium) contain sufficient predictive signal to estimate fracture toughness ($K_{IC}$) using deep learning. The study compares a lightweight Convolutional Neural Network (CNN) against traditional machine learning baselines (Linear Regression, Random Forest) trained on handcrafted texture features. 

**Scope Definition**: Due to the absence of an open, verified real-world dataset for metallic alloy fracture toughness in the provided "Verified datasets" block, this study **pivots to a Synthetic Microstructure Generator**. The primary goal is **Methodological Validation**: to determine if the pipeline can successfully learn complex structure-property relationships when ground truth is known, and to validate the stability of feature attribution (Grad-CAM) on synthetic data. The results are framed as a validation of the *pipeline's capability*, not as definitive claims about real-world material physics.

## Methodology

### Data Strategy
The project relies on a **Synthetic Microstructure Generator** that creates realistic 128x128 grayscale images of simulated grain structures and assigns $K_{IC}$ values based on a deterministic, non-linear function of grain size, phase distribution, and topological connectivity.
- **Generator Logic**: The generator simulates grain boundaries and precipitates using Voronoi tessellation. The target $K_{IC}$ is calculated using a modified Hall-Petch relation that includes a non-linear term for grain boundary connectivity (a feature not directly captured by simple GLCM). This ensures the CNN must learn complex patterns, preventing trivial baseline solutions.
- **Alloy Family Assignment**: Synthetic images are assigned alloy families (steel, Al, Ti) via random assignment with a fixed seed to ensure stratification. The distribution is set to be equal across families (e.g., [deferred] each) to satisfy FR-002.
- **Sample Size**: The generator targets $\ge$ [deferred] images to ensure statistical power for the Wilcoxon test.

**Critical Gap Identification**:
The spec assumes the existence of a "Metallurgical Microstructure–Fracture Toughness" dataset from the "Materials Data Facility." However, the **Verified datasets** block provided for this project contains NO valid sources for metallic alloy fracture data.
- The listed SEM URLs are for: Mathematical answer generation (SEMEVAL), Brain tumor segmentation, and AI vs Real image detection.
- The listed TEM URLs are for: Turkish text (OSCAR), Polish text (AEZAKMI), and Temporal language modeling.

**Resolution Strategy**:
Per the "Data availability" rules, a plan using access-gated or non-existent data is a fatal flaw. Since no open, verified source for *metallic alloy fracture toughness* exists in the provided list, and the spec's assumed dataset is not in the verified list:
1.  The implementation **cannot** proceed with the specific "Metallurgical Microstructure–Fracture Toughness" dataset as originally assumed.
2.  The plan adopts a **Synthetic Microstructure Generator** approach. This ensures the data is obtainable, the ground truth is known, and the pipeline is fully reproducible on the CI runner.
3.  The research question is reframed to "Methodological Validation of the Prediction Pipeline" rather than "Predicting Real-World Fracture Toughness."

**Limitations of Synthetic Data**:
The synthetic data lacks the complex, non-linear microstructural defects (voids, inclusions, complex grain boundaries) that actually drive fracture toughness variance in real materials. A model trained on this data cannot validate the predictive power of *real* imaging data. The relationship between microstructure and K_IC in real materials is non-linear, history-dependent, and influenced by factors (e.g., residual stress, inclusion morphology) not captured by simple grain-size functions. Therefore, the results do not demonstrate generalizability to real-world fracture mechanics; they only validate the pipeline's mathematical capacity to learn the programmed mapping.

### Model Architecture
- **CNN**: 3-block architecture (Conv-ReLU-BatchNorm-MaxPool) followed by FC layers (256 → 64 → 1). Input: 128x128 grayscale.
- **Baselines**:
    - Linear Regression on GLCM (Gray-Level Co-occurrence Matrix) features.
    - RandomForestRegressor on GLCM and Band-pass filtered power spectrum features.
- **Training**: 5 independent runs with different random seeds. Loss: Mean Squared Error (MSE). Optimizer: Adam.

### Statistical Analysis
- **Primary Metric**: Mean Absolute Error (MAE) and $R^2$.
- **Significance Test**: Wilcoxon signed-rank test (α = 0.05) on the distribution of MAE differences between CNN and baselines across the 5 runs. 
    - **Null Hypothesis**: There is no difference in optimization stability between the CNN and baselines on the synthetic data.
    - **Interpretation**: The test measures the stability of the optimizer on a fixed synthetic distribution, not the statistical significance of the model's predictive power against a null hypothesis of 'no signal' in real data. A permutation test against shuffled labels will be performed to establish a baseline for random chance.
- **Attribution Stability**: Grad-CAM heatmaps generated for 10+ test images. IoU calculated between heatmaps of multiple augmented views of the same image.
    - **Validation**: Heatmaps will be overlaid on the known ground-truth grain boundary masks to verify alignment with "physically meaningful" features in the synthetic context. In the synthetic domain, "physically meaningful" features are defined as the generated grain boundaries and precipitates. The stability metric validates that the CNN focuses on these structures rather than noise.

## Resolution Limits
- **Image Resolution**: Fixed at 128x128 pixels. This is a trade-off between computational feasibility on CPU and the ability to resolve fine microstructural details (precipitates). As noted in the verified facts, 128px is the default configuration (`2603.25384`).
- **Sample Size**: The synthetic generator will target an effective sample size of $\ge$ [deferred] images to ensure statistical power for the Wilcoxon test.
- **Domain Generalization**: The synthetic data approach limits physical generalizability to real-world alloys. The study will explicitly frame results as "methodological validation" of the pipeline rather than definitive material science claims. The results validate the *pipeline's ability to learn structure-property relationships* when ground truth is known, not as a claim about real-world fracture mechanics.

## Results
*Results are deferred to the implementation phase. The plan ensures that when run, the system will output:*
- R², MAE, RMSE for CNN, Linear Regression, and Random Forest.
- Wilcoxon test statistic and p-value.
- Mean IoU score for Grad-CAM stability.
- Heatmap images for test samples.

## Discussion
The study will evaluate whether the CNN learns features that are stable (high IoU) and predictive (low MAE) compared to handcrafted features. If the CNN outperforms baselines with statistical significance, it suggests that deep learning can capture complex microstructural patterns (e.g., grain boundary networks) that simple texture metrics miss. The use of synthetic data ensures reproducibility but requires careful validation that the synthetic images resemble real microstructures (e.g., via visual inspection of generated samples). The strict CPU constraint ensures the pipeline is accessible to all researchers without GPU hardware.

The results will be interpreted as a validation of the *pipeline's ability to learn structure-property relationships* when ground truth is known, not as a claim about real-world fracture mechanics. The claim "imaging data explains variance" is tautological for synthetic data, as the variance was programmed in. Therefore, the success criteria (SC-001, SC-002) are reinterpreted as validating the *pipeline's ability* to detect the programmed signal, not the signal's existence in real materials. The comparison between the CNN and baselines is a test of the CNN's capacity to learn complex non-linearities beyond simple texture metrics, given that the synthetic K_IC is a function of grain size (which GLCM measures). If the baseline models outperform or match the CNN, it indicates that the synthetic mapping is simple enough for traditional methods, or that the CNN is overfitting the generator's specific noise.

The results are framed as a validation of the pipeline's capability, not as definitive claims about real-world material physics. The synthetic data lacks the complex, non-linear microstructural defects that actually drive fracture toughness variance in real materials. Therefore, the results do not demonstrate generalizability to real-world fracture mechanics.