# Contract: Planner Research Guard (FR-006 / FR-007)

Module: `src/llmxive/speckit/_research_guard.py` (NEW, canonical). Called from `PlannerAgent.write_artifacts`: `assert_artifact_set_complete` BEFORE the write loop, then `assert_data_model_contracts_consistent` + `assert_urls_reachable` after the existing `refuse_if_diff` + `guard_emit` loop.

## `assert_artifact_set_complete(files: dict[str, str]) -> None` (FR-005)

- **Requires** all five logical artifacts present and non-empty: `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, and ≥1 `contracts/*.yaml` key.
- **Detects a failed split**: if `files` has only `plan.md` (the `_split_multi_file` no-marker fallback) while the response clearly intended multiple files, treat as a failed marker split.
- **Raises** `IncompleteArtifactSet(missing, reason)` listing which artifacts are absent/empty.
- This is the first gate so a malformed/partial response fails before any per-file work.

## `assert_urls_reachable(research_md_text: str, *, timeout: int = 10) -> None`

- **Extracts**: all `https?://…` URLs; bare `arXiv:<id>` → `https://arxiv.org/abs/<id>`; `doi:<doi>` / `https://doi.org/<doi>`.
- **Checks each**: HTTP `HEAD` (10s timeout, descriptive User-Agent); on 405/501 fall back to `GET` with `Range: bytes=0-0`. Accept final status **200–399** only.
- **Raises** `UnreachableReference(url, reason)` on the FIRST reference that is 4xx/5xx, times out, fails DNS/connection, or is malformed. **No retries** (FR-006 clarification).
- **No-op** when `research.md` contains zero references (a plan may legitimately cite none; FR-006 only constrains references that ARE present).

## `assert_data_model_contracts_consistent(files: dict[str, str]) -> None`

Structural consistency check (NOT a 1:1 entity↔schema name match — that proved
too fragile against real planner output, where schema filenames differ from
entity headings and the planner emits ≥1 schema, not one per entity):

- **Entities present**: `data-model.md` must define real entities — an attribute
  markdown table, a mermaid/ER diagram, or entity headings — not empty prose.
- **Schemas valid**: every `contracts/*.yaml` in `files` must parse as a
  non-empty YAML mapping/sequence (a real schema, not empty or a prose stub).
- **Raises** `InconsistentDataModel(reason, invalid_schemas=...)` when the
  data-model defines no entities, or any contracts schema is empty/unparseable.
- **Cardinality/naming**: intentionally unconstrained.
- **No-op** when there is no `data-model.md` in `files` (FR-005 requires its
  presence; this runs the consistency check only when it exists).

## Exceptions

Both subclass `RuntimeError`. On raise, the caller (`write_artifacts`) MUST unlink every artifact written this invocation before propagating, so the base class records `outcome: failed` and the stage holds at `clarified` (parity with `guard_emit`'s unlink-on-fail).

## Invariants

- Stdlib only (`urllib.request`, `http`, `re`, `yaml`) — no new third-party dependency (Principle IV).
- Deterministic given fixed network responses; the regression test pins responses with a local `http.server`.
