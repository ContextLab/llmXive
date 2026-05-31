# Quickstart: Authoritative-Fill / Claim Auto-Correction

## What it does

When an llmXive agent writes a factual value that can't be verified as written, the fill layer finds the correct value from an authoritative source, **confirms the value is literally present in the fetched source**, substitutes it, and repairs the citation — or leaves the claim blocked if no authoritative source has the value. The filled value never comes from the model's memory.

## Prerequisites

- Python 3.11, repo installed (`pip install -e .`).
- Dartmouth key (`llmxive.credentials.load_dartmouth_key()`) for the extractive-locator + real resolution.
- Network access (OEIS b-file, Wikipedia, Wikidata, Semantic Scholar, arXiv, TheoremSearch — all free).
- `LLMXIVE_REAL_TESTS=1` to run real-call tests; `LLMXIVE_CLAIM_FILL=1` to enable the fill in a manual run (set automatically by `cli.run`).

## Verify the headline scenario (27,635 → sourced 9,988)

```bash
export LLMXIVE_REAL_TESTS=1
python -m pytest tests/real_call/test_fill_e2e_real.py -q
```
Asserts: the fabricated "27,635 prime knots at 13 crossings" is corrected to **9,988** drawn from a resolvable source (OEIS A002863 b-file `13 9988`, surfaced via Wikipedia), the rendered document shows 9,988 cited to that source, never shows 27,635, and no human input is requested.

## Use the fill layer programmatically

```python
from llmxive.fill import service as fill
result = fill.fill_claim(claim, backend=backend, model=None, repo_root=repo_root())
if result.status == "filled":
    print(result.value, result.provenance.url, result.provenance.quote)   # "9988", "https://oeis.org/A002863", "13 9988"
else:
    print("blocked:", result.reason)   # no authoritative source had the value
```
In the pipeline this is invoked automatically inside `claims/resolve.py` when a numeric/entity claim can't be verified as written (and `LLMXIVE_CLAIM_FILL=1`).

## Confirm the safety property (no fill from model memory)

```bash
LLMXIVE_REAL_TESTS=1 python -m pytest tests/real_call/test_fill_no_source_blocks_real.py -q
```
Asserts: a claim whose value is **not** present in any fetched source is rejected (not filled) and stays blocked — the `present_in_source` gate (`grounding.number_substantiated`) is the hard boundary.

## Channels & authority

- **OEIS** (b-file by A-number) — integer-sequence/combinatorial counts; highest authority. (Its search API is Cloudflare-blocked; the A-number is surfaced by Wikipedia.)
- **Wikidata** — structured relational/entity statements.
- **Wikipedia** — general reference prose (also surfaces the OEIS A-number).
- **Theorem search** — math-classified claims (reuses the existing TheoremSearch backend).
- **Paper search** — Semantic Scholar + arXiv (lowest authority).

On conflict, the highest-authority channel's value wins and the disagreement is recorded in provenance.

## Offline gate (no network)

```bash
python -m pytest tests/contract tests/integration tests/unit -q -p no:cacheprovider \
  --deselect tests/unit/test_audit_pdf.py::TestPdfAuditorOnLivePdfs
```

## Success signals (map to SC-001…SC-008)

- Fabricated value corrected to a sourced one with provenance (SC-001); zero fills from model memory (SC-002); unknowable claim stays blocked (SC-003); each v1 type corrected, deferred types stay blocked (SC-004); cached reuse + invalidation (SC-005); zero human interventions (SC-006); conflicts recorded per policy (SC-007); citation repaired to the fill source (SC-008).
