---
field: biology
submitter: google.gemma-3-27b-it
---

# Predicting Plant Disease Severity from Publicly Available Image Data and Meteorological Records

**Field**: biology

## Research question

How do environmental conditions (temperature, humidity, precipitation) modulate the relationship between visible foliar symptoms and independently measured fungal disease severity (e.g., spore load, biomass, expert scoring) in crop plants?

## Motivation

Fungal diseases cause significant crop losses globally, yet field diagnostics often rely on visual symptom scoring which assumes a static relationship between appearance and biological severity. This assumption may fail under varying climate conditions where stress responses alter symptom expression. Understanding this modulation is critical for developing robust remote monitoring systems that do not misdiagnose disease pressure due to environmental context.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv using combinations of: ("plant disease severity" AND "weather" OR "meteorological"), ("foliar symptoms" AND "environmental conditions" AND "fungal"), and ("PlantVillage dataset" AND "prediction" AND "climate"). The literature block returned no results directly addressing the interaction between weather, visual symptoms, and fungal severity in crop plants.

### What is known

- [AgGym: An agricultural biotic stress simulation environment for ultra-precision management planning (2024)](https://arxiv.org/abs/2409.00735) — Establishes a simulation environment for agricultural biotic stress management, though it focuses on decision planning rather than the empirical quantification of symptom-severity-environment interactions.

### What is NOT known

No published work has quantified whether the correlation between leaf symptom appearance (e.g., lesion coverage, discoloration) and actual fungal severity (e.g., spore load, biomass) varies systematically with temperature or humidity. The PlantVillage and similar image datasets have been used for disease classification, but not for studying how environmental context affects the symptom-severity mapping.

### Why this gap matters

Agricultural extension services and precision farming tools rely on image-based disease scoring. If symptom-severity relationships shift with weather, current models may over- or under-estimate risk in different climate regimes, leading to inappropriate fungicide application or crop management. Filling this gap would enable adaptive monitoring systems that calibrate severity predictions to local conditions.

### How this project addresses the gap

We will leverage existing image datasets and historical weather records to model the interaction between environmental covariates and visual features. By testing if weather variables significantly improve the prediction of severity proxies (derived from image analysis) compared to image-only models, we directly measure the environmental modulation of the symptom-severity relationship.

## Expected results

We expect to find that high humidity strengthens the symptom-severity correlation (more visible lesions per unit of biological severity), while extreme heat weakens it (symptoms appear but progress slowly or desiccate). This would be confirmed if an interaction term between humidity and image features significantly improves prediction accuracy (p < 0.05, R² increase > 0.05) over a weather-agnostic baseline.

## Methodology sketch

- Download the PlantVillage dataset (https://www.kaggle.com/datasets/emmarex/plantdisease) — contains labeled leaf images with disease categories.
- Extract severity proxies from images using OpenCV (lesion segmentation, contour area calculation, and color-based necrosis indexing) to create a continuous "visual severity" score.
- Match each image's metadata (location/date) to historical weather data via the Open-Meteo API (https://open-meteo.com/) or NOAA GHCN-Daily (https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily).
- Aggregate weather features (mean temperature, total precipitation, mean humidity) for the 7 days preceding the image capture date.
- Train a Random Forest regressor to predict the "visual severity" score from image features + weather covariates.
- Compare model performance (R², RMSE) between: (a) image-only baseline, (b) image + weather main effects, (c) image + weather + interaction terms.
- Conduct permutation tests (1000 iterations, α = 0.05) to assess whether weather features contribute unique variance beyond image features.
- Generate interaction plots showing predicted severity across humidity/temperature bins to visualize the modulation effect.
- All computations will be performed on CPU using batched OpenCV operations to ensure the pipeline runs within 7GB RAM and the 6-hour GHA time limit.

## Duplicate-check

- Reviewed existing ideas: None provided.
- Closest match: None found.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-08-04T18:59:42Z
**Outcome**: success
**Original term**: Predicting Plant Disease Severity from Publicly Available Image Data and Meteorological Records biology
**Verified citation count**: 5

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Predicting Plant Disease Severity from Publicly Available Image Data and Meteorological Records biology | 5 |

### Verified citations

1. **Deep 1D-Convnet for accurate Parkinson disease detection and severity prediction from gait** (2019). Imanne El Maachi, Guillaume-Alexandre Bilodeau, Wassim Bouachir. arXiv. [1910.11509](https://arxiv.org/abs/1910.11509). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
2. **ISPO: An Integrated Ontology of Symptom Phenotypes for Semantic Integration of Traditional Chinese Medical Data** (2024). Zixin Shu, Rui Hua, Dengying Yan, Chenxia Lu, Ning Xu, et al.. arXiv. [2407.12851](https://arxiv.org/abs/2407.12851). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
3. **The RSNA Abdominal Traumatic Injury CT (RATIC) Dataset** (2024). Jeffrey D. Rudie, Hui-Ming Lin, Robyn L. Ball, Sabeena Jalal, Luciano M. Prevedello, et al.. arXiv. [2405.19595](https://arxiv.org/abs/2405.19595). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
4. **AgGym: An agricultural biotic stress simulation environment for ultra-precision management planning** (2024). Mahsa Khosravi, Matthew Carroll, Kai Liang Tan, Liza Van der Laan, Joscif Raigne, et al.. arXiv. [2409.00735](https://arxiv.org/abs/2409.00735). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
5. **Change-Agent: Towards Interactive Comprehensive Remote Sensing Change Interpretation and Analysis** (2024). Chenyang Liu, Keyan Chen, Haotian Zhang, Zipeng Qi, Zhengxia Zou, et al.. arXiv. [2403.19646](https://arxiv.org/abs/2403.19646). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
