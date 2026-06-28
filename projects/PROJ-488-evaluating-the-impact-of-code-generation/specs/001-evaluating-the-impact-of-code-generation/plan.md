# Implementation Plan: 001-code-review-quality

**Branch**: `001-code-review-quality` | **Date**: 2025-01-15 | **Spec**: `specs/001-code-review-quality/spec.md`
**Input**: Feature specification from `specs/001-code-review-quality/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

This feature implements a comparative analysis pipeline to evaluate the impact of code generation models on code review quality. The system downloads human-written (CodeSearchNet) and LLM-generated (CodeParrot/CodeGen) code datasets, filters for Python function snippets of comparable size, extracts static analysis metrics (complexity, bug indicators), and performs statistical comparison (Mann-Whitney U, Cliff's Delta) to generate review guidelines.

**IMPORTANT CAUSAL LANGUAGE DISCLAIMER**: All output guidelines are ASSOCIATIONAL RECOMMENDATIONS based on correlational data. The plan does NOT claim causal improvement to review quality. Guidelines are framed as "if metric X differs, consider review adjustment Y" with explicit acknowledgment of observational study limitations.

## Constitutional Amendment Request

**STATUS: RESEARCH BLOCKED PENDING AMENDMENT APPROVAL OR SPEC REVISION**

The following conflicts between the spec and ratified Constitution must be resolved before research can proceed. This section documents the formal amendment workflow required.

| Principle | Current Spec Requirement | Constitution Requirement | Resolution Required |
| :--- | :--- | :--- | :--- |
| **VI. Dataset Provenance** | CodeParrot/CodeGen for LLM code | HumanEval or MBPP for LLM code | 1) Amend Constitution VI to allow CodeParrot/CodeGen with justification, OR 2) Revise spec to use HumanEval/MBPP |
| **VII. Metric Transparency** | radon/pylint for metrics | TinyLlama-1.1B for metrics | 1) Amend Constitution VII to allow radon/pylint (CPU feasibility), OR 2) Revise spec to use TinyLlama-1.1B |

**Amendment Workflow**:
1. Document conflict in this plan (CONSTITUTIONAL AMENDMENT REQUEST section)
2. Open PR to amend Constitution with justification (see below)
3. **Research CANNOT complete until amendment approved OR spec revised**
4. Track amendment status in `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml`

**Amendment Justification for Principle VI**:
- CodeParrot/CodeGen provides LLM-generated code at scale (training corpus)
- HumanEval/MBPP are benchmark datasets with limited code volume (<500 samples)
- For statistical power (n≥1000 per group), CodeParrot/CodeGen is necessary
- Amendment request: Allow LLM-generated code from verified training corpora

**Amendment Justification for Principle VII**:
- TinyLlama on a substantial volume of snippets is expected to exceed runtime thresholds on limited CPU resources. (violates SC-004)
- radon/pylint are established static analysis tools (community standard)
- CPU feasibility is required for CI reproducibility
- Amendment request: Allow CPU-tractable static analysis tools with documented justification

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets` (HuggingFace), `radon`, `pylint`, `scipy`, `matplotlib`, `pandas`, `numpy`  
**Storage**: Local filesystem (`data/`, `results/`)  
**Testing**: `pytest`  
**Target Platform**: GitHub Actions free-tier runner (Linux, standard compute resources)  
**Project Type**: Data analysis pipeline / CLI  
**Performance Goals**: Total runtime ≤6 hours on CPU-only hardware; metric extraction ≤30 minutes for 2000 snippets  
**Constraints**: No GPU/CUDA; no deep-net training; memory ≤7 GB; disk ≤14 GB  
**Scale/Scope**: A collection of Python function snippets (distributed across groups)

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes / Mitigation |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned random seeds (FR-009) and checksummed datasets (FR-010). |
| **II. Verified Accuracy** | **BLOCKING** | Dataset verification workflow added; halt with error 101 if no verified source found. HF identifiers documented for traceability. |
| **III. Data Hygiene** | **PASS** | SHA-256 checksums recorded in `data/checksums.json` (FR-010); no in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All statistics trace to `results/` CSVs; no hand-typed numbers in paper. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes tracked in `state/...yaml`; `updated_at` timestamps managed by agent. |
| **VI. Dataset Provenance** | **BLOCKING** | Spec requires CodeParrot/CodeGen. Constitution VI requires HumanEval/MBPP. Research BLOCKED until amendment approved OR spec revised. See Constitutional Amendment Request section. |
| **VII. Metric Transparency** | **BLOCKING** | Spec requires radon/pylint. Constitution VII requires TinyLlama-1.1B. Research BLOCKED until amendment approved OR spec revised. CPU feasibility documented. See Constitutional Amendment Request section. |

