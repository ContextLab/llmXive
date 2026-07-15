# Design Document: Accessibility and Usability Research Pipeline

## 1. Introduction
This document outlines the architectural design of the research pipeline for evaluating XAI interfaces in complex computer systems for people with disabilities. The system is designed to be reproducible, statistically rigorous, and extensible.

## 2. System Architecture

### 2.1 Components
- **Simulator Module**: Handles interface rendering and user interaction simulation.
- **Data Collection Module**: Captures metrics and logs session data.
- **Analysis Module**: Performs statistical tests and generates summaries.
- **Visualization Module**: Creates plots and reports.
- **Configuration Module**: Manages project settings and environment variables.

### 2.2 Data Flow
1. **Initialization**: `setup/init_project.py` creates directory structure and dependencies.
2. **Simulation**: `simulator/app.py` runs sessions, collecting metrics via `metrics_collector.py`.
3. **Logging**: Raw data is saved to `data/raw/session_{id}.json` with checksums.
4. **Analysis**: `analysis/run_analysis.py` cleans data, runs tests, and outputs summaries.
5. **Reporting**: `analysis/run_report.py` generates visualizations and final reports.

## 3. Interface Design

### 3.1 Traditional Interface
- Standard UI without XAI overlays.
- Implemented in `simulator/interfaces/traditional.py`.

### 3.2 Explainable Interface
- Includes XAI overlays (heatmaps, rule-based explanations).
- Implemented in `simulator/interfaces/explainable.py`.
- Configurable via `simulator/xai_wrapper.py` to support different algorithms (SHAP, LIME, Rule-Based).

## 4. Data Management

### 4.1 Raw Data
- Stored in `data/raw/` as JSON files.
- Includes checksums for integrity verification.
- Immutable once written.

### 4.2 Processed Data
- Stored in `data/processed/` as CSV files.
- Includes cleaned metrics, statistical summaries, and descriptive statistics.

### 4.3 Data Models
- **Participant**: Represents a study participant.
- **Session**: Represents a single test session.
- **Metric**: Represents aggregated statistical results.

## 5. Statistical Methodology

### 5.1 Normality Testing
- Shapiro-Wilk test on difference scores between interface variants.

### 5.2 Inferential Analysis
- Repeated Measures ANOVA for Completion Time, Error Count, and SUS scores.
- Holm-Bonferroni correction for multiple comparisons.

### 5.3 Descriptive Statistics
- Mean and standard deviation for all metrics.
- `explanation_engagement_time` is descriptive only.

## 6. Reproducibility
- Random seeds are fixed via `utils/seed.py`.
- All analysis steps are documented in `code/analysis.ipynb`.
- Checksums ensure data integrity.

## 7. Extensibility
- New interface variants can be added by implementing the `Interface` protocol.
- New statistical tests can be added to `analysis/stat_utils.py`.
- Configuration is centralized in `config/settings.py`.

## 8. Security and Privacy
- Participant data is anonymized (no PII stored).
- Data access is controlled via file permissions.
- Logs do not contain sensitive information.
