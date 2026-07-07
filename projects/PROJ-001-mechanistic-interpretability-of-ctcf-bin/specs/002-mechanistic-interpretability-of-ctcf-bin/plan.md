# Implementation Plan: Mechanistic Interpretability of CTCF Binding-Site Selection

**Branch**: `001-mechanistic-interpretability-of-ctcf-binding` | **Date**: 2026-05-17 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-mechanistic-interpretability-of-ctcf-binding/spec.md`

## Summary
This project **cannot proceed** to the implementation phase as currently scoped. The specification requires a multi-modal analysis (ChIP-seq, ATAC-seq, Histone marks) to distinguish between sequence motifs and chromatin accessibility (the "Formal Cause"). However, the `# Verified datasets` block provided for this project contains **no verified sources** for the required ATAC-seq, CTCF ChIP-seq, or H3K27ac data. 

The plan explicitly identifies this as a **blocking data gap**. Any attempt to proceed with a "sequence-only" model or "synthetic labels" would violate the scientific validity of the research question (which relies on distinguishing accessible vs. inaccessible motifs) and the project's Constitution (Principle VI: Biological Validity requires validation against independent experimental data). 

Therefore, the primary task of this plan is to document the blocking constraints and halt the pipeline until verified multi-modal sources are identified. The "Implementation" steps below are conditional on the discovery of such sources.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `torch` (CPU-only), `biopython`, `pyyaml`, `huggingface_hub`, `datasets`  
**Storage**: Local filesystem (Parquet/CSV) for intermediate data; `data/` directory for artifacts.  
**Testing**: `pytest` (unit tests for data ingestion, model shape, schema validation).  
**Target Platform**: Linux (GitHub Actions Free Tier: multiple CPU cores, substantial RAM capacity, no GPU).  
**Project Type**: Computational Biology Research Pipeline.  
**Performance Goals**: N/A (Pipeline blocked).  
**Constraints**: No GPU/CUDA usage; no large-LLM training; data subset to fit available RAM; all statistical claims framed as associational.  
**Scale/Scope**: Analysis of genomic windows (±500 bp) from up to 10 cell types (targeting 5 verified sources); identification of ≥5 latent features.

> **CRITICAL NOTE**: The plan below describes the intended workflow **IF** verified multi-modal data were available. As it stands, the project is in a "Blocked" state.

## Constitution Check

*GATE: FAILED. The project cannot proceed to research/implementation.*

| Principle | Status | Implementation Strategy / Blocking Issue |
| :--- | :--- | :--- |
| **I. Reproducibility** | **BLOCKED** | Cannot reproduce results without verified data sources. |
| **II. Verified Accuracy** | **FAIL** | No verified sources for ATAC-seq, CTCF, or H3K27ac exist in the provided block. Citing non-existent URLs is prohibited. |
| **III. Data Hygiene** | **N/A** | No data can be ingested. |
| **IV. Single Source of Truth** | **N/A** | No metrics can be computed. |
| **V. Versioning Discipline** | **N/A** | No artifacts to version. |
| **VI. Biological Validity** | **FAIL** | Principle VI requires validation against independent experimental datasets. The plan admits no such dataset exists in the verified sources. Claims of "mechanistic interpretability" without chromatin data are scientifically invalid. |

**Reviewer Addressal**:
*   **rosalind-franklin-simulated (Hydration/Structure)**: The plan acknowledges that structural fidelity (hydration states) is beyond the current scope, but the primary blocker is the lack of *any* verified chromatin data (ATAC/Histone) to even begin addressing the "Formal Cause".
*   **aristotle-simulated (Four Causes)**: The plan explicitly acknowledges that the "Formal Cause" (chromatin) is missing. Therefore, the separation of Material and Formal causes cannot be modeled. The project is blocked until the Formal Cause can be measured.

## Project Structure

### Documentation (this feature)

```text
specs/001-mechanistic-interpretability-of-ctcf-binding/
├── plan.md              # This file (Blocked State)
├── research.md          # Phase 0 output (Data Feasibility Study)
├── data-model.md        # Phase 1 output (Placeholder)
├── quickstart.md        # Phase 1 output (Placeholder)
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (Not generated)
```

### Source Code (repository root)

```text
projects/PROJ-001-mechanistic-interpretability-of-ctcf-bin/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── __init__.py
│   │   ├── ingest.py          # [BLOCKED] Awaiting verified source
│   │   └── preprocess.py      # [BLOCKED]
│   ├── models/
│   │   ├── __init__.py
│   │   ├── predictor.py       # [BLOCKED]
│   │   └── sae.py             # [BLOCKED]
│   ├── interpret/
│   │   ├── __init__.py
│   │   ├── attribution.py     # [BLOCKED]
│   │   └── validation.py      # [BLOCKED]
│   └── main.py                # [BLOCKED]
├── data/
│   ├── raw/                   # [BLOCKED]
│   ├── processed/             # [BLOCKED]
│   └── manifest.json          # [BLOCKED]
├── tests/
│   ├── unit/
│   └── contract/
└── state/
    └── artifacts.yaml         # [BLOCKED]
```

**Structure Decision**: Structure is defined but cannot be populated.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **SAE + Integrated Gradients** | Required by spec (FR-003). | Cannot be applied without a trained model (FR-002) and verified labels. |
| **Multi-modal Input** | Required by spec (FR-001). | Sequence-only input is scientifically invalid for the research question (cannot distinguish accessibility). |

## Blocking Data Gap Summary

1.  **Missing ATAC-seq/ChIP-seq/Histone Data**: The `# Verified datasets` block contains no URLs for the required multi-modal data.
2.  **Missing Binding Labels**: No verified source for CTCF binding labels (ChIP-seq peaks) exists.
3.  **Invalid Fallback**: Using "synthetic labels" (motif scores) creates a circular training loop and fails to address the research question (identifying non-canonical binding).
4.  **Constitution Violation**: Proceeding without verified data violates Principle VI (Biological Validity) and Principle II (Verified Accuracy).

**Action**: The project is halted. The next step is to search for verified multi-modal ENCODE datasets or revise the spec to a scope that can be satisfied by available sequence-only data (which would fundamentally change the research question).