# Phase 1 Data Model: Per-Claim Verification Modes

Mostly **transient** — the new modes annotate the existing spec-016 `Claim` (its `evidence`, `resolved_value`) and reuse spec-017 `FetchedSource`/`FillProvenance`/`FillResult`. New value objects live in `src/llmxive/verify/`.

## Entity: VerificationMode (enum/string)

Per-claim selection: `exact` | `approximate` | `computational` | `source`. Chosen by `verify/mode.select_mode`. Not persisted as a schema field — derived per pass and recorded in `Claim.evidence["mode"]` for inspection.

## Entity: CuratedConstant

A recognized constant in the library-backed table (`verify/constants.py`).

| Field | Type | Notes |
|-|-|-|
| `key` | str | canonical name (`pi`, `e`, `tau`, `golden_ratio`, `speed_of_light`, …) |
| `aliases` | list[str] | match forms ("π","pi"; "c","speed of light") |
| `value` | float | the true value (math / scipy.constants), double precision |
| `authority` | str | citable authority (`math.pi (IEEE-754)`, `scipy.constants CODATA`) |
| `url` | str | a resolvable reference for the authority (cited in provenance) |

**Validation**: `value` is read from the library at load time (never hardcoded divergently); a claim's subject must match an alias to use this source, else fall back to retrieval.

## Entity: PrecisionSpec (`verify/approximate.py`)

Parsed from an approximate claim's value text.

| Field | Type | Notes |
|-|-|-|
| `claimed` | float | the asserted value |
| `decimals` | int | decimal places stated (`3.14`→2, `3`→0) |
| `sig_figs` | int | significant figures (for scientific/large) |
| `hedge` | bool | a hedge word/symbol present ("about", "~", "≈", …) |

**Rule (FR-002)**: VERIFIED iff `round(true, decimals) == claimed` (numeric, ε-tolerant); with `hedge`, also accept `round(true, decimals±1)`. Correction value = `round(true, decimals)` formatted to the claimed precision.

## Entity: ComputeVerdict (`verify/compute.py`)

The outcome of evaluating a self-contained computational claim.

| Field | Type | Notes |
|-|-|-|
| `evaluable` | bool | the claim parsed as a safe self-contained expression/relation |
| `status` | enum | `verified` \| `refuted` \| `not_evaluable` |
| `asserted` | str | the result the claim asserts |
| `computed` | str | the value sympy computed (deterministic) |
| `expression` | str | the normalized expression evaluated (provenance) |

**Rule (FR-014/015)**: `evaluable` requires a safe parse (no `eval`/`exec`); `not_evaluable` → fall back to source-based verification or block (never guess). `status=verified` iff `asserted == computed` (numeric/symbolic equality, reusing approximate tolerance when real-valued). Provenance = `expression` + `computed`.

## Mapping to spec-016 Verdict / spec-017 fill

- **computational** → a resolver path returning `Verdict(VERIFIED, value=asserted, evidence={"mode":"computational","compute":{expression,computed}}, resolver="compute")` on match; `Verdict(REFUTED…)` then a fill that substitutes `computed` on mismatch; `not_evaluable` → original NEI/REFUTED (source path).
- **approximate** → uses the constants channel (a `FetchedSource` whose `text` carries the true value) + the mode-aware `present_in_source` (round-to-precision); a verified value renders the claimed-precision value, a refuted one corrects to `round(true, decimals)`.
- **exact** → unchanged spec-017 path (`number_substantiated`).
- **magnitude/relational** → spec-016 `triple` resolvers + spec-017 `_maybe_fill`; `_FILLABLE_KINDS += {MAGNITUDE, RELATIONAL}`; `channels_for` routes them.

## Reused entities (unchanged)

`Claim` / `ClaimRegistry` / `Verdict` / `FetchedSource` / `FillProvenance` / `FillResult` from specs 016/017. The constants channel emits a `FetchedSource(channel="constants", source_id=<key>, url=<authority url>, text=<value + authority>, authority=AUTHORITY["constants"])`. `AUTHORITY["constants"]` is the **top rank** (≤ `oeis`=0) since a library constant is the primary/definitional authority for the constants it covers (it wins any conflict — FR-005).
