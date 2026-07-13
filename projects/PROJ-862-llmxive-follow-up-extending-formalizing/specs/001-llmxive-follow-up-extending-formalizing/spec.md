# Feature Specification: llmXive Follow-up: Input Noise Injection for Latent Separability

**Feature Branch**: `001-lm-axive-noise-injection`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Formalizing Latent Thoughts: Four Axioms of Thought Representation in'"

## User Scenarios & Testing

### User Story 1 - Baseline Latent Vector Extraction (Priority: P1)

**Journey**: The researcher loads the frozen transformer model and the designated reasoning dataset to extract the "thought" token hidden states for a set of baseline questions without any perturbation. This establishes the control group for the representational collapse analysis.

**Why this priority**: Without a valid baseline measurement of the current state (the "collapse"), the experiment cannot measure any change. This is the foundational data collection step required for the paired t-test.

**Independent Test**: Can be fully tested by running the extraction pipeline on a single task type and verifying that the output file contains a list of normalized vectors with the correct dimensionality, matching the model's hidden size.

**Acceptance Scenarios**:

1. **Given** a loaded frozen transformer model and a subset of 23 reasoning tasks, **When** the system processes the "thought" token for each question, **Then** it outputs a CSV file containing one row per question with the corresponding latent vector (normalized to unit length).
2. **Given** the baseline extraction process, **When** the system encounters a question pair from the same task type, **Then** it correctly identifies them as a pair and stores their vectors with a shared pair ID for later comparison.

---

### User Story 2 - Noise-Augmented Perturbation & Re-Extraction (Priority: P2)

**Journey**: The researcher applies controlled perturbations to the input embeddings of the same questions and re-runs the model to extract the perturbed latent vectors. This tests the hypothesis that input manifold smoothness is the cause of the collapse. The system must execute a sweep of noise thresholds ($\sigma \in [, 0.20]$ with step 0.01) and verify that each perturbation preserves semantic validity using an independent metric before proceeding.

**Why this priority**: This is the core experimental intervention. It directly addresses the research question by introducing the independent variable (noise sweep) to observe the dependent variable (separability change), while ensuring the change is not an artifact of model failure via independent validation.

**Independent Test**: Can be fully tested by injecting a known perturbation magnitude and verifying that the resulting input embeddings differ from the baseline by the expected amount, while the model weights remain unchanged and the output retains the ground truth answer (verified via BERTScore ≥ 0.85 and perplexity bound).

**Acceptance Scenarios**:

1. **Given** the baseline input embeddings and a configured sweep of perturbation magnitudes ($\sigma \in [0.01, 0.20]$ in steps of 0.01), **When** the system applies the perturbation (add Gaussian noise to embedding, project to nearest valid token), **Then** the perturbed embeddings maintain semantic validity (verified by an external SBERT check with score ≥ 0.95) and differ from the baseline by the expected Euclidean distance.
2. **Given** the perturbed inputs, **When** the frozen model processes them, **Then** the system extracts the new latent vectors at the same token position and saves them to a separate file linked to the baseline pair IDs, provided the semantic validity checks pass.
3. **Given** the sweep configuration, **When** the system iterates through $\sigma$, **Then** it records the validity status for each $\sigma$ and excludes any $\sigma$ where >90% of pairs fail the validity check from the final statistical analysis.

---

### User Story 3 - Statistical Separability Analysis (Priority: P3)

**Journey**: The researcher runs the statistical analysis comparing the cosine similarity of baseline pairs versus noise-augmented pairs to determine if the perturbation significantly increased separability, but only for pairs that passed the independent semantic validity filter.

**Why this priority**: This synthesizes the data into the final answer to the research question. It transforms raw vectors into a p-value and effect size, concluding the experiment, while controlling for semantic drift.

**Independent Test**: Can be fully tested by feeding the system a mock dataset with a known artificial difference in similarity and verifying that the statistical test correctly identifies the difference with the expected significance level, excluding any pairs that failed the semantic drift check.

**Acceptance Scenarios**:

1. **Given** the baseline and perturbed latent vectors for all question pairs that passed the semantic drift check (score ≥ 0.95), **When** the system calculates the pairwise cosine similarity for both conditions, **Then** it performs a paired t-test (or Wilcoxon signed-rank test if normality fails or n < 30) and outputs the p-value, mean difference, and confidence interval.
2. **Given** the statistical results, **When** the p-value is less than 0.05 (after family-wise error correction), **Then** the system flags the result as "Significant Separability Increase," otherwise it flags it as "No Significant Change."

