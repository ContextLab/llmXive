# Research: Automated AI Skill Generation via Expert Knowledge Distillation

## Executive Summary

This research validates the feasibility of reproducing the COLLEAGUE.SKILL paper's distillation pipeline using local, CPU-tractable methods. The core finding is that the "distillation" described in the paper can be implemented as a **deterministic text-processing workflow** using predefined prompt templates and example traces (`example_tianyi`), without requiring external LLM APIs or GPU resources. 

**Critical Distinction**: The project validates the **Artifact Format Reproducibility** (can we generate the correct files?) and **Pipeline Logic** (does the workflow run?), but **cannot** validate the **Scientific Efficacy** of the distillation method (i.e., whether the extracted content represents "true" expert knowledge). The "distillation" is a **Template Artifact Generation** process, not a **Knowledge Extraction** process.

## Dataset Strategy

The project relies on the `example_tianyi` dataset provided within the repository for the primary reproduction workflow. No external datasets are required for the core logic, as the "distillation" is a procedural generation based on the provided trace.

| Dataset Name | Source / URL | Format | Relevance to Spec | Notes |
|--------------|--------------|--------|-------------------|-------|
| `example_tianyi` | **Local Repository** (`examples/example_tianyi/`) | Text/JSONL | **Primary Input** | Contains the expert trace data used to distill the skill. |
| `example_jiaxiu` | **Local Repository** (`examples/example_jiaxiu/`) | Text/JSONL | **Secondary Input** | Used for optional secondary validation if `example_tianyi` is insufficient. |
| **NO External Dataset** | N/A | N/A | N/A | The spec assumes local data is sufficient. No external URL is cited or needed for the core reproduction. |

**Rationale**: The spec explicitly states the assumption that `example_tianyi` and `example_jiaxiu` are sufficient. Using external datasets would introduce unnecessary complexity and potential API dependency issues, violating the "no external LLM calls" constraint for the core logic.

## Technical Approach

### 1. Distillation Logic (Procedural Generation / Template Artifact)
The "distillation" process is implemented as a multi-step text processing pipeline:
1.  **Intake**: Load the input trace (`example_tianyi`). Validate format and content (Edge Cases: empty/malformed).
2.  **Extraction**: Apply predefined prompt templates to the trace to extract:
    *   **Mental Models**: Core principles, heuristics, and decision-making frameworks (Capability Track). *Note: These are extracted via pattern matching, not latent reasoning.*
    *   **Communication Style**: Tone, phrasing, and interaction rules (Bounded Behavior Track). *Note: These are extracted via pattern matching, not style transfer.*
3.  **Synthesis**: Format the extracted content into `persona.md` and `work.md` using Markdown templates.
4.  **Metadata**: Generate `meta.json` with `skill_id`, `version`, and `source`.

**Why this approach?**
*   **CPU Feasibility**: Text processing and template rendering are lightweight operations, easily running on a 2-core CPU runner.
*   **Reproducibility**: Deterministic templates ensure the same input produces the same output, crucial for validation.
*   **No External Dependencies**: Avoids rate limits, costs, and latency of external LLM APIs.
*   **Limitation**: This approach validates the **Format** and **Pipeline**, not the **Scientific Claim** of the paper.

### 2. Validation Strategy
*   **Schema Validation**: All generated artifacts are validated against `tools/skill_schema.py` (JSON Schema) to ensure structural correctness (FR-002, SC-002).
*   **Content Validation**: A custom validator (`content_checker.py`) uses **Keyword Density** and **Section Presence** to verify the presence of ≥3 distinct heuristics (SC-004). This is a **Syntactic Proxy** for semantic content.
*   **Installation Simulation**: The `install_claude_generated_skill.py` script parses the generated package to confirm it is consumable by downstream agents (FR-005, SC-003).

### 3. Error Handling & Robustness
*   **Input Validation**: The `intake.py` module checks for empty files, missing fields, and malformed JSON/CSV. It fails fast with a descriptive error (FR-006).
*   **Retry Logic**: If the pipeline simulates API calls (e.g., for validation checks), it implements exponential backoff with a limited number of retries (Edge Cases).
*   **PII Check**: A basic regex check flags potential PII (email, phone) in `persona.md` (Edge Cases).

## Compute Feasibility Analysis

| Component | Resource Requirement | Feasibility on Free CI (2 CPU, 7GB RAM) |
|-----------|---------------------|------------------------------------------|
| **Data Loading** | < 100 MB RAM | **Yes** |
| **Text Processing** | < 500 MB RAM | **Yes** |
| **Schema Validation** | < 100 MB RAM | **Yes** |
| **Template Rendering** | < 100 MB RAM | **Yes** |
| **Total Runtime** | < 10 minutes | **Yes** (Well [deferred] limit) |

**Conclusion**: The entire workflow is CPU-tractable and fits comfortably within the CI constraints. No GPU or heavy model training is required.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Insufficient Content in Example Data** | Generated `persona.md` may lack 3 distinct heuristics (SC-004). | Use `example_jiaxiu` as a fallback; enhance prompt templates to extract more detail; flag as a spec gap if data is truly insufficient. |
| **Schema Mismatch** | `tools/skill_schema.py` may not fully capture the paper's "bounded behavior" track. | Review the paper's definitions and update the schema in `contracts/` before implementation. |
| **External API Dependency** | Accidental use of external LLM calls in `distillation/`. | Strictly enforce the use of local prompt templates; add unit tests to verify no network calls are made. |
| **Scientific Validity Gap** | The project cannot validate the *quality* of the distillation, only the *format*. | Explicitly document this limitation in the final report. The project validates **Pipeline Reproducibility**, not **Method Efficacy**. |

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **Use local prompt templates instead of external LLM** | Ensures reproducibility, avoids API costs/rate limits, and guarantees CPU feasibility. Acknowledges this changes the mechanism from the paper's claim. |
| **Prioritize `example_tianyi` for reproduction** | Spec explicitly mentions it as the primary example. |
| **Implement strict schema validation** | Critical for ensuring the output is a valid "Skill Package" and not just text. |
| **Include PII check in validation** | Addresses the security edge case mentioned in the spec, even if data is synthetic. |
| **Use Keyword Density for SC-004** | A more robust proxy than header counting, though still a syntactic measure. |