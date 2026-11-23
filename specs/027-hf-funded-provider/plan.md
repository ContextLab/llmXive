# Hugging Face Funded Provider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When no free hosted backend can serve a call, serve it through Hugging Face Inference Providers, choosing the model from live leaderboard and catalog data inside a code-enforced monthly allowance, with no change at any call site.
**Architecture:** Hugging Face becomes a third catalog source and a third cost class ("funded") inside spec 026's single `runtime_snapshot → select → execute` path: two new snapshot components (`hf_catalog`, `leaderboard`) plus a funded guard feed the pure selector, which orders free remote → funded → local → paid. Spend is reserved and settled in USD on its own protected git ref through the existing strict-CAS ledger code, and eligibility comes from a reviewed `FundedPolicy` (score floors + per-call ceilings) rather than the hand-set family tiers.
**Tech Stack:** Python ≥ 3.11, `httpx` (already a dependency; no new packages), the spec-026 modules (`model_selection/*`, `git_event_log`), pytest with real git refs and a real local HTTP replay server, GitHub Actions env wiring.
**Spec:** specs/027-hf-funded-provider/spec.md

## Global Constraints

- Router base URL: `https://router.huggingface.co/v1` (OpenAI-compatible chat).
- Every chat call sends header `X-HF-Bill-To: <llmxive resource-group id>`; the id comes only from `LLMXIVE_HF_BILL_TO` (Actions variable, not a secret), no default — a missing id fails closed.
- Token: `credentials.load_hf_token()` — env `HF_TOKEN`, then macOS Keychain service `llmxive-huggingface`; never the plaintext Hub cache, never logged.
- Catalog: `GET https://router.huggingface.co/v1/models`, no key; `pricing.input`/`pricing.output` are USD per **million** tokens (÷ 1e6 into `ModelPricing`).
- `model_id` is sent as `<repo id>:<provider>`; a pinned provider is never silently replaced.
- HTTP 402 → `BackendUnavailable`; 401/403 → permanent credential error; 429/5xx → transient.
- Leaderboard: `https://openrouter.ai/api/v1/models`, joined by exact `hugging_face_id` (no fuzzy matching in v1); general score `intelligence_index`, coding score `coding_index` falling back to the general score when null. LMArena and Epoch are not wired in v1.
- Raw scores are kept only in the gitignored LKG store (`state/model_selection/`), never committed or republished.
- Snapshot component names: `"hf_catalog"`, `"leaderboard"` (each with own provenance + LKG).
- Fail closed: leaderboard `unavailable` or older than `max_catalog_age_s` → no funded candidate is eligible; no `hugging_face_id` match → ineligible.
- `cost_class ∈ {free, funded, paid}`; ordering is free *remote* → funded → local → paid.
- `cheap_structured`, `standard_generation`: lowest worst-case cost, ties broken by score. `deep_review`, `deep_code`, `independent_review`, `vision`: highest score whose worst-case cost fits the per-call ceiling; if none fits, the cheapest eligible.
- `LLMXIVE_HF_MONTHLY_USD` (default 50). Daily allowance = (monthly − spent this month) ÷ days left in the month.
- Reservations hold worst case × 1 (not × retries); a run may borrow up to three days of allowance ahead but never more than what is left in the month.
- Ledger: new protected ref `refs/llmxive/funded-ledger` (USD, monthly epoch, own bootstrap anchor); a call that dies without a `usage` block is charged its full reservation.
- Org credits cross-check: `GET https://huggingface.co/api/organizations/contextlab/billing/credits` (scope `org.billing.read`); if the org balance is below the remaining allowance, the lower number wins.
- Funded needs no `allow_paid` and no opt-in flag; `require_paid` excludes funded.
- Exhausted allowance is an outage (`ModelUnavailable` → `BackendUnavailable`), never a silent downgrade, never a human escalation.
- Constitution 1.3.0 → 1.4.0 with the "Funded services" paragraph from spec §6, verbatim.
- No mocks as the primary path (Constitution III). Real-call tests: `LLMXIVE_REAL_TESTS=1`, a few cents in total, bill-to from `LLMXIVE_HF_BILL_TO`.
- Schedules stay paused: no workflow `on:` block is touched.
- Floors and per-call ceilings are confirmed by the maintainer before merge; nothing in this plan fixes their production values.
- Line ranges below are at commit `70942bbae03`; the working branch is the 026→main integration branch, so re-locate by symbol name if the merge shifted them. Import `llmxive.model_selection.*` from `llmxive/backends/*` only inside functions (as `backends/credits.py:247` does) — a module-level import cycles through `model_selection/__init__` → `execute` → `backends.router`.

## Review Focus

1. **A leaderboard gap silently promoting a model.** Duplicate OpenRouter rows for one `hugging_face_id` with different scores, an id that differs only by case, a row with `benchmarks` but a null `intelligence_index`, and a leaderboard LKG one second past `max_catalog_age_s`. Tests: Task 9 `test_parse_leaderboard_duplicates_take_minimum_and_case_is_exact`; Task 11 `test_fail_closed_table`.
2. **Two runners and the calendar.** Concurrent reservations against one remote ref; a hold opened in one month and read in the next; last day of month, leap day, a non-UTC `now`; the borrow cap never exceeding the month. Tests: Task 8 `test_allowance_cap_table`, `test_two_runners_cannot_overspend_the_allowance`, `test_prior_month_hold_does_not_count`.
3. **A metered call recorded as free.** A provider priced `0.0` or with no price on the `huggingface` backend; a reply with no `usage`; `retries=3` multiplying attempts under a × 1 hold; a run-log entry that says Dartmouth and `$0`. Tests: Task 6 `test_cost_class_is_funded_even_at_zero_price`; Task 13 `test_missing_usage_charges_full_reservation`, `test_funded_dispatches_once_and_reserves_times_one`; Task 14 `test_implementer_run_log_attributes_funded_backend_and_cost`.
4. **Funded starving or bypassing the other classes.** More eligible funded pairs than `max_candidates`; allowance exhausted with paid opt-in on; `require_paid`; a 401/403 aborting the chain before the local resort. Tests: Task 12 `test_funded_slots_never_truncate_local_or_paid`, `test_exhausted_allowance_is_outage_not_paid`, `test_require_paid_excludes_funded`; Task 3 `test_credential_error_skips_candidate`.
5. **What the catalog cannot observe, and which provider is billed.** Unknown-family model with `reasoning` required; one repo on two providers with different `context_length`; a provider whose `status` is not live; the request body carrying anything other than the priced `<repo>:<provider>`. Tests: Task 11 `test_unobservable_features_and_context`; Task 9 `test_parse_hf_catalog_one_ref_per_live_provider`; Task 5 `test_chat_sends_pinned_provider_and_bill_to`.

---

## File Structure

Created
|File|Responsibility|
|-|-|
|`specs/027-hf-funded-provider/spec.md`|The approved spec (copied from the draft note).|
|`src/llmxive/backends/huggingface.py`|`HuggingFaceBackend` + the keyless router-catalog fetch.|
|`src/llmxive/backends/hf_budget.py`|Allowance arithmetic, funded-ledger spend projection, guard, observer, org-balance cross-check.|
|`scripts/hf/capture_fixtures.py`|Capture the recorded fixtures from the real endpoints (scores redacted).|
|`scripts/hf/score_distribution.py`|Print the live score/price distribution the maintainer picks floors from.|
|`tests/fixtures/hf_funded/{router_models,openrouter_models,chat_200,chat_402}.json`|Recorded fixtures, each with `captured_at`.|
|`tests/helpers/funded.py`|Hand-built funded snapshot + test-only `FundedPolicy`.|
|`tests/helpers/replay_server.py`|Real local HTTP server replaying recorded responses and recording requests.|
|`tests/unit/test_governance_027.py`, `test_credentials_hf.py`, `test_backend_shared_pieces.py`, `test_hf_fixtures.py`, `test_huggingface_backend.py`, `test_model_selection_cost_class.py`, `test_hf_budget.py`, `test_model_selection_hf_snapshot.py`, `test_funded_policy.py`, `test_model_selection_funded_select.py`, `test_runlog_funded.py`, `test_preflight_selection_report.py`, `test_workflow_hf_env.py`|One file per task, named after its component.|
|`tests/integration/test_funded_ledger.py`, `test_funded_execute.py`|Real-git-ref ledger and execution tests.|
|`tests/real_call/test_hf_funded_real.py`|The real-call lane.|

Modified
|File|Responsibility of the change|
|-|-|
|`.specify/memory/constitution.md`|1.4.0 amendment.|
|`src/llmxive/credentials.py`|`load_hf_token`.|
|`scripts/hf/pilot.py`, `scripts/hf/README.md`|Delegate token loading; describe production use, the $50 limits.|
|`src/llmxive/backends/base.py`|Shared `CircuitBreaker`, `BackendCredentialError`, `openai_content`, token counts on `ChatResponse`.|
|`src/llmxive/backends/dartmouth.py`|Import the moved pieces.|
|`src/llmxive/backends/router.py`|Register `"huggingface"`; credential error → SKIP.|
|`src/llmxive/types.py`, `agents/registry.yaml`|`BackendName.HUGGINGFACE`; registry backend entry.|
|`src/llmxive/model_selection/types.py`|Cost class, scores, observed features, funded guard, requirement fields.|
|`src/llmxive/model_selection/ledger_transport.py`, `reservations.py`|Ref-parametrised config, `charged` amount, public `reconcile`.|
|`src/llmxive/cli.py`, `infra/credit-ledger-ops.md`|`funded-ledger-bootstrap`; runbook section.|
|`src/llmxive/model_selection/snapshot.py`|Three new components, LKG, digest.|
|`src/llmxive/model_selection/policy.py`, `profiles.py`|`FundedPolicy`; profile name on the requirement.|
|`src/llmxive/model_selection/select.py`|Funded eligibility, ordering, class-aware freshness.|
|`src/llmxive/model_selection/execute.py`, `route.py`|Funded reserve → dispatch × 1 → settle; plumbing.|
|`src/llmxive/state/runlog.py`, `agents/base.py`, `agents/implementer.py`, `speckit/slash_command.py`|Truthful backend + cost in the run log.|
|`src/llmxive/state/execution_status.py`|Funded-best rung.|
|`src/llmxive/preflight.py`|Selection report.|
|`.github/workflows/*.yml` (10 files)|Env wiring only.|
|`src/llmxive/model_selection/inventory.py`, `specs/026-…/migration_manifest.{json,md}`|Detector sees `<repo>:<provider>`.|
|`README.md`, `CLAUDE.md`|Models & cost text.|
|`tests/real_call/test_model_selection_snapshot_real.py`, `tests/unit/test_execution_tier_constraints.py`|Assertions whose contract this spec changes (named in the owning task).|

Commit trailer used by every commit below (written out in each command):
`Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>` / `Claude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK`

---

