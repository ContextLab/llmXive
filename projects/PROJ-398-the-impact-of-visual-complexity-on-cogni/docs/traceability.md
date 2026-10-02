# Infrastructure Traceability Matrix

This document maps the infrastructure tasks (Phase 1) to the Functional Requirements (FRs) defined in the project specification.
It ensures that every technical implementation step directly supports a stated research or system requirement.

## Legend

- **Task ID**: The specific implementation task identifier.
- **Functional Requirement**: The requirement code (e.g., FR-001) and a brief description.
- **Mapping**: Indicates which tasks satisfy which requirements.

## Functional Requirements Reference

- **FR-001 (Data Integrity)**: The system must load data from verified local archives without fabricating data or using synthetic placeholders.
- **FR-002 (Reproducibility)**: The system must enforce a global random seed across all stochastic processes (YOLO, statsmodels, numpy).
- **FR-003 (Schema Compliance)**: All data artifacts must conform to defined schemas (e.g., `BackgroundFrame`).
- **FR-004 (CPU Compatibility)**: The pipeline must run exclusively on CPU-compatible environments (no GPU dependency).
- **FR-005 (Auditability)**: The system must maintain logs of configuration, validation, and execution states.

## Traceability Matrix

| Infrastructure Task | Description | Satisfied Requirements | Justification |
|:--- |:--- |:--- |:--- |
| **T001a** | Create code directory structure (`src/lib/`, `src/metrics/`, `src/experiment/`, `src/analysis/`, `tests/`) | FR-005, FR-002 | Establishes the modular structure required for auditability and separation of concerns, ensuring code is organized for reproducibility verification. |
| **T001b** | Create data directory structure (`data/stimuli/`, `data/processed/`, `data/measurements/`, `data/raw/`) | FR-001, FR-005 | Defines the physical storage locations for raw archives and processed metrics, enforcing the "load from local archive" constraint of FR-001. |
| **T003** | Configure linting (ruff) and formatting (black) tools | FR-005 | Ensures code quality and consistency, a prerequisite for maintaining a reproducible and auditable codebase. |
| **T004** | Implement `src/lib/utils.py` (`set_global_seed`, checksums) | FR-002, FR-001 | `set_global_seed` enforces reproducibility (FR-002). Checksum utilities enable data integrity verification (FR-001). |
| **T005** | Implement `src/lib/data_loader.py` (local archive loading) | FR-001 | Directly implements the mechanism to load from verified local archives, preventing synthetic data fabrication. |
| **T006** | Add `src/config.py` (global seed, path definitions) | FR-002, FR-001, FR-004 | Centralizes the random seed (FR-002) and path definitions (FR-001), ensuring consistent environment configuration. |
| **T007** | Add `src/lib/schema_validator.py` | FR-003 | Provides the utility to validate data against defined schemas (e.g., `BackgroundFrame`), ensuring data integrity. |

## Verification

The existence and content of this document are verified by:
- `tests/test_traceability.py::test_infrastructure_traceability`

This test asserts that `docs/traceability.md` exists, is non-empty, and contains references to the required infrastructure tasks (T001a, T001b, T003, T004, T005, T006, T007) and functional requirements.
