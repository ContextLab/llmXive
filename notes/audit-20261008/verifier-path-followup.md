# Live verifier evidence-path failure

After deploying #1472 (`c1d3eac`), the isolated totient canary generated
`code/src/utils/sieve.py`, but its task named the repository-rooted path
`projects/PROJ-9999-totient-canary/code/src/utils/sieve.py`. The verifier's
path detector returned no files. Independent review consequently rejected the
task for missing evidence, and repeated false rejections triggered replanning.
Other tasks used `src/...` relative to `code/`, which the verifier searched at
the project root instead. The run was stopped before this follow-up.

The production PROJ-591 pilot, run 37859267351, independently exposed another
case: T001 was rejected because directory-only scaffolding had no evidence
payload. That run persisted commit `ff06064c8ebb7beb6173c360639465b5bc9227bf`,
but stopped without a stage change or verified task completion. Its execution
feedback contains real missing scripts, an import mismatch, an undefined `Any`,
and a missing matplotlib dependency. Workflow success is not project success.

The follow-up resolves same-project repository paths, code-relative source/test
and config paths, directory listings, and nonexistent spec aliases that the
implementer already canonicalizes on write. Existing explicit paths retain
precedence. Cross-project references, traversal, and escaping symlinks cannot
supply evidence. Evidence displays the resolved file and hashes its contents;
directory evidence hashes the complete immediate listing. Overlapping path
matches no longer consume extra evidence slots.

The implementer's existing-file context had the same code-relative path bug.
Both components now use `project_paths.py`, so repair prompts receive the same
existing source that verification examines. Directory listings do not consume
the file-content slots, keeping a setup task's dependency manifest visible.
The canary's analysis driver is 12,742 characters: the old 6,000-character
implementation context ceiling omitted it entirely. Raise the bounded allowance
to 48,000 characters, and explicitly tell the model not to replace an omitted
file blindly instead of implying it has a disk-reading tool.

Validation: 134 focused verifier, preview, and implementer tests passed; the
earlier 41 verifier integration and execution tests passed; changed-file Ruff
passed. A regression exercises the
verification pass with real nested files and confirms the independent reviewer
receives the source and can reject incorrect scientific behavior. Separate
tests cover canonical feature paths, scaffolding, cache-input changes, and
project confinement. The full canary was resumed with this follow-up source;
it was stopped during follow-up development to load the context corrections;
research and paper acceptance remain unproven.

The next live verification pass accepted setup, sieve, and TV helper tasks.
An independent GCD check for n=1..500 found no mismatch, and the generated
sieve/TV libraries matched all 12 reference combinations through N=1,000,000
(sieve: 0.285 seconds; comparison evidence in `canary-math-library-check.json`).
The generated sieve and TV tests pass (19 tests, with pytest's importlib mode).
These are read-only checks of generated library code, not pipeline-generated
result tables or paper acceptance. No research code was corrected manually.

The pass also exposed a remaining resolver edge case: setup had created an
invented spec slug containing only `contracts/`. That scaffold prevented the
missing-file fallback even though the implementer had written the document in
the canonical feature. Distinguish real features by `spec.md`, keeping existing
files authoritative while resolving scaffold-only aliases. The live quickstart
and data-model references now both resolve to real canonical files; the 134
targeted tests still pass. Execution also identified malformed doubled shell
continuations and a module-path mismatch in the generated run-book; these
remain implementation work rather than accepted scientific outputs.

The production repair workflow (37859264827) completed with `no_candidate`:
the selected umbrella issues described merged fixes and pending acceptance,
without a concrete reproducible source defect. It did not publish a PR. This
is correct abstention, not evidence that automated production repair succeeded.