### Task 1: Governance — spec file and constitution 1.4.0
**Files:** Create `specs/027-hf-funded-provider/spec.md`, `tests/unit/test_governance_027.py` · Modify `.specify/memory/constitution.md` (1-23 Sync Impact Report, 138-160 Principle IV, 350 version line)
**Interfaces:**
- Consumes: `notes/2026-11-23-spec-027-hf-funded-provider-DRAFT.md`; constitution "Amendment procedure" (322-330) and "Versioning policy" (332-339: a material expansion of existing guidance is MINOR).
- Produces: the spec path every later task cites; constitution text "Funded services".
- [ ] Step 1: Write the failing test
```python
ROOT = Path(__file__).resolve().parents[2]
FUNDED = ("A metered service whose cost is covered by an institutional subscription the "
          "project already holds is *funded*.")
def test_spec_027_is_committed_and_approved():
    text = (ROOT / "specs/027-hf-funded-provider/spec.md").read_text()
    assert "DRAFT, not approved" not in text
    assert "approved by the maintainer 2026-11-23" in text
def test_constitution_is_1_4_0_with_funded_services():
    text = " ".join((ROOT / ".specify/memory/constitution.md").read_text().split())
    assert "**Version**: 1.4.0 | **Ratified**: 2026-04-28" in text
    assert "→ 1.3.0 → 1.4.0" in text            # Sync Impact Report chain
    assert FUNDED in text
    assert "Exhausting the allowance is an outage, not a licence to fall through to paid services." in text
```
- [ ] Step 2: `pytest tests/unit/test_governance_027.py -q` → FAIL (`FileNotFoundError` for the spec).
- [ ] Step 3: Copy the draft to the spec path, changing only the title/status lines to "Spec 027 — … (approved by the maintainer 2026-11-23)". In the constitution: append `→ 1.4.0` to the version chain and a `1.4.0 (2026-11-23, spec 027) = MINOR — …` rationale paragraph in the Sync Impact Report; add the spec §6 block quote verbatim as a "**Funded services.**" paragraph after line 156; set the version line to `1.4.0` and `Last Amended` to the merge date (rule 3 — if the merge slips, correct the date in the merge commit). Paste the Sync Impact Report into the PR description (rule 2), marking `README.md`, `CLAUDE.md`, `scripts/hf/README.md` "updated" and the `.specify/templates/*` "no edit needed".
- [ ] Step 4: `pytest tests/unit/test_governance_027.py -q` → PASS.
- [ ] Step 5: `git add specs/027-hf-funded-provider/spec.md .specify/memory/constitution.md tests/unit/test_governance_027.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "docs(027): commit approved spec; constitution 1.4.0 adds funded services" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 2: `credentials.load_hf_token`
**Files:** Modify `src/llmxive/credentials.py` (27-30 constants; new function after 273), `scripts/hf/pilot.py` (`token()` 20-43), `scripts/hf/README.md` (Credentials section) · Test `tests/unit/test_credentials_hf.py`
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
- [ ] Step 4: `pytest tests/unit/test_credentials_hf.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/credentials.py scripts/hf/pilot.py scripts/hf/README.md tests/unit/test_credentials_hf.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): credentials.load_hf_token (env then Keychain); pilot delegates" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 3: Shared backend pieces (extracted, not copied)
**Files:** Modify `src/llmxive/backends/base.py` (314-319 `ChatResponse`, after 422 new exception, 531-551 `__all__`), `src/llmxive/backends/dartmouth.py` (42-65 `_lc_content`, 181-268 `_CircuitBreaker`), `src/llmxive/backends/router.py` (148-164) · Test `tests/unit/test_backend_shared_pieces.py`; existing `tests/unit/test_dartmouth_circuit_breaker.py` must pass unedited
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
def test_credential_error_skips_candidate():           # Review Focus 4
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
**Files:** Create `scripts/hf/capture_fixtures.py`, `tests/fixtures/hf_funded/{router_models,openrouter_models,chat_200,chat_402}.json`, `tests/unit/test_hf_fixtures.py`
**Interfaces:**
- Consumes: `credentials.load_hf_token`; env `LLMXIVE_HF_BILL_TO`.
- Produces: four files, each `{"captured_at": "<YYYY-MM-DD>", "source_url": "<url>", "status": <int>, "payload": {...}}`; `openrouter_models.json` additionally `"scores_synthetic": true`. CLI: `python scripts/hf/capture_fixtures.py [--with-chat]`.
- Decisions: the two catalog GETs are keyless and free. `--with-chat` makes exactly one billed chat (`max_tokens` 64; take the cheapest live provider from the catalog just fetched, so no model id is written into the script) and one request with bill-to `000000000000000000000000` for the 402 body (a 402 is not billed). The script replaces every numeric value under `benchmarks.artificial_analysis` with `round((int(sha256(hugging_face_id).hexdigest(), 16) % 600) / 10, 1)` before writing (spec 5.3 / 5.9.7 forbid committing the real numbers; see Spec issues 7), keeps nulls as nulls, drops response headers, and strips `id`/`system_fingerprint` from the chat payload.
- [ ] Step 1: Write the failing test
```python
FX = Path(__file__).resolve().parents[1] / "fixtures" / "hf_funded"
def _load(name): return json.loads((FX / name).read_text())
def test_every_fixture_states_its_capture_date_and_source():
    for name in ("router_models.json", "openrouter_models.json", "chat_200.json", "chat_402.json"):
        fx = _load(name)
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", fx["captured_at"]) and fx["source_url"].startswith("https://")
def test_router_catalog_has_the_fields_the_spec_names():
    models = _load("router_models.json")["payload"]["data"]
    assert len(models) >= 100
    p = next(p for m in models for p in m["providers"] if p.get("pricing"))
    assert {"input", "output"} <= set(p["pricing"]) and "status" in p and "context_length" in p
def test_leaderboard_fixture_is_redacted_but_real_shaped():
    fx = _load("openrouter_models.json")
    assert fx["scores_synthetic"] is True
    rows = [r for r in fx["payload"]["data"] if r.get("hugging_face_id")]
    assert any("intelligence_index" in ((r.get("benchmarks") or {}).get("artificial_analysis") or {}) for r in rows)
def test_chat_fixtures_carry_usage_and_the_402():
    assert {"prompt_tokens", "completion_tokens"} <= set(_load("chat_200.json")["payload"]["usage"])
    assert _load("chat_402.json")["status"] == 402
```
- [ ] Step 2: `pytest tests/unit/test_hf_fixtures.py -q` → FAIL (`FileNotFoundError`).
- [ ] Step 3: Write the script and run `LLMXIVE_HF_BILL_TO=<group id> python scripts/hf/capture_fixtures.py --with-chat` (cost: under one cent). Inspect the four files for tokens, account names and balances before staging.
- [ ] Step 4: `pytest tests/unit/test_hf_fixtures.py -q` → PASS.
- [ ] Step 5: `git add scripts/hf/capture_fixtures.py tests/fixtures/hf_funded/router_models.json tests/fixtures/hf_funded/openrouter_models.json tests/fixtures/hf_funded/chat_200.json tests/fixtures/hf_funded/chat_402.json tests/unit/test_hf_fixtures.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "test(027): recorded HF router + leaderboard fixtures (scores redacted) and capture script" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 5: `HuggingFaceBackend`
**Files:** Create `src/llmxive/backends/huggingface.py`, `tests/helpers/replay_server.py`, `tests/unit/test_huggingface_backend.py` · Modify `src/llmxive/backends/router.py` (26-44), `src/llmxive/types.py` (185-189), `agents/registry.yaml` (2-12), `scripts/hf/README.md` (intro: Hugging Face is now a routed fallback)
**Interfaces:**
- Consumes: `base.{BaseBackend, ChatMessage, ChatResponse, CircuitBreaker, openai_content, invoke_with_deadline, BackendUnavailable, BackendCredentialError, TransientBackendError, EmptyReplyError, PermanentBackendError}`; `credentials.load_hf_token`.
- Produces: `ROUTER_BASE_URL = "https://router.huggingface.co/v1"`, `BILL_TO_ENV = "LLMXIVE_HF_BILL_TO"`, `BILL_TO_HEADER = "X-HF-Bill-To"`; `fetch_router_catalog(*, base_url: str = ROUTER_BASE_URL, timeout: float = 30.0) -> dict` (keyless GET `/models`); `class HuggingFaceBackend(BaseBackend)` with `name = "huggingface"`, `__init__(self, *, token: str | None = None, bill_to: str | None = None, base_url: str = ROUTER_BASE_URL)`, `list_models() -> list[str]` (repo ids), `chat(...)` per `BaseBackend`, `healthcheck()`. `tests.helpers.replay_server.ReplayServer(routes: dict[tuple[str, str], list[tuple[int, dict]]])` — a context manager with `.base_url` and `.requests: list[dict]` (`method`, `path`, `headers`, `json`).
- Decisions: one HTTP attempt per `chat()` (no internal retry — see Task 13); default deadline `float(os.environ.get("LLMXIVE_HF_DEADLINE_S", "360.0"))` for every model (the reasoning-model deadline from `dartmouth.py:116-118`, applied to all because the catalog cannot observe reasoning — spec 5.9.4); per-model breaker `CircuitBreaker(max_consecutive=3, window_s=1800.0, label="Hugging Face")`; empty content with `finish_reason == "length"` raises `TransientBackendError("… reasoning budget exhausted …")` (the phrase `chat_one_candidate` already advances on, `router.py:222`), any other empty content raises `EmptyReplyError`; `cost_estimate_usd` stays `0.0` here and is filled by `execute`, which knows the priced provider. Registry entry: `{name: huggingface, kind: openai_compatible, auth_env_vars: [HF_TOKEN, LLMXIVE_HF_BILL_TO], is_paid: false}`.
- [ ] Step 1: Write the failing test (a real HTTP exchange against `ReplayServer`)
```python
M = "acme/alpha-large:prov-a"; MSG = [ChatMessage("user", "hi")]
OK = (200, _load("chat_200.json")["payload"]); PAY = (402, _load("chat_402.json")["payload"])
def _be(srv, **kw): return HuggingFaceBackend(token="hf_t", bill_to="grp123", base_url=srv.base_url, **kw)
def test_chat_sends_pinned_provider_and_bill_to():                 # Review Focus 5
    with ReplayServer({("POST", "/chat/completions"): [OK]}) as srv:
        r = _be(srv).chat(MSG, model=M, max_tokens=64, temperature=0.0)
    req = srv.requests[0]
    assert req["headers"]["x-hf-bill-to"] == "grp123" and req["headers"]["authorization"] == "Bearer hf_t"
    assert req["json"]["model"] == M and req["json"]["max_tokens"] == 64 and req["json"]["stream"] is False
    assert r.backend == "huggingface" and r.model == M
    assert (r.input_tokens, r.output_tokens) == (OK[1]["usage"]["prompt_tokens"], OK[1]["usage"]["completion_tokens"])
@pytest.mark.parametrize("status,exc", [(402, BackendUnavailable), (401, BackendCredentialError),
    (403, BackendCredentialError), (429, TransientBackendError), (503, TransientBackendError), (400, PermanentBackendError)])
def test_status_mapping(status, exc):
    with ReplayServer({("POST", "/chat/completions"): [(status, {"error": "x"})]}) as srv:
        with pytest.raises(exc): _be(srv).chat(MSG, model=M)
    assert len(srv.requests) == 1                                   # exactly one attempt, no hidden retry
def test_missing_bill_to_or_token_fails_closed_without_a_request(monkeypatch):
    monkeypatch.delenv("LLMXIVE_HF_BILL_TO", raising=False); monkeypatch.delenv("HF_TOKEN", raising=False)
    with ReplayServer({}) as srv:
        with pytest.raises(BackendCredentialError, match="LLMXIVE_HF_BILL_TO"):
            HuggingFaceBackend(token="hf_t", base_url=srv.base_url).chat(MSG, model=M)
    assert srv.requests == []
