# Implementation Plan: Evaluating the Impact of LLM-Generated Code Explanations

**Branch**: `001-evaluating-the-impact-of-llm-generated-c` | **Date**: 2026-07-14 | **Spec**: `specs/001-evaluating-the-impact-of-llm-generated-c/spec.md`
**Input**: Feature specification from `/specs/001-evaluating-the-impact-of-llm-generated-c/spec.md`

## Summary

This project implements a **pipeline validation study** to evaluate the feasibility of a future study on how LLM-generated code explanations affect code comprehension. The system will curate a dataset of code snippets, generate explanations using TinyLlama-1.1B (primary for CPU) with CodeLlama-7B fallback (if GPU available), deploy a three-condition survey (Code Only, Code+LLM, Code+Docstring) using **simulated (mock) participant data**, and analyze the data using a Linear Mixed Model (LMM) with participant-only random intercepts as mandated by FR-005.

**Important Scope Note**: This phase uses **mock data** to validate the data engineering, statistical pipeline, and reproducibility constraints (CPU/Time). It does **not** collect real human subject data (US2) or draw definitive causal conclusions about comprehension (US3). The research question regarding "causal impact" is a hypothesis to be tested in a future phase with IRB-approved real data. This plan validates the *method* to test that hypothesis.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `datasets`, `pandas`, `statsmodels`, `scikit-learn`, `sacrebleu`, `seaborn`, `matplotlib`, `bitsandbytes`  
**Storage**: Local filesystem (`data/raw`, `data/intermediate`, `data/processed`) with checksums recorded in `state/`  
**Testing**: `pytest` (unit tests for data processing, integration tests for survey logic)  
**Target Platform**: Linux (GitHub Actions free-tier: a modest number of CPU cores, ~7 GB RAM)  
**Project Type**: Research pipeline / Data analysis (Pilot)  
**Performance Goals**: Process ~100 code snippets and ~500 mock responses within 2 hours; analysis < 30 mins.  
**Constraints**: Must run on CPU; no GPU available for generation (use quantized TinyLlama as primary); strict PII removal; strict adherence to Spec FR-001 (CodeLlama) and FR-005 (LMM).  
**Scale/Scope**: A subset of code snippets from HumanEval, A cohort of mock participants, conditions.

