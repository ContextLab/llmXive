# Hugging Face Funded Provider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When no free hosted backend can serve a call, serve it through Hugging Face Inference Providers, choosing the model by its LMArena score *relative to the other models routable that day* and by cost, inside a code-enforced monthly allowance, with no change at any call site.
**Architecture:** Hugging Face becomes a third catalog source and a third cost class ("funded") inside spec 026's single `runtime_snapshot → select → execute` path: three new snapshot components (`hf_catalog`, `leaderboard`, `funded`) feed the pure selector, which orders free remote → funded → local → paid. Each profile names a track (`reasoning` = LMArena `overall`, `coding` = LMArena `coding`) and a default strength level (`economy` / `balanced` / `strong` / `strongest`, defined by percentile among that day's scored models, widened by rating-interval overlap); within a level the cheapest qualifying model wins. Callers and the fix-loop tier ladder shift the level per call through `RequirementOverrides.level_delta`. Spend is reserved and settled in USD on its own protected git ref through the existing strict-CAS ledger code.
**Tech Stack:** Python ≥ 3.11, `httpx` (already a dependency; no new packages), the spec-026 modules (`model_selection/*`, `git_event_log`), pytest with real git refs and a real local HTTP replay server, GitHub Actions env wiring.
**Spec:** specs/027-hf-funded-provider/spec.md (section 5.10 supersedes the fixed floors and OpenRouter ranking of 5.3–5.5, 5.9.8 and section 7; 5.9.2 amended for 401/402/403).

## Global Constraints

