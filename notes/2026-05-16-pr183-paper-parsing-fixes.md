# PR #183: Paper parsing leaks + workflow reliability fixes — 2026-05-16

## Five bugs found via audit of latest papers + activity log

| Bug | Symptom | Root cause | Fix |
|-|-|-|-|
| 1 | `oticestring` above PROJ-578 title | `\providecommand{\@noticestring}` parses wrong with `@` non-letter | Wrap forwarded macros in `\makeatletter`/`\makeatother` |
| 2 | `nedot.` above PROJ-580 title | Same — `\@onedot` from CVPR style | Same wrapper fix |
| 3 | `[? ? ? ? ?]` citations in PROJ-576 | Source ships `main.bbl` but no `main.bib` | Copy source `.bbl` → `{stem}.bbl` next to wrapper |
| 4 | Submission Intake 75% failure rate | Failed `git pull --rebase` left worktree mid-rebase | Adopted paper-compile.yml stash-pull-regenerate pattern |
| 5 | Brainstorm/Flesh-Out cancelled at 25-min timeout | arXiv 429 × 105s backoff × N queries | Circuit breaker: 2nd 429 disables arXiv for 60s |

Bonus fix: `test_personality_tick.py::test_target_missing_holds_pointer` was failing on main because rubric gate ran before target-existence check; coerced `target_missing` to `abstained`. Moved target check before rubric.

Bonus fix #2: `compile_paper.py::_restyle_if_needed` reused old wrappers even after `extract_paper_content.py` was updated. PROJ-571 reproduced the exact `nedot.` leak my fix was supposed to eliminate, because its wrapper was generated before my fix and never regenerated. Added wrapper-staleness check (wrapper.mtime < script.mtime → regenerate).

## Files changed
- `.github/workflows/submission-intake.yml` — rebase loop pattern
- `scripts/compile_paper.py` — staleness check + `_install_precompiled_bbl` helper
- `scripts/extract_paper_content.py` — `\makeatletter` wrap on forwarded macros
- `src/llmxive/agents/personality.py` — early target-exists check
- `src/llmxive/librarian/search.py` — arXiv circuit breaker
- `tests/unit/test_arxiv_circuit_breaker.py` — NEW (3 tests)
- `tests/unit/test_compile_paper.py` — TestInstallPrecompiledBbl + TestRestyleStaleness
- `tests/unit/test_extract_paper_content.py` — TestBuildWrapperMakeAtLetterGuard + at-internal-macros test
- 11 papers' regenerated PDFs + wrappers: PROJ-565, 566, 569, 571, 572, 573, 576, 577, 578, 580, 581

## Tests
- 10 new unit tests added — all pass
- Full unit suite: 384 pass in 8m51s
- Integration suite passes including previously-failing personality_tick

## CI / merge
- Branch: `fix-intake-and-paper-leaks`
- PR: https://github.com/ContextLab/llmXive/pull/183
- Awaiting `real-call` check (slow Dartmouth API call); other 4 checks pass

## Known follow-ups (not in this PR)
- PROJ-574, 575 cannot be recompiled — no arxiv_id in metadata. Pre-existing issue.
- PROJ-567 (AnyFlow) pre-existing compile failure (flagged earlier).
- The `++` glyph rendering in PROJ-580 title looks different locally vs CI — likely font fallback divergence on macOS vs Linux tlmgr. Not blocking.
