# Data Model: Foundation Protocol

## Overview
This document defines the data structures used for inter-agent communication, experiment logging, and statistical analysis.

## Core Entities

### 1. MessageEnvelope
The fundamental unit of communication wrapped by the `foundation_protocol/`.

```yaml
type: object
properties:
  sender_id:
    type: string
    description: "Unique identifier of the sending agent"
  receiver_id:
    type: string
    description: "Unique identifier of the receiving agent"
  timestamp:
    type: number
    description: "Unix timestamp in milliseconds"
  signature:
    type: string
    description: "Ed25519 digital signature of the payload"
  payload:
    type: object
    description: "The actual message content (JSON serializable)"
  checkpoint:
    type: object
    description: "Optional checkpoint data for recovery"
    nullable: true
  protocol_version:
    type: string
    description: "Version of the Foundation Protocol"
```

### 2. MetricRecord
A single row in the experiment results CSV.

```yaml
type: object
properties:
  seed:
    type: integer
    description: "Random seed used for this episode"
  protocol:
    type: string
    enum: ["foundation", "native_direct"]
    description: "Protocol type used"
  task:
    type: string
    enum: ["hanabi", "spear", "resource_allocation"]
    description: "Benchmark task name"
  episode_length:
    type: integer
    description: "Number of steps taken in the episode"
  msg_count:
    type: integer
    description: "Total number of messages exchanged"
  bytes_sent:
    type: number
    description: "Total bytes transmitted (normalized by payload size)"
  recovery_success:
    type: boolean
    description: "Whether the system recovered from a crash"
  recovery_latency:
    type: number
    description: "Time (seconds) to recover from crash"
  task_success:
    type: boolean
    description: "Whether the task was completed successfully"
  agent_types:
    type: array
    items:
      type: string
    description: "List of agent types in the episode (e.g., ['ppo', 'rule'])"
```

### 3. BaselineConfig
Configuration for the native direct communication comparison.

```yaml
type: object
properties:
  communication_mode:
    type: string
    enum: ["native_direct"]
    description: "Communication mode (only native_direct for baseline)"
  checkpointing_enabled:
    type: boolean
    description: "False for baseline, True for intervention (middleware)"
  signing_enabled:
    type: boolean
    description: "False for baseline, True for intervention (middleware)"
```

## Data Flow

1.  **Generation**: `run_simulation.py` generates `MetricRecord` objects for each episode.
2.  **Aggregation**: `stats_analyzer.py` reads CSVs, computes paired differences, and runs statistical tests.
3.  **Storage**:
    -   Raw logs: `data/raw/episode_{seed}_{task}_{protocol}.csv`
    -   Aggregated results: `data/processed/metrics_summary.csv`
    -   Statistical output: `data/processed/stats_results.json`

## Constraints
-   All timestamps must be monotonically increasing within an episode.
-   `bytes_sent` must be normalized by payload size to ensure comparability across tasks.
-   `recovery_latency` is only recorded if `recovery_success` is true.