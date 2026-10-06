# Contradiction Report: FR-006 Runtime Limit vs. Constitution

## Issue Description
The original specification (FR-006) contained a runtime duration that conflicted with the project Constitution's maximum allowed execution time.

## Contradiction Details

```json
{
 "original_spec_value": "Unspecified or excessive duration",
 "constitution_value": "30 mins",
 "resolution": "Enforce 30 mins per Constitution",
 "rationale": "Constitution Principle VII mandates a strict 30-minute runtime limit for all automated pipeline tasks to ensure reproducibility and resource efficiency. The original spec value was either missing or exceeded this threshold, creating a critical compliance risk. Enforcing the 30-minute limit ensures the pipeline remains within the operational budget of the CI/CD environment and prevents resource exhaustion."
}
```

## Resolution Strategy
1. All pipeline scripts (ingestion, modeling, validation) must implement a watchdog mechanism (e.g., `signal` module or `timeout` wrapper).
2. Scripts exceeding 30 minutes must terminate with a non-zero exit code and a clear error message.
3. Future task definitions must explicitly state this constraint.

## Status
RESOLVED - Constitution enforced.