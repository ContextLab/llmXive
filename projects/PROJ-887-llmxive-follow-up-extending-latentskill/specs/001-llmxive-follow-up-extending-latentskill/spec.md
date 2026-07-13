# Feature Specification: llmXive follow-up: extending "LatentSkill: From In-Context Textual Skills to In-Weight Latent Skills"

**Feature Branch**: `001-lattentskill-retrieval-geometry`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'LatentSkill: From In-Context Textual Skills to In-Weight Latent Skills'"

## User Scenarios & Testing

### User Story 1 - Constructing the Skill Vector Database (Priority: P1)

The researcher MUST be able to ingest the pre-trained LoRA adapters (A and B matrices) from the original LatentSkill repository (ALFWorld and Search-QA benchmarks), flatten them into high-dimensional vectors, and generate a normalized "Skill Vector Database" index using only CPU-based operations.

**Why this priority**: This is the foundational data artifact. Without a constructed, normalized vector index of the existing skill weights, no retrieval or interpolation experiments can occur. It is the prerequisite for all subsequent analysis.

**Independent Test**: The system can be tested by successfully loading the raw LoRA weights, normalizing them, and outputting a static index file (e.g., `.npy` or `.npz`) containing the flattened vectors and their corresponding metadata (task description) without requiring GPU acceleration.

**Acceptance Scenarios**:

1. **Given** the original LatentSkill LoRA weight files and task descriptions are available, **When** the ingestion script runs on a CPU-only environment, **Then** a normalized vector index is generated containing all skill vectors with L2 normalization applied.
2. **Given** a raw LoRA weight file, **When** the flattening process is executed, **Then** the resulting vector dimensions match the theoretical product of the A and B matrix dimensions, and the data type remains compatible with standard CPU float32 operations.

---

### User Story 2 - Executing Retrieval and Interpolation Strategies (Priority: P2)

The researcher MUST be able to query the Skill Vector Database using text embeddings (derived from frozen sentence-transformers) to retrieve the nearest-neighbor skill or compute a weighted average of the top-$k$ skills, producing a candidate LoRA adapter for a novel composite task. This includes two distinct strategies: (1) **Arithmetic Mean**: an unweighted average of the top-$k$ vectors (serving as a baseline that ignores similarity scores), and (2) **Cosine-Weighted Averaging**: a similarity-weighted average where weights are proportional to the cosine similarity between the query and each neighbor.

**Why this priority**: This implements the core hypothesis: that the latent space is linear/dense enough for simple arithmetic or retrieval to replace the complex hypernetwork. This is the primary experimental mechanism.

**Independent Test**: The system can be tested by providing a novel composite task description, executing the retrieval/interpolation logic (both unweighted and weighted), and outputting synthesized LoRA adapter files (or weight deltas) ready for application to a base model, entirely on CPU.

**Acceptance Scenarios**:

1. **Given** a novel composite task description and the Skill Vector Database, **When** the cosine similarity retrieval is executed, **Then** the system identifies the single nearest-neighbor skill vector and returns its corresponding LoRA weights.
2. **Given** a composite task description and a set of top-$k$ retrieved vectors, **When** the unweighted arithmetic mean is executed, **Then** the system outputs a synthesized LoRA adapter representing the simple average of the retrieved weights.
3. **Given** a composite task description and a set of top-$k$ retrieved vectors, **When** the cosine-similarity-weighted averaging is executed, **Then** the system outputs a synthesized LoRA adapter that represents the weighted interpolation of the retrieved skills.

---

### User Story 3 - Validating Performance via Environment Logic (Priority: P3)

The researcher MUST be able to apply the retrieved or interpolated LoRA adapters to a held-out set of composite tasks using a frozen base LLM and evaluate success strictly based on the environment's internal logic (e.g., task completion flags), comparing these rates against a baseline. To account for stochasticity, the system MUST run each task multiple times to estimate a stable success probability.

**Why this priority**: This provides the empirical evidence required to answer the research question. It validates whether the structural properties of the space (linearity/density) actually translate to functional performance.

**Independent Test**: The system can be tested by running the evaluation pipeline on a small, held-out set of tasks, performing multiple runs per task, generating success/failure metrics, and outputting a statistical comparison (e.g., p-value) between the retrieval/interpolation methods and the baseline.

**Acceptance Scenarios**:

1. **Given** a synthesized LoRA adapter from User Story 2 and a composite task, **When** the adapter is applied to the frozen base LLM in the simulation environment for $N \ge 5$ runs, **Then** the system records a binary success/failure outcome for each run based solely on the environment's internal logic.
2. **Given** success rates (probabilities) for retrieval, interpolation, and baseline methods derived from multiple runs, **When** the statistical test is run, **Then** the system outputs a p-value indicating whether the difference in performance is statistically significant ($p < 0.05$).

