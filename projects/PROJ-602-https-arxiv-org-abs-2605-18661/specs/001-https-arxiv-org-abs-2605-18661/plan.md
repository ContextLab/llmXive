# Implementation Plan: AI for Auto-Research: Roadmap & User Guide Reproduction

**Branch**: `602-reproduce-auto-research` | **Date**: 2026-05-22 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/602-reproduce-auto-research/spec.md`

## Summary

This project executes a reproduction study of the paper "AI for Auto-Research: Roadmap & User Guide" (arXiv:2605.18661) using vendored code from `external/awesome-ai-auto-research`. The primary goal is to validate the pipeline's ability to generate distinct artifacts (text, figures, data) and log resource usage on a CPU-only CI environment.

**Critical Constraint Handling**: The plan explicitly distinguishes between **Structural Reproducibility** (can the code run?) and **Claim Validation** (did it achieve the results?).
1.  **Structural Validation**: Run the pipeline (using mocks if necessary) to confirm artifact generation and code execution.
2.  **Semantic Validation**: Use lightweight CPU-tractable embedding models to detect obvious hallucination patterns.
3.  **Transparency**: If the environment forces "Mock Mode" (no real LLM inference), the `REPRODUCTION_REPORT.md` will explicitly mark "Cost" and "True Novelty" claims as **Unverifiable**. This prevents a construct validity failure where mock output is falsely validated against real-world claims.

The implementation strictly adheres to the "free-tier" compute constraints (2 CPU, 7GB RAM, 6h limit).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pytest`, `pyyaml`, `requests`, `matplotlib`, `pandas`, `sentence-transformers` (for CPU-tractable semantic checks), `tenacity` (for retries), `torch` (CPU-only version).  
**Storage**: Local filesystem (`output/` directory for artifacts, `logs/` for execution traces).  
**Testing**: `pytest` (Unit tests for validation logic, integration tests for pipeline execution).  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 vCPU, 7GB RAM).  
**Project Type**: CLI / Reproduction Pipeline  
**Performance Goals**: Pipeline execution < 6 hours; Artifact generation < 5 minutes per phase; Memory usage < 6GB.  
**Constraints**: No GPU/CUDA; No external paid API calls without explicit logging; No hallucinated citations in validation logic.  
**Scale/Scope**: Single pipeline run; 3 artifact types; 1 validation report.

> **Dataset/Resource Note**: This project relies on the vendored code `external/awesome-ai-auto-research`. No external datasets are downloaded. If the vendor code requires external API keys, the reproduction will use a "Mock Mode" or a local CPU-tractable fallback (e.g., `llama-cpp-python` with a 1.5B quantized model if size permits, otherwise a deterministic mock generator) to satisfy the "no GPU" requirement.

## Project Principles

*Since no specific `constitution.md` was supplied for this project (FR-030), the plan adheres to the following principles derived directly from the Project's Success Criteria and Assumptions:*

1.  **Reproducibility**: The plan documents the environment (CPU-only) and explicitly adapts heavy methods to feasible approximations (mocks/embeddings), ensuring the study is runnable by others.
2.  **Integrity**: The validation logic (FR-004, SC-005) uses a hybrid approach (heuristics + embeddings) to detect fabrication, and explicitly flags "Unverifiable" claims rather than faking a pass.
3.  **Transparency**: The `REPRODUCTION_REPORT.md` (FR-005) mandates the disclosure of all methodological deviations (e.g., CPU vs GPU, mock vs real inference, semantic limitations).
4.  **Feasibility**: The plan prioritizes CPU-tractable methods and strict resource limits, ensuring the project does not stall on free-tier infrastructure.
5.  **No Silent Fallbacks**: The plan explicitly includes a "CUDA Patcher" step to ensure the code does not fail silently if GPU is missing; it must either run on CPU or fail with a clear error.

## Project Structure

### Documentation (this feature)

```text
specs/602-reproduce-auto-research/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
external/
└── awesome-ai-auto-research/  # Vendored git submodule (read-only)

src/
├── reproduction/
│   ├── __init__.py
│   ├── pipeline_runner.py     # Executes vendor entry point (with CUDA patching)
│   ├── validation.py          # Checks artifacts (Heuristic + Embedding)
│   ├── cost_estimator.py      # Parses logs for cost calculation
│   └── report_generator.py    # Generates REPRODUCTION_REPORT.md
├── mocks/
│   └── llm_mock.py            # CPU-safe fallback if vendor requires GPU
├── utils/
│   └── cuda_patcher.py        # Forces CPU mode / bypasses CUDA checks
└── main.py                    # Entry point for CI

tests/
├── unit/
│   ├── test_validation.py
│   └── test_cost_estimator.py
├── integration/
│   └── test_pipeline_e2e.py
└── contract/
    └── test_artifact_schemas.py
```

**Structure Decision**: A modular `src/reproduction` structure is chosen to isolate the vendor code from the validation and reporting logic. This ensures that the reproduction logic can be tested independently of the vendor code's specific implementation details, facilitating the "Methodological Deviation" reporting required by FR-005.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Mock/Adaptation Layer | The vendor code may require GPU/CUDA or heavy LLMs incompatible with free-tier CI. | A direct run would fail immediately, preventing any artifact generation or validation. |
| Hybrid Validation | Pure heuristics are insufficient for semantic fabrication; full LLM judges are too heavy. | A single "pass/fail" check cannot capture the specific "fabrication" or "cost" metrics required by SC-004/SC-005. |
| "Unverifiable" State | Real inference is impossible on CPU. | Falsely validating mock data against real-world claims is a scientific integrity failure. |

