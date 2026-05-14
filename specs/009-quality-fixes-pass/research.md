# Phase 0 Research — Quality Fixes 009

All Technical Context items resolved here. Format per template: Decision / Rationale / Alternatives.

## 1. Activity feed storage shape

- **Decision**: Per-project append-only JSON Lines file at `projects/PROJ-XXX-*/activity.jsonl`. One JSON object per line, schema in `contracts/activity-feed-item.schema.json`. A sibling `projects/PROJ-XXX-*/.audit/` directory holds rubric-rejected contributions and pre-edit text; both are committed to git but the `.audit/` path is *never* delivered to downstream agents.
- **Packing-for-delivery rule (FR-031 detail)**: when packing the feed into an agent's input context budget B (chars), the writer walks items newest-first, including the full `body` for each. If adding the next item's body would exceed B/2 (reserve half the budget for the agent's own work), the writer switches to including only `summary` for older items. If even `summary`-only inclusion would exceed B, the writer truncates from the oldest end and inserts a single `[truncated N earlier items]` marker (FR-031). Newest items always retain full `body`. Concurrency: the snapshot is taken from a single read with `fcntl.flock(LOCK_SH)` to avoid mid-pack races.
- **Rationale**: JSON Lines is append-safe (an interrupted write loses at most one trailing line), is trivially line-grep-able, parses incrementally for the "deliver in full or correctly-truncate-from-oldest" requirement (FR-031), and stays in plain text in the repo for honest git history. No database or external service — Constitution Principle IV.
- **Alternatives considered**:
  - GitHub Issue thread mirror — rejected: tight coupling to GitHub, no offline operation, hard to truncate-from-oldest deterministically.
  - Single global `activity.jsonl` keyed by `project_id` — rejected: every dispatch would scan the whole file; per-project files are O(1) by path.
  - SQLite — rejected: adds a binary artifact, complicates git review, exceeds Principle V's "plain text and grep-able" idiom.

## 2. PDF text + layout extraction

- **Decision**: Layered — `pdftotext -layout` (from Poppler) for fast text scans (catches `unevaluated_command`, `section_numbering`, `reference_style`); `pdfplumber` for figure box geometry (catches `figure_size_inconsistency`) and for author-block region inspection (FR-016).
- **Rationale**: Both are open-source, both are deterministic for a given PDF, both run on macOS and Linux CI. Using two libraries split by *concern* (text vs. geometry) keeps each auditor module ≤200 lines and Principle-I-pure (no overlap of responsibility).
- **Alternatives considered**:
  - `pdfminer.six` alone — rejected: text extraction worse than Poppler's `-layout` on multi-column papers.
  - `MuPDF`/`PyMuPDF` — rejected: license is AGPL, conflicts with the repo's permissive expectations.
  - Rasterise + OCR — rejected: nondeterministic, slow, redundant when source is structured PDF.

## 3. Template-vs-real classification rules (FR-006)

- **Decision**: Three deterministic signals, evaluated in order, with weighted score:
  1. Presence of any literal placeholder string drawn from `.specify/templates/*.md` (e.g. `[FEATURE NAME]`, `[Brief Title]`, `ACTION REQUIRED:`, `Fill them out with the right edge cases`). Each hit ≥3 collected from the templates → **template**.
  2. Density of `[bracketed-text]` markers that match the template's unfilled-placeholder pattern (≥40% of marker occurrences are unfilled) → **template**.
  3. Section-body length: if ≥60% of bodies under H2 headings are shorter than 20 non-whitespace characters → **partial** (escalates to `template` if rule 1 also fires).
- **Rationale**: Deterministic, fast, explainable. Each classification cites the rule(s) that fired so a maintainer can verify. Per spec assumption: LLM heuristics MAY augment but MUST NOT gate.
- **Alternatives considered**:
  - LLM-judged "does this look real" — rejected: nondeterministic and contradicts the spec's no-LLM-in-auditor rule.
  - Token-level embedding similarity to the template — rejected: catches stylistic similarity, not substantive emptiness; legacy migrations (PROJ-006 etc.) would false-positive.

## 4. Personality rubric rule set (FR-005)

- **Decision**: Four content tokens; a contribution must score ≥3/4 to pass. Each is detected by regex + lightweight semantic markers (deterministic — no LLM):
  - **Specific objection**: presence of phrases like "but", "however", "this misses", "I disagree", "the problem is", combined with a noun phrase referencing the artifact's content.
  - **Specific question**: a `?` terminating a sentence that references a noun phrase from the artifact.
  - **Adjacent-work pointer**: explicit citation pattern (`arXiv:`, `doi:`, author-year, paper title in quotes, or a URL to a paper/dataset) OR a named technique/method-name not present in the artifact body.
  - **Specific reason for praise**: laudatory verb ("agree", "compelling", "novel", "well-done") + noun phrase referencing a specific element of the artifact, NOT a generic acclamation.
- **Rationale**: All four are checkable without LLM, all four map directly to FR-005's enumerated criteria. The 3-of-4 threshold tolerates personas whose voice naturally omits one (e.g. Socrates rarely praises; Marie Curie rarely jokes) — voice is preserved while the curatorial signal is enforced.
- **Alternatives considered**:
  - Single hard threshold per token — rejected: too brittle, would reject valid voice variation.
  - LLM judge with rubric — rejected: nondeterministic, expensive, violates the auditor-is-deterministic rule.

## 5. Cite-order reference rendering (Clarification Q1 / FR-014)

- **Decision**: Replace whatever the source arXiv bundle uses with `\bibliographystyle{unsrt}` in the llmxive class (or equivalent through `natbib`'s `numbers,sort&compress`-disabled mode if the source already uses `natbib`); `normalize_references.py` in the pipeline rewrites in-text `\cite*{key}` to consistent `\cite{key}` (no per-style variants) and ensures the bibliography is `unsrt`-ordered.
- **Rationale**: `unsrt` is `\bibliographystyle{unsrt}` — orders by first citation in the body, which is exactly what cite-order means. It is the most common arXiv-friendly style; deterministic; trivially auditable (numbers must appear monotonically increasing in body order).
- **Alternatives considered**:
  - Build a custom `.bst` file — rejected: more code, no benefit over `unsrt`.
  - `natbib` numeric with `sort` — rejected: `sort` reorders to citation order in the bibliography but also collapses adjacent citations to ranges, which is a separate styling decision; we want pure cite-order without compression.

## 6. Supported-PDFs registry shape (Clarification Q2 / FR-022)

- **Decision**: `papers/.supported.json` — a JSON file listing every paper currently passing the auditor with zero defects, with timestamp of last successful audit and the auditor version that passed it. Registry is rewritten on every audit run (no manual edits); a CI job fails if a previously-registered paper now fails.
- **Rationale**: Single source of truth (Principle I), human-readable, git-diffable so removals are visible in PRs, auto-maintained per Q2 decision.
- **Alternatives considered**:
  - A separate registry directory — rejected: introduces a second source of truth (the registry itself + the actual defect state).
  - Inferring the registry from CI logs — rejected: not git-diffable, opaque.

## 7. Manifest schema for "comments considered" (FR-027)

- **Decision**: Structured JSON object emitted as the *last* block in any agent output, fenced as ```json comments-considered ```. Schema in `contracts/comments-considered-manifest.schema.json`. Items reference feed item IDs and carry one of four response codes (`addressed` / `acknowledged` / `rebutted` / `deferred`) plus a free-text reason. The runner's output-validation step parses the manifest and rejects on schema-fail or missing ID.
- **Rationale**: Structured > free-text — deterministic to validate (FR-028); placing the manifest *after* the contribution body keeps it from interrupting the persona's voice. JSON-in-fence is widely supported by every code path that handles markdown.
- **Alternatives considered**:
  - Sidecar `manifest.json` file — rejected: requires every agent path to know how to write two files atomically; complicates dispatch return shape.
  - Free-form prose acknowledgements — rejected: not validatable; defeats FR-028.

## 8. LaTeX class extension surface (FR-015, FR-016, FR-020)

- **Decision**: Extend `papers/.style/llmxive.cls` with:
  - `\figwidth{narrow|column|full}` macro — three bounded widths (`0.45\linewidth`, `\linewidth`, `\textwidth`). `normalize_figures.py` rewrites `\includegraphics[width=…]{...}` to use one of these three based on the source width relative to text width.
  - `\authorblock{…}` macro — fixed layout (name, affiliation, email/URL); `normalize_authors.py` rewrites any per-paper `\author{}`/custom author macros into a single canonical `\authorblock` call.
  - `\unsupportedblock{name}{...}` macro — explicit "this construct is not yet supported" failure path used by the pipeline when it encounters a custom block; emits a hard `\@latex@error` rather than silently rendering raw text (FR-020).
- **Rationale**: Keeps the class as the single LaTeX source of truth (Principle I); the pipeline rewrites *sources* not the class on a per-paper basis (Principle I corollary).
- **Alternatives considered**:
  - Per-paper `.tex` patches — rejected: scales badly; violates Principle I.
  - A separate "compatibility" `.sty` file — rejected: same logic doubled in two places.

## 9. Runner integration for activity-feed delivery (FR-026)

- **Decision**: Modify `src/llmxive/agents/runner.py`'s dispatch function. Before any agent's `run(...)` is called, the runner (a) loads `projects/<project_id>/activity.jsonl`, (b) packs it into the agent's context with a budget check (truncate-from-oldest with `[truncated N earlier items]` marker per FR-031), and (c) records the dispatch metadata. After the agent returns, the runner validates the "comments considered" manifest (FR-028) and either commits the contribution into the feed or records a failure into the feed.
- **Rationale**: Single integration point (Principle I) — every existing agent that goes through `runner.py` gets feed delivery and manifest validation for free; we do not modify each agent individually.
- **Alternatives considered**:
  - Per-agent feed loading — rejected: violates Principle I, multiplies the number of places where the feed contract has to be re-implemented.
  - Decorator on each agent — rejected: nearly the same cost as modifying runner, but harder to audit "did every agent get wrapped".

## 10. Existing template-stub vs. legacy-migration discrimination

- **Decision**: The auditor distinguishes by examining `Status:` frontmatter and the first non-frontmatter paragraph. If `Status: migrated from legacy technical-design (pre-refactor)` or `Status: active` accompanied by ≥500 characters of non-bracket content in the first 5 sections, the artifact is `real` even if it shares stylistic placeholders with the template.
- **Rationale**: PROJ-006, PROJ-008, etc. are concrete real-prose migrations with templated *headings* but real *bodies* — the auditor must not false-positive them as template. The spec's Assumptions explicitly call this out.
- **Alternatives considered**:
  - Whitelist of "legacy migration" paths — rejected: not maintainable as the migration set grows.
  - Word-count-only threshold — rejected: a `template` artifact with verbose placeholder explanations could exceed the threshold.

---

**Status**: All NEEDS CLARIFICATION items resolved. Phase 1 can proceed.