---

### Edge Cases

- **Semantic Collapse**: What happens if the injected noise is too high ($\sigma > 0.2$) and causes the model to output gibberish or hallucinate, invalidating the "thought" vector? (System must detect this via the Semantic Validity Check and exclude the pair or the entire $\sigma$ level).
- **Normality Violation**: How does the system handle a distribution of similarity differences that is heavily skewed? (System must automatically switch from paired t-test to Wilcoxon signed-rank test).
- **Resource Exhaustion**: What happens if the dataset size exceeds the available RAM limit of the CI runner? (System must implement a streaming or batching strategy to process pairs in chunks).
- **No Valid Sigma**: What happens if no $\sigma$ value is found that preserves semantic validity while perturbing the manifold? (System must report the trade-off curve and flag the experiment as inconclusive for that task type).

## Requirements

### Functional Requirements

- **FR-001**: System MUST load a frozen transformer model (e.g., Llama-3-8B or distilled variant) in CPU-only mode without requiring CUDA or GPU accelerators. (See US-1)
- **FR-002**: System MUST extract the hidden state vector at the designated "thought" token for every input question in the dataset. (See US-1)
- **FR-003**: System MUST inject perturbations ($\sigma$) directly into the input token embeddings before forward pass using the following algorithm: (1) Add Gaussian noise $N(0, \sigma^2)$ to the continuous input embedding vector, (2) Project the noisy vector to the nearest valid token embedding in the model's vocabulary (minimizing Euclidean distance), (3) Use the corresponding token ID for the forward pass. The system MUST execute a linear sweep of perturbation magnitudes $\sigma$ across a defined range in fixed increments. If >90% of pairs fail the semantic validity check at a specific $\sigma$, the system MUST record this as the 'validity collapse point' for that task type and exclude that $\sigma$ (and all higher values) from the final statistical analysis. (See US-2)
- **FR-004**: System MUST calculate the pairwise cosine similarity between the latent vectors of distinct questions within the same task type for both baseline and perturbed conditions. (See US-3)
- **FR-005**: System MUST perform a statistical hypothesis test (paired t-test if normality holds and n ≥ 30; otherwise Wilcoxon signed-rank test) on the distribution of similarity differences. The system MUST apply a family-wise error correction (Bonferroni or Holm) to all resulting p-values across all tested task types and noise thresholds before determining statistical significance. (See US-3)
- **FR-006**: System MUST execute a semantic validity check on the generated output text. The check MUST compare the output against the dataset's ground truth answer key (column `expected_answer`) using: (a) a strict answer token match, OR (b) a semantic equivalence check using BERTScore (F1 score ≥ 0.85). Additionally, the output perplexity MUST be ≤ 2.0x the baseline perplexity. If either the token/semantic match fails OR the perplexity bound is exceeded, the pair is excluded from analysis. If the dataset lacks an `expected_answer` column, the system MUST raise a configuration error and halt. (See US-2)
- **FR-007**: System MUST report a sensitivity analysis of the separability metric across the sweep of noise thresholds ($\sigma \in [0.01, 0.20]$) to validate the robustness of the findings. If no $\sigma$ yields valid semantic coherence, the system MUST report the trade-off curve between perturbation magnitude and semantic validity. (See US-3)
- **FR-009**: System MUST compute a semantic drift metric using a frozen, external embedding model (specifically `sentence-transformers/all-MiniLM-L6-v2`) to verify that the perturbed input still maps to the same semantic cluster as the baseline input. Pairs failing this check (cosine similarity < 0.95 with baseline in external space) MUST be excluded from the statistical test. This check serves as the independent validation of the *input* perturbation, decoupled from the target model's output generation. (See US-2, US-3)
- **FR-011**: System MUST calculate the global semantic validity pass-rate (percentage of pairs passing FR-006 and FR-009) for each $\sigma$ level. If the pass-rate falls below a predefined threshold for a specific $\sigma$, the system MUST abort processing for that $\sigma$ and subsequent higher values, recording the 'validity collapse point'. (See US-2)
- **FR-012**: System MUST verify the sample size of the filtered pair set before running the statistical test. If the number of valid pairs (n) is insufficient to meet the assumptions of parametric testing, the system MUST automatically switch to the Wilcoxon signed-rank test and report the reduced statistical power in the output. (See US-3)

