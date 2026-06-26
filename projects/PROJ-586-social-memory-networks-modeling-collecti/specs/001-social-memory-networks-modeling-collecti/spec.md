# Feature Specification: Social Memory Networks: Modeling Collective Remembering in Multi‑Agent LLMs

**Feature Branch**: `001-social-memory-networks`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: "Modeling collective remembering in multi‑agent LLMs to test transactive‑memory dynamics (specialization and cue‑driven retrieval) and their robustness to context‑window truncation."

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Baseline Transactive‑Memory Measurement (Priority: P1)

A researcher wants to obtain baseline measurements of specialization and cue‑retrieval efficiency when agents have full context, so that the phenomenon can be quantified before any manipulation.

**Why this priority**: Establishes the core dependent variables (specialization index, retrieval efficiency) required for all downstream analyses.

**Independent Test**: Run the experiment with the *Full‑context* condition only and verify that the script outputs both metrics and a reproducible CSV summary.

**Acceptance Scenarios**:

1. **Given** the experiment script is invoked with `--context full`, **When** 1 000 Hanabi games are simulated, **Then** a CSV file `results_full.csv` is produced containing (a) specialization index for each game and (b) cue‑retrieval efficiency per game, with no missing values.
2. **Given** the same run, **When** the script computes the specialization index, **Then** the reported value lies within the theoretical bounds for N_agents (0 to log₂(N_agents)).

### User Story 2 – Context‑Window Truncation Impact (Priority: P2)

A researcher wants to compare the baseline metrics against a limited‑context condition to test whether truncation degrades transactive‑memory dynamics.

**Why this priority**: Directly addresses the primary research question about robustness under context limits.

**Independent Test**: Run the experiment with the *Limited‑context* condition and verify that the statistical comparison reports a significant interaction (p < 0.05) or a documented null result.

**Acceptance Scenarios**:

1. **Given** the experiment script is invoked with `--context limited`, **When** 1 000 games are simulated, **Then** a CSV file `results_limited.csv` is produced with the same two metrics and no missing values.
2. **Given** both `results_full.csv` and `results_limited.csv`, **When** the analysis module executes, **Then** it outputs an ANOVA table reporting the Context × Metric interaction term and its p‑value, and the script flags significance according to α = 0.05.

### User Story 3 – Scaling Analysis Across Agent Populations (Priority: P3)

A researcher wants to investigate how the fidelity of collective remembering scales when the number of agents varies (e.g., 3, 5, 7 agents).

**Why this priority**: Extends the findings, satisfies reviewer suggestions about scaling laws, and tests methodological robustness. Note: Power‑law fitting with only 3 data points is statistically underpowered; this limitation is acknowledged in the analysis plan.

**Independent Test**: Run the experiment for each specified agent count and produce a plot of specialization index and retrieval efficiency versus number of agents, along with a fitted power‑law exponent.

**Acceptance Scenarios**:

