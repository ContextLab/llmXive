# Feature Specification: llmXive follow-up: extending "InterleaveThinker: Reinforcing Agentic Interleaved Generation"

**Feature Branch**: `001-llmxive-interleave-structure-vs-modality`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'InterleaveThinker: Reinforcing Agentic Interleaved Generation'"

## User Scenarios & Testing

### User Story 1 - Construct Text-Based Scene Simulator (Priority: P1)

**Journey**: The researcher downloads the `Interleave-Planner-SFT-80k` and `Interleave-Critic-SFT-112k` datasets and instantiates a text-based simulator that converts image generation prompts into structured JSON scene descriptions (objects, spatial relationships, attributes). The simulator operates in two modes: "Perfect Mode" (deterministic parsing) and "Noisy Mode" (injecting controlled semantic noise to simulate the grounding gap of visual generation). This allows the pipeline to execute without GPU-dependent image generation libraries while preserving the experimental variable of input fidelity.

**Why this priority**: This is the foundational enabler. Without a text-only representation that can simulate the "modality gap," the "structure vs. modality" variable cannot be isolated. The entire hypothesis testing depends on the ability to run the pipeline in a CPU-only environment with controllable input fidelity.

**Independent Test**: The simulator can be invoked with a prompt string and a mode flag ("Perfect" or "Noisy"), returning a valid JSON object within 500ms containing keys for `objects`, `relationships`, and `attributes`, with no external image generation API calls made.

**Acceptance Scenarios**:
1. **Given** a prompt "a red cube on a blue sphere" in "Perfect Mode", **When** the simulator processes the prompt, **Then** it outputs a JSON object containing `{"objects": [{"type": "cube", "color": "red"}, {"type": "sphere", "color": "blue"}], "relationships": [{"source": "cube", "target": "sphere", "relation": "on"}]}`.
2. **Given** a prompt in "Noisy Mode" with a target error rate of 10%, **When** the simulator generates the description, **Then** the output JSON preserves topological constraints with ≥ 90% fidelity (i.e., ≤ 10% of relationships are intentionally altered or hallucinated) to simulate the uncertainty inherent in visual grounding.

---

### User Story 2 - Execute CPU-Tractable Agentic Loop (Priority: P2)

**Journey**: The researcher configures a lightweight LLM (e.g., Llama-3-8B or Mistral-7B in default precision) to act as the "Generator" agent within the InterleaveThinker pipeline. The researcher runs the full interleaved trajectory (Planner → Text-Generator → Critic → Planner) on the WISE and RISE benchmarks using the JSON scene descriptions from the User Story, ensuring the Critic evaluates the JSON rather than images. The Critic threshold for re-planning is configurable across a sensitivity range.

**Why this priority**: This implements the core experimental condition (Text-Only Simulation). It validates that the agentic structure functions correctly when the visual modality is replaced by structured text, allowing for the collection of reasoning scores under varying input fidelity.

**Independent Test**: The pipeline processes benchmark samples from WISE/RISE, completes the full planning-generating-critic loop for each, and outputs a JSON log of reasoning scores (F1-score) within the 6-hour CI time limit on a CPU-only runner, with RAM usage ≤ 16GB.

**Acceptance Scenarios**:
1. **Given** a benchmark sample from WISE, **When** the pipeline executes the Planner → Generator → Critic loop, **Then** the system completes the trajectory and records an F1-score without crashing due to memory overflow or GPU dependency errors.
2. **Given** the Critic agent receives a JSON scene description, **When** it evaluates the description against the prompt, **Then** it returns a critique and a revised intent in JSON format, triggering the next Planner step if the F1-score is below the configured threshold (sensitivity range: {0.7, 0.8, 0.9}).

---

### User Story 3 - Perform Statistical Comparison and Ablation (Priority: P3)

**Journey**: The researcher compares the reasoning scores of the text-only simulation against a baseline (single-pass LLM or pre-computed image-based results) using paired t-tests or Wilcoxon signed-rank tests. Additionally, the researcher runs an ablation study where the Critic feedback loop is disabled to isolate the gain attributed to iterative correction. The analysis includes effect sizes and generates a formal report.

**Why this priority**: This delivers the scientific answer to the research question. It quantifies whether the structural decomposition (loops) or the modality (visuals) drives performance, providing the final metric for the project.

