# Quickstart: Phase 3 Validation

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-05-17

This guide takes a maintainer from "I have the repo checked out" to "I have a Phase 3 validation result on disk" in ≤ 5 minutes (excluding LLM wall-clock).

---

## 0. Prerequisites

| Requirement | How to check |
|-|-|
| Python 3.11 | `python --version` |
| `DARTMOUTH_CHAT_API_KEY` env var set | `echo $DARTMOUTH_CHAT_API_KEY \| head -c 4` (don't print full key) |
| Clean `git status` | `git status -s` reports no changes under `projects/PROJ-261-*` or `projects/PROJ-262-*` |
| Phase 3 reference projects at `project_initialized` | `grep current_stage state/projects/PROJ-26[12]-*.yaml` |

If any prerequisite fails, see the troubleshooting section at the end.

---

## 1. Smoke-test one canonical (~ 2 minutes)

Run Phase 3 on the smaller canonical (PROJ-261 — code duplication, Computer Science):

```bash
python scripts/validate_phase3.py --project PROJ-261-evaluating-the-impact-of-code-duplicatio
```

Expected output (on stderr):

```
[validate_phase3] preflight ok (7/7 checks)
[validate_phase3] PROJ-261-…: reset 0 pre-existing spec dir(s)
[validate_phase3] PROJ-261-…: invoking specifier (max-tasks=1)…
[validate_phase3] PROJ-261-…: specifier committed in 47.3s (5 FRs, 3 SCs, 2 stories, 1 marker)
[validate_phase3] PROJ-261-…: inspection → specs/011-…/inspections/PROJ-261-…/specifier.json
[validate_phase3] PROJ-261-…: invoking clarifier (max-tasks=1)…
[validate_phase3] PROJ-261-…: clarifier committed in 31.5s (1/1 markers resolved)
[validate_phase3] PROJ-261-…: inspection → specs/011-…/inspections/PROJ-261-…/clarifier.json
[validate_phase3] PROJ-261-…: final stage clarified
[validate_phase3] PROJ-261-…: post-conditions PASS (5 FRs ≥ 4, 3 SCs ≥ 3, 2 stories ≥ 2, 0 markers, run-log entries 2/2)
[validate_phase3] validated 1 project(s): 1 passed, 0 failed
```

Exit code: `0`.

---

## 2. Inspect what just happened

```bash
# Open the Specifier inspection record
$EDITOR specs/011-phase3-specify-clarify-testing/inspections/PROJ-261-evaluating-the-impact-of-code-duplicatio/specifier.json

# Sanity-check the produced spec
$EDITOR projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/specs/001-evaluating-the-impact-of-code-duplicatio/spec.md

# Confirm state advanced
grep current_stage state/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio.yaml
# → current_stage: clarified
```

You should be able to read the Specifier's inspection record top-to-bottom and reconstruct: (a) what prompt was sent, (b) what the LLM returned, (c) what the agent parsed it as, (d) what files were written.

---

## 3. Run the full validation (~ 4 minutes)

```bash
python scripts/validate_phase3.py --all
```

This processes both PROJ-261 and PROJ-262 sequentially, writes 4 inspection records (2 per project × 2 agents), and emits the carry-forward manifest.

Final artifact: `specs/011-phase3-specify-clarify-testing/carry-forward.yaml` with both canonicals listed as `final_state: clarified`.

---

## 4. Run the regression test suite (~ 5 seconds — no backend calls)

```bash
python -m pytest tests/integration/test_phase3_specify_clarify.py -v -k "not end_to_end"
```

This runs the 3 fast regression tests (diff-leak guard, template-only guard, echo-the-question guard) and SKIPS the real-call end-to-end test (which requires the backend key — already exercised above).

Expected: `3 passed in <1s` (or however long the guards take to execute on synthetic input).

---

## 5. Author the diagnostic report

```bash
$EDITOR notes/2026-05-17-spec-011-phase3-diagnostic.md
```

Use the structure documented in `contracts/diagnostic-report.md`. Fill in:
- The TL;DR (1–3 sentences)
- Per-project summary (PROJ-261 + PROJ-262)
- Guards-fired table (typically all "No" on a clean run)
- Recommendations (typically "None — both agents behaved per spec")
- Sign-off row

Then commit:

```bash
git add specs/011-phase3-specify-clarify-testing/ notes/2026-05-17-spec-011-phase3-diagnostic.md \
        projects/PROJ-26[12]-*/specs/ state/projects/PROJ-26[12]-*.yaml \
        state/run-log/ src/llmxive/speckit/_inspection.py scripts/validate_phase3.py \
        tests/integration/test_phase3_specify_clarify.py
git commit -m "spec(011): Phase 3 validation — PROJ-261 + PROJ-262 reach clarified"
```

---

## Troubleshooting

**Preflight check 1 fails (`DARTMOUTH_CHAT_API_KEY` missing)**: Source the maintainer's credentials file (typically `~/.config/llmxive/credentials.toml`) into the shell. The harness exits 2 — no state changes are made.

**Preflight check 3 fails (project not at `project_initialized`)**: The canonical has already been Phase 3'd by an earlier run. Either choose a different canonical or manually roll back `state/projects/<id>.yaml::current_stage` to `project_initialized` AND delete `projects/<id>/specs/<n>-<slug>/` (or use `python scripts/validate_phase3.py --no-reset` if you specifically want to resume a partial run — at your own risk).

**Specifier produces > 3 `[NEEDS CLARIFICATION]` markers**: The specifier prompt caps at 3 per the speckit-specify skill. If you see > 3, that's a real bug — file an issue + fix the agent prompt; the inspection record at `specs/011-…/inspections/<id>/specifier.json` will show exactly what was sent + returned.

**Clarifier outcome is `failed` with "echo-the-question" rejection**: The LLM tried to fake a resolution. Re-run the validation — Clarifier's prompt has stochastic resolution and a re-run usually succeeds. If it fails twice in a row, the prompt may need strengthening; the failed inspection record names exactly which marker was echoed.

**Wall-clock exceeds 600s for one agent**: The agent timed out per FR-014. The outcome is `failed`, not `committed`. Check the inspection record's `error` field — usually a backend-side stall. Re-run after a few minutes.

**Carry-forward manifest missing**: Only written by `--all` or `--emit-carry-forward`. A `--project <id>` run does NOT emit it by default (it would clobber the manifest with only-one-project data).
