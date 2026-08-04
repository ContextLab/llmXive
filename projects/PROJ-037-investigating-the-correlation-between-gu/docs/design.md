# Design Document: Gut Microbiome and Circadian Rhythm Study

## 1. Research Question
Is there an associational relationship between gut microbiome diversity (alpha/beta) and circadian rhythm disruption (sleep duration, quality, chronotype)?

**Important**: This study seeks **associations**, not causation. All conclusions must be framed as correlational.

## 2. Methodology

### 2.1 Data Sources
- **American Gut Project (AGP)**: 16S rRNA sequencing data and metadata (age, BMI, diet, antibiotics).
- **Open Humans**: Sleep metadata (duration, quality, chronotype).

### 2.2 Data Processing
1. **Ingestion**: Download raw data, merge on Participant ID, filter missing values, cap outliers, impute covariates.
2. **Diversity Calculation**: Compute Shannon/Simpson (alpha) and Bray-Curtis (beta) diversity.
3. **Associational Analysis**:
 - Spearman/Pearson correlations (diversity vs. sleep).
 - dbRDA for non-linear relationships.
 - GLM adjusted for confounders (age, BMI, diet, etc.).
 - PERMANOVA for categorical sleep variables.
4. **Validation**:
 - Bootstrap resampling (1000 iterations) for confidence intervals.
 - Sensitivity analysis on significance thresholds.

### 2.3 Statistical Rigor
- **FDR Correction**: Benjamini-Hochberg for all p-values.
- **Confounder Adjustment**: GLM includes age, BMI, diet type, medication, antibiotic history.
- **Associational Framing**: All outputs explicitly state "association" (no causal language).

## 3. Constraints
- **No Causal Claims**: FR-008 compliance mandatory.
- **Real Data Only**: No synthetic data. Pipeline fails if sources are unreachable.
- **CPU-Only**: No GPU dependencies.
- **Sample Size**: Bootstrap skipped if N < 40.

## 4. Output Artifacts
- `data/processed/cohort_merged.csv`: Cleaned cohort.
- `data/outputs/correlation_results.csv`: Statistical results.
- `data/outputs/heatmap.png`, `pcoa_sleep_quality.png`: Visualizations.
- `data/outputs/final_report.md`: Associational report.

## 5. Limitations
- **Diet Timing**: Unavailable in AGP; "diet type" used as a substitute.
- **Missing Data**: Imputed via median/mode; may introduce bias.
- **Cross-Sectional**: Cannot infer temporal relationships.

## 6. Reviewer Feedback
- **Linus Pauling (Simulated)**: "Correlation is necessary but insufficient; we must avoid causal claims." (See `research_question_validation.md`).

## 7. Future Work
- Integrate longitudinal data if available.
- Explore molecular mechanisms (out of scope for this project).