**Independent Test**: The analysis script outputs a report containing p-values and effect sizes (Cohen's d) for the difference between text-only and baseline scores, and a delta metric comparing "Full Loop" vs. "No-Critic Loop" performance, all computed on CPU.

**Acceptance Scenarios**:
1. **Given** two sets of reasoning scores (Text-Only vs. Baseline) of size N=100, **When** the statistical test is run, **Then** the system outputs a p-value, a confidence interval, and an effect size (Cohen's d) indicating whether the difference is statistically significant at α=0.05.
2. **Given** the ablation run (Text-Only without Critic), **When** compared to the full Text-Only run, **Then** the system reports the specific percentage drop in F1-score attributed solely to the removal of the iterative feedback loop.

---

### Edge Cases

- **What happens when the JSON simulator generates ambiguous spatial relationships?** The system must detect ambiguity and either default to a canonical interpretation or flag the sample for exclusion, ensuring the Critic does not fail on undefined inputs.
- **How does the system handle memory limits during the full pipeline execution?** If the LLM context window approaches the RAM limit of the CI runner (16GB), the system must implement chunking or early stopping to prevent OOM errors, ensuring the job completes within 6 hours.
- **What if the baseline image-based results are unavailable?** The system must gracefully degrade to comparing the Text-Only simulation against a Single-Pass Text Baseline, clearly marking the comparison as "Structure vs. Single-Step" rather than "Structure vs. Visual".

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement a deterministic text-based simulator that converts image prompts into structured JSON scene descriptions containing objects, attributes, and spatial relationships (See US-1).
- **FR-002**: System MUST execute the full agentic pipeline (Planner → Generator → Critic → Planner) using a lightweight LLM in default precision on CPU-only infrastructure (See US-2).
- **FR-003**: System MUST evaluate the Critic agent's feedback on JSON scene descriptions rather than pixel arrays, ensuring the feedback loop remains functional without visual rendering (See US-2).
- **FR-004**: System MUST perform statistical analysis (paired t-test or Wilcoxon signed-rank) on reasoning scores to determine significance between text-only simulation and baseline (See US-3).
- **FR-005**: System MUST execute an ablation study disabling the Critic loop to isolate the performance gain attributed specifically to iterative correction (See US-3).
- **FR-006**: System MUST enforce a memory constraint that keeps total RAM usage ≤ 16GB and total execution time ≤ 6 hours per CI job (See US-2).
- **FR-007**: System MUST implement a "Noisy Mode" in the simulator that injects semantic errors into the JSON scene description at a target rate between 5% and 15% to simulate the grounding gap of visual generation (See US-1).
- **FR-008**: System MUST support a configurable Critic threshold for re-planning, with a sensitivity analysis sweeping values {0.7, 0.8, 0.9} to ensure robustness (See US-2).
- **FR-009**: System MUST validate the simulator by measuring the `simulator_error_rate` against ground truth metadata in a `simulator_validation` subdirectory, quantifying the fidelity gap between text and visual representations (See US-1).
- **FR-010**: System MUST measure and report the "Generator Error Rate" (deviation between generated JSON and intended prompt) as a separate variable to account for model imperfections (See US-1).
- **FR-011**: System MUST generate a `statistical_significance_report.md` artifact containing p-values and effect sizes (Cohen's d) for the ablation study (See US-3).

### Key Entities

- **SceneDescription**: A structured JSON object representing a visual scene, containing lists of `objects` (with type/color/shape) and `relationships` (spatial/semantic links).
- **ReasoningScore**: A numerical metric (F1-score) assigned to a benchmark sample after the full agentic loop completes.
- **TrajectoryLog**: A record of the complete sequence of Planner, Generator, and Critic steps for a single benchmark sample, including intermediate JSON states and critiques.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in reasoning scores between the text-only simulation and the image-based baseline is measured against the hypothesis that the difference is ≤ 10% (See US-3).
- **SC-002**: The performance gain from the iterative Critic loop (Full vs. No-Critic) is measured against the baseline single-pass LLM performance to quantify the value of structural decomposition (See US-3).
- **SC-003**: The statistical significance (p-value) and effect size (Cohen's d) of the performance difference are measured against the standard α=0.05 threshold to determine if the modality change is a critical factor (See US-3).
- **SC-004**: The total execution time of the full pipeline on the WISE/RISE benchmarks is measured against the 6-hour CI time limit to ensure CPU feasibility (See US-2).
- **SC-005**: The memory footprint of the LLM inference and data processing is measured against the 16GB RAM limit of the free-tier runner (See US-2).
- **SC-006**: The `simulator_error_rate` is measured against a target range of 5-15% in Noisy Mode to validate the grounding gap simulation (See US-1).

## Assumptions

- **Assumption about data availability**: The `Interleave-Planner-SFT` and `Interleave-Critic-SFT` datasets are accessible via HuggingFace or the original repository and can be downloaded within the CI time limits.
- **Assumption about model capability**: A quantized or default-precision large language model (e.g., Llama-3, Mistral) is sufficient to generate coherent JSON scene descriptions and perform reasoning tasks on the WISE/RISE benchmarks, though the Generator may produce errors that must be measured (FR-010) rather than assumed to be zero.
- **Assumption about baseline data**: Pre-computed results for the original InterleaveThinker (image-based) are available for comparison; if not, the comparison will be made against a single-pass text baseline, which is a conservative but valid proxy for the "no-structure" condition.
- **Assumption about statistical power**: The sample size of the WISE/RISE benchmarks (or a representative subset) is sufficient to detect a [deferred] difference in reasoning scores with a power of 0.8 at α=0.05; if the dataset is smaller, the study will be framed as exploratory with a note on power limitations.
- **Assumption about threshold justification**: The threshold for the Critic agent to trigger a re-plan is configurable across {0.7, 0.8, 0.9} to ensure robustness; a sensitivity analysis will sweep this threshold over this range to ensure stability of conclusions.
- **Assumption about variable fit**: The WISE and RISE benchmarks contain the necessary variables (prompt, ground truth, reasoning steps) to evaluate the "structure vs. modality" hypothesis without requiring additional external data sources.