# Research: Social Memory Networks

## Research Question
Does collective remembering in multi-agent LLM systems exhibit emergent **Transactive Memory** properties (specialization and efficient cue-retrieval), and how robust are these properties to **context-window truncation**?

## Theoretical Background
Transactive Memory Systems (TMS) theory posits that groups develop a shared system for encoding, storing, and retrieving knowledge, often resulting in higher efficiency than individuals working in isolation. In biological systems, this involves specialization (different agents knowing different facts) and cue-driven retrieval (knowing *who* knows *what*). This project tests if LLM agents, when coupled via a shared memory buffer, spontaneously develop these dynamics.

Reviewer feedback (Geoffrey West) suggests investigating scaling laws: does memory efficiency scale sublinearly with the number of agents, similar to urban infrastructure? This plan incorporates a scaling analysis to test this hypothesis.

## Dataset Strategy

The project relies on **open, directly-downloadable datasets** to ensure reproducibility on CI runners. The spec identifies the following verified sources:

| Dataset Name | Source URL | Usage in Project |
|:--- |:--- |:--- |
| MultiAgent Bidding Dialogue | ` | Primary source for "facts" and dialogue context. Used to seed the memory buffer with discrete facts. |
| Multi-Agent Scam Conversation | ` | Secondary source for diverse interaction patterns and synthetic cue generation. |
| Multi-Agent Structure | ` | Structural reference for agent roles if explicit role annotation is missing. |

**Dataset Selection Rationale**:
1. **Accessibility**: All sources are Hugging Face datasets accessible via `datasets.load_dataset()` or direct parquet/CSV download. No credentials or data-use agreements are required, satisfying the "Data Availability" constraint.
2. **Variable Fit**: The datasets contain dialogue turns and agent interactions. While they may not explicitly label "facts" or "cues," the text spans can be parsed into discrete memory entries via NLP.
3. **Fallback Strategy**: If the selected dataset lacks explicit cue annotations (as anticipated in FR-011), the system will invoke a **Synthetic Cue Generator**. This generator extracts context spans from the dialogue and creates synthetic cue-response pairs, ensuring a minimum of 10 cues per game (per spec assumption).

**Data Processing Plan**:
- **Streaming**: For large files, `datasets.load_dataset(..., streaming=True)` will be used to iterate over rows without loading the full dataset into RAM.
- **Sampling**: If the full dataset exceeds the memory budget, a fixed-seed random sample (N=200 games equivalent) will be drawn.
- **Checksumming**: Every downloaded file will be checksummed and recorded in `data/manifest.json`.

## Methodology

### Experimental Design
A 2 (Context: Full vs. Limited) x 3 (Agent Count: 3, 5, 7) factorial design.
- **Independent Variables**:
 - `Context`: Full (unlimited window) vs. Limited (truncated to 128, 256, or 512 tokens).
 - `Agent Count`: 3, 5, 7 agents.
- **Dependent Variables**:
 - **Specialization Index**: Distribution-based metric of per-agent fact contribution (0 to log₂(N)).
 - **Cue-Retrieval Efficiency**: Proportion of successful retrievals relative to uniform chance (1/N).

### Ground-Truth Mechanism
To ensure construct validity for "successful retrievals," the simulation will inject a specific **target fact** into the memory buffer at the start of each game. A retrieval is "successful" only if the agent retrieves this exact target fact in response to a cue. This prevents hallucination from being counted as success.

### Statistical Analysis Plan
1. **ANOVA**:
 - **Separate One-Way ANOVAs**: One for Specialization Index and one for Cue-Retrieval Efficiency, with `Context` as the factor.
 - **Mixed-Design ANOVA**: To test the interaction between `Context` (between-subjects) and `Metric` (within-subjects), a Mixed-Design ANOVA will be performed. This correctly models the interaction term `Context x Metric` without the category error of treating Metric as an independent factor.
2. **Multiple Comparison Correction**: Bonferroni correction applied to all family-wise tests (FR-007).
3. **Power Analysis**: Sensitivity analysis to determine detectable effect size for N=200 games, α=0.05, power=0.80 (FR-009). If power < 0.70, a "Power limitation" flag is raised.
4. **Scaling Analysis**: Log-log linear regression (Y = a + b*log(N)) for metrics vs. agent count. Bootstrapping will be used to estimate the 95% confidence interval for the slope (beta). A note will be included that the 3 data points limit the reliability of the exponent estimate.

### Synthetic Cue Generator
If the dataset lacks explicit cue annotations, the system will generate synthetic cues using the following algorithm:
1. Extract N-grams (n=3 to 5) from the dialogue turns.
2. Randomly sample these N-grams to create cue-response pairs.
3. Ensure a minimum of 10 synthetic cues per game.

### Computational Feasibility
- **CPU-First**: All LLM inference will use `transformers` in CPU mode (default float32). Models will be loaded sequentially per turn to stay within available RAM constraints.
- **GPU Escape Hatch**: If a specific model requires CUDA (e.g., quantized inference for larger models), the execution script will detect the error and offload to a Kaggle GPU kernel (scaled to sufficient VRAM capacity for model execution, few hundred examples).
- **Time Budget**: 200 games per condition must complete within 6 hours on CPU. This necessitates using smaller models (e.g., `phi-2`, `distilbert`) or aggressive sampling if larger models are too slow.

## Ethical Considerations
- **Bias**: The datasets may contain biases (e.g., scam conversations). The analysis will focus on *structural* dynamics (memory efficiency) rather than the *content* of the dialogue.
- **Reproducibility**: All random seeds are fixed. No synthetic data will be used to replace real data; synthetic cues are only used to *augment* missing annotations.
