# Phase 0 Research — TheoremSearch backend + mathematics field (spec 006, amends spec 005)

No `NEEDS CLARIFICATION` markers remained after `/speckit-clarify`. The items below are integration-pattern decisions, not unknowns. Each is **Decision / Rationale / Alternatives considered**.

---

## D1 — TheoremSearch `/search` response shape and what the librarian consumes

**Decision**: `POST https://api.theoremsearch.com/search` with body `{"query": <term>, "limit": <N>}` returns `{"theorems": [<hit>, ...]}`. Each `<hit>` is `{theorem_id, name, body, slogan, theorem_type, label, link, paper: {paper_id, source, title, authors, link, summary, journal_ref, primary_category, categories, citations, year, journal_published}, similarity, score, has_metadata}`. The librarian consumes **only** `hit.paper` (and only when `hit.paper.source == "arXiv"`) plus `hit.score` (for ordering). It ignores `theorem_id / name / body / slogan / theorem_type / link` — those are Spec B (#114) territory.

**Rationale**: Confirmed by live probing (notes on issue #111): a query for "every finite group has a composition series" returned ProofWiki hits with `paper.source == "ProofWiki"`, `paper.link == "https://proofwiki.org/wiki/..."`, `paper.paper_id == "proofwiki"`, all paper-level metadata fields `null`/empty; a query for "sharp bound spectral gap random regular graphs" returned arXiv hits with `paper.source == "arXiv"`, `paper.paper_id == "1306.5434v2"` (versioned), `paper.link == "http://arxiv.org/abs/1306.5434v2"`, `paper.year == 2014`. The OpenAPI spec at `https://api.theoremsearch.com/openapi.json` lists `POST /search` plus `GET /paper/{paper_id}`, `GET /paper-search`, `POST /statements`, `GET /statement/{statement_id}`, `GET /graph/*`, and a `/mcp` server. No auth, no documented rate limits. Spec A needs none of the non-`/search` endpoints — `paper.paper_id` + `paper.link` are sufficient because the librarian's existing `ArxivClient.get_by_id` resolves the rest.

**Alternatives considered**: (a) Use `GET /paper/{paper_id}` to fetch the paper record directly from TheoremSearch instead of round-tripping to arXiv — rejected: adds a second TheoremSearch call and a dependency on TheoremSearch's metadata being complete, when the librarian already has a battle-tested arXiv resolver. (b) Use the `/mcp` server — rejected: the librarian's backends are plain HTTP clients; introducing an MCP dependency for one backend is disproportionate.

---

## D2 — arXiv-ID version-suffix handling

**Decision**: `paper.paper_id` from TheoremSearch is the *versioned* arXiv ID (`1306.5434v2`). The librarian strips the `vN` version suffix with `re.sub(r"v\d+$", "", paper_id)` before resolving — but note this is belt-and-suspenders: `ArxivClient.get_by_id` already accepts both `'1706.03762'` and `'1706.03762v3'` (its docstring says so, and it normalizes via `arxiv.Search(id_list=[arxiv_id])` then `_arxiv_short_id(result.entry_id)`). The librarian calls `arxiv_client.get_by_id(stripped_id)`; if it returns `None`, the candidate is dropped with a logged warning (same handling as any unresolvable arXiv candidate). The returned `Candidate` has `backend="arxiv"` — the TheoremSearch client **re-tags it** to `backend="theoremsearch"` (and keeps `primary_pointer` = the resolver-normalized short ID, so dedup against an arXiv-sourced copy of the same paper works).

**Rationale**: Confirmed by reading `src/llmxive/librarian/search.py:get_by_id` — it accepts versioned IDs and normalizes. Stripping first is harmless and makes the intent explicit. Re-tagging is the one-line difference that lets the output JSON show "this citation came via TheoremSearch" while everything downstream treats it identically to an arXiv candidate.

**Alternatives considered**: (a) Don't strip, pass the versioned ID through — rejected: `get_by_id` handles it but downstream dedup keys on `primary_pointer`; if TheoremSearch returns `1306.5434v2` and arXiv search returns `1306.5434`, they wouldn't dedup. Letting `get_by_id` normalize and using its returned `primary_pointer` fixes this. (b) Keep `backend="arxiv"` — rejected: loses the provenance signal the spec (FR-A02, SC-A01) requires.

---

## D3 — Math-classifier verdict cache: location and format

**Decision**: A single JSON file `state/librarian-cache/math-classifier-verdicts.json`, a dict mapping `f"{project_id}::{librarian_prompt_version}"` → `{"verdict": bool, "classified_at": "<ISO-8601>"}`. On a librarian invocation with a `project_id`: look up `f"{project_id}::{prompt_version}"`; hit → use the cached verdict, no LLM call; miss → call the classifier, store the result. When `project_id` is `None` (standalone smoke test), skip the cache entirely (classifier runs every time). The key includes `librarian_prompt_version`, so a `prompt_version` bump automatically invalidates all entries (a re-run re-classifies — which is correct, since the librarian prompt may have changed how it phrases questions).

**Rationale**: Per Clarifications 2026-05-12 the cache is keyed by `(project_id, librarian_prompt_version)`. A single JSON file is the simplest thing that works — math projects are rare (5 seed projects + whatever the brainstorm agent later adds), so the file stays tiny and human-inspectable. It lives under `state/librarian-cache/` next to the existing sha256-keyed result cache, so cache-management (wiping for a clean re-run) is one directory. Composite key as a string `"{project_id}::{version}"` avoids nested-dict bookkeeping.

**Alternatives considered**: (a) One file per key under `state/librarian-cache/math-classifier/<key>.json` — rejected: filesystem churn for a handful of entries; harder to eyeball. (b) Reuse the existing sha256-keyed result cache with a synthetic key — rejected: that cache stores `LibrarianResult` shapes keyed by normalized term; shoehorning a boolean into it muddies that cache's contract. (c) Per-question key (sha256 of normalized question) — rejected at /speckit-clarify (per-project chosen; avoids a second keying scheme).

---

## D4 — Where the TheoremSearch / math-classifier branch slots into `LibrarianAgent.invoke()`

**Decision**: After the existing extracted-query search loop (which builds `candidates: list[Candidate]` with a `merged_pointers: set[str]` for dedup) and **before** the call to `_verify_each(candidates, query=term)`. The branch:

```
# (existing: candidates + merged_pointers populated from SS + arXiv over all_queries)
ts_hits: list[Candidate] = []
math_audit = {"invoked": False, "verdict": None, "error": None}
if field in ("mathematics", "statistics"):
    ts_hits = _theoremsearch_candidates(term)            # always; classifier NOT invoked
elif _maybe_math_question(term, idea_body_excerpt, project_id, prompt_ver, ...):
    # _maybe_math_question internally fills math_audit and consults the per-project cache
    ts_hits = _theoremsearch_candidates(term)
for c in ts_hits:
    if c.primary_pointer in merged_pointers:
        continue
    merged_pointers.add(c.primary_pointer)
    candidates.append(c)
# (existing: verified, failures = _verify_each(candidates, query=term); expansion; relevance judge; pdf sample; ...)
```

`_theoremsearch_candidates(term)` wraps `TheoremSearchClient().search(term)` and swallows `TransientBackendError` → returns `[]` (the librarian must complete normally when TheoremSearch is down — FR-A06). `_maybe_math_question(...)` wraps `math_classifier.is_math_theory_question(...)`, populates `math_audit`, and uses the per-project cache. The `math_audit` dict is then passed into the `LibrarianResult` constructor as `math_classifier=math_audit` (parallel to the existing `relevance_judge=...`, `extracted_queries=...`).

**Rationale**: Slotting before `merge_candidates`/`_verify_each` means TheoremSearch candidates participate in dedup (a paper found by both arXiv and TheoremSearch appears once) and go through the *exact* same verify → expand → judge → PDF-sample pipeline as everything else — zero chain changes (the constraint in FR-A02). Putting it after the extracted-query loop (rather than interleaved) keeps the math path a clean, self-contained block that's trivial to test in isolation. The `math_audit` dict mirrors how `relevance_judge` / `extracted_queries` are already threaded into `LibrarianResult.to_dict()`.

**Alternatives considered**: (a) Run TheoremSearch as a peer inside the `for q in all_queries` loop (one TheoremSearch query per extracted query) — rejected: TheoremSearch is semantic, not keyword — one query with the full research question is the right granularity; 5 fragmented theorem queries would be worse, and 5× the API calls. (b) Run it as a separate post-verification step that adds candidates and re-runs the verify chain — rejected: re-running the chain is wasteful and risks double-verifying SS/arXiv candidates.

---

## D5 — `project_id` plumbing through `LibrarianAgent.invoke()`

**Decision**: Add `project_id: str | None = None` to `LibrarianAgent.invoke()`'s signature (after the existing kwargs, before the clients). The main caller — `flesh_out` in `src/llmxive/agents/idea_lifecycle.py` — already has the project_id (it's building the idea for a specific project) and passes it through. `reference_validator` (the other rewired caller) also has it. Tests and standalone smoke probes may omit it (`None` → the math-classifier runs without caching, which is fine for a one-shot test). The `project_id` is used **only** for the math-classifier verdict cache key — it does not affect search, verification, or the output JSON shape (other than being recorded nowhere; the `math_classifier` audit object records `invoked`/`verdict`/`error`, not the project_id).

**Rationale**: The classifier cache key per Clarifications is `(project_id, librarian_prompt_version)` — the librarian needs the project_id to compute it. An optional kwarg with a `None` default is the minimal, backward-compatible change: existing callers that don't pass it (including the soft-deprecated `lit_search` shim and any tests) keep working; the classifier just doesn't cache for them. `flesh_out` and `reference_validator` are the callers that *do* have a project_id and *should* benefit from the cache, so they pass it.

**Alternatives considered**: (a) Derive project_id from `repo_root` + something — rejected: brittle, and not all invocations are in a project context. (b) Make `project_id` required — rejected: breaks the standalone-smoke-test and shim use cases for zero benefit. (c) Cache by `idea_body_excerpt` hash instead of project_id — rejected at /speckit-clarify (per-project chosen).

---

## Carried-forward known issue (not resolved here, tracked separately)

The LLM relevance judge — and now the math-classifier — is **non-deterministic** (temperature > 0): the same question can yield different verdicts across runs. Tracked in **GitHub issue #112** (recommended fix: temperature=0 on the judge/classifier calls). This amendment does not fix it; the math-classifier's fail-open-to-`false` + per-project verdict cache bounds the impact (a missed trigger → TheoremSearch not consulted that run → SS+arXiv still cover the question; and once a project's verdict is cached it's frozen for that `prompt_version`).
