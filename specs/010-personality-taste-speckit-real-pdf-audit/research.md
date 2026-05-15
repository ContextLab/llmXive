# Research: Personality Taste, Real Speckit Artifacts, PDF Audit

## R1 — Personality prompt engineering for first-try compliance

**Decision**: Restructure the umbrella prompt (`src/llmxive/agents/prompts/personality.md`) to put a `## Required outputs` block at the top with three named, individually labelled fields the persona MUST supply: `position`, `adjacent_work`, `interest_signal`. Each persona card adds a fully-worked example in its YAML frontmatter (`example_contribution:`) showing what compliance looks like for that persona's voice. The example is rendered into the prompt at runtime as a few-shot anchor.

**Rationale**: The existing umbrella prompt (`personality.md` lines 72-91) already says "must contain at least one of: specific objection / specific question / specific praise / curatorial pointer" — but lets the persona pick. With the new spec requiring ALL THREE new axes plus the existing four, the persona has to satisfy seven gates simultaneously. Without a structured slot for each, the persona will keep producing free-form prose that occasionally happens to include the required pieces, occasionally not. Naming the slots forces the persona to fill each one explicitly; the few-shot example shows what fits a slot vs. doesn't.

**Alternatives considered**:
- (a) Stick with the current "at least one of" rubric and ratchet the retry budget up to 3: fails Principle V (silent retry past expensive checks); doesn't scale (more retries doesn't change what the persona writes; same prompt produces the same distribution).
- (b) Switch to JSON output for the contribution body: breaks the "contribution looks like persona writing" UX; the markdown body is what shows up on project cards.
- (c) Use a separate JSON sidecar for the required fields: dual-write problem (body and sidecar can drift); rejected per Q2's "JSON sidecar" answer.

## R2 — Stage rollback ordering when a template is pruned (FR-009)

**Decision**: When `speckit_prune.py` deletes a template artifact, walk the project's `state/projects/<id>.history.jsonl` *backwards* and find the most recent stage whose generated artifact (a) still exists on disk and (b) classifies as REAL via `_real_only_guard.is_real()`. Set the project's `current_stage` to that surviving stage. Record a `template_artifact_purge` event in the history with the deleted-artifact paths and the new stage.

**Rationale**: The existing `STAGE_TO_AGENT` mapping in `src/llmxive/pipeline/graph.py` is a linear order of stages (brainstormed → flesh_out_complete → validated → project_initialized → specified → clarified → planned → tasked → analyzed → in_progress → research_complete → ...). Each stage produces a specific set of artifacts. If we delete a template `spec.md` produced at the `specified` stage, the project should roll back to `project_initialized` (the latest pre-`specified` stage) and re-attempt. If `project_initialized` also has a templated artifact, we walk further back to `validated`, and so on. Walking the history file rather than reverse-mapping `STAGE_TO_AGENT` handles the case where a stage produces multiple artifacts (any survivor = stage survives) and the case where the project may have skipped stages (history is the ground truth).

**Alternatives considered**:
- (a) Always roll back to `flesh_out_complete`: oversimplified; loses work on projects whose `validated` and `project_initialized` artifacts were fine.
- (b) Use `STAGE_TO_AGENT` reverse-walk only: doesn't account for multi-artifact stages or skipped stages.
- (c) Don't roll back; just delete and leave `current_stage` as-is: leaves the project in an inconsistent state where the pipeline thinks `spec.md` exists when it doesn't; the next scheduler tick will crash.

## R3 — PDF page-image checker: deterministic vs. heuristic primitives (FR-014)

**Decision**: Mix two extraction layers:

1. **Text-extracted checks** (via `pdfminer.six`, already in deps): literal LaTeX command strings (`\\\w+\{`), citation glyph patterns (`\[\d+\]` PASS vs. `\(\w+\s*,\s*\d{4}\)` FAIL vs. superscript-number FAIL), section-number monotonicity (extract headings, parse leading numbers).
2. **Pixel-extracted checks** (via `pdf2image` rendering each page to PNG): figure-width measurement — locate figure-box bounding boxes via image segmentation and assert each width is within ±3 px of one of three canonical widths derived from `\figwidth`.

