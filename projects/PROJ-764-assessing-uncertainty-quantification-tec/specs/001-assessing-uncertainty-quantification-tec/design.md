# Design Document: Assessing Uncertainty Quantification

## Overview
This document outlines the design for assessing UQ techniques on material property prediction.

## Architecture
- Data Ingestion: OQMD dataset via HuggingFace.
- Preprocessing: Stratified splitting, PCA reduction.
- Modeling: Baseline FFNN, Deep Ensembles, MC Dropout, Sparse GP.
- Evaluation: Calibration (ECE), Interval Score, Sharpness.
- Application: Screening candidates based on Expected Loss.

## Constraints
- CPU-only execution.
- 5-hour pipeline timeout.
- Real data only (no synthetic fallbacks).