- Router base URL: `https://router.huggingface.co/v1` (OpenAI-compatible chat).
- Every chat call sends header `X-HF-Bill-To: <llmxive resource-group id>`; the id comes only from `LLMXIVE_HF_BILL_TO` (Actions variable, not a secret), no default — a missing id fails closed.
- Token: `credentials.load_hf_token()` — env `HF_TOKEN`, then macOS Keychain service `llmxive-huggingface`; never the plaintext Hub cache, never logged.
- Catalog: `GET https://router.huggingface.co/v1/models`, no key; `pricing.input`/`pricing.output` are USD per **million** tokens (÷ 1e6 into `ModelPricing`).
- `model_id` is sent as `<repo id>:<provider>`; a pinned provider is never silently replaced.
- HTTP 402 → `BackendUnavailable`; 401/403 → permanent credential error that skips the candidate; 429/5xx → transient. A 401/402/403, or a request never sent (missing token or bill-to), is a **pre-inference rejection** and is charged **zero**; every other funded call without a `usage` block is charged its full reservation (spec 5.9.2, amended).
- Scores (spec 5.10): LMArena `lmarena-ai/leaderboard-dataset`, config `text`, split `latest` (CC-BY-4.0), fetched keylessly from `https://datasets-server.huggingface.co/filter` with params `dataset`, `config`, `split`, `where="category"='<category>'`, `offset`, `length` (≤ 100; 101 returns HTTP 422 — verified 2026-11-23), paged until `offset ≥ num_rows_total`. Category `overall` is the `reasoning` track, `coding` the `coding` track. Row fields used: `model_name`, `rating`, `rating_lower`, `rating_upper`, `category`, `leaderboard_publish_date`.
- Name match: lowercase, alphanumerics only, trailing parenthesised suffix(es) dropped; a Hugging Face repo id is normalised from its part after `/`. Several LMArena rows that normalise to one name → the highest `rating` wins. A normalised name shared by two or more routable repos, or matching none, leaves those repos unscored (ineligible). No alias list.
- OpenRouter is not used (not for ranking, not as a cross-check). Epoch is not used.
- Strength levels by integer percent of the day's scored population for the track, sorted by `rating` descending (ties by repo id): cut-off index `max(0, ceil(pct·n / 100) − 1)` with `economy` 50, `balanced` 30, `strong` 10, `strongest` = index 0. A repo qualifies when its `rating_upper ≥ rating_lower` of the repo at the cut-off. Missing bounds → zero-width interval. Integer arithmetic only (`0.3 * 10` is `3.0000000000000004`).
- Population for a track = every repo in the snapshot with a score on that track whose `leaderboard_publish_date` is at most `FUNDED_POLICY.max_publish_age_days` (7) before the snapshot's UTC date. Call-specific filters (flags, context, exclusions, independence, allowance) choose among qualifiers; they never change the population.
- Within a level: the cheapest qualifying candidate (worst-case USD for the call; ties → higher `rating`, then model id) leads; the rest of the funded group is the next-cheapest qualifying candidates from families not already used, up to `FUNDED_POLICY.max_chain_slots` (2) in total.
- Profile defaults (track / level / steps down under budget pressure): `cheap_structured` reasoning/economy/yes; `standard_generation` reasoning/balanced/yes; `deep_code` coding/strong/yes; `deep_review` and `independent_review` reasoning/strong/no; `vision` reasoning/balanced/no, plus the catalog's image-input flag.
- `RequirementOverrides.level_delta: int` shifts the profile's level for one call, clamped to `[economy, strongest]`. The fix-loop tier ladder sets `level_delta` = its rung index (0, 1, 2); the optional paid rung sets 0.
- Budget pressure: when the level's pick does not fit the allowance's `available_usd` (or the caller's `max_credits`), a profile that steps down moves exactly one level down and the chain explanation says so; a review profile, or `economy`, does not — the funded group is empty, and paid candidates are dropped too unless `require_paid` (Constitution IV 1.4.0: exhausting the allowance is not a licence to fall through to paid).
- No per-call cost ceiling per profile: the per-call bound is the allowance's `available_usd` and the caller's `max_credits` (see Spec issues 15).
- No score value, model name, percentile cut-off result or floor is committed anywhere. Raw scores live only in the gitignored LKG store (`state/model_selection/lkg_snapshot.json`; `.gitignore:253`). Committed leaderboard fixtures keep real row shapes and names but carry deterministic synthetic ratings, are marked `"ratings_synthetic": true`, and are re-ordered by `model_name` so the row order does not leak the real ranking.
- Snapshot component names: `"hf_catalog"`, `"leaderboard"`, `"funded"` (the first two with their own LKG; `funded` is `live` or `unavailable`).
- Fail closed: `hf_catalog` or `leaderboard` `unavailable` or a `last_known_good` older than `max_catalog_age_s`, or `funded` not `live` → no funded candidate; a requirement with no track/level (not built from a profile) → no funded candidate; an unscored, ambiguous or stale-published repo → ineligible.
- `cost_class ∈ {free, funded, paid}`; funded ⇔ backend `huggingface` whatever the price; ordering is free *remote* → funded → local → paid.
- `LLMXIVE_HF_MONTHLY_USD` (default 50). Daily allowance = (monthly − spent this month) ÷ days left in the month. Reservations hold worst case × 1 (not × retries); a run may borrow up to three days of allowance ahead but never more than what is left in the month.
- Ledger: new protected ref `refs/llmxive/funded-ledger` (USD, monthly epoch, own bootstrap anchor).
- Org credits cross-check: `GET https://huggingface.co/api/organizations/contextlab/billing/credits` (scope `org.billing.read`); if the org balance is below the remaining allowance, the lower number wins.
- Funded needs no `allow_paid` and no opt-in flag; `require_paid` excludes funded.
- Exhausted allowance is an outage (`ModelUnavailable` → `BackendUnavailable`), never a silent downgrade, never a human escalation.
- `SELECTION_POLICY_VERSION` goes 3 → 4 (Task 14); pinned at `tests/unit/test_model_selection_policy.py:22`, `tests/unit/test_model_selection_select.py:490` and `:674`, `tests/unit/test_self_improvement_invocation_identity.py:131`.
- Constitution 1.3.0 → 1.4.0 with the "Funded services" paragraph from spec §6, verbatim.
- No mocks as the primary path (Constitution III). Real-call tests: `LLMXIVE_REAL_TESTS=1`, a few cents in total, bill-to from `LLMXIVE_HF_BILL_TO`.
- Schedules stay paused: no workflow `on:` block is touched.
- Line ranges below are at commit `ddac38cdfcf` (the integration branch after the `origin/main` merge); re-locate by symbol name if they move. Import `llmxive.model_selection.*` from `llmxive/backends/*` only inside functions (as `backends/credits.py:247` does) — a module-level import cycles through `model_selection/__init__` → `execute` → `backends.router`. The reverse direction (`model_selection` → `backends.huggingface`) is safe at module level.

## Review Focus

1. **A leaderboard gap silently promoting a model.** Two routable repos that normalise to one LMArena name; a renamed model (no match); a row with no bounds; a row with `rating_lower > rating`; a server that ignores the `where` filter; a short or `partial` page; a row published eight days ago; a leaderboard LKG one second past `max_catalog_age_s`. Tests: Task 9 `test_join_matches_by_normalised_repo_name_and_drops_ambiguous`, `test_parse_rows_highest_variant_wins_bounds_default_and_bad_rows_drop`, `test_short_or_inconsistent_paging_fails_closed`; Task 13 `test_fail_closed_table`, `test_stale_publish_date_is_ineligible_and_leaves_the_population`.
2. **Relative levels computed wrongly.** Float percent arithmetic; equality at the interval boundary; the population shrinking with the call's own filters; levels not nesting. Tests: Task 12 `test_cutoff_index_is_integer_arithmetic`, `test_level_qualifiers_on_the_reasoning_table`, `test_levels_nest_on_both_tables`; Task 14 `test_population_ignores_call_filters`.
3. **Two runners and the calendar.** Concurrent reservations against one remote ref; a hold opened in one month and read in the next; last day of month, leap day, a non-UTC `now`; the borrow cap never exceeding the month. Tests: Task 8 `test_allowance_cap_table`, `test_two_runners_cannot_overspend_the_allowance`, `test_prior_month_hold_does_not_count`.
4. **A metered call recorded as free, or a rejected one charged.** A provider priced `0.0` on the `huggingface` backend; a reply with no `usage`; a 402 / 401 / 403; `retries=3` under a × 1 hold; a run-log entry that says Dartmouth and `$0`. Tests: Task 6 `test_cost_class_is_funded_even_at_zero_price`; Task 15 `test_missing_usage_charges_full_reservation`, `test_pre_inference_rejection_charges_zero`, `test_funded_dispatches_once_and_reserves_times_one`; Task 16 `test_implementer_run_log_attributes_funded_backend_and_cost`.
5. **Funded starving or bypassing the other classes.** More qualifying funded pairs than slots; allowance exhausted with paid opt-in on; a review under budget pressure; `require_paid`; a 401/403 aborting the chain before the local resort; the tier ladder excluding the only funded qualifier at `strongest`. Tests: Task 14 `test_funded_slots_never_truncate_local_or_paid`, `test_exhausted_allowance_is_outage_not_paid`, `test_review_never_steps_down`, `test_require_paid_excludes_funded`; Task 3 `test_credential_error_skips_candidate`; Task 17 `test_funded_leader_is_never_excluded`.
6. **What the catalog cannot observe, and which provider is billed.** Unknown-family model with `reasoning` required; one repo on two providers with different `context_length`; a provider whose `status` is not live; the request body carrying anything other than the priced `<repo>:<provider>`. Tests: Task 13 `test_unobservable_features_and_context`; Task 10 `test_parse_hf_catalog_one_ref_per_live_provider`; Task 5 `test_chat_sends_pinned_provider_and_bill_to`.

---

## File Structure

Created
|File|Responsibility|
|-|-|
|`src/llmxive/backends/huggingface.py`|`HuggingFaceBackend`, the keyless router-catalog fetch, the pre-inference-rejection exception types.|
|`src/llmxive/backends/hf_budget.py`|Allowance arithmetic, funded-ledger spend projection, guard, observer, org-balance cross-check.|
|`src/llmxive/model_selection/leaderboard.py`|LMArena paged fetch, row parsing, name normalisation, catalog join (called only by `snapshot`).|
|`src/llmxive/model_selection/strength.py`|Pure track population, percentile cut-off and near-tie level qualification.|
|`scripts/hf/capture_fixtures.py`|Capture the recorded fixtures from the real endpoints (ratings replaced by a synthetic formula).|
|`tests/fixtures/hf_funded/{router_models,lmarena_text_overall,lmarena_text_coding,chat_200,chat_402}.json`|Recorded fixtures, each with `captured_at`.|
|`tests/helpers/funded.py`|Synthetic rating tables, ids, and a hand-built funded snapshot.|
|`tests/helpers/replay_server.py`|Real local HTTP server replaying recorded or computed responses and recording requests.|
|`tests/unit/test_governance_027.py`, `test_credentials_hf.py`, `test_backend_shared_pieces.py`, `test_hf_fixtures.py`, `test_huggingface_backend.py`, `test_model_selection_cost_class.py`, `test_hf_budget.py`, `test_model_selection_leaderboard.py`, `test_model_selection_hf_snapshot.py`, `test_funded_policy.py`, `test_model_selection_strength.py`, `test_model_selection_funded_select.py`, `test_runlog_funded.py`, `test_preflight_selection_report.py`, `test_workflow_hf_env.py`|One file per task, named after its component.|
|`tests/integration/test_funded_ledger.py`, `test_funded_execute.py`|Real-git-ref ledger and execution tests.|
|`tests/real_call/test_hf_funded_real.py`|The real-call lane.|

Modified
|File|Responsibility of the change|
|-|-|
|`.specify/memory/constitution.md`|1.4.0 amendment.|
|`src/llmxive/credentials.py`|`load_hf_token`.|
|`scripts/hf/pilot.py`, `scripts/hf/README.md`|Delegate token loading; describe production use, the $50 limits, real-call evidence.|
|`src/llmxive/backends/base.py`|Shared `CircuitBreaker`, `BackendCredentialError`, `openai_content`, token counts on `ChatResponse`.|
|`src/llmxive/backends/dartmouth.py`|Import the moved pieces.|
|`src/llmxive/backends/router.py`|Register `"huggingface"`; credential error → SKIP.|
|`src/llmxive/types.py`, `agents/registry.yaml`|`BackendName.HUGGINGFACE`; registry backend entry.|
|`src/llmxive/model_selection/types.py`|Cost class, tracks, levels, arena scores, observed features, funded guard, requirement and override fields.|
|`src/llmxive/model_selection/ledger_transport.py`, `reservations.py`|Ref-parametrised config, `charged` amount, public `reconcile`.|
|`src/llmxive/cli.py`, `infra/credit-ledger-ops.md`|`funded-ledger-bootstrap`; runbook section.|
|`src/llmxive/model_selection/snapshot.py`|Three new components, LKG, digest, score join.|
|`src/llmxive/model_selection/policy.py`, `profiles.py`|`FundedPolicy` (approved cut-offs); per-profile track, level, step-down; policy version 4.|
|`src/llmxive/model_selection/select.py`|Funded eligibility, level qualification, cheapest-within-level, budget step-down, class ordering, class-aware freshness.|
|`src/llmxive/model_selection/route.py`|`level_delta` merge, requirement digest, `funded_policy` seam, funded leaders not excluded by the free-rung leader exclusion.|
|`src/llmxive/model_selection/execute.py`|Funded reserve → dispatch × 1 → settle (zero for pre-inference rejections).|
|`src/llmxive/state/runlog.py`, `agents/base.py`, `agents/implementer.py`, `speckit/slash_command.py`|Truthful backend + cost in the run log.|
|`src/llmxive/state/execution_status.py`|Each free rung raises the funded level by its index.|
|`src/llmxive/preflight.py`|Selection report.|
|`.github/workflows/*.yml` (11 files, 12 env blocks)|Env wiring only.|
|`src/llmxive/model_selection/inventory.py`, `specs/026-…/migration_manifest.{json,md}`|Detector sees `<repo>:<provider>`.|
|`README.md`, `CLAUDE.md`|Models & cost text; LMArena attribution.|
|`tests/real_call/test_model_selection_snapshot_real.py`, `tests/unit/test_selection_identity.py`, the four version-pinning tests above|Assertions whose contract this spec changes (named in the owning task).|

Commit trailer used by every commit below (written out in each command):
`Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>` / `Claude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK`

---

### Task 1: Governance — constitution 1.4.0
**Files:** Create `tests/unit/test_governance_027.py` · Modify `.specify/memory/constitution.md` (1-23 Sync Impact Report, 138-160 Principle IV, 350 version line). The spec is already committed (`f71fc9a5bb6`, amended through `ddac38cdfcf`); this task does not touch it.
**Interfaces:**
- Consumes: constitution "Amendment procedure" (322-330) and "Versioning policy" (332-339: a material expansion of existing guidance is MINOR); spec §6.
- Produces: constitution text "Funded services" that Tasks 15 and 16 cite.
- [ ] Step 1: Write the failing test
```python
ROOT = Path(__file__).resolve().parents[2]
FUNDED = ("A metered service whose cost is covered by an institutional subscription the "
          "project already holds is *funded*.")
def test_spec_027_is_committed_approved_and_revised():
    text = (ROOT / "specs/027-hf-funded-provider/spec.md").read_text()
    assert "approved by the maintainer 2026-11-23" in text
    assert "### 5.10 Selection, revised 2026-11-23" in text
def test_constitution_is_1_4_0_with_funded_services():
    text = " ".join((ROOT / ".specify/memory/constitution.md").read_text().split())
    assert "**Version**: 1.4.0 | **Ratified**: 2026-04-28" in text
    assert "→ 1.3.0 → 1.4.0" in text            # Sync Impact Report chain
    assert FUNDED in text
    assert "Exhausting the allowance is an outage, not a licence to fall through to paid services." in text
```
- [ ] Step 2: `pytest tests/unit/test_governance_027.py -q` → FAIL (`test_constitution_is_1_4_0_with_funded_services`: version line is `1.3.0`).
- [ ] Step 3: In the constitution: append `→ 1.4.0` to the version chain and a `1.4.0 (2026-11-23, spec 027) = MINOR — …` rationale paragraph in the Sync Impact Report; add the spec §6 block quote verbatim as a "**Funded services.**" paragraph after line 156; set the version line to `1.4.0` and `Last Amended` to the merge date (rule 3 — if the merge slips, correct the date in the merge commit). Paste the Sync Impact Report into the PR description (rule 2), marking `README.md`, `CLAUDE.md`, `scripts/hf/README.md` "updated" and the `.specify/templates/*` "no edit needed".
- [ ] Step 4: `pytest tests/unit/test_governance_027.py -q` → PASS (2 passed).
- [ ] Step 5: `git add .specify/memory/constitution.md tests/unit/test_governance_027.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "docs(027): constitution 1.4.0 adds funded services" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 2: `credentials.load_hf_token`
**Files:** Modify `src/llmxive/credentials.py` (27-30 constants; new function after `load_kaggle_creds`, 276-306), `scripts/hf/pilot.py` (`token()` 20-43), `scripts/hf/README.md` (Credentials section, line 24) · Test `tests/unit/test_credentials_hf.py`
**Interfaces:**
- Consumes: the existing loader conventions in `credentials.py`; `scripts/hf/pilot.py::token` (the only existing HF credential reader — it becomes a caller, not a copy).
- Produces: `HF_TOKEN_NAME = "HF_TOKEN"`, `HF_KEYCHAIN_SERVICE = "llmxive-huggingface"`, `load_hf_token(*, platform: str | None = None, security_bin: str = "security") -> str | None`.
- [ ] Step 1: Write the failing test (real subprocess against a real executable written to `tmp_path`; no mocks)
```python
def _fake_security(tmp_path, body):          # a real executable standing in for /usr/bin/security
    p = tmp_path / "security"; p.write_text("#!/bin/sh\n" + body + "\n"); p.chmod(0o755); return str(p)
def test_env_wins(monkeypatch, tmp_path):
    monkeypatch.setenv("HF_TOKEN", "  hf_env  ")
    assert load_hf_token(platform="darwin", security_bin=_fake_security(tmp_path, "echo hf_kc")) == "hf_env"
def test_keychain_used_on_darwin_when_env_absent(monkeypatch, tmp_path):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    argv = tmp_path / "argv"
    sec = _fake_security(tmp_path, f'echo "$@" > {argv}; echo hf_kc')
    assert load_hf_token(platform="darwin", security_bin=sec) == "hf_kc"
    assert argv.read_text().split() == ["find-generic-password", "-s", "llmxive-huggingface", "-w"]
def test_keychain_miss_and_non_darwin_return_none(monkeypatch, tmp_path):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    assert load_hf_token(platform="darwin", security_bin=_fake_security(tmp_path, "exit 44")) is None
    assert load_hf_token(platform="linux", security_bin=_fake_security(tmp_path, "echo hf_kc")) is None
def test_plaintext_hub_cache_is_never_read(monkeypatch, tmp_path):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    (tmp_path / "token").write_text("hf_cache"); monkeypatch.setenv("HF_HOME", str(tmp_path))
    monkeypatch.setenv("HUGGING_FACE_HUB_TOKEN", "hf_legacy")
    assert load_hf_token(platform="linux") is None
```
- [ ] Step 2: `pytest tests/unit/test_credentials_hf.py -q` → FAIL (`ImportError: cannot import name 'load_hf_token'`).
- [ ] Step 3: Implement `load_hf_token` in `credentials.py` (`platform=None` means `sys.platform`; no `-a` account argument, so no personal account name enters `src/`). Replace the body of `scripts/hf/pilot.py::token` with a call to it that raises the existing `RuntimeError` on `None`. Update the README Credentials paragraph to say the loader lives in `llmxive.credentials`.
- [ ] Step 4: `pytest tests/unit/test_credentials_hf.py -q` → PASS (4 passed).
- [ ] Step 5: `git add src/llmxive/credentials.py scripts/hf/pilot.py scripts/hf/README.md tests/unit/test_credentials_hf.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): credentials.load_hf_token (env then Keychain); pilot delegates" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 3: Shared backend pieces (extracted, not copied)
**Files:** Modify `src/llmxive/backends/base.py` (314-319 `ChatResponse`, new exception after `BackendUnavailable` 368-370, 531-551 `__all__`), `src/llmxive/backends/dartmouth.py` (44-67 `_lc_content`, 225-383 `_CircuitBreaker`, 1051 `_new_breaker`), `src/llmxive/backends/router.py` (166-183 `disposition_of`) · Test `tests/unit/test_backend_shared_pieces.py`; existing `tests/unit/test_dartmouth_circuit_breaker.py` must pass unedited
**Interfaces:**
- Consumes: `dartmouth._CircuitBreaker(max_consecutive, window_s, clock)`, `dartmouth._lc_content(content)`.
- Produces (all in `backends/base.py`): `CircuitBreaker(*, max_consecutive: int, window_s: float, clock: Callable[[], float] = time.monotonic, label: str = "Dartmouth")`; `openai_content(content: str | tuple[ContentPart, ...]) -> str | list[dict]`; `class BackendCredentialError(PermanentBackendError)`; `ChatResponse.input_tokens: int | None = None`, `ChatResponse.output_tokens: int | None = None`. `router.disposition_of(BackendCredentialError(...)) is CandidateDisposition.SKIP`.
- [ ] Step 1: Write the failing test
```python
def test_breaker_is_shared_and_dartmouth_alias_is_the_same_class():
    from llmxive.backends import dartmouth
    assert dartmouth._CircuitBreaker is CircuitBreaker
def test_breaker_label_appears_in_open_error():
    br = CircuitBreaker(max_consecutive=1, window_s=1800.0, clock=lambda: 0.0, label="Hugging Face")
    with pytest.raises(TransientBackendError):
        br.call(lambda: (_ for _ in ()).throw(TransientBackendError("x")))
    with pytest.raises(BackendUnavailable, match="Hugging Face endpoint persistently unavailable"):
        br.call(lambda: "never")
def test_openai_content_passthrough_and_image_data_url():
    assert openai_content("hi") == "hi"
    png = _red_png()                                  # a real 2x2 PNG built with zlib/struct in the test
    out = openai_content((TextPart("what colour?"), ImagePart.from_bytes("image/png", png)))
    assert out[0] == {"type": "text", "text": "what colour?"}
    assert out[1]["image_url"]["url"].startswith("data:image/png;base64,")
def test_credential_error_skips_candidate():           # Review Focus 5
    assert disposition_of(BackendCredentialError("401")) is CandidateDisposition.SKIP
    assert isinstance(BackendCredentialError("x"), PermanentBackendError)
def test_chat_response_token_counts_default_to_none():
    r = ChatResponse(text="t", model="m", backend="b")
    assert r.input_tokens is None and r.output_tokens is None and r.cost_estimate_usd == 0.0
```
- [ ] Step 2: `pytest tests/unit/test_backend_shared_pieces.py -q` → FAIL (`ImportError: CircuitBreaker`).
- [ ] Step 3: Move the two definitions into `base.py` unchanged apart from the `label` parameter (default keeps today's message byte-identical); in `dartmouth.py` replace them with `from llmxive.backends.base import CircuitBreaker as _CircuitBreaker, openai_content as _lc_content`, keeping the env-derived defaults at their call site (`_new_breaker`). Add the `BackendCredentialError` branch to `disposition_of` before the `PermanentBackendError` branch.
- [ ] Step 4: `pytest tests/unit/test_backend_shared_pieces.py tests/unit/test_dartmouth_circuit_breaker.py tests/unit/test_model_selection_router_primitive.py tests/unit/test_dartmouth_retry.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/backends/base.py src/llmxive/backends/dartmouth.py src/llmxive/backends/router.py tests/unit/test_backend_shared_pieces.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "refactor(027): share CircuitBreaker/openai_content; typed credential error skips; token counts on ChatResponse" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 4: Capture the recorded fixtures
**Files:** Create `scripts/hf/capture_fixtures.py`, `tests/fixtures/hf_funded/{router_models,lmarena_text_overall,lmarena_text_coding,chat_200,chat_402}.json`, `tests/unit/test_hf_fixtures.py`
**Interfaces:**
- Consumes: `credentials.load_hf_token`; env `LLMXIVE_HF_BILL_TO`.
- Produces: five files, each `{"captured_at": "<YYYY-MM-DD>", "source_url": "<url>", "status": <int>, "payload": {...}}`. The two LMArena files additionally carry `"ratings_synthetic": true` and a payload `{"num_rows_total": <int>, "pages": <int>, "rows": [<row dict>, ...]}` (the `row` objects of every page, concatenated). In the script: `synthetic_rating(category: str, model_name: str) -> tuple[float, float, float, float]` returning `(rating, rating_lower, rating_upper, variance)`; CLI `python scripts/hf/capture_fixtures.py [--with-chat]`, guarded by `if __name__ == "__main__":` so the test can import it by path.
- Decisions: the catalog GET and the LMArena pages are keyless and free (`length=100`, offsets 0, 100, … until `num_rows_total`; `source_url` is the offset-0 URL). The synthetic formula, applied to every LMArena row: `h = int(sha256(f"{category}|{model_name}".encode()).hexdigest(), 16)`; `rating = 1000 + (h % 5000) / 10`; `half = 2 + ((h >> 64) % 100) / 10`; `rating_lower = round(rating - half, 1)`, `rating_upper = round(rating + half, 1)`, `variance = round(half, 1)`; `rank` is recomputed as `1 + #rows with a higher synthetic rating`; `vote_count`, names, `organization`, `license`, `category` and `leaderboard_publish_date` stay real. Rows are written sorted by `model_name` (the server returns them in real-rank order). `--with-chat` makes exactly one billed chat (`max_tokens` 64; the cheapest live provider in the catalog just fetched, so no model id is written into the script) and one request with bill-to `000000000000000000000000` for the 402 body (a 402 is not billed); it drops response headers and strips `id`/`system_fingerprint` from the chat payload.
- [ ] Step 1: Write the failing test
```python
FX = Path(__file__).resolve().parents[1] / "fixtures" / "hf_funded"
ROOT = Path(__file__).resolve().parents[2]
def _load(name): return json.loads((FX / name).read_text())
def _script():
    spec = importlib.util.spec_from_file_location("capture_fixtures", ROOT / "scripts/hf/capture_fixtures.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
ARENA = ("lmarena_text_overall.json", "lmarena_text_coding.json")
def test_every_fixture_states_its_capture_date_and_source():
    for name in ("router_models.json", *ARENA, "chat_200.json", "chat_402.json"):
        fx = _load(name)
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", fx["captured_at"]) and fx["source_url"].startswith("https://")
def test_router_catalog_has_the_fields_the_spec_names():
    models = _load("router_models.json")["payload"]["data"]
    assert len(models) >= 100
    p = next(p for m in models for p in m["providers"] if p.get("pricing"))
    assert {"input", "output"} <= set(p["pricing"]) and "status" in p and "context_length" in p
@pytest.mark.parametrize("name,category", [(ARENA[0], "overall"), (ARENA[1], "coding")])
def test_arena_fixture_is_complete_real_shaped_and_synthetic(name, category):
    fx = _load(name); rows = fx["payload"]["rows"]
    assert fx["ratings_synthetic"] is True and len(rows) == fx["payload"]["num_rows_total"] > 100
    assert fx["payload"]["pages"] == -(-len(rows) // 100)
    assert {"model_name", "rating", "rating_lower", "rating_upper", "category", "leaderboard_publish_date"} <= set(rows[0])
    assert {r["category"] for r in rows} == {category}
    assert [r["model_name"] for r in rows] == sorted(r["model_name"] for r in rows)   # real rank order not leaked
    syn = _script().synthetic_rating
    for r in rows:                                      # every committed number is the formula's, none is LMArena's
        assert (r["rating"], r["rating_lower"], r["rating_upper"], r["variance"]) == syn(category, r["model_name"])
def test_chat_fixtures_carry_usage_and_the_402():
    assert {"prompt_tokens", "completion_tokens"} <= set(_load("chat_200.json")["payload"]["usage"])
    assert _load("chat_402.json")["status"] == 402
```
- [ ] Step 2: `pytest tests/unit/test_hf_fixtures.py -q` → FAIL (`FileNotFoundError`).
- [ ] Step 3: Write the script and run `LLMXIVE_HF_BILL_TO=<group id> python scripts/hf/capture_fixtures.py --with-chat` (cost: under one cent). Inspect the five files for tokens, account names and balances before staging; confirm with `git diff --stat` that no file outside `tests/fixtures/hf_funded/` and the script changed.
- [ ] Step 4: `pytest tests/unit/test_hf_fixtures.py -q` → PASS (6 passed).
- [ ] Step 5: `git add scripts/hf/capture_fixtures.py tests/fixtures/hf_funded/router_models.json tests/fixtures/hf_funded/lmarena_text_overall.json tests/fixtures/hf_funded/lmarena_text_coding.json tests/fixtures/hf_funded/chat_200.json tests/fixtures/hf_funded/chat_402.json tests/unit/test_hf_fixtures.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "test(027): recorded HF router + LMArena fixtures (synthetic ratings) and capture script" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 5: `HuggingFaceBackend`
**Files:** Create `src/llmxive/backends/huggingface.py`, `tests/helpers/replay_server.py`, `tests/unit/test_huggingface_backend.py` · Modify `src/llmxive/backends/router.py` (`_REGISTRY` 44-47), `src/llmxive/types.py` (185-189 `BackendName`), `agents/registry.yaml` (2-12), `scripts/hf/README.md` (intro: Hugging Face is now a routed fallback)
**Interfaces:**
- Consumes: `base.{BaseBackend, ChatMessage, ChatResponse, CircuitBreaker, openai_content, invoke_with_deadline, BackendUnavailable, BackendCredentialError, TransientBackendError, EmptyReplyError, PermanentBackendError}`; `credentials.load_hf_token`.
- Produces: `ROUTER_BASE_URL = "https://router.huggingface.co/v1"`, `BILL_TO_ENV = "LLMXIVE_HF_BILL_TO"`, `BILL_TO_HEADER = "X-HF-Bill-To"`; `fetch_router_catalog(*, base_url: str = ROUTER_BASE_URL, timeout: float = 30.0) -> dict` (keyless GET `/models`); `class PreInferenceRejection(Exception)` (marker mixin: the provider rejected the request before inference, or it was never sent); `class HFPaymentRequired(PreInferenceRejection, BackendUnavailable)` (402); `class HFCredentialRejected(PreInferenceRejection, BackendCredentialError)` with `http_status: int | None` (401/403, or `None` = not sent: missing token or bill-to); `class HuggingFaceBackend(BaseBackend)` with `name = "huggingface"`, `__init__(self, *, token: str | None = None, bill_to: str | None = None, base_url: str = ROUTER_BASE_URL)`, `list_models() -> list[str]` (repo ids), `chat(...)` per `BaseBackend`, `healthcheck()`. `tests.helpers.replay_server.ReplayServer(routes: dict[tuple[str, str], list[tuple[int, dict]] | Callable[[dict], tuple[int, dict]]])` — a context manager with `.base_url` and `.requests: list[dict]` (`method`, `path`, `query: dict[str, str]`, `headers` with lower-cased names, `json` or `None`); a list route is served in order, a callable route is called with the recorded request.
- Decisions: one HTTP attempt per `chat()` (no internal retry — see Task 15); default deadline `float(os.environ.get("LLMXIVE_HF_DEADLINE_S", "360.0"))` for every model (the reasoning-model deadline from `dartmouth.py:118-119`, applied to all because the catalog cannot observe reasoning — spec 5.9.4); per-model breaker `CircuitBreaker(max_consecutive=3, window_s=1800.0, label="Hugging Face")`; empty content with `finish_reason == "length"` raises `TransientBackendError("… reasoning budget exhausted …")` (the phrase `chat_one_candidate` already advances on, `router.py:240`), any other empty content raises `EmptyReplyError`; `cost_estimate_usd` stays `0.0` here and is filled by `execute`, which knows the priced provider. Registry entry: `{name: huggingface, kind: openai_compatible, auth_env_vars: [HF_TOKEN, LLMXIVE_HF_BILL_TO], is_paid: false}`.
- [ ] Step 1: Write the failing test (a real HTTP exchange against `ReplayServer`)
```python
M = "acme/alpha-large:prov-a"; MSG = [ChatMessage("user", "hi")]
OK = (200, _load("chat_200.json")["payload"]); PAY = (402, _load("chat_402.json")["payload"])
def _be(srv, **kw): return HuggingFaceBackend(token="hf_t", bill_to="grp123", base_url=srv.base_url, **kw)
def test_chat_sends_pinned_provider_and_bill_to():                 # Review Focus 6
    with ReplayServer({("POST", "/chat/completions"): [OK]}) as srv:
        r = _be(srv).chat(MSG, model=M, max_tokens=64, temperature=0.0)
    req = srv.requests[0]
    assert req["headers"]["x-hf-bill-to"] == "grp123" and req["headers"]["authorization"] == "Bearer hf_t"
    assert req["json"]["model"] == M and req["json"]["max_tokens"] == 64 and req["json"]["stream"] is False
    assert r.backend == "huggingface" and r.model == M
    assert (r.input_tokens, r.output_tokens) == (OK[1]["usage"]["prompt_tokens"], OK[1]["usage"]["completion_tokens"])
@pytest.mark.parametrize("status,exc,pre", [(402, HFPaymentRequired, True), (401, HFCredentialRejected, True),
    (403, HFCredentialRejected, True), (429, TransientBackendError, False), (503, TransientBackendError, False),
    (400, PermanentBackendError, False)])
def test_status_mapping(status, exc, pre):
    body = PAY[1] if status == 402 else {"error": "x"}
    with ReplayServer({("POST", "/chat/completions"): [(status, body)]}) as srv:
        with pytest.raises(exc) as ei: _be(srv).chat(MSG, model=M)
    assert isinstance(ei.value, PreInferenceRejection) is pre
    assert isinstance(HFPaymentRequired("x"), BackendUnavailable) and isinstance(HFCredentialRejected("x", http_status=401), BackendCredentialError)
    assert len(srv.requests) == 1                                   # exactly one attempt, no hidden retry
def test_missing_bill_to_or_token_fails_closed_without_a_request(monkeypatch):
    monkeypatch.delenv("LLMXIVE_HF_BILL_TO", raising=False); monkeypatch.delenv("HF_TOKEN", raising=False)
    with ReplayServer({}) as srv:
        with pytest.raises(HFCredentialRejected, match="LLMXIVE_HF_BILL_TO") as ei:
            HuggingFaceBackend(token="hf_t", base_url=srv.base_url).chat(MSG, model=M)
    assert ei.value.http_status is None and srv.requests == []
def test_empty_reply_is_transient_and_length_is_budget_exhaustion():
    empty = lambda fr: (200, {"choices": [{"message": {"content": ""}, "finish_reason": fr}], "usage": {}})
    with ReplayServer({("POST", "/chat/completions"): [empty("stop"), empty("length")]}) as srv:
        with pytest.raises(EmptyReplyError): _be(srv).chat(MSG, model=M)
        with pytest.raises(TransientBackendError, match="reasoning budget exhausted"): _be(srv).chat(MSG, model=M)
def test_token_never_appears_in_an_error():
    with ReplayServer({("POST", "/chat/completions"): [(500, {"error": "boom"})]}) as srv:
        with pytest.raises(TransientBackendError) as ei: _be(srv).chat(MSG, model=M)
    assert "hf_t" not in str(ei.value)
def test_catalog_fetch_is_keyless_and_replay_records_query():
    with ReplayServer({("GET", "/models"): lambda req: (200, {"data": [], "echo": req["query"]})}) as srv:
        assert fetch_router_catalog(base_url=srv.base_url)["data"] == []
    assert "authorization" not in srv.requests[0]["headers"] and srv.requests[0]["json"] is None
def test_registered_and_named():
    assert isinstance(make_backend("huggingface"), HuggingFaceBackend)
    assert BackendName("huggingface") is BackendName.HUGGINGFACE
```
- [ ] Step 2: `pytest tests/unit/test_huggingface_backend.py -q` → FAIL (`ModuleNotFoundError: llmxive.backends.huggingface`).
- [ ] Step 3: Implement the backend with `httpx`, the replay helper with `http.server.ThreadingHTTPServer` on `127.0.0.1:0` (query parsed with `urllib.parse.parse_qs`, first value kept), the `_REGISTRY` entry, `BackendName.HUGGINGFACE = "huggingface"` (replace the 2026-05-29 "removed" comment), and the registry backend entry.
- [ ] Step 4: `pytest tests/unit/test_huggingface_backend.py tests/integration/test_free_backend_only.py tests/unit/test_config_consistency.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/backends/huggingface.py src/llmxive/backends/router.py src/llmxive/types.py agents/registry.yaml scripts/hf/README.md tests/helpers/replay_server.py tests/unit/test_huggingface_backend.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): HuggingFaceBackend (bill-to header, pinned provider, 402/401/429 taxonomy, pre-inference rejections)" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 6: Selection types — cost class, tracks, levels, scores, observed features, funded guard
**Files:** Modify `src/llmxive/model_selection/types.py` (15-17 literals, 143-174 `ModelRequirement`, 177-207 `RequirementOverrides`, 242-267 `RuntimeSnapshot`, 270-277 `Candidate`, after 302-311 `worst_case_credits`), `src/llmxive/model_selection/__init__.py` (exports), `tests/unit/test_selection_identity.py` (add `RequirementOverrides(level_delta=1)` to the `test_every_override_field_changes_the_selection` parameters) · Test `tests/unit/test_model_selection_cost_class.py`
**Interfaces:**
- Produces:
```python
CostClass = Literal["free", "funded", "paid"]
Track = Literal["reasoning", "coding"]
StrengthLevel = Literal["economy", "balanced", "strong", "strongest"]
STRENGTH_LEVELS: tuple[StrengthLevel, ...] = ("economy", "balanced", "strong", "strongest")
FUNDED_BACKENDS: frozenset[str] = frozenset({"huggingface"})
def cost_class_of(backend: str, pricing: ModelPricing) -> CostClass      # funded iff backend in FUNDED_BACKENDS, whatever the price
def worst_case_usd(pricing: ModelPricing, budget: CallBudget) -> float | None   # worst_case_credits / USD_TO_CREDITS
def shift_level(level: StrengthLevel, delta: int) -> StrengthLevel       # clamped to [economy, strongest]
@dataclass(frozen=True) class ArenaScore:  rating: float; rating_lower: float; rating_upper: float; publish_date: date
    # __post_init__: ValueError unless all three are finite and rating_lower <= rating <= rating_upper
@dataclass(frozen=True) class ModelScores: reasoning: ArenaScore | None = None; coding: ArenaScore | None = None
    def for_track(self, track: Track) -> ArenaScore | None
@dataclass(frozen=True) class ObservedModel: context_length: int | None; features: frozenset[str]   # ⊆ {"structured","tools","vision"}
@dataclass(frozen=True) class FundedGuardSnapshot:
    monthly_usd: float; spent_month_usd: float; spent_before_today_usd: float; outstanding_usd: float
    org_balance_usd: float | None; effective_cap_usd: float; available_usd: float
    epoch: str; observed_at: datetime; source: SnapshotSource
```
  `Candidate.cost_class` — a **property** (`cost_class_of(self.model_ref.backend, self.pricing)`), not a stored field, so no existing positional `Candidate(...)` can default a paid model to free. `ModelRequirement` gains `profile: str | None = None`, `track: Track | None = None`, `strength: StrengthLevel | None = None`, `budget_step_down: bool = False` (a requirement with `track` or `strength` `None` gets no funded candidate — Task 13). `RequirementOverrides.level_delta: int = 0` (`__post_init__`: `TypeError` unless a non-bool `int`; any sign). `RuntimeSnapshot` gains, after `digest`, `funded: FundedGuardSnapshot | None = None`, `scores: Mapping[str, ModelScores]` and `observed: Mapping[str, ObservedModel]` (both keyed by `model_id`, default empty, wrapped in `MappingProxyType` in `__post_init__`).