def test_empty_reply_is_transient_and_length_is_budget_exhaustion():
    empty = lambda fr: (200, {"choices": [{"message": {"content": ""}, "finish_reason": fr}], "usage": {}})
    with ReplayServer({("POST", "/chat/completions"): [empty("stop"), empty("length")]}) as srv:
        with pytest.raises(EmptyReplyError): _be(srv).chat(MSG, model=M)
        with pytest.raises(TransientBackendError, match="reasoning budget exhausted"): _be(srv).chat(MSG, model=M)
def test_token_never_appears_in_an_error():
    with ReplayServer({("POST", "/chat/completions"): [(500, {"error": "boom"})]}) as srv:
        with pytest.raises(TransientBackendError) as ei: _be(srv).chat(MSG, model=M)
    assert "hf_t" not in str(ei.value)
def test_registered_and_named():
    assert isinstance(make_backend("huggingface"), HuggingFaceBackend)
    assert BackendName("huggingface") is BackendName.HUGGINGFACE
```
- [ ] Step 2: `pytest tests/unit/test_huggingface_backend.py -q` → FAIL (`ModuleNotFoundError: llmxive.backends.huggingface`).
- [ ] Step 3: Implement the backend with `httpx`, the replay helper with `http.server.ThreadingHTTPServer` on `127.0.0.1:0`, the `_REGISTRY` entry, `BackendName.HUGGINGFACE = "huggingface"` (replace the 2026-05-29 "removed" comment), and the registry backend entry.
- [ ] Step 4: `pytest tests/unit/test_huggingface_backend.py tests/integration/test_free_backend_only.py tests/unit/test_config_consistency.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/backends/huggingface.py src/llmxive/backends/router.py src/llmxive/types.py agents/registry.yaml scripts/hf/README.md tests/helpers/replay_server.py tests/unit/test_huggingface_backend.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): HuggingFaceBackend (bill-to header, pinned provider, 402/401/429 taxonomy)" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 6: Selection types — cost class, scores, observed features, funded guard
**Files:** Modify `src/llmxive/model_selection/types.py` (15-17, 143-174, 177-195, 198-223, 226-233, 258-267), `src/llmxive/model_selection/__init__.py` (exports) · Test `tests/unit/test_model_selection_cost_class.py`
**Interfaces:**
- Produces:
```python
CostClass = Literal["free", "funded", "paid"]
FUNDED_BACKENDS: frozenset[str] = frozenset({"huggingface"})
def cost_class_of(backend: str, pricing: ModelPricing) -> CostClass      # funded iff backend in FUNDED_BACKENDS, whatever the price
def worst_case_usd(pricing: ModelPricing, budget: CallBudget) -> float | None   # worst_case_credits / USD_TO_CREDITS
@dataclass(frozen=True) class ModelScore:    general: float; coding: float
@dataclass(frozen=True) class ObservedModel: context_length: int | None; features: frozenset[str]   # ⊆ {"structured","tools","vision"}
@dataclass(frozen=True) class FundedGuardSnapshot:
    monthly_usd: float; spent_month_usd: float; spent_before_today_usd: float; outstanding_usd: float
    org_balance_usd: float | None; effective_cap_usd: float; available_usd: float
    epoch: str; observed_at: datetime; source: SnapshotSource
```
  `Candidate.cost_class` — a **property** (`cost_class_of(self.model_ref.backend, self.pricing)`), not a stored field, so no existing positional `Candidate(...)` can default a paid model to free. `ModelRequirement.profile: str | None = None`, `ModelRequirement.funded_best_quality: bool = False`; `RequirementOverrides.funded_best_quality: bool = False`. `RuntimeSnapshot` gains, after `digest`, `funded: FundedGuardSnapshot | None = None`, `scores: Mapping[str, ModelScore]` and `observed: Mapping[str, ObservedModel]` (both keyed by `model_id`, default empty, wrapped in `MappingProxyType` in `__post_init__`).
- [ ] Step 1: Write the failing test
```python
def test_cost_class_is_funded_even_at_zero_price():                 # Review Focus 3
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
def test_snapshot_new_fields_default_empty_and_are_read_only():
    snap = _offline_snapshot()                       # from tests.conftest
    assert snap.funded is None and dict(snap.scores) == {} and dict(snap.observed) == {}
    with pytest.raises(TypeError): snap.scores["x"] = ModelScore(1.0, 1.0)
```
- [ ] Step 2: `pytest tests/unit/test_model_selection_cost_class.py -q` → FAIL (`ImportError: cost_class_of`).
- [ ] Step 3: Implement the additions in `types.py` and export the new names.
- [ ] Step 4: `pytest tests/unit/test_model_selection_cost_class.py tests/unit/test_model_selection_select.py tests/unit/test_model_selection_execute.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/model_selection/types.py src/llmxive/model_selection/__init__.py tests/unit/test_model_selection_cost_class.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): cost_class and funded snapshot types" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 7: Funded ledger on its own ref
**Files:** Modify `src/llmxive/model_selection/ledger_transport.py` (65-70, 88-101, 162-190, 245-270, 323-350, `__all__`), `src/llmxive/model_selection/reservations.py` (78-95, 129-177, 278-279, 348-369, 470, 520, 549, 581, `__all__`), `src/llmxive/cli.py` (348-360, 1104-1110), `infra/credit-ledger-ops.md` (new "Funded ledger" section) · Test `tests/integration/test_funded_ledger.py`; extend `tests/unit/test_ledger_config_from_env.py`
**Interfaces:**
- Consumes: `LedgerConfig(remote, expected_anchor)`, `_log_ref(config)`, `read_events(repo, *, ref)`, `bootstrap_ledger(repo, remote)`, `reserve`, `_reconcile_one`, `project`.
- Produces: `FUNDED_LEDGER_REF = "refs/llmxive/funded-ledger"`; `LedgerConfig.ref: str = LEDGER_REF` (every read and write in both modules uses `config.ref`); `FUNDED_LEDGER_REMOTE_ENV = "LLMXIVE_FUNDED_LEDGER_REMOTE"`, `FUNDED_LEDGER_ANCHOR_ENV = "LLMXIVE_FUNDED_LEDGER_ANCHOR"`; `funded_ledger_config_from_env(*, remote: str | None = None, require_anchor: bool = True) -> LedgerConfig`; `bootstrap_ledger(repo, remote=None, *, ref: str = LEDGER_REF) -> str`; `reservations.reconcile(repo: Path, reservation_id: str, *, charged: float | None = None, now: datetime | None = None, config: LedgerConfig | None = None) -> None` (the public form of `_reconcile_one`; from any non-terminal state; first writer wins; `_reconcile_one` becomes a call to it); `Reservation.charged: float | None = None`; `"charged"` added to `_AMOUNT_FIELDS`. CLI `llmxive funded-ledger-bootstrap [--remote origin | --no-remote]`.
- Decisions: on the funded ref every amount field (`worst_case_credits`, `settlement_baseline`, `charged`) is **USD** and `budget_epoch` is `YYYY-MM` (UTC); the field names are the shared schema's and are not renamed. No funded sweep: a crashed `open` hold keeps counting at its full reservation until the month ends, which is exactly spec 5.9.2's charge.
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
- [ ] Step 3: Implement. Add the CLI command beside `credits-ledger-bootstrap` (it prints the anchor and the variable name to pin). Runbook section: ref name, USD unit, monthly epoch, `funded-ledger-bootstrap`, the two env vars, the same server-side fast-forward-only protection, and "no sweep".
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
def funded_headroom_available() -> tuple[bool, str]        # fail-closed coarse gate for the tier ladder
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

### Task 9: Snapshot components `hf_catalog`, `leaderboard`, `funded`
**Files:** Modify `src/llmxive/model_selection/snapshot.py` (39-43, 176-187, 216-238, 269-306, 309-338), `tests/real_call/test_model_selection_snapshot_real.py` (49) · Test `tests/unit/test_model_selection_hf_snapshot.py`
**Interfaces:**
- Consumes: `huggingface.fetch_router_catalog`, `hf_budget.funded_guard`, `lkg.{LKGStore, LKGEntry}`, `_vendor_of`, `_family_of`, Task 6 types.
- Produces: `OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"`; `_HFCatalogData = tuple[list[ModelRef], dict[str, ModelPricing], dict[str, ObservedModel]]`; `_parse_hf_catalog(raw: dict) -> _HFCatalogData`; `_parse_leaderboard(raw: dict) -> dict[str, ModelScore]` (keyed by repo id); `_fetch_huggingface() -> _HFCatalogData | None`; `_fetch_leaderboard() -> dict[str, ModelScore] | None`; `_fetch_funded_guard(*, now: datetime) -> FundedGuardSnapshot | None`; a generic `_resolve_component(name, fetch, to_payload, from_payload, empty, lkg, now, updates)` that `_resolve_models_component` now delegates to. `runtime_snapshot().sources` keys become `{"catalog", "local", "credit", "hf_catalog", "leaderboard", "funded"}`; `snapshot.scores[model_id]` is the leaderboard score of that id's repo; `_digest` covers `scores`, `observed` and `funded`.
- Decisions: one `ModelRef("huggingface", <provider>, "<repo>:<provider>", _family_of(<repo>, vendor), _vendor_of(<repo>))` per provider whose `status == "live"` — family and vendor come from the repo id alone (`_family_of` would otherwise leak `:provider` into the family for ids with no size suffix); a provider with no numeric `pricing.input`/`output` keeps its ref with `ModelPricing(None, None)` (unknown is never free). `ObservedModel.features`: `structured` ← `supports_structured_output`, `tools` ← `supports_tools`, `vision` ← `"image" in architecture.input_modalities`. Leaderboard rows: need a non-empty `hugging_face_id` and a numeric `intelligence_index`; duplicate ids take the **minimum** of each score; matching is exact and case-sensitive. The `funded` component has no LKG (`live` or `unavailable`).
- [ ] Step 1: Write the failing test
```python
CAT = _load("router_models.json")["payload"]; LB = _load("openrouter_models.json")["payload"]
def test_parse_hf_catalog_one_ref_per_live_provider():                # Review Focus 5
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
def test_parse_leaderboard_duplicates_take_minimum_and_case_is_exact():   # Review Focus 1
    aa = lambda g, c: {"benchmarks": {"artificial_analysis": {"intelligence_index": g, "coding_index": c}}}
    raw = {"data": [{"hugging_face_id": "acme/alpha-large", **aa(60.0, 55.0)},
                    {"hugging_face_id": "acme/alpha-large", **aa(48.0, None)},      # e.g. a non-reasoning variant
                    {"hugging_face_id": "acme/beta-mini", **aa(35.0, None)},
                    {"hugging_face_id": "acme/null-score", **aa(None, 70.0)},
                    {"hugging_face_id": "", **aa(90.0, 90.0)}, {"id": "no-hf-id", **aa(90.0, 90.0)}]}
    s = _parse_leaderboard(raw)
    assert s == {"acme/alpha-large": ModelScore(48.0, 48.0), "acme/beta-mini": ModelScore(35.0, 35.0)}
    assert "Acme/Alpha-Large" not in s
def test_recorded_leaderboard_joins_to_recorded_catalog():
    refs, _, _ = _parse_hf_catalog(CAT)
    assert {r.model_id.rsplit(":", 1)[0] for r in refs} & set(_parse_leaderboard(LB))
def test_snapshot_assembles_components_with_lkg(monkeypatch, tmp_path):     # the house seam: tests/unit/test_model_selection_lkg.py
    store = LKGStore(tmp_path / "lkg.json"); hf = _parse_hf_catalog(CAT); lb = _parse_leaderboard(LB)
    _patch(monkeypatch, hf=lambda: hf, lb=lambda: lb, guard=lambda *, now: _guard(now))   # + dartmouth/local/credit → None
    s1 = snap_mod.runtime_snapshot(now=T0, lkg_store=store)
    assert set(s1.sources) == {"catalog", "local", "credit", "hf_catalog", "leaderboard", "funded"}
    assert s1.sources["hf_catalog"].source == s1.sources["leaderboard"].source == s1.sources["funded"].source == "live"
    joined = next(m for m in s1.models if m.model_id.rsplit(":", 1)[0] in lb)
    assert s1.scores[joined.model_id] == lb[joined.model_id.rsplit(":", 1)[0]]
    _patch(monkeypatch, hf=lambda: None, lb=lambda: None, guard=lambda *, now: None)
    s2 = snap_mod.runtime_snapshot(now=T0 + timedelta(seconds=3601), lkg_store=store)
    assert (s2.sources["leaderboard"].source, s2.sources["leaderboard"].age_s) == ("last_known_good", 3601.0)
    assert s2.sources["funded"].source == "unavailable" and s2.funded is None
    assert len(s2.models) == len(s1.models) and s1.digest != s2.digest
    raw_file = (tmp_path / "lkg.json").read_text()
    assert "leaderboard" in raw_file                                           # scores live only in the LKG store
def test_digest_changes_when_a_score_changes(monkeypatch, tmp_path): ...       # same seam; alter one ModelScore → different digest
```
- [ ] Step 2: `pytest tests/unit/test_model_selection_hf_snapshot.py -q` → FAIL (`ImportError: _parse_hf_catalog`).
- [ ] Step 3: Implement. In `tests/real_call/test_model_selection_snapshot_real.py:49` change the expected key set to the six components (the snapshot contract this spec changes).
- [ ] Step 4: `pytest tests/unit/test_model_selection_hf_snapshot.py tests/unit/test_model_selection_lkg.py tests/unit/test_model_selection_snapshot.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/model_selection/snapshot.py tests/unit/test_model_selection_hf_snapshot.py tests/real_call/test_model_selection_snapshot_real.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): hf_catalog, leaderboard and funded snapshot components with LKG" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 10: `FundedPolicy` structure (values unset) and the score-distribution report
**Files:** Modify `src/llmxive/model_selection/policy.py` (57-60, append after 170), `src/llmxive/model_selection/profiles.py` (55-83), `src/llmxive/model_selection/__init__.py` · Create `scripts/hf/score_distribution.py`, `tests/helpers/funded.py`, `tests/unit/test_funded_policy.py`
**Interfaces:**
- Consumes: `snapshot._parse_hf_catalog`, `_parse_leaderboard`, `fetch_router_catalog`, `_fetch_leaderboard`; `types.worst_case_usd`.
- Produces:
```python
FundedKey = Literal["cheap", "standard", "deep", "deep_code", "vision"]
@dataclass(frozen=True) class FundedFloor:   min_score: float | None; score_field: Literal["general", "coding"]; required_flags: frozenset[str]
@dataclass(frozen=True) class FundedProfile: floor: FundedKey; rank: Literal["cheapest", "best_within_ceiling"]; per_call_ceiling_usd: float | None
@dataclass(frozen=True) class FundedPolicy:  floors: Mapping[FundedKey, FundedFloor]; profiles: Mapping[str, FundedProfile]; max_chain_slots: int
FUNDED_POLICY: FundedPolicy                  # the ONE place floors and ceilings live: src/llmxive/model_selection/policy.py
def distribution_report(catalog: _HFCatalogData, scores: Mapping[str, ModelScore], budget: CallBudget) -> list[str]   # in scripts/hf/score_distribution.py
```
  `RequirementProfile.build` sets `ModelRequirement.profile = self.name`. `None` for `min_score` or `per_call_ceiling_usd` means **unset → no funded candidate is eligible** for that profile (fail closed).
- `FUNDED_POLICY` as committed by this task — structure from spec 5.4/5.5/5.9.8, every number `None`:
|profile|floor key|score field|required flags|rank|
|-|-|-|-|-|
|`cheap_structured`|`cheap`|general|structured|cheapest|
|`standard_generation`|`standard`|general|structured|cheapest|
|`deep_review`, `independent_review`|`deep`|general|structured|best_within_ceiling|
|`deep_code`|`deep_code`|coding|structured|best_within_ceiling|
|`vision`|`vision`|general|structured, vision|best_within_ceiling|
  `max_chain_slots = 2` (also confirmed in Task 18).
- `tests/helpers/funded.py` (test data every later task shares; fictional `acme/…` ids so the pin detector never matches them). USD per token, `BUDGET = CallBudget(10_000, 2_000)`:
|name|model_id|in / out|worst case|context|features|general / coding|
|-|-|-|-|-|-|-|
|`A`|`acme/alpha-large:prov-a`|2e-6 / 8e-6|0.036|200000|structured, tools|60 / 55|
|`A2`|`acme/alpha-large:prov-b`|1e-6 / 4e-6|0.018|32000|structured|60 / 55|
|`B`|`acme/beta-mini:prov-a`|1e-7 / 4e-7|0.0018|128000|structured|35 / 30|
|`C`|`acme/gamma-vision:prov-c`|5e-7 / 2e-6|0.009|128000|structured, vision|45 / 40|
|`D`|`acme/delta-unscored:prov-a`|1e-7 / 1e-7|0.0012|128000|structured|none|
|`E`|`acme/gpt-oss-120b:prov-a` (family `gpt-oss`)|2e-7 / 8e-7|0.0036|128000|structured|40 / 50|
  `TEST_FUNDED_POLICY`: the table above with floors cheap 30, standard 30, deep 40, deep_code 40, vision 40; ceilings cheap/standard 0.50, the four best-rank profiles 0.05; `max_chain_slots=2` — test-only numbers, not proposals. `snapshot(*, dartmouth: tuple[str, ...] = (), claude: bool = False, paid_opt_in: bool = False, local: bool = True, hf: tuple[str, ...] = (A, A2, B, C, D, E), sources: dict[str, tuple[str, float]] | None = None, available_usd: float | None = 5.0) -> RuntimeSnapshot` (`available_usd=None` → `funded=None`, `"funded"` unavailable; `sources` overrides `(source, age_s)` per component; `NOW = 2026-11-23T12:00Z`), plus `policy_with(**ceilings_or_floors)` returning a modified copy, and the ids `QWEN`, `GEMMA4`, `GPT_OSS`, `CLAUDE`, `LOCAL` as in `tests/unit/test_model_selection_select.py:81-87`.
- [ ] Step 1: Write the failing test
```python
def test_funded_policy_covers_every_profile_with_the_spec_ranking():
    assert set(FUNDED_POLICY.profiles) == set(PROFILES)
    assert set(FUNDED_POLICY.floors) == {"cheap", "standard", "deep", "deep_code", "vision"}
    rank = {n: p.rank for n, p in FUNDED_POLICY.profiles.items()}
    assert rank["cheap_structured"] == rank["standard_generation"] == "cheapest"
    assert {rank[n] for n in ("deep_review", "deep_code", "independent_review", "vision")} == {"best_within_ceiling"}
    assert FUNDED_POLICY.floors["deep_code"].score_field == "coding"
    assert "vision" in FUNDED_POLICY.floors["vision"].required_flags
