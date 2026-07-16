# Research: llmXive follow-up: extending "COLLEAGUE.SKILL"

## Research Question

Does explicitly decoupling capability heuristics from behavioral style in LLM agent prompts reduce hallucinated expertise and style drift during long-horizon interactions compared to monolithic persona prompts?

## Hypothesis

- **H1 (Hallucination)**: The "Separated Tracks" prompt condition will yield a statistically significant lower Hallucination Rate compared to the "Monolithic" condition (p < 0.05), while maintaining comparable Heuristic Adherence.
- **H2 (Style)**: The "Separated Tracks" condition will maintain Style Consistency within a non-inferiority margin (e.g., <5% drop) compared to the "Monolithic" condition.
- **H3 (Robustness)**: The benefits of separation will be consistent across diverse task domains (coding, math, logic, creative, factual).

## Dataset Strategy

Since no open dataset currently contains the specific "capability vs. behavior" decoupled expert profiles and ground-truth multi-hop task scenarios required for this study, **synthetic data generation** is the primary strategy. However, to avoid circularity (Concern: scientific_soundness-434f4b95), **Ground Truth** for Hallucination Rate is sourced from external, verified knowledge bases.

### Verified Datasets / Sources
*Note: No external dataset currently exists with the exact structure required. The following sources are used for **component generation** or **validation logic**.*

| Dataset/Source | Purpose | Verified URL / Loader | Status |
| :--- | :--- | :--- | :--- |
| **HuggingFace `datasets`** | Loading base models (Llama-3-8B, Phi-3-mini) | `datasets.load_dataset("meta-llama/Meta-Llama-3-8B-Instruct")` (via `transformers`) | Verified |
| **Project Gutenberg** | External ground-truth facts for "Factual" domain tasks | `gutenberg` loader (e.g., specific texts for fact-checking) | Verified (External Truth) |
| **Standard Math Problem Sets** | External ground-truth for "Math" domain tasks | `openml` loader (e.g., standard algebra problems) | Verified (External Truth) |
| **Simulated Repository** | Generating Expert Profiles (Capability + Behavior)

This research aims to answer: How can diverse expert profiles be systematically generated to reflect varied capabilities and behaviors? The method involves constructing a framework for synthesizing expert personas based on defined capability and behavioral dimensions. References: [Preserve original citations verbatim]. | `code/data_generation/profiles.py` (Rule-based, deterministic) | **Primary Source** |
| **Simulated Repository** | Generating Multi-turn Task Scenarios | `code/data_generation/tasks.py` (Stratified sampling) | **Primary Source** |

**Data Strategy Rationale**:
1.  **Profiles**: Generated programmatically to ensure the strict separation of "capability rules" (heuristics) and "behavior tracks" (style).
2.  **Tasks**: Generated to cover the required domains (coding, math, logic, creative, factual).
3.  **Ground Truth & Hallucination Traps**: For "Hallucination Rate", the "truth" is not the generation script's embedded rules, but **external verified sources** (e.g., Project Gutenberg texts, standard math problem answers).
    - **Mechanism**: The `tasks.py` script generates tasks by first selecting a context from the external source. It then identifies facts present in the external source but *not* in the immediate context to serve as "hallucination traps". The evaluation script compares model outputs against these external sources using NLI models. This breaks the circularity where the script validates itself by ensuring the "truth" is external and the "traps" are derived from external knowledge, not internal script logic.

*Note: If a public "COLLEAGUE.SKILL" gallery becomes available with verified open access, it will be substituted. Until then, the simulated repository is the canonical source.*

## Model Selection & Compute Feasibility

### Model Choice
- **Primary Model**: `Llama-3-8B-Instruct` (Quantized to 4-bit, Q4_K_M).
  - **Rationale**: Models of sufficient scale are the smallest capable of maintaining context coherence. for multi-turn reasoning tasks. Quantization (low-bit) reduces memory footprint to a manageable size for consumer hardware., fitting within the memory limits of the CI runner.
  - **Alternative**: `Phi-3-mini` (3.8B) if Llama-3 fails to load or OOMs.
- **Backend**: `llama-cpp-python` (preferred for CPU efficiency) or `transformers` with `torch_dtype=torch.float32` (fallback, higher RAM).