### Edge Cases

- What happens when the composite task description is semantically distant from any existing skill in the database (out-of-distribution query)?
- How does the system handle cases where the top-$k$ retrieved vectors have near-identical cosine similarity scores? (Answer: The system applies the specific weighting logic of the chosen strategy—unweighted mean treats them equally; weighted averaging distributes weight proportionally to the exact similarity values).
- What occurs if the flattened LoRA weight dimensions between different adapters are inconsistent (e.g., due to mismatched base model versions)?

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest pre-trained LoRA adapters (A and B matrices) and flatten them into normalized high-dimensional vectors for index construction. (See US-1)
- **FR-002**: System MUST generate query vectors from text descriptions using a frozen, CPU-friendly sentence-transformer (e.g., `all-MiniLM-L6-v2`). (See US-2)
- **FR-003**: System MUST implement three approximation mechanisms: (1) single nearest-neighbor selection, (2) unweighted arithmetic mean of top-$k$ vectors, and (3) cosine-similarity-weighted averaging of top-$k$ vectors. (See US-2)
- **FR-004**: System MUST apply the synthesized LoRA adapters to a frozen base LLM and evaluate task success using the environment's internal logic (independent of the selection mechanism). (See US-3)
- **FR-005**: System MUST perform statistical testing (paired t-test or Wilcoxon signed-rank) to compare success rates of approximation strategies against the baseline with a significance threshold of $p < 0.05$. (See US-3)
- **FR-006**: System MUST enforce the Benjamini-Hochberg procedure for multiple-comparison correction when evaluating the set of primary hypothesis tests (comparing the 3 approximation strategies against the baseline) and the sensitivity analysis sweeps defined in SC-004, to control the False Discovery Rate (FDR). (See US-3)
- **FR-007**: System MUST validate the "text-weight alignment" assumption by calculating the Pearson correlation coefficient between text-space cosine distances and weight-space cosine distances for a held-out set of known task pairs; the correlation must be $\ge 0.6$ for the retrieval mechanism to be considered valid. (See US-2)
- **FR-008**: System MUST execute $N \ge 5$ independent runs for every task in the evaluation set to establish a stable success probability (mean of binary outcomes) before performing statistical tests. (See US-3)

### Key Entities

- **Skill Vector**: A normalized, high-dimensional representation of a flattened LoRA adapter (A and B matrices) associated with a specific task description.
- **Composite Task**: A novel task description formed by combining existing skills, used as a query to test the latent space geometry.
- **Success Metric**: A binary outcome (0/1) derived strictly from the environment's internal logic indicating task completion.
- **Reconstruction Error**: The cosine distance between the synthesized LoRA weights and the true weights of a known composite task.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: Task success rate for retrieval/interpolation methods is measured against the **standard fine-tuned baseline** success rate; the method is considered acceptable if the degradation is **no more than 10% lower** than the baseline. (See US-3)
- **SC-002**: Statistical significance of the performance difference between approximation strategies and the baseline is measured against the $p < 0.05$ threshold using a paired t-test or Wilcoxon signed-rank test, with Benjamini-Hochberg correction applied to all primary comparisons and sensitivity sweeps. (See US-3)
- **SC-003**: Wall-clock latency for skill selection (retrieval vs. hypernetwork inference) is measured against the 2-core CPU runner limit to quantify computational savings. (See US-2)
- **SC-004**: Sensitivity of the retrieval performance is measured against varying top-$k$ values ($k \in \{1, 3, 5\}$) to determine if the linear approximation is robust to the number of neighbors used. (See US-2)
- **SC-005**: The validity of the "linearity" assumption is measured against the **geometric reconstruction error** (cosine distance) between synthesized weights and true weights for known composite tasks; if the error rate exceeds **0.05**, the latent space is deemed non-linear for this purpose. (See US-2)

## Assumptions