def test_every_numeric_value_is_unset_or_positive():
    vals = [f.min_score for f in FUNDED_POLICY.floors.values()] + [p.per_call_ceiling_usd for p in FUNDED_POLICY.profiles.values()]
    assert all(v is None or v > 0 for v in vals)
def test_profile_name_rides_on_the_requirement():
    assert build_requirement("deep_code", BUDGET).profile == "deep_code"
    assert ModelRequirement(capability="deep", call_budget=BUDGET).profile is None
def test_distribution_report_on_the_recorded_fixture():
    lines = distribution_report(_parse_hf_catalog(CAT), _join(CAT, LB), BUDGET)
    assert lines[0].startswith("models with a live provider:") and any(l.startswith("general score quantiles") for l in lines)
    assert any(l.startswith("coding score quantiles") for l in lines) and any("structured" in l and "vision" in l for l in lines)
    assert any(l.startswith("worst-case USD quantiles") for l in lines)
```
- [ ] Step 2: `pytest tests/unit/test_funded_policy.py -q` → FAIL (`ImportError: FUNDED_POLICY`).
- [ ] Step 3: Implement the policy types and table, the `build` change, the helper module, and the script. The report prints, for scored models with a live provider: counts; min / p10 / p25 / p50 / p75 / p90 / max of the general and coding scores; how many also have `structured`, `tools`, `vision`; worst-case USD quantiles at the given budget; and one line per model (`score, cheapest provider, worst case`) sorted by score. `python scripts/hf/score_distribution.py` fetches both keyless endpoints live (free) and prints to stdout only — it writes no file, so no real score is committed.
- [ ] Step 4: `pytest tests/unit/test_funded_policy.py tests/unit/test_model_selection_profiles.py tests/unit/test_model_selection_policy.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/model_selection/policy.py src/llmxive/model_selection/profiles.py src/llmxive/model_selection/__init__.py scripts/hf/score_distribution.py tests/helpers/funded.py tests/unit/test_funded_policy.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): FundedPolicy structure (values unset, fail closed) and score-distribution report" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 11: `select` — funded eligibility
**Files:** Modify `src/llmxive/model_selection/select.py` (46-51, 115-197, 250-265) · Test `tests/unit/test_model_selection_funded_select.py`
**Interfaces:**
- Consumes: Tasks 6, 9, 10.
- Produces: `select(requirement, snapshot, *, policy: CapabilityPolicy | None = None, funded_policy: FundedPolicy | None = None) -> ModelChain` (default `FUNDED_POLICY`); `_component_of` returns `"hf_catalog"` for the `huggingface` backend.
- Eligibility of a `huggingface` candidate (replaces steps (b), (c), (f) of the loop for that backend; (d) excludes and (e) required independence are unchanged): `hf_catalog` **and** `leaderboard` neither `unavailable` nor `last_known_good` older than `max_catalog_age_s`; `snapshot.funded` present with `source == "live"`; `requirement.profile` in `funded_policy.profiles` with that profile's floor and ceiling set; a `snapshot.scores` entry whose floor field is `>= min_score`; `floor.required_flags <= observed.features`; each `required_features` item that is one of `structured`/`tools`/`vision` in `observed.features`, every other item (e.g. `reasoning`) in the reviewed family entry's features — no family entry → ineligible; `min_context_tokens <= observed.context_length` (unknown length fails a stated minimum); price known; `not require_paid`; `worst_case_usd <= snapshot.funded.available_usd` and, when set, `worst_case_credits <= max_credits`. `allow_paid` and the opt-in flag are not consulted. The reviewed table's `capabilities` and `quality_tier` are not consulted for this backend. Candidates in this task still sort with the existing key; Task 12 owns ordering. `approved_ceiling_credits` for a funded candidate is `available_usd * USD_TO_CREDITS`.
- [ ] Step 1: Write the failing test
```python
sel = lambda profile, snap, pol=TEST_FUNDED_POLICY, **kw: select(build_requirement(profile, BUDGET, **kw), snap, funded_policy=pol)
ids = lambda chain: {c.model_ref.model_id for c in chain.candidates}
def test_floor_and_flags_decide_eligibility():
    assert ids(sel("cheap_structured", snapshot(local=False))) <= {A, A2, B, C, E} and D not in ids(sel("cheap_structured", snapshot(local=False)))
    assert B not in ids(sel("deep_review", snapshot()))                 # general 35 < 40
    assert ids(sel("vision", snapshot())) == {C}                        # the only one with the image flag
    deep_code = ids(sel("deep_code", snapshot(), policy_with(max_chain_slots=9)))
    assert deep_code == {A, A2, C, E}                                   # coding ≥ 40; B (30) out
@pytest.mark.parametrize("snap_kw,pol", [                                # every fail-closed case in spec 5.4 — Review Focus 1
    ({"sources": {"leaderboard": ("unavailable", 0.0)}}, None),
    ({"sources": {"leaderboard": ("last_known_good", 3601.0)}}, None),
    ({"sources": {"hf_catalog": ("last_known_good", 3601.0)}}, None),
    ({"sources": {"hf_catalog": ("unavailable", 0.0)}}, None),
    ({"available_usd": None}, None),                                     # guard unavailable
    ({}, "unset_floor"), ({}, "unset_ceiling")])
def test_fail_closed_table(snap_kw, pol):
    policy = {"unset_floor": policy_with(deep=None), "unset_ceiling": policy_with(deep_review_ceiling=None), None: TEST_FUNDED_POLICY}[pol]
    with pytest.raises(ModelUnavailable):
        sel("deep_review", snapshot(local=False, **snap_kw), policy)
def test_leaderboard_lkg_at_exactly_the_limit_is_still_fresh():
    assert A in ids(sel("deep_review", snapshot(sources={"leaderboard": ("last_known_good", 3600.0)}), policy_with(max_chain_slots=9)))
def test_requirement_without_a_profile_gets_no_funded_candidate():
    with pytest.raises(ModelUnavailable):
        select(ModelRequirement(capability="deep", call_budget=BUDGET), snapshot(local=False), funded_policy=TEST_FUNDED_POLICY)
def test_unobservable_features_and_context():                            # Review Focus 5
    wide = policy_with(max_chain_slots=9)
    assert ids(sel("deep_review", snapshot(), wide, required_features=frozenset({"reasoning"}))) == {E}   # only the reviewed family
    assert ids(sel("deep_review", snapshot(), wide, required_features=frozenset({"tools"}))) == {A}
    got = ids(sel("deep_review", snapshot(), wide, min_context_tokens=100_000))
    assert A in got and A2 not in got                                     # same repo, provider B has 32000
def test_allowance_bounds_each_candidate_and_needs_no_opt_in():
    got = ids(sel("cheap_structured", snapshot(local=False, available_usd=0.004), policy_with(max_chain_slots=9)))
    assert got == {B, E}                                                  # 0.0018 and 0.0036 fit; 0.009 does not
    assert all(c.cost_class == "funded" for c in sel("cheap_structured", snapshot(local=False)).candidates)
def test_no_hugging_face_models_leaves_existing_behaviour_untouched():
    snap = snapshot(dartmouth=(QWEN, GEMMA4, GPT_OSS), hf=(), available_usd=None)
    assert [c.model_ref.model_id for c in sel("deep_review", snap).candidates] == [QWEN, GEMMA4, GPT_OSS]
```
- [ ] Step 2: `pytest tests/unit/test_model_selection_funded_select.py -q` → FAIL (`TypeError: select() got an unexpected keyword argument 'funded_policy'`).
- [ ] Step 3: Implement the funded branch in the eligibility loop; extend `_no_candidate_reason` with the `hf_catalog`/`leaderboard`/`funded` sources.
- [ ] Step 4: `pytest tests/unit/test_model_selection_funded_select.py tests/unit/test_model_selection_select.py tests/unit/test_config_consistency.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/model_selection/select.py tests/unit/test_model_selection_funded_select.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): funded eligibility in select (floors, observed flags, allowance; fail closed)" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 12: `select` — ordering, per-profile ranking, class-aware freshness
**Files:** Modify `src/llmxive/model_selection/select.py` (88-112 `_enforce_fresh_snapshot`, 199-247 ordering), `src/llmxive/model_selection/policy.py` (60: `SELECTION_POLICY_VERSION = 3`) · Test: append to `tests/unit/test_model_selection_funded_select.py`; update any pinned `== 2` version assertion found by `git grep -n "SELECTION_POLICY_VERSION\|selection_policy_version ==" tests/`
**Interfaces:**
- Produces: class rank free-remote 0 → funded 1 → free-local 2 → paid 3 as the first sort key; funded group ordered by `_order_funded` then cut to `funded_policy.max_chain_slots`; paid candidates dropped when the allowance is what removed funded ones (explanation line `"funded allowance exhausted — paid not reached (Constitution IV)"`) unless `require_paid`; `_enforce_fresh_snapshot` rewritten per spec 5.9.3.
- Algorithm the tests do not fully determine:
```python
def _order_funded(items, rule, *, best_quality):        # items: (ModelRef, cost_credits, score, unmet_pref)
    by_cost = lambda i: (i[1], -i[2], i[3], i[0].model_id)
    if rule.rank == "cheapest" and not best_quality:
        return sorted(items, key=by_cost)
    ceiling = rule.per_call_ceiling_usd * USD_TO_CREDITS
    fits = [i for i in items if i[1] <= ceiling]
    return sorted(fits, key=lambda i: (-i[2], i[3], i[1], i[0].model_id)) if fits else sorted(items, key=by_cost)
