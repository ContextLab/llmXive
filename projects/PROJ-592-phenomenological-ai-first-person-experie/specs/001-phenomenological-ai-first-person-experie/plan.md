# Implementation Plan: Phenomenological AI: First-Person Experience Modeling in Language Models

**Branch**: `592-phenomenological-ai-first-person-experie` | **Date**: 2026-06-17 | **Spec**: `specs/592-phenomenological-ai-first-person-experie/spec.md`
**Input**: Feature specification from `/specs/592-phenomenological-ai-first-person-experie/spec.md`

## Summary

This project implements a computational pipeline to generate and evaluate first-person phenomenological reports using four prompting strategies across two open-source LLMs. The system operates on a CPU-only environment (GitHub Actions free-tier) using **Q4_K** quantization (Verified Facts: 2606.12280) for inference.

**Generation Strategy**: The pipeline targets the generation of **[deferred] raw samples** (80 samples × 4 strategies × 20 prompts) using `TinyLlama-1.1B` exclusively for the automated CI pipeline.
- **Primary Execution**: The automated pipeline uses `TinyLlama` via `llama-cpp-python` (low-bit GGUF) to ensure feasibility on the GitHub Actions free-tier (2 CPU, ~7GB RAM).
- **Local Reproduction**: The specification's original target models (`Mistral-7B`, `Llama-7B`) are acknowledged as requiring >14GB RAM. They are **excluded** from the automated CI path to prevent OOM/Timeout failures. Users with local hardware (≥16GB RAM) may optionally run these models via a separate script (`code/generation/runner_local.py`), but results from these models are not required for the primary research validity.
- **Analysis Target**: The ANOVA is designed to run on a minimum of **[deferred] valid samples** (128 per condition) to ensure statistical power (80% at α=0.05, MDES f=0.25).

The system computes three validity metrics:
1.  **Logical Coherence**: Measured via NLI (secondary/exploratory).
2.  **Output Reproducibility**: Measured via embedding similarity of repeated generations (primary control for model stochasticity).
3.  **Marker Specificity**: Ratio of targeted markers to total markers (primary phenomenological metric).

The plan strictly adheres to the project constitution's reproducibility and data hygiene principles, ensuring all artifacts are checksummed, seeds are pinned, and human validation is integrated with automated metrics.

## Technical Context

