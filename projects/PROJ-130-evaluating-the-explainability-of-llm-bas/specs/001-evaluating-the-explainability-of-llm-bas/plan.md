# Implementation Plan: Evaluating the Explainability of LLM-Based Bug Fixes

**Branch**: `001-evaluating-explainability` | **Date**: 2024-01-15 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-evaluating-explainability/spec.md`

## Summary

This project evaluates how well three explainability techniques (attention visualization, code-diff saliency maps, and generated natural-language rationales) reflect the actual correctness and safety of bug fixes suggested by large language models for source-code defects. The technical approach involves: (1) downloading Defects4J v2.0 from the official repository, (2) generating patches using CodeLlama-7B-Instruct, (3) executing patches against test suites to determine correctness, (4) extracting explainability scores, and (5) performing statistical correlation analysis with confound controls.

**Critical Limitation Note**: Generated rationales are evaluated via INTERNAL COHERENCE against the code change, NOT against commit messages or issue descriptions (which describe WHAT changed, not WHY). BLEU/ROUGE against non-rationale text is explicitly INVALID for this purpose (see FR-006 revision).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: transformers, datasets, captum, scikit-learn, pytest, pandas, numpy, evaluate  
**Storage**: Local filesystem under `data/`, `explanations/`, `code/`  
**Testing**: pytest with contract tests against YAML schemas  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: computational research pipeline  
**Performance Goals**: Process 50 bugs end-to-end within 6 hours on CPU-only runner  
**Constraints**: No GPU/CUDA, ≤7 GB RAM, ≤14 GB disk, 60-second timeout per test run  
**Scale/Scope**: A representative sample of bugs from Defects4J v2.0 (sample size chosen for feasibility; minimum detectable r of moderate magnitude at [deferred] power)

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
|-----------|--------|----------------------|
| I. Reproducibility | ✅ PASS | Random seeds pinned in code/; external datasets fetched from canonical sources on every run |
| II. Verified Accuracy | ✅ PASS | All citations in research.md/plan.md validated against primary sources before review |
| III. Data Hygiene | ✅ PASS | Datasets checksummed and recorded under `state/`; raw data preserved unchanged |
| IV. Single Source of Truth | ✅ PASS | All figures/statistics trace back to data/ rows and code/ blocks; no hand-typed numbers |
| V. Versioning Discipline | ✅ PASS | All artifacts carry content hashes; state timestamps updated on artifact changes |
| VI. Explainability Artifact Transparency | ✅ PASS | All explainability outputs saved under `explanations/` with standardized naming and JSON metadata |
| VII. Benchmark Dataset Integrity | ✅ PASS | Defects4J v2.0 stored unchanged under `data/defects4j/`; CodeLlama revision recorded in `code/model_revision.txt` |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-explainability/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── dataset.schema.yaml
│   ├── patch.schema.yaml
│   ├── correctness.schema.yaml
│   ├── explainability.schema.yaml
│   └── statistical.schema.yaml
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-130-evaluating-the-explainability-of-llm-bas/
├── data/
│   └── defects4j/              # Original dataset archive (unchanged)
│       └── [raw parquet files]
├── code/
│   ├── 01_download_data.py     # FR-001: Download Defects4J
│   ├── 02_generate_patches.py  # FR-002, FR-011: Generate patches with seeded inference
│   ├── 03_execute_tests.py     # FR-003, FR-010: Execute test suites with timeout
│   ├── 04_extract_attention.py # FR-004: Extract attention weights
│   ├── 05_compute_saliency.py  # FR-005: Compute Integrated Gradients
│   ├── 06_compute_rationale_coherence.py # FR-006: Compute rationale coherence (REVISED)
│   ├── 07_statistical_analysis.py # FR-007, FR-008, FR-009: Statistical tests with confound controls
│   ├── model_revision.txt      # FR-012: Record model revision identifier
│   └── requirements.txt        # Pin all dependencies
├── explanations/
│   ├── <bug-id>_attention.png  # VI. Explainability Artifact Transparency
│   ├── <bug-id>_saliency.npy   # VI. Explainability Artifact Transparency
│   ├── <bug-id>_rationale.txt  # VI. Explainability Artifact Transparency
│   └── <bug-id>_metadata.json  # VI. Explainability Artifact Transparency
├── state/
│   └── projects/PROJ-130-evaluating-the-explainability-of-llm-bas.yaml
│       └── artifact_hashes     # III. Data Hygiene
└── tests/
    ├── contract/               # Contract tests against YAML schemas
    ├── integration/            # End-to-end pipeline tests
    └── unit/                   # Unit tests for individual functions
```

