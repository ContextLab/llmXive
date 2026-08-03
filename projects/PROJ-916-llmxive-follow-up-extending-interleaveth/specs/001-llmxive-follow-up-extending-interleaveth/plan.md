# Implementation Plan: llmXive follow-up: extending "InterleaveThinker: Reinforcing Agentic Interleaved Generation"

**Branch**: `001-llmxive-interleave-structure-vs-modality` | **Date**: 2026-08-03 | **Spec**: `specs/001-llmxive-follow-up-extending-interleaveth/spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-interleaveth/spec.md`

## Summary

This feature extends the "InterleaveThinker" research by isolating the impact of **structural decomposition** (iterative planning/critiquing loops) from **representational fidelity** (perfect vs. noisy structured text). 

**Reframed Hypothesis**: The study now explicitly tests whether **iterative agentic structure** improves reasoning robustness against **semantic uncertainty** in text-based scene descriptions. 
*   **Original Goal**: "Structure vs. Modality" (Visual vs. Text).
*   **Revised Goal**: "Structure vs. Single-Pass" within a **Text-Only** modality, using **Human-Annotated Scene Graphs** (from Visual Genome/GQA) as the independent ground truth.
*   **Rationale**: Without access to actual pixel-based generation, simulating "visual grounding" is methodologically invalid. Instead, we simulate "semantic uncertainty" (noise in the structured representation) to test the robustness of the agentic loop. The core question becomes: *Does the iterative Critic loop significantly improve the recovery of the true scene graph from a noisy input compared to a single-pass generator?*

**Technical Approach**:
1.  **Dataset**: Use **Visual Genome** (scene graph subset) and **GQA** (scene graph subset) which provide image prompts (captions) and **Human-Annotated Scene Graphs** (objects, relationships).
2.  **Simulator**: Converts the text caption into a **Candidate Scene Graph** (JSON). 
    *   *Perfect Mode*: Deterministic parsing (high fidelity).
    *   *Noisy Mode*: Injects controlled semantic noise (e.g., swapped relationships, missing objects) into the **simulator output** to simulate the "grounding gap" as *representational uncertainty*. The **Ground Truth** for scoring remains the **original, un-noised Human-Annotated Scene Graph**.
3.  **Pipeline**: Executes the agentic loop (Planner → Generator → Critic) using the Candidate Scene Graph as input. The Generator attempts to reconstruct the **Human-Annotated Scene Graph** (Ground Truth).
4.  **Metric**: **ReasoningScore** is the F1-score (or Graph Edit Distance) between the Generator's output and the **Human-Annotated Scene Graph**. This breaks the circularity by using an independent ground truth.
5.  **Ablation**: Compare "Full Loop" vs. "No-Critic" (Single-Pass) to quantify the structural gain.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (CPU-optimized), `datasets` (streaming), `scikit-learn`, `torch` (CPU), `pyyaml`, `pytest`, `networkx` (for graph metrics)  
**Storage**: Local `data/` directory (checksummed), temporary `data/intermediate/` for streaming shards  
**Testing**: `pytest` (unit), `pytest-benchmark` (latency), contract tests against YAML schemas  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7GB RAM)  
**Project Type**: Research Pipeline / CLI Tool  
**Performance Goals**: <6 hours total runtime per CI job; <16GB RAM usage; <500ms latency for simulator JSON generation  
**Constraints**: No GPU access on CI; no external image generation APIs; strict memory limits for LLM inference  
**Scale/Scope**: Visual Genome and GQA scene graph subsets (streamed); ~100-500 benchmark samples for statistical power  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

