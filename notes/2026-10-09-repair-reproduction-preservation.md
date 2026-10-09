# Reject invalid reproductions and unsafe writer repairs

Deployed trial [37937595531](https://github.com/ContextLab/llmXive/actions/runs/37937595531)
failed without an accepted repair. Its first candidate imported a newly invented
helper inside each regression test. Those imports returned pytest exit 1,
incorrectly satisfying the baseline exit-code check without exercising an
existing caller. Its third candidate genuinely reproduced the implementation
writer's file/directory collision, but materialized invalid indentation and
would delete an existing `.bak` before moving the current file.

The runner now rejects baseline runtime ImportError/ModuleNotFoundError traces,
in addition to the existing exit-code requirement. Regressions must exercise
existing production callers. Materialized Python is compiled without execution
during proposal validation; syntax errors include exact file, line, column and
source text in the existing three-round correction loop before any sandbox run.

The separately executed fixed preservation suite now drives the observed
`ImplementerAgent.write_artifacts` caller with arbitrary binary file content,
occupied `.bak` and `.placeholder.txt` backup names, and external symlinks at
three project paths. Safe refusal remains acceptable, but all prior content and
symlinks must survive. A deliberately unsafe backup-deletion mutation is rejected
in all three regular-file cases. It is a gate probe, not an adopted or manually
repaired model candidate.

The runtime-import regressions and syntax-correction regression fail on the
previous runner. The focused repair/state-reader suite passes 75 tests. These
framework checks are not live autonomous repair acceptance; the original failed
trial and its proposals remain unchanged.
