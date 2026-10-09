# Project-local revision artifacts — 2026-10-09

The strict research commit guard accepts only concrete project folders, `state/`, and `web/data/`. The revision adapter and implementer log writer still wrote under platform `specs/auto-revisions/`, so a review kickback could produce work that the next cron commit refused. The old workflow test searched for `git add -A` in shell text and did not prove these paths persisted; PR #1529 replaces that test with real Git persistence tests.

## Migration and compatibility

Move **1,356 tracked files, 6,769,457 bytes, across 122 projects** from `specs/auto-revisions/<id>/round-N/` to `projects/<id>/.specify/auto-revisions/round-N/`. Every Git blob and mode is unchanged. `project-revision-migration.json` records the source commit and each old/new path, blob, mode, and byte count. Verification compared every staged destination with both its recorded blob/mode and the source commit; every old index path was absent. These are active revision files, so the manifest is a migration receipt rather than an immutable-file CI gate: later task/log updates remain valid.

New revision specs and implementer logs use the project-local directory. Round discovery, implementer work-spec reads, revision-log reads, operator unblock checks, and dashboard history links understand both layouts. Existing state and history pointers are preserved as historical provenance; readers resolve an old pointer to the migrated file when present. The repository-layout check rejects newly tracked `specs/auto-revisions/` files, including in sparse checkouts.

Full-replan resets retain the existing bounded round-budget semantics, but archive the prior cycle and history under the owning project's `.specify/revision-archives/` instead of deleting them. Legacy directories are copied without mutation; a project-local marker prevents those retired rounds from consuming the new budget. Archive sources and destinations are validated before any source moves. Escaping directory/file symlinks and nested source symlinks are refused, preserving source bytes and preventing accidental import of unrelated data. Repository symlink aliases retain usable relative pointers.

## Fixed-writer audit

| Writer | Prior default | Result |
| --- | --- | --- |
| Revision adapter and implementer logs | `specs/auto-revisions/<id>/` | Project-local revision directory; legacy readers retained |
| Seven convergence revisers | `.llmxive/summarize_cache/` | Owning project `.specify/summarize_cache/` |
| Generic convergence engine through both production callers | CWD `.summaries/` when an input overflowed | Explicit owning-project cache; generic/multi-project runner calls use shared `state/summarize_cache/` |
| Paper reviewer | `projects/<id>/paper/.chunk_summaries/` | Already project-local |
| Dashboard builder | `web/data/` | Already allowed |
| PDF auditor registry | `papers/.supported.json` | Separate audit workflow maintenance output, not a research-run writer |

The standalone summarization utility still accepts caller-selected caches; its generic fallback remains for API compatibility. Both production engine entry points and all seven production revisers now select explicit allowed caches. A real overflow test expands the stored source and proves every source token remains in order with its original multiplicity; a runner-level test proves the project-owned cache reaches the actual engine.

**Remaining historical ownership debt:** `.llmxive/summarize_cache/` has 783 tracked files. Their manifests record content hashes, goals, models, timestamps, and chunk pointers, without an explicit owning-project field. These historical caches are retained because blindly moving them could break embedded summary pointers or misattribute evidence. New defaults stop adding to that root cache. Further owner attribution belongs to recurring repository-reliability issue #1241.

## Validation

Focused regression coverage includes real Git guard acceptance, byte-preserving historical pointer resolution, bounded round reset with archived provenance, all seven reviser defaults, real overflow reconstruction, production runner cache propagation, dashboard legacy-link resolution, project/path traversal rejection, repository symlink aliases, archive/legacy/source/history/state symlink escapes, existing revision consumption, and research/paper review routing. Exact broad-suite results are recorded in the pull request. Live research advancement is a separate acceptance checkpoint; passing these tests does not establish scientific acceptance of a project.
