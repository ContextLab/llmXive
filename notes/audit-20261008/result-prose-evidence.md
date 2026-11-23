# Ground result prose in signed artifact contents (2026-10-09)

The execution stage signs table/figure paths. The result resolver compared an extracted prose claim's full canonical sentence with those paths, so a correctly reported table value could never be substantiated. Scalar-only fixtures hid this production mismatch.

Keep exact receipt-value resolution, and add bounded CSV/TSV/JSON content grounding for prose. Every source requires a valid signature and matching current content hash. Reuse source-grounded entailment with a quotation actually present in the source, check all reported numbers, and revalidate the artifacts after the model returns. Missing, unsigned, changed, deleted, linked, oversized, or unsupported evidence stays unresolved. No external fill, receipt minting, or model-only acceptance is introduced.

Cached prose claims carry hashes of all supporting artifacts and invalidate on any change. Whole prose is preserved during rendering and cannot become a scalar replacement inherited by a different claim.

Successful implementation previews now mint receipts for their real outputs, labeled `implementation_preview`, before results-writing tasks need them. Failed previews mint none. This does not promote stages, accept final execution, consume final fix rounds, or alter task checkboxes.

Validation: 90 focused tests pass, including real successful/failed preview subprocesses. Three new regression cases fail with the old result resolver. A real Dartmouth GPT-OSS probe verifies the correct value, refutes an invented value and a correct value assigned to the wrong prime, and leaves an unsupported test-success claim unresolved. Exact replies/timing are in `result-prose-live.json`; this used an isolated signed fixture, not the scientific canary's acceptance state.

Entailment remains model-mediated. This establishes that a sentence accurately reports authenticated output, not that the underlying scientific method is correct. Independent scientific review remains necessary; the live canary's integer-rounded TV calculations remain unaccepted.
