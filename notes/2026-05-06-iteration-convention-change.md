# Iteration convention change — sibling spawning retired

**Date**: 2026-05-06
**Triggered by**: spec 004 (Phase 2 testing) Phase 7 cleanup
**Affects**: spec 003 (retroactive — kept for historical reproducibility), spec 004+ (new convention)

## What changed

**Old convention (specs 003 + 004)**: each iteration of an agent spawned a new sibling project with an `-iterN` suffix (e.g., `PROJ-261-...-iter2`, `-iter3`, `-iterFAIL-backend`, etc.). Old iters were left in `projects/` with `archived_at` markers.

**New convention (spec 005+)**: iteration happens **in place** on the canonical `PROJ-NNN-<slug>/` directory. Each iteration is a separate **git commit** on the feature branch with a descriptive message; the iteration trail is browsable via `git log -- projects/PROJ-NNN-<slug>/`. No suffix-named sibling directories.

## Why it changed

The sibling pattern produced messy project trees:
- After spec 004 alone, just two canonicals had **8 sibling directories** between them (iter2, iter3, iter4, iter5, iter6 for PROJ-261; iter2, iter3, iter4, iter6 for PROJ-262), most archived.
- Each sibling carried a duplicate `state/projects/<id>.yaml`, a duplicate `.specify/` scaffold, a duplicate `idea/<slug>.md`, plus `.history.jsonl` files. ~70 files of redundant duplication just for two carry-forward projects' worth of testing.
- Spec 005 (Phase 3) and beyond would compound the proliferation: each project under test would acquire its own `-iterN` family.

The original justification was "every iteration is independently replayable from a clean state" — but git already provides this via `git checkout <commit>` on the canonical's path, with the additional benefit of structured commit messages explaining what changed.

## What's preserved

- **`tests/phase1/sibling_project.py`** is preserved as-is with a deprecation banner (so spec 003's historical reproducibility holds).
- **The Phase 1 commit history** (e5e423c, 8f2fe48, 7c5cc08, etc.) remains the audit trail for spec 004's iteration trajectory v1.0.0 → v1.1.0 → v1.2.0.
- **Spec 003 / spec 004 diagnostic reports** retain their original sibling-iter references in the prose (because that IS what happened at the time).

## What's removed

- All `projects/PROJ-261-...-iterN/` and `projects/PROJ-262-...-iterN/` directories from spec 004.
- All `state/projects/PROJ-26*-iter*.yaml` files.
- All `state/projects/PROJ-26*-iter*.history.jsonl` files.
- Run-log JSONL entries for iter siblings remain in `state/run-log/2026-05/` (they are timestamped historical evidence; deleting them would erase auditability).

## What's promoted

- **Iter6's audited constitution** for each carry-forward project is copied onto its canonical path (`projects/PROJ-NNN-<slug>/.specify/memory/constitution.md`), with the `-iter6` suffix stripped from the substituted project_id references.
- The spec 003 → spec 004 carry-forward trajectory is now: `PROJ-261-evaluating-the-impact-of-code-duplicatio` and `PROJ-262-predicting-molecular-dipole-moments-with` are the **canonical** carry-forward targets, holding the latest audited Phase 2 outputs.

## Convention going forward

For any future-phase spec (005+):

1. **Iterate in place** on the canonical project directory. Edit `idea/`, `.specify/memory/constitution.md`, `state/projects/<id>.yaml`, etc., directly.
2. **One commit per iteration**, with messages like `phaseN/spec-NNN: <agent_name> iter K — <what changed and why>`. The iteration count is in the commit message, not the directory name.
3. **Add an iteration log section to the diagnostic report** (`§ 5 — Iteration log`) summarizing each iteration's commit hash + scope + outcome. The git log is the source of truth; the report's § 5 is a curated index.
4. **Don't spawn sibling-iter projects** unless absolutely necessary (e.g., to deliberately exercise a multi-state-machine path that requires two independently-evolving projects). If you do spawn one, name it explicitly with rationale, not just `-iterN`.

## Backwards compatibility

- Spec 003 + spec 004 reports retain their sibling-iter references in prose (they describe historical state).
- The `tests/phase1/sibling_project.py` deprecation banner points future readers here.
- `tests/phase1/test_idempotency.py` doesn't depend on siblings (it uses pytest `tmp_path` fixtures); regression test still passes.
- `tests/phase1/test_citation_resolver.py` is unaffected.

## Verification

- `find projects/PROJ-26*-iter* 2>/dev/null` → empty.
- `ls state/projects/ | grep iter` → empty.
- `pytest tests/phase1/` → 15/15 passing.
- `sha256sum projects/PROJ-26{1,2}-*/.specify/memory/constitution.md` → matches the audited iter6 content (with the -iter6 suffix stripped).
