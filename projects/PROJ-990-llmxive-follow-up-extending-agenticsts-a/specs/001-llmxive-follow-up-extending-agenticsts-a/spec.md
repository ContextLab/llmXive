# Feature Specification: llmXive follow-up: extending "AgenticSTS: A Bounded-Memory Testbed for Long-Horizon LLM Agents"

**Feature Branch**: `001-llmxive-memory-adaptation`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'AgenticSTS: A Bounded-Memory Testbed for Long-Horizon LLM Agents'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dataset Parsing and Entropy Calculation (Priority: P1)

The research system MUST parse the AgenticSTS trajectories from the repository `https://huggingface.co/datasets/agentic-sts/trajectories-v1` to extract per-turn game metrics (health ratio, enemy threat level, deck size) and compute the Shannon entropy of the possible move distribution for every turn. This is the foundational data layer required for all subsequent analysis; without accurate entropy labeling of the environment's stochasticity, no dynamic policy can be trained or evaluated.

**Why this priority**: This is the data prerequisite. If the environment's volatility cannot be quantified from the logs, the core hypothesis regarding "stochasticity of the decision environment" cannot be tested.

**Independent Test**: Can be fully tested by running the parsing script on the raw trajectory logs from the specified repository and verifying that the output CSV contains non-null entropy values for every turn across all trajectories, with entropy values bounded between 0 and log2(number of possible moves), and that the SHA-256 checksum of the downloaded data matches the published hash.

**Acceptance Scenarios**:

1. **Given** a raw AgenticSTS trajectory log file from the specified repository, **When** the parsing script processes the file, **Then** the output includes a column `shannon_entropy` where every value is $\ge 0$ and $\le \log_2(\text{max\_moves})$.
2. **Given** a trajectory with constant enemy threat and health, **When** the entropy is calculated, **Then** the resulting entropy value is 0 (indicating a deterministic environment).
3. **Given** a trajectory where all possible moves are equally likely, **When** the entropy is calculated, **Then** the resulting entropy value matches the theoretical maximum for the action space size.

---

### User Story 2 - Dynamic Policy Training and Simulation (Priority: P2)

The system MUST train a lightweight, CPU-tractable classifier (e.g., shallow decision tree or logistic regression) on a training split of the parsed trajectories to predict the "utility" of memory layers based on game state features and entropy. The "utility" of a layer is defined as the **reduction in KL divergence** achieved by including that specific layer compared to excluding it, calculated using the move distribution of the **STATIC baseline** (to ensure the training target is independent of the dynamic policy). The system MUST then implement a dynamic retrieval agent that uses this model to select only the top-$k$ predicted high-utility layers during simulation, constrained by a hard token budget.

**Why this priority**: This implements the core experimental intervention (the dynamic policy) against which the static baselines are compared. It represents the "dynamic adaptation" component of the research question.

**Independent Test**: Can be fully tested by training the model on the training split, running the dynamic agent on a held-out test set, and verifying that the agent achieves a statistically significant reduction in token usage (p < 0.05) compared to the static "all-layers" baseline while maintaining non-inferior win rates, and that the model predicts per-layer utility scores correctly.

**Acceptance Scenarios**:

1. **Given** a trained classifier and a test trajectory, **When** the dynamic agent runs, **Then** the number of retrieved memory layers per turn is $\le$ the total available layers and $\ge 1$.
2. **Given** a high-entropy turn in the test set, **When** the agent queries the model, **Then** the selected top-$k$ layers have a higher average predicted utility (reduction in KL divergence vs. exclusion) than a random selection of the same size from the available layers.
3. **Given** a hard token budget of 4096 tokens, **When** the agent constructs the prompt, **Then** the total token count of the retrieved context is $\le 4096$.

---

### User Story 3 - Statistical Comparison and Reporting (Priority: P3)

The system MUST simulate the game runs for the test set using the dynamic policy and compare outcomes against two baselines: (1) static "all-layers" retrieval and (2) "no-store" random retrieval. It MUST calculate win rates and average token consumption, then apply the **Exact Binomial Test on Discordant Pairs** (with shifted null hypothesis) to determine if the dynamic policy's win rate is non-inferior to the static baseline (within a 5% margin) while significantly reducing token usage.

**Why this priority**: This delivers the final scientific result required to answer the research question. It validates the "expected results" regarding win rate preservation and token reduction.

**Independent Test**: Can be fully tested by executing the full evaluation pipeline on the test set and generating a report containing win rates, token averages, and p-values for the comparisons, ensuring the non-inferiority test is applied correctly for paired binary outcomes and the token test handles non-normality.

**Acceptance Scenarios**:

1. **Given** the results from the dynamic, static, and random baselines, **When** the statistical analysis runs, **Then** the report includes a p-value from the Exact Binomial Test on Discordant Pairs comparing dynamic vs. static win rates.
2. **Given** the dynamic policy results, **When** token usage is calculated, **Then** the average token reduction compared to the static baseline is reported as a percentage.
3. **Given** the hypothesis that dynamic $\approx$ static win rate, **When** the non-inferiority test is run with a margin of $\delta = 0.05$, **Then** the result is explicitly labeled as "supported" or "rejected" based on the p-value threshold of $\alpha = 0.05$.

---

### Edge Cases