## Review Guideline Generation Protocol

**Purpose**: Document mechanism for translating statistical results into review guidelines (addresses methodology-cb9c836e).

**Protocol**:
1. For each metric with p < 0.05 (after Benjamini-Hochberg correction) AND |Cliff's delta| ≥ 0.1:
   - Generate recommendation describing how to adjust review standards for AI-generated artifacts
   - Frame as "associational recommendation" (not causal claim)
   - Include effect size magnitude (small/medium/large based on Cliff's delta thresholds)
2. Validation requirement: Guidelines must be reviewed by at least one human reviewer against pilot study data (n≥50)
3. Documentation: All guidelines recorded in `results/guidelines.md` with statistical justification

**Causal Disclaimer**: All guidelines are ASSOCIATIONAL RECOMMENDATIONS. The analysis compares metric distributions but does NOT establish that following guidelines improves review quality. Validation requires separate empirical study.

## Project Structure

### Documentation (this feature)

```text
specs/001-code-review-quality/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-488-evaluating-the-impact-of-code-generation/
├── code/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── data_ingestion.py       # HF download, filtering
│   ├── metric_extraction.py    # radon, pylint
│   ├── statistical_analysis.py # MWU, Cliff's Delta
│   ├── visualization.py        # Boxplots
│   ├── requirements.txt        # Pinned dependencies
│   └── seeds.py                # Seed management
├── data/
│   ├── raw/                    # Downloaded datasets (checksummed)
│   ├── processed/              # Filtered snippets
│   ├── metrics/                # Extracted scores
│   └── checksums.json          # FR-010
├── results/
│   ├── stats.csv               # Test results
│   ├── figures/                # Boxplots
│   └── guidelines.md           # Review recommendations
├── specs/001-code-review-quality/
└── state/
    └── projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml
```

**Structure Decision**: Single project structure (`code/`, `data/`, `results/`) chosen for simplicity and alignment with Constitution Principle I (Reproducibility) and IV (Single Source of Truth).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Constitution VI Conflict** (HumanEval/MBPP vs CodeParrot) | Spec mandates CodeParrot/CodeGen. Constitution VI mandates HumanEval/MBPP. | HumanEval/MBPP have insufficient sample size (<500) for statistical power (n≥1000 per group). **Research BLOCKED pending amendment**. |
| **Constitution VII Conflict** (TinyLlama vs radon/pylint) | Spec FR-003 mandates radon/pylint for CPU feasibility (6h limit). TinyLlama on 2000 snippets may exceed runtime on 2-core CPU. | Using TinyLlama would require GPU or significantly longer runtime, violating SC-004 (Compute Feasibility). **Research BLOCKED pending amendment**. |
| **Dataset Verification Gap** (FR-001) | Verified List states "NO verified source found" for required datasets. | Cannot proceed without data; Plan includes verification workflow. Halt with error 101 if no verified source. |
| **Independence Assumption** (Mann-Whitney U) | CodeSearchNet snippets may share authors/repositories, violating independence. | Plan addresses by subsampling to one snippet per repository OR documenting cluster-robust SE limitation. |