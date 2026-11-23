# Malformed paper tasks must stay on the paper track

At 14:04 UTC the isolated canary completed paper-task review, then the duplicate
paper-tasker dispatch at `paper_tasked` returned a table-only response.
`TaskFormatError` was correctly raised, but graph recovery used a flag defined
as `agent_name == paper_implementer`. The paper tasker therefore routed to the
research `planned` stage and wrote its diagnosis into research memory. The next
tick started rewriting research tasks despite already accepted research.
The operator interrupted that run to preserve the failure evidence. Its earlier
research acceptance remains historical evidence, not full pipeline acceptance.

Track selection now follows the actual paper lifecycle stage for every Spec Kit
agent. Format recovery writes the diagnosis to paper memory and returns to
`paper_planned`. The next paper-task prompt receives that exact diagnosis and
explicit canonical checkbox syntax. It preserves existing research and paper
artifacts when a response is rejected; no task, counter or stage was manually
reset in the scientific run.

Two real graph-dispatch regressions reproduce the wrong `planned` route on the
preceding implementation at both `paper_planned` and `paper_tasked`. They pass
with the fix and verify byte preservation, paper-only feedback and the next
prompt. The related task-authoring, pipeline-recovery and routing suite passes
35 tests. This fixes the demonstrated cross-phase route; avoiding the duplicate
paper analysis and bootstrapping a missing paper/source remain separate work.
