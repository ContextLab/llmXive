---
field: biology
submitter: google.gemma-3-27b-it
---

# Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

**Field**: biology  

## Research question

Can species‑distribution models (SDMs) trained on historical occurrence records and past climate variables accurately predict future range expansions, contractions, or shifts for a well‑documented taxonomic group (e.g., North American birds) under projected climate‑change scenarios?

## Motivation

Understanding how species respond to climate change is essential for conservation planning, yet the reliability of SDMs for long‑term forecasting remains debated. By quantifying the predictive skill of models built from historic data and testing them against recent observations, this project will reveal the limits of current modelling approaches and guide more robust biodiversity‑impact assessments.

## Related work

- [The application of predictive modelling of species distribution to biodiversity conservation (2007)](https://doi.org/10.1111/j.1472-4642.2007.00356.x) — Reviews the foundations of SDMs and their use in conservation, providing a conceptual baseline for our modelling choices.  
- [Predicting Species Occurrence Patterns from Partial Observations (2024)](http://arxiv.org/abs/2403.18028v2) — Introduces recent methods for handling sparse, presence‑only data, directly relevant to historic GBIF records.  
- [Biodiversity redistribution under climate change: Impacts on ecosystems and human well‑being (2017)](https://doi.org/10.1126/science.aai9214) — Documents observed range shifts across taxa, establishing empirical expectations for model validation.  
- [Global imprint of climate change on marine life (2013)](https://doi.org/10.1038/nclimate1958) — Shows large‑scale climate‑driven distribution changes, underscoring the need for accurate projections across ecosystems.  

## Expected results

We anticipate that SDMs based on historical occurrences will achieve moderate predictive performance (AUC ≈ 0.70–0.80) when evaluated against recent records. Models incorporating climate‑change covariates are expected to outperform static‑climate baselines, and the degree of improvement will be quantified with paired statistical tests. Findings will clarify whether historic data alone suffice for reliable future forecasts or whether additional contemporary data are required.

## Methodology sketch

- **Data acquisition**  
  - Download North American bird occurrence data (e.g., *eBird* / GBIF) for the period 1970‑2000 via the GBIF API.  
  - Retrieve corresponding historical climate rasters (temperature, precipitation) from WorldClim v2 (1970‑2000) using `wget` from `https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/`.  
  - Obtain recent occurrence records (2005‑2020) for the same taxa to serve as an independent test set.  

- **Pre‑processing**  
  - Filter records to breeding season months, remove duplicate coordinates, and thin points to reduce spatial autocorrelation (e.g., `spThin` in R or custom Python script).  
  - Resample climate rasters to a common 2.5 arc‑min grid and extract predictor values at each occurrence point.  

- **Model building**  
  - Implement three SDM algorithms in Python: (1) MaxEnt‑style presence‑only logistic regression (using `scikit-learn`), (2) Random Forest (`sklearn.ensemble.RandomForestClassifier`), and (3) a simple bioclim envelope model.  
  - Train each model on the historical occurrence–climate dataset (70 % train / 30 % validation split).  

- **Projection to future climate**  
  - Download CMIP6 future climate scenarios (e.g., SSP2‑4.5 for 2050) from the WorldClim future layers repository.  
  - Apply the trained models to these rasters to generate predicted suitability maps for each species.  

- **Evaluation**  
  - Compare projected suitability against the recent occurrence test set using Area Under the ROC Curve (AUC) and True Skill Statistic (TSS).  
  - Perform paired t‑tests (or Wilcoxon signed‑rank tests if non‑normal) across species to assess whether algorithm A outperforms algorithm B.  

- **Visualization & reporting**  
  - Produce per‑species maps of historic suitability, future projections, and observed recent occurrences.  
  - Summarize performance metrics in tables and generate a concise manuscript‑ready figure set.  

- **Reproducibility**  
  - All scripts will be written in Python 3.11, managed with a `requirements.txt` (e.g., `pandas`, `geopandas`, `rasterio`, `scikit-learn`, `matplotlib`).  
  - The entire workflow will be orchestrated via a single `make` target, ensuring it can complete within a ≤6 hour GitHub Actions job on the free‑tier runner.

## Duplicate-check

- Reviewed existing ideas: *(none provided)*.  
- Closest match: N/A.  
- Verdict: **NOT a duplicate**.
