# Implementation Plan: llmXive follow-up: extending "MemGUI-Agent: An End-to-End Long-Horizon Mobile GUI Agent with Proacti"

**Branch**: `001-llmxive-long-horizon-context` | **Date**: 2026-09-07 | **Spec**: `specs/001-llmxive-long-horizon-context/spec.md`

## Summary

This project investigates whether the "Context-as-Action" (ConAct) mechanism in mobile GUI agents suffers from information decay in ultra-long horizons (50+ steps) and if a lightweight semantic recall module can restore success rates. The implementation will construct a synthetic ultra-long-horizon benchmark using procedural generation based on verified UI state templates, execute a CPU-only baseline agent (MemGUI-SFT, -bit quantized) to measure decay, implement a retrieval-augmented agent using a pre-trained sentence embedding model, and perform a Mixed-Effects Logistic Regression (GLMM) to validate efficacy while controlling for trajectory-level clustering.

## Technical Context

**Language/Version**: Python  
**Primary Dependencies**: `transformers` (CPU-only, 4-bit quantization), `sentence-transformers` (`all-MiniLM-L6-v2`), `datasets` (streaming), `statsmodels` (GLMM), `scipy`, `accelerate` (CPU configuration), `pandas`, `pytest`, `bitsandbytes` (for 4-bit quantization).  
**Storage**: Local filesystem for synthetic JSONL trajectories, execution logs, and model weights (cached).  
**Testing**: `pytest` for unit tests (data generation logic, retrieval logic), integration tests for end-to-end trajectory execution.  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, 7GB RAM).  
**Project Type**: Computational Research / Data Analysis Pipeline.  
**Performance Goals**: Execution of trajectories (-60 steps each) within 6 hours on CPU; recall overhead <10% latency increase.  
**Constraints**: No GPU access on CI (CPU-only inference for baseline); strict memory limits (modest RAM capacity); no external data access (must use verified Hugging Face datasets or local synthetic generation).  
**Scale/Scope**: A set of synthetic trajectories (reduced from 50 to fit memory); [deferred] total steps; retrieval model; baseline agent.

> **Dataset Note**: The spec references "MemGUI-3K" and "MemGUI-8B-SFT". The verified datasets list provided for this project **does not** contain a verified URL for the MemGUI dataset. The plan **does not** rely on MemGUI-3K for data generation. Instead, it uses a **procedural generator** based on state templates derived from the verified `UltraData-SFT-Agent-2609` dataset (abstracted to mobile-like semantics) to ensure the benchmark is fully self-contained and not gated. The MemGUI model is assumed to be accessible via Hugging Face for inference; if not, the study pivots to a verified substitute model (e.g., a compact instruct model). which is pre-verified.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

