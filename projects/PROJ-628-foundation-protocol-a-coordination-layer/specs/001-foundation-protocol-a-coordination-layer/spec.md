# Feature Specification: Foundation Protocol – Coordination Layer for Agentic Society

**Feature Branch**: `feature-001-foundation-protocol`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: “How does the adoption of a standardized coordination protocol (the Foundation Protocol) affect the efficiency and robustness of heterogeneous autonomous agents interacting in a simulated multi‑agent ecosystem?”  

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Evaluate Efficiency Gains in a Cooperative Game (Priority: P1)

Researchers run the Hanabi cooperative card game using three heterogeneous agents (PPO learner, rule‑based planner, heuristic) that communicate exclusively via a selected protocol.  
**Why this priority**: Demonstrates the core claim that the Foundation Protocol improves task‑completion speed and reduces communication overhead, directly addressing the primary research question.  
**Independent Test**: Execute the Hanabi benchmark under two conditions: (1) Foundation Protocol with native un-wrapped communication stacks for baseline, and (2) Foundation Protocol. Compare average episode length, total messages, and bandwidth using a concurrent baseline run on identical seeds.  
**Acceptance Scenarios**:

1. **Given** the agents are instantiated with the Foundation Protocol, **When** random seeds are run, **Then** the mean episode length is ≤ 95 % of the baseline mean (i.e., ≥ 5 % reduction) measured against a concurrent baseline run using legacy protocols on the same seeds.  
2. **Given** the agents use legacy protocols, **When** the same seeds are run, **Then** the mean total messages exchanged is ≥ 1.10 × the Foundation Protocol mean (i.e., ≥ 10 % higher) measured against a concurrent baseline run using legacy protocols on the same seeds.  

---

### User Story 2 – Assess Robustness to Agent Failures (Priority: P2)

Researchers inject a crash into a randomly selected agent at 0.30 episode progress in the smart-contract auditing workflow and measure recovery.
**Why this priority**: Robustness is the second key outcome; showing faster or more successful recoveries validates the protocol’s fault‑tolerance benefits.  
**Independent Test**: Run the smart‑contract auditing workflow with the crash injection under both protocol conditions (Foundation Protocol vs. Legacy Protocol with equivalent checkpointing) and record recovery success rate and time to consensus. The baseline must use native, un-wrapped communication stacks with equivalent checkpointing capabilities.  
**Acceptance Scenarios**:

1. **Given** the Foundation Protocol is active, **When** a crash occurs at 0.30 episode progress over 30 seeds, **Then** the recovery success rate is ≥ 90 % measured against a concurrent baseline run using legacy protocols with equivalent checkpointing on the same seeds.
2. **Given** the Foundation Protocol is active, **When** a crash occurs, **Then** the recovery latency is ≤ 1.5 × the baseline recovery latency (measured in seconds) over 30 seeds.
3. **Given** the Foundation Protocol is active, **When** a crash occurs, **Then** the task-completion rate is ≥ 95 % of the baseline task-completion rate over 30 seeds.

---

### User Story 3 – Measure Communication Overhead Across Tasks (Priority: P3)

Researchers compare bandwidth consumption and message size across three benchmark tasks (Hanabi, SPEAR‑style auditing, multi‑level resource allocation).  
**Why this priority**: Quantifies the scalability implication highlighted by reviewers; essential for understanding deployment costs.  
**Independent Test**: Collect per‑episode byte traffic (normalized by payload size) for each task under both protocol conditions (Foundation Protocol vs. Legacy Protocol with equivalent signing) on identical seeds.  
**Acceptance Scenarios**:

1. **Given** the Foundation Protocol, **When** the multi‑level resource allocation task is executed, **Then** average bytes per episode (normalized) are ≤ 85 % of the baseline average.
2. **Given** the Foundation Protocol, **When** the Hanabi task is executed, **Then** average bytes per episode (normalized) are ≤ 90 % of the baseline average.
3. **Given** the Foundation Protocol, **When** the SPEAR auditing task is executed, **Then** average bytes per episode (normalized) are ≤ 85 % of the baseline average.

### Edge Cases

