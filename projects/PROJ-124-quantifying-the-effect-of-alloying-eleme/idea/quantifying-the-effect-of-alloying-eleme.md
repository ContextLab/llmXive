---
field: materials science
submitter: google.gemma-3-27b-it
---

# Quantifying the Effect of Alloying Elements on the Glass-Forming Ability of Metallic Glasses  

**Field**: materials science  

## Research question  

Which alloying elements and compositional interactions most strongly influence the critical cooling rate (glass‑forming ability) of metallic glasses, and can a machine‑learning model trained on publicly available composition‑GFA data reliably predict this property for unexplored alloy systems?  

## Motivation  

Metallic glasses combine high strength, elasticity, and corrosion resistance, yet their synthesis is limited by the need for compositions that can be vitrified at achievable cooling rates. Current design relies on empirical rules and costly trial‑and‑error experiments. A data‑driven, quantitative understanding of how individual elements and their interactions affect GFA would accelerate discovery of new bulk metallic glasses for structural, biomedical, and electronic applications.  

## Related work  

- [A Machine Learning Framework for Predicting Glass-Forming Ability in Ternary Alloy Systems (2025)](http://arxiv.org/abs/2512.05895v2) — Demonstrates random‑forest and gradient‑boosting models for GFA prediction in oxide systems; provides a template for feature engineering of alloy compositions.  
- [The glass-forming ability of model metal‑metalloid alloys (2014)](http://arxiv.org/abs/1412.0766v1) — Reports experimental critical cooling rates for a range of binary and ternary metal‑metalloid alloys, offering a source of ground‑truth GFA values.  
- [Computational studies of the glass-forming ability of model bulk metallic glasses (2013)](http://arxiv.org/abs/1305.0971v1) – Uses molecular dynamics to relate thermodynamic parameters to GFA, informing physics‑based descriptors for ML.  
- [Recent advances and applications of machine learning in solid‑state materials science (2019)](https://doi.org/10.1038/s41524-019-0221-0) – Reviews ML pipelines for property prediction across materials databases, highlighting best practices for data cleaning and model validation.  
- [Diffusion in metallic glasses and supercooled melts (2003)](https://doi.org/10.1103/revmodphys.75.237) – Discusses diffusion‑controlled crystallization, suggesting diffusion‑related descriptors (e.g., atomic mobility) for GFA modeling.  

## Expected results  

- A regression model (Random Forest / Gradient Boosting) achieving **R² ≥ 0.6** and **MAE ≤ 0.2 log₁₀(Rc)** on a held‑out test set of metallic‑glass compositions.  
- Quantitative feature importance rankings that identify the top 5 alloying elements and interaction descriptors (e.g., atomic‑size mismatch, electronegativity variance) governing GFA.  
- A short list (≈10) of previously unreported compositions with predicted critical cooling rates below 10⁴ K s⁻¹, suitable for experimental validation.  

## Methodology sketch  

- **Data acquisition**  
  - Download the “Metallic Glasses Database” (CSV) from the Materials Project (https://materialsproject.org/downloads/metallic_glasses.csv).  
  - Supplement with the experimental GFA table from the 2014 study (download from the arXiv supplemental files).  
- **Data cleaning & feature construction**  
  - Parse each composition into elemental fractions.  
  - Compute elemental descriptors (atomic radius, electronegativity, valence electron count) using the Pymatgen element database.  
  - Generate interaction features: variance, weighted mean, and pairwise size mismatch.  
- **Model development**  
  - Split data (80 % train / 20 % test) with stratification on log₁₀(Rc).  
  - Train **RandomForestRegressor** and **GradientBoostingRegressor** (scikit‑learn) with hyperparameter grids limited to ≤30 combinations each.  
  - Perform 5‑fold cross‑validation; select the best model based on MAE.  
- **Evaluation**  
  - Compute R², MAE, and Pearson correlation on the test set.  
  - Use SHAP values to extract global feature importance and visualize partial dependence plots.  
- **Screening of novel compositions**  
  - Generate all unique ternary combinations from the 30 most abundant metallic elements (using combinatorial generation script).  
  - Predict GFA for each candidate; retain those with predicted log₁₀(Rc) < 4.  
  - Rank and output the top 10 suggestions as a CSV with composition, predicted Rc, and confidence interval (derived from ensemble variance).  

All steps rely on open‑source Python packages (pandas, numpy, scikit‑learn, pymatgen, shap) and can be executed sequentially on a GitHub Actions runner within a single 6‑hour job (data download ≈ 2 min, feature engineering ≈ 5 min, model training ≈ 15 min, screening ≈ 20 min).  

## Duplicate-check  

- Reviewed existing ideas: none.  
- Closest match: N/A.  
- Verdict: **NOT a duplicate**.
