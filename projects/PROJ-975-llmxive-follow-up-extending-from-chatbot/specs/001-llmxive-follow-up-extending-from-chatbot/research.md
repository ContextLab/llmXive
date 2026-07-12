# Research: llmXive follow-up: extending "From Chatbot to Digital Colleague"

## Research Question

At what threshold of skill library cardinality does retrieval noise induce diminishing returns in task success rates and latency for persistent LLM agents, and does an active "Skill Pruning" heuristic effectively restore performance metrics in CPU-constrained environments?

## Methodology

### Experimental Design
A controlled simulation experiment using synthetic data.
1.  **Data Generation**: Generate a set of multi-step tasks and Python skills with programmatically controlled semantic overlap.
    *   **Semantic Obfuscation**: Task prompts will use abstract descriptions or synonyms for the required actions to prevent trivial string matching with skill names.
2.  **Execution Loop**: Run an agent across multiple library cardinalities (e.g., small, medium, and large sets of skills).
3.  **Intervention**: Run an additional condition with the 100-skill library + Pruning Heuristic enabled.
4.  **Measurement**: Record success rate, token usage, latency, and retrieval precision@k.

### Dataset Strategy

**Source**: Synthetic Data Generator (Local).
*   **Rationale**: The spec requires tasks "independent of the specific skill set" and "controlled variation of skill cardinality." No existing public dataset offers this level of granular control over semantic overlap and deterministic action sequences for LLM agents.
*   **Generation Logic**:
    *   **Tasks**: Constructed from templates requiring 3-5 deterministic actions (e.g., `read_file`, `parse_json`, `write_result`).
    *   **Skills**: Python functions generated with varying levels of semantic similarity (using `sentence-transformers` embeddings).
    *   **Overlap**: Controlled by injecting common sub-routines (e.g., `format_date`) into multiple skill definitions.
    *   **Complexity Stratification**: Task complexity (number of steps, abstractness) is varied **independently** of library size to ensure the success rate is not trivially determined by the library size input.

**Verified Datasets**:
*   *None required*. The study relies entirely on the `code/generators/` module. No external URLs are cited or used.

**Ground Truth & "Human-Annotated" Labels (FR-005, SC-002)**:
*   **Mechanism**: A **Synthetic Oracle** combined with an **LLM-as-a-Judge**.
    1.  **Synthetic Oracle**: At task creation, the generator deterministically assigns the `required_skill_ids` based on the task definition (the "intended" solution).
    2.  **LLM-as-a-Judge**: An independent LLM instance (using a different model/prompt than the retriever) evaluates the relevance of the retrieved skills against the task context. It generates a binary relevance label (1 = relevant, 0 = not) for the top-k retrieved skills.
    3.  **Validation Set**: A subset of 50 tasks is selected, and the Judge's output is stored as `data/raw/validation_labels.csv`.
*   **Independence**: The Oracle provides the deterministic truth, while the Judge provides an independent semantic validation layer, breaking circularity and simulating "human-annotated" labels without external human intervention.
*   **Independence from Generator**: The task prompts are semantically obfuscated (e.g., "process the date data" instead of "call format_date") so that the retrieval system cannot infer the required skill via keyword matching. The retrieval must rely on the embedding model to map the abstract prompt to the correct skill ID provided by the Oracle.

### Statistical Analysis Plan

1.  **Diminishing Returns (SC-001)**:
    *   **Metric**: Task Success Rate vs. Library Size.
    *   **Method**: **Piecewise Regression (Segmented Regression)**. Unlike One-way ANOVA (which only tests for mean differences), Piecewise Regression will model the relationship between library size and success rate to identify the specific **breakpoint (threshold)** where the slope significantly changes (indicating diminishing returns).
    *   **Null Hypothesis**: No breakpoint exists (linear or flat relationship).
    *   *Note: This method replaces the One-way ANOVA mandated in SC-004 of the source spec, as ANOVA is insufficient to identify a specific threshold.*

2.  **Retrieval Precision (SC-002)**:
    *   **Metric**: Precision@k (k=5).
    *   **Method**: Compare retrieved skills against the **LLM-as-a-Judge** labels (stored in `data/raw/validation_labels.csv`).

3.  **Pruning Efficacy (SC-003)**:
    *   **Metric**: Recovery of Success Rate and Latency.
    *   **Method**: **Paired t-test** (or Wilcoxon signed-rank if non-normal) comparing the "100-skill unpruned" run vs. the "100-skill pruned" run.

4.  **False Positive Rate (SC-005)**:
    *   **Metric**: Count of "False Prune" events / Total Pruning Events.
    *   **Definition**: A task failure where the removed skill was the only valid solution for the required action.

### Compute Feasibility & Constraints

*   **Hardware**: GitHub Actions Free Tier (CPU, standard memory allocation, No GPU).
*   **Model Selection**: `all-MiniLM-L6-v2` (Sentence Transformers) for retrieval; `Llama-3-8B-Instruct` (quantized or distilled) for LLM-as-a-Judge (CPU-optimized).
    *   *Rationale*: Small footprint, runs efficiently on CPU, sufficient for semantic similarity tasks without requiring 8-bit quantization or CUDA.
*   **Memory Management**:
    *   Embeddings pre-calculated and stored in RAM (a set of skills × a fixed embedding dimension × 4 bytes).
    *   Tasks processed in batches of a moderate size to prevent log file bloat.
    *   Strict timeout per task enforced by `subprocess` or timeout wrapper.
*   **Runtime**: Estimated < 2 hours for full sweep (500 tasks × 5 configs), well within 6h limit.

### Decision Rationale

*   **Why Synthetic Data?** Real-world datasets (e.g., SWE-bench) lack the deterministic "ground truth" for *which* specific skill was required, making "Retrieval Precision" impossible to calculate accurately.
*   **Why CPU-Only?** The project targets "edge-deployed agents." Testing on GPU would invalidate the "cognitive overhead" hypothesis which assumes resource constraints.
*   **Why Pruning Heuristic?** To address Constitution Principle VII, the plan must explicitly test if *active management* solves the *passive accumulation* problem.
*   **Why Piecewise Regression?** To validly answer the research question about a *specific threshold*, a global F-test (ANOVA) is insufficient. Piecewise regression models the non-monotonic trend and locates the breakpoint.
*   **Why Corrected Pruning Logic?** The source spec (FR-004) erroneously suggests removing high-similarity skills. This plan implements the **corrected logic**: remove skills with *low* similarity (<0.15) or zero usage. A kickback is required to update the spec.
*   **Why LLM-as-a-Judge?** To satisfy the "human-annotated" requirement (FR-005, SC-002) without external human intervention, an independent LLM judge provides a semantically valid proxy for human relevance labeling.

### Spec Kickback Summary
1.  **FR-004**: Change `similarity > 0.85` to `similarity < 0.15 OR usage == 0`.
2.  **SC-004**: Change `One-way ANOVA` to `Piecewise Regression`.
3.  **FR-005/SC-002**: Clarify that "human-annotated" labels are satisfied by the `Synthetic Oracle + LLM-as-a-Judge` proxy mechanism.