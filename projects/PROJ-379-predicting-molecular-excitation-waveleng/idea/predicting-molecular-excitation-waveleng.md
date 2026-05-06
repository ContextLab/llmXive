---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Molecular Excitation Wavelengths from SMILES with Graph Neural Networks

**Field**: chemistry

## Research question

How does molecular graph structure, as encoded in SMILES, relate to the wavelength of maximum absorption (λmax) across diverse organic chromophores?

## Motivation

Excitation wavelength prediction is essential for spectroscopy, photochemistry, and materials design, but traditional quantum chemical calculations are computationally expensive. Establishing a data-driven structure–spectrum relationship would enable rapid screening of candidate molecules without requiring high-level electronic structure computations.

## Literature gap analysis

### What we searched

We queried Semantic Scholar / arXiv / OpenAlex using terms: "molecular excitation wavelength prediction SMILES graph neural network", "UV-Vis absorption spectrum machine learning", and "chromophore λmax deep learning". The search returned sparse results: only 2 papers in the literature block, neither directly addressing the structure–spectrum prediction task.

### What is known

- [MECCH: Metapath Context Convolution-based Heterogeneous Graph Neural Networks (2022)](http://arxiv.org/abs/2211.12792v2) — Establishes HGNN methodology for heterogeneous molecular graphs but does not apply it to spectroscopic property prediction.
- [AGILE platform: a deep learning powered approach to accelerate LNP development for mRNA delivery (2024)](https://doi.org/10.1038/s41467-024-50619-z) — Demonstrates deep learning for molecular delivery applications but not for excitation wavelength prediction.

### What is NOT known

No published work has systematically evaluated how well GNNs can predict λmax from SMILES alone across diverse organic chromophores. Existing spectral databases exist but lack standardized ML-ready benchmarks for this specific regression task.

### Why this gap matters

Filling this gap would enable rapid virtual screening of photoactive molecules for applications in solar cells, fluorescent probes, and photopharmacology without requiring expensive quantum calculations for each candidate.

### How this project addresses the gap

The methodology will (1) curate a SMILES–λmax paired dataset from public spectral repositories, (2) train a message-passing GNN to regress λmax from molecular graphs, and (3) evaluate prediction error against held-out test molecules, producing the first standardized benchmark for this structure–spectrum relationship.

## Expected results

We expect the GNN to achieve mean absolute error (MAE) <30 nm on held-out test molecules, demonstrating that molecular graph structure alone contains sufficient signal for approximate λmax prediction. Success would be measured by outperforming a random baseline and a simple fingerprint-based linear model; failure would be indicated by MAE >50 nm across all model variants.

## Methodology sketch

- Download UV-Vis spectral dataset from PubChem or Spectral Database for Organic Compounds (SDBS) via public API (wget/curl; ~10K molecules).
- Parse SMILES strings into molecular graphs using RDKit (CPU-only, <7GB RAM).
- Split data 80/10/10 (train/validation/test) ensuring scaffold-based split to avoid structural leakage.
- Implement message-passing GNN (2–3 layers, <1M parameters) in PyTorch Geometric or DGL (CPU-compatible).
- Train model for ≤50 epochs with early stopping on validation loss (wall-clock target: ≤4h on GHA).
- Evaluate test set MAE, R², and compare against baseline (ECFP fingerprint + linear regression).
- Perform feature importance analysis via GNNExplainer or gradient-based attribution on top-50 test molecules.
- Document all dataset URLs, hyperparameters, and code in reproducible GitHub repository.

## Duplicate-check

- Reviewed existing ideas: [AGILE platform deep learning LNP], [MECCH heterogeneous GNN].
- Closest match: MECCH (similarity sketch: both use GNNs on molecular graphs, but MECCH focuses on heterogeneous graph representation learning, not spectroscopic property prediction).
- Verdict: NOT a duplicate