- Note: `canonical_overrides` reads `dataclasses.fields`, so `level_delta` joins every `selection_identity` string (one-time invalidation of stored receipts, together with the version-4 bump in Task 14 — see Spec issues 22).
- [ ] Step 1: Write the failing test
```python
def test_cost_class_is_funded_even_at_zero_price():                 # Review Focus 4
    assert cost_class_of("huggingface", ModelPricing(0.0, 0.0)) == "funded"
    assert cost_class_of("huggingface", ModelPricing(None, None)) == "funded"
def test_cost_class_free_and_paid_follow_price_off_hugging_face():
    assert cost_class_of("dartmouth", ModelPricing(0.0, 0.0)) == "free"
    assert cost_class_of("dartmouth", ModelPricing(1e-6, 5e-6)) == "paid"
    assert cost_class_of("local", ModelPricing(0.0, 0.0)) == "free"
def test_candidate_cost_class_is_derived_not_defaulted():
    paid = Candidate(ModelRef("dartmouth", "ep", "m", "f", "v"), ModelPricing(1e-6, 5e-6), 2.5, 10.0)
    assert paid.cost_class == "paid"
def test_worst_case_usd():
    assert worst_case_usd(ModelPricing(1e-7, 4e-7), CallBudget(10_000, 2_000)) == pytest.approx(0.0018)
    assert worst_case_usd(ModelPricing(None, None), CallBudget(1, 1)) is None
@pytest.mark.parametrize("level,delta,want", [("strong", 1, "strongest"), ("strong", 5, "strongest"), ("economy", -1, "economy"),
    ("balanced", -1, "economy"), ("economy", 2, "strong"), ("strongest", 0, "strongest")])
def test_shift_level_clamps(level, delta, want):
    assert shift_level(level, delta) == want
def test_arena_score_rejects_inconsistent_bounds_and_scores_pick_by_track():
    d = date(2026, 11, 22)
    with pytest.raises(ValueError): ArenaScore(1300.0, 1310.0, 1320.0, d)
    with pytest.raises(ValueError): ArenaScore(float("nan"), 1.0, 2.0, d)
    s = ModelScores(reasoning=ArenaScore(1300.0, 1300.0, 1300.0, d))
    assert s.for_track("reasoning").rating == 1300.0 and s.for_track("coding") is None
def test_requirement_and_override_defaults():
    r = ModelRequirement(capability="deep", call_budget=CallBudget(1, 1))
    assert (r.profile, r.track, r.strength, r.budget_step_down) == (None, None, None, False)
    assert RequirementOverrides().level_delta == 0 and RequirementOverrides(level_delta=-2).level_delta == -2
    for bad in (True, 1.0, "1"):
        with pytest.raises(TypeError): RequirementOverrides(level_delta=bad)
def test_snapshot_new_fields_default_empty_and_are_read_only():
    snap = _offline_snapshot()                       # from tests.conftest
    assert snap.funded is None and dict(snap.scores) == {} and dict(snap.observed) == {}
    with pytest.raises(TypeError): snap.scores["x"] = ModelScores()
```
- [ ] Step 2: `pytest tests/unit/test_model_selection_cost_class.py -q` → FAIL (`ImportError: cost_class_of`).
- [ ] Step 3: Implement the additions in `types.py`, export the new names, and add the `level_delta` parameter to `test_selection_identity.py`.
- [ ] Step 4: `pytest tests/unit/test_model_selection_cost_class.py tests/unit/test_selection_identity.py tests/unit/test_model_selection_select.py tests/unit/test_model_selection_execute.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/model_selection/types.py src/llmxive/model_selection/__init__.py tests/unit/test_model_selection_cost_class.py tests/unit/test_selection_identity.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): cost class, tracks, strength levels, arena scores and funded snapshot types" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 7: Funded ledger on its own ref
**Files:** Modify `src/llmxive/model_selection/ledger_transport.py` (65-70, 88-101, 162-190, 245-270, 323-350, `__all__`), `src/llmxive/model_selection/reservations.py` (78-95, 129-177, 278-279, 348-369, 470, 520, 549, 581, `__all__`), `src/llmxive/cli.py` (`_cmd_credits_ledger_bootstrap` 386-399, parser 1144-1150), `infra/credit-ledger-ops.md` (new "Funded ledger" section) · Test `tests/integration/test_funded_ledger.py`; extend `tests/unit/test_ledger_config_from_env.py`
**Interfaces:**
- Consumes: `LedgerConfig(remote, expected_anchor)`, `_log_ref(config)`, `read_events(repo, *, ref)`, `bootstrap_ledger(repo, remote)`, `reserve`, `_reconcile_one`, `project`.
- Produces: `FUNDED_LEDGER_REF = "refs/llmxive/funded-ledger"`; `LedgerConfig.ref: str = LEDGER_REF` (every read and write in both modules uses `config.ref`); `FUNDED_LEDGER_REMOTE_ENV = "LLMXIVE_FUNDED_LEDGER_REMOTE"`, `FUNDED_LEDGER_ANCHOR_ENV = "LLMXIVE_FUNDED_LEDGER_ANCHOR"`; `funded_ledger_config_from_env(*, remote: str | None = None, require_anchor: bool = True) -> LedgerConfig`; `bootstrap_ledger(repo, remote=None, *, ref: str = LEDGER_REF) -> str`; `reservations.reconcile(repo: Path, reservation_id: str, *, charged: float | None = None, now: datetime | None = None, config: LedgerConfig | None = None) -> None` (the public form of `_reconcile_one`; from any non-terminal state; first writer wins; `_reconcile_one` becomes a call to it); `Reservation.charged: float | None = None`; `"charged"` added to `_AMOUNT_FIELDS`. CLI `llmxive funded-ledger-bootstrap [--remote origin | --no-remote]`.
- Decisions: on the funded ref every amount field (`worst_case_credits`, `settlement_baseline`, `charged`) is **USD** and `budget_epoch` is `YYYY-MM` (UTC); the field names are the shared schema's and are not renamed. No funded sweep: a crashed `open` hold keeps counting at its full reservation until the month ends, which is exactly spec 5.9.2's charge for a call without `usage`.
- [ ] Step 1: Write the failing test (real git repos, as `tests/integration/test_credit_reservations.py` does; reuse its `_git` / `repo` fixture shapes)
```python
CFG = LedgerConfig(remote=None, ref=FUNDED_LEDGER_REF); EPOCH = "2026-11"
def _reserve(repo, rid, usd, *, cap, spend=0.0, config=CFG, now=T0):
    return reserve(repo, reservation_id=rid, worst_case_credits=usd, model="acme/alpha-large:prov-a",
        credit_observer=lambda: CreditObservation(spend=spend, effective_cap=cap, budget_epoch=EPOCH),
        lease_expires_at=now + timedelta(seconds=420), now=now, config=config)
def test_funded_ref_is_separate_from_the_credit_ledger(repo):
    r = _reserve(repo, "f1", 0.25, cap=1.0)
    assert r.state == STATE_OPEN and r.worst_case_credits == 0.25
    assert read_events(repo) == []                                   # credit-ledger ref untouched
    assert [e["type"] for e in read_events(repo, ref=FUNDED_LEDGER_REF)] == ["open"]
def test_reconcile_records_the_charge_and_first_writer_wins(repo):
    _reserve(repo, "f1", 0.25, cap=1.0)
    reconcile(repo, "f1", charged=0.0024, now=T0, config=CFG)
    reconcile(repo, "f1", charged=0.25, now=T0, config=CFG)          # idempotent: no second event
    res = project(read_events(repo, ref=FUNDED_LEDGER_REF))["f1"]
    assert res.state == STATE_RECONCILED and res.charged == 0.0024
def test_zero_charge_is_recorded_as_zero(repo):                      # spec 5.9.2: 401/402/403 charge zero
    _reserve(repo, "f1", 0.25, cap=1.0); reconcile(repo, "f1", charged=0.0, now=T0, config=CFG)
    assert project(read_events(repo, ref=FUNDED_LEDGER_REF))["f1"].charged == 0.0
def test_negative_or_nan_charge_is_rejected(repo):
    _reserve(repo, "f1", 0.25, cap=1.0)
    for bad in (-0.01, float("nan")):
        with pytest.raises(ValueError): reconcile(repo, "f1", charged=bad, now=T0, config=CFG)
def test_existing_credit_ledger_reconcile_has_no_charge(repo):       # shared schema stays backward compatible
    _reserve(repo, "c1", 10.0, cap=100.0, config=LedgerConfig(remote=None)); settle(repo, "c1", now=T0)
    reconcile_settled(repo, observed_spend=10.0, epoch=EPOCH, now=T0)
    assert project(read_events(repo))["c1"].charged is None
def test_bootstrap_funded_ref_on_a_remote(remote_and_clone):
    remote, a = remote_and_clone
    anchor = bootstrap_ledger(a, remote="origin", ref=FUNDED_LEDGER_REF)
    out = subprocess.run(["git", "ls-remote", str(remote), FUNDED_LEDGER_REF], capture_output=True, text=True).stdout
    assert out.split()[0] == anchor
```
  and in `test_ledger_config_from_env.py`: `funded_ledger_config_from_env()` raises `LedgerError` matching `LLMXIVE_FUNDED_LEDGER_ANCHOR` when unset; with it set returns `LedgerConfig(remote="origin", expected_anchor="abc", ref="refs/llmxive/funded-ledger")`; `ledger_config_from_env()` still returns `ref == "refs/llmxive/credit-ledger"`.
- [ ] Step 2: `pytest tests/integration/test_funded_ledger.py tests/unit/test_ledger_config_from_env.py -q` → FAIL (`ImportError: FUNDED_LEDGER_REF`).
- [ ] Step 3: Implement. Add the CLI command beside `credits-ledger-bootstrap` (it prints the anchor and the variable name to pin). Runbook section: ref name, USD unit, monthly epoch, `funded-ledger-bootstrap`, the two env vars, the same server-side fast-forward-only protection, "no sweep", and "401/402/403 are reconciled at zero".
- [ ] Step 4: `pytest tests/integration/test_funded_ledger.py tests/unit/test_ledger_config_from_env.py tests/integration/test_credit_reservations.py tests/integration/test_credit_ledger_transport.py tests/integration/test_model_selection_execute.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/model_selection/ledger_transport.py src/llmxive/model_selection/reservations.py src/llmxive/cli.py infra/credit-ledger-ops.md tests/integration/test_funded_ledger.py tests/unit/test_ledger_config_from_env.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): funded ledger ref (USD, monthly epoch) on the existing CAS transport" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 8: Allowance guard (`backends/hf_budget.py`)
**Files:** Create `src/llmxive/backends/hf_budget.py`, `tests/unit/test_hf_budget.py` · Test also appended to `tests/integration/test_funded_ledger.py`
**Interfaces:**
- Consumes: Task 7 (`funded_ledger_config_from_env`, `read_events`, `project`, `reconcile`, `fetch_ledger`, `counting_total`, `CreditObservation`), `types.FundedGuardSnapshot`, `credentials.load_hf_token`, `huggingface.BILL_TO_ENV`.
- Produces:
```python
MONTHLY_USD_ENV = "LLMXIVE_HF_MONTHLY_USD"; DEFAULT_MONTHLY_USD = 50.0; BORROW_AHEAD_DAYS = 3
ORG_CREDITS_URL = "https://huggingface.co/api/organizations/contextlab/billing/credits"
class FundedUnavailable(RuntimeError)
def monthly_allowance_usd() -> float                       # unset → 50.0; unparsable/negative/non-finite → 0.0 + warning (fail closed)
def epoch_of(now: datetime) -> str                         # UTC "YYYY-MM"
def days_left_in_month(now: datetime) -> int               # UTC, counting today
def allowance_cap_usd(*, monthly_usd: float, spent_month_usd: float, spent_before_today_usd: float,
                      now: datetime, org_balance_usd: float | None = None) -> float
@dataclass(frozen=True) class FundedSpend: spent_month_usd: float; spent_before_today_usd: float; outstanding_usd: float
def funded_spend(reservations: Iterable[Reservation], *, now: datetime) -> FundedSpend
def parse_org_credits(payload: dict) -> float              # payload["balanceUsd"]
def fetch_org_balance_usd(*, timeout: float = 30.0) -> float | None     # None on any failure, incl. 403 (cross-check "when the token allows")
def funded_observer(repo: Path, *, config: LedgerConfig, now_fn: Callable[[], datetime] = ...,
                    org_balance_usd: float | None = None) -> Callable[[], CreditObservation]
def funded_guard(repo: Path, *, now: datetime, config: LedgerConfig | None = None,
                 org_balance_fetch: Callable[[], float | None] = fetch_org_balance_usd) -> FundedGuardSnapshot  # raises FundedUnavailable
def settle_funded(repo: Path, reservation_id: str, *, charged_usd: float | None, now: datetime, config: LedgerConfig) -> float
```
- Algorithm the signature does not determine (the value `reservations.admits` compares month-to-date spend against):
```python
def allowance_cap_usd(*, monthly_usd, spent_month_usd, spent_before_today_usd, now, org_balance_usd=None):
    left_at_day_start = max(0.0, monthly_usd - spent_before_today_usd)
    daily = left_at_day_start / days_left_in_month(now)
    today = min(daily * (1 + BORROW_AHEAD_DAYS), left_at_day_start)   # today's share + three days ahead, never past the month
    cap = spent_before_today_usd + today
    if org_balance_usd is not None:
        cap = min(cap, spent_month_usd + org_balance_usd)             # the lower number wins
    return cap
```
  `funded_spend`, for reservations whose `budget_epoch == epoch_of(now)`: `spent_month_usd` = Σ `charged` of reconciled ones (`charged is None` → its `worst_case_credits`); `outstanding_usd` = `counting_total`; `spent_before_today_usd` = Σ over those with `created_at` (UTC date) before today of (`charged` if reconciled else `worst_case_credits`). `funded_guard` raises `FundedUnavailable` when the bill-to id, the token, the anchor or the ledger sync is missing; `available_usd = max(0, effective_cap_usd − spent_month_usd − outstanding_usd)`. `settle_funded` reconciles with `charged_usd`, or the reservation's full amount when `None`, and returns what it wrote.
- [ ] Step 1: Write the failing test
```python
U = lambda s: datetime.fromisoformat(s).replace(tzinfo=UTC)
@pytest.mark.parametrize("monthly,month,before,now,org,expected", [      # Review Focus 2
    (50.0, 12.0, 10.0, U("2026-11-23T12:00:00"), None, 30.0),            # 40 left / 8 days = 5/day; 4 days' worth = 20
    (50.0, 12.0, 10.0, U("2026-11-23T12:00:00"), 3.0, 15.0),             # org balance below remaining → lower wins
    (50.0, 40.0, 40.0, U("2026-11-30T23:59:59"), None, 50.0),            # last day: borrow capped by the month
    (50.0, 0.0, 0.0,  U("2026-12-01T00:00:00"), None, 4 * 50.0 / 31),    # first instant of the next month
    (50.0, 60.0, 60.0, U("2026-11-23T12:00:00"), None, 60.0),            # already over: cap == spend, zero headroom
    (29.0, 0.0, 0.0,  U("2028-02-29T10:00:00"), None, 29.0),             # leap day is the last day
])
def test_allowance_cap_table(monthly, month, before, now, org, expected):
    assert allowance_cap_usd(monthly_usd=monthly, spent_month_usd=month, spent_before_today_usd=before,
                             now=now, org_balance_usd=org) == pytest.approx(expected)
def test_days_left_and_epoch_use_utc():
    assert [days_left_in_month(U(d)) for d in ("2026-11-23T00:00:00", "2026-11-30T12:00:00", "2026-12-01T00:00:00", "2027-02-01T00:00:00")] == [8, 1, 31, 28]
    assert epoch_of(datetime.fromisoformat("2026-11-30T20:00:00-05:00")) == "2026-12"
def test_monthly_allowance_env(monkeypatch):
    monkeypatch.delenv(MONTHLY_USD_ENV, raising=False); assert monthly_allowance_usd() == 50.0
    monkeypatch.setenv(MONTHLY_USD_ENV, "20"); assert monthly_allowance_usd() == 20.0
    for bad in ("abc", "-5", "nan"):
        monkeypatch.setenv(MONTHLY_USD_ENV, bad); assert monthly_allowance_usd() == 0.0
def test_parse_org_credits():
    assert parse_org_credits({"balanceUsd": 199.99, "balances": []}) == 199.99
```
  and against a real git ref (in `test_funded_ledger.py`):