**Fallback Strategy**: The plan explicitly states that SFT-80k/112k datasets are **NOT** used due to lack of verified source for scene graph pairs. Instead, the experiment relies on **few-shot prompting** with Visual Genome/GQA annotations.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Plan mandates pinned `requirements.txt`, random seed management, and re-runnable scripts on fresh runners. |
| **II. Verified Accuracy** | **Compliant** | Plan restricts dataset citations to the "Verified datasets" block (Visual Genome, GQA). SFT-112k gap is addressed via few-shot fallback. |
| **III. Data Hygiene** | **Compliant** | Plan includes checksumming for all `data/` artifacts and a `simulator_validation/` subdirectory to log `simulator_error_rate` against **Human-Annotated Scene Graphs**. |
| **IV. Single Source of Truth** | **Compliant** | All statistical reports (`statistical_significance_report.md`) will be auto-generated from `data/` logs, not hand-typed. |
| **V. Versioning Discipline** | **Compliant** | Plan includes content hash generation for artifacts; state updates will be triggered by the Advancement-Evaluator. |
| **VI. Modality-Agnostic Structural Validation** | **Compliant** | Plan explicitly includes the `simulator_validation` step (FR-009) to compare JSON output against **Human-Annotated Scene Graphs** (from Visual Genome/GQA), logging discrepancies as `simulator_error_rate` (Graph Edit Distance). |
| **VII. Statistical Rigor in Agent Ablation** | **Compliant** | Plan mandates paired t-tests/Wilcoxon tests for Full Loop vs. No-Critic ablation (FR-004, FR-005) and outputs effect sizes (Cohen's d) in `statistical_significance_report.md`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-interleave-structure-vs-modality/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── scene.schema.yaml
│   ├── trajectory.schema.yaml
│   └── stats.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-916-llmxive-follow-up-extending-interleaveth/code/
├── data/
│   ├── raw/                 # Downloaded datasets (checksummed)
│   ├── intermediate/        # Streaming shards, temporary JSON logs
│   └── simulator_validation/# Ground truth comparisons, error rates (Graph Edit Distance)
├── src/
│   ├── __init__.py
│   ├── simulator/           # Text-based scene simulator (Perfect/Noisy modes)
│   ├── agents/              # Planner, Generator, Critic logic
│   ├── pipeline/            # Orchestration of the agentic loop
│   ├── benchmarks/          # Visual Genome/GQA loaders and evaluators
│   └── stats/               # Statistical analysis and reporting
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/            # Schema validation tests
├── requirements.txt
└── run_experiment.py        # Entry point for CI execution
```

**Structure Decision**: Single project structure selected to minimize overhead and ensure tight integration between the simulator, agents, and statistical reporting. This aligns with the "Research Pipeline" project type and allows for efficient memory management on the CI runner.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **No GPU Escape Hatch** | The hypothesis requires CPU-only execution to prove structural gains are independent of visual modality (and to prove robustness to noise). | A GPU-based approach would conflate modality benefits with structural benefits, failing the core research question. |
| **Streaming Data** | Datasets (Visual Genome/GQA) may exceed CI RAM limits if fully loaded. | Loading full datasets into memory would cause OOM errors; streaming ensures feasibility within 7GB RAM. |
| **Ablation Study** | Required to isolate the "Critic Loop" contribution from the baseline. | Comparing only "Text vs. Image" would not answer whether *structure* drives the gain; the ablation is essential for causal inference on structure. |
| **Few-Shot Fallback** | SFT-112k dataset is unavailable. | Fine-tuning is not required; the experiment relies on few-shot prompting with the benchmark's own annotations as context. |

## Methodology Overview

1.  **Data Ingestion**: Load Visual Genome/GQA Scene Graphs.
2.  **Simulator**: Parse text captions into JSON (Perfect/Noisy). Validate against **Human-Annotated Scene Graphs** to compute `simulator_error_rate`.
3.  **Agentic Loop**: Run Generator (reconstructs scene from JSON) → Critic (evaluates against prompt/JSON) → Planner (iterates).
4.  **Evaluation**: Compute `ReasoningScore` (F1/GED) against **Human-Annotated Scene Graphs**.
5.  **Ablation**: Compare Full Loop vs. No-Critic.
6.  **Statistics**: Paired t-test/Wilcoxon for significance.
7.  **Stratification**: Control for Generator Error Rate in statistical analysis.