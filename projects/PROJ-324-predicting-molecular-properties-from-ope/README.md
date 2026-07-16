# PROJ-324: Predicting Molecular Properties from Open Babel Fingerprints with Random Forests

## Overview
This project investigates the predictive power of Open Babel molecular fingerprints combined with Random Forest models to estimate molecular properties (logP, solubility, boiling point). It contrasts these non-linear models against Crippen's additive fragment baseline to identify structural substructures where additive models fail.

## Project Structure
- `code/`: Source code for data processing, model training, and analysis.
- `data/`: Raw, processed, and derived datasets.
- `tests/`: Unit, integration, and contract tests.
- `specs/`: Project specifications and design documents.

## Key Research Questions
1. Can Random Forest models using Open Babel fingerprints significantly outperform Crippen's additive model?
2. Which specific fingerprint bits (substructures) contribute most to the error reduction?
3. Where do additive models fail due to conformational or interaction effects?

## Status
Phase 1 (Setup) and Phase 2 (Foundational) are in progress.
See `tasks.md` for the full task list.
