# Phase 1 Contracts: Per-Claim Verification Modes

Module-level contracts. New code in `src/llmxive/verify/` + `fill/channels/constants.py`; modifications at the spec-016/017 wire-in points (research D6).

## `verify/mode.py` — hybrid mode selector (FR-001)

```python
def select_mode(claim: Claim, *, backend=None, model=None, repo_root=None) -> str
    # returns "exact" | "approximate" | "computational" | "source"
def looks_self_contained(text: str) -> bool      # PURE heuristic: evaluable expression/relation
def looks_approximate(text: str) -> bool         # PURE heuristic: hedge / decimal / recognized constant
```
**Guarantees**: deterministic heuristics decide when confident (pure, offline-testable); the LLM classifier is consulted ONLY when heuristics are ambiguous (and only with a backend). Default-safe: an integer-valued discrete claim never routes to `approximate` (protects exact counts). Same input → same mode (heuristic path).

## `verify/constants.py` — library-backed constants (FR-004/005)

```python
def lookup(subject: str) -> CuratedConstant | None   # alias match → math/scipy value
def true_value(subject: str) -> float | None
CONSTANTS: dict[str, CuratedConstant]                 # built from math + scipy.constants at import
```
**Guarantees**: values are read from `math` / `scipy.constants` (never hardcoded divergently — a self-test asserts `lookup("pi").value == math.pi`); zero network; provenance names the authority + a resolvable url. Unknown subject → None (caller falls back to retrieval).

## `verify/approximate.py` — precision-aware comparison (FR-002)

```python
def parse_precision(value_text: str) -> PrecisionSpec        # decimals/sig-figs + claimed value
def has_hedge(claim_text: str) -> bool                       # about/~/≈/approximately/roughly/around
def is_valid_rounding(claimed: float, true_value: float, *, decimals: int, hedge: bool) -> bool
def correction(true_value: float, *, decimals: int) -> str   # round(true, decimals), formatted (no "3.0")
```
**Guarantees**: PURE + deterministic. `is_valid_rounding` ⇔ `round(true, decimals) == claimed` (ε-tolerant numeric compare); `hedge` also accepts `decimals±1`. "π 3.14"→True, "π about 3"→True, "π 3.15"→False, "e 2.5"→False. Never string-substring.

## `verify/compute.py` — safe computational evaluator (FR-014/015)

```python
def extract_expression(claim: Claim, *, backend, model, repo_root) -> tuple[str, str] | None
    # (expression, asserted_result) located from the claim — LLM locator only; never computes
def evaluate(expression: str) -> str | None                  # sympy computes; None if not safely parseable
def verify_computational(claim: Claim, *, backend, model, repo_root) -> ComputeVerdict
```
**Guarantees**: `evaluate` uses restricted `sympy` parsing (NO `eval`/`exec`); the COMPUTED value is produced by sympy/code, never the LLM (the LLM only locates the expression+asserted result). Supports arithmetic, comparisons, percentages, unit conversions (`sympy.physics.units`), algebraic identities (`simplify`), set/logic (`sympy.logic`/`sympy.sets`). `not_evaluable` (unparseable/ambiguous) → caller falls back to source/block. `verified` iff `asserted == computed` (reusing approximate tolerance when real-valued).

## `fill/channels/constants.py` — constants as a fill channel

```python
def search_and_fetch(query: str, claim: Claim, *, timeout: float = 30.0) -> list[FetchedSource]
```
**Guarantees**: if the claim's subject matches a curated constant, returns one `FetchedSource(channel="constants", source_id=key, url=authority_url, title=key, text="<value> (<authority>)", authority=AUTHORITY["constants"])`; else `[]`. No network. Slots into `fill/service._get_channel` + `channels_for`.

## Integration contracts (modifications)

- `claims/resolve.py`: a numeric/relational claim is first mode-selected (`verify.mode.select_mode`). `computational` → `verify.compute.verify_computational` (VERIFIED, or REFUTED→fill substitutes the computed value); `approximate` → fill with the constants channel + mode-aware gate; `exact` → unchanged. For `MAGNITUDE`/`RELATIONAL`, after `triple.resolve_*` returns NEI/REFUTED, call the existing `_maybe_fill`.
- `fill/extract.py::present_in_source(value, source, kind)`: when the claim/source indicates approximate mode, compare via `verify.approximate.is_valid_rounding` against the source's number instead of literal `number_substantiated`; exact path unchanged.
- `fill/service.py`: `_FILLABLE_KINDS = {NUMERIC, ENTITY_FACT, MAGNITUDE, RELATIONAL}`; `_get_channel("constants")` wired.
- `fill/channels/__init__.py`: `AUTHORITY["constants"]` high; `channels_for` adds `MAGNITUDE→[wikidata,wikipedia,paper]`, `RELATIONAL→[wikidata,wikipedia,paper]`, and `constants` to NUMERIC/approximate routing.
- `cli.py::run`: `os.environ.setdefault` to enable the spec-018 modes on real runs.
