# Implementation dependency and import context

The live canary repeatedly mixed raw residue arrays with functions expecting residue counts. Its API summary exposed function names but neither their arguments nor their docstrings. It also contained separate `src`/`src.utils` packages at project root and under `code/`; the run-book failed with `No module named src.utils.tv` even though `code/src/utils/tv.py` existed. The previous summary described both layouts with the same canonical import spelling without identifying the collision.

Implementation context now includes function signatures/docstrings, warns when two files map to the same module, and inlines the actual local imported modules plus package initializers alongside explicitly referenced files. Dependency context is bounded and keeps complete files; omitted contents are explicitly marked. This supplies evidence for coherent generated repairs without relocating, replacing, or editing scientific source files itself.

Validation: 7 focused tests pass. A real Python subprocess reproduces the root/code package-shadowing failure; the prompt context exposes the hidden dependency, both sets of initializers, and the function's actual input contract. Another test distinguishes a local absolute import from an unrelated source file. Live generated repair remains to be verified.
