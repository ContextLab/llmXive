# Preserve active planning artifacts through replanning

At 04:32 UTC the live canary's task review kicked back from PLANNED to CLARIFIED.
The next planner step failed before its model call: setup-plan.sh returned exit 1.
Python had already resolved the authoritative `specs/001-totient-canary` pointer,
but the shell script ignored it and used numeric-prefix lookup. Read-only
`get_feature_paths` reproduced the exact error: two directories share prefix
001 (`001-finite-range-residue-imbalance` and `001-totient-canary`). The project
had no `.specify/feature.json`; the stored Python pointer was unambiguous.

The planner now skips template setup for an existing plan. For a new plan it
passes the authoritative feature directory and name as subprocess-local settings,
so missing/stale feature.json and a parent main branch cannot choose another
feature. Existing plan, research, data-model, quickstart and contract files are
supplied as revision inputs. A rejected artifact revision restores prior bytes
instead of deleting the previous plan; newly created rejected artifacts are
removed. Writes are confined to the active feature.

55 focused planner/discovery/integration tests passed. Five new cases exercise
real shell setup with missing/stale metadata and duplicate prefixes, preservation and prompt inclusion
of an existing plan, and rollback after a genuinely invalid multi-document YAML
contract. These cases fail against the previous platform. No scientific canary
plan, result or stage was manually changed to recover from this failure.