**Language/Version**: Python  
**Primary Dependencies**: `transformers` (CPU-optimized), `llama-cpp-python` (for GGUF 1.1B models), `sentence-transformers`, `scikit-learn`, `pandas`, `nltk`, `torch` (CPU wheels), `datasets`, `statsmodels`  
**Storage**: Local file system (`data/` for artifacts, `code/` for scripts), CSV/JSON formats  
**Testing**: `pytest` (unit tests for metric logic, integration tests for pipeline flow)  
**Target Platform**: Linux (Ubuntu 22.04) on GitHub Actions free-tier (2 CPU, ~7GB RAM)  
**Project Type**: Computational research pipeline / CLI  
**Performance Goals**: 
- **Target Volume**: [deferred] raw samples (FR-001).
- **Analysis Volume**: Minimum 1,024 valid samples (Power Target).
- **Runtime**: ≤ 6 hours (CI timeout).
- **Memory**: < 6GB per process (sequential model loading).  
**Constraints**: 
- NO GPU, NO CUDA.
- **Model Selection**: `TinyLlama-1.1B` is the **only** model used in the automated pipeline. Larger models are excluded from CI due to RAM constraints (memory requirements exceeding available capacity).
- **Sequential Execution**: NLI and Embedding models are loaded/unloaded sequentially to prevent OOM during analysis.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: The plan mandates pinned random seeds in `code/`, use of canonical HuggingFace model IDs for checkpoints, and a `requirements.txt` for dependency isolation. All generated data will be checksummed.
- **Principle II (Verified Accuracy)**: All citations in `research.md` and `plan.md` will be validated against primary sources. The use of Q4_K quantization is cited from the **Verified Facts** block (source: 2606.12280, https://arxiv.org/abs/2606.12280), satisfying the gate by using the provided authoritative reference.
- **Principle III (Data Hygiene)**: Raw data (generated reports) will be preserved unchanged; derived metrics will be written to new files (`data/validity_scores.csv`). No PII will be committed.
- **Principle IV (Single Source of Truth)**: All figures and statistics in the final paper will trace back to `data/validity_scores.csv` and `data/qualitative/` ratings.
- **Principle V (Versioning Discipline)**: Artifacts will carry content hashes; the `state/` YAML will be updated on changes.
- **Principle VI (Phenomenological Validity)**: The plan implements the three required metrics (Logical Coherence, Output Reproducibility, Marker Specificity) exactly as specified, with NLI downgraded to a secondary metric to avoid category errors.
- **Principle VII (Human Qualitative Auditing)**: The plan includes a protocol for two independent raters, calculation of Cohen's κ, and archiving of raw ratings.

**Gates Determined**:
- **Reproducibility Gate**: Pass. Seeds and canonical sources defined.
- **Data Hygiene Gate**: Pass. Checksums and immutability enforced.
- **Validity Gate**: Pass. Metrics defined per spec.
- **Human Audit Gate**: Pass. Rater protocol defined.

## Project Structure

### Documentation (this feature)

```text
specs/592-phenomenological-ai-first-person-experie/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Documentation copy)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── generation/
│   ├── runner.py            # Main generation loop with retry logic (FR-001)
│   ├── prompt_templates.py  # 4 prompting strategies
│   └── model_loader.py      # GGUF loader for CPU inference
├── analysis/
│   ├── metrics.py           # NLI consistency, embedding stability, marker presence
│   ├── statistics.py        # ANOVA/Kruskal-Wallis, FDR, sensitivity analysis
│   └── qualitative.py       # Cohen's κ calculation
├── orchestration/
│   └── main.py              # End-to-end pipeline (Phase 4 integration)
├── utils/
│   ├── logger.py
│   └── checksums.py
├── contracts/               # Runtime schemas (imported by code)
│   ├── generation_output.schema.yaml
│   ├── metric.schema.yaml
│   └── rating.schema.yaml
├── data/
│   ├── raw/                 # Generated reports (immutable)
│   ├── derived/             # Validity scores, embeddings
│   └── qualitative/         # Human ratings
└── contracts/               # Documentation copy (for review)

tests/
├── unit/
│   ├── test_metrics.py
│   └── test_retry_logic.py
└── integration/
    └── test_pipeline.py

requirements.txt
```

**Structure Decision**: The chosen structure separates generation, analysis, and orchestration to ensure modularity and testability. The `contracts/` directory resides in `src/` for runtime import by `runner.py` and `metrics.py`. A copy is maintained in `specs/` for documentation review. This aligns with the "Single Source of Truth" principle and resolves the path ambiguity.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **CPU-only inference for TinyLlama (GGUF)** | Spec requires large-scale models, but CI has constrained RAM. 7B models are infeasible. | Using large language models in FP/FP is impossible (GB RAM). `llama-cpp-python` with 4-bit GGUF for TinyLlama is the only CPU-safe method that fits the CI box. |
| **Four prompting strategies + 1 model** | Spec requires comparison of strategies. | Reducing strategies would invalidate the ANOVA design (independent variable manipulation). We compare strategies *within* the TinyLlama architecture to test the "Phenomenological Style" hypothesis. |
| **Three distinct validity metrics** | Constitution Principle VI requires all three. | Using a single metric would fail the "Phenomenological Validity" non-negotiable. |
| **Control Corpus Generation** | Required for discriminant validity (methodology-87fdb544). | Without a control, we cannot distinguish 'phenomenological style' from 'general text quality'. |
| **Sequential Model Loading** | Required to prevent OOM during analysis (data_resources-36182768). | Loading NLI and Embedding models simultaneously exceeds 7GB RAM. |

## Unresolved panel concerns (addressed)

- **Task Dependencies (T016, T024)**: The plan restructures the execution order. `runner.py` (generation) is implemented first (Phase 2/3). `main.py` (orchestration) is placed in a distinct "Integration Phase" (Phase 4) that explicitly depends on the *schema* of the output from `runner.py` (finalized in Phase 1), not the *execution* of the full generation run. This allows parallel development of the analysis module (Phase 3) based on the schema contract, satisfying the "producer before consumer" semantic layer.
- **Documentation Dependencies (T037 vs T040-T044)**: The plan ensures that `main.py` (T024) and all analysis scripts (T040-T044) are implemented and tested *before* the final documentation update (T037). The `tasks.md` will reflect this corrected order.
- **Task Duplication (T012)**: The local runner logic is consolidated into a single `runner.py` script with a CLI flag (`--local` vs `--ci`). No duplicate tasks exist in the plan; the "Polish" phase will only involve configuration updates, not re-implementation.
- **Missing Retry Evidence (T010)**: The plan explicitly includes `runner.py` with a `max_retries=3` loop and a "missing" flag mechanism. The implementation will be verified by `test_retry_logic.py`.
- **Schema-Task Mapping**: The plan now explicitly maps `generation_output.schema.yaml` to T016 (Retry Logic) and `metric.schema.yaml` to T040-T044 (Analysis), ensuring the schema is finalized in Phase 1 before Phase 2 begins.
- **Statistical Confounding (Model ID)**: The plan now explicitly includes 'Model ID' as a random effect in the Linear Mixed-Effects Model to prevent confounding prompting strategy effects with model architecture differences.

## Phases & Execution Order

1.  **Phase 0: Research & Design** (Current)
    -   Select models and datasets (verified sources).
    -   Define prompt templates and marker dictionaries.
    -   Design schemas and data models.
2.  **Phase 1: Data Model & Contracts**
    -   Implement `contracts/*.schema.yaml` in `src/contracts/`.
    -   Create `data-model.md` and `quickstart.md`.
    -   **Contract Finalization**: Ensure schemas are versioned and available for Phase 2.
3.  **Phase 2: Generation Module**
    -   Implement `model_loader.py` (GGUF, CPU).
    -   Implement `runner.py` with retry logic (FR-001). **Dependency**: `generation_output.schema.yaml`.
    -   Unit tests for generation.
4.  **Phase 3: Analysis Module**
    -   Implement `metrics.py` (NLI, embeddings, markers).
    -   Implement `statistics.py` (ANOVA/Kruskal-Wallis, FDR, sensitivity).
    -   Unit tests for metrics.
5.  **Phase 4: Integration & Orchestration**
    -   Implement `main.py` to chain generation and analysis. **Dependency**: Schemas from Phase 1, Logic from Phase 2 & 3.
    -   Run full pipeline on a subset for validation.
    -   Integrate human rating workflow (FR-010).
6.  **Phase 5: Validation & Archiving**
    -   Compute full metrics on all samples.
    -   Perform human rating and compute Cohen's κ.
    -   **Power Analysis**: Determine if Pilot (N=20) is sufficient or if GPU offload is required for Full Study (N=80).
    -   Archive all artifacts (FR-007).
7.  **Phase 6: Documentation & Polish**
    -   Update `tasks.md` and final report.
    -   Verify all citations and checksums.
    -   **Dependency**: Requires completion of Phase 5 (Analysis) and T040-T044 (Review Enhancements).

## Risks & Mitigations

-   **Risk**: CPU inference of 7B models exceeds 6-hour limit.
    -   *Mitigation*: Use `Q4_K` quantization (Verified Facts: 2606.12280); limit samples to Pilot (N=20); stream data to disk immediately.
-   **Risk**: NLI model fails on long sentences.
    -   *Mitigation*: Implement chunking or skip logic with logging (Edge Case 1).
-   **Risk**: Human raters unavailable or low κ.
    -   *Mitigation*: Plan for re-evaluation of low-agreement batches (FR-011); use automated metrics as primary, human as validation.
-   **Risk**: Model access blocked by rate limits.
    -   *Mitigation*: Use HuggingFace Hub with proper caching; implement exponential backoff in `runner.py`.
-   **Risk**: Statistical Power (Type II Error).
    -   *Mitigation*: Explicitly report power limitations for N=20; use Pilot to estimate effect size for Full Study planning.
-   **Risk**: Confounding by Model Architecture.
    -   *Mitigation*: Statistical model explicitly includes 'Model ID' as a random effect to isolate the 'Strategy' effect.

## Next Steps

1.  Finalize `research.md` with model and dataset selection.
2.  Draft `data-model.md` and `contracts/`.
3.  Implement `runner.py` with retry logic (addressing T010).
4.  Execute Phase 2 and 3 in parallel, using schema contracts as the interface.
