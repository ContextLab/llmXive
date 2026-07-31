# Specification for Predicting the Yield Strength of High‑Entropy Alloys

## Introduction
This document specifies the functional and non‑functional requirements for the project **PROJ‑418‑predicting‑the‑yield‑strength‑of‑high‑en**. It is organized into sections describing user stories, system behavior, data handling, and assumptions.

## User Stories
* **US1** – Data acquisition and descriptor engineering
* **US2** – Model training and predictive performance evaluation
* **US3** – Statistical validation and significance reporting

## Functional Requirements
* Download verified HEA composition datasets.
* Compute compositional descriptors (δ, Δχ, VEC, mixing entropy, melting‑temperature variance).
* Train Linear Regression, Random Forest, and Gradient Boosting models with 5‑fold cross‑validation.
* Perform statistical validation including VIF calculation, permutation importance, multiple‑comparison correction, bootstrap resampling, and sensitivity analysis.

## Non‑Functional Requirements
* All scripts must be deterministic (fixed random seeds).
* Runtime of the full pipeline must not exceed 6 hours on a single CPU.
* All generated artifacts must conform to schemas defined in `contracts/`.

## Assumptions
- The permutation importance implementation must always execute **1000 permutations**. Adaptive permutation counts are **not permitted**; the implementation must enforce a fixed count of 1000 regardless of dataset size.
- All yield‑strength values are assumed to be reported in MPa after unit normalization.
- The raw dataset is expected to be available from the verified URL defined in `research.md`.

## Disclaimer
All analyses are associational; no causal inference should be drawn from the results. This disclaimer is injected into all generated figures and reports.