```python
def test_funded_spend_and_guard_from_real_events(repo, monkeypatch):
    for rid, usd, day, charged in [("a", 4.0, "2026-11-20", 4.0), ("b", 2.0, "2026-11-23", 1.5),
                                   ("c", 0.5, "2026-11-23", None), ("d", 0.25, "2026-11-21", None)]:
        _reserve(repo, rid, usd, cap=1e9, now=U(day + "T09:00:00"))
        if charged is not None: reconcile(repo, rid, charged=charged, now=U(day + "T09:01:00"), config=CFG)
    now = U("2026-11-23T12:00:00")
    assert funded_spend(project(read_events(repo, ref=FUNDED_LEDGER_REF)).values(), now=now) == FundedSpend(5.5, 4.25, 0.75)
    monkeypatch.setenv("LLMXIVE_HF_BILL_TO", "grp123"); monkeypatch.setenv("HF_TOKEN", "hf_t")
    g = funded_guard(repo, now=now, config=CFG, org_balance_fetch=lambda: None)
    assert g.effective_cap_usd == pytest.approx(27.125) and g.available_usd == pytest.approx(20.875)
    assert (g.epoch, g.source, g.monthly_usd) == ("2026-11", "live", 50.0)
def test_guard_fails_closed_without_bill_to(repo, monkeypatch):
    monkeypatch.delenv("LLMXIVE_HF_BILL_TO", raising=False); monkeypatch.setenv("HF_TOKEN", "hf_t")
    with pytest.raises(FundedUnavailable, match="LLMXIVE_HF_BILL_TO"):
        funded_guard(repo, now=T0, config=CFG, org_balance_fetch=lambda: None)
def test_prior_month_hold_does_not_count(repo):
    _reserve(repo, "old", 30.0, cap=1e9, now=U("2026-11-30T23:59:00"))          # epoch 2026-11, never settled
    obs = funded_observer(repo, config=CFG, now_fn=lambda: U("2026-12-01T00:01:00"))()
    assert (obs.budget_epoch, obs.spend) == ("2026-12", 0.0)
    assert funded_spend(project(read_events(repo, ref=FUNDED_LEDGER_REF)).values(), now=U("2026-12-01T00:01:00")).outstanding_usd == 0.0
def test_two_runners_cannot_overspend_the_allowance(remote_and_two_clones):     # as test_two_runners_cannot_collectively_overspend
    _remote, a, b = remote_and_two_clones                                        # bootstrapped with ref=FUNDED_LEDGER_REF
    cfg = LedgerConfig(remote="origin", ref=FUNDED_LEDGER_REF); now = U("2026-11-30T12:00:00")
    results = []
    def run(clone, rid):
        try:
            reserve(clone, reservation_id=rid, worst_case_credits=30.0, model="m", lease_expires_at=now + timedelta(seconds=420),
                    credit_observer=funded_observer(clone, config=cfg, now_fn=lambda: now), now=now, config=cfg); results.append("ok")
        except LedgerDenied: results.append("denied")
    ts = [threading.Thread(target=run, args=(a, "ra")), threading.Thread(target=run, args=(b, "rb"))]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert sorted(results) == ["denied", "ok"]                                   # $50 month, two $30 holds
def test_settle_funded_charges_full_reservation_when_usage_is_missing(repo):
    _reserve(repo, "f1", 0.25, cap=1.0)
    assert settle_funded(repo, "f1", charged_usd=None, now=T0, config=CFG) == 0.25
```
- [ ] Step 2: `pytest tests/unit/test_hf_budget.py tests/integration/test_funded_ledger.py -q` → FAIL (`ModuleNotFoundError: llmxive.backends.hf_budget`).
- [ ] Step 3: Implement `hf_budget.py` (function-local `model_selection` imports).
- [ ] Step 4: same command → PASS.
- [ ] Step 5: `git add src/llmxive/backends/hf_budget.py tests/unit/test_hf_budget.py tests/integration/test_funded_ledger.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): funded allowance guard (daily pacing, 3-day borrow, org-balance cross-check)" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 9: LMArena leaderboard — paged fetch, parsing, name matching
**Files:** Create `src/llmxive/model_selection/leaderboard.py`, `tests/unit/test_model_selection_leaderboard.py`
**Interfaces:**
- Consumes: Task 6 `ArenaScore`, `ModelScores`, `Track`; Task 5 `ReplayServer` (callable routes, recorded `query`); Task 4 fixtures.
- Produces:
```python
LMARENA_DATASET = "lmarena-ai/leaderboard-dataset"; LMARENA_CONFIG = "text"; LMARENA_SPLIT = "latest"
DATASETS_SERVER_FILTER_URL = "https://datasets-server.huggingface.co/filter"
PAGE_LENGTH = 100                                         # the server's maximum; 101 → HTTP 422
TRACK_CATEGORY: Mapping[Track, str] = MappingProxyType({"reasoning": "overall", "coding": "coding"})
class LeaderboardError(RuntimeError)
def normalise_name(name: str) -> str                       # strip trailing "( … )" groups, lowercase, keep [a-z0-9]
def normalise_repo(repo_id: str) -> str                    # normalise_name(repo_id.split("/", 1)[-1])
def parse_arena_rows(rows: Iterable[Mapping], *, category: str) -> dict[str, ArenaScore]   # keyed by normalised name
def fetch_arena_category(category: str, *, base_url: str = DATASETS_SERVER_FILTER_URL, timeout: float = 30.0) -> list[dict]
def fetch_arena_scores(*, base_url: str = DATASETS_SERVER_FILTER_URL) -> dict[Track, dict[str, ArenaScore]] | None
def join_scores(repo_ids: Iterable[str], arena: Mapping[Track, Mapping[str, ArenaScore]]) -> tuple[dict[str, ModelScores], tuple[str, ...]]
```
- Behaviour the signatures do not fix: `parse_arena_rows` raises `LeaderboardError` on a row whose `category` differs from the one asked for (the server ignored the filter); skips (with a warning) a row whose `rating` is not a finite number, whose `leaderboard_publish_date` is not an ISO date, whose bounds make `ArenaScore` raise, or whose name normalises to the empty string; a missing `rating_lower`/`rating_upper` becomes `rating` (zero-width); several rows with one normalised name keep the highest `rating`. `fetch_arena_category` sends no `Authorization` header, passes `dataset`, `config`, `split`, `where='"category"=\'<category>\''`, `offset`, `length=100` as query params, pages until `offset >= num_rows_total`, and raises `LeaderboardError` on a non-200, `partial: true`, a missing `num_rows_total`, or a page that returns zero rows before the total is reached. `fetch_arena_scores` fetches both categories through `TRACK_CATEGORY` and returns `None` (logged) on any `LeaderboardError` or `httpx.HTTPError` — the snapshot's LKG fallback takes over. `join_scores` returns, per input repo id, `ModelScores` with each track's score when exactly one input repo has that normalised name; the second element lists, sorted, every normalised name present in the arena data that two or more input repos share (those repos get nothing for that name). Repos with no score on either track are absent from the result. This module is the only caller of the datasets server; only `snapshot.py` calls it.
- [ ] Step 1: Write the failing test
```python
D = date(2026, 11, 22)
def _row(name, rating, category="overall", lower="same", upper="same", published="2026-11-22"):
    return {"model_name": name, "organization": "x", "license": "y", "rating": rating,
            "rating_lower": rating if lower == "same" else lower, "rating_upper": rating if upper == "same" else upper,
            "variance": 1.0, "vote_count": 100.0, "rank": 1.0, "category": category, "leaderboard_publish_date": published}
@pytest.mark.parametrize("raw,norm", [("Gemini 4 Carbon (High)", "gemini4carbon"), ("gpt-oss-120b", "gptoss120b"),
    ("Claude Opus 4.6", "claudeopus46"), ("DeepSeek-V3.2 (thinking) (beta) ", "deepseekv32"), ("  ", "")])
def test_normalise_name(raw, norm):
    assert normalise_name(raw) == norm
def test_normalise_repo_uses_the_part_after_the_org():
    assert normalise_repo("openai/gpt-oss-120b") == "gptoss120b" == normalise_name("gpt-oss-120b")
def test_parse_rows_highest_variant_wins_bounds_default_and_bad_rows_drop():   # Review Focus 1
    rows = [_row("Alpha Large (High)", 1300.0, lower=1290.0, upper=1310.0), _row("Alpha Large", 1250.0),
            _row("Beta Mini", 1200.0, lower=None, upper=None), _row("Gamma", None),
            _row("Delta", 1100.0, lower=1120.0, upper=1130.0), _row("Eps", 1000.0, published="yesterday")]
    got = parse_arena_rows(rows, category="overall")
    assert got == {"alphalarge": ArenaScore(1300.0, 1290.0, 1310.0, D), "betamini": ArenaScore(1200.0, 1200.0, 1200.0, D)}
    with pytest.raises(LeaderboardError): parse_arena_rows([_row("Z", 1.0, category="coding")], category="overall")
def test_join_matches_by_normalised_repo_name_and_drops_ambiguous():           # Review Focus 1
    s1, s2, s3 = (ArenaScore(r, r, r, D) for r in (1300.0, 1500.0, 1250.0))
    arena = {"reasoning": {"alphalarge": s1, "zetadup": s2}, "coding": {"alphalarge": s3}}
    scores, ambiguous = join_scores(["acme/alpha-large", "acme/zeta-dup", "other-lab/zeta-dup", "acme/unlisted"], arena)
    assert scores == {"acme/alpha-large": ModelScores(reasoning=s1, coding=s3)}
    assert ambiguous == ("zetadup",)
def _pager(rows, *, total=None, stop_after=None):
    def respond(req):
        off, ln = int(req["query"]["offset"]), int(req["query"]["length"])
        page = [] if stop_after is not None and off >= stop_after else rows[off:off + ln]
        return 200, {"features": [], "rows": [{"row_idx": off + i, "row": r, "truncated_cells": []} for i, r in enumerate(page)],
                     "num_rows_total": len(rows) if total is None else total, "num_rows_per_page": 100, "partial": False}
    return respond
def test_fetch_pages_until_num_rows_total_without_a_key():
    rows = [_row(f"M{i}", 1000.0 + i, "coding") for i in range(250)]
    with ReplayServer({("GET", "/filter"): _pager(rows)}) as srv:
        got = fetch_arena_category("coding", base_url=srv.base_url + "/filter")
    assert got == rows and [r["query"]["offset"] for r in srv.requests] == ["0", "100", "200"]
    q = srv.requests[0]["query"]
    assert (q["dataset"], q["config"], q["split"], q["where"], q["length"]) == (
        "lmarena-ai/leaderboard-dataset", "text", "latest", "\"category\"='coding'", "100")
    assert all("authorization" not in r["headers"] for r in srv.requests)
def test_short_or_inconsistent_paging_fails_closed():
    rows = [_row(f"M{i}", 1000.0 + i, "coding") for i in range(250)]
    for route in (_pager(rows, stop_after=100), lambda req: (500, {"error": "x"}),
                  lambda req: (200, {"rows": [], "num_rows_total": 5, "partial": True}), lambda req: (200, {"rows": []})):
        with ReplayServer({("GET", "/filter"): route}) as srv:
            with pytest.raises(LeaderboardError): fetch_arena_category("coding", base_url=srv.base_url + "/filter")
def test_fetch_arena_scores_maps_categories_to_tracks_and_returns_none_on_failure():
    by_cat = {"overall": [_row("Alpha Large", 1300.0)], "coding": [_row("Alpha Large", 1250.0, "coding")]}
    def route(req): return _pager(by_cat["coding" if "coding" in req["query"]["where"] else "overall"])(req)
    with ReplayServer({("GET", "/filter"): route}) as srv:
        got = fetch_arena_scores(base_url=srv.base_url + "/filter")
    assert got["reasoning"]["alphalarge"].rating == 1300.0 and got["coding"]["alphalarge"].rating == 1250.0
    with ReplayServer({("GET", "/filter"): lambda req: (503, {})}) as srv:
        assert fetch_arena_scores(base_url=srv.base_url + "/filter") is None
def test_recorded_fixtures_join_to_the_recorded_catalog():         # re-checks spec 5.10's "63 matched, none ambiguous"
    repos = {m["id"] for m in _load("router_models.json")["payload"]["data"]}
    arena = {t: parse_arena_rows(_load(f"lmarena_text_{c}.json")["payload"]["rows"], category=c) for t, c in TRACK_CATEGORY.items()}
    scores, ambiguous = join_scores(repos, arena)
    assert sum(s.reasoning is not None for s in scores.values()) >= 50
    assert sum(s.coding is not None for s in scores.values()) >= 50
    assert ambiguous == ()
```
- [ ] Step 2: `pytest tests/unit/test_model_selection_leaderboard.py -q` → FAIL (`ModuleNotFoundError: llmxive.model_selection.leaderboard`).
- [ ] Step 3: Implement with `httpx` (`params=` does the URL encoding). If `test_recorded_fixtures_join_to_the_recorded_catalog` fails on the counts or on ambiguity, report the numbers to the maintainer (they contradict spec 5.10's live check) — do not edit the fixture or loosen the bound.
- [ ] Step 4: `pytest tests/unit/test_model_selection_leaderboard.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/model_selection/leaderboard.py tests/unit/test_model_selection_leaderboard.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): LMArena leaderboard fetch (paged, keyless), parsing and catalog name matching" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 10: Snapshot components `hf_catalog`, `leaderboard`, `funded`
**Files:** Modify `src/llmxive/model_selection/snapshot.py` (39-43 constants, 176-207 payload helpers, 216-238 `_resolve_models_component`, 269-306 `_digest`, 309-338 `runtime_snapshot`), `tests/real_call/test_model_selection_snapshot_real.py` (49) · Test `tests/unit/test_model_selection_hf_snapshot.py`
**Interfaces:**
- Consumes: `huggingface.fetch_router_catalog`; `hf_budget.funded_guard`, `hf_budget.FundedUnavailable`; `ledger_transport.funded_ledger_config_from_env`; `leaderboard.{fetch_arena_scores, join_scores, parse_arena_rows, TRACK_CATEGORY}`; `lkg.{LKGStore, LKGEntry}`; `_vendor_of`, `_family_of`; Task 6 types.
- Produces: `_HFCatalogData = tuple[list[ModelRef], dict[str, ModelPricing], dict[str, ObservedModel]]`; `_ArenaData = dict[Track, dict[str, ArenaScore]]`; `_parse_hf_catalog(raw: dict) -> _HFCatalogData`; `_fetch_huggingface() -> _HFCatalogData | None`; `_fetch_leaderboard() -> _ArenaData | None` (delegates to `fetch_arena_scores`); `_fetch_funded_guard(*, now: datetime) -> FundedGuardSnapshot | None` (`None` on `FundedUnavailable` or a `LedgerError`); `_arena_to_payload` / `_arena_from_payload` (`{track: {name: [rating, lower, upper, "YYYY-MM-DD"]}}`); a generic `_resolve_component(name, fetch, to_payload, from_payload, empty, lkg, now, updates)` that `_resolve_models_component` now delegates to. `runtime_snapshot().sources` keys become `{"catalog", "local", "credit", "hf_catalog", "leaderboard", "funded"}`; `snapshot.scores[model_id]` is `join_scores(<every hf_catalog repo>, <leaderboard data>)[0][<repo of model_id>]` for every `huggingface` model whose repo matched; `snapshot.observed[model_id]` the catalog's flags; `_digest` covers `scores` (all four `ArenaScore` fields), `observed` and `funded`.
- Decisions: one `ModelRef("huggingface", <provider>, "<repo>:<provider>", _family_of(<repo>, vendor), _vendor_of(<repo>))` per provider whose `status == "live"` — family and vendor come from the repo id alone (`_family_of` would otherwise leak `:provider` into the family for ids with no size suffix); a provider with no numeric `pricing.input`/`output` keeps its ref with `ModelPricing(None, None)` (unknown is never free). `ObservedModel.features`: `structured` ← `supports_structured_output`, `tools` ← `supports_tools`, `vision` ← `"image" in architecture.input_modalities`. The leaderboard LKG stores the parsed arena data (by normalised name), not the join, so an LKG leaderboard still joins against a live catalog. The `funded` component has no LKG (`live` or `unavailable`). The join's ambiguous list is logged at WARNING with the names only (no ratings).
- [ ] Step 1: Write the failing test
```python
CAT = _load("router_models.json")["payload"]
ARENA = {t: parse_arena_rows(_load(f"lmarena_text_{c}.json")["payload"]["rows"], category=c) for t, c in TRACK_CATEGORY.items()}
def test_parse_hf_catalog_one_ref_per_live_provider():                # Review Focus 6
    refs, pricing, observed = _parse_hf_catalog(CAT)
    live = [(m["id"], p["provider"]) for m in CAT["data"] for p in m["providers"] if p.get("status") == "live"]
    assert sorted(r.model_id for r in refs) == sorted(f"{i}:{p}" for i, p in live)
    r = refs[0]; repo, provider = r.model_id.rsplit(":", 1)
    assert (r.backend, r.serving_endpoint) == ("huggingface", provider) and ":" not in r.model_family
    src = next(p for m in CAT["data"] if m["id"] == repo for p in m["providers"] if p["provider"] == provider)
    assert pricing[r.model_id].input_usd_per_token == pytest.approx(src["pricing"]["input"] / 1e6)
    assert observed[r.model_id].context_length == src.get("context_length")
def test_parse_hf_catalog_synthetic_edges():
    raw = {"data": [{"id": "acme/alpha-large", "architecture": {"input_modalities": ["text", "image"]}, "providers": [
        {"provider": "prov-a", "status": "live", "pricing": {"input": 2.0, "output": 8.0}, "context_length": 200000,
         "supports_structured_output": True, "supports_tools": False},
        {"provider": "prov-b", "status": "staging", "pricing": {"input": 1.0, "output": 4.0}},
        {"provider": "prov-c", "status": "live"}]}]}
    refs, pricing, observed = _parse_hf_catalog(raw)
    assert [r.model_id for r in refs] == ["acme/alpha-large:prov-a", "acme/alpha-large:prov-c"]
    assert pricing["acme/alpha-large:prov-a"] == ModelPricing(2e-6, 8e-6)
    assert not pricing["acme/alpha-large:prov-c"].is_known
    assert observed["acme/alpha-large:prov-a"] == ObservedModel(200000, frozenset({"structured", "vision"}))
def _guard(now): return FundedGuardSnapshot(50.0, 10.0, 10.0, 0.0, None, 30.0, 5.0, "2026-11", now, "live")
def _patch(monkeypatch, *, hf, lb, guard):                                # the house seam: tests/unit/test_model_selection_lkg.py
    for name in ("_fetch_dartmouth", "_fetch_local"): monkeypatch.setattr(snap_mod, name, lambda: None)
    monkeypatch.setattr(snap_mod, "_fetch_credit", lambda *, now: None)
    monkeypatch.setattr(snap_mod, "_fetch_huggingface", hf); monkeypatch.setattr(snap_mod, "_fetch_leaderboard", lb)
    monkeypatch.setattr(snap_mod, "_fetch_funded_guard", guard)
def test_snapshot_joins_scores_per_provider_and_falls_back_to_lkg(monkeypatch, tmp_path):
    store = LKGStore(tmp_path / "lkg.json"); hf = _parse_hf_catalog(CAT)
    _patch(monkeypatch, hf=lambda: hf, lb=lambda: ARENA, guard=lambda *, now: _guard(now))
    s1 = snap_mod.runtime_snapshot(now=T0, lkg_store=store)
    assert set(s1.sources) == {"catalog", "local", "credit", "hf_catalog", "leaderboard", "funded"}
    assert s1.sources["hf_catalog"].source == s1.sources["leaderboard"].source == s1.sources["funded"].source == "live"
    joined, _ = join_scores({r.model_id.rsplit(":", 1)[0] for r in hf[0]}, ARENA)
    for m in s1.models:
        if m.backend == "huggingface":
            assert s1.scores.get(m.model_id) == joined.get(m.model_id.rsplit(":", 1)[0])
    assert s1.scores and s1.funded == _guard(T0)
    _patch(monkeypatch, hf=lambda: None, lb=lambda: None, guard=lambda *, now: None)
    s2 = snap_mod.runtime_snapshot(now=T0 + timedelta(seconds=3601), lkg_store=store)
    assert (s2.sources["leaderboard"].source, s2.sources["leaderboard"].age_s) == ("last_known_good", 3601.0)
    assert s2.sources["funded"].source == "unavailable" and s2.funded is None
    assert dict(s2.scores) == dict(s1.scores) and len(s2.models) == len(s1.models) and s1.digest != s2.digest
def test_lkg_leaderboard_joins_against_the_live_catalog(monkeypatch, tmp_path):
    store = LKGStore(tmp_path / "lkg.json"); refs, pricing, observed = _parse_hf_catalog(CAT)
    _patch(monkeypatch, hf=lambda: (refs, pricing, observed), lb=lambda: ARENA, guard=lambda *, now: None)
    gone = next(iter(snap_mod.runtime_snapshot(now=T0, lkg_store=store).scores)).rsplit(":", 1)[0]
    kept = [r for r in refs if not r.model_id.startswith(gone + ":")]
    _patch(monkeypatch, hf=lambda: (kept, pricing, observed), lb=lambda: None, guard=lambda *, now: None)
    s = snap_mod.runtime_snapshot(now=T0 + timedelta(seconds=60), lkg_store=store)
    assert s.sources["leaderboard"].source == "last_known_good" and s.scores
    assert not any(k.startswith(gone + ":") for k in s.scores)
def test_scores_live_only_in_the_gitignored_lkg_store():
    root = Path(__file__).resolve().parents[2]
    assert subprocess.run(["git", "check-ignore", "-q", "state/model_selection/lkg_snapshot.json"], cwd=root).returncode == 0
def test_digest_changes_when_a_score_or_its_publish_date_changes(monkeypatch, tmp_path):
    hf = _parse_hf_catalog(CAT); name = next(iter(ARENA["reasoning"])); s = ARENA["reasoning"][name]
    digests = []
    for score in (s, replace(s, rating_upper=s.rating_upper + 1), replace(s, publish_date=s.publish_date - timedelta(days=1))):
        arena = {**ARENA, "reasoning": {**ARENA["reasoning"], name: score}}
        _patch(monkeypatch, hf=lambda: hf, lb=lambda a=arena: a, guard=lambda *, now: None)
        digests.append(snap_mod.runtime_snapshot(now=T0, lkg_store=LKGStore(tmp_path / f"{len(digests)}.json")).digest)
    assert len(set(digests)) == 3
```
- [ ] Step 2: `pytest tests/unit/test_model_selection_hf_snapshot.py -q` → FAIL (`ImportError: _parse_hf_catalog`).
- [ ] Step 3: Implement. In `tests/real_call/test_model_selection_snapshot_real.py:49` change the expected key set to the six components (the snapshot contract this spec changes).
- [ ] Step 4: `pytest tests/unit/test_model_selection_hf_snapshot.py tests/unit/test_model_selection_lkg.py tests/unit/test_model_selection_snapshot.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/model_selection/snapshot.py tests/unit/test_model_selection_hf_snapshot.py tests/real_call/test_model_selection_snapshot_real.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): hf_catalog, leaderboard and funded snapshot components with LKG and score join" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 11: Funded policy, per-profile track and level, and the `level_delta` override
**Files:** Modify `src/llmxive/model_selection/policy.py` (append after `CAPABILITY_POLICY`, 157-203), `src/llmxive/model_selection/profiles.py` (43-92 `RequirementProfile`, 96-161 `PROFILES`), `src/llmxive/model_selection/route.py` (148-181 `_requirement_digest`, 294-302 override merge in `resolve_chain`), `src/llmxive/model_selection/__init__.py` · Test `tests/unit/test_funded_policy.py`
**Interfaces:**
- Consumes: Task 6 `Track`, `StrengthLevel`, `shift_level`, `RequirementOverrides.level_delta`, `ModelRequirement.{profile, track, strength, budget_step_down}`.
- Produces:
```python
@dataclass(frozen=True)
class FundedPolicy:
    level_top_percent: Mapping[StrengthLevel, int | None]  # None = the top-scoring model (index 0)
    max_publish_age_days: int
    max_chain_slots: int
