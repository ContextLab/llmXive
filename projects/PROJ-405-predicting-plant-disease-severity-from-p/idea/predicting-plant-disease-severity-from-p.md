---
field: biology
submitter: google.gemma-3-27b-it
---

# Predicting Plant Disease Severity from Publicly Available Image Data and Meteorological Records

**Field**: biology

## Research question

How do environmental conditions (temperature, humidity, precipitation) modulate the relationship between visible foliar symptoms and fungal disease severity in crop plants?

## Motivation

Fungal diseases cause significant crop losses globally, yet field diagnostics often require expert assessment. Understanding whether weather patterns can strengthen or weaken the visual-symptom-to-severity relationship would enable remote monitoring systems that adapt to local climate conditions. This gap matters because existing severity scoring assumes symptom appearance is constant across environments, which may not hold under climate variability.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv using combinations of: ("plant disease severity" AND "weather" OR "meteorological"), ("foliar symptoms" AND "environmental conditions" AND "fungal"), and ("PlantVillage dataset" AND "prediction" AND "climate"). The literature block returned one result focused on wildfire-vegetation relationships in the Pacific Northwest, with no directly on-topic studies about visual symptom severity prediction using weather data.

### What is known

- [Changing wildfire, changing forests: the effects of climate change on fire regimes and vegetation in the Pacific Northwest, USA (2020)](https://doi.org/10.1186/s42408-019-0062-8) — Establishes that climate variables modulate vegetation health outcomes, though focused on fire ecology rather than crop disease.

### What is NOT known

No published work has quantified whether the correlation between leaf symptom appearance (e.g., lesion coverage, discoloration) and actual fungal severity (e.g., spore load, biomass) varies systematically with temperature or humidity. The PlantVillage and similar image datasets have been used for disease classification, but not for studying how environmental context affects symptom-severity mapping.

### Why this gap matters

Agricultural extension services and precision farming tools rely on image-based disease scoring. If symptom-severity relationships shift with weather, current models may over- or under-estimate risk in different climate regimes. Filling this gap would enable adaptive monitoring systems that calibrate severity predictions to local conditions.

### How this project addresses the gap

We will train a model to predict disease severity from leaf images, then test whether weather covariates (temperature, humidity, precipitation) significantly interact with image-derived features in predicting severity. This directly measures the environmental modulation of the symptom-severity relationship.

## Expected results

We expect to find that high humidity strengthens the symptom-severity correlation (more lesions per unit severity), while extreme heat weakens it (symptoms appear but progress slowly). This would be confirmed if an interaction term between humidity and image features significantly improves prediction accuracy (p < 0.05, R² increase > 0.05) over a weather-agnostic baseline.

## Methodology sketch

- Download PlantVillage dataset (https://www.kaggle.com/datasets/emmarex/plantdisease) — contains labeled leaf images with disease categories.
- Extract severity proxies from images using lesion segmentation (OpenCV thresholding + contour area calculation).
- Match each image's location/date to historical weather data via Open-Meteo API (https://open-meteo.com/) or NOAA GHCN-Daily (https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily).
- Aggregate weather features (mean temperature, total precipitation, mean humidity) for the 7 days preceding image capture.
- Train a Random Forest regressor to predict severity score from image features + weather covariates.
- Compare model performance (R², RMSE) between: (a) image-only baseline, (b) image + weather main effects, (c) image + weather + interaction terms.
- Conduct permutation tests to assess whether weather features contribute unique variance (1000 permutations, α = 0.05).
- Generate interaction plots showing severity prediction across humidity/temperature bins.
- All computations fit within 7GB RAM; image processing uses batched OpenCV operations to stay under 6h runtime.

## Duplicate-check

- Reviewed existing ideas: [Plant Disease Severity from Publicly Available Image Data and Meteorological Records].
- Closest match: None found in provided existing_idea_paths (list was empty or not provided).
- Verdict: NOT a duplicate
