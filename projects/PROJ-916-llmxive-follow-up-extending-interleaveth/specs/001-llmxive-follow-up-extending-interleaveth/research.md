# Research: llmXive follow-up: extending "InterleaveThinker: Reinforcing Agentic Interleaved Generation"

## Executive Summary

This research investigates whether the performance gains observed in "InterleaveThinker" are driven by the **iterative agentic structure** (Planning → Generating → Critiquing) or the **visual modality** (pixel-based generation).

**Reframed Scope**: Since the visual modality cannot be simulated in a text-only environment without fabricating visual grounding, the study now focuses on **Structural Decomposition** within a **Text-Only** modality. The "Noisy Mode" simulates **Semantic Uncertainty** (noise in the structured representation) rather than visual grounding gaps. The core question is: *Does the iterative Critic loop significantly improve the recovery of the true scene graph from a noisy input compared to a single-pass generator?*

## Dataset Strategy

The plan relies on the following verified datasets. Where a dataset lacks a verified source, the plan explicitly states the limitation and uses available open substitutes or flags the gap.

| Dataset | Purpose | Verified Source (URL) | Strategy |
|:--- |:--- |:--- |:--- |
| **Visual Genome** | Benchmark for visual reasoning (captions + **Scene Graphs**). | ` | Load via `datasets` library. Use captions as prompts and **Human-Annotated Scene Graphs** as Ground Truth. |
| **GQA** | Benchmark for visual reasoning (captions + **Scene Graphs**). | ` | Load via `datasets` library. Use captions as prompts and **Human-Annotated Scene Graphs** as Ground Truth. |
| **SFT-80k** | **NO verified source found** for scene graph pairs. | **Gap Identified**: The spec assumes availability. The plan will **not** use this dataset. The experiment relies on **few-shot prompting** with Visual Genome/GQA annotations as the primary context. |
| **SFT-112k** | **NO verified source found** for scene graph pairs. | **Gap Identified**: The spec assumes availability. The plan will **not** use this dataset. The experiment relies on **few-shot prompting** with Visual Genome/GQA annotations as the primary context. |
| **GPU-dependent** | Pre-computed image-based results for baseline. | **NO verified source found** | **Gap Identified**: The baseline is a "Single-Pass Text Baseline" (no iterative loop), clearly marking the comparison as "Structure vs. Single-Step". |

## Methodology

### Phase 1: Text-Based Scene Simulator (FR-001, FR-007, FR-009)

1. **Deterministic Parsing**: Implement a parser that converts natural language captions (e.g., "a red cube on a blue sphere") into a `SceneDescription` JSON object.
 * **Perfect Mode**: Deterministic extraction of objects, attributes, and spatial relationships from the caption.
 * **Noisy Mode**: Inject semantic noise (e.g., swap relationships, hallucinate attributes) into the **simulator output** at a target rate (5-15%) to simulate **Semantic Uncertainty**. The noise distribution is calibrated against the **Human-Annotated Scene Graph** (Ground Truth) to ensure realistic degradation (e.g., swapping relationships that exist in the graph, omitting objects).
2. **Validation (Critical)**: Compare simulator output against the **Human-Annotated Scene Graph** (Ground Truth) from Visual Genome/GQA.
 * **Metric**: `simulator_error_rate` = **Graph Edit Distance (GED)** or **F1-score of object/relationship matching** between Simulator Output and Human-Annotated Ground Truth.
 * **Location**: `data/simulator_validation/`.
 * **Ground Truth Provenance**: The Ground Truth is the **native human-annotated scene graph** from Visual Genome/GQA, not derived from a parser, ensuring independence from the simulator's logic.
3. **Ambiguity Handling**: Detect ambiguous spatial relationships and flag samples for exclusion or default to canonical interpretations.

### Phase 2: CPU-Tractable Agentic Loop (FR-002, FR-003, FR-006, FR-008)

1. **Agent Configuration**:
 * **Generator**: Lightweight LLM (e.g., Llama-3-8B or Mistral-7B) in default precision, running on CPU.
 * **Critic**: Evaluates the `SceneDescription` JSON against the prompt and the **Human-Annotated Scene Graph** (if available for validation) or the prompt logic.
 * **Planner**: Orchestrates the loop based on Critic feedback.
