# Match Python's explicit package import behavior

The canary at 05:42 UTC on 2026-10-09 rejected a generated validation test:
`from src.utils import validation` was said to import a nonexistent name from
an empty package initializer. The package's child `validation.py` existed.
Python can load that child without an explicit initializer re-export.

The static implementation guard now recognizes child modules, regular
subpackages and namespace subpackages for explicit package imports. It also
stops treating `__all__` as an explicit-import whitelist: `__all__` controls
star imports, neither forbids other bound names nor creates a nonexistent one.

Validation: 33 related tests pass. Five behavioral regressions fail on the
previous source. Each new regression first executes an actual Python import,
then checks agreement with the static guard; the negative case proves that
putting a nonexistent name in `__all__` cannot make its import valid. This does
not solve the separate source-layout collision or prove scientific acceptance.