- What happens when a trajectory has 0 variance in possible moves (entropy = 0)? The system must handle this without division-by-zero errors in entropy calculation.
- How does the system handle a trajectory where the "utility" prediction model assigns near-zero utility to all layers? The system must enforce a minimum retrieval of 1 layer to prevent agent starvation.
- How does the system handle a trajectory where the token budget is so tight that even the single highest-utility layer exceeds the limit? The system must truncate the layer content or skip the retrieval for that turn, logging the event as a "budget violation."

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST parse the AgenticSTS trajectories from the repository `https://huggingface.co/datasets/agentic-sts/trajectories-v1` to extract per-turn metrics (health ratio, enemy threat level, deck size) and compute Shannon entropy for every turn. The system MUST verify the SHA-256 checksum of the downloaded data and validate the presence of the `move_distribution` (probability vector) column before processing. (See US-1).
- **FR-002**: The system MUST train a lightweight, CPU-tractable classifier (e.g., decision tree or logistic regression) on a training split to predict the **per-layer utility** of memory layers. Utility is defined as the reduction in KL divergence achieved by including the layer compared to excluding it, calculated using the **STATIC baseline's** move distribution. Features MUST include turn-level metrics (health, threat, entropy) AND layer-specific attributes (layer index, semantic similarity to current state) to enable per-layer prediction. (See US-2).
- **FR-003**: The dynamic retrieval agent MUST select only the top-$k$ predicted high-utility layers for each turn based on the per-layer utility scores, where $k$ is dynamically constrained by a hard token budget of 4096 tokens. (See US-2).
- **FR-004**: The system MUST simulate game runs for the held-out test set using the dynamic policy, the static "all-layers" baseline, and the "no-store" random baseline. (See US-3).
- **FR-005**: The system MUST calculate win rates and average token consumption for each condition. For win rates, it MUST apply the **Exact Binomial Test on Discordant Pairs** (shifted null) to test non-inferiority within a margin of $\delta = 0.05$. For token consumption, it MUST first perform a Shapiro-Wilk normality test on the paired differences; if $p < 0.05$, it MUST use the **Wilcoxon signed-rank test**, otherwise a paired t-test, to verify a reduction of $\ge 30\%$ and $\le 50\%$. (See US-3).
- **FR-006**: The system MUST implement **Holm-Bonferroni correction** ONLY for the family of tests comprising the sensitivity analysis sweeps (FR-007), not for the primary win rate or secondary token reduction tests. (See US-3).
- **FR-007**: The system MUST perform a sensitivity analysis by re-running the simulation with token budgets of $\{2048, 6144\}$ tokens (in addition to the primary 4096) and report the robustness of the token reduction claim across these thresholds. (See US-3).
- **FR-008**: The system MUST perform an **a priori power analysis** to determine the minimum number of trajectories required to detect a 5% non-inferiority margin ($\delta=0.05$) with $\alpha=0.05$ and power $\ge 0.80$. If the available dataset size is below this threshold, the study must be declared "underpowered" and non-inferiority claims must be withheld. (See US-3).

### Key Entities

- **Trajectory**: A single game run containing a sequence of turns, each with game state metrics and move outcomes.
- **Entropy**: A scalar value ($0 \le H \le \log_2 N$) representing the stochasticity of the possible move distribution at a specific turn.
- **Memory Layer**: A distinct chunk of context information available for retrieval, associated with a predicted utility score (reduction in KL divergence).
- **Baseline Condition**: The configuration of the agent (Dynamic, Static, or Random) used during simulation for comparison.
- **Layer Embedding**: A vector representation of a memory layer's content used as a feature for the utility classifier.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Win rate of the dynamic policy is measured against the win rate of the static "all-layers" baseline to determine non-inferiority. (See US-3).
- **SC-002**: Average token consumption of the dynamic policy is measured against the average token consumption of the static baseline to quantify reduction, verifying the reduction is $\ge 30\%$ and $\le 50\%$. (See US-3).
- **SC-003**: Statistical significance of the win rate difference is measured against the $\alpha = 0.05$ threshold using the Exact Binomial Test on Discordant Pairs with a non-inferiority margin of $\delta = 0.05$. (See US-3).
- **SC-004**: The validity of the entropy predictor is measured by checking the correlation between computed Shannon entropy and the **win-rate improvement (Dynamic - Static) in high-entropy turns**. (See US-2).
- **SC-005**: The computational feasibility is measured by ensuring the total runtime of the training and simulation pipeline does not exceed **6 hours** on a standard **ubuntu-22.04-8core** GitHub Actions runner (8 vCPUs, 32GB RAM). (See US-2).
- **SC-006**: The sensitivity analysis report MUST include win rate and token usage trends across the $\{2048, 4096, 6144\}$ token budget sweep. (See US-3).

## Assumptions

- The existing AgenticSTS trajectories from `https://huggingface.co/datasets/agentic-sts/trajectories-v1` contain sufficient metadata (`move_distribution` as probability vector, `health`, `threat`, `deck_size`) to accurately compute Shannon entropy and train the utility classifier.
- The "win rate" metric is defined consistently across the static, dynamic, and random baselines using the game engine's ground-truth outcome logic, independent of the input features.
- The lightweight classifier (decision tree/logistic regression) is sufficient to capture the relationship between game state entropy and memory utility (KL divergence reduction) without requiring deep learning or GPU acceleration.
- The hard token budget of 4096 tokens is a defensible community-standard default for LLM context windows in this research domain, as no specific budget was fixed in the idea description.
- The analysis will be conducted on a CPU-only environment; no GPU, CUDA, or mixed-precision training will be used, relying on standard scikit-learn or similar CPU-optimized libraries.
- The "no-store" random baseline will select memory layers uniformly at random, serving as a lower-bound control for retrieval effectiveness.
- The sensitivity analysis for the token budget threshold will sweep the cutoff over $\{2048, 4096, 6144\}$ tokens to verify the robustness of the token reduction claim.
- The dataset provides a SHA-256 checksum file for integrity verification.
- The a priori power analysis will determine that the available dataset size is sufficient to detect a 5% non-inferiority margin with 80% power.