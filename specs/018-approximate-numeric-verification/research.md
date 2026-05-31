# Phase 0 Research: Per-Claim Verification Modes

The 4 design decisions were resolved in `/speckit-clarify` (Session 2026-05-30). This file records the **library/behavior verification** (done live 2026-05-30) that de-risks the modes, plus the per-mode mechanics. Every constant value and evaluation below was confirmed with the installed libraries before being committed to the design (FR-013, Constitution II).

## D1 — Library-backed constants (VERIFIED)

- **Decision**: the curated constants table is library-backed: mathematical constants from `math` (+ derived), physical constants from `scipy.constants` (CODATA). Double precision (~15–16 sig figs). The true value is read from the library (deterministic, citable), never the LLM.
- **Evidence (live)**: `math.pi=3.141592653589793`, `math.e=2.718281828459045`, `math.tau=6.283185307179586`, golden ratio `(1+√5)/2=1.618033988749895`; `scipy.constants.c=299792458.0`, `h=6.62607015e-34`, `G=6.6743e-11` (CODATA). Provenance string names the authority (e.g. `math.pi (IEEE-754 double)` / `scipy.constants CODATA`).
- **Coverage**: a small alias map (π/pi, e/Euler's number, τ/tau, φ/golden ratio, c/speed of light, h/Planck, G/gravitational constant, …); unmatched constants fall back to source retrieval.

## D2 — Approximate comparison: round-to-stated-precision (VERIFIED mechanics)

- **Decision**: parse the claimed value's precision (decimal places / sig figs); VERIFIED iff `round(true_value, precision) == claimed_value` (compared **numerically**, then formatted to the claimed precision so "3" not "3.0"); a hedge ("about/~/≈/approximately/roughly/around") widens by one extra place (also accept `round(true, precision±1)`).
- **Evidence (live)**: `round(math.pi,2)=3.14` → "π is 3.14" ✓; `round(math.pi,0)=3.0` (numeric 3) → "π is about 3" ✓ (hedge); "π is 3.15" → `round(π,2)=3.14 ≠ 3.15` ✗; "e is 2.5" → `round(e,1)=2.7 ≠ 2.5` ✗ → corrected to 2.7 (claim precision) or 2.71828 (rendered).
- **Comparison is numeric**: compare `float(claimed)` to `round(true, p)` with a tiny epsilon for float noise; never string-substring (the spec-017 literal gate's failure mode).

## D3 — Computational evaluation via sympy (VERIFIED)

- **Decision**: self-contained claims are **evaluated**, not searched. A safe `sympy` path computes the asserted relation/expression and compares to the asserted result; VERIFIED on match, REFUTED + corrected to the computed value otherwise. Scope (clarified, broadest): arithmetic, comparisons/inequalities, percentages, unit conversions, algebraic identities, set/logic relations.
- **Evidence (live)**: `sympify("1+2")=3`; `bool(sympify("1>2"))=False`; `Eq(1+1,2)=True`; `Rational(30,100)*200=60`; `simplify((x+1)**2 - (x**2+2x+1))==0` → identity True; `convert_to(5*kilometer, meter)=5000*meter`. So "1 plus 2 is 1" → compute 3 → REFUTE+correct to 3; "1 is larger than 2" → False → REFUTE; "5 km is 5,200 m" → 5000 m → REFUTE+correct.
- **Safety (FR-015)**: NEVER `eval`/`exec`. Parse with restricted `sympy` parsing (`parse_expr` with a constrained transformation set / a whitelist, not raw `sympify` on untrusted free text); the LLM only *extracts the expression+asserted-result* from the claim text (a locator, like spec-017), and the **computation is done by sympy/code**. An unparseable/ambiguous claim → fall back to source-based verification or block (never guess).
- **Provenance**: the evaluated expression + computed result (deterministic, reproducible) — the computation is the authority (same trust basis as a library constant), satisfying FR-011.

## D4 — Hybrid mode selection (FR-001)

- **Decision**: deterministic heuristics first, LLM tie-break only when ambiguous. Heuristics: (a) a **self-contained-expression detector** (the claim text is an evaluable relation: contains an operator/comparison/“plus/times/% of/convert/equals” + no external entity) → computational; (b) a **recognized-constant lookup** (subject matches the constants alias map) → approximate-constant; (c) **hedge words or decimal/scientific notation** on a real-valued quantity → approximate; (d) a **bare integer count of discrete things** → exact; (e) otherwise → source-fact. Only genuinely ambiguous cases call the LLM classifier.
- **Default-safe** (edge case): when uncertain between exact and approximate for an integer-valued discrete claim, prefer the **exact** gate (never loosen a count) — protects the 9,988 path (FR-003/SC-002).

## D5 — Magnitude/relational fill (the spec-017 fast-follow)

- **Decision**: enable `MAGNITUDE` + `RELATIONAL` as fillable kinds. The spec-016 `claims/triple.py` `resolve_superlative` (candidate-set + `check_ordering`) and `resolve_relational` (decompose → retrieve → entailment) are check-only; on their NEI/REFUTED, call the spec-017 `_maybe_fill` so the layer searches (Wikidata/Wikipedia/paper), extracts the correct extremum/object, gates it present-in-source, and corrects (or blocks). Route via `channels_for(MAGNITUDE/RELATIONAL)` + `_FILLABLE_KINDS`.
- **Edge (FR-009)**: a claimed object that is one of several sourced-valid objects (multi-valued relation) is VERIFIED, not over-corrected.

## D6 — Reuse map (exact wire-in points, from the Explore pass)

| Need | Reuse / wire-in | Symbol(s) |
|-|-|-|
| numeric sub-triage | `claims/classify.py` (NUMERIC branch) → `verify/mode.py` | `classify`; new `select_mode(claim,*,backend,model,repo_root)` |
| mode-aware gate | `fill/extract.py` | `present_in_source(value, source, kind)` → add approximate branch |
| exact gate (UNCHANGED) | `grounding/service.py`, `agents/grounding_guard.py` | `number_substantiated`, `number_appears_in` |
| superlative/relational | `claims/triple.py` | `resolve_superlative`, `resolve_relational`, `check_ordering`, `decompose_triple` |
| fill dispatch | `claims/resolve.py` | `_maybe_fill(claim, verdict, *, backend, model, repo_root)` (call at MAGNITUDE/RELATIONAL NEI/REFUTED) |
| channels + kinds | `fill/service.py`, `fill/channels/__init__.py` | `_FILLABLE_KINDS`, `_get_channel`, `channels_for`, `AUTHORITY` |
| conflict + citation | `fill/conflict.py`, `fill/citation_repair.py` | `choose`, `repair_citation` |
| render | `claims/pointer.py`, `claims/service.py` | `render`, `process_document` |
| cli flag | `cli.py` | `os.environ.setdefault("LLMXIVE_*","1")` |

## D7 — Testing (FR-013): deterministic-first

- **Offline/deterministic (no network/LLM)**: constants lookup (math/scipy), round-to-precision comparison, sympy evaluation of arithmetic/comparison/%/units/identity/logic, the heuristic mode selector. These are the bulk of correctness and run in the offline gate.
- **Real-call (gated)**: the LLM tie-break classifier on ambiguous claims; the LLM expression/value locator for computational claims; superlative/relational fills (Saturn→Jupiter, Sydney→Canberra) which need real search.
- **No-regress**: the spec-017 exact-count e2e (9,988) stays green; the exact gate is untouched.

**Output**: all decisions resolved with live evidence; no NEEDS CLARIFICATION remain. Proceed to Phase 1.
