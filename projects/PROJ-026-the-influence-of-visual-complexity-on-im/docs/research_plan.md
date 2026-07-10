# Research Plan: Visual Complexity and Implicit Bias

## 1. Introduction

This project investigates whether the visual complexity of background stimuli influences implicit bias scores (D-scores) in Implicit Association Tests (IAT).

## 2. Hypotheses

- **H1**: There is a significant difference in D-scores between Low, Medium, and High visual complexity conditions.
- **H2**: Visual complexity metrics (Edge Density, Entropy, Fractal Dimension) are positively correlated with cognitive load, potentially affecting response times.

## 3. Methodology

### 3.1 Stimuli
A diverse set of background images will be categorized into three levels of visual complexity based on quantitative metrics:
- **Edge Density**: Proportion of edge pixels (Canny).
- **Entropy**: Information content of the grayscale histogram.
- **Fractal Dimension**: Complexity of self-similar patterns (Box-counting).

### 3.2 Procedure
Participants will complete an IAT task with background images from the categorized sets. The order of complexity conditions will be counterbalanced (Low-High vs. High-Low) to control for fatigue effects.

### 3.3 Data Analysis
- **Primary**: Permutation Test to compare mean D-scores across complexity groups.
- **Secondary**: Sensitivity Analysis (LOIO, Threshold Sweep) to ensure robustness.
- **Power**: Post-hoc power calculation to assess study sensitivity.

## 4. Implementation Phases

### Phase 1: Setup
- Project structure, dependencies, and configuration.

### Phase 2: Foundational
- Data models, logging, and directory setup.

### Phase 3: User Story 1 (Stimuli)
- Implement metrics and batch processing.

### Phase 4: User Story 2 (Data)
- D-score aggregation and trial filtering.

### Phase 5: User Story 3 (Analysis)
- Permutation test, sensitivity analysis, and visualization.

## 5. Deliverables

- **Code**: Fully functional Python pipeline.
- **Data**: Processed complexity scores and D-scores.
- **Results**: JSON files with statistical outcomes and publication-quality plots.
- **Documentation**: Comprehensive README, API reference, and methodology notes.

## 6. Timeline

- **Setup & Foundation**: 1-2 days
- **US1 (Stimuli)**: 2-3 days
- **US2 (Data)**: 2-3 days
- **US3 (Analysis)**: 3-4 days
- **Polish & Testing**: 1-2 days

## 7. Risks and Mitigations

- **Risk**: Small sample size leading to low power.
 - *Mitigation*: Post-hoc power analysis; consider effect size estimation.
- **Risk**: Stimulus-set confounds.
 - *Mitigation*: Permutation test design and LOIO sensitivity analysis.
- **Risk**: Computational constraints (CPU-only).
 - *Mitigation*: Optimize image processing loops; limit permutation count.
