# Task verification: canonical paths and valid empty package markers

The fresh 2026-10-09 canary's T001 was reopened despite its quickstart existing.
At 13:08 UTC the verifier explicitly rejected `specs/001-totient-canary/quickstart.md`
because the generated task used the invented slug
`specs/001-finite-range-residue-imbalance-eulers-totient/quickstart.md`. The shared
resolver and implementer already map this nonexistent feature alias to the active
feature. The evidence included both requested and resolved paths, but semantic
review still treated the old spelling as mandatory.

The verifier now uses the central configured free primary, GLM-5.3, instead of a
hidden GPT-OSS-120B default. Its instructions explain the evidence collector's
existing path mappings and command equivalence under an explicitly stated working
directory. Original task text and commands are preserved verbatim; no paths are
rewritten. Missing paths, separate real features, and project confinement still
use the unchanged resolver. Cache fingerprints bind task/specification/evidence,
verifier policy, and requested model, so old verdicts are reconsidered. Explicit
model overrides remain supported in verification and receipt lookup.

An intentionally empty `__init__.py` also previously failed the empty-artifact
check. Real empty package markers now proceed to semantic review; empty analysis
modules and data remain invalid. Existence alone never establishes completion.

## Real model evidence

A captured T001 replay with GPT-OSS-120B rejected the existing document in 5.77s.
A path-mapping instruction alone still failed (5.71s). A diagnostic four-case
matrix tested an equivalent command, an omitted argument, a missing document, and
an empty package marker. GPT-OSS passed three and incorrectly rejected the
working-directory equivalence. GLM passed all four (106.51s). A repeat that also
asserted the actual response model was GLM-5.3 passed four of four in 131.93s.
These diagnostic matrices used a preliminary path-normalization approach that was
removed after independent review found it could change command meaning.

Crucially, the captured real T001 case also passed with GLM-5.3 using its original,
unmodified task and evidence (32.64s, actual response model checked). The final
live regression matrix tests unmodified requirements, both command-path directions,
a change-directory command, missing arguments/documents, and an empty package
marker. This is a narrow comparison, not a general model benchmark. It supports
using the configured primary while preserving every substantive requirement.

The scientific canary was not modified by these diagnostic replays. Related
offline validation includes receipt invalidation after model/policy changes and
rejection of empty substantive Python modules. Full-suite and final live results
are recorded in the pull request.

Final original-task matrix: **6 passed in 238.04s**, each response asserted to be
GLM-5.3. PRs retain canonical-command, missing-argument, and empty-marker cases;
reverse-path, change-directory, and missing-document variants run nightly. Related
offline tests: **32 passed**. Broader validation is recorded with the PR.

Full fast unit/contract/integration run: **7,913 passed, 20 skipped, 4 deselected**;
one live-tree integration audit failed because the sparse checkout omitted project
specifications. After materializing all tracked project specs, the complete audit
module passed **3 tests in 29.29s**. No product-code change or assertion weakening
was needed. Ruff and diff checks pass.