```
  Freshness for `require_fresh_snapshot`: the Dartmouth class is fresh when `catalog` and `credit` are both fresh-enough (today's rule); the funded class is fresh when `hf_catalog` and `leaderboard` are fresh-enough and `funded` is `live`. Raise `ModelUnavailable` only when **neither** class is fresh; otherwise drop the candidates of a class that is not fresh (local candidates are never gated, as today).
- [ ] Step 1: Write the failing test
```python
order = lambda chain: [c.model_ref.model_id for c in chain.candidates]
def test_order_is_free_remote_then_funded_then_local_then_paid():
    snap = snapshot(dartmouth=(QWEN, GEMMA4, GPT_OSS), claude=True, paid_opt_in=True)
    assert order(sel("cheap_structured", snap, allow_paid=True)) == [QWEN, GEMMA4, GPT_OSS, B, E, LOCAL, CLAUDE]
def test_funded_slots_never_truncate_local_or_paid():                     # Review Focus 4: 5 eligible funded, cap 8
    chain = sel("standard_generation", snapshot(dartmouth=(QWEN, GEMMA4, GPT_OSS), claude=True, paid_opt_in=True), allow_paid=True)
    assert sum(c.cost_class == "funded" for c in chain.candidates) == 2 and order(chain)[-2:] == [LOCAL, CLAUDE]
def test_cheapest_profiles_rank_by_cost_then_score():
    assert order(sel("cheap_structured", snapshot())) == [B, E, LOCAL]
def test_best_profiles_rank_by_score_within_the_ceiling():
    assert order(sel("deep_review", snapshot())) == [A2, A]               # 60 = 60 → cheaper provider first
    assert order(sel("deep_code", snapshot(), policy_with(deep_code_ceiling=0.02))) == [A2, E]   # A (0.036) over the ceiling
def test_when_nothing_fits_the_ceiling_the_cheapest_eligible_leads():
    assert order(sel("deep_code", snapshot(), policy_with(deep_code_ceiling=0.001))) == [E, C]
def test_funded_best_quality_overrides_cheapest_first():
    assert order(sel("cheap_structured", snapshot(local=False), funded_best_quality=True)) == [A2, A]
def test_require_paid_excludes_funded():                                  # Review Focus 4
    snap = snapshot(claude=True, paid_opt_in=True)
    assert order(sel("deep_review", snap, allow_paid=True, require_paid=True)) == [CLAUDE]
def test_exhausted_allowance_is_outage_not_paid():                        # Review Focus 4
    snap = snapshot(claude=True, paid_opt_in=True, available_usd=0.001)
    chain = sel("cheap_structured", snap, allow_paid=True)
    assert order(chain) == [LOCAL] and any("funded allowance exhausted" in e for e in chain.explanation)
    with pytest.raises(ModelUnavailable): sel("deep_review", snap, allow_paid=True)
    assert order(sel("deep_review", snap, allow_paid=True, require_paid=True)) == [CLAUDE]      # an explicit paid rung is still paid
def test_independence_dimensions_work_unchanged():
    base = IndependenceBaseline(families=frozenset({"alpha-large"}))
    assert order(sel("independent_review", snapshot(), independence_against=base)) == [C, E]
STALE = ("last_known_good", 901.0); GONE = ("unavailable", 0.0)
def test_review_is_served_by_funded_when_dartmouth_is_not_fresh():
    snap = snapshot(dartmouth=(QWEN,), sources={"catalog": STALE, "credit": GONE})
    assert order(sel("independent_review", snap)) == [A2, A]
def test_review_is_served_by_dartmouth_when_funded_is_not_fresh():
    for bad in ({"leaderboard": STALE}, {"hf_catalog": GONE}):
        assert order(sel("independent_review", snapshot(dartmouth=(QWEN, GEMMA4), sources=bad))) == [QWEN, GEMMA4]
    assert order(sel("independent_review", snapshot(dartmouth=(QWEN, GEMMA4), available_usd=None))) == [QWEN, GEMMA4]
def test_review_is_an_outage_only_when_no_class_is_fresh():
    with pytest.raises(ModelUnavailable, match="fresh"):
        sel("independent_review", snapshot(dartmouth=(QWEN,), sources={"credit": GONE, "leaderboard": STALE}))
def test_select_stays_byte_identical_and_versioned():
    s = snapshot(dartmouth=(QWEN,)); assert sel("deep_review", s) == sel("deep_review", s)
    assert sel("deep_review", s).selection_policy_version == 3
```
- [ ] Step 2: `pytest tests/unit/test_model_selection_funded_select.py -q` → FAIL (`test_order_is_free_remote…`: funded candidates not ordered before `LOCAL`).
- [ ] Step 3: Implement the ordering, the slot cut, the paid suppression and the freshness rewrite; bump the version and extend the `policy.py` docstring with a "v3 (spec 027)" paragraph.
- [ ] Step 4: `pytest tests/unit/test_model_selection_funded_select.py tests/unit/test_model_selection_select.py tests/unit/test_model_selection_policy.py tests/unit/test_config_consistency.py tests/unit/test_us5_ac1_primary_preservation.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/model_selection/select.py src/llmxive/model_selection/policy.py tests/unit/test_model_selection_funded_select.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): free-remote > funded > local > paid ordering, per-profile funded ranking, class-aware review freshness" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`
  (If the grep in **Files** found a pinned version assertion, add that test file to `git add`.)

