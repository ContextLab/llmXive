# Research: Assessing Uncertainty Quantification Techniques for Machine‑Learning Predicted Material Properties

## Dataset Strategy

The primary dataset is the OQMD subset hosted on Hugging Face ([https://huggingface.co/datasets/OQMD/OQMD-Subset](https://huggingface.co/datasets/OQMD/OQMD-Subset)). This dataset provides compositional and structural features along with target material properties (formation energy, bulk modulus, band gap).  Data will be downloaded and preprocessed to handle missing values and ensure compatibility with the baseline model. Specifically, rows with missing critical features will be excluded, and a validation report will be generated logging the excluded samples.

## Decision/Rationale

All methods are planned for CPU-first execution due to the resource constraints of the GitHub Actions runner. The baseline neural network and Deep Ensembles are well-suited for CPU training and inference. Monte-Carlo Dropout adds minimal overhead and can also run efficiently on CPU. Sparse Gaussian Process will leverage PCA for dimensionality reduction to mitigate the computational cost on CPU. No methods require a GPU.

## Uncertainty Quantification Techniques

*   **Deep Ensembles:** Training multiple independent models and averaging their predictions provides a robust estimate of uncertainty.
*   **Monte-Carlo Dropout:** Applying dropout during inference generates multiple stochastic predictions, allowing for uncertainty estimation.
*   **Sparse Gaussian Process:** Using a sparse approximation of the Gaussian Process kernel allows for scalable uncertainty estimation.

## Evaluation Metrics

*   **Expected Calibration Error (ECE):** Measures the difference between predicted confidence and empirical accuracy.
*   **Proper Interval Scores:** Evaluate the sharpness and calibration of prediction intervals.
*   **Reliability Diagrams:** Visualize the relationship between predicted confidence and empirical accuracy.
*   **Precision/Recall:** Assesses the performance of UQ-based screening in a downstream task.

## Dataset Variables

The following variables are required:

*   **Predictors:** Compositional features (element fractions), structural descriptors (atomic radius, packing fraction)
*   **Outcomes:** Formation energy, bulk modulus, band gap
*   **Covariates:** None explicitly planned, but stratification will be based on property quantiles.

## References

*   OQMD Dataset: [https://huggingface.co/datasets/OQMD/OQMD-Subset](https://huggingface.co/datasets/OQMD/OQMD-Subset)
*   Hugging Face Datasets library: [https://huggingface.co/docs/datasets/](https://huggingface.co/docs/datasets/)
