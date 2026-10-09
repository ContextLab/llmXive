# Refused artifacts must keep their implementation task incomplete

The fresh isolated canary's GLM-5.3 response at 13:00:22 UTC supplied valid
`code/totient_census.py` but malformed `code/tests/test_totient_census.py`:
the next YAML artifact was indented into Python source at line 128. The source
writer correctly refused that test, yet checked T002 complete and moved to T003.
The inspection truthfully recorded a committed partial write; it did not prove
all T002 deliverables were written or independently accepted. Read-only source:
`/private/tmp/llmxive-canary-fresh-20261009-1250/notes/inspection-history/implementer-2026-10-09T13-00-22.445335+00-00.json`.

`ImplementerAgent.write_artifacts` previously printed each refusal, continued,
and marked the task X whenever no requested execution failed. It now collects
those exact diagnostics, retains successfully written siblings, saves a
redacted `code/.tasks/<task>.artifact-write.log`, and leaves the task unchecked.
It does not execute any scripts from a partially refused proposal, including
older files whose replacements were refused. The existing task-specific retry
log reader feeds the diagnosis and referenced file paths into the next prompt.
A structurally valid retry removes the obsolete refusal log. Independent task
review and actual execution still decide scientific completion.

The change covers syntax, unresolved-name, sibling-import, diff-fragment,
path-confinement, directory-target, empty/non-text contents, and missing-path
refusals. A completed report with no writable artifact or execution request is
also kept incomplete. It does not change the separate failed/atomize verdict
protocol or unrecoverable YAML handling; those are distinct review concerns.

Validation: seven behavioral regressions fail on baseline; eight new checks
pass including persisted-log redaction. The principal test uses the real writer,
mechanical task selector and prompt builder: valid source stays on disk, the
invalid test is absent, T002 remains next, and its exact syntax diagnostic is
present in the retry prompt. An execute:true sentinel never runs from the
partially refused report, and a corrected retry writes its test and proceeds.
Together with related execution, retry, shell, import/binding and context tests,
56 distinct focused checks pass. No scientific canary state/artifacts were
edited or promoted. Live recovery remains unverified.
