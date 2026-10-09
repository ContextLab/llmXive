# Python binding validation (2026-10-09)

The fresh full-pipeline canary rejected `code/run_full_sweep.py` before execution because its exception handler's `exc` variable was classified as an unresolved import. The earlier canary similarly rejected `src/totient_tv.py` for `name`. The static checker collected assignments/imports but omitted exception, loop, context-manager, and comprehension bindings.

The guard now recognizes loop/context-manager targets and tracks local exception/comprehension scopes while gathering loaded names. Comprehension iterables are visited before their own targets are bound. Exception and comprehension names do not become module globals. This change only removes false pre-write rejections; execution and task verification still determine acceptance.

Validation: 45 focused tests pass, including 16 real Python subprocess examples covering valid bindings and actual NameErrors. Replaying the new cases against the old checker produces 12 failures and 4 passes. The existing checker remains a conservative, order-insensitive approximation rather than a complete Python scope or control-flow analyzer.

This fixes a concrete implementation blocker under recurring issue #1139. It does not establish full-sweep or paper acceptance.
