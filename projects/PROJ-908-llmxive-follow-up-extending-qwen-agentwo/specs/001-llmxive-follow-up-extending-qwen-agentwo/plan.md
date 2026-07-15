# Implementation Plan: llmXive follow-up: extending "Qwen-AgentWorld: Language World Models for General Agents"

**Branch**: `001-llmxive-followup` | **Date**: 2026-07-15 | **Spec**: `specs/001-llmxive-followup/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-followup/spec.md`

## Summary

This feature implements a rigorous validation framework to quantify the divergence between Large Language Model (LLM) reasoning and deterministic ground-truth physics in the Qwen-AgentWorld environment. The technical approach involves: (1) parsing the AgentWorld environment source code to construct a deterministic State-Transition Oracle (Ground Truth); (2) applying First-Order Logic (FOL) Inductive Logic Programming (ILP) to LLM Chain-of-Thought (CoT) traces to extract a Hypothesized Rule Set; (3) validating extracted rules against the Oracle to ensure independence; and (4) executing a comparative analysis on standardized long-horizon tasks to classify errors into "Hallucination" (active deviation from valid physics) and "Rule Gap" (failure to execute valid physics), followed by a paired permutation test for statistical significance.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets` (for HuggingFace data loading), `scikit-learn` (for preprocessing), `prolog` (for FOL rule induction), `networkx` (for state graph representation), `pandas` (data manipulation), `pytest` (testing).  
**Storage**: Local file system (temporary) for parsed datasets; no external database required.  
**Testing**: `pytest` with fixed random seeds (42).  
**Target Platform**: Linux server (GitHub Actions free-tier: multiple CPUs, sufficient RAM).  
**Project Type**: Research pipeline / CLI tool.  
**Performance Goals**: Complete end-to-end analysis of 500 tasks within 6 hours on CPU.  
**Constraints**: Must run on CPU-only free-tier runner. LLM inference is performed using a verified, CPU-quantized model (e.g., Qwen-1.8B-Int4) or pre-generated traces.  
**Scale/Scope**: A substantial number of planning tasks, multiple state transitions per task, ILP induction on a corresponding set of traces.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned.; `requirements.txt` pins versions; data fetched via verified HF URLs with checksums. |
| **II. Verified Accuracy** | **PASS** | All dataset citations restricted to the `# Verified datasets` block; no invented URLs. Trace generation uses verified open-source models. |
| **III. Data Hygiene** | **PASS** | Raw data downloaded to `data/raw/` with checksum verification; derivatives written to `data/processed/` with new names. |
| **IV. Single Source of Truth** | **PASS** | Final metrics derived strictly from `data/processed/` divergence reports; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes tracked in project state file; code changes trigger state updates. |
| **VI. Ground-Truth Oracle Independence** | **PASS** | Oracle derived *strictly* from environment source code (parsing logic), mathematically independent of LLM traces. |
| **VII. Trajectory Error Classification** | **PASS** | Classification logic strictly enforces "Hallucination" vs "Rule Gap" for *analysis*. "Extraction Uncertainty" and "Cold Start" are recorded separately and **excluded** from the primary statistical analysis to satisfy the "exactly two categories" mandate. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-followup/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── oracle.schema.yaml
    ├── rules.schema.yaml
    └── divergence.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-908-llmxive-follow-up-extending-qwen-agentwo/
├── code/
│   ├── __init__.py
│   ├── main.py                 # Entry point for pipeline
│   ├── oracle/
│   │   ├── parser.py           # FR-001: Source code parser
│   │   └── simulator.py        # Deterministic state transition logic
│   ├── rules/
│   │   ├── extractor.py        # FR-002: FOL/ILP induction
│   │   ├── validator.py        # Rule consistency checks against Oracle
│   │   └── generator.py        # Synthetic trace generation for validation
│   ├── analysis/
│   │   ├── diverge.py          # FR-003, FR-004: Comparison engine
│   │   └── stats.py            # FR-005: Paired permutation test
│   ├── inference/
│   │   └── runner.py           # CPU-quantized LLM inference
│   └── utils/
│       ├── loaders.py          # Data loading from verified sources
│       └── checksums.py        # Data hygiene utilities
├── data/
│   ├── raw/                    # Downloaded datasets (checksummed)
│   ├── processed/              # Derived artifacts (oracle, rules, reports)
│   └── external/               # Environment source code (if needed)
├── tests/
│   ├── unit/                   # Unit tests for parser, extractor
│   ├── integration/            # End-to-end pipeline tests
│   └── contract/               # Schema validation tests
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure chosen (`code/` subdirectory) as this is a research pipeline. Added `inference/` for trace generation and `rules/validator.py` for Oracle-based validation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **FOL/ILP Extraction (FR-002)** | Required to transform unstructured CoT into *relational* logical rules (e.g., `holds(A,B) -> holds(A,C)`). | Decision Trees produce axis-parallel splits (e.g., `x > 5`) which cannot capture the relational state dependencies (e.g., `key held AND door adjacent -> open`) required for physics modeling. Regex is insufficient for logical inference. |
| **Oracle-Based Rule Validation** | Required to ensure extracted rules are not circular projections of LLM errors. | Using the extracted rule as the validator creates a tautology. The Oracle must validate the rule's correctness before it is used for classification. |
| **Paired Permutation Test (FR-005)** | Required to compare dependent rates (spatial vs. temporal) within the same trajectories. | Standard independent permutation tests assume independence between groups, which is false for sequential state transitions; would yield invalid p-values. |
| **Separate Cold Start/Extraction Logging** | Required to distinguish "missing data" from "logical failure". | Aggregating all errors would conflate "unknown" with "wrong", violating the "Hallucination vs Rule Gap" distinction. |

## Implementation Phases

### Phase 0: Data Acquisition & Oracle Construction
1.  **Download**: Fetch `AgentWorldBench` and environment source code.
2.  **Parse**: Run `oracle/parser.py` to generate `oracle_graph.json` (Deterministic State-Transition Oracle).
3.  **Validate**: Verify Oracle against `AgentWorldBench` schema (Schema Alignment).

### Phase 1: Trace Generation & Rule Extraction
1.  **Generate**: Run `inference/runner.py` with a verified CPU-quantized model to generate CoT traces for a representative set of tasks.
2.  **Extract**: Run `rules/extractor.py` (FOL/ILP) to generate `extracted_rules.json`.
3.  **Validate Rules**: Run `rules/validator.py` to cross-check extracted rules against the Oracle. Flag discrepancies as "Extraction Failure".

### Phase 2: Divergence Analysis
1.  **Execute**: Run `analysis/diverge.py` to compare LLM, Oracle, and Validated Rules.
2.  **Classify**:
    *   **Match**: LLM == Oracle.
    *   **Hallucination**: LLM != Oracle AND Oracle Logic is Inferable (verified by Oracle).
    *   **Rule Gap**: LLM != Oracle AND Oracle Logic is Inferable BUT Extracted Rule != Oracle.
    *   **Extraction Uncertainty**: Ambiguous trace (Excluded from analysis).
    *   **Cold Start**: Interaction type never seen (Excluded from analysis).
3.  **Filter**: Exclude Uncertainty and Cold Start from the primary Hallucination/Rule Gap counts.

### Phase 3: Statistical Significance
1.  **Test**: Run `analysis/stats.py` using a **Paired Permutation Test** to compare divergence rates between interaction classes.
2.  **Report**: Generate `divergence_report.json` with p-values and boundary conditions.