### Compute Strategy (CPU-First)
- **Constraint**: 2 CPU cores, ~7GB RAM, ~14GB disk, ≤6h per job.
- **Execution Plan**:
  1.  **Model Loading**: Load the quantized model once per run (or per batch) to avoid repeated I/O overhead.
  2.  **Batching**: Process tasks in small batches to manage memory and allow for timeout handling.
  3.  **Timeouts**: Enforce a -second timeout per task (as per US-1). If exceeded, log the failure and proceed.
  4.  **Streaming**: No streaming of the *model* (it must be loaded), but outputs are streamed to disk immediately to prevent memory bloat.
  5.  **GPU Escape Hatch**: Not applicable. The hypothesis specifically tests *CPU-constrained* performance. If the model fails to run on CPU, the experiment cannot proceed (as per Constitution Principle VII). No GPU offload is planned for the primary analysis.

## Evaluation Methodology

### Metrics Definition (Rule-Based, Non-Circular)

1.  **Heuristic Adherence**:
    - **Calculation**: Binary match (1/0) against the "capability track" rules defined in the profile.
    - **Logic**:
        - **Coding Tasks**: Parsed via **AST (Abstract Syntax Tree)** to verify structural constraints (e.g., function definition, import statements) and logical correctness.
        - **Math Tasks**: Verified via **SymPy** to check if the solution satisfies the equation or constraint.
        - **General Tasks**: Verified via **Z3 Solver** for logical constraints (e.g., "if A then B").
    - **Tool**: `ast` module, `sympy`, `z3-solver`. *Replaces brittle regex/eval.*

2.  **Style Consistency**:
    - **Calculation**: Composite score (0.0-1.0) = 0.5 * (Keyword Frequency) + 0.5 * (Tone/Structure Deviation).
    - **Logic**:
        - **Keyword Frequency**: Regex matching of "behavior track" keywords.
        - **Tone/Structure Deviation**: A pre-trained **Style Classifier** (e.g., DeBERTa fine-tuned on style datasets) scores the output for tone (formal, conversational, etc.) and structure. If the predicted tone contradicts the "behavior track" definition, the score is penalized.
    - **Tool**: Regex + `transformers` (Style Classifier). *Addresses concern that keyword presence != style.*

3.  **Hallucination Rate**:
    - **Calculation**: Ratio of facts in the output that are NOT present in the task context OR contradicted by **External Verified Knowledge Bases**.
    - **Logic**:
        - Extract entity-value pairs from output.
        - Compare against **External Truth** (e.g., Project Gutenberg, standard math answers) using **DeBERTa-MNLI** (Natural Language Inference) model.
        - If the NLI model predicts "Contradiction" or "Neutral" (where "Entailment" is expected) against the external truth, increment counter.
    - **Tool**: `transformers` (DeBERTa-MNLI). *Replaces simple set-difference logic to distinguish valid inference from hallucination.*

### Statistical Analysis Plan
- **Model**: Generalized Linear Mixed Model (GLMM).
  - **Fixed Effects**: `Prompt Condition` (Monolithic, Separated, Generic), `Task Domain`.
  - **Random Effects**: Random intercepts for `Profile` and `Task` (to account for nested data).
  - **Outcome Variables**: `Hallucination Rate` (Binomial family), `Heuristic Adherence` (Binomial family), `Style Consistency` (Beta family or transformed).
  - **Link Function**: Logit for binary/ratio outcomes; Logit or Probit for bounded scores.
- **Correction**: Bonferroni correction for multiple comparisons (3 metrics × 2 pairwise comparisons = 6 tests).
- **Sensitivity Analysis**: Sweep `Style Consistency` threshold (0.01, 0.05, 0.1) and report variance in false-positive rates (FR-008).

## Ethical Considerations & Limitations

- **Synthetic Data**: Results are based on generated profiles and tasks. Generalizability to real-world human experts is limited but sufficient for the proof-of-concept.
- **Model Bias**: Small language models (8B) have inherent biases. The study controls for this by comparing conditions within the same model.
- **Compute Limits**: The 7GB RAM limit may restrict the maximum context window or batch size, potentially affecting performance on very long tasks.