1.  **Reproducibility (Principle I)**: The plan mandates pinning all dependencies in `requirements.txt` and using deterministic random seeds for synthetic trajectory generation. The baseline and recall agents will use frozen weights.
2.  **Verified Accuracy (Principle II)**: Citations to the MemGUI paper and `all-MiniLM-L6-v2` will be validated. **Critical Gap**: The spec relies on "MemGUI-3K" and "MemGUI-8B-SFT". The provided "Verified datasets" block **does not** list these. The plan explicitly handles this by using a **procedural generation method** based on verified state templates (from `UltraData-SFT-Agent`) for the benchmark, ensuring the data layer is not gated. Any pivot to a substitute model (e.g., Phi-3) must be pre-verified in the "Verified datasets" block before execution, as required by the Constitution's Verified Accuracy gate.
3.  **Data Hygiene (Principle III)**: Synthetic trajectories will be generated once, checksummed, and stored in `data/synthetic_benchmark/`. No raw data modification.
4.  **Single Source of Truth (Principle IV)**: Every figure, statistic, or interpretation in the paper MUST trace back to exactly one row in this project's `data/` and one block in this project's `code/`. Derived numbers MUST NOT be hand-typed into the paper. All success rates and latency metrics will be derived from `data/` logs and `code/` analysis scripts.
5.  **Versioning Discipline (Principle V)**: Every artifact under this project carries a content hash. The Advancement-Evaluator Agent invalidates stale review records when the hashed artifact changes. Every research-stage artifact change updates this project's `state/projects/PROJ-964-llmxive-follow-up-extending-memgui-agent.yaml` `updated_at` timestamp.
6.  **Context Integrity in Long-Horizon Evaluation (Principle VI)**: Every evaluation of the "Context-as-Action" (ConAct) baseline versus the semantic recall extension MUST explicitly isolate the variable of "context retrieval" by keeping the base policy weights frozen, as specified in the Methodology sketch. Success rates MUST be measured on a synthetic ultra-long-horizon test set (multiple steps) constructed to require retrieval of information from multiple steps prior., ensuring the experiment directly targets the hypothesized information decay bottleneck rather than general model performance.
7. **Resource-Constrained Inference Validation (Principle VII)**: Every claim regarding the efficacy of the lightweight semantic recall module MUST be accompanied by resource profiling data (inference latency and peak memory footprint) demonstrating that the added overhead remains below [deferred] on standard CPU hardware. This principle is grounded in the project's motivation to determine if resource-constrained mobile deployments can rely on efficient inference-time memory augmentation rather than GPU-intensive retraining.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-long-horizon-context/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data_generation/
│   ├── __init__.py
│   ├── synthetic_benchmark.py      # Constructs + step trajectories (procedural)
│   ├── coherence_validator.py      # Validates semantic plausibility of chains
│   └── validator.py                # Checks dependency links
├── agents/
│   ├── __init__.py
│   ├── base_conact.py              # CPU-only MemGUI-8B-SFT wrapper (4-bit)
│   └── recall_agent.py             # Base + retrieval injection
├── retrieval/
│   ├── __init__.py
│   ├── index_builder.py            # Builds FAISS/InMemory index from history
│   └── retriever.py                # Query generation & snippet injection
├── evaluation/
│   ├── __init__.py
│   ├── runner.py                   # Executes trajectories, logs results
│   └── stats.py                    # Mixed-Effects Logistic Regression (GLMM)
├── utils/
│   ├── config.py                   # Seed pinning, path config
│   └── memory_profiler.py          # Peak memory/latency logging
├── main.py                         # Orchestration entry point
└── requirements.txt                # Pinned dependencies
```

**Structure Decision**: Single project structure under `code/` is selected. The workflow is linear: Generate Data -> Validate -> Run Baseline -> Run Recall -> Run Controls -> Analyze. Separation of `agents`, `retrieval`, and `evaluation` ensures modularity for the statistical comparison.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Synthetic Benchmark Generation | Real ultra-long mobile trajectories (tens to hundreds of steps) with explicit cross-app dependencies are not available in public datasets. | Using existing short-horizon datasets would fail to test the "information decay" hypothesis at the required scale (50+ steps). |
| CPU-Only Inference (4-bit) | CI environment lacks GPU; GPU escape hatch is for training/fine-tuning, not for running a 50-step inference chain which is already slow on CPU. | Using a GPU escape hatch for inference would be overkill and potentially exceed the 6h limit if the batch size is large; CPU-first is the constraint. Low-bit quantization is required to fit constrained RAM. |
| Mixed-Effects Logistic Regression | Success rates in small-sample agent experiments often violate normality assumptions and involve hierarchical data (steps within trajectories). | A Wilcoxon signed-rank test on aggregated rates loses granularity and ignores trajectory-level clustering, leading to invalid p-values. |
| Semantic Coherence Validation | Synthetic chains must be semantically plausible to ensure failure is due to memory decay, not illogical state transitions. | Unvalidated synthetic chains risk introducing "artifact failure" as a confounding variable. |
| Negative & Shuffled Controls | To prove semantic retrieval is the active variable, not just "more text" or "presence of correct info". | A simple baseline comparison is insufficient to isolate the retrieval mechanism's contribution. |