# Research: The Impact of Visual Search Strategies on Attentional Capture by Emotional Faces

## Overview

This research phase investigates the feasibility of analyzing visual search strategies (global vs. local) in emotional face detection using publicly available eye-tracking datasets. The primary goal is to identify suitable datasets, validate variable availability, and outline the statistical methodology for addressing the research question.

## Verified Datasets

> **Note**: Only datasets listed in the "# Verified datasets" block of the user message may be cited. If a dataset lacks a verified source, it is described by name but no URL is fabricated.

| Dataset Name | Description | Verified URL | Status |
|--------------|-------------|--------------|--------|
| [No specific dataset found yet] | Search ongoing for eye-tracking datasets with face stimuli. | N/A | **Searching** |

**Dataset Strategy**:  
The project will search HuggingFace Datasets for datasets containing 'eye-tracking', 'face', and 'emotion' keywords.
- **Primary Goal**: Find a dataset with pre-defined `roi_annotations` for eye and mouth regions.
- **Fallback Strategy**: If no dataset with pre-defined ROIs is found, the pipeline will apply a **Generic ROI Fallback**: splitting the face image into a 3x3 grid and defining 'eye' as the top-center and 'mouth' as the bottom-center regions. This allows the analysis to proceed with real human data rather than synthetic data.
- **Critical Variable Check**: If a dataset lacks `gaze_coordinates`, `response_times`, `emotion_labels`, or `roi_annotations` (or the ability to derive ROIs), the pipeline will HALT and log a specific error (FR-009).

**Fallback Plan**:  
If no dataset with complete variables is available, the project will **not** proceed with synthetic data for the primary analysis, as this would invalidate the research question regarding 'attentional capture by emotional faces' in real human subjects. Instead, the project will document the data unavailability as a primary limitation and pivot to a methodological validation study using a small, publicly available subset of data to demonstrate the pipeline logic.

## Methodology

### Data Acquisition
- **Source**: HuggingFace Datasets (`datasets.load_dataset()`).
- **Validation**: Check for non-null `gaze_coordinates` and `response_times` (FR-001).
- **Retry Logic**: Exponential backoff (1s, 2s, 4s) for network failures (FR-002).

### Feature Extraction
- **Metrics**: Fixation duration (eye vs. mouth), saccade amplitude, dispersion (FR-003).
- **ROI Handling**: If `roi_annotations` are missing, use **Generic ROI Fallback** (3x3 grid split).
- **Collinearity Check**: Calculate VIF for predictor pairs; flag if VIF ≥5 (FR-005).

### Strategy Classification
- **Clustering**: k-means (k=2) on fixation distribution features (FR-004).
- **Validity**: Silhouette score ≥0.25 required; if lower, log warning and use descriptive stats.
- **Sensitivity**: Sweep k∈{2,3} to assess robustness (FR-010).
- **Stability Check**: Bootstrap clustering on 100 samples to assess label stability (replaces invalid k-fold CV).

### Statistical Analysis
- **Primary Model**: Linear Mixed-Effects Model (LMM) with detection time as outcome, **continuous fixation ratio** (eye/mouth) as fixed effect, participant as random intercept (FR-006).
- **Secondary Model**: LMM with cluster label as fixed effect (exploratory only).
- **Non-triviality Check**: Permutation test (1000 iterations) to ensure association is not due to chance.
- **Convergence**: Max 500 iterations; fallback to simpler linear model if failed.
- **Multiplicity**: Bonferroni or Benjamini-Hochberg correction for >1 test (FR-007).
- **Power Analysis**: **A priori** sample size estimation based on literature effect sizes; post-hoc power for actual sample size (FR-008).

## Causal Inference Limitations

- **Observational Nature**: No random assignment of processing strategy; findings are **associational**.
- **Reframed Question**: The research question is explicitly "What is the association between visual search strategies and attentional capture?" rather than "What is the impact?".
- **Causal Claims**: All claims in the final paper must be limited to correlation. Any 'impact' language must be removed or heavily qualified.

## Assumptions & Limitations

- **Dataset Availability**: If ROI data is missing, Generic ROI Fallback is used.
- **Computational Constraints**: All methods must run on CPU-only, 7GB RAM environment.
- **Instrument Validation**: Assumes eye-tracking instruments in source datasets are validated; if not, this is documented.
- **Circularity**: Addressed by using continuous predictor and permutation testing.

## Decision Rationale

- **CPU-Only Methods**: Chosen to ensure compatibility with GitHub Actions free-tier.
- **Continuous Predictor**: Chosen to avoid circularity of using derived cluster labels as predictors.
- **Generic ROI Fallback**: Chosen to allow analysis of real human data even if pre-defined ROIs are missing.
- **Bootstrap Stability**: Chosen over k-fold CV for unsupervised clustering to avoid invalid label prediction.
- **Permutation Test**: Chosen to ensure non-triviality of results.

## References

> Citations will be validated by the Reference-Validator Agent. Title overlap ≥0.7 required.

- HuggingFace Datasets Documentation.
- Statsmodels Documentation for LMM.
- Scikit-learn Documentation for Clustering and Diagnostics.
- Literature on visual search strategies and effect sizes (for a priori power analysis).