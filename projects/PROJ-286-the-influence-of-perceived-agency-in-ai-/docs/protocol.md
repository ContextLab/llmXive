# Pre-Registered Analysis Plan: The Influence of Perceived Agency in AI Interactions on Trust

**Project ID**: PROJ-286
**Protocol Version**: 1.0
**Date Registered**: 2023-10-27
**Reference**: FR-006, US-3

## 1. Objective
This document defines the pre-registered analysis plan to evaluate the effect of perceived agency (High, Low, Control conditions) on user trust in AI systems. The plan includes sensitivity analysis parameters and statistical correction strategies to ensure methodological robustness.

## 2. Data Sources
- **Primary Data**: `data/raw/` (CSV exports from experimental interface).
- **Verified Scale Items**: `data/verified_sources/lee_see_2004_items.json` (Lee & See, 2004).
- **Configuration**: `code/analysis/config.yaml` (merged with `code/analysis/config_user.yaml`).

## 3. Sensitivity Analysis Parameters
The following parameters define the sensitivity sweep ranges used to test the stability of the primary analysis results. These values are sourced from `code/analysis/config_defaults.yaml` and may be overridden by user configuration.

### 3.1 Attention Thresholds
Minimum percentage of attention check questions required to pass.
- **Range**: [70, 80, 90, 95]
- **Default**: 80

### 3.2 Adherence Cutoffs
Minimum percentage of AI recommendations followed to be included in the "Adherent" subgroup.
- **Range**: [70, 80, 90]
- **Default**: 80

### 3.3 Trust Outlier Definition
Z-score threshold for identifying outliers in the `trust_score` distribution.
- **Range**: [2.5, 3.0, 3.5]
- **Default**: 3.0

### 3.4 Straight-lining Detection
Maximum number of consecutive identical responses allowed before flagging as straight-lining.
- **Range**: [4, 5, 6]
- **Default**: 5

## 4. Primary Analysis Workflow

### 4.1 Data Cleaning
1. Load raw CSVs from `data/raw/`.
2. Apply attention check filters based on `attention_thresholds` (Sensitivity Sweep).
3. Flag and exclude straight-lining participants based on `straightlining_threshold` (Sensitivity Sweep).
4. Identify and exclude trust outliers based on `trust_outlier_z` (Sensitivity Sweep).
5. Output cleaned dataset to `data/processed/cleaned_data.csv`.

### 4.2 Manipulation Check (Mandatory Gate)
- **Test**: One-Way ANOVA on `Perceived_Agency_Score` by `Condition`.
- **Criterion**: If p > 0.05, the manipulation is considered failed. The analysis pipeline **HALTS** immediately. No further trust analysis is performed.
- **Output**: `results/manipulation_check.json`.

### 4.3 Cognitive Load Check
- **Test**: One-Way ANOVA on `Cognitive_Load_Score` by `Condition`.
- **Decision**: If p < 0.05, `Cognitive_Load_Score` is included as a covariate in the main analysis (ANCOVA). Otherwise, standard ANOVA is used.
- **Output**: `results/cognitive_load_check.json`.

### 4.4 Primary Statistical Test
- **Omnibus Test**: One-Way ANOVA on `trust_score` by `Condition`.
- **Planned Contrasts**: Execute regardless of Omnibus significance.
 - Contrast 1 (High vs. Low): Vector `[1, -1, 0]`
 - Contrast 2 ((High+Low) vs. Control): Vector `[0.5, 0.5, -1]`
- **Post-Hoc Tests**:
 - **Tukey HSD**: Computed only if Omnibus p < 0.05.
 - **Holm-Bonferroni**: Applied to the unified set of 5 tests (2 planned + 3 pairwise) as the primary family-wise error control method.
- **Output**: `results/omnibus_anova.json`, `results/unified_correction.json`.

## 5. Robustness & Reporting
- **Sensitivity Sweep**: Re-run primary analysis for every combination of sensitivity parameters defined in Section 3.
- **Output**: `results/sensitivity_sweep.csv`.
- **Final Report**: Compile all results into `docs/report.md`, including:
 - Power analysis status (Pre-study and Achieved).
 - Primary findings (ANOVA, Contrasts, Post-hoc).
 - Sensitivity analysis stability summary.
 - Limitations (e.g., insufficient power if achieved power < 0.80).

## 6. Version Control
This protocol is version-controlled. Any changes to the sensitivity parameters or statistical methods must be documented in a new version of this file and reflected in `code/analysis/config.yaml`.