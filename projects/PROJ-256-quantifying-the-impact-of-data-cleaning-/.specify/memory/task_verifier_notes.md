# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T1201a** — The implementer did not provide any artifact (e.g., a text file, JSON, or console output) listing the `t0*.py` files found in the `code/` directory. Without such a list, the requirement to audit and generate the file list is not satisfied. The next implementer must produce a non‑empty list of matching filenames from the `code/` directory.
- **T1201b** — No migration plan document (e.g., a markdown, text, or spreadsheet listing the `t0*.py` files and the steps to migrate them) was provided, and there is no evidence that such a plan covers all identified files. The required artifact is missing, so the task is not satisfied.
- **T1204** — No evidence was provided that any `t0*.py` files were removed from the `code/` directory, nor is there a verification artifact (e.g., a file listing or test output) confirming that `code/` contains no such files. The implementer must supply proof that the deletion was performed and that T1204a passes.
- **T1205** — No audit report or any list of hard‑coded path strings from the Python modules in `code/` was provided; the required artifact T1205a is missing, so the task is not satisfied.
