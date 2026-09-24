# Implementation Plan: Evaluating the Effectiveness of Prompt Engineering for LLM-Based Code Translation

**Branch**: `001-prompt-engineering-code-translation` | **Date**: 2024-05-21 | **Spec**: `specs/001-prompt-engineering-code-translation/spec.md`
**Input**: Feature specification from `/specs/001-prompt-engineering-code-translation/spec.md`

## Summary

This project evaluates four prompt engineering strategies (Zero-shot Basic, Zero-shot+Style, Few-shot, Few-shot+Style) for translating Python code to JavaScript using the CodeLlama model via the HuggingFace Inference API. The implementation involves downloading and preprocessing a corpus of ≥200 code pairs, executing translations, validating functional correctness via unit tests (using deterministic transpilation for ground truth), measuring code quality (cyclomatic complexity, lines of code), and performing statistical analysis (GLMM, Repeated Measures ANOVA) to determine significant differences between conditions. The entire pipeline is designed to run within the constraints of a GitHub Actions free-tier runner (limited CPU, constrained RAM, 6h limit) using CPU-tractable methods and API-based inference.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets`, `pandas`, `requests`, `scikit-learn`, `statsmodels`, `node`, `npm`  
**Storage**: Local CSV/JSON files in `data/`, version-controlled prompts in `data/prompts/`  
**Testing**: `pytest` for unit tests; integration tests via execution scripts; statistical validation via `statsmodels`  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Research pipeline / Data processing / Statistical analysis  
**Performance Goals**: Total runtime ≤ 6 hours; Memory footprint ≤ 7 GB; API timeout handling (configurable duration)  
**Constraints**: No GPU; No local LLM training; API rate limit handling (exponential backoff); Data chunking for RAM limits  
**Scale/Scope**: 200 code snippets × 4 conditions = 800 API requests; A large-scale analysis of generated code lines will be conducted.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | ✅ PASS | All seeds pinned in `code/`; datasets fetched from canonical HF URLs; `requirements.txt` pins versions; `package-lock.json` pins Node.js deps; scripts runnable end-to-end. |
| **II. Verified Accuracy** | ✅ PASS | Only URLs from `# Verified datasets` block cited; Reference-Validator agent will check titles; no hallucinated sources. |
| **III. Data Hygiene** | ✅ PASS | **Checksum Generation Step**: A dedicated script `code/utils/checksum_artifacts.py` will generate SHA-256 hashes for all raw data files in `data/raw/` and write them to `state/` before any transformation. No data is modified in place; transformations write new files. PII scan enforced. |
| **IV. Single Source of Truth** | ✅ PASS | All statistics trace to `data/evaluation/` CSV; no hand-typed numbers in paper; derived files documented. |
| **V. Versioning Discipline** | ✅ PASS | **State Update Mechanism**: The `code/utils/update_state.py` script will compute content hashes of all artifacts in `data/` and `code/`. If hashes change, it updates the `updated_at` timestamp in `state/projects/PROJ-230-evaluating-the-effectiveness-of-prompt-e.yaml` and invalidates stale review records. |
| **VI. Prompt Specification Integrity** | ✅ PASS | Prompts stored in `data/prompts/` as version-controlled text; exact text logged with model ID and seed; changelog required for modifications. |
| **VII. Evaluation Transparency** | ✅ PASS | Correctness via deterministic test translation + unit-test pass/fail only; stats (GLMM, RM-ANOVA) with fixed lib version; p-values and CIs included with raw data. |

## Project Structure

### Documentation (this feature)

```text
specs/001-prompt-engineering-code-translation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── ingestion/
│   ├── download_datasets.py
│   └── preprocess_corpus.py
├── prompts/             # REMOVED: Prompts moved to data/prompts/ per Constitution VI
├── execution/
│   ├── run_inference.py
│   └── api_client.py
├── evaluation/
│   ├── translate_tests.py       # Uses deterministic transpiler
│   ├── run_node_tests.py
│   ├── compute_quality.py
│   └── statistical_analysis.py
├── utils/
│   ├── logging.py
│   ├── timeout_utils.py
│   ├── checksum_artifacts.py    # NEW: For Principle III
│   └── update_state.py          # NEW: For Principle V
└── main.py

tests/
├── contract/
├── integration/
└── unit/

data/
├── raw/
├── processed/
├── prompts/             # NEW: All prompt templates stored here
│   ├── zero_shot_basic.txt
│   ├── zero_shot_style.txt
│   ├── few_shot_basic.txt
│   └── few_shot_style.txt
└── evaluation/

requirements.txt
package.json             # NEW: For Node.js dependencies
package-lock.json        # NEW: For Node.js version pinning
```

**Structure Decision**: Single-project structure with modular directories for ingestion, execution, and evaluation to ensure separation of concerns and reproducibility. All data flows through `data/` with clear intermediate states. Prompts are strictly located in `data/prompts/` to satisfy Constitution Principle VI.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed with no violations. | N/A |