### Task 13: `execute` / `route_chat` — reserve, dispatch once, settle the real cost
**Files:** Modify `src/llmxive/model_selection/execute.py` (94-106, new `_open_funded_reservation` after 246, 249-265, 381-423, 490-512, 541-562), `src/llmxive/model_selection/route.py` (146-179, 244-265, 362-378, 409-420), `README.md` (180-199, 256, 294-296), `CLAUDE.md` (20) · Test `tests/integration/test_funded_execute.py`
**Interfaces:**
- Consumes: `hf_budget.{funded_observer, settle_funded}`, `ledger_transport.funded_ledger_config_from_env`, `reservations.{reserve, ReservationLease, lease_duration_for}`, `Candidate.cost_class`, `ChatResponse.input_tokens/output_tokens`.
- Produces: `execute(..., funded_ledger_config: LedgerConfig | None = None, funded_observer: Callable[[], CreditObservation] | None = None)`; `ExecutionResult.charged_usd: float | None = None`; `route_chat(..., funded_ledger_config: LedgerConfig | None = None, funded_policy: FundedPolicy | None = None)` (forwarded to `select`; an injection seam beside `snapshot=`); `_requirement_digest` includes `profile` and `funded_best_quality`; `overrides.funded_best_quality` ORs into the requirement.
- Behaviour: branch on `candidate.cost_class` (the existing `not pricing.is_free` tests at 390 and 403 become `== "paid"`). For `"funded"`: skip (advance) unless `chain.snapshot_provenance["funded"].source == "live"` and a ledger repo and config resolve (`None` → `funded_ledger_config_from_env()`, a `LedgerError` skips); reserve `worst_case_credits / USD_TO_CREDITS` once — never `× retries` — under the same lease heartbeat; a `LedgerError` skips; dispatch with `retries=1`; in `finally`, `settle_funded(charged_usd=…)` where the charge is `input_tokens × pricing.input + output_tokens × pricing.output` when the response carries both counts and `None` (full reservation) on any failure or missing usage; return the response with `cost_estimate_usd` set to that charge. `ReservationOpened`/`DispatchStarted`/`CandidateOutcome` are emitted as for paid; `reservation_authority` (whose unit is Dartmouth credits) is not consulted for funded.
- README "Models & cost": the order free hosted → Hugging Face (funded, within `LLMXIVE_HF_MONTHLY_USD`) → local → paid; that ranking uses Artificial Analysis indices as listed by OpenRouter, used for internal ranking only and not redistributed (spec 5.9.7 attribution); the new env vars. `CLAUDE.md:20`: backends are Dartmouth Chat + Hugging Face Inference Providers + local transformers.
- [ ] Step 1: Write the failing test (real git ledger in `tmp_path`; the fake backend is the `backend_factory` seam FR-015 sanctions)
```python
CFG = LedgerConfig(remote=None, ref=FUNDED_LEDGER_REF)
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
def test_funded_reserve_call_settle_records_real_cost(repo):
    res = _run(repo, _HF({}), sel("cheap_structured", snapshot(local=False)))       # leader B
    opened = next(e for e in events(repo) if e["type"] == "open"); done = next(e for e in events(repo) if e["type"] == "reconciled")
    assert opened["model"] == B and opened["worst_case_credits"] == pytest.approx(0.0018) and opened["budget_epoch"] == "2026-11"
    assert done["charged"] == pytest.approx(1200 * 1e-7 + 300 * 4e-7)               # usage × the priced provider's rate
    assert res.charged_usd == done["charged"] == res.response.cost_estimate_usd
    assert read_events(repo) == []                                                   # Dartmouth credit ledger untouched
def test_funded_dispatches_once_and_reserves_times_one(repo):                       # Review Focus 3
    be = _HF({B: TransientBackendError("503"), E: TransientBackendError("503")})
    with pytest.raises(ChainExhausted): _run(repo, be, sel("cheap_structured", snapshot(local=False)), retries=3)
    assert be.calls == [B, E]                                                        # one attempt each despite retries=3
    assert [e["worst_case_credits"] for e in events(repo) if e["type"] == "open"] == [pytest.approx(0.0018), pytest.approx(0.0036)]
def test_missing_usage_charges_full_reservation(repo):                              # Review Focus 3
    _run(repo, _HF({B: ChatResponse("ok", B, "huggingface")}), sel("cheap_structured", snapshot(local=False)))
    assert next(e for e in events(repo) if e["type"] == "reconciled")["charged"] == pytest.approx(0.0018)
def test_failed_call_is_charged_its_reservation_and_chain_advances(repo):
    res = _run(repo, _HF({B: BackendUnavailable("402")}), sel("cheap_structured", snapshot(local=False)))
    assert res.model_ref.model_id == E
    charged = {e["reservation_id"].split("-prov-a-")[0]: e["charged"] for e in events(repo) if e["type"] == "reconciled"}
    assert sorted(charged.values()) == [pytest.approx(1200 * 2e-7 + 300 * 8e-7), pytest.approx(0.0018)]
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
def test_route_chat_serves_funded_and_digest_sees_the_profile(repo):
    be = _HF({})
    r = route_chat(MSG, profile="deep_review", max_tokens=512, snapshot=snapshot(local=False), backend_factory=lambda n: be,
                   ledger_repo=repo, funded_ledger_config=CFG, funded_policy=TEST_FUNDED_POLICY)   # production values are unset until Task 19
    assert r.backend == "huggingface" and r.cost_estimate_usd > 0
    a = _requirement_digest(build_requirement("deep_review", BUDGET)); b = _requirement_digest(build_requirement("independent_review", BUDGET))
    assert a != _requirement_digest(build_requirement("deep_review", BUDGET, funded_best_quality=True)) and a != b
```
- [ ] Step 2: `pytest tests/integration/test_funded_execute.py -q` → FAIL (`TypeError: execute() got an unexpected keyword argument 'funded_ledger_config'`).
- [ ] Step 3: Implement the funded branch in `execute` and the two `route_chat` keywords. Update README and `CLAUDE.md` in this commit.
- [ ] Step 4: `pytest tests/integration/test_funded_execute.py tests/integration/test_model_selection_execute.py tests/unit/test_model_selection_execute.py tests/unit/test_model_selection_route.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/model_selection/execute.py src/llmxive/model_selection/route.py README.md CLAUDE.md tests/integration/test_funded_execute.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): funded reserve -> single dispatch -> settle at usage x catalog price" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 14: Truthful run-log entries
**Files:** Modify `src/llmxive/state/runlog.py` (32-66), `src/llmxive/agents/base.py` (144, 160-168, 206-222), `src/llmxive/speckit/slash_command.py` (144, 159, 174-190), `src/llmxive/agents/implementer.py` (1070-1073, 1722-1729, 2028-2054) · Test `tests/unit/test_runlog_funded.py`
**Interfaces:**
- Consumes: `BackendName.HUGGINGFACE`, `ChatResponse.cost_estimate_usd` (set by `execute` in Task 13).
- Produces: `_check_cost_invariant` accepts a non-zero cost when `entry.backend is BackendName.HUGGINGFACE` (allowance-guarded in code; Constitution IV 1.4.0) and still raises for any other backend without `LLMXIVE_PAID_OPT_IN`; each of the three run-log writers records the **sum** of `cost_estimate_usd` over every response received in that run and the backend of the last response (the implementer via new `self._last_cost_usd: float`, and `BackendName(self._last_backend_used)` instead of the `DARTMOUTH` placeholder once a response exists).
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
def test_implementer_run_log_attributes_funded_backend_and_cost(...):          # Review Focus 3
    # Two tasks answered by "huggingface" at 0.01 and 0.02 → entry.backend is HUGGINGFACE, cost == pytest.approx(0.03).
```
  For the last two, build the agent and context exactly as the nearest existing test does (`git grep -ln "chat_with_fallback" tests/unit tests/integration | head`) — see "Not determined from the code" for why this plan does not name it.
- [ ] Step 2: `pytest tests/unit/test_runlog_funded.py -q` → FAIL (`CostInvariantError` in the first test).
- [ ] Step 3: Implement the four edits; update the `CostInvariantError` docstring to name the funded path.
- [ ] Step 4: `pytest tests/unit/test_runlog_funded.py tests/integration/test_free_backend_only.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/state/runlog.py src/llmxive/agents/base.py src/llmxive/speckit/slash_command.py src/llmxive/agents/implementer.py tests/unit/test_runlog_funded.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "fix(027): run log records the real backend and cost of funded calls" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 15: Tier ladder — the funded-best rung
**Files:** Modify `src/llmxive/state/execution_status.py` (49-64 comment, 74-104, 125-153, 196-222) · Test `tests/unit/test_execution_tier_constraints.py` (append; change one existing expectation)
**Interfaces:**
- Consumes: `RequirementOverrides.funded_best_quality`, `hf_budget.funded_headroom_available`.
- Produces: `TierConstraint.funded_best_quality: bool = False`, property `is_funded`; `_FUNDED_BEST_RUNG = TierConstraint(allow_paid=False, funded_best_quality=True)`; ladder `(tier 0 base, tier 1 exclude_leader, tier 2 funded-best, [tier 3 paid when LLMXIVE_EXECUTION_PAID_ESCALATION])`; `funded_tier_usable() -> bool` (fails closed); `next_usable_tier` skips the funded rung when it is unusable or `free_only`.
- [ ] Step 1: Write the failing test
```python
def test_ladder_is_default_second_opinion_funded_best_then_paid(monkeypatch):
    assert [(c.exclude_leader, c.funded_best_quality, c.is_paid) for c in es.model_tier_ladder()] == \
           [(False, False, False), (True, False, False), (False, True, False)]
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_ESCALATION", "1")
    assert es.model_tier_ladder()[-1].is_paid and len(es.model_tier_ladder()) == 4
def test_funded_rung_overrides_need_no_paid_authority():
    ov = es.tier_constraint(2).to_overrides()
    assert ov.funded_best_quality is True and ov.allow_paid is False and ov.require_paid is False
def test_funded_rung_is_skipped_without_headroom_and_for_fabrication(monkeypatch):
    monkeypatch.setattr(es, "funded_tier_usable", lambda: False); assert es.next_usable_tier(1) is None
    monkeypatch.setattr(es, "funded_tier_usable", lambda: True);  assert es.next_usable_tier(1) == 2
    assert es.next_usable_tier(1, free_only=True) is None
def test_funded_tier_usable_fails_closed_when_unconfigured(monkeypatch):
    monkeypatch.delenv("LLMXIVE_HF_BILL_TO", raising=False); assert es.funded_tier_usable() is False