FUNDED_POLICY = FundedPolicy(
    level_top_percent=MappingProxyType({"economy": 50, "balanced": 30, "strong": 10, "strongest": None}),  # approved 2026-11-23 (spec 5.10)
    max_publish_age_days=7,          # builder's call, Spec issues 16
    max_chain_slots=2,               # builder's call, Spec issues 11
)
```
  `RequirementProfile` gains `track: Track | None = None`, `strength: StrengthLevel | None = None`, `budget_step_down: bool = False`; `build` sets `profile=self.name` and copies the three. `PROFILES` values per the Global Constraints table. In `resolve_chain`, when `overrides` is given and `base.strength is not None`, `requirement.strength = shift_level(base.strength, overrides.level_delta)`. `_requirement_digest` adds `profile`, `track`, `strength`, `budget_step_down`.
- [ ] Step 1: Write the failing test
```python
B1 = CallBudget(1_000, 100)
def test_profile_defaults_are_the_approved_track_and_level():
    want = {"cheap_structured": ("reasoning", "economy", True), "standard_generation": ("reasoning", "balanced", True),
            "deep_review": ("reasoning", "strong", False), "independent_review": ("reasoning", "strong", False),
            "deep_code": ("coding", "strong", True), "vision": ("reasoning", "balanced", False)}
    assert {n: (p.track, p.strength, p.budget_step_down) for n, p in PROFILES.items()} == want
def test_build_carries_profile_track_and_level():
    r = build_requirement("deep_code", B1)
    assert (r.profile, r.track, r.strength, r.budget_step_down) == ("deep_code", "coding", "strong", True)
def test_funded_policy_holds_the_approved_cutoffs_and_no_score():
    assert dict(FUNDED_POLICY.level_top_percent) == {"economy": 50, "balanced": 30, "strong": 10, "strongest": None}
    assert (FUNDED_POLICY.max_publish_age_days, FUNDED_POLICY.max_chain_slots) == (7, 2)
    assert {f.name for f in fields(FundedPolicy)} == {"level_top_percent", "max_publish_age_days", "max_chain_slots"}
@pytest.mark.parametrize("profile,delta,want", [("deep_code", 1, "strongest"), ("deep_code", 5, "strongest"),
    ("deep_code", -1, "balanced"), ("cheap_structured", -3, "economy"), ("standard_generation", 0, "balanced")])
def test_level_delta_shifts_the_profile_level_for_one_call(profile, delta, want):   # offline snapshot (tests/conftest.py)
    req, _ = resolve_chain([], profile=profile, max_tokens=1, overrides=RequirementOverrides(level_delta=delta))
    assert req.strength == want
    assert resolve_chain([], profile=profile, max_tokens=1)[0].strength == PROFILES[profile].strength
def test_requirement_digest_sees_profile_track_and_level():
    a = _requirement_digest(build_requirement("deep_review", B1))
    assert a != _requirement_digest(build_requirement("independent_review", B1))
    assert a != _requirement_digest(build_requirement("deep_review", B1, strength="strongest"))
    assert a != _requirement_digest(build_requirement("deep_review", B1, budget_step_down=True))
    assert a == _requirement_digest(build_requirement("deep_review", B1))
```
- [ ] Step 2: `pytest tests/unit/test_funded_policy.py -q` → FAIL (`ImportError: FUNDED_POLICY`).
- [ ] Step 3: Implement. Extend the `policy.py` module docstring with a "Funded policy (spec 027)" paragraph: the cut-offs are percent of that day's scored population, approved 2026-11-23; no score value lives in the repository.
- [ ] Step 4: `pytest tests/unit/test_funded_policy.py tests/unit/test_model_selection_profiles.py tests/unit/test_model_selection_policy.py tests/unit/test_selection_identity.py tests/unit/test_model_selection_route.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/model_selection/policy.py src/llmxive/model_selection/profiles.py src/llmxive/model_selection/route.py src/llmxive/model_selection/__init__.py tests/unit/test_funded_policy.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): funded policy cut-offs, per-profile track and level, level_delta override" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 12: Strength levels — population, percentile cut-off, near-ties
**Files:** Create `src/llmxive/model_selection/strength.py`, `tests/helpers/funded.py` (rating tables and ids; Task 13 adds the snapshot builder), `tests/unit/test_model_selection_strength.py`
**Interfaces:**
- Consumes: Task 6 `ArenaScore`, `ModelScores`, `Track`, `StrengthLevel`; Task 11 `FundedPolicy`, `FUNDED_POLICY`.
- Produces:
```python
def repo_of(model_id: str) -> str                                       # "acme/alpha-large:prov-a" → "acme/alpha-large"
def track_population(scores: Mapping[str, ModelScores], track: Track, *, today: date,
                     max_publish_age_days: int) -> dict[str, ArenaScore]      # repo → score; (today - publish_date).days <= max age
def cutoff_index(n: int, top_percent: int | None) -> int                # None → 0; else max(0, ceil(top_percent * n / 100) - 1), integers only
def level_qualifiers(population: Mapping[str, ArenaScore], level: StrengthLevel,
                     policy: FundedPolicy) -> frozenset[str]                  # repos with rating_upper >= cut-off repo's rating_lower
```
  Population order: `rating` descending, then repo id ascending. Empty population → `frozenset()`.
- `tests/helpers/funded.py` (fictional `acme/…` ids so the pin detector never matches them): `PUBLISHED = date(2026, 11, 22)`; repos `REPO_A = "acme/alpha-large"`, `REPO_B = "acme/beta-mini"`, `REPO_C = "acme/gamma-vision"`, `REPO_D = "acme/delta-unscored"`, `REPO_E = "acme/gpt-oss-120b"` (family `gpt-oss`, in the reviewed table), `FILLERS = tuple(f"acme/filler-{i:02d}" for i in range(1, 17))`; every rating below is `(rating, rating − 5, rating + 5)` unless given as a triple — synthetic test data, not LMArena numbers:
|track|order (rating)|
|-|-|
|`REASONING`|A 1400; E (1390, 1380, 1400); F01 1376; F02 1360; F03 1350; C 1340; F04 1330; F05 1320; F06 1310; B 1300; F07 1290; F08…F16 1280, 1270, …, 1200|
|`CODING`|B 1500; A 1480; F01…F16 1460, 1450, …, 1310; C 1290; E 1280|
  so with n = 20 the cut-off indices are economy 9, balanced 5, strong 1, strongest 0.
- [ ] Step 1: Write the failing test
```python
pop = lambda table: {repo: ArenaScore(*table[repo], PUBLISHED) for repo in table}
R, C_ = pop(REASONING), pop(CODING); F = FILLERS
@pytest.mark.parametrize("n,pct,idx", [(20, 50, 9), (20, 30, 5), (20, 10, 1), (20, None, 0), (10, 30, 2), (1, 50, 0),
    (63, 50, 31), (63, 30, 18), (63, 10, 6), (3, 10, 0), (0, 50, 0)])
def test_cutoff_index_is_integer_arithmetic(n, pct, idx):            # Review Focus 2: ceil(0.3*10) would give 3, not 2
    assert cutoff_index(n, pct) == idx
def test_level_qualifiers_on_the_reasoning_table():                   # near-ties at the boundary qualify (>=)
    q = lambda lvl: level_qualifiers(R, lvl, FUNDED_POLICY)
    assert q("strongest") == {REPO_A, REPO_E}                         # E's upper 1400 >= A's lower 1395
    assert q("strong") == {REPO_A, REPO_E, F[0]}                      # F01 upper 1381 >= E lower 1380
    assert q("balanced") == {REPO_A, REPO_E, F[0], F[1], F[2], REPO_C, F[3]}    # F04 upper 1335 == C lower 1335
    assert q("economy") == q("balanced") | {F[4], F[5], REPO_B, F[6]}           # F07 upper 1295 == B lower 1295
def test_level_qualifiers_on_the_coding_table():
    q = lambda lvl: level_qualifiers(C_, lvl, FUNDED_POLICY)
    assert q("strongest") == {REPO_B} and q("strong") == {REPO_B, REPO_A}
    assert q("balanced") == {REPO_B, REPO_A, *F[:5]} and q("economy") == {REPO_B, REPO_A, *F[:9]}
def test_levels_nest_on_both_tables():
    for p in (R, C_):
        s = [level_qualifiers(p, lvl, FUNDED_POLICY) for lvl in ("strongest", "strong", "balanced", "economy")]
        assert s[0] <= s[1] <= s[2] <= s[3]
def test_zero_width_interval_and_rating_ties_are_deterministic():
    p = {"x/a": ArenaScore(1000.0, 1000.0, 1000.0, PUBLISHED), "x/b": ArenaScore(1000.0, 1000.0, 1000.0, PUBLISHED),
         "x/c": ArenaScore(999.0, 999.0, 999.0, PUBLISHED)}
    assert level_qualifiers(p, "strongest", FUNDED_POLICY) == {"x/a", "x/b"}
    assert level_qualifiers({}, "economy", FUNDED_POLICY) == frozenset()
def test_track_population_drops_stale_rows_and_other_tracks():
    s = lambda d: ArenaScore(1300.0, 1290.0, 1310.0, d)
    scores = {"acme/a:p1": ModelScores(reasoning=s(date(2026, 11, 16))), "acme/a:p2": ModelScores(reasoning=s(date(2026, 11, 16))),
              "acme/b:p1": ModelScores(reasoning=s(date(2026, 11, 15))), "acme/d:p1": ModelScores(coding=s(PUBLISHED))}
    got = track_population(scores, "reasoning", today=date(2026, 11, 23), max_publish_age_days=7)
    assert set(got) == {"acme/a"}                                     # 7 days old is in, 8 is out, coding-only is out
```
- [ ] Step 2: `pytest tests/unit/test_model_selection_strength.py -q` → FAIL (`ModuleNotFoundError: llmxive.model_selection.strength`).
- [ ] Step 3: Implement `strength.py` (pure; no I/O, no clock) and the helper tables.
- [ ] Step 4: `pytest tests/unit/test_model_selection_strength.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/model_selection/strength.py tests/helpers/funded.py tests/unit/test_model_selection_strength.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): relative strength levels (percentile cut-off, interval near-ties)" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 13: `select` — funded eligibility
**Files:** Modify `src/llmxive/model_selection/select.py` (46-51 `_component_of`, 115-197 `select` loop, 250-265 `_no_candidate_reason`), `tests/helpers/funded.py` (snapshot builder) · Test `tests/unit/test_model_selection_funded_select.py`
**Interfaces:**
- Consumes: Tasks 6, 10 (snapshot shape), 11 (`FUNDED_POLICY`), 12 (`track_population`, `repo_of`).
- Produces: `select(requirement, snapshot, *, policy: CapabilityPolicy | None = None, funded_policy: FundedPolicy | None = None) -> ModelChain` (default `FUNDED_POLICY`); `_component_of` returns `"hf_catalog"` for the `huggingface` backend.
- Eligibility of a `huggingface` candidate (replaces steps (b), (c), (f) of the loop for that backend; (d) exclusions and (e) required independence are unchanged): `hf_catalog` **and** `leaderboard` neither `unavailable` nor `last_known_good` older than `max_catalog_age_s`; `snapshot.funded` present with `source == "live"`; `requirement.track` and `requirement.strength` both set; the candidate's repo in `track_population(snapshot.scores, requirement.track, today=snapshot.observed_at.date(), max_publish_age_days=funded_policy.max_publish_age_days)`; `requirement.capability == "vision"` ⇒ `"vision" in observed.features`; each `required_features` item that is one of `structured`/`tools`/`vision` in `observed.features`, every other item (e.g. `reasoning`) in the reviewed family entry's features — no family entry → ineligible; `min_context_tokens <= observed.context_length` (unknown length fails a stated minimum); price known; `not requirement.require_paid`. `allow_paid`, the opt-in flag, the reviewed table's `capabilities` and `quality_tier` are not consulted for this backend. The allowance and `max_credits` are **not** applied here (Task 14 needs the unfiltered level pick to detect budget pressure); level qualification is Task 14's. `approved_ceiling_credits` for a funded candidate is `snapshot.funded.available_usd * USD_TO_CREDITS`. In this task funded candidates still sort with the existing key.
- `tests/helpers/funded.py` additions. USD per token, `BUDGET = CallBudget(10_000, 2_000)`, `NOW = datetime(2026, 11, 23, 12, tzinfo=UTC)`:
|name|model_id|in / out|worst case|context|features|
|-|-|-|-|-|-|
|`A`|`acme/alpha-large:prov-a`|2e-6 / 8e-6|0.036|200000|structured, tools|
|`A2`|`acme/alpha-large:prov-b`|1e-6 / 4e-6|0.018|32000|structured|
|`B`|`acme/beta-mini:prov-a`|1e-7 / 4e-7|0.0018|128000|structured|
|`C`|`acme/gamma-vision:prov-c`|5e-7 / 2e-6|0.009|128000|structured, vision|
|`D`|`acme/delta-unscored:prov-a`|1e-7 / 1e-7|0.0012|128000|structured (no score)|
|`E`|`acme/gpt-oss-120b:prov-a`|2e-7 / 8e-7|0.0036|128000|structured|
|`FX`|`f"{repo}:prov-z"` for each of `FILLERS`|1e-5 / 4e-5|0.18|128000|none|
  Scores: every repo in `REASONING`/`CODING` (Task 12) gets both tracks, `publish_date=PUBLISHED`. `snapshot(*, dartmouth: tuple[str, ...] = (), claude: bool = False, paid_opt_in: bool = False, local: bool = True, hf: tuple[str, ...] = ALL_HF, sources: dict[str, tuple[str, float]] | None = None, available_usd: float | None = 5.0, prices: dict[str, tuple[float, float]] | None = None, publish_dates: dict[str, date] | None = None) -> RuntimeSnapshot` (all six components `live`/age 0 unless `sources` overrides `(source, age_s)`; `available_usd=None` → `funded=None` and `"funded"` unavailable; the guard otherwise reports `monthly_usd=50.0, spent_month_usd=10.0`, epoch `"2026-11"`; `prices` / `publish_dates` override per model id / per repo); `sel(profile, snap, pol=FUNDED_POLICY, **req_overrides)` = `select(build_requirement(profile, BUDGET, **req_overrides), snap, funded_policy=pol)`; `policy_with(**changes)` = `dataclasses.replace(FUNDED_POLICY, **changes)`; `ids(chain)` / `order(chain)`; the ids `GLM`, `QWEN`, `GEMMA4`, `GPT_OSS`, `CLAUDE`, `LOCAL` as in `tests/unit/test_model_selection_select.py:35-41,666`.
- [ ] Step 1: Write the failing test
```python
WIDE = {"max_candidates": 99}
SCORED_HF = {A, A2, B, C, E, *FX}
def test_score_track_and_flags_decide_eligibility():
    assert ids(sel("cheap_structured", snapshot(local=False), **WIDE)) == SCORED_HF          # D has no score
    assert ids(sel("deep_code", snapshot(local=False), **WIDE)) == SCORED_HF
    assert ids(sel("vision", snapshot(), **WIDE)) == {C}                                     # the only image-input model
@pytest.mark.parametrize("snap_kw", [                                    # Review Focus 1
    {"sources": {"leaderboard": ("unavailable", 0.0)}}, {"sources": {"leaderboard": ("last_known_good", 3601.0)}},
    {"sources": {"hf_catalog": ("last_known_good", 3601.0)}}, {"sources": {"hf_catalog": ("unavailable", 0.0)}},
    {"available_usd": None}])
def test_fail_closed_table(snap_kw):
    with pytest.raises(ModelUnavailable): sel("deep_review", snapshot(local=False, **snap_kw))
def test_a_requirement_without_track_and_level_gets_no_funded_candidate():
    with pytest.raises(ModelUnavailable):
        select(ModelRequirement(capability="deep", call_budget=BUDGET), snapshot(local=False))
def test_stale_publish_date_is_ineligible_and_leaves_the_population():                     # Review Focus 1
    got = ids(sel("cheap_structured", snapshot(local=False, publish_dates={REPO_B: date(2026, 11, 15)}), **WIDE))
    assert B not in got and E in got
    with pytest.raises(ModelUnavailable):
        sel("deep_review", snapshot(local=False, publish_dates={r: date(2026, 11, 1) for r in REASONING}))
def test_leaderboard_lkg_at_exactly_the_limit_is_still_fresh():
    assert A in ids(sel("deep_review", snapshot(sources={"leaderboard": ("last_known_good", 3600.0)}), **WIDE))
def test_unobservable_features_and_context():                                              # Review Focus 6
    assert ids(sel("deep_review", snapshot(), required_features=frozenset({"reasoning"}), **WIDE)) == {E}
    assert ids(sel("deep_review", snapshot(), required_features=frozenset({"tools"}), **WIDE)) == {A}
    got = ids(sel("deep_review", snapshot(), min_context_tokens=100_000, **WIDE))
    assert A in got and A2 not in got                                     # same repo, provider B has 32000
def test_funded_needs_no_opt_in_and_is_funded_class():
    chain = sel("cheap_structured", snapshot(local=False), **WIDE)
    assert all(c.cost_class == "funded" for c in chain.candidates)
    assert all(c.approved_ceiling_credits == pytest.approx(5000.0) for c in chain.candidates)
def test_no_hugging_face_models_leaves_existing_behaviour_untouched():
    snap = snapshot(dartmouth=(GLM, QWEN, GEMMA4, GPT_OSS), hf=(), available_usd=None)
    assert order(sel("deep_review", snap)) == [GLM, QWEN, GEMMA4, GPT_OSS]
