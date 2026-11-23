# Spec 027 — Hugging Face as a funded fallback provider, with leaderboard-ranked, cost-paced model selection

Status: approved by the maintainer 2026-11-23 (design, funded-tier classification,
Hugging Face ranked ahead of the local model, three-day borrow-ahead, and the
constitution paragraph in section 6). Selection was revised the same day (section 5.10):
there are no score floors and no per-profile cost ceilings; where sections 5.3-5.6, 7
and 8 mention them, 5.10 governs.

## 1. Intent

Dartmouth Chat, llmXive's only capable free backend, is down until further notice
(maintainer, 2026-11-23). The pipeline must keep working by serving its internal model
calls through the lab's Hugging Face subscription whenever Dartmouth is unavailable, must
choose the model for each call from live quality data and the scope of the task rather
than from a hand-pinned name, and must do so inside a fixed monthly budget.

## 2. Goals, non-goals, anti-goals

Goals
- G1. When no free backend can serve a call, a Hugging Face Inference Providers model
  serves it, with no change at the call site (call sites already name a spec-026 profile).
- G2. Model choice is dynamic: quality comes from public leaderboard data refreshed at
  run time; capability flags and prices come from the live Hugging Face catalog.
- G3. Spend never exceeds a configured monthly allowance (default **$50**), paced by day.
  When the allowance is used up, calls stop cleanly as an outage, never as a silent
  downgrade and never as a human escalation.
- G4. Dartmouth is still preferred whenever it is up (it is free).
- G5. Every decision records which model, which provider, what it was expected to cost
  and what it did cost.

