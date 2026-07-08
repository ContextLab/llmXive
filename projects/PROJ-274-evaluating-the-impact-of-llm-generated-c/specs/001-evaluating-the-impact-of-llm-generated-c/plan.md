# Implementation Plan: Evaluating the Impact of LLM-Generated Code Documentation on Developer Onboarding

**Branch**: `001-evaluating-llm-docs-impact` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-evaluating-llm-docs-impact/spec.md`

## Summary

This project implements a controlled experimental pipeline to evaluate the impact of LLM-generated code documentation versus human-written or no documentation on developer onboarding time and effort. The technical approach involves: (1) a documentation generation pipeline using LLMs pinned to specific repository commits; (2) a data collection system for tracking participant metrics (time, questions, ratings); and (3) a statistical analysis engine performing **Linear Mixed-Effects Models (LMM)** to account for repository difficulty as a random effect. All components are designed to run on CPU-only free-tier CI with strict memory constraints.

**Study Scope**: This is a **Pilot/Feasibility Study**. The sample size (N=15-20) is intentionally small to test the pipeline and estimate effect sizes. It is **not** statistically powered to detect medium effects (f=0.25) with high power (requires N≈159). The primary goal is to estimate effect sizes and variance components to power a future full-scale study.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `requests`, `pandas`, `scipy`, `statsmodels`, `scikit-learn`, `openai`, `transformers`, `llama-cpp-python`, `tiktoken`, `pyyaml`  
**Storage**: Local JSON/CSV files in `data/` (no external database required for this scale)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Research pipeline / CLI tool  
**Performance Goals**: Analysis pipeline < 6 hours, RAM < 7GB (Analysis phase only; Generation phase is context-window limited)  
**Constraints**: No GPU, no heavy LLM training, strict reproducibility (random seeds, commit pinning), CPU-only fallback for LLM generation.  
**Scale/Scope**: ~15-20 participants (Pilot), ~3-5 repositories (≤ 500 files each)

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: Plan ensures all random seeds are pinned, external datasets (if any) are fetched from canonical sources, and repository commits are pinned by hash.
- **II. Verified Accuracy**: All citations in `research.md` will be verified against the "# Verified datasets" block. No fabricated URLs.
- **III. Data Hygiene**: Raw data will be checksummed; transformations will produce new files; PII will be anonymized.
- **IV. Single Source of Truth**: All statistics in the final report will trace back to `data/` rows and `code/` scripts.
- **V. Versioning Discipline**: Artifacts will carry content hashes; `state/` will be updated on changes.
- **VI. Human Subjects Compliance**: Plan references IRB protocols located at `data/raw/irb_protocol.pdf`. Anonymization is performed before analysis scripts access the dataset.
- **VII. Generation Traceability**: LLM configuration (model, temp, prompt) will be logged and checksummed alongside generated docs.

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-llm-docs-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/
├── code/
│   ├── __init__.py
│   ├── config.py              # Configuration & seed pinning
│   ├── data_collection.py     # Participant logging & metrics
│   ├── doc_generation.py      # LLM documentation pipeline
│   ├── analysis.py            # Statistical tests (LMM) & reporting
│   ├── validation.py          # Contract validation & rubric checks
│   └── utils.py               # Helper functions
├── data/
│   ├── raw/                   # Raw participant logs, generated docs, IRB docs
│   ├── processed/             # Cleaned datasets for analysis
│   └── checksums.txt          # Artifact hashes
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure chosen to simplify data flow and testing for a research pipeline. No frontend/backend split needed as the system is CLI-driven with human moderation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed with no violations. | N/A |

## Implementation Phases

### Phase 0: Repository Selection & Rubric Validation
*Addresses FR-009 and Concern spec_coverage-ef58c7f1*
1. **Select Repositories**: Identify 3-5 open-source repositories (≤ 500 files).
2. **Verify Human Docs**: Apply a rubric to verify existing human documentation quality.
   - *Criteria*: Must have setup instructions, API reference, and architectural overview.
   - *Action*: If a repo fails the rubric, it is excluded or the 'Human' condition is adjusted.
3. **Pin Commits**: Record the specific commit hash for each repo to ensure consistency between generation and study.
4. **Output**: `data/raw/repo_selection_rubric.json` (checksummed).

### Phase 1: Documentation Generation Pipeline
*Addresses FR-002, FR-008*
1. **Generate LLM Docs**: Run `doc_generation.py` for selected repos.
   - *Primary*: API-based LLM (e.g., OpenAI).
   - *Fallback*: Local model (e.g., `llama-3-8b` via `llama-cpp-python`) if API fails (FR-008).
2. **Verify Parity**: Ensure 'Human' condition uses the *exact* same repo artifacts as 'LLM' target to prevent confounding.
3. **Log Config**: Record model name, temperature, prompt, and commit hash.
4. **Output**: `data/raw/llm_docs/`, `data/raw/llm_config.yaml`.

### Phase 2: Data Collection & Intervention Logic
*Addresses FR-003, FR-004, Edge Cases*
1. **Recruit & Assign**: Randomly assign N=15-20 participants to conditions (LLM, Human, None).
2. **Execute Tasks**: Participants complete standardized onboarding tasks.
3. **Moderator Intervention (Stop-Loss)**:
   - *Trigger*: If LLM docs are unusable or participant is stuck.
   - *Action*: Log `intervention_flag=True`, `failure_reason="poor_docs"`, and cap time or mark as failed.
4. **Log Metrics**: Record start/end times, question counts, ratings.
5. **Output**: `data/raw/participant_logs.json`.

### Phase 3: Contract Validation & Data Processing
*Addresses Concern plan_consistency-58b792d5*
1. **Validate Schema**: Run `validation.py` to check `data/raw/participant_logs.json` against `contracts/dataset.schema.yaml`.
   - *Fail*: If schema mismatch, halt and report.
2. **Anonymize**: Remove PII, map to `participant_id`.
3. **Clean**: Handle incomplete/failed records (exclude from primary time analysis, retain for dropout reporting).
4. **Output**: `data/processed/cleaned_dataset.csv`.

### Phase 4: Statistical Analysis (LMM)
*Addresses FR-005, FR-006, Concerns methodology-f00e2e9d, scientific_soundness-120d0222*
1. **Model Selection**: Fit a **Linear Mixed-Effects Model (LMM)**:
   - *Fixed Effects*: Condition (LLM, Human, None).
   - *Random Effects*: Repository (to control for difficulty).
   - *Alternative*: If assumptions fail, use Non-parametric Aligned Rank Transform (ART) ANOVA with blocking.
2. **Post-Hoc**: Apply Tukey HSD (or equivalent for LMM) with family-wise error correction.
3. **Power Analysis**: Calculate observed power and effect sizes (Cohen's f, partial eta-squared).
   - *Note*: Explicitly report that N=15-20 is underpowered for medium effects.
4. **Output**: `data/reports/analysis_results.json`, `data/reports/final_report.md`.

### Phase 5: Reporting
*Addresses FR-007*
1. **Generate Report**: Summarize means, SDs, p-values, effect sizes, and power limitations.
2. **Verify**: Ensure all stats trace to `data/processed/cleaned_dataset.csv`.
3. **Output**: Final research report.

## Resource Constraints & Feasibility

- **RAM**: Analysis phase (LMM on N=20) requires <100MB. The 7GB limit is **irrelevant** for the statistical analysis phase but constrains the *generation* phase (context window limits).
- **Runtime**: LMM and data processing complete in <1 hour. Generation phase is the bottleneck (LLM API latency).
- **CPU**: All statistical tests and data processing run on CPU. Local model fallback uses CPU-optimized `llama-cpp-python`.
- **Power**: Explicitly acknowledged as a limitation. The study is a pilot to estimate parameters for a future study with a sample size.

