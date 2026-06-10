# Written cost justification — credit-managed paid Dartmouth models

Constitution Principle IV requires that any paid path be (a) technically
necessary, (b) justified in writing, and (c) encapsulated. This document
is the written justification for the credit-managed `paid_opt_in`
backend path (issue #295, scope item 3).

## What was measured (live, 2026-06-10)

| Fact | Value | Evidence |
|-|-|-|
| Balance endpoint | `GET https://chat.dartmouth.edu/api/v1/credits/balance` | returns `{"account":"Personal","spend":…,"max_budget":2000.0,"budget_duration":"1d","budget_reset_at":"2026-06-11T03:45:00Z"}` |
| Daily budget | 2000.00 credits, renews daily 03:45Z (11:45 PM ET) | matches maintainer's report on #295 |
| Credit unit | **1 credit = $0.001 USD list-price equivalent** | a real claude-haiku call (12 prompt + 4 completion tokens, catalog $1/M-in $5/M-out → $0.000032) moved `spend` by exactly 0.032 credits — ratio 1000.0 |
| Daily ceiling | ≈ **$2.00/day** of list-price usage | 2000 × $0.001 |
| Catalog prices | real list prices in `model_info` (haiku $1/$5, sonnet $3/$15, opus $5/$25, gpt-5.5 $5/$30 per Mtok) | `GET /api/models` |
| Metering | asynchronous, lags seconds–tens of seconds | poll in `test_tiny_paid_call_end_to_end` |
| Actual dollars charged to the project | **$0.00** | credits are an institutional daily allocation; unused credits do not roll over |

## Why this satisfies Constitution IV

- **(a) Necessity:** the audit (#294) identified the hardest stages
  (deep paper review) as quality-limited on free models; the maintainer
  explicitly directed (issue #295 comment) that daily credits "could
  still satisfy the 'free' requirement, as long as the credits are
  (a) managed carefully and (b) not exceeded."
- **(b) Written justification:** this document; per-agent flips of
  `paid_opt_in: true` each require their own justification in the
  introducing PR (enforced by the registry pin test
  `test_every_agent_is_paid_opt_in_false`).
- **(c) Encapsulation:** the entire paid path is contained in
  `src/llmxive/backends/credits.py` + one guard block in
  `DartmouthBackend.chat`. Removing the env switch restores strict
  free-only behavior with zero other changes; no agent, router, or
  lifecycle code knows about credits.

## Management controls ("carefully managed, never exceeded")

1. **Default OFF** — paid calls require `LLMXIVE_PAID_OPT_IN=1` at the
   process level; nothing in CI or cron sets it.
2. **Budget cap with reserve** — calls are refused once `spend` reaches
   `LLMXIVE_PAID_BUDGET_FRACTION` (default 0.75) × `max_budget`,
   leaving a 25% reserve so accounting lag / concurrent runs cannot
   overshoot the daily budget.
3. **Fail-closed** — if the balance endpoint is unreachable or returns
   an unexpected shape, paid calls are refused. Free models never
   consult the credit layer.
4. **Honest accounting** — opted-in calls log their real list-price
   estimate (`cost_estimate_usd = tokens × catalog price`); the run-log
   invariant still hard-fails any non-zero cost outside the opt-in.
5. **Observability** — `llmxive credits` shows live spend / cap / reset.
