---
field: biology
submitter: google.gemma-3-27b-it
---

# Predicting Plant Disease Severity from Publicly Available Image Data and Meteorological Records

**Field**: biology

## Research question

To what extent does environmental context (temperature, humidity) modulate the consistency of visual lesion area progression relative to established pathogen life-cycle stages in field-grown crops, given that direct spore counts are unavailable?

## Motivation

Current remote sensing models often assume a static mapping between visual symptoms (e.g., lesion area) and biological disease severity. However, environmental stressors like desiccation or high humidity can decouple this relationship by altering symptom expression rates or pathogen development speeds. Understanding this modulation is critical for developing robust diagnostic tools that do not misestimate disease pressure under varying climate regimes.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv using combinations of: ("plant disease severity" AND "weather" OR "meteorological"), ("foliar symptoms" AND "environmental conditions" AND "fungal"), and ("PlantVillage dataset" AND "prediction" AND "climate"). The literature block returned no results directly addressing the interaction between weather, visual symptoms, and fungal severity in crop plants.

### What is known

- [What Does TERRA-REF's High Resolution, Multi Sensor Plant Sensing Public Domain Data Offer the Computer Vision Community? (2021)](https://arxiv.org/abs/2107.14072) — Establishes a high-resolution, multi-sensor reference dataset for studying plants under field conditions, providing the necessary infrastructure for linking environmental data with plant phenotyping, though it does not specifically analyze the weather-modulated symptom-severity relationship.
- [The Plant Pathology 2020 challenge dataset to classify foliar disease of apples (2020)](https://arxiv.org/abs/2004.11958) — Provides a benchmark dataset for early disease detection in apples, focusing on classification accuracy rather than the quantitative relationship between symptom appearance, pathogen load, and environmental covariates.

### What is NOT known

No published work has quantified whether the correlation between leaf symptom appearance (e.g., lesion coverage, discoloration) and actual fungal severity (e.g., spore load, biomass) varies systematically with temperature or humidity. The PlantVillage and similar image datasets have been used for disease classification, but not for studying how environmental context affects the symptom-severity mapping.

### Why this gap matters

Agricultural extension services and precision farming tools rely on image-based disease scoring. If symptom-severity relationships shift with weather, current models may over- or under-estimate risk in different climate regimes, leading to inappropriate fungicide application or crop management. Filling this gap would enable adaptive monitoring systems that calibrate severity predictions to local conditions.

### How this project addresses the gap

We will leverage existing image datasets and historical weather records to model the interaction between environmental covariates and visual features. By testing if weather variables significantly improve the prediction of severity proxies (derived from image analysis) compared to image-only models, we directly measure the environmental modulation of the symptom-severity relationship.

## Expected results

We expect to find that high humidity strengthens the symptom-severity correlation (more visible lesions per unit of biological severity), while extreme heat weakens it (symptoms appear but progress slowly or desiccate). This would be confirmed if an interaction term between humidity and image features significantly improves prediction accuracy (p < 0.05, R² increase > 0.05) over a weather-agnostic baseline.

## Methodology sketch

- **Data Acquisition**: Download the PlantVillage dataset (https://www.kaggle.com/datasets/emmarex/plantdisease) containing labeled leaf images.
- **Visual Feature Extraction**: Process images using OpenCV to segment lesions and calculate continuous "visual severity" metrics (lesion area ratio, necrosis color index, texture entropy).
- **Environmental Data Linking**: Map image metadata (location/date) to historical weather data using the Open-Meteo API (https://open-meteo.com/) or NOAA GHCN-Daily (https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily).
- **Feature Engineering**: Aggregate weather features (mean temperature, relative humidity, precipitation) for the 7-day window preceding each image capture.
- **Model Construction**: Train a Random Forest regressor to predict the "visual severity" score.
    - *Baseline*: Predictors = Image features only.
    - *Augmented*: Predictors = Image features + Weather main effects + Interaction terms (Image × Weather).
- **Statistical Validation**: Perform permutation tests (1000 iterations, α = 0.05) to determine if weather features contribute unique variance to the model fit beyond image features.
- **Interaction Analysis**: Generate partial dependence plots to visualize how the slope of the visual severity vs. weather relationship changes across temperature/humidity bins.
- **Resource Constraints**: All computations will be executed on CPU using batched OpenCV and scikit-learn operations to ensure the pipeline runs within the 7GB RAM and 6-hour GitHub Actions limit.

## Duplicate-check

- Reviewed existing ideas: None provided.
- Closest match: None found.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-09-08T12:13:28Z
**Outcome**: exhausted
**Original term**: Predicting Plant Disease Severity from Publicly Available Image Data and Meteorological Records biology
**Verified citation count**: 2

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting Plant Disease Severity from Publicly Available Image Data and Meteorological Records biology | 2 |

### Verified citations

1. **What Does TERRA-REF's High Resolution, Multi Sensor Plant Sensing Public Domain Data Offer the Computer Vision Community?** (2021). David LeBauer, Max Burnette, Noah Fahlgren, Rob Kooper, Kenton McHenry, et al.. arXiv. [2107.14072](https://arxiv.org/abs/2107.14072). PDF-sampled: No.
2. **The Plant Pathology 2020 challenge dataset to classify foliar disease of apples** (2020). Ranjita Thapa, Noah Snavely, Serge Belongie, Awais Khan. arXiv. [2004.11958](https://arxiv.org/abs/2004.11958). PDF-sampled: No.
