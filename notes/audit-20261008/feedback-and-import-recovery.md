# Verifier feedback and execution import recovery

The live canary exposed two platform defects after its sieve and total-variation
libraries passed independent numerical checks.

1. `run_verification_pass` rewrote rejection notes using only the latest batch.
   Accepting a different task erased the unfinished task's diagnosis, although its
   rejection count remained. Notes now retain outstanding diagnoses across batches,
   deferred retries and escalation. A task-definition signature retires obsolete
   feedback and counts when replanning reuses a task ID; volatile claim/HTML
   annotations do not reset its count. Accepted work and removed tasks clear their
   own notes. Legacy unbound counts restart once because their task definition
   cannot be established safely.
2. At 02:02 UTC on 2026-10-09, generated `code/src/totient_tv.py` failed with
   `ModuleNotFoundError: No module named 'src.utils.sieve'`. An empty root `src`
   scaffold shadowed the implemented `code/src` package. Research PYTHONPATH now
   prefers source workspaces before the project root; the script's own directory
   retains Python's normal first priority. No generated research code was edited.

Validation: all five initial new regression cases fail against the pre-fix source
(snapshot 75beacbdf87), including a real subprocess package collision. The repaired
source passes 72 related verifier, pipeline, implementation and sandbox tests.
An additional regression checks re-review when an accepted ID changes requirements.
This is platform verification, not evidence of full research/paper acceptance.