> **Governance Resolution (Constitution vs. Spec)**: The project Constitution (Principle VII) mandates StarCoder-15B, but the Spec (FR-001) mandates CodeLlama-7B. Per the Constitution's "Governance" clause, a formal amendment (Task T000b) is required to update `constitution.md` to authorize CodeLlama-7B. **This plan assumes T000b is completed successfully before execution.** If T000b is not completed, the plan defaults to StarCoder-15B (if feasible) or halts. For the purpose of this CPU-bound run, TinyLlama-1.1B is selected as the primary model to ensure feasibility, with CodeLlama-7B as a fallback if the GPU escape hatch is triggered.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **I. Reproducibility**: All random seeds pinned in `code/`. External datasets fetched from canonical sources. `requirements.txt` pins versions.
2.  **II. Verified Accuracy**: All citations (e.g., for BLEU, LMM) will be verified against primary sources.
3.  **III. Data Hygiene**: All `data/` files checksummed. Raw data immutable. Derivations produce new files. PII scan passed.
4.  **IV. Single Source of Truth**: All stats in `final_report.md` trace to `data/processed/results.csv` and `code/05_analysis.py`.
5.  **V. Versioning**: Artifacts hashed. `state/` updated on change.
6.  **VI. Human-Subject Data Integrity**: Responses anonymized (no PII). Filtering rules (<30s) applied via script. *Note: Current data is mock; this rule applies to future real data.*
7.  **VII. Controlled Explanation Generation**: **RESOLVED**: The Spec (FR-001) mandates CodeLlama-7B. The Constitution (Principle VII) mandates StarCoder-15B. This conflict is resolved by **Task T000b** (Amendment). The plan proceeds with TinyLlama-1.1B (CPU feasible) and CodeLlama-7B (fallback) as the implementation of the Spec's intent, pending the amendment artifact.

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-impact-of-llm-generated-c/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── analysis.schema.yaml
│   ├── analysis_result.schema.yaml
│   ├── bleu_sensitivity.schema.yaml
│   ├── explanation.schema.yaml
│   ├── participant_response.schema.yaml
│   ├── participant_summary.schema.yaml
│   ├── response.schema.yaml
│   └── snippet.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/001-evaluating-the-impact-of-llm-generated-c/
├── code/
│   ├── 01_data_curation.py       # Snippet loading, complexity labeling
│   ├── 02_explanation_gen.py     # LLM generation (TinyLlama primary, CodeLlama fallback)
│   ├── 03_survey_logic.py        # Mock data generation, survey condition logic
│   ├── 04_data_cleaning.py       # PII removal, filtering (<30s), missing_count calc
│   ├── 05_analysis.py            # LMM, Tukey HSD, BLEU descriptive analysis
│   ├── 06_report_gen.py          # Final report assembly
│   ├── utils/
│   │   ├── config.py             # Env var loading (HF_TOKEN, etc.)
│   │   └── logging.py            # Centralized logging setup
│   └── requirements.txt
├── data/
│   ├── raw/                      # Original code snippets (if external)
│   ├── intermediate/
│   │   ├── explanations.csv      # Generated explanations
│   │   ├── mock_responses.csv    # Mock survey data (row-level)
│   │   ├── participant_summary.csv # Aggregate participant stats (includes missing_count)
│   │   └── cleaned_responses.csv # Filtered, anonymized data
│   └── processed/
│       ├── results.csv           # LMM output, stats
│       └── final_report.md       # Final deliverable
└── tests/
    ├── unit/
    └── integration/
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) is sufficient for this research pipeline. No frontend/backend split required as the "survey" is simulated via mock data generation for the pipeline validation phase.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| LMM with Participant Random Intercepts (FR-005) | Required by Spec FR-005 to account for individual differences. | Fixed-effects only model would ignore participant variability. |
| BLEU Descriptive Analysis (FR-009) | Required by FR-009 to contextualize explanation quality (limitation statement). | Simple BLEU score alone is insufficient; must report limitations. |
| Model Fallback Logic (TinyLlama/CodeLlama) | Required by FR-001 to ensure robustness. | Hard-failing on generation errors would break the pipeline. |
| **Categorical Complexity** | Required to avoid unvalidated synthetic continuous scores. | Using line count as a continuous covariate introduces construct validity threats. |

## Data Model & Contracts

- **Snippet**: {snippet_id, code, docstring, complexity_score, complexity}
- **Response**: {response_id, participant_id, snippet_id, condition, answer, is_correct, latency_ms, timestamp} (Row-level)
- **ParticipantSummary**: {participant_id, total_responses, missing_count, avg_latency} (Aggregate)
- **Analysis Result**: {threshold, accuracy_mean, latency_mean, p_value_interaction}

*Note: `missing_count` is an aggregate metric stored in `ParticipantSummary`, not in the row-level `Response` entity, to maintain data integrity.*

## Limitations & Validity Threats

1.  **Mock Data**: This study uses simulated responses. Results are indicative of pipeline feasibility, not human comprehension.
2.  **Synthetic Complexity**: Complexity labels are derived from code metrics (lines, cyclomatic), not human ratings. This limits external validity regarding "comprehension difficulty."
3.  **Snippet Variance**: Per FR-005, the model uses participant-only random intercepts, ignoring snippet-level variance. This may inflate Type I error rates.
4.  **Model Feasibility**: TinyLlama is used as the primary model for CPU feasibility. CodeLlama-7B is a fallback.
5.  **BLEU Limitation**: BLEU measures similarity to the docstring (functional description), not pedagogical quality.