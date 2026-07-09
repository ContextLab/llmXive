# Architecture Decision Records

## ADR-001: Project Structure
**Status**: Accepted
**Date**: 2023-10-27

### Context
The project requires a clean separation of concerns between data ingestion, preprocessing, model training, and analysis.

### Decision
We will adopt a modular `code/` directory structure with clear separation:
- `ingestion.py`: Data fetching and cleaning
- `preprocessing.py`: Feature engineering
- `training.py`: Model training
- `evaluation.py`: Model assessment
- `explainability.py`: SHAP and sensitivity analysis

### Consequences
- Clear boundaries for unit testing
- Easier parallel development
- Simplified dependency management
