# Specification: Exploring the Role of Network Structure in Superconducting Qubit Coupling

## Overview

This project investigates the correlation between topological properties of superconducting qubit coupling maps (e.g., average shortest path length, clustering coefficient) and device performance metrics (e.g., coherence times, gate errors). The study utilizes real-time calibration data from IBM Quantum backends.

## User Stories

### US1: Retrieve and Parse IBM Quantum Calibration Data
- **Goal**: Fetch latest calibration data for all accessible backends.
- **Acceptance Criteria**:
 - Data is fetched within 30 days of execution.
 - Topology (coupling map) and performance metrics are extracted.
 - Invalid or stale data is excluded with logging.

### US2: Construct Connectivity Graphs and Compute Topological Metrics
- **Goal**: Convert coupling maps to graphs and compute metrics.
- **Acceptance Criteria**:
 - Graphs are undirected.
 - Metrics include shortest path, clustering, betweenness, spectral gap.
 - Disconnected graphs are handled gracefully.

### US3: Execute Statistical Correlation and Robustness Analysis
- **Goal**: Correlate topology with performance.
- **Acceptance Criteria**:
 - Spearman rank correlation is computed.
 - FDR correction is applied.
 - Robustness checks (LODO, Time Window) are performed.

## Functional Requirements

### FR-001: Data Freshness
Devices with calibration data older than 30 days must be excluded from analysis.

### FR-002: Metric Extraction
The system must extract T1, T2, gate errors, readout errors, and coupling maps.

### FR-003: Cross-Sectional Analysis (UPDATED)
**Original Requirement**: The study would correlate topology derived from a historical time window with performance metrics.
**Resolution**: The requirement for a "historical time window" for topology is hereby **RETRACTED**.
**Revised Requirement**: The study shall operate as a **cross-sectional analysis**. Topology and performance metrics are extracted from the *same* calibration snapshot (simultaneous data). The "historical time window" constraint (SC-004) is interpreted as a robustness check mechanism (see FR-004) rather than a primary data ingestion window for topology.
**Rationale**: Network topology (coupling map) for a specific device is generally static or changes infrequently compared to performance metrics (T1/T2, errors) which fluctuate daily. Creating a "time window" of topologies that do not significantly differ from the current state adds unnecessary complexity and potential data alignment errors without scientific benefit. The primary hypothesis relies on the instantaneous correlation between the device's physical connectivity and its current performance.

### FR-004: Robustness Checks
- **LODO**: Leave-One-Device-Out analysis to ensure stability.
- **Time Window**: Performance metrics from a fixed 30-day historical window shall be compared against the full dataset to verify correlation stability (satisfying SC-004).

## Data Model

- **QubitDevice**: Represents a backend with `device_id`, `timestamp`, `coupling_map`, `properties`.
- **GraphMetric**: Stores `device_id`, `metric_name`, `value`.
- **PerformanceMetric**: Stores `device_id`, `metric_name`, `value`.
- **CorrelationResult**: Stores `metric_a`, `metric_b`, `rho`, `p_value`, `adj_p_value`.

## Non-Functional Requirements

- **NFR-001**: All code must be Python 3.11+.
- **NFR-002**: No synthetic data generation; all data from IBM Quantum API.
- **NFR-003**: CPU-only execution constraints.
- **NFR-004**: Reproducibility via `state/projects/PROJ-163-...yaml` artifact hashes.

## Constraints

- **C-001**: API rate limits must be respected with exponential backoff.
- **C-002**: Disconnected graphs must result in a spectral gap of 0.