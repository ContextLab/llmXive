# Implementation Plan: Exploring the Correlation Between Molecular Flexibility and Drug Transport Across Cell Membranes

## Project Overview
This project investigates the hypothesis that molecular flexibility, quantified via torsional variance from Normal Mode Analysis (NMA), is a significant predictor of Caco-2 permeability (logPapp), independent of traditional physicochemical properties.

## Objectives
1. **Retrieve & Preprocess**: Acquire a high-quality Caco-2 dataset from ChEMBL, ensuring protocol homogeneity.
2. **Compute Descriptors**: Generate 3D conformer ensembles and calculate torsional variance using PyVib.
3. **Correlate**: Establish statistical relationships between flexibility and permeability, controlling for MW, PSA, and logP.
4. **Validate**: Assess model robustness via cross-validation and scaling law analysis.

## Constraints & Deviations
- **Data Source**: ChEMBL REST API (Assay Type: Caco-2).
- **Flexibility Metric**: Torsional variance (dihedral) in rad², derived from PyVib. Bond/angle variances are diagnostic only.
- **Confounders**: Strictly limited to logP, MW, and PSA as per FR-007.
- **Statistical Rigor**: Benjamini-Hochberg FDR correction applied to all correlation p-values.
- **Scaling Law**: If linear R² < 0.3, a power-law model is fitted and validated against the linear model.
- **Transparency**: All computational steps are CPU-tractable; no GPU offload. A transparency report is generated dynamically.

## Execution Pipeline
1. `code/setup_project_structure.py`: Initialize directories.
2. `code/data/retrieval.py`: Fetch raw data from ChEMBL.
3. `code/data/preprocessing.py`: Filter for quality and protocol consistency.
4. `code/data/conformer_gen.py`: Generate 3D ensembles.
5. `code/data/descriptors.py`: Calculate variance metrics.
6. `code/data/analysis.py`: Perform correlation, FDR, and scaling analysis.
7. `code/data/visualize.py`: Generate publication-quality plots.
8. `code/utils/generate_transparency_report.py`: Document methodology.

## Status
- **Phase 1 (Setup)**: Complete.
- **Phase 2 (Foundational)**: Complete.
- **Phase 3 (US1 - Data)**: Complete.
- **Phase 4 (US2 - Analysis)**: Complete (including Scaling Law analysis T026-T028).
- **Phase 5 (US3 - Validation)**: Complete.
- **Phase N (Polish)**: T038 (Plan Update) Complete.

## Notes
- The plan confirms that the "Computational Method Transparency" section in `research.md` is generated dynamically (T036) and reflects the actual execution parameters (conformer count, metric definitions, statistical tests).
- No deviations from the original specification were required; the implemented pipeline strictly adheres to the defined constraints.