```
- [ ] Step 2: `pytest tests/unit/test_model_selection_funded_select.py -q` → FAIL (`TypeError: select() got an unexpected keyword argument 'funded_policy'`).
- [ ] Step 3: Implement the funded branch in the eligibility loop and the helper's snapshot builder; extend `_no_candidate_reason` with the `hf_catalog`/`leaderboard`/`funded` sources.
- [ ] Step 4: `pytest tests/unit/test_model_selection_funded_select.py tests/unit/test_model_selection_select.py tests/unit/test_config_consistency.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/model_selection/select.py tests/helpers/funded.py tests/unit/test_model_selection_funded_select.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): funded eligibility in select (track score, publish freshness, observed flags; fail closed)" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 14: `select` — level qualification, cheapest-within-level, budget step-down, class ordering, freshness
**Files:** Modify `src/llmxive/model_selection/select.py` (88-112 `_enforce_fresh_snapshot`, 199-247 ordering), `src/llmxive/model_selection/policy.py` (86: `SELECTION_POLICY_VERSION = 4`; docstring "v4 (spec 027)" paragraph), `tests/unit/test_model_selection_policy.py` (22), `tests/unit/test_model_selection_select.py` (490, 674), `tests/unit/test_self_improvement_invocation_identity.py` (131) · Test: append to `tests/unit/test_model_selection_funded_select.py`
**Interfaces:**
- Consumes: Task 12 `level_qualifiers`, `track_population`, `repo_of`; Task 6 `worst_case_usd`, `STRENGTH_LEVELS`.
- Produces: class rank free-remote 0 → funded 1 → free-local 2 → paid 3 as the first sort key; the funded group built by `_funded_group` below; paid candidates dropped when the allowance is what emptied the funded group, unless `require_paid`; `_enforce_fresh_snapshot` rewritten per spec 5.9.3; `_no_candidate_reason` includes the funded explanation lines.
- Algorithm the tests do not fully determine:
```python
def _funded_group(eligible, req, snap, fp):           # eligible: funded (ModelRef, cost_credits) pairs from Task 13
    pop = track_population(snap.scores, req.track, today=snap.observed_at.date(), max_publish_age_days=fp.max_publish_age_days)
    avail = snap.funded.available_usd * USD_TO_CREDITS
    cap = avail if req.max_credits is None else min(avail, float(req.max_credits))
    level, notes = req.strength, []
    while True:
        q = level_qualifiers(pop, level, fp)
        at_level = [(m, c) for m, c in eligible if repo_of(m.model_id) in q]
        fits = [(m, c) for m, c in at_level if c <= cap]
        notes.append(f"funded: {req.track}/{level} — {len(q)} of {len(pop)} models qualify")
        if fits or not at_level:
            break
        if not req.budget_step_down or level == "economy" or level != req.strength:
            break                                       # reviews, economy, and an already-stepped level stop here
        lower = STRENGTH_LEVELS[STRENGTH_LEVELS.index(level) - 1]
        pick = min(c for _, c in at_level)
        notes.append(f"funded: {level} pick exceeds the allowance (${pick / 1000:.4f} > ${cap / 1000:.4f}) "
                     f"— stepped down to {lower} (budget pressure)")
        level = lower
    if at_level and not fits:
        notes.append("funded allowance exhausted — no step-down for this call; paid not reached (Constitution IV)")
        return [], notes, True                          # allowance_removed=True
    rating = lambda m: pop[repo_of(m.model_id)].rating
    group, families = [], set()
    for m, c in sorted(fits, key=lambda mc: (mc[1], -rating(mc[0]), mc[0].model_id)):
        if m.model_family in families: continue
        group.append((m, c)); families.add(m.model_family)
        if len(group) == fp.max_chain_slots: break
    return group, notes, False
```
  (The loop steps down at most once: on the second pass `level != req.strength`, so it either fits or stops.) Freshness for `require_fresh_snapshot`: the Dartmouth class is fresh when `catalog` and `credit` are both fresh-enough (today's rule); the funded class is fresh when `hf_catalog` and `leaderboard` are fresh-enough and `funded` is `live`. Raise `ModelUnavailable` only when **neither** class is fresh; otherwise drop the candidates of a class that is not fresh (local candidates are never gated, as today). The final chain is free-remote (existing key) + funded group (its own order) + local + paid (existing key, suppressed as above), then cut to `max_candidates`.
- [ ] Step 1: Write the failing test
```python
FULL = dict(dartmouth=(GLM, QWEN, GEMMA4, GPT_OSS), claude=True, paid_opt_in=True)
def test_order_is_free_remote_then_funded_then_local_then_paid():
    assert order(sel("cheap_structured", snapshot(**FULL), allow_paid=True)) == [GLM, QWEN, GEMMA4, GPT_OSS, B, E, LOCAL, CLAUDE]
def test_funded_slots_never_truncate_local_or_paid():                     # Review Focus 5: 8 qualify at balanced, cap 8
    chain = sel("standard_generation", snapshot(**FULL), allow_paid=True)
    assert sum(c.cost_class == "funded" for c in chain.candidates) == 2 and order(chain)[-2:] == [LOCAL, CLAUDE]
@pytest.mark.parametrize("profile,want", [("cheap_structured", [B, E, LOCAL]), ("standard_generation", [E, C, LOCAL]),
    ("deep_review", [E, A2]), ("deep_code", [B, A2]), ("vision", [C])])
def test_cheapest_qualifier_leads_then_other_families(profile, want):
    assert order(sel(profile, snapshot())) == want
def test_a_statistically_tied_cheaper_model_wins_its_level():            # F04 is in "balanced" only by interval overlap
    assert order(sel("standard_generation", snapshot(prices={FX[3]: (1e-8, 1e-8)}))) == [FX[3], E, LOCAL]
def test_population_ignores_call_filters():                              # Review Focus 2: C is "balanced" among all 20, not "strongest" among vision models
    assert order(sel("vision", snapshot())) == [C]
    with pytest.raises(ModelUnavailable): sel("vision", snapshot(), strength="strongest")
def test_tracks_are_ranked_separately():
    assert order(sel("deep_code", snapshot()))[0] == B and order(sel("deep_review", snapshot()))[0] == E
def test_level_raise_and_lower_for_one_call():
    assert order(sel("deep_code", snapshot(), strength="strongest")) == [B]
    assert order(sel("cheap_structured", snapshot(), strength="balanced")) == [E, C, LOCAL]
def test_generation_steps_down_one_level_under_budget_pressure():
    chain = sel("standard_generation", snapshot(available_usd=0.003))
    assert order(chain) == [B, LOCAL]
    assert any("stepped down to economy (budget pressure)" in e for e in chain.explanation)
def test_step_down_is_one_level_only():
    with pytest.raises(ModelUnavailable, match="funded allowance exhausted"):
        sel("deep_code", snapshot(available_usd=0.001))                   # strong → balanced still does not fit
def test_review_never_steps_down():                                       # Review Focus 5
    with pytest.raises(ModelUnavailable, match="funded allowance exhausted"):
        sel("deep_review", snapshot(available_usd=0.003))
    assert order(sel("deep_review", snapshot(available_usd=0.004))) == [E]   # A2 (0.018) no longer fits
def test_exhausted_allowance_is_outage_not_paid():                        # Review Focus 5
    snap = snapshot(claude=True, paid_opt_in=True, available_usd=0.001)
    chain = sel("cheap_structured", snap, allow_paid=True)                # economy cannot step down
    assert order(chain) == [LOCAL] and any("funded allowance exhausted" in e for e in chain.explanation)
    with pytest.raises(ModelUnavailable): sel("deep_review", snap, allow_paid=True)
    assert order(sel("deep_review", snap, allow_paid=True, require_paid=True)) == [CLAUDE]   # an explicit paid rung is still paid
def test_max_credits_bounds_funded_like_the_allowance():
    assert order(sel("deep_review", snapshot(), max_credits=10)) == [E]  # 0.0036 USD = 3.6 credits; A2 = 18
def test_require_paid_excludes_funded():                                  # Review Focus 5
    assert order(sel("deep_review", snapshot(claude=True, paid_opt_in=True), allow_paid=True, require_paid=True)) == [CLAUDE]
def test_independence_dimensions_work_unchanged():
    base = IndependenceBaseline(families=frozenset({"gpt-oss"}))
    assert order(sel("independent_review", snapshot(), independence_against=base)) == [A2, FX[0]]
def test_chain_explanation_names_track_level_and_population():
    assert any(e.startswith("funded: reasoning/strong — 3 of 20 models qualify") for e in sel("deep_review", snapshot()).explanation)
STALE = ("last_known_good", 901.0); GONE = ("unavailable", 0.0)
def test_review_is_served_by_funded_when_dartmouth_is_not_fresh():
    assert order(sel("independent_review", snapshot(dartmouth=(QWEN,), sources={"catalog": STALE, "credit": GONE}))) == [E, A2]
def test_review_is_served_by_dartmouth_when_funded_is_not_fresh():
    for bad in ({"leaderboard": STALE}, {"hf_catalog": GONE}):
        assert order(sel("independent_review", snapshot(dartmouth=(QWEN, GEMMA4), sources=bad))) == [QWEN, GEMMA4]
    assert order(sel("independent_review", snapshot(dartmouth=(QWEN, GEMMA4), available_usd=None))) == [QWEN, GEMMA4]
def test_review_is_an_outage_only_when_no_class_is_fresh():
    with pytest.raises(ModelUnavailable, match="fresh"):
        sel("independent_review", snapshot(dartmouth=(QWEN,), sources={"credit": GONE, "leaderboard": STALE}))
def test_select_stays_byte_identical_and_versioned():
    s = snapshot(dartmouth=(QWEN,)); assert sel("deep_review", s) == sel("deep_review", s)
    assert sel("deep_review", s).selection_policy_version == 4
```
- [ ] Step 2: `pytest tests/unit/test_model_selection_funded_select.py -q` → FAIL (`test_order_is_free_remote…`: funded candidates not ordered before `LOCAL`).
- [ ] Step 3: Implement `_funded_group`, the class ordering, the paid suppression and the freshness rewrite; bump the version to 4 and change the four pinned `3`s listed in **Files** to `4`.
- [ ] Step 4: `pytest tests/unit/test_model_selection_funded_select.py tests/unit/test_model_selection_select.py tests/unit/test_model_selection_policy.py tests/unit/test_self_improvement_invocation_identity.py tests/unit/test_selection_identity.py tests/unit/test_config_consistency.py tests/unit/test_us5_ac1_primary_preservation.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/model_selection/select.py src/llmxive/model_selection/policy.py tests/unit/test_model_selection_funded_select.py tests/unit/test_model_selection_policy.py tests/unit/test_model_selection_select.py tests/unit/test_self_improvement_invocation_identity.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): relative-strength funded ranking, budget step-down, free-remote > funded > local > paid, class-aware review freshness" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 15: `execute` / `route_chat` — reserve, dispatch once, settle the real cost
**Files:** Modify `src/llmxive/model_selection/execute.py` (94-106, new `_open_funded_reservation` after 246, 249-265, 381-423, 490-512, 541-562), `src/llmxive/model_selection/route.py` (223-243 `_select_audited`, 246-314 `resolve_chain`, 347-368 `route_chat` signature, 484-495 the `execute` call), `README.md` ("Models and compute", 113-145), `CLAUDE.md` (20-21) · Test `tests/integration/test_funded_execute.py`
**Interfaces:**
- Consumes: `hf_budget.{funded_observer, settle_funded}`, `ledger_transport.funded_ledger_config_from_env`, `reservations.{reserve, ReservationLease, lease_duration_for}`, `Candidate.cost_class`, `ChatResponse.input_tokens/output_tokens`, `huggingface.PreInferenceRejection`, Task 13 `select(..., funded_policy=)`.
- Produces: `execute(..., funded_ledger_config: LedgerConfig | None = None, funded_observer: Callable[[], CreditObservation] | None = None)`; `ExecutionResult.charged_usd: float | None = None`; `route_chat(..., funded_ledger_config: LedgerConfig | None = None, funded_policy: FundedPolicy | None = None)`; `resolve_chain(..., funded_policy: FundedPolicy | None = None)` and `_select_audited(..., funded_policy=None)` forward it to `select` (an injection seam beside `snapshot=`; `None` → `FUNDED_POLICY`).
- Behaviour: branch on `candidate.cost_class` (the existing `not pricing.is_free` tests at 390 and 403 become `== "paid"`). For `"funded"`: skip (advance) unless `chain.snapshot_provenance["funded"].source == "live"` and a ledger repo and config resolve (`None` → `funded_ledger_config_from_env()`, a `LedgerError` skips); reserve `worst_case_credits / USD_TO_CREDITS` once — never `× retries` — under the same lease heartbeat; a `LedgerError` skips; dispatch with `retries=1`; in `finally`, `settle_funded(charged_usd=…)` where the charge is `input_tokens × pricing.input + output_tokens × pricing.output` when the response carries both counts, `0.0` when the failure `isinstance(exc, PreInferenceRejection)` (HTTP 401/402/403, or never sent — spec 5.9.2 amended), and `None` (full reservation) on any other failure or a response without usage; return the response with `cost_estimate_usd` set to that charge. `ReservationOpened`/`DispatchStarted`/`CandidateOutcome` are emitted as for paid; `reservation_authority` (whose unit is Dartmouth credits) is not consulted for funded.
- README "Models and compute": the order free hosted → Hugging Face (funded, within `LLMXIVE_HF_MONTHLY_USD`) → local → paid; the funded model is the cheapest one whose LMArena score is in the profile's strength level among the models routable that day; scores come from the LMArena leaderboard dataset (`lmarena-ai/leaderboard-dataset`, CC-BY-4.0, attributed here), are used for internal ranking only, and are never committed (spec 5.9.7, now LMArena); the new env vars. `CLAUDE.md:20-21`: backends are Dartmouth Chat + Hugging Face Inference Providers + local transformers.
- [ ] Step 1: Write the failing test (real git ledger in `tmp_path`; the fake backend is the `backend_factory` seam FR-015 sanctions)
```python
CFG = LedgerConfig(remote=None, ref=FUNDED_LEDGER_REF); MSG = [ChatMessage("user", "hi")]   # `repo`: the Task 7 git fixture
OBS = lambda cap=1.0: (lambda: CreditObservation(spend=0.0, effective_cap=cap, budget_epoch="2026-11"))
class _HF:                                   # scripted per model; counts calls
    def __init__(self, script): self.script, self.calls = script, []
    def chat(self, messages, *, model=None, max_tokens=None, temperature=None, deadline_s=None):
        self.calls.append(model); r = self.script.get(model, "ok")
        if isinstance(r, BaseException): raise r
        return r if isinstance(r, ChatResponse) else ChatResponse("ok", model, "huggingface", input_tokens=1200, output_tokens=300)
def _run(repo, be, chain, **kw):
    return execute(chain, MSG, options=ExecutionOptions(max_tokens=512), backend_factory=lambda name: be, ledger_repo=repo,
                   funded_ledger_config=CFG, funded_observer=kw.pop("obs", OBS()), now=NOW, **kw)
events = lambda repo: read_events(repo, ref=FUNDED_LEDGER_REF)
charged = lambda repo: {e["reservation_id"]: e["charged"] for e in events(repo) if e["type"] == "reconciled"}
def test_funded_reserve_call_settle_records_real_cost(repo):
    res = _run(repo, _HF({}), sel("cheap_structured", snapshot(local=False)))       # leader B
    opened = next(e for e in events(repo) if e["type"] == "open"); done = next(e for e in events(repo) if e["type"] == "reconciled")
    assert opened["model"] == B and opened["worst_case_credits"] == pytest.approx(0.0018) and opened["budget_epoch"] == "2026-11"
    assert done["charged"] == pytest.approx(1200 * 1e-7 + 300 * 4e-7)               # usage × the priced provider's rate
    assert res.charged_usd == done["charged"] == res.response.cost_estimate_usd
    assert read_events(repo) == []                                                   # Dartmouth credit ledger untouched
def test_funded_dispatches_once_and_reserves_times_one(repo):                       # Review Focus 4
    be = _HF({B: TransientBackendError("503"), E: TransientBackendError("503")})
    with pytest.raises(ChainExhausted): _run(repo, be, sel("cheap_structured", snapshot(local=False)), retries=3)
    assert be.calls == [B, E]                                                        # one attempt each despite retries=3
    assert [e["worst_case_credits"] for e in events(repo) if e["type"] == "open"] == [pytest.approx(0.0018), pytest.approx(0.0036)]
def test_missing_usage_charges_full_reservation(repo):                              # Review Focus 4
    _run(repo, _HF({B: ChatResponse("ok", B, "huggingface")}), sel("cheap_structured", snapshot(local=False)))
    assert list(charged(repo).values()) == [pytest.approx(0.0018)]
def test_failed_call_is_charged_its_reservation_and_chain_advances(repo):
    res = _run(repo, _HF({B: TransientBackendError("503")}), sel("cheap_structured", snapshot(local=False)))
    assert res.model_ref.model_id == E
    assert sorted(charged(repo).values()) == [pytest.approx(1200 * 2e-7 + 300 * 8e-7), pytest.approx(0.0018)]
@pytest.mark.parametrize("exc", [HFPaymentRequired("402"), HFCredentialRejected("401", http_status=401),
    HFCredentialRejected("403", http_status=403), HFCredentialRejected("no bill-to", http_status=None)])
def test_pre_inference_rejection_charges_zero(repo, exc):                           # spec 5.9.2 amended — Review Focus 4
    res = _run(repo, _HF({B: exc}), sel("cheap_structured", snapshot(local=False)))
    assert res.model_ref.model_id == E                                               # 402 advances, 401/403 skip — the chain goes on
    assert sorted(charged(repo).values()) == [0.0, pytest.approx(1200 * 2e-7 + 300 * 8e-7)]
def test_denied_reservation_skips_to_the_next_class_without_a_call(repo):
    class _Local(_HF):
        def chat(self, messages, **kw): self.calls.append(kw["model"]); return ChatResponse("local", kw["model"], "local")
    hf, local = _HF({}), _Local({})
    res = execute(sel("cheap_structured", snapshot()), MSG, options=ExecutionOptions(max_tokens=512), ledger_repo=repo,
                  backend_factory=lambda n: local if n == "local" else hf, funded_ledger_config=CFG, funded_observer=OBS(cap=0.0), now=NOW)
    assert hf.calls == [] and res.model_ref.backend == "local" and events(repo) == []
def test_funded_skipped_when_guard_was_not_live_at_selection(repo):
    chain = sel("cheap_structured", snapshot(local=False))
    stale = replace(chain, snapshot_provenance={**chain.snapshot_provenance, "funded": SnapshotProvenance("unavailable", NOW, 0.0)})
    be = _HF({})
    with pytest.raises(ChainExhausted): _run(repo, be, stale)
    assert be.calls == []
def test_unconfigured_production_ledger_fails_closed(repo, monkeypatch):
    monkeypatch.delenv("LLMXIVE_FUNDED_LEDGER_ANCHOR", raising=False); be = _HF({})
    with pytest.raises(ChainExhausted):
        execute(sel("cheap_structured", snapshot(local=False)), MSG, options=ExecutionOptions(max_tokens=512),
                backend_factory=lambda n: be, ledger_repo=repo, now=NOW)
    assert be.calls == []
def test_route_chat_serves_funded_through_the_policy_seam(repo):
    be = _HF({})
    r = route_chat(MSG, profile="deep_review", max_tokens=512, snapshot=snapshot(local=False), backend_factory=lambda n: be,
                   ledger_repo=repo, funded_ledger_config=CFG, funded_policy=policy_with(max_chain_slots=1))
    assert r.backend == "huggingface" and r.model == E and r.cost_estimate_usd > 0 and be.calls == [E]
```
- [ ] Step 2: `pytest tests/integration/test_funded_execute.py -q` → FAIL (`TypeError: execute() got an unexpected keyword argument 'funded_ledger_config'`).
- [ ] Step 3: Implement the funded branch in `execute` and the `funded_policy` / `funded_ledger_config` threading in `route.py`. Update README and `CLAUDE.md` in this commit.
- [ ] Step 4: `pytest tests/integration/test_funded_execute.py tests/integration/test_model_selection_execute.py tests/unit/test_model_selection_execute.py tests/unit/test_model_selection_route.py tests/unit/test_selection_identity.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/model_selection/execute.py src/llmxive/model_selection/route.py README.md CLAUDE.md tests/integration/test_funded_execute.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): funded reserve -> single dispatch -> settle at usage x catalog price (zero for 401/402/403)" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 16: Truthful run-log entries
**Files:** Modify `src/llmxive/state/runlog.py` (32-66), `src/llmxive/agents/base.py` (158, 173-182, 220-236), `src/llmxive/speckit/slash_command.py` (144, 158, 170-175, 195-208), `src/llmxive/agents/implementer.py` (1069-1073, 1722-1731, 2040-2056) · Test `tests/unit/test_runlog_funded.py`
**Interfaces:**
- Consumes: `BackendName.HUGGINGFACE`, `ChatResponse.cost_estimate_usd` (set by `execute` in Task 15).
- Produces: `_check_cost_invariant` accepts a non-zero cost when `entry.backend is BackendName.HUGGINGFACE` (allowance-guarded in code; Constitution IV 1.4.0) and still raises for any other backend without `LLMXIVE_PAID_OPT_IN`; each of the three run-log writers records the **sum** of `cost_estimate_usd` over every response received in that run and the backend of the last response (the implementer via new `self._last_cost_usd: float`, and `BackendName(self._last_backend_used)` instead of the `DARTMOUTH` placeholder at 1070 once a response exists).
- [ ] Step 1: Write the failing test
```python
def _entry(backend, cost): ...   # as tests/integration/test_free_backend_only.py::_cost_entry, with `backend=` a parameter
def test_funded_cost_is_logged_without_paid_opt_in(tmp_path, monkeypatch):
    monkeypatch.delenv("LLMXIVE_PAID_OPT_IN", raising=False); _mk_state(tmp_path)
    path = append_entry(_entry(BackendName.HUGGINGFACE, 0.0123), repo_root=tmp_path)
    row = json.loads(path.read_text().splitlines()[-1])
    assert row["backend"] == "huggingface" and row["cost_estimate_usd"] == 0.0123
def test_dartmouth_cost_still_needs_the_opt_in(tmp_path, monkeypatch):
    monkeypatch.delenv("LLMXIVE_PAID_OPT_IN", raising=False); _mk_state(tmp_path)
    with pytest.raises(CostInvariantError): append_entry(_entry(BackendName.DARTMOUTH, 0.0123), repo_root=tmp_path)
def test_agent_run_log_records_the_response_backend_and_cost(...):
    # Drive Agent.run with the stub the repo already uses for this boundary (the same
    # `chat_with_fallback` module attribute tests/conftest.py replaces for task_verifier), returning
    # ChatResponse("…", "acme/alpha-large:prov-a", "huggingface", cost_estimate_usd=0.0123); assert the
    # appended RunLogEntry has backend is BackendName.HUGGINGFACE and cost_estimate_usd == 0.0123.
def test_implementer_run_log_attributes_funded_backend_and_cost(...):          # Review Focus 4
    # Two tasks answered by "huggingface" at 0.01 and 0.02 → entry.backend is HUGGINGFACE, cost == pytest.approx(0.03).
```
  For the last two, build the agent and context exactly as the nearest existing test does (`git grep -ln "chat_with_fallback" tests/unit tests/integration | head`) — see "Not determined from the code" for why this plan does not name it.
