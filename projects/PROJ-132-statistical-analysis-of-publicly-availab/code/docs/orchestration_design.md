# Orchestration Design (T045)

## Purpose
Implement a file-based lock mechanism to serialize the execution of T025 and T032,
preventing concurrent execution of heavy permutation tests that could exceed CI
runtime limits (SC-005).

## Mechanism
- **Lock File**: `state/pipeline.lock`
- **Acquisition**: Uses `fcntl.flock` for cross-platform file locking.
- **Timeout**: 300 seconds (5 minutes) to prevent indefinite blocking.
- **Intervals**: Checks lock status every 1 second.

## Execution Flow
1. T025 starts, attempts to acquire lock.
2. If successful, runs permutation test.
3. Releases lock upon completion (success or failure).
4. T032 starts, attempts to acquire lock.
5. If successful, runs trajectory permutation test.
6. Releases lock.

## Error Handling
- **Timeout**: If lock not acquired within 300s, task aborts with error.
- **Crash Recovery**: File-based locks are automatically released if the process
 terminates unexpectedly (OS handles flock release).

## Logging
- All lock events (acquire, release, timeout, error) are logged to `logs/pipeline.log`.
- Log format includes timestamp, task name, and event details.

## Testing
- Unit tests in `tests/unit/test_orchestration.py` verify:
 - Successful acquisition
 - Blocking behavior
 - Timeout logic
 - Concurrent execution serialization
- Integration tests verify end-to-end flow in pipeline runners.