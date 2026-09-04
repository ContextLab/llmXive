# Implementation Plan: The Influence of Chatbot Politeness on User-Perceived Quality

**Branch**: `001-chatbot-politeness-trust` | **Date**: 2026-06-26 | **Spec**: `spec.md`

## Summary

This feature implements a statistical pipeline to test the **association** between linguistic politeness in chatbot responses and user-perceived quality (used as a validated proxy for 'trust'). The approach involves downloading **three** datasets—**HCI_P2**, **Persona-Chat**, and **EmpatheticDialogues**—filtering dialogues for completeness, computing mean politeness scores per conversation using the `jfiedler/politeness-bert` model, and fitting a Cumulative Link Mixed-Effects Model (CLMM) to estimate the effect of politeness on quality ratings while controlling for conversation length, sentiment, and user-level random effects. Robustness checks using a lexicon-based classifier (Politeness Corpus) and subgroup analyses (age/gender) follow. The pipeline adheres to GitHub Actions free-tier constraints (CPU-first, ~7GB RAM) and strictly follows the project constitution regarding data hygiene and reproducibility.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets`, `transformers`, `scikit-learn`, `ordinal`, `pandas`, `numpy`, `scipy`, `pyyaml`, `python-dotenv`, `simr` (for power analysis logic)  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `results`), CSV/Parquet formats.  
**Testing**: `pytest` (unit tests for data loading, schema validation; integration tests for pipeline execution).  
**Target Platform**: Linux (GitHub Actions runner), CPU-only (with fallback to Kaggle GPU if `transformers` inference exceeds memory, though `politeness-bert` is designed for CPU).  
**Project Type**: Data analysis pipeline / Research script.  
**Performance Goals**: Full pipeline execution < 6 hours on 2-core CPU; Memory peak < 7GB.  
**Constraints**: No external credentials for gated datasets; all data must be downloadable via public URL; statistical methods must handle ordinal outcomes correctly (CLMM).  
**Scale/Scope**: ~30k dialogues (estimated across three datasets); A primary model, a robustness model, and multiple subgroup models

The research question remains: [Research Question]
The method remains: [Method]
The references remain: [References].

> **Dataset Constraint Resolution**: The spec mandates downloading **Persona-Chat** and **EmpatheticDialogues** (FR-001). The previous draft incorrectly excluded them due to a missing "Verified Datasets" block in the draft. This plan has been revised to include **all three datasets** (HCI_P2, Persona-Chat, EmpatheticDialogues) using their canonical, verified Hugging Face repositories. The pipeline is designed to merge and harmonize data from all three sources.

## Constitution Check

| Principle | Status | Action/Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ | Random seeds pinned in `code/`; datasets fetched from canonical HF URLs; `requirements.txt` provided. |
| **II. Verified Accuracy** | ✅ | Citations in `research.md` limited to verified URLs; no fabricated dataset links. |
| **III. Data Hygiene** | ✅ | Raw data checksummed; no in-place modification; derived files versioned. |
| **IV. Single Source of Truth** | ✅ | All stats trace to `data/processed` and `code/`; no hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | ✅ | Artifacts hashed; state updated on change. |
| **VI. Psychometric Measurement Validity** | ✅ | **Resolved**: `quality_rating` is used as a proxy for 'trust' with explicit citation to HCI literature (Nass & Moon, 2000; Bickmore & Picard, 2005) validating the correlation in conversational agents. |
| **VII. Linguistic Feature Extraction** | ✅ | `jfiedler/politeness-bert` version pinned; applied uniformly to all utterances. |

## Project Structure

### Documentation (this feature)

```text
specs/001-chatbot-politeness-trust/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── output.schema.yaml
    └── config.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-755-the-influence-of-chatbot-politeness-on-u/
├── code/
│   ├── __init__.py
│   ├── main.py                 # Entry point, orchestrates pipeline
│   ├── config.py               # Loads .env, validates config
│   ├── data/
│   │   ├── loader.py           # Downloads and parses HCI_P2, Persona-Chat, EmpatheticDialogues
│   │   ├── preprocess.py       # Filtering, politeness scoring, merging
│   │   └── utils.py            # Helper functions
│   ├── analysis/
│   │   ├── clmm.py             # CLMM fitting and diagnostics
│   │   ├── robustness.py       # Lexicon classifier and subgroup analysis
│   │   ├── power_analysis.py   # MDE estimation
│   │   └── metrics.py          # Convergence checks, effect size calc
│   ├── utils/
│   │   ├── schema_validator.py # Validates outputs against contracts
│   │   └── logging.py          # Structured logging
│   └── requirements.txt
├── data/
│   ├── raw/                    # Downloaded raw files (checksummed)
│   └── processed/              # Cleaned CSVs with scores
├── results/                    # Model outputs, plots, logs
├── .env.example                # Template for HF_TOKEN
└── tests/
    ├── test_loader.py
    ├── test_preprocess.py
    └── test_schema.py
```

**Structure Decision**: Single project structure under `code/` is chosen for simplicity. The analysis is linear (Download → Score → Model → Report), so a flat `code/` directory with submodules for `data`, `analysis`, and `utils` is sufficient. No separate frontend/backend is needed.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **CLMM vs GLM** | The outcome (`quality_rating`) is ordinal (Likert scale).. A standard linear regression (GLM) would violate assumptions of interval data and normality of residuals. CLMM is required for valid inference on ordinal outcomes. | Using a simple linear regression would produce biased standard errors and incorrect p-values for ordinal data. |
| **Mixed-Effects** | Users contribute multiple dialogues. Ignoring user-level clustering (random effects) would violate independence assumptions, inflating Type I error. | A standard CLM (without random effects) would treat repeated measures from the same user as independent, leading to false positives. |
| **Robustness Check (Lexicon)** | To ensure findings are not an artifact of the specific BERT model architecture. | Relying on a single model risks model-specific bias; a lexicon-based approach provides a conceptual baseline. |
| **Multi-Dataset** | Spec FR-001 mandates Persona-Chat and EmpatheticDialogues. | Using only HCI_P2 would violate the spec and limit generalizability. |