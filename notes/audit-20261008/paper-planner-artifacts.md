# Paper planner uses the active feature and shared artifact guards

The fresh canary's initial paper-plan reply used markers such as
`specs/002-finite-range-residue-imbalance-eulers-totient-paper/plan.md`.
The paper writer joined those directly to `paper/specs/001-paper`, creating an
unintended nested feature while the canonical plan still contained a template.
Its later review cycle repaired the canonical plan; that recovery does not make
the initial write correct. The paper setup script also lacked the active-feature
override already used in research planning and could overwrite an existing plan.

The paper planner now reuses the research planner's complete-set validation,
confined writes, YAML/content guards, rollback and bounded corrective retry.
Paper-specific prompts, full claim checking and the paper review panel remain.
Setup uses the stored feature, preserves existing documents, and supplies them
as revision inputs. Malformed prefixed markers require a corrected model reply;
the platform does not silently reinterpret scientific paths or accept a template.

Eight new regressions fail on the preceding implementation and pass with this
change. They cover real shell setup under missing/stale/ambiguous feature metadata,
prior-file preservation, nested and escaping paths, malformed YAML and successful
corrective retry before the paper panel. The related planner, paper panel,
feature-resolution and revision tests pass: 106 tests. Ruff and diff checks pass.
A real corrective replay of the captured malformed response is in progress in a
separate copy. It tests the emission boundary only, with the review panel outside
that replay; full paper acceptance remains a separate running canary.
