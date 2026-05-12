# Contract: math-classifier (`is_math_theory_question` / `classify`)

**Module**: `src/llmxive/librarian/math_classifier.py` (NEW)
**Prompt**: `agents/prompts/math_classifier.md` (NEW)
**Consumed by**: `LibrarianAgent.invoke()` (via the `_maybe_math_question(...)` helper in `src/llmxive/agents/librarian.py`)

## Signature

```python
@dataclasses.dataclass(frozen=True)
class MathClassifierResult:
    invoked: bool
    verdict: bool | None
    error: str | None
    cached: bool   # in-memory only; dropped when serialized to the math_classifier audit object

def classify(
    question: str,
    idea_body_excerpt: str | None,
    *,
    project_id: str | None,
    librarian_prompt_version: str,
    model: str,
    default_backend: str,
    fallback_backends: list[str],
    repo_root: "Path | None" = None,
) -> MathClassifierResult: ...

# Thin convenience wrapper (optional):
def is_math_theory_question(...) -> bool:  # returns classify(...).verdict or False
```

## Behavior

`classify(...)` decides whether `question` (optionally informed by `idea_body_excerpt`) is a **pure-mathematics theorem / proof / formal-structure question** — the kind for which TheoremSearch (a theorem-statement search engine) is a useful candidate source.

1. **Cache check** (only if `project_id is not None`): read `state/librarian-cache/math-classifier-verdicts.json` (a flat dict; absent or malformed → treat as `{}`, logged). Key = `f"{project_id}::{librarian_prompt_version}"`. Hit → return `MathClassifierResult(invoked=True, verdict=<cached bool>, error=None, cached=True)` — **no LLM call**.
2. **LLM call**: render `agents/prompts/math_classifier.md` with `question` + `idea_body_excerpt`; call via the existing backend router (`default_backend`, `fallback_backends`, `model` — same plumbing `query_extractor` uses). The prompt instructs: *"Reply with `YES` or `NO` on the first line, then a one-sentence rationale."*
3. **Parse**: first non-empty line, uppercased, `.startswith("YES")` → `verdict = True`; `.startswith("NO")` → `verdict = False`; anything else (unparseable) → **fail open**: `verdict = False`, treat as an error-ish case but with `error=None` and a logged warning ("[math-classifier] unparseable response, defaulting to non-math: <first 80 chars>"). *(Design choice: an unparseable-but-returned response is treated as `verdict=False, error=None` — distinct from a backend failure which sets `error`.)*
4. **On backend failure** (router raises, all fallbacks exhausted, timeout, etc.): **fail open** — `MathClassifierResult(invoked=True, verdict=False, error="<exception message>", cached=False)`, AND write a **loud** stderr diagnostic: `[math-classifier] backend failure; treating question as non-math (TheoremSearch skipped): <error>` (matching the existing `[arxiv]` / `[query-extractor]` logging style). Do NOT re-raise — the librarian must proceed on SS+arXiv.
5. **Cache write** (only if `project_id is not None` AND the verdict was freshly computed without error): store `{key: {"verdict": verdict, "classified_at": <ISO-8601 UTC>}}`, merge-write the JSON file. (Do not cache error outcomes — a transient backend blip shouldn't poison the cache; the next run retries.)
6. Return the `MathClassifierResult`.

## Caller contract (`_maybe_math_question` in `librarian.py`)

```python
def _maybe_math_question(term, idea_body_excerpt, project_id, prompt_ver, entry, repo_root) -> tuple[bool, dict]:
    res = math_classifier.classify(
        term, idea_body_excerpt,
        project_id=project_id, librarian_prompt_version=prompt_ver,
        model=entry.default_model,
        default_backend=entry.default_backend.value,
        fallback_backends=[b.value for b in entry.fallback_backends],
        repo_root=repo_root,
    )
    audit = {"invoked": res.invoked, "verdict": res.verdict, "error": res.error}
    return (bool(res.verdict), audit)
```

When `field ∈ {"mathematics", "statistics"}`, `_maybe_math_question` is **not called** — the librarian sets `audit = {"invoked": False, "verdict": None, "error": None}` and queries TheoremSearch unconditionally.

## The `math_classifier` audit object (in `LibrarianResult` JSON)

The serialized form: `{"invoked": bool, "verdict": bool | null, "error": str | null}` — exactly the in-memory `MathClassifierResult` minus `cached`. Placed in `LibrarianResult.to_dict()` alongside `relevance_judge`, `extracted_queries`, `per_query_hit_count`. See `librarian-json-output-delta.md`.

## Test obligations (→ `tests/phase2/test_math_classifier.py`)

- **Parser**: `"YES\nbecause it's about a theorem"` → `verdict True`; `"NO\nit's an empirical ML question"` → `verdict False`; `"hmm, maybe?"` (unparseable) → `verdict False, error None` + warning logged.
- **Cache hit**: two `classify(...)` calls with the same `(project_id, librarian_prompt_version)` → second returns `cached=True` and does NOT call the LLM (assert via a monkeypatched/recording backend, or by checking the cache file was read not written on the 2nd call).
- **Cache miss on prompt-version change**: same `project_id`, different `librarian_prompt_version` → second call is a miss (re-classifies).
- **`project_id=None`** → no cache read/write; classifier runs every call.
- **Backend failure** → `verdict False, error "<msg>"`, stderr diagnostic emitted, no exception propagated, cache NOT written.
- **Real-LLM smoke** (gated on `DARTMOUTH_CHAT_API_KEY` + `LLMXIVE_REAL_TESTS=1`): a plainly-math question ("what is the tightest known concentration inequality for sums of bounded independent random variables, and in which paper is it proved?") → `verdict True`; a plainly-non-math question ("how does code-clone density correlate with LLM perplexity on Python?") → `verdict False`.
