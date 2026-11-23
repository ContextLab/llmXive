# Credit-reservation ledger — operations runbook (spec 026 / FR-016)

The paid-model **credit-reservation ledger** makes the fractional daily-budget cap
atomic across every runner: a paid call reserves its `worst_case_credits` in an
authoritative, append-only ledger before the provider call, so concurrent calls —
same process or across CI runners — can never collectively overspend
(`backends/credits.py` + `model_selection/{ledger_transport,reservations}.py`).

Paid calls are OFF by default (`LLMXIVE_PAID_OPT_IN` unset). This runbook covers
what an operator must configure to turn them on **safely**. Until it is done, paid
execution and the maintenance sweep **fail closed** (paid disabled) — never a
silent local-only reservation.

## The authoritative ref

- Ref: **`refs/llmxive/credit-ledger`** — a standalone, append-only ref (NOT a
  working branch). Events live at `reservations/<schema_revision>/<event-id>.json`
  and are projected into reservation state.
- All reads and mutations go through a **strict per-record CAS** (fetch → rebuild
  projection → verify predicate against fresh spend → append-only → fast-forward
  push → recompute on rejection). This is NOT `commit-and-push.sh`.

## One-time bootstrap (admin)

Run ONCE, by a maintainer with push access to the ref:

```
llmxive credits-ledger-bootstrap --remote origin
```

It creates the ref with an empty anchor commit and **prints the anchor OID**.
Record that OID — it is the pinned trust anchor for every subsequent read/write.

## Required configuration (both execution and maintenance)

Set these wherever paid execution OR the sweep runs (CI secrets / job env):

| Env var | Meaning |
|-|-|
| `LLMXIVE_PAID_OPT_IN=1` | master switch for paid calls (off by default) |
| `LLMXIVE_CREDIT_LEDGER_REMOTE` | git remote holding the ref (default `origin`) |
| `LLMXIVE_CREDIT_LEDGER_ANCHOR` | the bootstrap anchor OID printed above |

`ledger_transport.ledger_config_from_env()` is the single source that reads these.
`execute()` (paid path) and `credits-ledger-sweep` both build their `LedgerConfig`
from it, so they share the **same** remote + anchor. Without the anchor, both fail
closed. `LLMXIVE_PAID_BUDGET_FRACTION` (default `0.75`) bounds the fraction of the
daily budget paid calls may consume.

## Server-side ref protection (deploy-time — REQUIRED)

The CAS guarantee assumes the ref cannot be force-rewritten or written by an
untrusted identity. Configure on the host (e.g. a GitHub ruleset / protected-ref
rule on `refs/llmxive/credit-ledger`):

- **fast-forward-only** — reject non-fast-forward / force pushes (a force-rewrite
  between `ls-remote` and fetch is what the pinned-anchor ancestry check guards
  against in-repo; server-side protection makes it impossible).
- **writable only by the ledger identity** — the token/app that performs reservations
  and the sweep. No other principal may append.
- token identity: the same GitHub App / bot identity used for pipeline commits, with
  push permission scoped to `refs/llmxive/*`.

## Maintenance sweep

Run on a maintenance cron (reads the same env):

```
llmxive credits-ledger-sweep --remote origin
```

It conservatively settles crashed in-flight reservations, discards prior-epoch
holds at the daily reset, and reconciles the current-epoch settling batch against
freshly-observed provider spend (attribution-prefix rule). Idempotent; safe to run
repeatedly. Use `--no-remote` only for local/single-runner testing.

## Fail-closed summary

- No `LLMXIVE_CREDIT_LEDGER_ANCHOR` → `execute()` skips every paid candidate and the
  sweep errors. Paid fallback stays disabled (never a local-only reservation).
- Unreachable / wrong remote, or a tip that does not descend from the pinned anchor
  → `LedgerAuthError`, fail closed.
- Ledger unreachable at call time → the paid candidate is skipped, the chain
  advances to free candidates (or `ChainExhausted`). No paid call proceeds without a
  verified ledger.

## Funded ledger (spec 027)

The real-money (Hugging Face) spend is reserved and settled on a SEPARATE ref,
`refs/llmxive/funded-ledger`, using the same CAS transport and event schema as the
credit ledger (`LedgerConfig(ref=...)`). Differences:

- Units: every amount field (`worst_case_credits`, `settlement_baseline`, `charged`) is **USD**.
  Field names are the shared schema's and are not renamed.
- Epoch: `budget_epoch` is the calendar month `YYYY-MM` (UTC).
- Bootstrap (one-time admin): `llmxive funded-ledger-bootstrap [--remote origin | --no-remote]`;
  it prints the anchor to pin.
- Configuration: `LLMXIVE_FUNDED_LEDGER_REMOTE` (default `origin`) and
  `LLMXIVE_FUNDED_LEDGER_ANCHOR` (required; fail closed when unset), read by
  `funded_ledger_config_from_env()`.
- Protection: the same server-side rule as the credit ledger — fast-forward-only, writable
  only by the ledger identity (see "Server-side ref protection" above).
- No sweep: a crashed `open` hold keeps counting at its full reservation until the month
  ends, which is exactly the charge for a call without `usage` (spec 5.9.2).
- 401/402/403 responses are reconciled at zero (`reconcile(..., charged=0.0)`); the first
  reconcile wins and later ones are no-ops.
