---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting Material Degradation Pathways from Compositional Data

**Field**: materials science

## Research question

To what extent does bulk alloy stoichiometry constrain the dominant corrosion degradation pathway (e.g., pitting vs. stress corrosion cracking) under standardized electrochemical conditions?

## Motivation

Identifying degradation modes typically requires expensive, time-consuming electrochemical testing. If composition alone can predict the dominant failure mechanism, materials selection pipelines can be accelerated significantly. This addresses the gap between high-throughput compositional databases and the scarcity of high-quality degradation pathway labels.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv for "alloy corrosion prediction machine learning", "composition degradation pathway ML", and "materials property prediction ML". We also reviewed the provided verified literature block for any work linking composition to degradation modes in metallic systems.

### What is known

- [Leveraging Data Science for Sustainable Material Management: Predictive Analytics and Optimization for Waste Reduction and Lifecycle Extension (2025)](https://www.semanticscholar.org/paper/5606996a2ccaad0bb64894275e9d01d483558fc6) — Establishes the general framework for using data science to extend material lifespan, though focused on waste management rather than specific degradation mechanisms.
- [XElemNet: towards explainable AI for deep neural networks in materials science (2024)](https://www.semanticscholar.org/paper/7b018d4089008493d2fa391467d7a527fcad839e) — Demonstrates deep learning for predicting formation energy from composition, validating the feasibility of composition-to-property mapping in metals.
- [Predicting band gap from chemical composition: A simple learned model for a material property with atypical statistics (2025)](https://www.semanticscholar.org/paper/1a0551fc1f14f6ef252fff1fb3d9928658a27aeb) — Shows that composition-based ML is effective for electronic properties, but does not address mechanical or chemical degradation pathways.

### What is NOT known

No published work in the verified literature directly maps alloy stoichiometry to discrete corrosion degradation pathways (pitting, SCC, fatigue) using machine learning. Existing work focuses on thermodynamic stability (formation energy) or electronic properties (band gap), leaving the specific mapping of composition to failure mode unquantified.

### Why this gap matters

Filling this gap would enable rapid screening of alloy candidates for corrosive environments without requiring full-scale lifetime testing, reducing R&D costs and material waste in industries like aerospace and infrastructure.

### How this project addresses the gap

This project will attempt to train a multi-label classifier on available public corrosion datasets to determine if a statistically significant signal exists between composition and degradation mode, thereby establishing the baseline feasibility of this mapping.

## Expected results

We expect to find a moderate correlation between specific alloying elements (e.g., Cr, Ni) and specific degradation modes, though environmental factors may introduce noise. Success is measured by achieving a macro-F1 score significantly above random baseline (>0.6) on a held-out test set of public corrosion records.

## Methodology sketch

- Download open corrosion datasets from Zenodo (https://zenodo.org/) using keywords "alloy corrosion", "degradation pathway", and "composition".
- Extract elemental weight percentages and target degradation labels (pitting, SCC, fatigue, none).
- Filter records to ensure only metallic alloys are included; remove polymers and composites.
- Encode composition features using atomic properties (electronegativity, radius) similar to the approach in XElemNet (https://www.semanticscholar.org/paper/7b018d4089008493d2fa391467d7a527fcad839e).
- Split data into 80/20 train/test sets stratified by degradation label.
- Train a Random Forest multi-label classifier using scikit-learn on CPU (GHA compatible).
- Evaluate performance using macro-F1 score and confusion matrix to identify dominant error modes.
- Perform feature importance analysis to determine which elements drive specific degradation predictions.

## Duplicate-check

- Reviewed existing ideas: None provided in input.
- Closest match: N/A.
- Verdict: NOT a duplicate.