```
  Existing `test_fabrication_free_only_never_reaches_paid`: the paid rung moves from index 2 to 3, so its `assert es.next_usable_tier(1) == 2` becomes `== 3` (funded unusable offline, paid stubbed usable). No other existing assertion changes.
- [ ] Step 2: `pytest tests/unit/test_execution_tier_constraints.py -q` → FAIL (`AttributeError: 'TierConstraint' object has no attribute 'funded_best_quality'`).
- [ ] Step 3: Implement; rewrite the ladder comment block to describe four rungs.
- [ ] Step 4: `pytest tests/unit/test_execution_tier_constraints.py tests/unit/test_execution_exhaustion_flow.py tests/unit/test_convergence_kickback_flow.py tests/unit/test_exclude_leader.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/state/execution_status.py tests/unit/test_execution_tier_constraints.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): funded best-quality rung between the free and paid escalation tiers" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 16: `llmxive preflight` selection report
**Files:** Modify `src/llmxive/preflight.py` (1-13 docstring, 27-30, 100-128) · Test `tests/unit/test_preflight_selection_report.py`
**Interfaces:**
- Consumes: `runtime_snapshot`, `select`, `build_requirement`, `PROFILES`, `FundedPolicy`.
- Produces: `selection_report(snap: RuntimeSnapshot, *, funded_policy: FundedPolicy | None = None) -> list[str]` (pure; no network); `main()` appends its lines as `[preflight] info:` after one `runtime_snapshot()` call (catalog GETs and a ledger fetch — no chat request). `"LLMXIVE_HF_BILL_TO"` and `"LLMXIVE_FUNDED_LEDGER_ANCHOR"` join the optional-setting notices. `_REPORT_BUDGET = CallBudget(8_000, 4_096)` — a nominal budget used only to rank for display.
- Line formats: `backends: dartmouth=<source> huggingface=<source> local=<source>` (the `catalog` / `hf_catalog` / `local` provenance); `funded allowance: $50.00/month, spent $10.00 this month, $5.00 available now (2026-11)` or `funded allowance: unavailable`; per profile `top candidate [<profile>]: <model_id> (<backend>, <cost_class>, worst case $<x.xxxx>)` or `top candidate [<profile>]: none — <first 120 chars of the ModelUnavailable message>`.
- [ ] Step 1: Write the failing test
```python
def test_report_names_three_backends_allowance_spend_and_top_candidates():
    lines = selection_report(snapshot(dartmouth=(), sources={"catalog": ("unavailable", 0.0)}), funded_policy=TEST_FUNDED_POLICY)
    assert lines[0] == "backends: dartmouth=unavailable huggingface=live local=live"
    assert lines[1] == "funded allowance: $50.00/month, spent $10.00 this month, $5.00 available now (2026-11)"
    assert f"top candidate [cheap_structured]: {B} (huggingface, funded, worst case $0.0024)" in lines   # at _REPORT_BUDGET: 8000×1e-7 + 4096×4e-7 = 0.0024384
    assert sum(l.startswith("top candidate [") for l in lines) == len(PROFILES)
def test_report_says_unavailable_and_none_without_raising():
    lines = selection_report(snapshot(local=False, available_usd=None), funded_policy=TEST_FUNDED_POLICY)
    assert lines[1] == "funded allowance: unavailable" and any(l.startswith("top candidate [deep_review]: none — ") for l in lines)
def test_report_makes_no_request():
    with ReplayServer({}) as srv:                      # nothing in selection_report can reach a network: it takes a snapshot
        selection_report(snapshot(), funded_policy=TEST_FUNDED_POLICY)
    assert srv.requests == []
```
- [ ] Step 2: `pytest tests/unit/test_preflight_selection_report.py -q` → FAIL (`ImportError: selection_report`).
- [ ] Step 3: Implement `selection_report` and the `main()` lines; worst case is `worst_case_usd(pricing, _REPORT_BUDGET)` formatted `:.4f`.
- [ ] Step 4: `pytest tests/unit/test_preflight_selection_report.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/preflight.py tests/unit/test_preflight_selection_report.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): preflight reports backend reachability, allowance, spend and top candidates" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 17: Workflow env wiring
**Files:** Modify `.github/workflows/advance.yml` (85-93), `llmxive-pipeline.yml` (71-74, 77-100), `maintenance.yml` (34-42), `pipeline-personality.yml` (28-36), `reprocess.yml` (41-49), `submission-intake.yml` (38-40), `prompt-eval.yml` (30-31), `spec015-calibration.yml` (70-71), `llmxive-real-call-tests.yml` (26-30), `llmxive-real-call-nightly.yml` (23-27) · Test `tests/unit/test_workflow_hf_env.py`
**Interfaces:**
- Produces: in every `env:` mapping that passes `DARTMOUTH_CHAT_API_KEY: ${{ secrets.DARTMOUTH_CHAT_API_KEY }}`, the three lines `HF_TOKEN: ${{ secrets.HF_TOKEN }}`, `LLMXIVE_HF_BILL_TO: ${{ vars.LLMXIVE_HF_BILL_TO }}`, `LLMXIVE_FUNDED_LEDGER_ANCHOR: ${{ vars.LLMXIVE_FUNDED_LEDGER_ANCHOR }}`.
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
    assert seen >= 11
def test_bill_to_is_a_variable_never_a_secret():
    assert "secrets.LLMXIVE_HF_BILL_TO" not in "".join(p.read_text() for p in WF.glob("*.yml"))
```
- [ ] Step 2: `pytest tests/unit/test_workflow_hf_env.py -q` → FAIL (`advance.yml`: `HF_TOKEN` is `None`).
- [ ] Step 3: Add the lines. Then prove no trigger moved: `git diff -- .github/workflows | grep -nE '^[+-][^+-].*(cron|schedule:|workflow_dispatch|^[+-]on:)'` must print nothing.
- [ ] Step 4: `pytest tests/unit/test_workflow_hf_env.py -q` → PASS.
- [ ] Step 5: `git add .github/workflows/advance.yml .github/workflows/llmxive-pipeline.yml .github/workflows/maintenance.yml .github/workflows/pipeline-personality.yml .github/workflows/reprocess.yml .github/workflows/submission-intake.yml .github/workflows/prompt-eval.yml .github/workflows/spec015-calibration.yml .github/workflows/llmxive-real-call-tests.yml .github/workflows/llmxive-real-call-nightly.yml tests/unit/test_workflow_hf_env.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "ci(027): pass HF_TOKEN, LLMXIVE_HF_BILL_TO and the funded-ledger anchor to model-calling jobs" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 18: Enforcement — the pin detector sees `<repo>:<provider>`
**Files:** Modify `src/llmxive/model_selection/inventory.py` (54-79), `specs/026-model-selection-consolidation/migration_manifest.json`, `migration_manifest.md` (regenerated) · Test: append to `tests/unit/test_model_selection_enforcement.py` and `tests/unit/test_model_selection_inventory.py`
**Interfaces:**
- Consumes: how sanction is decided today — `inventory.categorize` allows a literal only in `_CANONICAL_FILES` (`policy.py`), in a `_CANONICAL_SYMBOLS` pair, or under `tests/`; everything else in `src/llmxive/` is a `migration_target` and `enforcement.find_pin_violations` rejects it unconditionally. This plan adds **no** production model-id literal, so neither allowlist is extended.
- Produces: `_HF_SLASH_MODEL` accepts an optional `:<provider>` suffix (`(?::[A-Za-z0-9][A-Za-z0-9._-]*)?`); `_HF_ORGS` gains every org prefix present in `tests/fixtures/hf_funded/router_models.json` (a reviewed literal set, generated once from the fixture).
- [ ] Step 1: Write the failing test
```python
def test_detector_recognises_every_recorded_router_id_with_and_without_provider():
    for m in _load("router_models.json")["payload"]["data"]:
        assert looks_like_model_id(m["id"]), m["id"]
        for p in m["providers"]: assert looks_like_model_id(f"{m['id']}:{p['provider']}")
    assert not looks_like_model_id("state/model_selection") and not looks_like_model_id("acme/alpha-large:prov-a")
def test_a_planted_provider_pinned_literal_in_production_is_a_violation(tmp_path):
    rid = _load("router_models.json")["payload"]["data"][0]; pin = f"{rid['id']}:{rid['providers'][0]['provider']}"
    _write(tmp_path / "src/llmxive/backends/huggingface.py", f'DEFAULT = "{pin}"\n')
    assert [v["file"] for v in find_pin_violations(tmp_path)] == ["src/llmxive/backends/huggingface.py"]
def test_the_real_tree_still_has_zero_violations_after_027():
    assert find_violations(REPO_ROOT) == []
```
- [ ] Step 2: `pytest tests/unit/test_model_selection_enforcement.py tests/unit/test_model_selection_inventory.py -q` → FAIL (first new test: an id with a `:provider` suffix is not recognised).
- [ ] Step 3: Implement, then regenerate the manifest: `python -m llmxive.model_selection.inventory`.
- [ ] Step 4: same command → PASS (including the existing `test_committed_manifest_is_current_with_the_live_scan`).
- [ ] Step 5: `git add src/llmxive/model_selection/inventory.py specs/026-model-selection-consolidation/migration_manifest.json specs/026-model-selection-consolidation/migration_manifest.md tests/unit/test_model_selection_enforcement.py tests/unit/test_model_selection_inventory.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "test(027): pin detector covers Hugging Face repo:provider ids; manifest regenerated" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 19: Maintainer-confirmed floors and ceilings (BLOCKED on the maintainer)
**Files:** Modify `src/llmxive/model_selection/policy.py` (`FUNDED_POLICY`, `SELECTION_POLICY_VERSION = 4`) · Test: append to `tests/unit/test_funded_policy.py`; update the version expectation in `test_select_stays_byte_identical_and_versioned`
**Interfaces:**
- Produces: `FUNDED_POLICY` with no `None`; `FUNDED_POLICY_CONFIRMED = "<maintainer>, <YYYY-MM-DD>"` beside it.
- [ ] Step 0 (gate): run `python scripts/hf/score_distribution.py`, send its output to the maintainer with these eleven blanks, and stop until they answer: `min_score` for `cheap`, `standard`, `deep`, `deep_code`, `vision`; `per_call_ceiling_usd` for each of the six profiles; and whether `max_chain_slots = 2` stands. Do not choose values.
- [ ] Step 1: Write the failing test
```python
def test_funded_policy_is_confirmed_before_merge():
    assert all(f.min_score is not None for f in FUNDED_POLICY.floors.values())
    assert all(p.per_call_ceiling_usd is not None for p in FUNDED_POLICY.profiles.values())
    assert re.fullmatch(r".+, \d{4}-\d{2}-\d{2}", FUNDED_POLICY_CONFIRMED)
def test_confirmed_policy_serves_every_profile_on_the_recorded_catalog():
    snap = recorded_snapshot()                    # tests/helpers/funded.py: the two recorded fixtures + a live $5 guard
    for name in PROFILES:
        chain = select(build_requirement(name, BUDGET), snap)
        assert chain.candidates and all(c.cost_class == "funded" for c in chain.candidates)
        rule = FUNDED_POLICY.profiles[name]; floor = FUNDED_POLICY.floors[rule.floor]
        for c in chain.candidates:
            s = snap.scores[c.model_ref.model_id]
            assert (s.coding if floor.score_field == "coding" else s.general) >= floor.min_score
            assert floor.required_flags <= snap.observed[c.model_ref.model_id].features
```
  (The recorded leaderboard carries synthetic scores, so the second test proves the table is internally usable; the real distribution is exercised by Task 20.)
- [ ] Step 2: `pytest tests/unit/test_funded_policy.py -q` → FAIL (`test_funded_policy_is_confirmed_before_merge`).
- [ ] Step 3: Enter the maintainer's values; add `recorded_snapshot()` to the helper. If the second test fails because a confirmed floor exceeds every synthetic score for a profile, raise that with the maintainer — do not edit the fixture's scores to fit.
- [ ] Step 4: `pytest tests/unit/test_funded_policy.py tests/unit/test_model_selection_funded_select.py -q` → PASS.
- [ ] Step 5: `git add src/llmxive/model_selection/policy.py tests/helpers/funded.py tests/unit/test_funded_policy.py tests/unit/test_model_selection_funded_select.py && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(027): maintainer-confirmed funded floors and per-call ceilings" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 20: Real-call lane
**Files:** Create `tests/real_call/test_hf_funded_real.py` · Modify `scripts/hf/README.md` (acceptance evidence for this lane: date, tokens, cost)
**Interfaces:**
- Consumes: everything above. Operator prerequisites, once: `llmxive funded-ledger-bootstrap --remote origin`; set the Actions variables `LLMXIVE_HF_BILL_TO` and `LLMXIVE_FUNDED_LEDGER_ANCHOR`; protect `refs/llmxive/funded-ledger` fast-forward-only.
- Decisions: fast module (not added to `_SLOW_MODULES`); a missing `HF_TOKEN`, `LLMXIVE_HF_BILL_TO` or `LLMXIVE_FUNDED_LEDGER_ANCHOR` **fails** with the variable's name (not a skip); Dartmouth is made unreachable the way `tests/real_call/test_dartmouth_outage_falls_back.py` does it — a `backend_factory` that returns a backend raising `BackendUnavailable` for `"dartmouth"` and `make_backend(name)` otherwise; `max_tokens=1024`, `retries=1`; the spend lands on the production funded ledger (it is real spend on the same resource group). Total: eight short chats — cents.
- [ ] Step 1: Write the test
```python
pytestmark = pytest.mark.skipif(os.environ.get("LLMXIVE_REAL_TESTS") != "1", reason="real-call test; set LLMXIVE_REAL_TESTS=1")
@pytest.fixture(scope="module", autouse=True)
def _require_settings():
    missing = [v for v in ("LLMXIVE_HF_BILL_TO", "LLMXIVE_FUNDED_LEDGER_ANCHOR") if not os.environ.get(v)]
    assert not missing and load_hf_token(), f"real-call lane needs HF_TOKEN and {missing}"