### Key Entities

- **QuestionPair**: A logical grouping of two distinct questions from the same task type, identified by a unique PairID.
- **LatentVector**: A high-dimensional vector representation extracted from the model's hidden state at the "thought" token.
- **SimilarityMetric**: The cosine similarity score between two LatentVectors, ranging from -1 to 1.
- **NoiseConfig**: A configuration object defining the noise distribution parameters ($\mu=0$, $\sigma$).
- **SemanticDriftScore**: A cosine similarity score between the baseline and perturbed input embeddings as measured by the external SBERT model.
- **ValidityCollapsePoint**: The specific noise magnitude ($\sigma$) at which the global semantic validity pass-rate drops below [deferred], causing the system to halt further testing for that task type.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The reduction in mean pairwise cosine similarity between baseline and perturbed conditions is measured against the null hypothesis of zero difference using a paired statistical test, **restricted to pairs that passed the independent semantic drift check (FR-009) with a score ≥ 0.95**. (See FR-005, FR-009)
- **SC-002**: The robustness of the separability finding is measured against a sensitivity sweep of noise thresholds ($\sigma \in [0.01, 0.20]$) to ensure the effect is not an artifact of a single arbitrary $\sigma$. (See FR-007)
- **SC-003**: The system's ability to calculate the semantic validity pass-rate is measured against the requirement to report this rate for every $\sigma$ level. (See FR-011)
- **SC-004**: The computational feasibility is measured against the constraint of execution within 6 hours on a 2-core, CPU-only runner with a **peak Resident Set Size (RSS) ≤ 7GB**, measured via Python `tracemalloc` module on the main process. (See FR-001)
- **SC-005**: The methodological soundness regarding multiplicity is measured by the application of a family-wise error correction (Bonferroni or Holm) if multiple task types are tested simultaneously. (See FR-005)
- **SC-006**: The distribution of the 'validity collapse point' is measured across all task types to determine the robustness of the perturbation method. (See FR-003)

## Assumptions

- **Dataset Availability**: The "23 reasoning tasks" dataset or a publicly available equivalent (e.g., BigBench subset) is accessible and contains the specific "within-task" question pairs previously identified as failing the Separability axiom, along with a **ground truth answer key** (column `expected_answer`) for semantic validity checks.
- **Model Compatibility**: A small, open-weight model (e.g., Llama-3-8B or a distilled variant) is available in a format compatible with CPU-only inference via `transformers` without requiring 8-bit quantization or GPU-specific kernels.
- **Perturbation Validity**: The existence of a "sweet spot" for $\sigma$ is NOT assumed. The system MUST empirically measure and report the trade-off curve between perturbation magnitude and semantic validity (as mandated by FR-007) to verify if a range of $\sigma$ exists where the input perturbation alters the latent manifold while preserving semantic meaning.
- **Input vs Output Validity**: The SBERT check (FR-009) validates the *input* perturbation (ensuring it is a valid semantic neighbor), while the BERTScore check (FR-006) validates the *output* (ensuring the task capability is preserved). These are distinct and necessary to avoid circular validation: the input check ensures the perturbation is "small" in semantic space, the output check ensures the model didn't "break" the task, and the latent check measures the effect of the input perturbation on the representation.
- **Inference Cost**: The total number of question pairs is small enough that the cumulative forward pass time for both baseline and perturbed conditions fits within the 6-hour CI job limit on a 2-core runner.
- **Statistical Normality**: The distribution of similarity differences is either approximately normal (allowing t-test) or the sample size is sufficient to rely on the Wilcoxon signed-rank test as a robust non-parametric alternative.
- **No Causal Claims**: The study is observational regarding the model's internal mechanics; findings will be framed as associational evidence regarding the "smoothness" hypothesis, not as proof of architectural incapacity without further controlled ablation.
- **External Embedding Model**: A frozen, pre-trained Sentence-BERT model (`sentence-transformers/all-MiniLM-L6-v2`) is available for the independent semantic drift check (FR-009) and does not require GPU acceleration.