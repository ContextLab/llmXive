# Preserve task requirements through claim verification

At 03:24 UTC the canary verifier rejected T004 because a sieve library did not
also implement the whole study's CLI, outputs and validation mode. Its task text
had been replaced by `{{claim:c_0e451899}}`. The claim store retained the original
instruction to implement a sieve, return a uint64 phi array and record runtime;
the resolver's value retained only a statement about algorithmic complexity.
Every implementation write was subjecting the entire task document to full
empirical-claim extraction and substitution.

Task documents are now treated as executable requirements. Citation validation
still runs at the artifact-write boundary, but claim extraction cannot rewrite
their parameters or replace instructions with factual-value pointers. Legacy
pointers are restored from their exact original spans in the same artifact's
project claim store, preserving task IDs and statuses. A missing/wrong-artifact
span fails closed and is routed for requirement repair. Implementers and the
independent verifier read the same restored instructions. The verifier prompt
also distinguishes completion of one task from final acceptance of the study.
Research results and manuscripts still enter full claim verification.

Validation: 53 focused pointer/verifier tests and 81 broader claim-pipeline tests
pass (7 existing skips). Tests confirm verbatim parameters, recovery of the full
original instruction rather than a shorter factual value, refusal of unrelated
claim records, and continued full extraction for research results. The live
canary was stopped to deploy this specific correctness fix; its scientific code,
results and statuses were not manually edited.

The next live run exposed nested historical pointers; recovery now recursively expands the original stored spans with cycle/depth protection (8 focused tests). It also showed task revision running claim extraction on unchanged specification/plan context. Research and paper task revisers now apply revision guards only to their writable task document, then restore the unchanged context; 19 requirement/reviser tests pass.
