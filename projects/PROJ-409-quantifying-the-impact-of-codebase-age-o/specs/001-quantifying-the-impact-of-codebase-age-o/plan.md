# Implementation Plan: Quantifying the Impact of Codebase Age on LLM Code Understanding

**Branch**: `001-quantify-age-impact` | **Date**: 2026-06-27 | **Spec**: `specs/001-quantify-age-impact/spec.md`
**Input**: Feature specification from `/specs/001-quantify-age-impact/spec.md`

## Summary

This project investigates the associational relationship between the "age" of code (measured by median commit age of files) and the performance of small-scale CodeLLMs on that code. The technical approach involves three phases: () extracting function-level Python snippets from public repositories and calculating git-based age metrics; (2) running CPU-only inference using a quantized CodeGen-350M model to generate perplexity and syntax validity scores; and (3) performing Spearman rank correlation analysis (controlling for complexity and length) to determine statistical significance. The entire pipeline is designed to execute within the strict GitHub Actions free-tier constraints (2 CPU cores, ~7 GB RAM, ≤6 hours).

**Key Methodological Adjustment**: To address independence concerns, the unit of analysis is the **file**, not the snippet. Metrics are aggregated per file (mean perplexity, syntax validity rate) before correlation. Complexity and length are controlled for as covariates.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `huggingface_hub`, `transformers` (CPU-optimized), `torch` (CPU), `bitsandbytes` (CPU-quantization support), `gitpython`, `pandas`, `scipy`, `ast`, `tokenizers`, `networkx` (for complexity).  
**Storage**: Local filesystem (`.git` clones in temp, CSV/JSON outputs in `data/`). No persistent database.  
**Testing**: `pytest` (unit tests for extraction, inference, and correlation logic).  
**Target Platform**: GitHub Actions `ubuntu-latest` (Linux, 2-core, 7GB RAM).  
**Project Type**: Data analysis pipeline / CLI tool.  
**Performance Goals**: Complete inference for up to 1,000 snippets within 6 hours; memory usage < 7 GB.  
**Constraints**: No GPU/CUDA; strict 6-hour timeout; minimum 800 valid snippets for statistical power; 8-bit/4-bit quantization required for model loading.  
**Scale/Scope**: 3-5 repositories, ~dozens of snippets each, A substantial number of total samples..

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance Strategy |
|------------------------|---------------------|
| **I. Reproducibility** | All random seeds (for sampling and model inference) will be pinned in `code/`. The extraction script will fetch repos via canonical GitHub URLs. The `requirements.txt` will pin exact versions. |
| **II. Verified Accuracy** | Citations for the CodeGen model and statistical methods will be verified against primary sources (HuggingFace, original papers) before inclusion. **Automated Enforcement**: A new script `code/utils/reference_validator.py` will be added to the project. It runs as a pre-commit hook and a CI gate, parsing all markdown artifacts for citations and verifying them against the primary source URLs before allowing the `research_review` transition. |
| **III. Data Hygiene** | Raw repo clones and extracted CSVs will be checksummed. No in-place modification of raw data; derived metrics (perplexity, syntax validity) will be written to new files. PII scanning will be run on extracted code. |
| **IV. Single Source of Truth** | Correlation coefficients in the final report will be generated programmatically from the `data/results/file_analysis.csv` file, not hand-typed. |
| **V. Versioning Discipline** | **Implementation Step**: After each pipeline phase (Extraction, Inference, Analysis), the `code/utils/hasher.py` script will be executed automatically. It generates SHA-256 hashes for all CSV outputs and updates the project state YAML (`state/projects/PROJ-409-...yaml`) with the `artifact_hashes` map. This ensures the Versioning Discipline is enforced by code. |
| **VI. Temporal Metadata Fidelity** | `median_commit_age` will be derived strictly from `git log` timestamps of each file, not inferred. The script will handle sparse history as per spec (edge case). Age is calculated once per file. |
| **VII. Computational Budget Adherence** | The plan explicitly uses a small model (CodeGen-350M) with 8-bit quantization and a 6-hour timeout guardrail. Execution time will be logged and reported. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantify-age-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-409-quantifying-the-impact-of-codebase-age-o/
├── code/
│   ├── __init__.py
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── git_utils.py        # Git history parsing, age calculation (per file)
│   │   ├── snippet_extractor.py # AST-based function extraction
│   │   └── run_extraction.py   # CLI entry point for US-1
│   ├── inference/
│   │   ├── __init__.py
│   │   ├── model_loader.py     # CPU-only model loading (quantized)
│   │   ├── metrics_calculator.py # Perplexity & syntax validity logic
│   │   └── run_inference.py    # CLI entry point for US-2
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── correlation.py      # Spearman calculation (US-3) with covariate control
│   │   └── report_generator.py # Final report generation
│   └── utils/
│       ├── config.py           # Constants, seeds, timeouts
│       ├── logging.py          # Unified logging
│       ├── hasher.py           # Generates SHA-256 hashes for artifacts (Constitution V)
│       └── reference_validator.py # Verifies citations (Constitution II)
├── data/
│   ├── raw/                    # Git clones (temporary)
│   ├── extracted/              # Intermediate CSVs (snippets)
│   ├── aggregated/             # File-level aggregated metrics
│   └── results/                # Final results & report
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure under `code/` with modular subpackages for extraction, inference, and analysis. This aligns with the linear data flow (Extract -> Infer -> Analyze) and simplifies dependency management for the CPU-only runner. The addition of `hasher.py` and `reference_validator.py` ensures automated compliance with Constitution principles V and II.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Quantized Model Loading** | Required to fit CodeGen-350M into 7 GB RAM on CPU. | Full precision model would exceed memory, causing OOM crashes. |
| **AST-based Extraction** | Needed to reliably isolate function-level snippets and ignore boilerplate. | Regex-based extraction is brittle and prone to capturing partial code or comments. |
| **File-Level Aggregation** | Required to satisfy independence assumptions in statistical testing. | Snippet-level analysis would inflate sample size and risk false positives due to shared file age. |
| **Covariate Control** | Required to isolate 'age' effect from 'complexity' and 'length'. | Without control, correlations may be confounded by code quality differences. |
| **Automated Validators** | Required to enforce Constitution II and V without manual intervention. | Manual checks are error-prone and not reproducible. |

