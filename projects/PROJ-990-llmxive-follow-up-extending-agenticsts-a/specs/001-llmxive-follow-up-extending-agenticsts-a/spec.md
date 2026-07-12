# Feature Specification: llmXive follow-up: extending "AgenticSTS: A Bounded-Memory Testbed for Long-Horizon LLM Agents"

**Feature Branch**: `001-llmxive-agenticsts-followup`  
**Created**: 2026-07-05  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'AgenticSTS: A Bounded-Memory Testbed for Long-Horizon LLM Agents'"

## User Scenarios & Testing

### User Story 1 - Dynamic Memory Policy Execution (Priority: P1)

As a researcher running the AgenticSTS testbed, I need the system to automatically select a subset of typed memory layers for each decision turn based on real-time game-state entropy, so that I can evaluate if adaptive retrieval preserves win rates while reducing token usage compared to a static baseline.

**Why this priority**: This is the core hypothesis test. Without the dynamic policy implementation, the comparison against the static "all-layers" baseline cannot occur, and the primary research question remains unanswered.

**Independent Test**: This can be tested by running a held-out set of game trajectories through the dynamic policy agent and verifying that the agent successfully retrieves a variable number of memory layers (less than the total available) based on the calculated entropy of the current turn, without crashing or exceeding the hard token budget.

**Acceptance Scenarios**:

1. **Given** a game trajectory with a high-entropy decision turn (e.g., multiple enemy threats), **When** the dynamic policy agent processes the turn, **Then** the system selects a larger subset of memory layers (e.g., ≥ 3 layers) to ensure sufficient context.
2. **Given** a game trajectory with a low-entropy decision turn (e.g., routine movement), **When** the dynamic policy agent processes the turn, **Then** the system selects a minimal subset of memory layers (e.g., ≤ 1 layer) to maximize token savings.
3. **Given** a game trajectory where the calculated entropy suggests a specific layer set, **When** the token budget is exceeded by the raw layer content, **Then** the system truncates or prunes the least useful layers to ensure the final prompt size is ≤ the defined budget (e.g., 4096 tokens).

---

### User Story 2 - Baseline Comparison & Metric Aggregation (Priority: P2)

As a researcher, I need the system to re-simulate the same test trajectories using a static "all-layers" retrieval baseline and a "no-store" random baseline, so that I can generate comparative data on win rates and token consumption.

**Why this priority**: The value of the dynamic policy is only apparent when contrasted against a static standard. This story ensures the necessary control data is generated to support statistical analysis.

**Independent Test**: This can be tested by executing the same set of held-out trajectories through the static baseline agent and verifying that the output logs contain the total token count and the final win/loss outcome for every trajectory.

**Acceptance Scenarios**:

1. **Given** the same set of 50 held-out game trajectories used for the dynamic policy, **When** the static baseline agent runs, **Then** the system records the total prompt token count and the final win rate for the entire set.
2. **Given** the same set of trajectories, **When** the "no-store" random baseline agent runs, **Then** the system records the total prompt token count and the final win rate to establish a lower-bound performance floor.
3. **Given** the results from all three conditions (Dynamic, Static, Random), **When** the aggregation script runs, **Then** it outputs a summary CSV containing the average win rate and average token usage per condition.

---

### User Story 3 - Statistical Significance Reporting (Priority: P3)