**Structure Decision**: Single project structure (DEFAULT) with clear separation between data/, code/, explanations/, and tests/. This aligns with the computational research pipeline nature of the project and supports reproducibility requirements.

## Complexity Tracking

No violations identified. All complexity is justified by research requirements.

## Phase Plan (Ordered for Computational Feasibility)

### Phase 0: Research & Dataset Verification (Week 1)
- **FR-001**: Download Defects4J v2.0 from OFFICIAL GitHub repository (https://github.com/rjust/defects4j), NOT community HuggingFace uploads
- **Dataset-variable fit verification**: Confirm The benchmark dataset contains buggy files, test suites, and optional reference text
- **Test suite executability verification**: Verify test suite can be executed on generated patch by running Defects4J test command on sample bug (CRITICAL for FR-003)
- **Compute feasibility assessment**: Verify CodeLlama-7B-Instruct runs on CPU within 6h budget

### Phase 1: Data Model & Schema Design (Week 1)
- Define all data structures (Bug, Patch, CorrectnessLabel, ExplainabilityScore, StatisticalResult)
- Create YAML schemas for validation (contracts/*.schema.yaml) including correctness.schema.yaml
- Design explainability artifact naming convention (explanations/*)

### Phase 2: Patch Generation Pipeline (Week 2)
- **FR-002**: Prompt CodeLlama-7B-Instruct to generate patches
- **FR-011**: Pin random seeds for reproducibility
- **FR-012**: Record model revision identifier
- Handle edge cases: invalid patches, generation failures, timeouts

### Phase 3: Test Execution Pipeline (Week 2)
- **FR-003**: Execute patches against Defects4J test suite
- **FR-010**: Enforce 60-second timeout per test run
- Record binary pass/fail outcome plus unsafe flag for new failures

### Phase 4: Explainability Score Extraction (Week 3)
- **FR-004**: Extract per-token attention weights from last decoder layer
  - **LIMITATION**: Attention ≠ explanation (Jain & Wallace, Serrano & Smith)

The research question is: Can attention mechanisms truly provide explanations for model decisions, or do they merely highlight salient input features without revealing underlying reasoning?

The method will be: We will conduct a series of ablation studies and qualitative analyses on transformer-based models, manipulating attention weights and observing the impact on model performance and human interpretability assessments.; results framed as correlation, not explanation validity
- **FR-005**: Apply Captum's Integrated Gradients to tokenized diffs
- **FR-006**: Compute rationale coherence against code change semantics (REVISED: NOT BLEU/ROUGE against commit messages)
  - Rationale quality measured via internal coherence with code change, not ground-truth alignment
  - BLEU/ROUGE against commit messages/issue descriptions is INVALID (they describe WHAT, not WHY)
  - Record coherence score; document limitation that this does not validate explanation correctness

### Phase 5: Statistical Analysis (Week 3)
- **FR-007**: Compute point-biserial correlation between scores and correctness
  - **Confound controls**: Include bug complexity (lines of code, cyclomatic complexity), test suite quality flags, and model uncertainty as covariates
  - **Stratified analysis**: By bug complexity tier (low/medium/high)
- **FR-008**: Fit logistic regression models and evaluate via AUC-ROC
- **FR-009**: Perform paired t-tests with Bonferroni correction (α = 0.05 / 6 = 0.0083)
- **Power analysis**: Minimum detectable correlation ≈0.30 for n=50 at [deferred] power (documented, not deferred)

### Phase 6: Validation & Documentation (Week 4)
- Contract tests against YAML schemas
- Reproducibility verification (re-run on fresh runner)
- Finalize quickstart.md and research.md