- The original LatentSkill repository (arXiv:2606.06087) provides downloadable LoRA weight files (A and B matrices) and corresponding task descriptions in a format compatible with standard PyTorch/NumPy loading.
- The base LLM (e.g., Llama-8B) can be run in a quantized mode (e.g., 4-bit or 8-bit via `bitsandbytes` or similar CPU-optimized quantization) within the 7 GB RAM limit of the GitHub Actions free runner.
- The "environment's internal logic" for ALFWorld and Search-QA is accessible as a deterministic simulation or script that returns a binary success/failure flag independent of the LLM's internal state, provided the action sequence is correct.
- The sentence-transformer `all-MiniLM-L6-v2` is small enough to be loaded and executed on the CPU-only runner without exceeding memory constraints.
- **Scientific Premise**: The latent space geometry of LoRA adapters is assumed to be consistent across different base models if the same fine-tuning protocol is used; any deviation in base model architecture is treated as a confounding variable to be controlled.
- **Text-Weight Alignment**: It is assumed that semantic distance in text space (cosine similarity of embeddings) correlates monotonically with functional distance in weight space (cosine similarity of LoRA vectors); this assumption is empirically validated via FR-007.
- The dataset of available skills is sufficiently dense that a novel composite task has at least one semantically similar skill within the top-$k$ neighbors; if the space is sparse, the retrieval mechanism may fail to find a relevant vector.
- The statistical power of the test is sufficient to detect a small-to-moderate difference in success rates with the available number of held-out composite tasks; if the sample size is too small, the power limitation will be acknowledged in the final report.
- The latency measurement includes only the skill selection phase (retrieval/interpolation) and excludes the time required for the base LLM to generate a response, as the focus is on the overhead of the hypernetwork replacement.
- The "5-10% tolerance window" for performance degradation is a community-standard default for acceptable approximation error in this domain, as no specific threshold was provided in the idea.
- The top-$k$ value for retrieval is set to $k=5$ as a defensible default for balancing precision and recall in high-dimensional spaces, with sensitivity analysis performed over $k \in \{1, 3, 5, 10\}$.
- The quantization method used for the base LLM (e.g., 4-bit) does not introduce significant noise that would confound the comparison between retrieval and baseline methods.
- The frozen sentence-transformer model is assumed to provide a valid semantic representation of the task descriptions, such that cosine similarity in text space correlates with proximity in weight space.
- The "environment's internal logic" is assumed to be a reliable and deterministic measure of task success, without stochastic elements that would require multiple runs per task to establish a ground truth (addressed by FR-008).
- The GitHub Actions free runner (2 CPU, 7 GB RAM) is capable of handling the memory footprint of the flattened LoRA vectors, the sentence-transformer, and the quantized base LLM simultaneously.
- The original LatentSkill hypernetwork weights are either available for direct comparison or a standard fine-tuned baseline can be used as a proxy if the hypernetwork is not accessible.
- The composite tasks used for evaluation are generated by combining existing skills in a way that is semantically meaningful and not trivially solvable by a single existing skill.
- The statistical tests (t-test/Wilcoxon) are appropriate for the distribution of the success rates; if normality assumptions fail, the non-parametric alternative will be used.
- The "linearity" of the latent space is defined as the ability to approximate novel task weights via linear interpolation of existing weights; non-linear properties (e.g., curvature) are outside the scope of this specific test.
- The "density" of the latent space is defined as the minimum distance between any two skill vectors in the database; if the space is too sparse, retrieval may fail to find a relevant neighbor.
- The "computational bottleneck" of the hypernetwork is assumed to be the inference time for skill selection; other bottlenecks (e.g., data loading) are not considered in this analysis.
- The "edge device" scenario is approximated by the CPU-only runner, assuming that the latency and memory constraints of the runner are representative of a standard edge device.
- The "serverless environment" scenario is approximated by the 6-hour job limit and the 14 GB disk limit of the GitHub Actions runner.
- The "deterministic agent architecture" is assumed to be achievable if retrieval/interpolation is viable, as the selection mechanism becomes a simple lookup rather than a generative process.
- The "modular AI systems" trade-off between flexibility and computational cost is assumed to be the primary motivation for this research, and the results will inform this trade-off.
- The "novel task compositions" are assumed to be unseen during the training of the original LoRA adapters, ensuring that the test is truly out-of-distribution.
- The "synthetic composite tasks" are assumed to be generated by combining the textual descriptions of existing skills in a way that preserves the semantic meaning of the components.
- The "held-out evaluation metric" is assumed to be independent of the LoRA weights and text embeddings, ensuring that the validation is not circular.
- The "paired t-test" is assumed to be the appropriate statistical test for comparing the success rates of the approximation strategies against the baseline, as the same tasks are used for all methods.
- The "Wilcoxon signed-rank test" is assumed to be the appropriate non-parametric alternative if the success rates are not normally distributed.
- The "Benjamini-Hochberg correction" is assumed to be the appropriate multiple-comparison correction method for controlling the false discovery rate, mandated by FR-006 due to the multiple comparisons inherent in testing 3 strategies and sensitivity sweeps.
- The "sensitivity analysis" for the top-$k$ value is assumed to be necessary to determine the robustness of the retrieval mechanism to the number of neighbors used.
- The "power limitation" is assumed to be a potential issue if the number of held-out composite tasks is too small to detect a 5-10% difference in success rates.