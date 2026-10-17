# Quickstart: Assessing Uncertainty Quantification Techniques

## Runnable Command

To run the thin end-to-end analysis (using a small subset of data for verification), execute:

```bash
python -m code.main --thin
```

## Pipeline Overview

This pipeline evaluates and compares four Uncertainty Quantification (UQ) methods for materials property prediction:
1. **Gaussian Process Regression (GPR)**: Provides Bayesian uncertainty estimates.
2. **Monte-Carlo Dropout (MC-Dropout)**: Approximates Bayesian inference via stochastic forward passes.
3. **Deep Ensemble**: Aggregates predictions from multiple independently initialized models.
4. **Split-Conformal Prediction**: Provides distribution-free coverage guarantees using a calibration set.

### Key Constraints and Rules
- **Training Cap**: To ensure computational efficiency and fair comparison, training is capped at **[deferred] samples** per method per dataset.
- **Deterministic Sampling**: To guarantee reproducibility, the pipeline employs a "first-N rows" sampling rule using a fixed random seed (**seed 42**).
- **Statistical Rigor**: Method comparisons are performed using the **paired Wilcoxon signed-rank test**. This test is used because predictions for different UQ methods are paired on the same test samples, allowing for a rigorous assessment of whether one method consistently outperforms another in calibration or sharpness.
- **Property Proxy**: Due to the unavailability of a public, programmatically accessible Elastic Modulus dataset, **Formation Energy** (from OQMD) is used as a proxy. All conclusions regarding mechanical stiffness are qualified as qualitative.

## Expected Outputs

The pipeline generates the following primary artifacts:
- `data/results/per_sample_errors.csv`: Detailed predictions, bounds, and errors for every sample, conforming to the contract in `specs/001-assessing-uncertainty-quantification-tec/contracts/per_sample_errors.schema.yaml`.
- `data/results/pipeline_run.json`: Execution log documenting the run status and resource usage.
