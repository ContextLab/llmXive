# Contradiction Report: FR-006 vs Constitution Principle VII

## Status
**CRITICAL** - Requires immediate attention before implementation proceeds.

## Contradiction Details

### FR-006 (Functional Requirement)
**Requirement**: The system must be capable of running the full data ingestion, model training, and validation pipeline within a **6-hour** execution window to support nightly batch processing and large-scale hyperparameter sweeps.

### Constitution Principle VII (System Constraint)
**Constraint**: All automated execution stages must complete within **30 minutes** to prevent resource exhaustion, ensure rapid feedback loops, and maintain CI/CD pipeline efficiency.

## Analysis

1. **Time Limit Discrepancy**: FR-006 specifies a 6-hour limit, while Principle VII enforces a strict 30-minute limit.
2. **Conflict Impact**:
 - A 6-hour run would violate the Constitution's 30-minute constraint.
 - The 30-minute constraint may be insufficient for full hyperparameter sweeps on large datasets as envisioned in FR-006.
3. **Root Cause**: FR-006 appears to be a legacy requirement or an optimistic estimate that does not account for the strict efficiency mandates of the project Constitution.

## Resolution Strategy

**Decision**: The Constitution Principle VII takes precedence. The 30-minute limit is the hard ceiling for all execution stages.

**Action Items for Subsequent Tasks**:
1. **Enforce Time Limits**: All data processing and model training scripts MUST implement a watchdog timer (e.g., using `signal` or `threading.Timer`) that aborts execution if the 30-minute threshold is exceeded.
2. **Optimization Requirement**: If the full pipeline cannot complete within 30 minutes on real data, the scope must be reduced (e.g., fewer hyperparameter combinations, smaller sample sizes, or simplified models) rather than extending the time limit.
3. **Documentation**: All task implementations must explicitly reference this contradiction and demonstrate adherence to the 30-minute limit.

## Implementation Evidence

The following artifacts demonstrate enforcement of the 30-minute limit:
- `src/modeling/train.py`: Implements `TimeoutGuard` and `timeout_handler` to enforce the 30-minute runtime cap.
- `src/ingestion/download_materials_project.py`: Includes rate-limiting and timeout logic to prevent indefinite hangs.
- `src/ingestion/download_supercon.py`: Includes validation logic that fails fast if data quality checks exceed time budgets.

## Recommendation

- Update FR-006 to reflect the 30-minute constraint or mark it as "Deferred" pending architectural changes (e.g., distributed computing) that could support longer runs without violating Constitution principles.
- Ensure all future task descriptions explicitly state the 30-minute runtime budget.

---
**Report Generated**: 2024-05-21
**Priority**: CRITICAL
**Owner**: System Architecture Team