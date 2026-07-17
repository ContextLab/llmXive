# Implementation Plan: llmXive Automation System (001-gene-regulation)

**Branch**: `001-gene-regulation` | **Date**: 2026-07-14 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification for Fully Autonomous Scientific Discovery Pipeline

## Summary

This plan implements the core automation pipeline for the `llmXive` system, focusing on the `001-gene-regulation` feature branch. The system ingests standardized datasets, generates research hypotheses via an LLM agent, scores them for novelty against a local literature corpus, generates executable Python code to validate them, and performs statistical analysis to correlate LLM architectural configurations (ArchConfig) with reproducibility and novelty metrics. The implementation strictly adheres to CPU-only constraints for GitHub Actions free-tier runners (limited CPU, 7GB RAM) and ensures every Functional Requirement (FR) and Success Criterion (SC) is addressed with a concrete implementation phase.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `transformers` (CPU-optimized), `sentence-transformers`, `datasets`, `pytest`, `scipy`, `pyyaml`, `statsmodels`  
**Storage**: Local filesystem (`data/`, `code/`, `lit_search/`) with checksums; no external DB.  
**Testing**: `pytest` (unit, integration, contract tests), custom smoke tests for pipeline execution.  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM, 14GB disk, no GPU).  
**Project Type**: CLI/automation pipeline (research tool).  
**Performance Goals**: Pipeline completion for 5 datasets × 20 hypotheses within 6 hours; <7GB RAM peak; <14GB disk usage.  
**Constraints**: No GPU/CUDA; no large model fine-tuning; strict timeout (60s per code execution); strict memory limits (retry with sampling on `MemoryError`).  
**Scale/Scope**: 5 datasets (sampled), ~100 hypotheses total, 1 literature corpus (pre-indexed or generated on-fly).

> **Note on Compute Feasibility**: All LLM inference uses small, CPU-tractable models (e.g., `all-MiniLM-L6-v2` for embeddings, distilled LLMs for generation) or local API calls to small models. No training from scratch. Data is sampled to fit RAM.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. Datasets fetched from canonical HuggingFace/UCI URLs. `requirements.txt` pinned. |
| **II. Verified Accuracy** | **PASS** | **Phase 0, Step 3** explicitly runs the Reference-Validator Agent to validate all citations in `research.md` and `plan.md` against primary sources before proceeding. Novelty scores computed against ground-truth corpus. |
| **III. Data Hygiene** | **PASS** | Raw data in `data/` is checksummed. Derivations write new files. PII scan enforced via pre-commit hook. |
| **IV. Single Source of Truth** | **PASS** | All stats in `paper/` trace to `data/` rows and `code/` blocks. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts carry content hashes. `state/` updated on change. |
| **VI. Hypothesis Novelty** | **PASS** | Novelty computed via semantic similarity against `lit_search` index. **Phase, Step 3** ensures hypotheses with default score 0.5 are flagged as 'non_novel' and retained. Index is frozen and independent of ArchConfig. |
| **VII. Automated Execution** | **PASS** | Code execution in isolated sandbox. Logs capture `Pass`/`Fail` and specific error types. >40% failure rate is a metric. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── hypothesis.schema.yaml
    ├── execution_log.schema.yaml
    └── dataset_schema.schema.yaml
```

### Source Code (repository root)

```text
src/
├── agents/
│   ├── brainstorm.py       # Hypothesis generation (LLM)
│   ├── coder.py            # Code generation
│   └── scorer.py           # Novelty scoring
├── core/
│   ├── pipeline.py         # Orchestration
│   ├── executor.py         # Code execution sandbox
│   └── stats.py            # Statistical analysis
├── utils/
│   ├── data_loader.py      # Dataset ingestion & sampling
│   ├── corpus_builder.py   # Literature index
│   └── seed.py             # Seed management
├── cli/
│   └── main.py             # Entry point
└── config/
    └── arch_configs.yaml   # ArchConfig definitions

