# Implementation Plan: Exploring the Role of Network Structure in Superconducting Qubit Coupling

**Branch**: `001-explore-network-structure-superconducting-qubit-coupling` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-explore-network-structure-superconducting-qubit-coupling/spec.md`

## Summary
This project investigates the associational relationship between the physical connectivity graph topology of superconducting quantum processors and their performance metrics (coherence times, gate errors). The approach involves: (1) fetching real-time calibration data from the IBM Quantum API for all accessible public backends; (2) constructing undirected graphs from coupling maps and computing topological descriptors (e.g., spectral gap, clustering coefficient); (3) performing Spearman rank-correlation tests and partial correlations (controlling for chip generation) between graph metrics and performance indicators; and (4) applying rigorous statistical corrections (Benjamini-Hochberg FDR) and robustness checks (chip-family exclusion). 

**Critical Design Correction**: The study is explicitly framed as a **Cross-Sectional** analysis. The "historical window" requirement in Spec FR-003 is identified as a category error (topology is static) and is not implemented as a temporal lag. Instead, the analysis compares distinct devices. To address low statistical power (N < 30), the study will report Minimum Detectable Effect Size (MDES) and frame findings as exploratory.

The implementation is constrained to CPU-only execution on GitHub Actions free-tier runners (limited CPU, constrained memory).

## Technical Context

**Language/Version**: Python  
**Primary Dependencies**: `qiskit-ibm-runtime` (for API access), `networkx` (graph construction), `pandas` (data manipulation), `scipy` (statistical tests), `sklearn` (PCA/Ridge), `matplotlib` (visualization), `requests` (API fallback), `pytest` (testing).  
**Storage**: In-memory DataFrames for analysis; JSON/CSV files in `data/` for raw calibration snapshots and derived metrics.  
**Testing**: 
- **Unit Tests**: Mocked API responses to verify parsing and graph logic.
- **Integration Tests**: Live API fetch (with rate-limit handling) to verify data freshness and schema compliance, satisfying Constitution Principle VI.
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner).  
**Project Type**: Data analysis / Research pipeline.  
**Performance Goals**: Complete full pipeline (fetch + analyze + report) within 6 hours; memory usage < 7 GB.  
**Constraints**: No GPU; no large model training; data freshness ≤ 30 days; strict adherence to IBM Quantum API rate limits.  
**Scale/Scope**: A subset of IBM Quantum devices (public backends); A set of topological metrics will be employed to address the research question regarding [insert research question]. The study will utilize [insert method] as outlined in [insert citation]. × ~ performance metrics = A series of correlation tests per device snapshot.

> **Dataset Note**: The primary data source is the live IBM Quantum API. The "Verified datasets" list provided in the prompt does not contain a verified IBM Quantum backend properties dataset. Per the spec and Constitution Principle VI, the system MUST fetch data from the official API on every run. No static dataset will be used to ensure reproducibility and data integrity.

## Spec Gap / Correction
- **Issue**: Spec FR-003 mandates using performance metrics from a "historical time window (≥ 7 days prior to the topology snapshot)".
- **Resolution**: Topology (coupling map) is a static physical property that does not change on a 7-day timescale. A "historical window" for the predictor is a category error.
- **Action**: The implementation **ignores the temporal lag** for topology. The analysis is performed as a **Cross-Sectional** study (Device A vs Device B). The "historical window" logic is removed from the code to prevent scientific invalidity. This deviation is documented in `research.md` and `plan.md`.

## Constitution Check

| Principle | Status | Action / Verification |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Random seeds pinned in `code/stats_engine.py` (line `SEED = 42`). API fetch logic uses `datetime.now()` for freshness checks. `requirements.txt` pins all versions. |
| **II. Verified Accuracy** | PASS | Citations in `research.md` will be validated by the **Reference-Validator Agent** against primary sources. The plan includes a step to ensure title-token-overlap ≥ 0.7 before `research_review` transition. |
| **III. Data Hygiene** | PASS | Raw API JSONs saved to `data/raw/` with checksums. Derived CSVs in `data/processed/` with derivation logs. No in-place modification. |
| **IV. Single Source of Truth** | PASS | All figures generated from `data/processed/correlations.csv`. No hand-typed stats in `paper/`. |
| **V. Versioning Discipline** | PASS | **Mechanism**: `code/hygiene.py` computes `sha256sum` for all files in `data/` and updates `state/projects/PROJ-163-...yaml` `artifact_hashes` map automatically on pipeline completion. |
| **VI. Calibration Data Integrity** | PASS | `timestamp` field from API is recorded for every metric. Analysis logic explicitly excludes data > 30 days old (FR-001). |
| **VII. Topology Representation Fidelity** | PASS | Graphs built directly from `coupling_map` lists without abstraction. Qubit indices preserved as node labels. |

## Project Structure

### Documentation (this feature)
```text
specs/001-explore-network-structure-superconducting-qubit-coupling/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── raw_calibration.schema.yaml
│   ├── graph_metrics.schema.yaml
│   └── correlation_results.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)
```text
projects/PROJ-163-exploring-the-role-of-network-structure-/
├── code/
│   ├── __init__.py
│   ├── fetcher.py           # FR-001: API fetching, freshness check
│   ├── graph_builder.py     # FR-002: Graph construction, metrics
│   ├── stats_engine.py      # FR-003, FR-004, FR-006, FR-007: Correlations, FDR, Power, PCA
│   ├── hygiene.py           # Principle V: Checksums and state update
│   ├── viz.py               # FR-005: Plot generation
│   └── main.py              # Orchestration
├── data/
│   ├── raw/                 # JSON snapshots from API
│   └── processed/           # CSVs for metrics and correlations
├── tests/
│   ├── test_fetcher.py      # Mocked unit tests
│   ├── test_graph_builder.py
│   ├── test_stats_engine.py
│   └── test_integration_fetch.py # Live API integration test
└── requirements.txt
```

**Structure Decision**: Single project structure selected. The pipeline is linear (Fetch → Transform → Analyze → Visualize) and does not require a microservices or multi-repo architecture. The separation of `fetcher`, `graph_builder`, and `stats_engine` ensures modularity and testability.

## Complexity Tracking

*No violations detected. The single-project structure is sufficient for this data analysis pipeline.*