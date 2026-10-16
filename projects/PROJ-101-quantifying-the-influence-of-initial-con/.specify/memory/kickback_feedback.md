# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T006` (rejected 1x): The provided `code/simulation/generator.py` correctly implements the ODE, integration with DOP853, tolerances, and noise injection, and the shim `data/generator.py` maps most functions. However, the shim’s `integrate_trajectory` ignores the `sigma_noise` argument and never emits the `HighNoiseWarning` for σ > 0.1 nor raises `UnphysicalTrajectoryError` for σ > 1.0, causing the `test_high_noise_warning` and `test_unphysical_trajectory_error_high_sigma` tests in `tests/unit/test_generator.py` to fail. The task’s verification requires those unit tests to pass, so the implementation is incomplete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

