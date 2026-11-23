# Predicting the Impact of Residual Stress on Fatigue Life

This research project investigates the extent to which residual stress mediates the relationship between manufacturing process parameters and fatigue life across different material classes (specifically steels and aluminum alloys). It also evaluates the predictive value added by explicitly modeling residual stress compared to direct process-to-fatigue modeling.

## Research Question
To what extent does residual stress mediate the relationship between manufacturing process parameters and fatigue life across different material classes, and how much predictive value does stress-mediated estimation add beyond direct process-to-fatigue modeling?

## Data Sources
The pipeline ingests public fatigue datasets from the following repositories:
- **NIST Materials Data Repository**
- **UCI Machine Learning Repository**
- **OpenML**

## Project Structure
- `code/`: Source code for ingestion, preprocessing, modeling, and mediation analysis.
- `data/`: Raw and processed datasets.
- `results/`: Output tables, logs, and figures.
- `tests/`: Unit and integration tests.
- `scripts/`: Orchestration scripts for environment checks and pipeline execution.

## Getting Started
For detailed setup and execution instructions, please refer to the [Quickstart Guide](quickstart.md).