- [ ] Step 2: `pytest tests/unit/test_runlog_funded.py -q` → FAIL (`CostInvariantError` in the first test).
- [ ] Step 3: Implement the four edits; update the `CostInvariantError` docstring to name the funded path.
- [ ] Step 4: `pytest tests/unit/test_runlog_funded.py tests/integration/test_free_backend_only.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/state/runlog.py src/llmxive/agents/base.py src/llmxive/speckit/slash_command.py src/llmxive/agents/implementer.py tests/unit/test_runlog_funded.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "fix(027): run log records the real backend and cost of funded calls" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 17: Tier ladder — each free rung raises the funded level
**Files:** Modify `src/llmxive/state/execution_status.py` (50-68 ladder comment, 77-100 `TierConstraint`, 103-113 rungs), `src/llmxive/model_selection/route.py` (303-312 leader-exclusion loop in `resolve_chain`) · Test: append to `tests/unit/test_execution_tier_constraints.py`
**Interfaces:**
- Consumes: `RequirementOverrides.level_delta` (Task 6), the `level_delta` merge in `resolve_chain` (Task 11), `Candidate.cost_class`, `tests/helpers/funded.snapshot` (Task 13).
- Produces: `TierConstraint.level_delta: int = 0`, passed through `to_overrides()`; `_FREE_RUNGS = (TierConstraint(allow_paid=False), TierConstraint(allow_paid=False, exclude_leader=True, level_delta=1), TierConstraint(allow_paid=False, exclude_leaders=2, level_delta=2))`; `_PAID_RUNG` unchanged (`level_delta=0`). The ladder keeps its length (three free rungs + the optional paid rung), so `next_usable_tier`, `tier_constraint`, the corrupt-tier rule and every existing test in the file stay as they are. In `resolve_chain`, a leader-exclusion pass stops as soon as the leader's `cost_class` is not `"free"`: a funded leader is never excluded — for the funded class the rung's escalation is the level raise (spec 5.10 replaces the 5.9.5 "funded best-quality" rung with it).
- [ ] Step 1: Write the failing test
```python
from tests.helpers.funded import B, E, snapshot
from llmxive.model_selection.route import resolve_chain
def test_each_free_rung_raises_the_funded_level_by_its_index(monkeypatch):
    assert [c.to_overrides().level_delta for c in es.model_tier_ladder()] == [0, 1, 2]
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "1")
    assert es.model_tier_ladder()[-1].to_overrides().level_delta == 0 and len(es.model_tier_ladder()) == 4
def test_rungs_climb_levels_and_end_at_strongest_when_dartmouth_is_down():
    snap = snapshot(local=False)
    def walk(profile):
        out = [resolve_chain([], profile=profile, max_tokens=1, overrides=c.to_overrides(), snapshot=snap) for c in es.model_tier_ladder()]
        return [r.strength for r, _ in out], [ch.candidates[0].model_ref.model_id for _, ch in out]
    assert walk("cheap_structured") == (["economy", "balanced", "strong"], [B, E, E])
    assert walk("deep_code") == (["strong", "strongest", "strongest"], [B, B, B])
def test_funded_leader_is_never_excluded():                                # Review Focus 5
    req, chain = resolve_chain([], profile="deep_code", max_tokens=1, snapshot=snapshot(local=False),
                               overrides=RequirementOverrides(exclude_leaders=2, level_delta=1))
    assert [c.model_ref.model_id for c in chain.candidates] == [B] and req.exclude_models == frozenset()
```
  Existing `test_third_free_rung_drops_the_top_two_candidates` (offline Dartmouth snapshot) must still pass unedited: free leaders are excluded exactly as before.
- [ ] Step 2: `pytest tests/unit/test_execution_tier_constraints.py -q` → FAIL (`TypeError: TierConstraint.__init__() got an unexpected keyword argument 'level_delta'`).
- [ ] Step 3: Implement; rewrite the ladder comment block to say each free rung also raises the funded strength level by one (clamped at `strongest`), and that a funded leader is never excluded.
- [ ] Step 4: `pytest tests/unit/test_execution_tier_constraints.py tests/unit/test_execution_exhaustion_flow.py tests/unit/test_convergence_kickback_flow.py tests/unit/test_exclude_leader.py tests/unit/test_selection_identity.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/state/execution_status.py src/llmxive/model_selection/route.py tests/unit/test_execution_tier_constraints.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): fix-loop tier ladder raises the funded strength level one per rung" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 18: `llmxive preflight` selection report
**Files:** Modify `src/llmxive/preflight.py` (1-13 docstring, 27-30, 100-128 `main`) · Test `tests/unit/test_preflight_selection_report.py`
**Interfaces:**
- Consumes: `runtime_snapshot`, `select`, `build_requirement`, `PROFILES`, `FundedPolicy`, `strength.repo_of`, `worst_case_usd`.
- Produces: `selection_report(snap: RuntimeSnapshot, *, funded_policy: FundedPolicy | None = None) -> list[str]` (pure; no network); `main()` appends its lines as `[preflight] info:` after one `runtime_snapshot()` call (catalog and leaderboard GETs and a ledger fetch — no chat request). `"LLMXIVE_HF_BILL_TO"` and `"LLMXIVE_FUNDED_LEDGER_ANCHOR"` join the optional-setting notices. `_REPORT_BUDGET = CallBudget(8_000, 4_096)` — a nominal budget used only to rank for display.
- Line formats (no rating is ever printed): `backends: dartmouth=<source> huggingface=<source> local=<source>` (the `catalog` / `hf_catalog` / `local` provenance); `funded allowance: $50.00/month, spent $10.00 this month, $5.00 available now (2026-11)` or `funded allowance: unavailable`; `leaderboard: <source>, published <latest publish date or n/a>, reasoning <k> models, coding <m> models` (distinct repos with a score on each track); per profile `top candidate [<profile>] <track>/<level>: <model_id> (<backend>, <cost_class>, worst case $<x.xxxx>)` or `top candidate [<profile>] <track>/<level>: none — <first 120 chars of the ModelUnavailable message>`.
- [ ] Step 1: Write the failing test
```python
def test_report_names_backends_allowance_leaderboard_and_top_candidates():
    lines = selection_report(snapshot(dartmouth=(), sources={"catalog": ("unavailable", 0.0)}))
    assert lines[0] == "backends: dartmouth=unavailable huggingface=live local=live"
    assert lines[1] == "funded allowance: $50.00/month, spent $10.00 this month, $5.00 available now (2026-11)"
    assert lines[2] == "leaderboard: live, published 2026-11-22, reasoning 20 models, coding 20 models"
    # at _REPORT_BUDGET: 8000×1e-7 + 4096×4e-7 = 0.0024384
    assert f"top candidate [cheap_structured] reasoning/economy: {B} (huggingface, funded, worst case $0.0024)" in lines
    assert f"top candidate [deep_code] coding/strong: {B} (huggingface, funded, worst case $0.0024)" in lines
    assert sum(l.startswith("top candidate [") for l in lines) == len(PROFILES)
def test_report_says_unavailable_and_none_without_raising():
    lines = selection_report(snapshot(local=False, available_usd=None))
    assert lines[1] == "funded allowance: unavailable"
    assert any(l.startswith("top candidate [deep_review] reasoning/strong: none — ") for l in lines)
def test_report_makes_no_request_and_prints_no_rating():
    with ReplayServer({}) as srv:                      # selection_report takes a snapshot; nothing in it can reach a network
        lines = selection_report(snapshot())
    assert srv.requests == []
    assert not any(str(int(r[0])) in l for l in lines for r in REASONING.values())   # no synthetic rating leaks either
```
- [ ] Step 2: `pytest tests/unit/test_preflight_selection_report.py -q` → FAIL (`ImportError: selection_report`).
- [ ] Step 3: Implement `selection_report` and the `main()` lines; worst case is `worst_case_usd(pricing, _REPORT_BUDGET)` formatted `:.4f`; the track/level shown is the profile's default.
- [ ] Step 4: `pytest tests/unit/test_preflight_selection_report.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/preflight.py tests/unit/test_preflight_selection_report.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): preflight reports backend reachability, allowance, leaderboard coverage and top candidates" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 19: Workflow env wiring
**Files:** Modify `.github/workflows/advance.yml` (86), `llmxive-pipeline.yml` (74, 84), `maintenance.yml` (37), `pipeline-personality.yml` (31), `reprocess.yml` (69), `submission-intake.yml` (42), `prompt-eval.yml` (31), `spec015-calibration.yml` (74), `llmxive-real-call-tests.yml` (187), `llmxive-real-call-nightly.yml` (27), `repair.yml` (61) — the line of each `DARTMOUTH_CHAT_API_KEY: ${{ secrets.DARTMOUTH_CHAT_API_KEY }}` · Test `tests/unit/test_workflow_hf_env.py`
**Interfaces:**
- Produces: in every `env:` mapping that passes `DARTMOUTH_CHAT_API_KEY: ${{ secrets.DARTMOUTH_CHAT_API_KEY }}`, the three lines `HF_TOKEN: ${{ secrets.HF_TOKEN }}`, `LLMXIVE_HF_BILL_TO: ${{ vars.LLMXIVE_HF_BILL_TO }}`, `LLMXIVE_FUNDED_LEDGER_ANCHOR: ${{ vars.LLMXIVE_FUNDED_LEDGER_ANCHOR }}`. The blocks that set the key to `""` (real-call-tests 54, 129; nightly 68) are deliberately keyless and are left alone.
- [ ] Step 1: Write the failing test
```python
WF = Path(__file__).resolve().parents[2] / ".github" / "workflows"
WANT = {"HF_TOKEN": "${{ secrets.HF_TOKEN }}", "LLMXIVE_HF_BILL_TO": "${{ vars.LLMXIVE_HF_BILL_TO }}",
        "LLMXIVE_FUNDED_LEDGER_ANCHOR": "${{ vars.LLMXIVE_FUNDED_LEDGER_ANCHOR }}"}
def _env_blocks(node):
    if isinstance(node, dict):
        if isinstance(node.get("env"), dict): yield node["env"]
        for v in node.values(): yield from _env_blocks(v)
    elif isinstance(node, list):
        for v in node: yield from _env_blocks(v)
def test_every_model_calling_env_block_carries_the_hf_settings():
    seen = 0
    for path in sorted(WF.glob("*.yml")):
        for env in _env_blocks(yaml.safe_load(path.read_text())):
            if "secrets.DARTMOUTH_CHAT_API_KEY" in str(env.get("DARTMOUTH_CHAT_API_KEY", "")):
                seen += 1
                assert {k: env.get(k) for k in WANT} == WANT, path.name
    assert seen >= 12
def test_bill_to_is_a_variable_never_a_secret():
    assert "secrets.LLMXIVE_HF_BILL_TO" not in "".join(p.read_text() for p in WF.glob("*.yml"))
```
- [ ] Step 2: `pytest tests/unit/test_workflow_hf_env.py -q` → FAIL (`advance.yml`: `HF_TOKEN` is `None`).
- [ ] Step 3: Add the lines. Then prove no trigger moved: `git diff -- .github/workflows | grep -nE '^[+-][^+-].*(cron|schedule:|workflow_dispatch|^[+-]on:)'` must print nothing.
- [ ] Step 4: `pytest tests/unit/test_workflow_hf_env.py tests/unit/test_execution_tier_constraints.py -q` → PASS.
- [ ] Step 5: `git add .github/workflows/advance.yml .github/workflows/llmxive-pipeline.yml .github/workflows/maintenance.yml .github/workflows/pipeline-personality.yml .github/workflows/reprocess.yml .github/workflows/submission-intake.yml .github/workflows/prompt-eval.yml .github/workflows/spec015-calibration.yml .github/workflows/llmxive-real-call-tests.yml .github/workflows/llmxive-real-call-nightly.yml .github/workflows/repair.yml tests/unit/test_workflow_hf_env.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "ci(027): pass HF_TOKEN, LLMXIVE_HF_BILL_TO and the funded-ledger anchor to model-calling jobs" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 20: Enforcement — the pin detector sees `<repo>:<provider>`
**Files:** Modify `src/llmxive/model_selection/inventory.py` (59-77 `_HF_ORGS`, 78-80 `_HF_SLASH_MODEL`), `specs/026-model-selection-consolidation/migration_manifest.json`, `migration_manifest.md` (regenerated) · Test: append to `tests/unit/test_model_selection_enforcement.py` and `tests/unit/test_model_selection_inventory.py`
**Interfaces:**
- Consumes: how sanction is decided today — `inventory.categorize` (138) allows a literal only in `_CANONICAL_FILES` (`policy.py`), in a `_CANONICAL_SYMBOLS` pair, or under `tests/`; everything else in `src/llmxive/` is a `migration_target` and `enforcement.find_pin_violations` (69) rejects it unconditionally. This plan adds **no** production model-id literal (the funded selection names no model, and `leaderboard.py` holds a dataset id, not a model id), so neither allowlist is extended.
- Produces: `_HF_SLASH_MODEL` accepts an optional `:<provider>` suffix (`(?::[A-Za-z0-9][A-Za-z0-9._-]*)?`); `_HF_ORGS` gains every org prefix present in `tests/fixtures/hf_funded/router_models.json` (a reviewed literal set, generated once from the fixture).
- [ ] Step 1: Write the failing test
```python
def test_detector_recognises_every_recorded_router_id_with_and_without_provider():
    for m in _load("router_models.json")["payload"]["data"]:
        assert looks_like_model_id(m["id"]), m["id"]
        for p in m["providers"]: assert looks_like_model_id(f"{m['id']}:{p['provider']}")
    assert not looks_like_model_id("state/model_selection") and not looks_like_model_id("acme/alpha-large:prov-a")
    assert not looks_like_model_id("lmarena-ai/leaderboard-dataset")
def test_a_planted_provider_pinned_literal_in_production_is_a_violation(tmp_path):
    rid = _load("router_models.json")["payload"]["data"][0]; pin = f"{rid['id']}:{rid['providers'][0]['provider']}"
    _write(tmp_path / "src/llmxive/backends/huggingface.py", f'DEFAULT = "{pin}"\n')
    assert [v["file"] for v in find_pin_violations(tmp_path)] == ["src/llmxive/backends/huggingface.py"]
def test_the_real_tree_still_has_zero_violations_after_027():
    assert find_violations(REPO_ROOT) == []
```
- [ ] Step 2: `pytest tests/unit/test_model_selection_enforcement.py tests/unit/test_model_selection_inventory.py -q` → FAIL (first new test: an id with a `:provider` suffix is not recognised).
- [ ] Step 3: Implement, then regenerate the manifest: `python -m llmxive.model_selection.inventory`. If `lmarena-ai` is an org in the router catalog, keep the dataset-id assertion by matching the dataset path outside `_HF_SLASH_MODEL`'s scope — do not drop the assertion.
- [ ] Step 4: same command → PASS (including the existing `test_committed_manifest_is_current_with_the_live_scan`).
- [ ] Step 5: `git add src/llmxive/model_selection/inventory.py specs/026-model-selection-consolidation/migration_manifest.json specs/026-model-selection-consolidation/migration_manifest.md tests/unit/test_model_selection_enforcement.py tests/unit/test_model_selection_inventory.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "test(027): pin detector covers Hugging Face repo:provider ids; manifest regenerated" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 21: Real-call lane
**Files:** Create `tests/real_call/test_hf_funded_real.py` · Modify `scripts/hf/README.md` (acceptance evidence for this lane: date, tokens, cost, matched-model counts — no ratings)
**Interfaces:**
- Consumes: everything above. Operator prerequisites, once: `llmxive funded-ledger-bootstrap --remote origin`; set the Actions variables `LLMXIVE_HF_BILL_TO` and `LLMXIVE_FUNDED_LEDGER_ANCHOR`; protect `refs/llmxive/funded-ledger` fast-forward-only.
- Decisions: fast module (not added to `_SLOW_MODULES`); a missing `HF_TOKEN`, `LLMXIVE_HF_BILL_TO` or `LLMXIVE_FUNDED_LEDGER_ANCHOR` **fails** with the variable's name (not a skip); Dartmouth is made unreachable the way `tests/real_call/test_dartmouth_outage_falls_back.py` does it — a `backend_factory` that returns a backend raising `BackendUnavailable` for `"dartmouth"` and `make_backend(name)` otherwise; `max_tokens=1024`, `retries=1`; the spend lands on the production funded ledger (it is real spend on the same resource group). Total: seven short chats plus up to three rejected (unbilled) requests — cents. The lane prints counts and model ids, never a rating. Module helpers: `_reconciled_events()` = `fetch_ledger` then `read_events(repo_root(), ref=FUNDED_LEDGER_REF)` filtered to `type == "reconciled"`, `_reconciled_ids()` their `reservation_id`s; `_dartmouth_down(name)` as above; the image comes from `tests/real_call/test_vision_real.py::_red_square_png` (import it; do not copy it).
- [ ] Step 1: Write the test
```python
pytestmark = pytest.mark.skipif(os.environ.get("LLMXIVE_REAL_TESTS") != "1", reason="real-call test; set LLMXIVE_REAL_TESTS=1")
@pytest.fixture(scope="module", autouse=True)
def _require_settings():
    missing = [v for v in ("LLMXIVE_HF_BILL_TO", "LLMXIVE_FUNDED_LEDGER_ANCHOR") if not os.environ.get(v)]
    assert not missing and load_hf_token(), f"real-call lane needs HF_TOKEN and {missing}"