2. **Execution**: Run the full trajectory (Planner → Generator → Critic → Planner) on Visual Genome/GQA samples.
 * **Input**: The `SceneDescription` JSON (Perfect or Noisy) generated in Phase 1.
 * **Goal**: The Generator attempts to reconstruct the **Human-Annotated Scene Graph** (Ground Truth) from the noisy input.
 * **Memory Management**: Implement chunking or early stopping if context window approaches RAM limits (16GB).
 * **Threshold Sensitivity**: Sweep Critic re-planning thresholds {0.7, 0.8, 0.9} (FR-008).
3. **Logging**: Record `TrajectoryLog` for each sample, including intermediate JSON states, critiques, and final `ReasoningScore`.
 * **ReasoningScore**: F1-score (or GED) between Generator Output and **Human-Annotated Scene Graph** (the original, un-noised ground truth).

### Phase 3: Statistical Analysis & Ablation (FR-004, FR-005, FR-010, FR-011)

1. **Ablation Study**: Run a "No-Critic" condition (single-pass Generator) to isolate the gain from iterative correction.
2. **Stratified Analysis**: Stratify samples by the measured `actual_generator_error_rate` (deviation from Ground Truth) to control for confounding effects of poor generation quality.
3. **Statistical Testing**:
 * **Comparison**: Text-Only (Full Loop) vs. Baseline (Single-Pass).
 * **Method**: Paired t-test or Wilcoxon signed-rank test (depending on normality).
 * **Metrics**: p-value, 95% confidence interval, Cohen's d (effect size).
4. **Reporting**: Generate `statistical_significance_report.md` with all metrics and a clear statement on whether the difference is significant at α=0.05. This artifact is a mandatory output required by Constitution Principle VII.
5. **Error Analysis**: Report "Generator Error Rate" (deviation between generated JSON and **Human-Annotated Scene Graph**) as a separate variable to account for model imperfections (FR-010).

## Compute Feasibility & GPU Escape Hatch

* **CPU-First**: The primary execution path is CPU-only. The LLM will be run in default precision (or lower-precision quantized if memory constraints require) on the GitHub Actions free-tier runner (2 CPU, ~7GB RAM).
* **Streaming**: Datasets will be streamed (`datasets.load_dataset(..., streaming=True)`) to avoid loading entire datasets into memory.
* **GPU Escape Hatch**: If a specific method (e.g., fine-tuning a larger model) is deemed non-tractable on CPU, the plan will scale it down to a few hundred examples and use a quantized model (`load_in_8bit`) on a Kaggle GPU (16GB VRAM). However, the core hypothesis (Structure vs. Uncertainty) is designed to be tested on CPU.
* **No Fabrication**: No synthetic stand-ins will be used for GPU-dependent computations. If a GPU computation is required, the plan will explicitly state the scaling down strategy and rely on the auto-offload mechanism.

## Statistical Rigor & Limitations

* **Multiple Comparisons**: If multiple thresholds or benchmarks are tested, a correction (e.g., Bonferroni) will be applied to the p-values.
* **Power Analysis**: The sample size (N) will be determined by the available Visual Genome/GQA samples. If N is small, the study will be framed as exploratory with a note on power limitations.
* **Causal Inference**: The ablation study (Full Loop vs. No-Critic) provides a causal claim about the value of **Structure** within the text modality. The study does **not** claim to isolate "Modality" (Visual vs. Text) as the visual modality is not simulated.
* **Collinearity**: If predictors (e.g., prompt complexity) are definitionally related to outcomes, their relationship will be reported descriptively, and independent effects will not be claimed.

## Risks & Mitigations

* **Risk**: SFT-112k dataset is unavailable.
 * **Mitigation**: Use **few-shot prompting** with Visual Genome/GQA annotations. No fine-tuning required.
* **Risk**: Pre-computed image-based baseline is unavailable.
 * **Mitigation**: Use a "Single-Pass Text Baseline" and clearly label the comparison as "Structure vs. Single-Step".
* **Risk**: LLM memory overflow on CI.
 * **Mitigation**: Implement context window chunking, early stopping, and use smaller model variants (e.g., 7B/8B).
* **Risk**: Simulator error rate exceeds target (5-15%).
 * **Mitigation**: Tune noise injection parameters and validate against **Human-Annotated Scene Graphs** in `simulator_validation/`.