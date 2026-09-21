# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): No code, data file, or documentation for a Tier‑2 environment generator was provided; thus there is no artifact demonstrating a graph with ≥20 nodes, branching paths, and stochastic transition probabilities as required. The task lacks the necessary implementation evidence.
- `T013` (rejected 1x): No code, data files, or generated environment artifacts for Tier 3 (or any tier) are provided; the claim cannot be verified against any concrete output. The required Tier 3 graph with 100+ nodes, sparse rewards, and high‑entropy transitions is missing.
- `T015` (rejected 1x): No code, data, or documentation showing a seed‑based deterministic graph regeneration system (using seed + code version hash, on‑the‑fly generation, and checksum validation) was provided. The evidence only contains high‑level user story descriptions, not the required implementation artifact. The task remains undone until such a module and its verification outputs are supplied.
- `T018` (rejected 1x): No code, data, or documentation artifacts were provided for the synthetic environment generator, the OPID routing‑threshold integration, or the performance measurements. Consequently, there is no evidence that the Bernoulli‑trial routing logic (p = 1 − threshold) was implemented or tested, nor that the required experiments were run. The task remains unfinished.
- `T019` (rejected 1x): declared artifact(s) missing/empty/invalid: src/agent/opid_router.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

