# Functional Requirements

FR-001: System must handle datasets >7GB using chunked processing.
FR-002: System must support both Fixed Effects and Random Effects models.
FR-003: REML must be used for k < 10; DL for k >= 10.
FR-004: System must log every subsample iteration (ID, k, seed).
FR-005: System must detect zero-variance studies and handle gracefully.
FR-006: GAM is the primary method for threshold detection.
FR-007: Nominal coverage target must be configurable (default 0.95).
FR-008: Sensitivity analysis must perturb reference values by their SE.
FR-009: System must output diagnostic plots for stability and coverage.

# Non-Functional Requirements

NF-001: All random operations must be seed-deterministic.
NF-002: Code must pass Ruff linting and Black formatting.
NF-003: Execution time for full bootstrap analysis must be < 6 hours on 2 CPU cores.
NF-004: No PII data may be stored in logs or outputs.
