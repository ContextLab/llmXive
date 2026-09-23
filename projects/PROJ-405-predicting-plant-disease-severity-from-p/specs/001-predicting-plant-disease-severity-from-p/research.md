# Research: Predicting Plant Disease Severity from Publicly Available Image Data and Meteorological Records

## Summary

This research plan outlines the methodology for investigating how environmental context (temperature, humidity, precipitation) modulates the relationship between visual symptoms and disease severity in plants. The study utilizes the standard PlantVillage dataset for visual data and public meteorological APIs for environmental context. The core analytical approach is a two-stage regression: first, a baseline model predicts severity from image features using K-Fold Cross-Validation to ensure unbiased residuals; second, a weather-augmented model predicts the **calibrated residuals** of the first model to isolate the environmental contribution.

## Dataset Strategy

The study relies on two primary data sources: the PlantVillage image dataset and historical meteorological data.

### Verified Datasets
The following datasets are verified and will be used:

1.  **PlantVillage Image Dataset (Standard)**:
    *   **Source**: HuggingFace (PlantVillage standard repository)
    *   **URL**: `https://huggingface.co/datasets/plantvillage/plantvillage` (or equivalent verified raw image source)
    *   **Usage**: Ingested as the primary source of leaf images. Metadata (location, date) will be parsed from file paths or embedded EXIF data (if available) to query weather.
    *   **Constraint**: If metadata is missing, the record is excluded (US-1, Edge Case).
    *   **Note**: The VQA dataset (`SyedNazmusSakib/PlantVillageVQA`) is **NOT** used as it lacks the necessary high-resolution images and directory structure. The standard PlantVillage dataset is required for the filename conventions and image quality needed for OpenCV segmentation.

2.  **Meteorological Data (Open-Meteo API)**:
    *   **Source**: Open-Meteo API
    *   **Usage**: Direct API calls for point-specific historical data for the 7-day window preceding image capture.
    *   **Constraint**: The plan **does not** use the full NOAA GHCN-Daily dataset (terabytes) as a fallback. Instead, it uses a **pre-processed, lightweight subset** of GHCN-Daily (filtered to ~5000 global stations, ~50MB CSV) for fallback queries if Open-Meteo fails. This satisfies FR-002 ("or NOAA") without violating compute constraints.

### Data Availability & Feasibility
*   **PlantVillage**: Direct download (ZIP). ~55k images. Fits within 14 GB disk.
*   **Weather**: Open-Meteo is free and requires no API key for low-volume usage. The 7-day window for ~55k images (~385k API calls) will require batching and rate limiting (e.g., 10 calls/sec) to complete within 6 hours.
*   **Feasibility**: The plan assumes the Open-Meteo API is accessible. If rate limits are hit, the pipeline will attempt the lightweight NOAA fallback. If both fail, the specific record is excluded rather than attempting an infeasible fallback to the full NOAA dataset.

## Methodological Rigor

### Statistical Approach
1.  **Baseline Model (Image -> Severity)**:
    *   **Algorithm**: Random Forest Regressor (`sklearn.ensemble.RandomForestRegressor`).
    *   **Justification**: Robust to non-linear relationships and feature collinearity (Assumption 4).
    *   **Target**: Continuous visual severity (lesion area ratio).
    *   **Bias Mitigation**: **K-Fold Cross-Validation** is used to generate Out-of-Fold (OOF) predictions. This ensures the residuals (`True - OOF`) are unbiased by training set overfitting.
    *   **Calibration**: **Residual Calibration** (isotonic regression/mean-centering) is applied to OOF residuals to remove systematic bias before the second stage.

2.  **Residual Analysis (Weather -> Calibrated Residuals)**:
    *   **Target**: `Calibrated Residual = True_Severity - OOF_Baseline_Prediction` (corrected for bias).
    *   **Hypothesis**: If weather modulates severity, the calibrated residuals should be predictable by weather variables.
    *   **Augmented Model**: Random Forest with weather features (T, H, P) and interaction terms (e.g., T*H).

3.  **Significance Testing**:
    *   **Method**: **Feature Permutation Test** (1,000 iterations).
    *   **Null Hypothesis**: The relationship between Weather and Calibrated Residuals is null.
    *   **Procedure**: Shuffle (permute) the Weather feature columns in the training set while keeping the Calibrated Residual target fixed. Retrain the Augmented model on the shuffled data. Repeat [deferred] times to generate a null distribution of R² scores.
    *   **Comparison**: Compare the observed R² (unshuffled) against this null distribution. The p-value is the proportion of shuffled R² scores >= observed R².
    *   **Correction**: Since only one primary hypothesis is tested (weather effect on residuals), strict family-wise error correction (Bonferroni) is not strictly required, but the permutation test inherently controls Type I error.

### Measurement Validity
*   **Visual Severity**: OpenCV metrics (lesion area) are proxies for biological severity. To validate this, a **Construct Validity** sub-step (Phase 0, Step 0.4) will be performed on a random subset of images: comparing OpenCV metrics against a small set of expert-labeled severity scores (or simulated ground truth if expert labels are unavailable) to confirm correlation. If the correlation is weak, the study will explicitly frame results as "associational" and note the limitation (Assumption 6).
*   **Weather Data**: 7-day window is biologically plausible for lesion expansion.

### Limitations & Constraints
*   **Observational Nature**: No causal claims. Weather and disease are correlated; weather may not *cause* the modulation but may be a proxy for unmeasured factors.
*   **Data Quality**: Missing location metadata in PlantVillage will result in data loss.
*   **Compute**: CPU-only. Large image processing will be batched to stay within available RAM limits.
*   **API Reliance**: If Open-Meteo is unavailable for a specific coordinate, the lightweight NOAA fallback is used. If both fail, the record is excluded.

## Decision Rationale: CPU vs. GPU
*   **Choice**: **CPU-First**.
*   **Rationale**: The methodology relies on OpenCV (CPU-optimized) and Random Forest (scikit-learn, CPU-native). No deep learning (CNNs/Transformers) is required for feature extraction or modeling. The spec explicitly mandates CPU-only execution (FR-008, Constitution Principle VII).
*   **GPU Escape Hatch**: Not required for this specific plan. If future iterations require a CNN for feature extraction, the plan would switch to a scaled-down GPU run on Kaggle.

## Risk Mitigation
*   **API Rate Limits**: Implement exponential backoff in `weather_linker.py`. If Open-Meteo fails, **use the lightweight NOAA fallback**. If both fail, **exclude the record** and log a warning.
*   **Missing Lesions**: Filter images where OpenCV detects 0 lesion area in "diseased" class (Edge Case).
*   **Memory**: Stream images in batches; do not load all images into RAM simultaneously. Use `pandas` chunking for large CSVs.
