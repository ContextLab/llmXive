# Repository hygiene audit — 2026-10-09

Snapshot: `c7b56c85814` (main). The original user checkout and its untracked work were not changed. Inventory used the entire Git tree, including files absent from the sparse audit worktree.

## Findings and recovery

- **2,664 tracked files / 409,818,219 bytes (390.83 MiB)** leaked into 33 repository-root entries. They include GEO downloads, BEIR corpora, OpenNeuro samples, extracted RefSeq records, PDFs, a large GIF, incomplete downloads, and empty files.
- Two more misplaced files lived under `projects/data` and `projects/state`, outside any project namespace. They contain a header-only CSV and null checksum entries; they are not successful scientific outputs.
- Most introducing commits also record a failed data-source discovery (`status: none`). The old discovery executor inherited the repository working directory and cron staged the entire working tree. The October recovery already isolated discovery snippets in temporary directories and restricted cron writes. This audit preserves the historical leftovers rather than deleting or ignoring them.
- The former hygiene checker recognized four scratch filenames and root PNGs. It missed the other extensions and extracted directories. It could also retain an LLM's `verdict: clean` despite deterministic flags.
- Current `run_in_venv` accepted an explicit working directory outside its project, including a symlink escape. The new check rejects that directory **before** venv creation or executing generated code.

All **2,666 files / 409,818,339 bytes** are relocated without changing a byte or file mode. Twenty groups with an introducing commit and matching discovery intent are kept in the associated project's `.specify/recovered-downloads/`. Fifteen groups whose scientific ownership is ambiguous (or which are misplaced empty scaffolds) are preserved under `state/recovered-downloads/<introducing-commit>/`, retaining their original paths. These are **recovery archives, not approved study data**. No tasks, stage states, checksums, or scientific acceptance records are changed.

The [machine-readable manifest](root-file-recovery.json) records every original path, destination, Git blob hash, mode, byte count, introducing commit, discovery record, and attribution status. It records the later overwrite of `figure.png` by a different discovery attempt. The three particle-tracking illustration files are also explicitly named in the dataset README that overwrote the platform README in their introducing commit; the restored platform README remains intact.

Reference review found existing BEIR recipes use a relative download directory and current project code uses its own download/output paths. Keeping the archived probe downloads does not require changing these recipes: discovery now runs in an isolated temporary directory, and research commands run in the project directory. Generic filename matches elsewhere were fixture names, function names, or separate project outputs; these were not rewritten.

Platform assets (`src`, `agents`, `scripts`, `specs`, etc.), canonical `state`, and the `web`/generated `docs` dashboard trees remain in their documented locations. Existing `.omc` user changes and local untracked files were not touched. This is a current-tree cleanup: Git history and total object storage are not rewritten or reduced.

## Guardrails and verification

- `python src/llmxive/checks/repository_layout.py` checks the Git index against documented platform roots and requires `projects/<PROJ-id>/...`. It sees sparse-checkout paths and handles spaces/newlines.
- The independent `audit-repository-layout` CI job runs without package installation or model calls. A three-file sparse checkout audits the entire 268,060-path Git index while materializing only 972 KiB locally. The existing hygiene agent uses the same rule. Its final verdict now follows deterministic flags.
- The cron commit guard applies the same project namespace rule to staged, unstaged, and untracked changes. It refuses new `projects/data` / `projects/state` leakage instead of silently staging it.
- `python scripts/verify_root_file_recovery.py --check-original` compares all relocated hashes and modes with the pre-migration Git tree and the current index. **2,666 exact matches; zero original leaked paths remain.** CI omits `--check-original` so a shallow checkout verifies the recorded hashes without fetching history.
- Focused real Git/filesystem/subprocess tests cover misplaced downloads, unknown directories, sparse paths, wrong project namespaces, symlink working-directory escapes, credential-isolated discovery, and deterministic hygiene verdicts. Ruff and Actionlint pass. The broad offline suite initially had 3,304 passes, 36 failures, 6 errors, and 21 skips. Materializing missing sparse-checkout fixtures resolves 36 of those failures/errors; six integration failures remain in canonical claim sweeps, subject reuse, and the older one-task format expectation. All six reproduce on the unchanged base commit. The focused changed-area suite passes 33 tests.

These checks are correctness and persistence boundaries, **not an OS filesystem sandbox**. Generated code with explicit absolute paths can still attempt writes elsewhere; cron refuses to publish such writes. Stronger OS containment remains tracked under the pipeline/storage recurring issues. Ambiguous archive ownership remains under #1241; assigning a scientific owner or accepting an input requires evidence beyond a coincident pipeline commit.
