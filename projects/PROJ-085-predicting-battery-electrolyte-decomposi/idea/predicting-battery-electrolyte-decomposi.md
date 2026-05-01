---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Battery Electrolyte Decomposition Products via DFT and Machine Learning

**Field**: chemistry

## Research question

Can machine learning models trained on existing Density Functional Theory (DFT) datasets accurately predict the decomposition pathways of common lithium-ion battery electrolytes under varying electrochemical conditions?

## Motivation

Experimental identification of electrolyte decomposition products is slow and resource-intensive, limiting the pace of battery optimization. While DFT provides accurate energy landscapes, running new calculations for every candidate is computationally prohibitive for high-throughput screening. Leveraging pre-computed public DFT data to train lightweight ML models offers a feasible path to rapid electrolyte stability prediction within standard compute constraints.

## Related work

- [Lithium Batteries and the Solid Electrolyte Interphase (SEI)—Progress and Outlook (2023)](https://doi.org/10.1002/aenm.202203307) — Provides context on interfacial dynamics and the importance of optimizing electrochemical energy storage materials, supporting the need for predictive screening tools.

## Expected results

The ML model will achieve a coefficient of determination (R²) > 0.8 on a held-out test set of known decomposition energies. The workflow will successfully identify key molecular descriptors (e.g., HOMO/LUMO levels, bond dissociation energies) that correlate with electrolyte stability, validated through k-fold cross-validation.

## Methodology sketch

- **Data Acquisition**: Download pre-computed DFT energies and molecular structures for common electrolytes (e.g., EC, DMC, LiPF6) from the Materials Project public database (https://materialsproject.org/) or equivalent Zenodo repositories.
- **Feature Engineering**: Extract molecular descriptors (atomic composition, bond lengths, electronic properties) using RDKit and Pandas within a Python environment.
- **Model Selection**: Implement a Random Forest Regressor using Scikit-learn, optimized for CPU-only execution and ≤7GB RAM usage.
- **Training**: Train the model on 80% of the dataset, performing hyperparameter tuning via GridSearchCV with 5-fold cross-validation.
- **Validation**: Evaluate performance on the remaining 20% test set using Mean Absolute Error (MAE) and R² metrics.
- **Prediction**: Apply the trained model to predict stability scores for a small set of novel electrolyte candidates (≤10 molecules) to demonstrate screening capability.
- **Visualization**: Generate correlation plots and feature importance charts using Matplotlib/Seaborn for the final report.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: N/A (No corpus access).
- Verdict: NOT a duplicate