Non-goals
- Finishing spec 025 (self-improvement lane); any alphaXiv-derived review mechanism.
- Hugging Face Jobs / storage (issues #1241, #1285).
- Re-enabling schedules. Runs stay manual (maintainer ruling 2026-11-23).

Anti-goals (a build that does these has failed even if tests pass)
- Recording a metered call as free.
- A second model-selection mechanism beside spec 026's snapshot → select → execute.
- A leaderboard outage or a renamed model silently promoting an unvetted model into a
  review or code role.
- Spending past the allowance because two runners raced.

## 3. Constraints and verified facts (all checked 2026-11-23)

- Router: `https://router.huggingface.co/v1` (OpenAI-compatible chat). A call succeeds
  only with header `X-HF-Bill-To: <llmxive resource-group id>` (id recorded in
  `scripts/hf/README.md`); billing to the personal account or to the org name returns
  HTTP 402 `PrepaidCreditsRequired`. Real call `openai/gpt-oss-120b:cheapest` → 200.
- Catalog: `GET https://router.huggingface.co/v1/models`, no key. 158 models; each has
  `providers[]` with `pricing.input`/`pricing.output` in USD per **million** tokens,
  `context_length`, `supports_structured_output`, `supports_tools`, `status`,
  `uptime_last_day_percent`, `throughput`; `architecture.input_modalities` marks vision.
  No provider entry is free today.
- Credits: `GET https://huggingface.co/api/organizations/contextlab/billing/credits`
  (token scope `org.billing.read`) → `{"balanceUsd": 199.99…, "balances":[{"name":"Team
  Included Credits (monthly)","expiresAt":"2026-12-01…"}]}`. That balance is the whole
  org's, not llmXive's. The resource group's own limit ($20 as recorded in October) is
  not readable with the current token (403) and is raised only in the HF settings UI.
- The token in CI is the `HF_TOKEN` Actions secret. Locally the pilot helper reads
  `HF_TOKEN` or the macOS Keychain service `llmxive-huggingface`.
- Leaderboards that returned parseable data without a key today:
  - OpenRouter `https://openrouter.ai/api/v1/models` — rows carry `hugging_face_id`
    (exact repo id; 186 models) and a `benchmarks.artificial_analysis` object
    (`intelligence_index`, `coding_index`, `agentic_index`, …; 132 models have both).
  - LMArena `lmarena-ai/leaderboard-dataset` on the Hub (CC-BY-4.0; configs text, vision,
    document, webdev, agent; display names, not repo ids).
  - Epoch `https://epoch.ai/data/benchmark_data.zip` (CC-BY; includes SciCode).
  - No machine-readable leaderboard scores peer-review or scientific-writing ability.
- Unverified: terms for automated reuse of the Artificial Analysis numbers embedded in
  OpenRouter's listing; router rate limits (no documentation page exists).
- Spec 026 today: `policy.py` is a reviewed `family → PolicyEntry(capabilities, features,
  quality_tier, max_context_tokens)` table and states that catalog presence is never
  proof of competence; `select()` orders free-before-paid, then quality tier; paid
  admission needs `allow_paid`, a live credit observation and the opt-in flag; the credit
  guard reads Dartmouth's balance only.

## 4. Approaches considered

A. **Funded tier inside spec 026 (chosen by the maintainer, 2026-11-23).** Hugging Face
   becomes a third catalog source; its models are a third cost class, "funded", ranked
   after free and before paid, admitted under their own allowance guard.
   Trade-off: touches the pure selector's ordering and the constitution's cost principle.
B. Paid class behind `LLMXIVE_PAID_OPT_IN`. No constitution change, but every manual run
   needs the flag, and the paid guard is built around Dartmouth's balance endpoint, which
   is down. Rejected by the maintainer.
C. Count included credits as free. Simplest; recorded costs stop reflecting real spend.
   Rejected (anti-goal 1).
D. Bolt a Hugging Face fallback onto `main`'s pinned router. Fastest, but a second
   mechanism (anti-goal 2); the maintainer chose to bring spec 026 to `main` first.

## 5. Design

### 5.1 Backend
`src/llmxive/backends/huggingface.py`: `HuggingFaceBackend(BaseBackend)`, registered in
`router._REGISTRY` as `"huggingface"`. OpenAI-compatible chat against the router with the
bill-to header; reuses the existing shared pieces (`invoke_with_deadline`, the
transient/permanent error taxonomy, the circuit breaker, empty-reply detection) rather
than copying Dartmouth's. `model_id` is sent as `<repo id>:<provider>` so the provider
that was priced is the provider that is billed (a pinned provider is never silently
replaced). HTTP 402 maps to `BackendUnavailable` (allowance or group limit reached);
401/403 to a permanent credential error; 429/5xx to transient.
Credentials: `credentials.load_hf_token()` — env `HF_TOKEN`, then Keychain; never the
plaintext Hub cache, never logged. The bill-to id comes from `LLMXIVE_HF_BILL_TO`
(Actions variable; not a secret) with no default, so a missing id fails closed.

### 5.2 Catalog component
`snapshot._fetch_huggingface()` adds component `"hf_catalog"` (own provenance + LKG, like
`catalog` and `local`). One `ModelRef` per (model, live provider) with
`backend="huggingface"`, `serving_endpoint=<provider>`, real `ModelPricing` (÷ 1e6), and
the catalog's context length and structured/tools/vision flags carried as observed
features. `select._component_of` maps the backend to its component.

### 5.3 Quality component
`snapshot._fetch_leaderboard()` adds component `"leaderboard"`: OpenRouter's listing
joined to the catalog by exact `hugging_face_id` (no fuzzy matching in v1). It yields,
per model, a general score (`intelligence_index`) and a coding score (`coding_index`,
falling back to the general score when null). LMArena and Epoch are **not** wired in v1;
they are named as the planned cross-check once an alias map exists.
Raw scores are kept only in the gitignored LKG store, not committed.

### 5.4 Policy: reviewed floors, dynamic ranking
`policy.py` gains a reviewed `FundedPolicy`: for each capability (`cheap`, `standard`,
`deep`, `vision`) and for `deep_code`, a **minimum score**, the score field to use, and
required observed flags (e.g. structured output; image input for `vision`). A Hugging
Face model is eligible for a capability when it has a leaderboard score at or above that
floor and the flags. Above the floor, ranking is by leaderboard score, not by the
hand-set `quality_tier`. The reviewed family table stays authoritative for free and paid
backends and for features the catalog cannot observe (e.g. `reasoning` token budgeting).
This amends spec 026's rule that catalog data is never proof of competence: public
benchmark scores above a reviewed floor now count, for the funded class only.
Fail-closed cases: leaderboard component `unavailable` or older than
`max_catalog_age_s` → no funded candidate is eligible (calls end as an outage); a model
with no `hugging_face_id` match → ineligible.

### 5.5 Cost class and ordering
`ModelRef`/`Candidate` gain `cost_class ∈ {free, funded, paid}` derived from the backend,
not from the price. `select()` ordering becomes free → funded → paid. Within funded:
- `cheap_structured` and `standard_generation`: lowest worst-case cost among eligible
  models, ties broken by score.
- `deep_review`, `deep_code`, `independent_review`, `vision`: highest score whose
  worst-case cost fits the per-call ceiling for that profile; if none fits, the cheapest
  eligible.
Independence dimensions work unchanged (family, vendor, serving endpoint), so a review
panel can still require different families.

### 5.6 Allowance guard
`backends/hf_budget.py` + a `FundedGuardSnapshot` in the runtime snapshot:
- `LLMXIVE_HF_MONTHLY_USD` (default 50). Daily allowance = (monthly − spent this month)
  ÷ days left in the month, so an idle day rolls forward and a heavy day cannot spend
  the month.
- Spend is taken from each response's `usage` × the price of the pinned provider and
  appended through the existing spec-026 reservation ledger (same reserve → settle
  discipline that guards paid Dartmouth calls), so concurrent runners cannot overspend.
- The org credits endpoint is read as a cross-check when the token allows: if the org
  balance is below the remaining allowance, the lower number wins.
- Exhausted allowance → `ModelUnavailable` for the funded class → callers see the
  existing clean `BackendUnavailable` outage path.
- Per-call ceilings per profile live beside the floors in `policy.py`.

### 5.7 Wiring
Workflows that make model calls get `HF_TOKEN: ${{ secrets.HF_TOKEN }}` and
`LLMXIVE_HF_BILL_TO: ${{ vars.LLMXIVE_HF_BILL_TO }}`. `llmxive preflight` reports the
three backends' reachability, the allowance, month-to-date spend and the top candidate
per profile, and makes no paid call.

### 5.8 Tests
- Offline: selection tables over a recorded catalog + leaderboard snapshot (fixture
  captured from the real endpoints on a stated date); ordering free → funded → paid;
  every fail-closed case in 5.4; allowance arithmetic at month boundaries; concurrent
  reservation against a real git ref (as the spec-026 ledger tests do).
- Real-call (`LLMXIVE_REAL_TESTS=1`, a few cents in total): one chat per profile through
  `route_chat` with Dartmouth unreachable; a strict-JSON probe; an image probe for
  `vision`; a 402 path using a deliberately wrong bill-to id; recorded spend equals
  `usage` × catalog price.
- No mocks as the primary path (Constitution III).

### 5.9 Decisions added after an independent builder's read (2026-11-23)

Marked **[call]** where the author decided and the maintainer should check, **[open]**
where only the maintainer can decide.

1. **[decided by the maintainer 2026-11-23: Hugging Face outranks the local model] Where the local 3B model ranks.** `LocalBackend` always offers
   `Qwen/Qwen2.5-3B-Instruct`, which the policy rates `cheap` and `standard`. Under a
   strict free → funded order it would serve every `cheap_structured` and
   `standard_generation` call while Dartmouth is down and Hugging Face would never be
   reached for them. Proposed: order is free *remote* → funded → local → paid, i.e. the
   local model becomes the last free resort (used when the allowance is exhausted or
   Hugging Face is unreachable). The amendment in section 6 is worded for this.
2. **[call] Ledger.** A new protected ref `refs/llmxive/funded-ledger` (USD, monthly
   epoch, own bootstrap anchor) using the existing transport and reserve → settle code;
   the Dartmouth credit ledger is not reused because its unit and epoch differ. A call
   that dies without a `usage` block is charged its full reservation, except a
   definitive pre-inference rejection (HTTP 401, 402 or 403), which is charged zero. Spend on the same
   resource group from outside the pipeline is not in the ledger; the org-balance
   cross-check (5.6) and Hugging Face's own group limit bound it.
3. **[call] Freshness for `independent_review`.** `_enforce_fresh_snapshot` checks the
   components the surviving candidates depend on: Dartmouth `catalog` + `credit` for
   Dartmouth candidates; `hf_catalog` + `leaderboard` + the funded guard for Hugging Face
   candidates. A review is an outage only when no candidate class is fresh. This amends
   spec 026 FR-007.
4. **[call] Features the catalog cannot observe.** A Hugging Face model whose family is
   in the reviewed table inherits that entry's features. One whose family is not is
   eligible only for requirements that do not list `reasoning`, and the backend budgets
   tokens and deadlines for it as if it were a reasoning model (the conservative case).
   `min_context_tokens` is checked against the catalog's per-provider `context_length`.
   The code also requires that `context_length` be at least the call budget's input
   bound plus output bound; a provider reporting no `context_length` is ineligible
   (selection policy version 5).
5. **[call] Interaction with paid controls.** Funded needs no `allow_paid` and no opt-in
   flag. `require_paid` excludes funded (it means paid). In the `execution_status` tier
   ladder the rungs become: default selection → funded best-quality (ignores the
   cheapest-first rule) → paid opt-in tiers. Funded calls count against a spec-025
   Attempt's call ceiling like any other call.
6. **[decided by the maintainer 2026-11-23: the proposal below is accepted] Is the daily allowance a hard stop?** At $50/month a day is about $1.67.
   Proposed: reservations hold worst case × 1 (not × retries), and a run may borrow up to
   three days of allowance ahead but never more than what is left in the month; past
   that the run ends as an outage until the next day.
7. **[call] Artificial Analysis terms.** The scores are used internally for ranking,
   attributed in the docs, and never committed or republished. If that use turns out to
   be disallowed, the fallback source is Epoch's CC-BY capabilities index, which needs an
   alias map; until one exists the funded class would fail closed.
8. **[call] Vision ranking.** General score plus the catalog's image-input flag in v1.

### 5.10 Selection, revised 2026-11-23 (supersedes the fixed floors in 5.3-5.5, 5.9.8 and section 7)

Maintainer direction: separate models for planning/reasoning and for writing code; the
leaderboard changes daily, so selection must be fully automatic; no fixed minimum
scores, because models keep improving — what matters is a model's score *relative to
the others available that day*, balanced against cost; and how strong a model a call
gets must adapt per task, not be fixed.

Scores (checked live 2026-11-23)
- Primary source: LMArena `lmarena-ai/leaderboard-dataset`, config `text`, split
  `latest` (CC-BY-4.0). Category `overall` is the **reasoning** score; category
  `coding` is the **coding** score. 63 routable Hugging Face models matched in each,
  none ambiguously. OpenRouter's listing has no coding score for any model
  (`coding_index` is null on every row) and a general index for fewer models, so it is
  kept only as a recorded cross-check, not used for ranking.
- Name match: lowercase, alphanumerics only, any parenthesised effort suffix dropped;
  when several variants of one model are listed, the highest rating is used. A
  normalised name that matches more than one routable model, or none, makes that model
  ineligible. No hand-maintained alias list.

Two tracks
- Each profile names a track: `reasoning` (planning, reviewing, analysis, writing) or
  `coding` (implementation, repair, anything whose output is code). A model's rank is
  taken from that track's scores only.

Relative strength, no fixed scores
- For each track, the day's eligible models are ranked by score and each gets its
  percentile among them. A call asks for a **strength level**, defined by percentile, not
  by score: `economy` (at or above the median), `balanced` (top 30%), `strong` (top 10%),
  `strongest` (the top-scoring model). The percentile cut-offs are reviewed policy; no
  score value is written anywhere in the repo.
- Within a level, the pick is the cheapest model that qualifies (worst-case cost for the
  call), so a cheaper model that scores as well always wins. The rest of the chain is
  the next-cheapest qualifying models from other families.

Near-ties (approved 2026-11-23)
- Each LMArena row carries `rating_lower` / `rating_upper` (verified live). Two models
  are tied when their intervals overlap. So a model qualifies for a level when its
  `rating_upper` is at or above the `rating_lower` of the model sitting at that level's
  percentile cut-off; for `strongest`, at or above the top model's `rating_lower`. The
  cheapest qualifying model still wins, so a statistically indistinguishable cheaper
  model beats a dearer one at every level. A row missing either bound is treated as a
  zero-width interval (both bounds equal the rating).
- Levels nest: a model qualifies for a level only if it also qualifies for every weaker
  level, so a wide interval on the top model can never make `strongest` admit a model
  that `strong` rejects.
- A publish date more than one day in the future is invalid and makes the leaderboard
  unavailable.
- Freshness is judged from the row's `leaderboard_publish_date` as well as from when
  the snapshot was fetched.

Adapting per task
- Each profile has a default (track, level): `cheap_structured` reasoning/economy;
  `standard_generation` reasoning/balanced; `deep_review` and `independent_review`
  reasoning/strong; `deep_code` coding/strong; `vision` reasoning/balanced plus the
  image-input flag.
- A caller may raise or lower the level for one call through the existing requirement
  overrides. The execution and convergence fix-loops raise it one level each time a tier
  is exhausted, ending at `strongest`; this replaces the "funded best-quality" rung in
  5.9.5.
- Budget pressure: when the level's pick does not fit what is left of the allowance,
  generation and structured calls step down one level and the decision record says so;
  review calls never step down — they end as an outage until the allowance refills.

Fail closed, as before: scores unavailable or stale → no funded candidate.
A leaderboard whose `leaderboard_publish_date` is more than 7 days old is stale.
There is no per-profile cost ceiling: a call is bounded by what is left of the allowance
and by the caller's own budget.
The percentile cut-offs and per-profile defaults above were approved by the maintainer
on 2026-11-23; nothing numeric remains to confirm before merge.

## 6. Constitution amendment (approved 2026-11-23)

Constitution IV currently recognises free and paid. Proposed addition (version 1.3.0 →
1.4.0):

> **Funded services.** A metered service whose cost is covered by an institutional
> subscription the project already holds is *funded*. A funded service MAY be used when
> no free hosted option can serve the request, MUST be ranked after every free hosted
> option and before any paid one, MAY be ranked ahead of a free local fallback model of
> lower measured quality, MUST run under a spend allowance enforced in code, and MUST have
> its real cost recorded for every call. Exhausting the allowance is an outage, not a
> licence to fall through to paid services.

`tests/unit/test_config_consistency.py`'s free-only assertion on the registry is
unaffected: the registry names profiles, not models.

## 7. Left to the builder

File/function names beyond those above; the initial numeric floors and per-call ceilings
(to be proposed from the live score distribution and confirmed by the maintainer before
merge); retry counts; fixture format.

## 8. Open items for the maintainer

1. DONE 2026-11-23: the resource-group limits were set to Total $50, Inference Providers
   $50, Jobs $50 (Spaces and Inference Endpoints $0). Jobs spend shares the $50 total.
2. Whether `HF_TOKEN` in Actions is the dedicated fine-grained token the pilot README
   called for (inference + `org.billing.read`), since this session cannot read a secret.
3. Initial floors (section 7).
4. Jobs share the same $50 group limit (maintainer, 2026-11-23: Hugging Face Jobs will
   run project analyses that GitHub Actions cannot). The funded ledger in 5.6 sees only
   inference spend, so until Jobs offload is designed the inference allowance and Jobs
   spend can together reach the group limit early; the org-balance cross-check does not
   catch this. To settle when Jobs offload is specified: one shared allowance with a
   split, or separate allowances.
