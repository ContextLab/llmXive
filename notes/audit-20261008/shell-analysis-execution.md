# Execute research shell wrappers instead of silently skipping them

The canary task list and generated files include scripts/run_full_analysis.sh,
check_runtime.sh, and check_results.sh. Code inspection found that the implementer
silently ignored execute:true on every non-Python artifact. The quickstart runner
also silently dropped bash/sh command lines. Neither behavior provides evidence
that a shell-orchestrated analysis actually ran.

Two real subprocess regressions fail against the previous canary platform:
(1) the requested shell artifact produces no result file; (2) the runbook executes
only its Python smoke check and omits both shell commands. The fixed runtime runs
project-local .sh scripts with literal argv, the project venv on PATH, and the
same credential-stripped environment used for Python. Nonzero exits block the
execution gate, and timed-out shell process groups are killed including Python
children. Unsupported execute:true types and execution setup exceptions now
produce failure logs instead of being ignored.

33 focused tests passed, including both previously failing regressions, actual
venv use, argument preservation, credential removal, a shell exit 7, and a child
process timeout with no late artifact write. This is runtime behavior proof;
live full-study and paper acceptance remain pending. The current canary quickstart
still contains only small Python examples, so this does not establish that the
model has authored a complete full-study runbook yet.
