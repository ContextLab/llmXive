# Project Plan: The Influence of Visual Aesthetics on Perceived Credibility of Online Information

## Overview
This project investigates how visual design fidelity (Professional, Minimalist, Low-Quality, Neutral) impacts the perceived credibility and professionalism of online information.

## Objectives
1. Create a web-based survey platform (Streamlit) to present stimuli.
2. Collect participant ratings on credibility and professionalism.
3. Analyze data using Repeated-Measures ANOVA and Mixed-Effects models.
4. Ensure strict adherence to IRB guidelines and data privacy (hashed IPs, no client-side PII).

## Project Structure
The project follows a standard scientific Python layout:
- `code/`: Source code for the survey app and analysis pipelines.
- `data/`: Raw data collections and processed analysis results.
- `tests/`: Unit and integration tests.
- `specs/`: Feature specifications and design documents.
- `docs/`: Supporting documentation (IRB protocols, stimulus design).

## Technology Stack
- **Language**: Python 3.11
- **Frontend**: Streamlit (for survey delivery)
- **Data Processing**: Pandas, NumPy
- **Statistics**: SciPy, Statsmodels
- **Configuration**: PyYAML

## Phase Breakdown
- **Phase 1: Setup**: Project initialization, requirements, linting.
- **Phase 2: Foundational**: Stimuli creation, directory structure, utility functions.
- **Phase 3: User Story 0**: Informed Consent Workflow.
- **Phase 4: User Story 1**: Data Collection (Survey, Latin Square, CSV Export).
- **Phase 5: User Story 2**: Statistical Analysis (ANOVA, Post-hoc).
- **Phase 6: User Story 3**: Robustness Checks (Mixed-Effects).
- **Phase 7: Polish**: Testing and documentation.

## Ethical Considerations
- IRB approval required before data collection.
- No raw IP addresses stored; immediate hashing required.
- No client-side storage of PII.
- Clear withdrawal mechanism.
