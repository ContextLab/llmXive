# Spec Contradiction: FR-006 vs Constitution Principle VII

## Issue Summary
A critical contradiction exists between the functional requirement **FR-006** and **Constitution Principle VII** regarding pipeline execution time limits.

## Conflicting Requirements

### FR-006 (Functional Requirement)
- **Description**: The pipeline must be capable of running a full end-to-end execution (ingestion, modeling, validation, visualization) within **6 hours**.
- **Context**: This requirement was likely derived from standard CI/CD timeout thresholds for large-scale data processing tasks.

### Constitution Principle VII
- **Description**: All automated scientific pipelines must complete within **30 minutes** to ensure rapid iteration and prevent resource hogging on shared infrastructure.
- **Context**: This principle enforces strict efficiency and rapid feedback loops for the research team.

## Conflict Analysis
- **Discrepancy**: 6 hours (360 minutes) vs 30 minutes.
- **Magnitude**: A 12x difference in allowed runtime.
- **Impact**: Implementing FR-006 as written would violate Constitution Principle VII, causing the pipeline to fail compliance checks and potentially exhaust shared compute resources.

## Resolution & Enforcement Strategy
To resolve this contradiction, the following enforcement strategy is adopted for all subsequent tasks:

1. **Hard Runtime Limit**: The **30-minute limit** (Constitution Principle VII) takes precedence. All scripts must be designed to complete within this window.
2. **Watchdog Implementation**: All long-running processes (specifically model training in `src/modeling/train.py` and data ingestion in `src/ingestion/`) must implement a runtime watchdog.
 - If a process exceeds 25 minutes (leaving a 5-minute safety margin for I/O and reporting), it must abort gracefully with a clear error code.
3. **Optimization Requirement**: Any task that cannot meet the 30-minute limit must be re-scoped, optimized, or split into smaller parallelizable sub-tasks.
4. **Documentation**: All subsequent tasks must explicitly note the 30-minute constraint in their implementation notes.

## Action Items for Implementation
- [x] Document this contradiction (This file).
- [ ] Enforce 30-minute timeout in `src/modeling/train.py` (Task T019).
- [ ] Enforce 30-minute timeout in `src/ingestion/download_materials_project.py` and `download_supercon.py`.
- [ ] Update `quickstart.md` to reflect the 30-minute execution target.

## Status
**RESOLVED**: Constitution Principle VII is the governing constraint. FR-006 is effectively superseded by the stricter 30-minute limit.