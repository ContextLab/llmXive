---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Molecular Properties from Vibrational Spectra with Deep Learning  

**Field**: chemistry  

## Research question  

Can a deep learning model trained on experimentally or computationally derived vibrational spectra accurately predict key molecular electronic properties (dipole moment, polarizability, HOMO‑LUMO gap) for small organic molecules?  

## Motivation  

Vibrational spectroscopy (IR/Raman) is cheap, rapid, and widely available, yet its quantitative use for inferring electronic properties remains limited. Current quantum‑chemical calculations that provide those properties are computationally intensive for large libraries. Demonstrating that spectra alone contain sufficient information for property prediction would enable high‑throughput screening of molecular databases without costly electronic‑structure calculations.  

## Related work  

- [Toward Complete Molecular Structure Prediction from Infrared Spectroscopy Using Deep Learning (2025)](https://www.semanticscholar.org/paper/b9bf97ec6ace00cd988365179abeb5c9140f0675) — Shows that deep CNNs can invert IR spectra to recover full molecular graphs, suggesting that spectral information is rich enough for detailed molecular inference.  
- [Unlocking the Potential of Machine Learning in Enhancing Quantum Chemical Calculations for Infrared Spectral Prediction (2025)](https://www.semanticscholar.org/paper/61facc0dd6b697e3b4dd94b4736f4a18633b48f3) — Uses ML to improve the accuracy and speed of IR‑spectra prediction, providing a pipeline for generating large synthetic spectral datasets.  
- [Improving the prediction performance of ab initio method on vibrational energy spectra of HF/HBr/H35Cl/Na35Cl based on machine learning algorithm (2023)](https://www.semanticscholar.org/paper/43a10624bb4d80b376687c2bc6116d071135dc76) — Demonstrates that ML can correct systematic errors in computed vibrational energies, highlighting the feasibility of learning spectral‑property relationships.  
- [Deep Spatial Learning with Molecular Vibration (2020)](http://arxiv.org/abs/2011.07200v1) — Introduces a spatial‑graph‑based neural network that ingests vibrational mode information to predict molecular properties, directly relevant to our proposed CNN approach.  
- [Fusing Raman Spectra with Fiber Metrics in Machine Learning Models That Predict the Physical-Mechanical Properties of Paper (2025)](https://www.semanticscholar.org/paper/cafed83b1981dde4ad1ba2f20ea3473b8d6ffe6a) — Shows successful regression from Raman spectra to quantitative material properties, providing a methodological precedent.  
- [Predicting optical spectra for optoelectronic polymers using coarse‑grained models and recurrent neural networks (2020)](https://www.semanticscholar.org/paper/c76ff3d347931ef6a44dc8451a26346d46bd62c2) — Uses RNNs to map coarse‑grained representations to spectra, illustrating flexible sequence‑to‑property learning that can be adapted for vibrational data.  

## Expected results  

- A convolutional neural network will achieve mean absolute errors (MAE) of ≤ 0.05 D for dipole moments, ≤ 0.2 Å³ for isotropic polarizability, and ≤ 0.1 eV for HOMO‑LUMO gaps on a held‑out QM9 test set, outperforming simple linear baselines.  
- Statistical comparison (paired t‑test) between the model’s MAE and the MAE of a baseline DFT‑derived property (computed on the same molecules) will show a significant reduction (p < 0.01), confirming that spectra‑based prediction is not merely reproducing the training distribution but adds predictive value.  

## Methodology sketch  

- **Data acquisition**  
  1. Download the QM9 dataset (≈ 133 k molecules) from DeepChem: `wget https://deepchem.io.s3.amazonaws.com/datasets/qm9.zip`.  
  2. Retrieve corresponding experimental/computed IR spectra from the NIST Chemistry WebBook bulk dump (ZIP available at `https://github.com/nist-data/IR-spectra/archive/refs/heads/main.zip`).  
  3. Align each molecule’s SMILES (from QM9) with its IR spectrum via InChIKey matching; discard unmatched entries.  

- **Pre‑processing**  
  4. Convert each IR spectrum to a 1‑D intensity vector on a fixed wavenumber grid (400–4000 cm⁻¹, 1 cm⁻¹ resolution).  
  5. Normalize intensities per spectrum (unit‑area) and apply a Gaussian smoothing (σ = 2 cm⁻¹).  
  6. Standardize target properties (dipole, polarizability, HOMO‑LUMO gap) using the training‑set mean and variance.  

- **Model architecture**  
  7. Build a 1‑D CNN in PyTorch: three convolutional blocks (kernel sizes 5, 7, 9; each followed by ReLU, batch‑norm, max‑pool), flatten, then two fully‑connected layers ending in three independent regression heads (one per property).  

- **Training**  
  8. Split data: 80 % train, 10 % validation, 10 % test (stratified by molecular size).  
  9. Optimize with Adam (lr = 1e‑3), batch size = 256, early stopping on validation loss (patience = 10 epochs).  
  10. Log training curves with TensorBoard; checkpoint the best model.  

- **Evaluation**  
  11. Compute MAE and R² for each property on the test set.  
  12. Perform paired t‑tests comparing model predictions vs. DFT reference values (using the same test molecules) to assess statistical significance.  
  13. Visualize representative spectra with overlaid predicted vs. true property values.  

- **Reproducibility & Runtime constraints**  
  14. All steps run on a single‑core CPU (GitHub Actions runner) within the 6‑hour limit: data download (~30 min), preprocessing (~45 min), training (≈ 2 h, 2‑epoch checkpoints), evaluation (~15 min).  
  15. Provide a `requirements.txt` (PyTorch ≤ 2.0, pandas, numpy, scikit‑learn, matplotlib, tensorboard) and a Bash script `run.sh` that orchestrates the pipeline.  

## Duplicate-check  

- Reviewed existing ideas: *(none provided)*.  
- Closest match: *(none identified)*.  
- Verdict: **NOT a duplicate**.
