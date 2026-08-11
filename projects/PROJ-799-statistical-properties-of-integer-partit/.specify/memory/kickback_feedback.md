# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004` (rejected 1x): The repository contains `code/utils/prime_sieve.py` with a correct implementation, but the required output file `code/utils/primes.npy` is missing, so the verification step (file existence, dtype `int32`, correct shape) cannot be satisfied. The implementer must run the script (or otherwise generate) to create the `.npy` file with the prime list.
- `T013` (rejected 1x): No code changes or test output were provided; there is no `generate_partitions.py` file showing added validation logic, nor any evidence (e.g., diff, unit test, or execution log) that the script now skips values of n with p_{\mathcal{P}}(n)=0 or Q_{as}(n) ≤ 0. The required artifact is missing.
- `T031` (rejected 1x): No `generate_partitions.py` file or its contents were presented, so we cannot confirm that the required comment documenting the generating function $\prod_{p\in\mathbb{P}}(1+q^p)$ (and distinguishing it from $\prod(1-q^k)^{-1}$) actually exists. The implementer must supply the code file with the explicit comment.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

