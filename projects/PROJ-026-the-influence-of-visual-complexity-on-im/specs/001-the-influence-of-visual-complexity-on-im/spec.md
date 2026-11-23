# Specification: The Influence of Visual Complexity on Implicit Bias

**Project ID**: PROJ-026
**Version**: 1.1 (Amended)
**Status**: Active

## 1. Introduction

This project investigates the relationship between visual complexity of background images and implicit bias as measured by the Implicit Association Test (IAT).

## 2. Functional Requirements

- **FR-001**: The system must compute visual complexity metrics (edge density, entropy, fractal dimension) for input images.
- **FR-002**: The system must categorize images into Low and High complexity groups using a median split.
- **FR-003**: **Amended** - The system must perform a **Permutation Test** (n=1000) to assess the significance of the difference in D-scores between complexity conditions.
 - *Note*: See **Amendment 001** (`amendment-001.md`) for the official replacement of the original Repeated-Measures ANOVA requirement.
- **FR-004**: The system must calculate and report effect sizes (Cohen's d, partial η²) alongside the permutation p-value.
- **FR-005**: The system must generate publication-quality visualizations of the results.

## 3. Data Models

- **ImageStimulus**: Metadata for background images including complexity metrics.
- **ParticipantResponse**: Raw response data from IAT sessions.
- **AggregatedScore**: Derived D-scores per participant/session.

## 4. Analysis Pipeline

1. **Stimulus Processing**: Validate, filter, and compute metrics for images.
2. **Data Collection**: Load response logs, filter trials, calculate D-scores.
3. **Statistical Analysis**: Run Permutation Test, Sensitivity Analysis (Threshold + LOIO), and Power Analysis.
4. **Visualization**: Generate boxplots and sensitivity charts.

## 5. References

- Plan.md
- Amendment 001: `amendment-001.md`