- What happens when an agent receives a malformed envelope (e.g., missing signature)?
- How does the system handle simultaneous crashes of multiple agents at the same timestep?
- What if the underlying network layer drops messages beyond a configurable loss rate (e.g., [deferred])?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a middleware library `foundation_protocol/` exposing message routing, envelope signing, and checkpointing APIs compatible with existing agent codebases. The baseline legacy protocols MUST also include equivalent checkpointing capabilities to isolate coordination logic. (See US-1)  
- **FR-002**: System MUST allow agents to register a protocol handler at runtime and switch between legacy protocols (using native, un-wrapped communication stacks) and the Foundation Protocol without code changes to the agent logic. (See US-1)  
- **FR-003**: System MUST log, for each episode, the total number of messages exchanged, total bytes transmitted (normalized by message payload size), and timestamps of each message for later analysis. (See US-1 & US-3)  
- **FR-004**: System MUST support injection of a deterministic crash event at a configurable episode progress fraction (fixed default 0.30) and automatically trigger the recovery workflow defined by the active protocol. The baseline MUST use equivalent checkpointing capabilities. (See US-2)  
- **FR-005**: System MUST compute and output per‑seed metrics: episode length, task‑completion success flag, recovery success flag, and recovery latency. (See US-2)  
- **FR-006**: System MUST perform paired‑sample statistical comparison: McNemar's test for binary outcomes (recovery success, task success) and paired t-test for continuous metrics (episode length, messages, bandwidth, latency) between baseline and intervention, applying a Bonferroni correction for the six primary metrics (episode length, messages, bandwidth, recovery success, recovery latency, task-completion rate) to control family-wise error rate. (See US-1, US-2, US-3)  
- **FR-007**: System MUST report a sensitivity analysis sweeping the significance threshold α over the set {0.01, 0.05, 0.10} and include effect‑size (Cohen’s d) variation across the sweep. (See US-1)  
- **FR-008**: System MUST enforce that all random seeds are fixed and logged to guarantee reproducibility. (See US-1‑US-3)  
- **FR-009**: System MUST execute all experiments on CPU‑only hardware, avoiding GPU‑specific libraries or large‑model inference. (See US‑all)  
- **FR-010**: System MUST generate a `Makefile` target `make report` that compiles all results into a LaTeX‑style PDF and archives raw CSVs under `results/` for Zenodo deposition. (See US‑all)

### Key Entities *(include if feature involves data)*

- **Agent**: an autonomous entity (e.g., PPO learner, rule‑based planner) that sends and receives messages via a selected protocol.  
- **MessageEnvelope**: structured payload containing `sender_id`, `receiver_id`, `timestamp`, `signature`, and optional `checkpoint` data.  
- **MetricRecord**: a per‑episode row capturing `seed`, `protocol`, `episode_length`, `msg_count`, `bytes_sent`, `recovery_success`, `recovery_latency`, `task_success`.  
- **ProtocolHandler**: an interface defining the methods for message serialization, signing, and checkpointing, implemented by both Foundation and Legacy protocols.  
- **BaselineConfig**: a configuration object specifying the legacy protocol implementation and its checkpointing capabilities to ensure fair comparison.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Mean episode length under the Foundation Protocol is ≤ 95 % of the baseline mean (effect size d ≥ 0.5) measured against a concurrent baseline run using legacy protocols on identical seeds (See US-1).  
- **SC-002**: Mean total messages per episode under the Foundation Protocol is ≤ 90 % of baseline measured against a concurrent baseline run using legacy protocols on identical seeds (See US-1).  
- **SC-003**: Recovery success rate after injected crash is ≥ 90 % under the Foundation Protocol AND the Foundation Protocol recovery rate is statistically significantly higher than the baseline rate (measured via McNemar's test) (See US-2).  
- **SC-004**: Average bandwidth (bytes per episode, normalized by payload size) under the Foundation Protocol is ≤ 85 % of baseline across all three tasks (See US-3).  
- **SC-005**: All paired statistical tests report p < 0.05 after Bonferroni correction: (FP episode length vs. Baseline episode length), (FP messages vs. Baseline messages), (FP bandwidth vs. Baseline bandwidth), (FP recovery success vs. Baseline recovery success), (FP recovery latency vs. Baseline recovery latency), (FP task-completion vs. Baseline task-completion); the sensitivity analysis shows that conclusions are stable for α ∈ {0.01, 0.05, 0.10} (See FR-006, FR-007).  

## Assumptions

- The PettingZoo environments (Hanabi, SPEAR‑style auditing, IRM4MLS resource allocation) are fully compatible with Python 3.10 and run within ≤ 4 GB RAM on a single CPU core.  
- Legacy protocols (MCP, A2A, DIDComm) are available as open‑source Python packages and can be imported without modification.  
- Cryptographic signing uses the `ed25519` library, which is CPU‑only and incurs negligible runtime overhead (< 1 ms per message).  
- Random‑seed count of 30 provides ≥ 80 % power to detect medium effect sizes (Cohen’s d ≈ 0.5) for the primary efficiency metrics; a formal power analysis will be documented in the final report.  
- Network latency and packet loss are simulated within the environment; real‑world network conditions are out of scope for this prototype.  

## Implementation Constraints

- The SPEAR benchmark repository does not include a ready-to-run Docker image; it requires a local data generation step using the provided `generate_data.py` script with a minimum of 30 random seeds to ensure statistical power (See FR-008). This step must be executed prior to the experiment run to populate the `data/` directory with the required synthetic audit logs.