# Phase 0 Research — Paper Revision Implementer + Publisher

This document resolves every open design question surfaced in `plan.md`'s
Technical Context before Phase 1 (data-model + contracts) begins. Each
entry follows the Decision / Rationale / Alternatives format.

## 1. DOI registrar

**Decision**: Zenodo (https://zenodo.org, REST API at `https://zenodo.org/api/`).

**Rationale**:
- **Free**: no per-DOI fees, no annual subscription.
- **Real DOIs**: Zenodo is a DataCite member; depositing → publishing
  registers a permanent, resolvable DataCite DOI of the form
  `10.5281/zenodo.<n>`. Sandbox emits `10.5072/zenodo.<n>` (also
  resolvable but flagged as test).
- **CERN-operated**: institutional longevity comparable to arXiv.
- **Documented REST API** with versioning support (`/actions/newversion`)
  — meets FR-025, FR-027.
- **No deposit-size limits** for individual files relevant to a research
  paper (current cap is 50GB per file).

**Alternatives considered**:
- **DataCite direct** (https://datacite.org): would need a paid
  Repository membership (~$1-2k/year). Rejected per Constitution IV.
- **Crossref**: paid membership ($275/year + per-DOI fees). Rejected
  per Constitution IV.
- **GitHub release as a citable artifact**: GitHub auto-issues a Zenodo
  DOI on release, which is effectively what we do directly via Zenodo's
  API. Going direct gives us per-paper metadata control (creators,
  description, keywords) that the GitHub-Zenodo integration aggregates
  at the repo level.

**API surface used**:
| Operation | Endpoint | Notes |
|-|-|-|
| Create deposition with pre-reserved DOI | `POST /api/deposit/depositions` with `{ "metadata": { ..., "prereserve_doi": true } }` | DOI is in the response under `metadata.prereserve_doi.doi` — usable BEFORE publish, which is how we bake it into the PDF before final compile. |
| Upload PDF | `PUT /api/files/<bucket>/<filename>` (newer file API) OR `POST /api/deposit/depositions/<id>/files` (older form-data API) | Bucket URL is returned by step above under `links.bucket`. |
| Publish deposition | `POST /api/deposit/depositions/<id>/actions/publish` | After this call the DOI is registered with DataCite and becomes resolvable. |
| New version of an existing deposition | `POST /api/deposit/depositions/<id>/actions/newversion` | Returns a new draft linked to the original via Concept DOI. |

**Authentication**: bearer token in `Authorization: Bearer <token>`. Token
provisioned via Zenodo account → Applications → Personal access tokens
with scopes `deposit:write` + `deposit:actions`.

**Sandbox vs production**:
- Production: `https://zenodo.org/api`
- Sandbox: `https://sandbox.zenodo.org/api` (separate account, separate
  token, DOIs prefixed `10.5072/`). Used in `tests/real_call/test_publisher_zenodo_sandbox.py`.

## 2. Implementer edit format

**Decision**: structured edits in one of two forms returned by the LLM:
- **`search_and_replace`**: `{ "kind": "search_and_replace", "file": "<rel-path>", "search": "<verbatim text>", "replace": "<new text>" }`
- **`unified_diff`**: `{ "kind": "unified_diff", "file": "<rel-path>", "diff": "<standard --- / +++ / @@ unified diff>" }`

The LLM prompt instructs it to pick whichever form is cleanest for the
edit; `search_and_replace` is preferred for single-line / single-paragraph
fixes (most writing-class tasks), `unified_diff` for multi-hunk edits.

**Rationale**:
- Both forms are **localized** — they touch a bounded region of the file,
  which means we can review, rollback, and audit them per FR-005 + FR-017.
- **No whole-file rewrites**: the prompt forbids the LLM from emitting a
  full-file replacement.
- Both forms are **machine-applicable**: `search_and_replace` via Python
  `str.replace()` (after asserting `search` matches exactly once;
  multi-match → reject as ambiguous); `unified_diff` via `git apply`
  (which is on every CI runner already because of git itself).

**Alternatives considered**:
- **Whole-file rewrite**: rejected (FR-005 explicitly prohibits).
- **AST-aware LaTeX edits** (e.g., via `pylatexenc`): rejected for v1
  because the LLM doesn't see the AST, and adding an AST-roundtrip
  introduces translation errors. We can layer this in v2 if `unified_diff`
  hit rate is low.

**Edit-validation pre-flight checks** (before applying):
1. The file path is under `paper/source/` OR (for science-class tasks
   only) under `projects/<id>/code/` or `projects/<id>/data/`. Anywhere
   else → reject.
2. For `search_and_replace`: `search` must appear EXACTLY ONCE in the
   file (else reject as ambiguous → task marked `skipped`).
3. For `unified_diff`: the diff must apply cleanly via `git apply
   --check`. If `--check` fails → reject as `skipped`.
4. After applying, the file MUST parse (for `.tex` the bar is "LaTeX
   compiles end-to-end" — verified by FR-003 step (e)).

## 3. Rollback mechanism

**Decision**: pure-Python content snapshot (`bytes`) keyed by SHA-256.
Before each task: capture `before_hash = sha256(file.read_bytes())` and
the full `before_bytes`. On compile-failure: `file.write_bytes(before_bytes)`.

**Rationale**:
- **Zero git dependency at runtime**: we don't `git stash` or `git
  checkout` mid-task — the implementer might run in a worktree that's
  not git-clean, or in a subdirectory the user didn't intend to commit.
- **Idempotent + per-task scoped**: each task's snapshot is independent;
  rolling back task N doesn't disturb tasks 1..N-1.
- **Auditable**: `before_hash` is recorded in `implementer-log.yaml`
  (FR-004) so operators can reconstruct any rollback retroactively.

**Alternatives considered**:
- **git stash per task**: rejected — complicates concurrent runs and
  requires a clean working tree.
- **git checkout `<file>`**: requires the file to be tracked in git; some
  prototype/test scenarios may not have that guarantee.
- **filesystem-level snapshots (`cp`)**: equivalent to our `bytes`
  snapshot but uses more I/O. Rejected for simplicity.

## 4. Author identity canonicalization

**Decision**: canonical identity string `"<name> (<model_name> on <backend>, <ISO 8601 date>)"`, with
dedupe key `(name, agent_version)` (NOT including the date — re-runs on
different dates collapse to one author entry).

**Rationale**:
- The dedupe key matches FR-008's contract.
- The full canonical string carries the model + backend so readers can
  tell which model wrote each revision — important for the journal's
  "LLM agents are authors" claim (US3 priority justification).
- The first-contribution timestamp is captured in
  `metadata.json::authors[].first_contributed_at` (FR-006), so we don't
  need to encode it in the display name.

**Example identity strings**:
- `llmXive-implementer-v1.0 (qwen.qwen3.5-122b on dartmouth, 2026-05-19)` — first-contribution display
- `llmXive-implementer-v1.0` — dedupe key (collapses the `(...)` parenthetical)

**Display in `\author{}`**: original authors first, then `\par\hrule\par
\textit{Revised by:}` then the LLM contributors in chronological-first-contribution
order. Per FR-007.

## 5. DOI versioning on re-acceptance

**Decision**: invoke Zenodo's `POST /api/deposit/depositions/<id>/actions/newversion`
endpoint to mint a NEW DOI version. Append the new DOI to
`metadata.json::doi_versions` (ordered list) and make it the new canonical
`metadata.json::doi`. The original DOI continues to resolve to the prior
PDF (Zenodo guarantees this).

**Rationale**:
- FR-027 mandates this exact flow.
- Zenodo's versioning links both DOIs via a shared "Concept DOI"
  (returned in `links.parent`). The Concept DOI is the stable
  inter-version identifier; we record it in `publication.yaml::concept_doi`
  for future reference.

**API call sequence for re-acceptance**:
1. Read `metadata.json::zenodo_id` (the prior deposition's internal id).
2. `POST /api/deposit/depositions/<zenodo_id>/actions/newversion` → returns
   the new draft deposition's id under `links.latest_draft`.
3. Fetch the new draft (`GET /api/deposit/depositions/<new_id>`).
4. Upload the revised PDF to the new draft's bucket.
5. Update the deposition metadata (revised authors, revised abstract if
   any).
6. `POST /api/deposit/depositions/<new_id>/actions/publish`.
7. Capture the new DOI from the response.

**Alternatives considered**:
- **Always mint a brand-new deposition** (no versioning): would lose the
  inter-revision linkage Zenodo provides. Rejected.

## 6. Post-paper appendix typography

**Decision**: a separate `.tex` fragment (generated by the spec-013
`gen_appendix.py` prototype, promoted to `src/llmxive/pipeline/`) is
`\input{...}`'d before `\end{document}` in the published main `.tex`.
The fragment uses `llmxive.cls`'s existing typographic primitives
(`\section*{Reviews}`, `\subsection*{...}`, `\bigskip`, etc.) so it
shares fonts, colors, and rules with the main paper.

**Rationale**:
- FR-035 explicitly allows this approach.
- Keeps the appendix in the SAME PDF artifact (FR-034) — no separate
  files for the reader to track.
- The prototype `gen_appendix.py` already generates this fragment
  deterministically from `paper/reviews/paper_reviewer*.md` and
  `paper/revision_history.yaml`; promoting it to production code is a
  straightforward refactor (move the file + add unit tests).

**Spacer page implementation** (FR-036): a `\clearpage` followed by a
minipage with the demarcation text + GitHub directory link, then
another `\clearpage`. No page numbers, no headers — achieved by
wrapping the spacer in `\thispagestyle{empty}`.

**Alternatives considered**:
- **Separate back-merged PDF compiled from its own appendix.tex** (also
  allowed by FR-035): rejected for v1 because it requires a `pdfunite`
  or `pdftk` post-step that adds a dependency. Single-file `\input` is
  cleaner.
- **Markdown-rendered reviews via `pandoc`**: rejected because `pandoc`
  isn't always available on minimum-spec runners, and the prototype's
  pure-Python `render_inline()` (with `\ref`/`\cite` passthrough) is
  battle-tested against MemLens's 102-page output.

## Cross-references

- Existing chunked-summarization infrastructure (spec-013 reviewer
  changes) shipped in commit `3817c32b` — no research needed; design
  is documented in the commit message + `src/llmxive/agents/paper_reviewer.py:108-294`.
- llmxive.cls extensions (`\paperdoi`, `\papervolume`, `\paperissue`,
  adjustbox auto-fit, tabularray, sloppy abstract) shipped in commit
  `3817c32b` — `papers/.style/llmxive.cls`.
- Existing per-specialist re-review protocol (spec 012 / FR-014-017) is
  reused verbatim per US5; no research needed.
