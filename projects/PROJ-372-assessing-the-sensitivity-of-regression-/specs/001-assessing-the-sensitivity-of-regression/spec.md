# Spec: Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection

## Overview
This project investigates how the stability of OLS regression coefficients varies with dataset subset selection size and the presence of assumption violations (heteroscedasticity, outliers, multicollinearity).

## User Stories

### US1: Data Ingestion and Violation Profiling
As a researcher, I want to ingest verified numerical datasets and automatically profile them for OLS assumption violations so that I can filter or stratify them by violation severity.
- **Acceptance Criteria**:
 - System ingests datasets from HuggingFace/UCI.
 - System computes Condition Number, Breusch-Pagan statistic, and Cook's Distance.
 - System classifies violation severity (Low/Medium/High).
 - System outputs a `DatasetProfile` JSON artifact.

### US2: Subset Resampling and Stability Estimation
As a researcher, I want to generate random subsets of data across 5 specific sample size tiers and fit OLS models to each so that I can compute the empirical standard deviation of coefficients.
- **Acceptance Criteria**:
 - System generates random subsets for each dataset.
 - **Sample Size Tiers**: The system uses the following specific sample size tier percentages defined in the research design:
 - **Tier 1**: [deferred]
 - **Tier 2**: [deferred]
 - **Tier 3**: [deferred]
 - **Tier 4**: [deferred]
 - **Tier 5**: [deferred]
 - System fits OLS models to each subset.
 - System computes empirical standard deviation of coefficients across subsets per tier.
 - System verifies convergence (Standard Error of SD < 5%).

### US3: Interaction Analysis and Sensitivity Visualization
As a researcher, I want to run a meta-analysis with interaction terms to understand how violation severity and condition number jointly affect coefficient stability.
- **Acceptance Criteria**:
 - System performs multiple regression with interaction terms.
 - System generates stability curves (Coefficient SD vs Condition Number).
 - System outputs a final report with associational findings.

## Research Design Parameters
- **Sample Size Tiers**: [10, 25, 50, 75, 90] (Percentages of full dataset size).
- **Number of Subsets per Tier**: 200.
- **Convergence Threshold**: Standard Error of the SD must be < 5% of the SD.
- **Violation Severity Thresholds**:
 - Low: Breusch-Pagan p-value > 0.10
 - Medium: 0.05 < p-value <= 0.10
 - High: p-value <= 0.05

## Data Models
- `DatasetProfile`: Contains metadata, violation stats, and severity classification.
- `StabilityResult`: Contains coefficient statistics per subset and tier.
- `InteractionModel`: Contains regression results of the meta-analysis.

## Constraints
- **Real Data Only**: No synthetic data generation.
- **Streaming**: Must stream datasets > 7GB.
- **Compute**: CPU-only execution.
