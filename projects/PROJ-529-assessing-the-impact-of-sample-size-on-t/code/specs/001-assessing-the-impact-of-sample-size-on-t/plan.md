# Project Plan: Assessing the Impact of Sample Size on Meta-Analytic Reliability

## Overview
This project investigates how the number of studies (k) in a meta-analysis affects the stability and reliability of pooled effect size estimates.

## Objectives
1. Acquire a corpus of real-world meta-analyses.
2. Generate bootstrap subsamples for varying study counts (k).
3. Compute stability metrics (SD of pooled effects) and coverage rates.
4. Identify the minimum k required for stable estimates (threshold detection).

## Methodology
- **Data Source**: Cochrane Library / Campbell Collaboration (Real) or Parameterized Simulation (Fallback).
- **Statistical Models**: Fixed Effects (FE) and Random Effects (RE) using Inverse Variance weighting.
- **Estimators**: DerSimonian-Laird (DL) for k >= 10, Restricted Maximum Likelihood (REML) for k < 10.
- **Analysis**: Generalized Additive Models (GAM) to detect non-linear stability thresholds.

## Deliverables
- `data/raw/`: Downloaded meta-analysis data or simulation parameters.
- `data/processed/`: Subsampled datasets, stability metrics, coverage rates.
- `data/output/`: Threshold estimates, diagnostic plots, final reports.
- `code/`: Implementation of acquisition, subsampling, modeling, and analysis.

## Success Criteria
- Real data acquisition >= 50 meta-analyses (or documented simulation fallback).
- Identification of a specific k-threshold where stability plateaus.
- Reproducible pipeline for subsampling and metric computation.