## Plan Completeness & Methodological Rigor

### FR/SC Coverage Mapping

| Requirement ID | Plan Phase/Step | Description |
| :--- | :--- | :--- |
| **FR-001** (No GPU) | `src/utils/cuda_patcher.py` + `reproduction/pipeline_runner.py` | **Explicit CUDA Patching**: `cuda_patcher.py` forcibly injects `torch.set_device('cpu')` and patches `torch.cuda.is_available()` to return `False`. This prevents vendor code from failing on initialization. If patching fails, the run aborts with a clear "GPU Required" error (no silent failure). |
| **FR-002** (3 Artifacts) | `reproduction/pipeline_runner.py` | Validates output directory post-run; asserts existence of `.md`, `.png`, `.csv` (or equivalent). |
| **FR-003** (Cost Log) | `reproduction/cost_estimator.py` | Parses `logs/api_usage.json`; calculates total cost; handles missing logs gracefully (reports "N/A" if mock mode). |
| **FR-004** (Fabrication) | `reproduction/validation.py` | **Hybrid Check**: 1. **Structural** (empty strings, "TODO" - for empty content). 2. **Semantic** (embedding similarity to known hallucination patterns via `all-MiniLM-L6-v2`). Reports a `fabrication_score`. |
| **FR-005** (Report) | `reproduction/report_generator.py` | Aggregates logs, validation results, and environment info into `REPRODUCTION_REPORT.md`. Includes "Methodological Limitations" section. |
| **FR-006** (Retry) | `reproduction/pipeline_runner.py` | Wraps external calls with `tenacity` (or custom) retry logic (limited number of attempts, exponential backoff). |
| **SC-001** (6h/CI) | `tests/integration/test_pipeline_e2e.py` | Simulates run; asserts completion time < 6h (mocked for speed); asserts exit code 0. |
| **SC-002** (3 Non-empty) | `reproduction/validation.py` | Checks file size > 0 and format validity. |
| **SC-003** (Deviations) | `reproduction/report_generator.py` | Explicitly logs "No GPU" and any "Mocked Inference" events. |
| **SC-004** (Cost Value) | `reproduction/cost_estimator.py` | Outputs numeric value or "N/A" with justification if logs missing or mock mode active. |
| **SC-005** (Fabrication Check) | `reproduction/validation.py` | Computes `fabrication_score`. **Threshold Logic**: If score > 0.8, flag as "Fabrication Detected". Report lists "Unverifiable" for novelty if mock mode used. |

### Validation Tiering & Thresholds

To address the gap between continuous scores and binary success criteria:
- **Fabrication Score**: A float [0.0, 1.0] calculated by `validation.py`.
  - **0.0-0.4**: Likely Authentic.
  - **0.4-0.8**: Ambiguous (requires manual review).
  - **0.8-1.0**: High Risk (Fabrication Detected).
- **Success Criterion (SC-005)**: The system passes if it correctly identifies content with a score > 0.8 as "Fabrication Detected".
- **Novelty/Cost Claims**: If the pipeline runs in "Mock Mode", these claims are **not** validated. The report will state: "Claim X is Unverifiable due to CPU-only constraints."

### Statistical & Methodological Notes
- **Causal/Associational**: This is a reproduction study, not a hypothesis test on new data. Claims are limited to "The vendor code produces X under Y conditions."
- **Power/Sample Size**: Not applicable for a single pipeline run.
- **Measurement Validity**: The "fabrication" check uses a hybrid approach. The report will explicitly state: "Detection relies on syntactic heuristics for empty content and lightweight embeddings for semantic hallucination. Subtle hallucinations may be missed." This transparency satisfies the integrity requirement.

### Compute Feasibility Strategy
- **No GPU**: All heavy inference is replaced by `src/mocks/llm_mock.py` which generates deterministic, short text blocks. If the vendor code *must* run a model, `llama-cpp-python` with a 1.5B parameter quantized model (GGUF) will be attempted only if the dataset is tiny (<100MB). Otherwise, mock mode is the default.
- **Memory**: Data is processed in streaming fashion where possible; large files are not loaded entirely into RAM.
- **Runtime**: The "Creation" phase is capped at 30 minutes. If the vendor code exceeds this, the run is terminated and logged as a "Timeout Deviation."
- **Semantic Check**: Uses a sentence-transformers model that is CPU-tractable and fits within RAM limits.

### Methodological Limitations (Mandatory in Report)
The `REPRODUCTION_REPORT.md` will include a section:
> **Limitations**:
> 1. **Semantic Validity**: Fabrication detection relies on heuristics and lightweight embeddings; it cannot guarantee the absence of all hallucinations.
> 2. **Cost/Novelty Claims**: These claims are marked "Unverifiable" if the pipeline runs in Mock Mode due to CPU constraints.
> 3. **Dataset**: No external datasets were used; validation is limited to the vendor code's internal logic.

## Project Principles (Final)

*Referencing the fallback principles defined above:*
- **Reproducibility**: Met via detailed environment documentation.
- **Integrity**: Met via "Unverifiable" flags and hybrid validation.
- **Transparency**: Met via the mandatory "Limitations" section.
- **Feasibility**: Met via CPU-tractable methods.
- **No Silent Fallbacks**: Met via explicit CUDA patching and error handling.