---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Material Stability using Machine Learning and DFT Calculations  

**Field**: chemistry  

## Research question  

Can a supervised machine‑learning model, trained on publicly available DFT formation‑energy data, accurately predict the thermodynamic stability (formation energy and decomposition energy) of inorganic compounds that are not present in the training set?  

## Motivation  

Thermodynamic stability determines whether a newly designed solid can be synthesized and remain functional under operating conditions. Current high‑throughput DFT screenings are computationally expensive, limiting the pace of discovery. A reliable, low‑cost surrogate model would enable rapid pre‑screening of candidate materials for energy‑storage, catalysis, and electronic applications, accelerating the Materials Genome Initiative.  

## Related work  

- [A general‑purpose machine learning framework for predicting properties of inorganic materials (2016)](https://doi.org/10.1038/npjcompumats.2016.28) — Demonstrates a pipeline that extracts compositional descriptors and trains regression models on Materials Project DFT data.  
- [Recent advances and applications of machine learning in solid‑state materials science (2019)](https://doi.org/10.1038/s41524-019-0221-0) — Reviews successful applications of ML to predict formation energies, band gaps, and elastic constants across large materials datasets.  
- [Machine learning in materials informatics: recent applications and prospects (2017)](https://doi.org/10.1038/s41524-017-0056-5) — Discusses descriptor engineering (e.g., Magpie, matminer) and benchmark models for inorganic thermochemistry.  
- [The Open Quantum Materials Database (OQMD): assessing the accuracy of DFT formation energies (2015)](https://doi.org/10.1038/npjcompumats.2015.10) — Provides a curated dataset of ~300 k DFT formation energies that serves as a benchmark for ML surrogates.  
- [Intercalation Chemistry of the Disordered Rocksalt Li₃V₂O₅ Anode from Cluster Expansions and Machine Learning Interatomic Potentials (2023)](https://doi.org/10.1021/acs.chemmater.2c02839) — Shows how ML interatomic potentials can capture complex chemistry in battery anodes, illustrating the relevance of ML for stability predictions.  
- [DOME: Recommendations for supervised machine learning validation in biology (2020)](http://arxiv.org/abs/2006.16189v4) — Offers best‑practice guidelines for model validation (train/val/test splits, cross‑validation) that are directly applicable to materials‑ML studies.  
- [Constructing artificial life and materials scientists with accelerated AI using Deep AndersoNN (2024)](http://arxiv.org/abs/2407.19724v1) — Introduces a novel implicit‑layer architecture that could be explored for efficient surrogate modeling of DFT energies.  

## Expected results  

- A regression model (e.g., Gradient Boosting, Random Forest, or a shallow neural network) that achieves mean absolute error ≤ 0.05 eV/atom on a held‑out test set of ≥ 5 000 compounds.  
- Demonstrated ability to rank candidate compounds by predicted decomposition energy, correctly identifying > 80 % of experimentally known stable phases within the top‑10 % of predictions.  
- Open‑source code and a lightweight dataset (≈ 200 MB) that can be downloaded and run on a GitHub Actions runner in ≤ 5 hours.  

## Methodology sketch  

1. **Data acquisition**  
   - Download the OQMD formation‑energy CSV from the Zenodo archive (URL provided in the OQMD paper).  
   - Optionally fetch a complementary set of ~10 000 compounds from the Materials Project via their REST API (public key required).  

2. **Feature engineering**  
   - Use *matminer* to compute Magpie compositional descriptors (e.g., atomic number mean, electronegativity variance).  
   - Append elemental property statistics (e.g., average atomic radius, oxide formation enthalpy) obtained from the *pymatgen* periodic table module.  

3. **Dataset split**  
   - Randomly stratify by chemical system (e.g., binary, ternary) into 70 % training, 15 % validation, 15 % test.  
   - Ensure that none of the test compounds appear in the training set to evaluate true extrapolation.  

4. **Model training**  
   - Train a Gradient Boosting Regressor (scikit‑learn) with early stopping on the validation set.  
   - Hyper‑parameter tune using a limited grid (max_depth ∈ {4,6,8}, n_estimators ∈ {200,400}).  

5. **Stability assessment**  
   - For each compound in the test set, compute its predicted formation energy.  
   - Use *pymatgen*’s `PhaseDiagram` class with the predicted energies of all test compounds plus the known stable elemental phases to estimate decomposition energy (energy above the convex hull).  

6. **Model evaluation**  
   - Report MAE, RMSE, and R² for formation‑energy predictions on the test set.  
   - Compute the precision‑recall curve for classifying “stable” (decomposition energy < 0.05 eV/atom) vs. “unstable” compounds.  

7. **Reproducibility & runtime constraints**  
   - All steps are scripted in a single Python file (`run_ml_stability.py`).  
   - Data download ≤ 200 MB; total RAM usage ≤ 4 GB; CPU time ≤ 3 h on the GitHub Actions Ubuntu‑latest runner.  

8. **Deliverables**  
   - GitHub repository containing the code, a lightweight processed dataset, and a Jupyter notebook reproducing the main figures (predicted vs. DFT formation energies, ROC curve for stability classification).  

## Duplicate-check  

- Reviewed existing ideas: *(none provided)*.  
- Closest match: N/A.  
- Verdict: **NOT a duplicate**.
