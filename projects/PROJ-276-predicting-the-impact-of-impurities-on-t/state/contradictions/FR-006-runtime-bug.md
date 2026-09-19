# Contradiction Report: FR-006 vs Constitution Principle VII

## Summary
A critical contradiction exists between the Feature Requirement FR-006 and Constitution Principle VII regarding runtime execution limits.

## Conflicting Requirements

### FR-006: Runtime Execution Requirement
- **Specification**: The system must support long-running ingestion and modeling pipelines that may take up to **6 hours** to complete.
- **Context**: Complex data ingestion from multiple sources (Materials Project API, SuperCon dataset) and extensive model training with hyperparameter tuning may require extended execution time.

### Constitution Principle VII: Execution Time Limit
- **Specification**: All automated research pipeline tasks must complete within **30 minutes** to ensure rapid iteration and prevent resource exhaustion.
- **Context**: This principle is designed to maintain CI/CD efficiency and prevent runaway processes in automated environments.

## Impact Analysis

1. **Immediate Conflict**: FR-006 explicitly requires 6-hour capability, while Principle VII enforces a 30-minute hard limit.
2. **Execution Risk**: Tasks attempting to run for >30 minutes will be terminated by the Constitution enforcement mechanism.
3. **Design Implication**: The pipeline architecture must be redesigned to operate within 30-minute windows, potentially through:
 - Chunked processing with state persistence
 - Asynchronous job queuing with external orchestration
 - Simplified model configurations that meet the time budget

## Resolution Strategy

**Decision**: Constitution Principle VII takes precedence as a foundational constraint. FR-006 must be revised to align with the 30-minute limit.

### Enforcement Mechanism
All subsequent tasks MUST implement a configurable runtime watchdog:
- Default limit: 30 minutes (1800 seconds)
- Configurable via environment variable `PIPELINE_TIMEOUT_SECONDS`
- Hard abort with clear error message if exceeded
- Graceful checkpointing before timeout (if applicable)

### Implementation Requirements
1. Add timeout guards to all long-running scripts (ingestion, modeling, validation)
2. Implement state persistence for resumable operations
3. Document timeout behavior in all user-facing documentation
4. Update FR-006 to reflect the 30-minute constraint

## Action Items

- [ ] Update FR-006 to specify 30-minute maximum runtime
- [ ] Implement `TimeoutGuard` in all pipeline components
- [ ] Add checkpointing mechanism for long-running tasks
- [ ] Verify all existing scripts respect the timeout limit
- [ ] Update `quickstart.md` with timeout expectations

## Verification

This contradiction is now documented. All future implementation tasks must:
1. Respect the 30-minute execution limit
2. Include explicit timeout handling
3. Fail loudly if the limit is approached or exceeded

**Status**: Documented | **Priority**: CRITICAL | **Next Action**: Implement timeout enforcement in all pipeline scripts