@pytest.fixture(scope="module")
def snap(): return runtime_snapshot()
def test_live_catalog_and_leaderboard_parse_page_and_join():                      # keyless, free
    refs, pricing, _ = _parse_hf_catalog(fetch_router_catalog())
    assert refs and all(p.input_usd_per_token is None or p.input_usd_per_token >= 0 for p in pricing.values())
    arena = fetch_arena_scores()
    assert arena is not None and set(arena) == {"reasoning", "coding"} and all(len(v) > PAGE_LENGTH for v in arena.values())
    scores, ambiguous = join_scores({r.model_id.rsplit(":", 1)[0] for r in refs}, arena)
    print(f"matched reasoning={sum(s.reasoning is not None for s in scores.values())} "
          f"coding={sum(s.coding is not None for s in scores.values())} ambiguous={list(ambiguous)}")
    assert any(s.reasoning for s in scores.values()) and any(s.coding for s in scores.values())
def test_org_balance_reads_or_declines_cleanly():
    bal = fetch_org_balance_usd(); assert bal is None or bal >= 0
@pytest.mark.parametrize("profile", ["cheap_structured", "standard_generation", "deep_review", "deep_code", "independent_review"])
def test_each_profile_leader_is_the_cheapest_qualifier_at_its_level(snap, profile):    # pure, on the live snapshot
    req = build_requirement(profile, CallBudget(2_000, 1_024)); chain = select(req, snap)
    funded = [c for c in chain.candidates if c.cost_class == "funded"]
    pop = track_population(snap.scores, req.track, today=snap.observed_at.date(), max_publish_age_days=FUNDED_POLICY.max_publish_age_days)
    q = level_qualifiers(pop, req.strength, FUNDED_POLICY)
    assert funded and all(repo_of(c.model_ref.model_id) in q for c in funded)
    assert funded[0].worst_case_credits == min(c.worst_case_credits for c in funded)
@pytest.mark.parametrize("profile", ["cheap_structured", "standard_generation", "deep_review", "deep_code", "independent_review"])
def test_each_profile_is_served_by_hugging_face_and_spend_equals_usage_times_price(snap, profile):
    before = _reconciled_ids()
    r = route_chat([ChatMessage("user", "Reply with the single word: ready")], profile=profile, max_tokens=1024,
                   retries=1, snapshot=snap, backend_factory=_dartmouth_down)
    assert r.backend == "huggingface" and r.text.strip()
    price = snap.pricing[r.model]
    expected = r.input_tokens * price.input_usd_per_token + r.output_tokens * price.output_usd_per_token
    new = [e for e in _reconciled_events() if e["reservation_id"] not in before]
    assert r.cost_estimate_usd == pytest.approx(expected) and [e["charged"] for e in new][-1] == pytest.approx(expected)
def test_strict_json_probe():
    r = route_chat([ChatMessage("user", 'Return only this JSON object: {"hf_funded": "ok"}.')], profile="cheap_structured",
                   max_tokens=1024, retries=1, backend_factory=_dartmouth_down)
    assert json.loads(r.text) == {"hf_funded": "ok"}
def test_vision_probe_reads_a_red_square():
    img = ImagePart.from_bytes("image/png", _red_square_png()[0])
    r = route_chat([ChatMessage("user", (TextPart("What colour is this image? One word."), img))], profile="vision",
                   max_tokens=1024, retries=1, backend_factory=_dartmouth_down)
    assert r.backend == "huggingface" and "red" in r.text.lower()
def test_wrong_bill_to_is_a_402_outage_not_a_charge_to_another_account(snap):
    model = sorted(m.model_id for m in snap.models if m.backend == "huggingface")[0]
    with pytest.raises(HFPaymentRequired) as ei:
        HuggingFaceBackend(bill_to="000000000000000000000000").chat([ChatMessage("user", "hi")], model=model, max_tokens=8)
    assert isinstance(ei.value, PreInferenceRejection) and disposition_of(ei.value) is CandidateDisposition.RETRY_ADVANCE
    assert load_hf_token() not in str(ei.value)
def test_wrong_bill_to_through_the_router_is_charged_zero(snap):                  # spec 5.9.2 amended, against the real ledger
    before = _reconciled_ids()
    bad = lambda name: HuggingFaceBackend(bill_to="000000000000000000000000") if name == "huggingface" else _dartmouth_down(name)
    with pytest.raises(ChainExhausted):
        route_chat([ChatMessage("user", "hi")], profile="deep_review", max_tokens=8, retries=1, snapshot=snap, backend_factory=bad)
    new = [e for e in _reconciled_events() if e["reservation_id"] not in before]
    assert new and all(e["charged"] == 0.0 for e in new)
```
- [ ] Step 2: `LLMXIVE_REAL_TESTS=1 pytest tests/real_call/test_hf_funded_real.py -q` with `LLMXIVE_HF_BILL_TO` unset → FAIL in `_require_settings` naming the variable (proves the lane cannot silently pass).
- [ ] Step 3: Set the three settings and run it for real.
- [ ] Step 4: `LLMXIVE_REAL_TESTS=1 pytest tests/real_call/test_hf_funded_real.py tests/real_call/test_model_selection_snapshot_real.py -q -s` → PASS; then `llmxive preflight` shows the spend this run added and the leaderboard coverage line. Record date, token counts, total cost and the matched/ambiguous counts in `scripts/hf/README.md` (no ratings).
- [ ] Step 5: `git add tests/real_call/test_hf_funded_real.py scripts/hf/README.md && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "test(027): real-call lane for the funded provider (per-profile level check, JSON, vision, 402 at zero, spend = usage x price)" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 22: Full gate
**Files:** none expected; any fix goes to the file that owns the defect, with its own test.
- [ ] Step 1: `pytest tests/unit tests/contract tests/integration -m "not slow" -q` → all pass.
- [ ] Step 2: `ruff check src tests` → clean.
- [ ] Step 3: `LLMXIVE_REAL_TESTS=1 pytest tests/real_call/test_hf_funded_real.py tests/real_call/test_model_selection_snapshot_real.py -q` → pass.
- [ ] Step 4: `git grep -nE '"rating(_lower|_upper)?": [0-9]' -- ':!tests/fixtures/hf_funded/lmarena_text_*.json'` and a scan of `git diff origin/main -- src scripts README.md` for numbers next to an LMArena model name → nothing (no real score committed; the fixtures' numbers are proved synthetic by Task 4).
- [ ] Step 5: If any of 1–4 needed a change, repeat **all four** from Step 1 (a fix for one check can break another), then: `git add <each file changed, by name> && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "fix(027): <what the gate found>" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`
- [ ] Step 6: `git status --short` is empty; `git log --oneline` shows the task commits; confirm the constitution's `Last Amended` equals the merge date; open the PR with the Sync Impact Report from Task 1 in its description.

---

## Spec coverage

|Spec section|Task|
|-|-|
|§1–2 goals, anti-goals|13–16 (anti-goal 1: 6, 15, 16; 2: 13–15 extend `select`/`execute` only; 3: 9, 10, 13 fail closed on unmatched/ambiguous/stale; 4: 8)|
|§3 facts|Global Constraints; 4, 5, 9, 21 re-verify them against the live endpoints|
|5.1 backend, credentials|2, 3, 5|
|5.2 catalog component|10 (+ 13 `_component_of`)|
|5.3–5.5 (superseded by 5.10 for scores and ranking)|cost class and class ordering: 6, 14; the rest per 5.10 below|
|5.6 allowance guard|7, 8, 15 (per-call ceilings: none — Spec issues 15)|
|5.7 wiring, preflight|18, 19|
|5.8 tests|4 (fixtures), 8, 9, 12–15 (offline), 21 (real)|
|5.9.1 local after funded|14 · 5.9.2 ledger, zero for 401/402/403|5, 7, 8, 15, 21 · 5.9.3 freshness|14 · 5.9.4 unobservable|5, 13 · 5.9.5 paid controls|13, 14 (ladder: 17) · 5.9.6 borrow, × 1|8, 15 · 5.9.7 attribution (now LMArena)|15 (README) · 5.9.8 vision|13 (image flag), 11 (reasoning/balanced)|
|5.10 LMArena source, categories → tracks|9, 10|
|5.10 name match, highest variant, ambiguous/unmatched ineligible, no alias list|9 (+ 13 eligibility)|
|5.10 two tracks, rank from the track only|11 (profile → track), 12, 14 `test_tracks_are_ranked_separately`|
|5.10 percentile levels, no score in repo|11 (`FUNDED_POLICY`), 12, 4 + 22 (no real score committed)|
|5.10 cheapest qualifying wins; rest from other families|14|
|5.10 near-ties by interval overlap, zero-width default|9 (parse), 12, 14 `test_a_statistically_tied_cheaper_model_wins_its_level`|
|5.10 freshness by publish date and fetch time|10 (provenance), 12 (`track_population`), 13|
|5.10 per-profile defaults|11|
|5.10 caller raises/lowers the level per call|6 (`level_delta`), 11 (merge), 14 `test_level_raise_and_lower_for_one_call`|
|5.10 fix-loops raise one level per tier, ending at strongest|17|
|5.10 budget pressure: generation steps down one level, reviews never|14|
|5.10 fail closed when scores unavailable or stale|13|
|§6 constitution|1|
|§7 left to the builder|11 (publish age, chain slots); 5, 15 (retry count: one attempt); 4 (fixture format)|
|§8 open items|item 2 and item 4 are listed under Spec issues; item 3 is superseded by 5.10|

Gaps found in self-review and closed: run-log truthfulness (Task 16) and the detector's blindness to `:provider` ids (Task 20) had no owner in the first draft; chain truncation by `max_candidates` (Task 14) was implied by nothing in the spec; the free-rung leader exclusion would have removed the only `strongest` funded qualifier (Task 17); a population filtered by the call's own flags would have made every vision model "strongest" (Task 14 `test_population_ignores_call_filters`); `0.3 * n` float arithmetic in the cut-off (Task 12).

## Spec issues found

1. **`cost_class` "derived from the backend, not from the price" cannot hold for Dartmouth**, which serves free and paid models from one backend (`select.py:184` reads `pricing.is_free`). Plan: funded ⇔ backend is `huggingface`; free/paid still follow the price (Task 6).
2. **"Reuses the existing shared pieces … the circuit breaker, empty-reply detection" — they are not shared.** `_CircuitBreaker` is private to `dartmouth.py:225-383` with Dartmouth wording; empty-reply handling is inline in `DartmouthBackend.chat`. Only `invoke_with_deadline` and the exception taxonomy live in `base.py`. Plan moves the breaker and the content serializer (Task 3).
3. **A "permanent credential error" for 401/403 aborts the whole chain** (`router.py:180-181`), so a bad token would block the local last resort that 5.9.1 promises. Plan: a typed `BackendCredentialError` that `disposition_of` classifies SKIP (Task 3).
4. **Per-profile ranking needs the profile, and the requirement does not carry it** (`model_selection/types.py:143-174`); `deep_review` and `deep_code` are both capability `"deep"` (`profiles.py:124-141`). Plan adds `ModelRequirement.profile`, `track`, `strength`, `budget_step_down`, set by `RequirementProfile.build` (Tasks 6, 11).
5. **"Using the existing transport and reserve → settle code" is not possible as-is:** the ref is hard-wired (`ledger_transport.py:66, 180-190`; `reservations.py:279, 470, 520, 581`) and no event can carry an actual charge (`reservations.py:348-369`). Plan adds `LedgerConfig.ref` and a `charged` amount (Task 7).
6. **G5 / anti-goal 1 versus the run log.** `BackendName` has no `huggingface` member (`types.py:185-189`), so `BackendName(response.backend)` raises at `agents/base.py:182` and `slash_command.py:175`; cost is hard-coded `0.0` (`agents/base.py:235`, `slash_command.py:207`, `implementer.py:2054`) and the implementer logs `DARTMOUTH` (`implementer.py:1070`); `_check_cost_invariant` rejects any non-zero cost without `LLMXIVE_PAID_OPT_IN` (`runlog.py:45-66`), contradicting 5.9.5 "no opt-in flag". Task 16.
7. **5.8 asks for a fixture "captured from the real endpoints"; the project keeps scores only in the gitignored LKG store** (5.10: "no score value is written anywhere in the repo"). LMArena's CC-BY-4.0 licence would allow committing them; the project rule does not. Plan commits real rows and names with deterministic synthetic `rating`/`rating_lower`/`rating_upper`/`variance`/`rank`, marked `ratings_synthetic`, and re-orders rows by name because the server's row order is the real ranking (Task 4). `vote_count` stays real (not a score) — say so if it should be synthetic too.
8. **5.9.5's ladder omitted the existing `exclude_leader` rungs, and the merge added a third free rung** (`execution_status.py:107-111`). 5.10 replaces the "funded best-quality" rung with "raise one level each time a tier is exhausted, ending at strongest". Plan keeps the ladder's length and gives each free rung `level_delta` = its index (0, 1, 2), so an `economy` profile tops out at `strong` and a `strong` profile reaches `strongest` at tier 1; the paid rung keeps `level_delta=0` (Task 17). Adding rungs until `strongest` would multiply the fix-round budget (each rung costs `MAX_EXECUTION_FIX_ROUNDS`), so the plan does not. While Dartmouth is up, a raised level changes nothing (free remote still leads).
9. **The free-rung leader exclusion would empty the funded class at high levels.** With Dartmouth down, tier 1 (`exclude_leader`, `level_delta=1`) would exclude the single `strongest` qualifier and the call would become an outage. Plan: leader exclusion stops at the first non-free leader — a funded leader is never excluded; its escalation is the level raise (Task 17).
10. **§6 "exhausting the allowance is … not a licence to fall through to paid" versus the order "… → local → paid"** with `LLMXIVE_PAID_OPT_IN: "1"` in the pipeline workflows. Plan: when the allowance is what emptied the funded group, paid candidates are dropped too, except on an explicit `require_paid` rung (Task 14).
11. **"The rest of the chain is the next-cheapest qualifying models from other families" names no length**, and `max_candidates` is 8 for five profiles (4 for `independent_review`) while the catalog has ~158 models. Plan: `FUNDED_POLICY.max_chain_slots = 2` (builder's call, under §7 "retry counts"), so the funded group never truncates the local and paid tail (Task 14 `test_funded_slots_never_truncate_local_or_paid`).
12. **"Borrow up to three days of allowance ahead" is ambiguous** (three days' worth in total, or today plus three). Plan uses today plus three, `BORROW_AHEAD_DAYS = 3` (Task 8).
13. **5.9.2 charged the full reservation to any call without `usage`, including a 402/401** the provider did not bill. RESOLVED 2026-11-23 (spec 5.9.2 amended): HTTP 401, 402 and 403 charge zero; every other call without `usage` charges the full reservation. Plan extends "charge zero" to a request the backend never sent (missing token or bill-to) — nothing reached the provider (Tasks 5, 15, 21).
14. **The pin detector cannot see `<repo>:<provider>` ids** (`inventory.py:78-80` anchors on a fixed org list and forbids `:`), so FR-014 enforcement would not have covered this provider. Task 20.
15. **Per-call ceilings: the spec contradicts itself.** 5.10 says "nothing numeric remains to confirm before merge" and supersedes section 7, but the status line (lines 5-6), 5.6's last bullet ("Per-call ceilings per profile live beside the floors in `policy.py`") and §8 item 3 ("Initial floors") still ask for floors/ceilings. Under 5.10 a per-profile ceiling has no job: within a level the cheapest qualifier already wins, and budget pressure is handled by the step-down rule. Plan: no per-profile ceiling; each funded candidate must fit `available_usd` and the caller's `max_credits` (Task 14). The spec text should be corrected (this plan does not edit the spec).
16. **"Freshness is judged from the row's `leaderboard_publish_date`" gives no age limit.** Plan: `FUNDED_POLICY.max_publish_age_days = 7` — a row published more than seven days before the snapshot's UTC date is ineligible and leaves the population (Tasks 11–13). On 2026-11-23 the `latest` split was published 2026-11-22.
17. **"Each gets its percentile among them" does not fix the population or the rounding.** Plan: the population is every scored, fresh, routable repo for the track, independent of the call's own filters (otherwise "strongest vision model" would be any vision model); the cut-off is the repo at index `ceil(pct·n/100) − 1` in integer arithmetic; ties on `rating` order by repo id (Task 12).
18. **"Lowercase, alphanumerics only" for a Hugging Face repo id** does not say whether the org is part of the name (LMArena names carry no org). Plan normalises the part after `/`; two routable repos that collide (e.g. the same model under two orgs) are both ineligible for that name, per "matches more than one routable model" (Task 9).
19. **Required observed flags.** The superseded 5.4 listed "e.g. structured output"; 5.10 names only the image-input flag for `vision`. No code path sends `response_format` (verified: no `response_format`/`json_schema` in `backends/` or `model_selection/`), so `structured` is not required; callers that list `structured`/`tools`/`vision` in `required_features` are checked against the catalog's flags (Task 13).
20. **Which calls are "review calls" for budget pressure.** Selection sees only the profile. Plan: `deep_review`, `independent_review` and `vision` (the paper figure review, `paper_reprocess/preprint_figures.py:245`) never step down; `cheap_structured`, `standard_generation` and `deep_code` do. All 26 `deep_review` agents in `agents/registry.yaml` therefore never step down, including the non-reviewer ones among them (Task 11).
21. **OpenRouter as "an optional recorded cross-check"** (5.10). No task needs it, so the plan drops OpenRouter entirely — no fetch, no fixture, no component.
22. **`selection_identity` changes for every call.** `canonical_overrides` reads every `RequirementOverrides` field, so adding `level_delta` appends `|level_delta=0` to every identity string, and the version-4 bump changes `policy=`. Stored receipts and review-cache keys bound to the old identity are invalidated once at merge; this is the intended behaviour of a reviewed policy change (Tasks 6, 14).
23. **§8 item 4 (Jobs sharing the $50 group limit)** remains open and outside this plan; the org-balance cross-check (Task 8) is the only bound on spend the ledger does not see.

## Not determined from the code

- Which existing test drives `Agent.run` / the implementer with a stubbed `chat_with_fallback` — Task 16's last two tests name the assertions but point at a grep for the harness.
- How a spec-025 Attempt counts calls against its call ceiling (`self_improvement/attempt_config.py`); Task 15 assumes it counts `DispatchStarted` events, which funded emits unchanged.
- Whether `paper-compile.yml`, `signoff-poll.yml`, `audit.yml`, `hf-daily-papers.yml`, `pages.yml` reach a model call; they pass no Dartmouth key today, so Task 19's rule leaves them alone.
- Whether the Actions `GITHUB_TOKEN` may push `refs/llmxive/funded-ledger` (the credit-ledger anchor is not wired in any workflow at this commit, so there is no precedent to copy).
- How often LMArena publishes the `latest` split (one observation: 2026-11-22 on 2026-11-23), and whether `datasets-server.huggingface.co` rate-limits keyless clients (about ten paged GETs per snapshot; no documentation found). The seven-day window (Spec issues 16) and the LKG fallback absorb a missed day.
- Whether `variance` and `rank` count as "score values" under the no-scores-in-the-repo rule; the plan treats them as such and synthesises them (Task 4).
- Whether `HF_TOKEN` in Actions is the dedicated fine-grained token (inference + `org.billing.read`) — spec §8 item 2; Task 21's `test_org_balance_reads_or_declines_cleanly` accepts both outcomes.
