# Phase 1 Contracts: Semantic Substantiation Gate

Function contracts for the new/changed interfaces. These are the buildable
surface `/speckit-tasks` decomposes. Signatures are concrete; behavior is the
contract its tests assert.

## C1 — Channel classifier (`fill/channels/__init__.py`)

```python
STRUCTURED_CHANNELS: frozenset[str]   # = {"constants", "oeis", "wikidata"}

def is_structured(channel: str) -> bool:
    """True iff the channel's data structure makes the subject↔value link
    inherent (constants alias table / OEIS b-file by index / Wikidata triple)."""

def is_prose(channel: str) -> bool:
    """True iff the channel is free prose where a value can coincidentally
    appear. Defined as `not is_structured(channel)` so an unknown channel is
    PROSE (fail-closed)."""
```

**Contract**:
- `is_structured(c)` for `c in {"constants","oeis","wikidata"}` → `True`.
- `is_prose(c)` for `c in {"wikipedia","theorem","paper"}` → `True`.
- `is_prose("anything-unrecognized")` → `True` (fail-closed).
- `is_structured(c) != is_prose(c)` for every string `c`.

## C2 — Public subject keywords (`claims/canonical.py`)

```python
def subject_keywords(claim: Claim) -> list[str]:
    """Sorted, deduplicated, lowercase, singularized, digit-free, stop-word-free
    subject tokens for *claim*. (Promotion of the former private
    `_subject_keywords`; single implementation.)"""
```

**Contract**: identical output to today's `_subject_keywords`; all prior internal
callers updated to the public name; no behavior change.

## C3 — Prose substantiation gate (`fill/relevance.py`, NEW)

```python
@dataclass(frozen=True, slots=True)
class _SourceDoc:
    full_text: str
    abstract: str = ""

def prose_substantiated(
    value: str,
    source: FetchedSource,
    claim: Claim,
    *,
    backend: Any,
    model: str | None,
    repo_root: Path | None,
) -> bool:
    """Semantic substantiation for a PROSE-channel candidate. Returns True ONLY
    when BOTH hold:
      1. (deterministic, zero-network) at least one of `subject_keywords(claim)`
         co-occurs within ±_WINDOW chars of some occurrence of `value` in
         `source.text` (numeric → `_number_anchor_re(value)`; entity → normalized
         substring). No co-occurrence → False (no LLM call).
      2. `assess(claim.canonical or claim.raw_text, _SourceDoc(source.text),
         backend=backend, model=model, repo_root=repo_root).status == "grounded"`.
    Any failure, `contradicted`, `not_found`, missing backend, or exception → False
    (fail-closed)."""
```

**Contract**:
- Subject keywords absent near every occurrence of `value` → `False`, and `assess`
  is NOT called (assert via a recording/None backend in unit tests).
- `backend is None` → `False` (cannot substantiate prose without entailment).
- `assess` returns `grounded` → `True`; `contradicted`/`not_found`/raises → `False`.

## C4 — Single trust boundary (`fill/extract.py`)

```python
def _accept(
    candidate: str,
    source: FetchedSource,
    claim: Claim,
    *,
    backend: Any,
    model: str | None,
    repo_root: Path | None,
) -> bool:
    """The one admission gate. True iff present_in_source AND (channel is
    STRUCTURED, OR prose_substantiated for a PROSE channel)."""
```

**Contract**:
- STRUCTURED channel: `_accept == present_in_source(candidate, source, claim.kind)`
  (byte-for-byte today's behavior; no LLM call) — FR-004.
- PROSE channel: `_accept == present_in_source(...) and
  prose_substantiated(...)`.
- `extract_value` returns the candidate iff `_accept(...)` is True, at BOTH the
  offline (`backend is None`) and LLM admission sites.

## C5 — Claim-kind pre-guard (`fill/service.py::fill_claim`)

```python
# inserted after the existing kind guard, before cache/fetch:
#   NUMERIC claim whose asserted value is a bound/percent  → blocked (no fetch)
#   NUMERIC claim asserting no numeric token (digit-less)  → blocked (no fetch)
```

**Contract**:
- `fill_claim` on "braid index ≤ crossing number …" (bound) → `FillResult`
  `status="blocked"`, and NO channel fetch / `subject_query` runs (assert via a
  recording backend / fetch counter) — FR-002/SC-006.
- `fill_claim` on a digit-less NUMERIC claim → `status="blocked"`, no fetch —
  FR-003.
- Non-bound, digit-bearing NUMERIC and all STRUCTURED-resolvable claims are
  unaffected (e.g. 9988 still fills) — FR-009/SC-002.

## C6 — `conflict.choose` (UNCHANGED — documented invariant)

No signature change. Documented invariant: `choose` only ever receives candidates
that passed `_accept`; therefore a relevance-failing PROSE candidate is never
ranked, and an empty candidate list (all PROSE failed, no STRUCTURED) blocks the
fill upstream — FR-008 satisfied by construction (see research D6).