def test_live_catalog_and_leaderboard_parse_and_join():                        # keyless, free
    refs, pricing, _ = _parse_hf_catalog(fetch_router_catalog())
    assert refs and all(p.input_usd_per_token is None or p.input_usd_per_token >= 0 for p in pricing.values())
    assert {r.model_id.rsplit(":", 1)[0] for r in refs} & set(_fetch_leaderboard())
def test_org_balance_reads_or_declines_cleanly():
    bal = fetch_org_balance_usd(); assert bal is None or bal >= 0
@pytest.mark.parametrize("profile", ["cheap_structured", "standard_generation", "deep_review", "deep_code", "independent_review"])
def test_each_profile_is_served_by_hugging_face_and_spend_equals_usage_times_price(profile):
    snap = runtime_snapshot(); before = _reconciled_ids()
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
    img = ImagePart.from_bytes("image/png", _solid_png(256, 256, (255, 0, 0)))
    r = route_chat([ChatMessage("user", (TextPart("What colour is this image? One word."), img))], profile="vision",
                   max_tokens=1024, retries=1, backend_factory=_dartmouth_down)
    assert r.backend == "huggingface" and "red" in r.text.lower()
def test_wrong_bill_to_is_a_402_outage_not_a_charge_to_another_account():
    model = sorted(m.model_id for m in runtime_snapshot().models if m.backend == "huggingface")[0]
    with pytest.raises(BackendUnavailable) as ei:
        HuggingFaceBackend(bill_to="000000000000000000000000").chat([ChatMessage("user", "hi")], model=model, max_tokens=8)
    assert disposition_of(ei.value) is CandidateDisposition.RETRY_ADVANCE and load_hf_token() not in str(ei.value)
```
- [ ] Step 2: `LLMXIVE_REAL_TESTS=1 pytest tests/real_call/test_hf_funded_real.py -q` with `LLMXIVE_HF_BILL_TO` unset → FAIL in `_require_settings` naming the variable (proves the lane cannot silently pass).
- [ ] Step 3: Set the three settings and run it for real.
- [ ] Step 4: `LLMXIVE_REAL_TESTS=1 pytest tests/real_call/test_hf_funded_real.py tests/real_call/test_model_selection_snapshot_real.py -q` → PASS; then `llmxive preflight` shows the spend this run added. Record date, token counts and total cost in `scripts/hf/README.md`.
- [ ] Step 5: `git add tests/real_call/test_hf_funded_real.py scripts/hf/README.md && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "test(027): real-call lane for the funded provider (per-profile, JSON, vision, 402, spend = usage x price)" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`

### Task 21: Full gate
**Files:** none expected; any fix goes to the file that owns the defect, with its own test.
- [ ] Step 1: `pytest tests/unit tests/contract tests/integration -m "not slow" -q` → all pass.
- [ ] Step 2: `ruff check src tests` → clean.
- [ ] Step 3: `LLMXIVE_REAL_TESTS=1 pytest tests/real_call/test_hf_funded_real.py tests/real_call/test_model_selection_snapshot_real.py -q` → pass.
- [ ] Step 4: If any of 1–3 needed a change, repeat **all three** from Step 1 (a fix for one check can break another), then: `git add <each file changed, by name> && PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "fix(027): <what the gate found>" -m $'Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01DcKtypjyK1UB7PSkync3eK'`
- [ ] Step 5: `git status --short` is empty; `git log --oneline` shows the task commits; confirm the constitution's `Last Amended` equals the merge date; open the PR with the Sync Impact Report from Task 1 in its description.

---

## Spec coverage

|Spec section|Task|
|-|-|
|§1–2 goals, anti-goals|11–14 (anti-goal 1: 6, 13, 14; 2: 11–13 extend `select`/`execute` only; 3: 9, 11; 4: 8)|
|§3 facts|Global Constraints; 4, 5, 9, 20 re-verify them against the live endpoints|
|5.1 backend, credentials|2, 3, 5|
|5.2 catalog component|9 (+ 11 `_component_of`)|
|5.3 quality component|9|
|5.4 policy, fail-closed|10, 11, 19|
|5.5 cost class, ordering|6, 12|
|5.6 allowance guard|7, 8, 13|
|5.7 wiring, preflight|16, 17|
|5.8 tests|4 (fixtures), 8, 11–13 (offline), 20 (real)|
|5.9.1 local after funded|12 · 5.9.2 ledger|7, 8, 13 · 5.9.3 freshness|12 · 5.9.4 unobservable|5, 11 · 5.9.5 paid controls, ladder|11, 12, 15 · 5.9.6 borrow, × 1|8, 13 · 5.9.7 attribution|9, 13 (README) · 5.9.8 vision|10|
|§6 constitution|1|
|§7 left to the builder|10, 19 (floors, ceilings); 5, 13 (retry count: one attempt); 4 (fixture format)|
|§8 open items|19 (floors); item 2 is listed below|

Gaps found in self-review and closed: run-log truthfulness (Task 14) and the detector's blindness to `:provider` ids (Task 18) had no owner in the first draft; chain truncation by `max_candidates` (Task 12) was implied by nothing in the spec.

## Spec issues found

1. **`cost_class` "derived from the backend, not from the price" cannot hold for Dartmouth**, which serves free and paid models from one backend (`select.py:184` reads `pricing.is_free`). Plan: funded ⇔ backend is `huggingface`; free/paid still follow the price (Task 6).
2. **"Reuses the existing shared pieces … the circuit breaker, empty-reply detection" — they are not shared.** `_CircuitBreaker` is private to `dartmouth.py:189-268` with Dartmouth wording; empty-reply handling is inline in `DartmouthBackend.chat` (`dartmouth.py:~1120-1142`). Only `invoke_with_deadline` and the exception taxonomy live in `base.py`. Plan moves the breaker and the content serializer (Task 3).
3. **A "permanent credential error" for 401/403 aborts the whole chain** (`router.py:162-163`), so a bad token would block the local last resort that 5.9.1 promises. Plan: a typed `BackendCredentialError` that `disposition_of` classifies SKIP (Task 3).
4. **Per-profile ranking needs the profile, and the requirement does not carry it** (`types.py:143-174`); `deep_review` and `deep_code` are both capability `"deep"` (`profiles.py:115-132`). Plan adds `ModelRequirement.profile` (Tasks 6, 10).
5. **"Using the existing transport and reserve → settle code" is not possible as-is:** the ref is hard-wired (`ledger_transport.py:66, 180-190`; `reservations.py:279, 470, 520, 581`) and no event can carry an actual charge (`reservations.py:348-369`). Plan adds `LedgerConfig.ref` and a `charged` amount (Task 7).
6. **G5 / anti-goal 1 versus the run log.** `BackendName` has no `huggingface` member (`types.py:185-189`), so `BackendName(response.backend)` raises at `agents/base.py:167` and `slash_command.py:159`; cost is hard-coded `0.0` (`agents/base.py:220`, `slash_command.py:189`, `implementer.py:2051`) and the implementer logs `DARTMOUTH` (`implementer.py:1070`); `_check_cost_invariant` rejects any non-zero cost without `LLMXIVE_PAID_OPT_IN` (`runlog.py:54-66`), contradicting 5.9.5 "no opt-in flag". Task 14.
7. **5.8 asks for a leaderboard fixture "captured from the real endpoints"; 5.3 and 5.9.7 forbid committing the scores.** Plan commits the real rows with deterministic synthetic scores, marked `scores_synthetic` (Task 4); the real numbers are only read live (Task 20) or printed (Task 10).
8. **5.9.5's ladder omits the existing tier-1 `exclude_leader` rung** (`execution_status.py:99-104`). Plan keeps it and inserts funded-best at index 2, moving paid to 3. Also: while Dartmouth is up the funded-best rung picks the same leader as tier 0, because free remote still ranks first — say so if the rung should instead require funded.
9. **§6 "exhausting the allowance is … not a licence to fall through to paid" versus the order "… → local → paid"** with `LLMXIVE_PAID_OPT_IN: "1"` in every pipeline workflow (`advance.yml:90`). Plan: when the allowance is what removed funded candidates, paid ones are dropped too, except on an explicit `require_paid` rung (Task 12). Confirm.
10. **"Borrow up to three days of allowance ahead" is ambiguous** (three days' worth in total, or today plus three). Plan uses today plus three, `BORROW_AHEAD_DAYS = 3` (Task 8).
11. **`max_candidates` is 8 (`profiles.py`) and the catalog has 158 models**, so funded pairs would truncate the local and paid tail. Plan caps funded at `max_chain_slots` (placeholder 2, confirmed in Task 19).
12. **5.9.2 charges the full reservation to any call without `usage`, including a 402/401** the provider certainly did not bill. RESOLVED 2026-11-23 (spec 5.9.2 amended): HTTP 401, 402 and 403 charge zero; every other call without `usage` charges the full reservation. Task 13 must add `test_pre_inference_rejection_charges_zero` beside `test_missing_usage_charges_full_reservation`.
13. **The pin detector cannot see `<repo>:<provider>` ids** (`inventory.py:76-79` anchors on a fixed org list and forbids `:`), so FR-014 enforcement would not have covered this provider. Task 18.

## Not determined from the code

- `scripts/hf/` does not exist at `70942bbae03` (only on `origin/main`); Tasks 2, 4, 5, 10 assume the integration branch has it.
- Which existing test drives `Agent.run` / the implementer with a stubbed `chat_with_fallback` — Task 14's last two tests name the assertions but point at a grep for the harness.
- How a spec-025 Attempt counts calls against `call_ceiling` (`self_improvement/attempt_config.py:38`); Task 13 assumes it counts `DispatchStarted` events, which funded emits unchanged.
- Whether any test pins `SELECTION_POLICY_VERSION == 2` (Task 12 greps for it).
- Whether `paper-compile.yml`, `signoff-poll.yml`, `audit.yml`, `hf-daily-papers.yml` reach a model call; they pass no Dartmouth key today, so Task 17's rule leaves them alone.
- Whether the Actions `GITHUB_TOKEN` may push `refs/llmxive/funded-ledger` (the credit-ledger anchor is not wired in any workflow at this commit, so there is no precedent to copy).
- Pre-existing and outside this spec: the workflows set `LLMXIVE_EXECUTION_PAID_TIERS` (a list of model ids) while the code reads `LLMXIVE_EXECUTION_PAID_ESCALATION` (`execution_status.py:70`), so the paid rung is never enabled in CI. Left untouched — enabling it is a spending decision.