1. **Given** the script is invoked with `--agents 3,5,7`, **When** each configuration runs 800 games, **Then** a PDF `scaling_plot.pdf` is generated showing metric trends and the estimated exponent (β) for each metric.
2. **Given** the scaling results, **When** β is computed, **Then** the script reports the 95 % confidence interval and notes whether the exponent is sub‑linear (β < 1), with a note that 3 data points limit power‑law reliability.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a command‑line interface `run_experiment.py` that accepts flags `--context {full,limited}`, `--agents N`, and `--dataset {hanabi,coqa}` (See US-1, US-2, US-3).  
- **FR-002**: The system MUST instantiate multiple public decoder‑only LLMs via the `transformers` library (See US-1).  
- **FR-003**: The system MUST implement a shared external memory buffer that agents can read/write using a standardized `<MEMORY_ACTION>` token (See US-1).  
- **FR-004**: The system MUST compute the specialization index as a distribution‑based metric of per‑agent fact‑contribution for each game, bounded between 0 and log₂(N_agents) (See US-1, US-3).  
- **FR-005**: The system MUST compute cue‑retrieval efficiency as the proportion of successful fact‑retrieval queries when the querying agent provides an explicit cue, relative to uniform chance baseline (1/N_agents) (See US-1, US-2).  
- **FR-006**: The system MUST perform a two‑way independent‑samples ANOVA with factors *Context* (full vs limited) and *Metric* (specialization, retrieval) and output the interaction p‑value (See US-2).  
- **FR-007**: The system MUST apply a Bonferroni correction to all family‑wise hypothesis tests and report the corrected α (See US-2).  
- **FR-008**: The system MUST conduct a sensitivity analysis sweeping the context‑truncation token limit over the set {128, 256, 512} tokens and record how each metric varies (See US-2).  
- **FR-009**: The system MUST generate a power‑analysis report estimating the detectable effect size for the interaction given N = 1 000 games, α = 0.05, and power = 0.80; if the estimated power < 0.70, the report must flag a limitation (See US-2).  
- **FR-010**: The system MUST log all runtime errors (e.g., malformed memory tokens, file‑write conflicts) to `experiment.log` with timestamps and continue processing remaining games (See Edge Cases).  
- **FR-011**: The system MUST detect when the external dataset lacks explicit cue annotations and fall back to a synthetic cue generator that creates cue‑response pairs from available context spans (See Assumptions).  
- **FR-012**: The system MUST handle write‑conflicts to the shared memory buffer by implementing a queue‑based serialization mechanism and logging conflict events (See Edge Cases).  

### Key Entities *(include if feature involves data)*

- **Agent**: Represents a single LLM instance; key attributes include `model_name`, `generated_text`, and `memory_actions`.  
- **MemoryBuffer**: External shared memory store; attributes include `key`, `value`, `timestamp`, and `owner_agent_id`.  
- **GameResult**: Row in the output CSV; fields `game_id`, `specialization_index`, `retrieval_efficiency`, `context_condition`, `agent_count`.  

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Baseline metrics (specialization index, cue‑retrieval efficiency) are successfully computed for ≥ 95 % of games in the full‑context condition (See US-1).  
- **SC-002**: The ANOVA interaction term is reported with a p‑value and, if p < 0.05, the system logs "Significant context effect" (See US-2).  
- **SC-003**: The sensitivity analysis produces a trend report across the three token thresholds, and the maximum absolute change in any metric between thresholds is [deferred] (See US-2).  
- **SC-004**: The power‑analysis report indicates [deferred] statistical power for the planned interaction, or otherwise the report includes an explicit "Power limitation" flag (See US-2).  
- **SC-005**: The scaling analysis plot (`scaling_plot.pdf`) includes fitted power‑law curves with [deferred] for both metrics across agent counts 3, 5, 7; note that 3 data points limit power‑law reliability (See US-3).  

## Assumptions

- The Hanabi Learning Environment dataset provides sufficient "facts" (game state descriptions) that can be encoded as discrete memory entries; if not, a fallback synthetic fact generator will be used.  
- The CoQA‑MultiAgent dataset may or may not contain explicit cue annotations; the system will detect this condition and fall back to a synthetic cue generator that creates cue‑response pairs from available context spans, with a minimum of 10 synthetic cues per game to ensure statistical validity.  
- All selected LLMs fit within available compute resources; otherwise, models will be loaded sequentially per turn to stay within memory limits.  
- Context‑window truncation thresholds align with community‑standard token budgets for the chosen model class; the chosen sweep set {128, 256, 512} reflects typical inference constraints.  
- No GPU or CUDA libraries are required; all `transformers` calls use CPU inference and default float32 precision.  
- The external memory buffer size will remain within disk usage limits throughout the experiment.  
- Random seeds are fixed (`seed=42`) to guarantee reproducibility across CI runs.  

---