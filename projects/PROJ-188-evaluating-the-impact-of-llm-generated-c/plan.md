# Project Plan: Evaluating the Impact of LLM-Generated Code Explanations on Comprehension

## Overview

This project investigates how LLM-generated code explanations affect developer comprehension compared to official docstrings and code-only conditions. The study uses the CodeSearchNet corpus, generates explanations using CodeLlama-7B (with TinyLlama fallback), and analyzes results using a Linear Mixed Model (LMM).

## Objectives

1. Curate a dataset of Python code snippets from CodeSearchNet with complexity labels.
2. Generate LLM explanations for these snippets, adhering to token limits and model fallback strategies.
3. Construct a simulated survey to test comprehension under three conditions: Code Only, Code+LLM Explanation, Code+Official Docstring.
4. Analyze the data using a Linear Mixed Model (LMM) to determine the impact of explanation type and code complexity on comprehension.
5. Assess the robustness of results via BLEU sensitivity analysis.

## User Stories

### US1: Dataset Curation and Explanation Generation
- Ingest CodeSearchNet corpus.
- Calculate and label cyclomatic complexity.
- Generate LLM explanations with fallback logic.
- Validate data quality (token counts, labels, N>=20).

### US2: Study Survey Construction and Deployment
- Implement participant randomization.
- Render survey conditions (Code Only, Code+LLM, Code+Docstring).
- Simulate/mock survey responses for testing.
- Ingest real/mock data and calculate missing counts.

### US3: Statistical Analysis and Robustness Reporting
- Clean and filter participant data.
- Fit Linear Mixed Model (LMM) with participant-only random intercepts.
- Perform post-hoc Tukey HSD tests.
- Conduct BLEU sensitivity sweep.
- Generate final report with F-statistics, p-values, and limitations.

## Technical Architecture

### Directory Structure
```
PROJ-188-evaluating-the-impact-of-llm-generated-c/
├── code/
│ ├── utils/
│ │ ├── config.py
│ │ ├── metrics.py
│ │ └── env_loader.py
│ ├── 01_data_curation.py
│ ├── 02_survey_logic.py
│ ├── 03_analysis.py
│ └──... (other utility scripts)
├── data/
│ ├── raw/
│ ├── intermediate/
│ │ ├── explanations.json
│ │ ├── survey_conditions.json
│ │ ├── mock_responses.csv
│ │ └── responses.csv
│ ├── processed/
│ │ ├── sensitivity_report.csv
│ │ ├── analysis_results.json
│ │ └── final_report.md
│ └── analysis_notes.md
├── tests/
│ ├── test_curation.py
│ └── test_analysis.py
├── requirements.txt
└── README.md
```

### Key Dependencies
- Python 3.11
- `transformers`, `torch`, `scikit-learn`, `statsmodels`, `sacrebleu`, `datasets`, `pandas`, `numpy`, `pyyaml`, `python-dotenv`

## Statistical Model Selection (Updated)

**Decision**: The project will use a **Linear Mixed Model (LMM)** as mandated by **Spec FR-005**.

**Rejection of GLMM**: Although the initial plan considered a Generalized Linear Mixed Model (GLMM) with random effects for both `participant_id` and `snippet_id` to control for variability in both dimensions, this approach was **explicitly rejected**. The rejection is based on the strict requirement in **Spec FR-005** to use an LMM with *participant-only* random intercepts. Deviating from this specification would require a formal amendment to the project plan and analysis protocol, which has not been requested. Therefore, the analysis will proceed with the LMM specified in FR-005.

**Model Formula**: `answer ~ condition * complexity + (1|participant_id)`
**Family**: Gaussian

## Risk Management

- **Model Loading**: CodeLlama-7B may fail to load on CPU or exceed memory. Mitigation: Implement fallback to TinyLlama-1.1B.
- **Data Quality**: Generated explanations may be nonsensical. Mitigation: Validate token counts and content before analysis.
- **Statistical Power**: Small sample size may lead to low power. Mitigation: Use LMM to maximize power with repeated measures; report effect sizes.

## Timeline

- **Phase 0**: Governance & Prerequisites (T000a)
- **Phase 1**: Setup (T001a-T001d)
- **Phase 2**: Foundational (T002-T008, T015b)
- **Phase 3**: US1 Implementation (T012-T017)
- **Phase 4**: US2 Implementation (T018-T022b)
- **Phase 5**: US3 Implementation (T023-T030)
- **Phase N**: Polish & Cross-Cutting (T031-T035)

## Governance

- **Constitution Principle VII**: Requires StarCoder-15B.
- **Spec FR-001**: Requires CodeLlama-7B.
- **Resolution**: Amendment T000a approved to align Spec FR-001 with Constitution Principle VII by updating the model requirement to CodeLlama-7B with a token limit of 200, or updating the Constitution. (Note: The task description implies the amendment resolved the conflict in favor of CodeLlama-7B with constraints).
- **Statistical Model**: Spec FR-005 mandates LMM. Plan updated to reflect rejection of GLMM rationale.

## Success Criteria

- Successfully generate `data/intermediate/explanations.json` with N>=20 valid entries.
- Successfully simulate/mock survey data in `data/intermediate/responses.csv`.
- Successfully run LMM analysis and produce `data/processed/final_report.md` with required metrics.
- All unit and integration tests pass.