tests/
├── contract/               # Schema validation tests
├── integration/            # End-to-end pipeline tests
└── unit/                   # Agent unit tests

data/
├── raw/                    # Downloaded datasets (checksummed)
├── processed/              # Sampled/derived data
└── lit_search/             # Vector index files

code/
└── generated/              # Executable scripts per hypothesis
```

**Structure Decision**: Single project structure with clear separation of `agents` (generation), `core` (logic), and `utils` (support). This minimizes overhead and fits the CLI/research tool paradigm.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Isolated Code Execution** | Required by FR-004/FR-005 to catch dependency/logic errors safely. | Running code in the main process would crash the entire pipeline on a single error and cannot simulate sandboxed failures. |
| **Novelty Scoring (Embeddings)** | Required by FR-003/FR-006 to quantify novelty against literature. | Heuristic keyword matching is insufficient for "rephrased training data" detection; semantic similarity is required. |
| **Statistical Correction (FDR)** | Required by FR-007 for >3 ArchConfigs to control family-wise error. | Bonferroni is too conservative for N=100; FDR (Benjamini-Hochberg) preserves power while controlling false discoveries. |
| **Mixed-Effects Modeling** | Required to handle dataset-level clustering (hypotheses from same dataset are not independent). | Standard t-tests assume independence; ignoring clustering inflates Type I error rates. |
| **Plausibility Filter** | Required to distinguish "novel" from "nonsense" (construct validity). | Low similarity alone could indicate gibberish; perplexity scoring filters non-coherent hypotheses. |

## Phase Plan

### Phase 0: Research & Data Strategy
*Goal: Validate dataset fit, finalize literature corpus strategy, and validate citations.*
1.  **Dataset Verification**: Verify that selected UCI/HuggingFace datasets contain variables needed for hypothesis generation (predictors, outcomes). **Exclude UCI DROP** as it lacks tabular variables. Confirm access to train/test splits for UCI HAR. (Addresses FR-001, SC-001).
2.  **Corpus Construction**: Define strategy for `lit_search` index. **Filter literature by publication date** to ensure all items are post-LLM training cutoff. Generate a small CPU-tractable index from recent literature using `sentence-transformers`. (Addresses FR-003, Assumption: Literature, Constitution VI).
3.  **Reference Validation**: Execute the **Reference-Validator Agent** to verify all citations in `research.md` and `plan.md` against primary sources. (Addresses Constitution II).
4.  **ArchConfig Definition**: Define the set of LLM configurations. **Include structural parameters** (context window, model size) rather than just quality parameters to avoid tautology in correlation analysis. (Addresses FR-002, FR-007).

### Phase 1: Data Model & Contracts
*Goal: Define schemas for Hypothesis, ExecutionLog, and Dataset.*
1.  Draft `contracts/hypothesis.schema.yaml` (ID, text, variables, novelty_score, source).
2.  Draft `contracts/execution_log.schema.yaml` (ID, code, status, error_type, runtime).
3.  Draft `contracts/dataset_schema.schema.yaml` (columns, types, checksum).
4.  Implement `data-model.md` with entity definitions and relationships.

### Phase 2: Core Pipeline Implementation
*Goal: Build the ingestion, generation, and execution engine.*
1.  **Ingestion**: Implement `data_loader.py` to fetch, checksum, and sample datasets to fit 7GB RAM. **Fetch both train and test splits** for UCI HAR. (FR-001).
2.  **Hypothesis Generation**: Implement `agents/brainstorm.py` using CPU-tractable LLM. Generate hypotheses/dataset. (FR-002).
3.  **Novelty Scoring**: Implement `agents/scorer.py` using a **frozen, pre-computed index** and fixed embedding model (`all-MiniLM-L6-v2`). Compute cosine similarity. **Add Plausibility Check** (perplexity) to filter gibberish. **Handle empty corpus** by assigning score 0.5 and flagging hypothesis as 'non_novel' (retained in logs). (FR-003, Edge Case, Constitution VI).
4.  **Code Generation**: Implement `agents/coder.py` to generate Python scripts. (FR-004).
5.  **Execution Sandbox**: Implement `core/executor.py` with 60s timeout, `MemoryError` retry (1x), and error categorization. (FR-004, FR-005, Edge Case).
6.  **Static Analysis**: Implement pre-execution check for variable existence and logical plausibility. (FR-010).

### Phase 3: Statistical Analysis & Reporting
*Goal: Aggregate results and compute correlations.*
1.  **Normality Check**: Perform Shapiro-Wilk test on novelty scores. If violated, switch to non-parametric methods (Kruskal-Wallis) for group comparisons. (Addresses SC-003).
2.  **Mixed-Effects Modeling**: Implement `core/stats.py` to fit **Linear Mixed-Effects Models (LMM)** with random intercepts per dataset and fixed effects for ArchConfig variations. This accounts for clustering and handles independent groups without artificial pairing. (Addresses FR-006, SC-003).
3.  **Multiple Comparisons**: Apply **Benjamini-Hochberg FDR correction** to p-values from the LMM fixed effects to control false discovery rate. (Addresses FR-007).
4.  **Baseline & Sensitivity**: Implement baseline generation (human hypotheses) and sensitivity analysis (vary embedding model/threshold). (FR-008, FR-009).
5.  **Exploratory Nature**: Explicitly state in the report that the study is **exploratory** and that non-significant results cannot rule out the hypothesis due to limited power (N=100). (Addresses SC-003).

### Phase 4: Integration & Validation
*Goal: End-to-end smoke test, contract validation, and manual annotation.*
1.  Run pipeline on single UCI dataset (smoke test). Verify CSV output of hypotheses + scores. (US-1).
2.  Validate code execution on single hypothesis. Verify error logging. (US-2).
3.  **Manual Annotation Sub-Phase**: Select a representative sample of hypotheses, employ **two independent annotators**, and compute **Cohen's Kappa** to verify false-positive rate of the novelty scorer. (Addresses SC-004).
4.  Ensure all outputs match `contracts/*.schema.yaml`.

## Compute Feasibility & Risk Mitigation

- **Memory**: Data is sampled to <2GB. Embedding model is a lightweight sentence-transformer architecture. LLM generation uses small distilled models or API calls.
- **Time**: 60s timeout per code execution. Max 20 hypotheses/dataset × 5 datasets = 100 executions. Total estimated runtime <2 hours.
- **GPU**: None. All operations are CPU-bound.
- **Risk**: `MemoryError` during code execution. Mitigation: Retry with random sample (bounded by a reasonable time limit). Log as `ResourceExceeded`.

## FR/SC Mapping

| ID | Description | Plan Phase |
| :--- | :--- | :--- |
| FR-001 | Ingest/Validate Datasets | Phase 2 (Ingestion) |
| FR-002 | Generate Hypotheses | Phase 2 (Generation) |
| FR-003 | Novelty Scoring (Embeddings) | Phase 2 (Scoring) |
| FR-004 | Code Gen & Execution (60s) | Phase 2 (Execution) |
| FR-005 | Log Outcomes | Phase 2 (Execution) |
| FR-006 | Statistical Regression | Phase 3 (Stats) |
| FR-007 | Multiple-Comparison Correction | Phase 3 (Stats) |
| FR-008 | Human Baseline (5) | Phase 3 (Baseline) |
| FR-009 | Sensitivity Analysis | Phase 3 (Stats) |
| FR-010 | Static Analysis | Phase 2 (Pre-exec) |
| SC-001 | Hallucinated Citation Rate | Phase 3 (Stats) |
| SC-002 | Reproducibility Failure Rate | Phase 3 (Stats) |
| SC-003 | Statistical Significance (p-value) | Phase 3 (Stats) |
| SC-004 | False-Positive Rate (Manual Check) | Phase 4 (Validation) |
| SC-005 | Computational Cost (CPU sec) | Phase 4 (Validation) |