**Rationale**: Most of the user-reported failure patterns are text-level (literal commands, mixed cite styles, section-number gaps). For these, `pdfminer.six` gives a deterministic extraction without rasterizing. The only checker that genuinely needs the rendered image is figure-width verification, because the source-level `\figwidth` macro can be applied correctly in source yet rendered at a different width due to a `\setlength` or `\renewcommand` upstream. We rasterize only the *pages with figures* (cheap heuristic: pages where pdfminer.six's text content contains a `Figure \d+` caption nearby), keeping the average per-page cost low.

**Alternatives considered**:
- (a) All checks at image level via OCR: slow (10-100× slower than text extraction), introduces OCR-error false positives.
- (b) All checks at source `.tex` level: doesn't catch render-time drift (e.g., a `\setlength{\textwidth}{...}` two files away in an `\input{}`).
- (c) Use a tool like `qpdf` for text extraction instead of `pdfminer.six`: `qpdf` is an apt dependency, not a Python lib; adds runtime install fragility.

## R4 — Liveness check semantics (FR-002)

**Decision**: `requests.head(url, allow_redirects=True, timeout=LIVENESS_TIMEOUT_SEC)` where `LIVENESS_TIMEOUT_SEC` defaults to 10. Treat `2xx` and `3xx` (after redirect resolution) as PASS. Specifically:

- arXiv ID `2202.01933` → HEAD `https://arxiv.org/abs/2202.01933`
- DOI `10.1234/example.5678` → HEAD `https://doi.org/10.1234/example.5678`
- raw URL → HEAD the URL directly

Cache key: the raw pointer string (the arXiv ID / DOI / URL itself, not the resolved URL). Cache TTL: 7 days. Cache stored at `state/audit/liveness-cache.json`. Each cache entry: `{pointer: {checked_at_utc, status: pass|fail, http_code: int}}`. On cache hit within TTL, skip the network call.

**Rationale**: HEAD over GET is the standard primary-source-verification pattern (Constitution Principle II is satisfied without downloading the full paper). 7-day TTL balances Principle II (freshness) against Principle IV (avoid hammering arXiv on retries). Cache stored as JSON on the filesystem (not a database) per project storage discipline.

**Alternatives considered**:
- (a) GET instead of HEAD: wastes bandwidth (arXiv PDFs are large); HEAD is sufficient for liveness.
- (b) No cache: every cron tick hammers arXiv/DOI for the same pointers → cost and rate-limit risk.
- (c) Per-pointer dynamic TTL based on response headers: complexity not justified for the audit set's volume.

## R5 — Scheduler concurrency (FR-012)

**Decision**: Replace the current "process one highest-priority project per tick" with a "process up to N highest-priority projects per tick" loop, scoped over distinct project IDs (no two concurrent units may write to the same `state/projects/<id>.yaml`). N is read from `PIPELINE_PARALLELISM` env var, default 8. Implementation: serial execution within a tick (the agent calls are slow but the YAML writes are fast; serial avoids needing a thread/process pool for what is fundamentally an I/O-bound coordination layer), advancing up to N distinct projects per tick.

**Rationale**: The cron tick budget on GitHub Actions free tier is ~5 minutes wall-clock. Each stage advancement is ≤30 seconds (mostly LLM call). Serial advancement of 8 projects per tick fits comfortably; concurrent (thread/process) advancement would introduce file-locking complexity (the existing `pipeline/lock.py` already handles per-project locks but isn't tested under thread contention). Throughput math: 8 projects/tick × 48 ticks/day = 384 advancements/day, well above SC-005's 50/day floor.

**Alternatives considered**:
- (a) Concurrent advancement with `asyncio.gather` over project locks: complexity (per-project file lock, write-collision handling) not justified for the throughput math.
- (b) Multiple concurrent runners (separate GitHub Actions jobs): coordination via state files is fragile; the existing single-runner cron is the simpler invariant.
- (c) Higher default cap (e.g., 16): risks per-tick timeout on large-context LLM calls. 8 is the safe starting point; tunable via env var.

## R6 — PDF audit "source-missing" remediation (FR-018)

**Decision**: When the audit finds a PDF whose source `.tex` isn't recoverable from the repo (no `papers/PROJ-*/main.tex`, no `arxiv_id` recorded in project state for re-fetch), move the PDF to `state/audit/pdf/_quarantine/<YYYY-MM-DD>/<paper-path>` and mark the project's `current_stage` as `paper_review_quarantined` (a new terminal-ish stage that signals human re-review). Do *not* leave the broken PDF under `docs/papers/` where the public site picks it up.

**Rationale**: Public artifact quality is the user's reported concern. A PDF with rendering bugs that can't be fixed deterministically must be removed from `docs/papers/` until either (a) the source is recovered, or (b) a normalizer extension fixes the underlying class of bug. Quarantine preserves the PDF for human review without polluting the public surface.

**Alternatives considered**:
- (a) Leave the broken PDF in place with a warning sticker page prepended: still public; defeats the user's goal.
- (b) Delete the PDF outright: loses traceability for the bug class.
- (c) Re-fetch source from arXiv if `arxiv_id` is recorded: implemented as a sub-step (Option = "source-fixable via re-fetch"); quarantine only when re-fetch also fails.