As a researcher, I need the system to perform paired statistical tests (McNemar's test) on the per-trajectory win/loss outcomes between the dynamic and static baselines, so that I can determine if the observed improvements are statistically significant.

**Why this priority**: This story provides the scientific rigor required to validate the hypothesis. It transforms raw data into a defensible conclusion regarding the efficacy of the dynamic policy.

**Independent Test**: This can be tested by running the analysis script on a generated dataset where the dynamic policy has a known [deferred] token reduction and identical win rates, and verifying that the script correctly reports a non-significant difference in win rate (p > 0.05) and a significant difference in token usage (p < 0.05).

**Acceptance Scenarios**:

1. **Given** paired binary win/loss data from the dynamic and static baselines for the same trajectories, **When** the normality assumption is not applicable (binary data), **Then** the system automatically selects and executes McNemar's test.
2. **Given** paired token-usage data, **When** the normality assumption holds, **Then** the system executes a paired t-test and outputs the p-value and effect size.
3. **Given** multiple hypothesis tests (win rate and token usage), **When** the analysis completes, **Then** the system applies a Bonferroni correction to the reported p-values to control for multiplicity.

---

### Edge Cases

- **What happens when** the game-state entropy calculation returns `NaN` or `Infinity` due to a malformed game state (e.g., division by zero in threat calculation)?
  - *Handling*: The system MUST default to retrieving the full "all-layers" set for that specific turn to prevent context starvation, and log a warning event.
- **How does the system handle** a scenario where the "dynamic" selection logic predicts a token count that is already below the minimum viable context window (e.g., < 256 tokens)?
  - *Handling*: The system MUST enforce a hard minimum token floor by appending the most critical memory layer. (e.g., "Current Objective") regardless of the entropy prediction.
- **What happens when** the 298 existing AgenticSTS trajectories are insufficient to train the lightweight classifier with statistical power?
  - *Handling*: The system MUST flag the training set size as insufficient if the number of samples n < 300, defaulting to a simpler heuristic (e.g., fixed k=2) in such cases. For a set of existing AgenticSTS trajectories, the system assumes this meets the minimum threshold for a lightweight classifier (Decision Tree/Logistic Regression) based on convention in ML literature for low-complexity models, but MUST log a warning that statistical power is marginal (n=298) and recommend expanding the dataset if the classifier's cross-validation accuracy falls below an acceptable threshold.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST parse the existing AgenticSTS trajectories to extract per-turn game metrics (health ratio, enemy threat level, deck size, and move entropy) and the corresponding ground-truth memory layer utility. "Move entropy" is defined as the Shannon entropy of the probability distribution of available legal moves. "Ground-truth memory layer utility" is defined as the measured impact on win rate when a specific layer is removed (ablation study), not derived from static retrieval logs (See US-1).
- **FR-002**: The system MUST train a lightweight, CPU-tractable classifier (e.g., Decision Tree or Logistic Regression) on a training split of the trajectories to predict memory layer utility based on game state features (See US-1).
- **FR-003**: The system MUST implement a dynamic retrieval agent that, for each turn in the test set, queries the trained model to select the top-$k$ predicted high-utility layers, constrained by a hard token budget of 4096 tokens (See US-1).
- **FR-004**: The system MUST re-simulate the game runs for the test set using the dynamic policy, the static "all-layers" baseline, and a "no-store" random baseline to generate comparable outcome data (See US-2).
- **FR-005**: The system MUST perform paired statistical tests (McNemar's test for binary win/loss outcomes; paired t-test for token usage) to compare dynamic and static baselines, applying a Bonferroni correction for multiple comparisons (See US-3).
- **FR-006**: The system MUST validate the proxy assumption that static-log-derived utility correlates with ablation-derived utility by testing on a hold-out set of at least 20 trajectories where ground truth is established via ablation (See US-3).

### Key Entities

- **Game Trajectory**: A sequence of turns representing a single game run, containing per-turn state metrics and the final win/loss outcome.
- **Memory Layer**: A typed category of stored information (e.g., "Inventory", "Enemy State", "Objective") associated with a specific token cost.
- **Entropy Metric**: A numerical value derived from game state features representing the stochasticity or complexity of the current decision context.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Win rate of the dynamic policy is measured against the win rate of the static "all-layers" baseline using McNemar's test (See US-3).
- **SC-002**: Average prompt token usage of the dynamic policy is measured against the average token usage of the static "all-layers" baseline to verify a reduction of at least 30% (See US-2).
- **SC-003**: Statistical significance of the win rate difference is measured against a significance level of α = 0.05, with Bonferroni correction applied for multiple tests (See US-3).
- **SC-004**: Token reduction consistency is measured by calculating the standard deviation of token savings across the held-out test set to ensure the policy does not produce erratic results (See US-2).

## Assumptions

- The 298 existing AgenticSTS trajectories contain sufficient variance in game-state entropy to train a meaningful lightweight classifier; if the dataset is too homogeneous, the system defaults to a heuristic fallback.
- The "information utility" of memory layers inferred from static retrieval logs is a valid proxy for the dynamic context, provided that a correlation check (FR-006) confirms a Pearson correlation coefficient ≥ 0.7 between the proxy and ablation-derived ground truth on a hold-out set.
- The game engine's ground-truth outcome logic (win/loss) is independent of the specific memory retrieval strategy used during the original runs, ensuring valid comparison.
- The lightweight classifier (Decision Tree/Logistic Regression) will train and infer within the standard GitHub Actions free-tier time limit on a limited number of CPU cores with constrained RAM...
- The hard token budget of 4096 tokens is a defensible community standard for bounded-context experiments; if the specific game context requires a different size, this will be adjusted in the implementation phase.
- The entropy calculation method (based on health, threat, deck size) is sufficient to proxy "decision complexity" without requiring a full simulation of the agent's internal reasoning state.