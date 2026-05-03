---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Phase Transitions in Amorphous Solids Using Machine Learning  

**Field**: chemistry  

## Research question  

Can machine‑learning models accurately predict the glass‑transition temperature (Tg) and crystallization propensity of amorphous solids from their chemical composition and short‑range structural descriptors derived from inexpensive molecular‑dynamics (MD) simulations?  

## Motivation  

Amorphous materials (glasses, polymer electrolytes, amorphous pharmaceuticals) lack long‑range order, making their thermal‑phase behavior difficult to predict with conventional crystal‑structure‑based methods. A fast, composition‑driven predictor would enable rapid screening of candidate formulations for batteries, optics, and drug delivery, reducing reliance on costly trial‑and‑error synthesis and long‑duration MD or ab‑initio simulations.  

## Related work  

- [Chemist versus Machine: Traditional Knowledge versus Machine Learning Techniques (2020)](https://doi.org/10.1016/j.trechm.2020.10.007) — Reviews the transition from heuristic chemical rules to data‑driven ML models for materials discovery, highlighting the need for domain‑specific descriptors.  
- [Performance and Cost Assessment of Machine Learning Interatomic Potentials (2020)](https://doi.org/10.1021/acs.jpca.9b08723) — Demonstrates how ML‑based interatomic potentials can capture local atomic environments at a fraction of the cost of quantum‑chemical calculations, providing a template for generating cheap MD trajectories.  
- [Machine Learning Interatomic Potentials as Emerging Tools for Materials Science (2019)](https://doi.org/10.1002/adma.201902765) — Discusses the development of ML interatomic potentials and their application to large‑scale atomistic simulations, supporting the feasibility of generating structural descriptors for amorphous systems.  

## Expected results  

- A regression model (e.g., random forest or modest feed‑forward neural network) that predicts Tg within ±10 K (≈5 % relative error) for a held‑out test set of amorphous compositions.  
- Classification accuracy ≥80 % for binary crystallization propensity (crystallizes vs. remains amorphous) on the same test set.  
- Demonstrated correlation between descriptor importance (e.g., first‑peak RDF height, bond‑angle variance) and physical intuition, providing interpretability.  

## Methodology sketch  

1. **Dataset assembly**  
   - Download publicly available amorphous‑material composition tables from the Open Materials Database (e.g., OQMD, Materials Project) via their REST APIs.  
   - Select ~500 distinct compositions spanning oxides, sulfides, and organic glass formers.  

2. **MD trajectory generation**  
   - Use ASE + LAMMPS with a pre‑trained machine‑learning interatomic potential (e.g., SNAP or GAP) available from the OpenKIM repository.  
   - For each composition, equilibrate a 2 nm cubic cell (≈500 atoms) at 1500 K, then cool at 10 K/ps to 300 K, recording temperature, energy, and structural snapshots.  Each run requires ≤5 minutes on the GitHub Actions CPU pool.  

3. **Descriptor extraction**  
   - Compute short‑range structural features from the final 300 K snapshot using MDAnalysis:  
     - Radial distribution function (RDF) peaks (position, height) for each element pair.  
     - Bond‑angle distribution moments (mean, variance).  
     - Coordination numbers and packing fractions.  
   - Append compositional features (element fractions, atomic radii, electronegativity differences).  

4. **Target labeling**  
   - Obtain experimental Tg values from the literature (e.g., the “Glass Data” dataset on Zenodo, DOI 10.5281/zenodo.XXXXX).  
   - Define crystallization propensity by checking whether the cooled MD trajectory shows a sudden drop in potential energy indicative of nucleation (binary label).  

5. **Model training & validation**  
   - Split data 80/20 train‑test, stratified by composition class.  
   - Train a random‑forest regressor (scikit‑learn, 200 trees) for Tg and a random‑forest classifier for crystallization.  
   - Perform 5‑fold cross‑validation; tune hyperparameters with a limited grid (max depth, min samples leaf).  

6. **Performance assessment**  
   - Report RMSE for Tg, confusion matrix and ROC‑AUC for crystallization.  
   - Use SHAP values to identify the most predictive descriptors.  

7. **Reproducibility package**  
   - Provide a `requirements.txt` (Python 3.11, ASE, LAMMPS‑Python, MDAnalysis, scikit‑learn, shap).  
   - Include a shell script that automates data download, MD runs, feature extraction, and model training; each step is bounded to <30 minutes on the runner.  

## Duplicate-check  

- Reviewed existing ideas: *(none provided in the current project corpus)*.  
- Closest match: *(no near‑duplicate identified)*.  
- Verdict: **NOT a duplicate**.
