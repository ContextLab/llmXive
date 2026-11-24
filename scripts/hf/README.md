# Hugging Face pilot

The `contextlab` Academia subscription supplies optional storage and burst compute
for llmXive. Dartmouth remains the primary model backend; Hugging Face Inference
Providers is now a routed fallback backend (`llmxive.backends.huggingface`, billed
to the resource group below via `LLMXIVE_HF_BILL_TO`). These explicit pilot
commands do not change automatic model selection or upload project directories.

## Provisioned resources

- Organization: `contextlab` (Academia plan verified 2026-10-09).
- Resource group: `llmxive`, ID `6ac8defed831a06784773cfd`.
- Group spend limit set on Hugging Face at provisioning (2026-10-09): **$20** per
  month; Jobs and Inference Providers share it. Hugging Face enforces this limit on
  its side.
- llmXive's own funded allowance for routed inference is `LLMXIVE_HF_MONTHLY_USD`,
  default **$50** per month (`DEFAULT_MONTHLY_USD` in `llmxive.backends.hf_budget`),
  reserved and settled on the funded ledger before and after each call.
- Paid Spaces and Inference Endpoints: **$0** limits.
- Private versioned artifacts: <https://huggingface.co/datasets/contextlab/llmxive-artifacts>.
- Private working bucket: <https://huggingface.co/buckets/contextlab/llmxive-work>.
- Group settings: <https://huggingface.co/organizations/contextlab/settings/resource-groups/6ac8defed831a06784773cfd?tab=settings>.

Credits are pooled across the organization, not separate wallets attached to ten
bot accounts. At provisioning, the $20 group limit represented ten seats' monthly allocation. It does not
reserve credits against other lab usage, and is not an additional subscription.
HF enforces the group limit; jobs must specify this group and inference requests
must use its ID in `X-HF-Bill-To`. HF may stop running work shortly after a limit
is reached, so this is not a promise of zero overshoot.

## Credentials

Never commit credentials, put them in a command-line argument, log them, or use a
credential-bearing URL. The loader is `llmxive.credentials.load_hf_token` (this
helper calls it); it reads only `HF_TOKEN` (for a GitHub Actions secret) or the
macOS Keychain service `llmxive-huggingface`. It does not read a plaintext HF cache or repository `.env` file.
The current local credential is in Keychain. Eleven workflows under
`.github/workflows/` pass the `HF_TOKEN` secret to their jobs, together with the
Actions variables `LLMXIVE_HF_BILL_TO` and `LLMXIVE_FUNDED_LEDGER_ANCHOR`. Before enabling CI, create a dedicated fine-grained
HF token limited to the required project repositories, Jobs, and inference,
and save it as a GitHub Actions secret. Do not reuse a broad lab administrator
token in pull-request workflows. A service account can replace the personal
identity when unattended production usage is introduced.

## Explicit acceptance probes

Run from a checkout with llmXive dependencies installed:

```sh
python scripts/hf/pilot.py storage-probe
python scripts/hf/pilot.py cpu-probe
python scripts/hf/pilot.py job-status --job-id JOB_ID
python scripts/hf/pilot.py inference-probe
```

Storage writes a small synthetic JSON object, downloads it at its exact revision,
compares bytes, and verifies anonymous access is denied. It refuses public storage.
The CPU probe independently computes Euler totients through 100, asserts their
sum is 3044, and emits a digest. It uses CPU Basic, a 120-second timeout, one
attempt, no public ports, and no credentials inside the job container. Inference
uses `moonshotai/Kimi-K3:together`, a fixed synthetic prompt, 256 output tokens,
one request, and a 90-second client deadline. A client deadline cannot guarantee
that upstream inference stops; the group limit still applies.

These are infrastructure acceptance probes, not benchmarks of scientific quality.
They incur small usage charges against included credits. Do not schedule repeated
probes as a health-check loop.

## Acceptance evidence (2026-10-09)

- Private storage round trip passed at revision
  `cdc3e35ed4eec0d29acb10c7aa9e0162d04ae025`; SHA-256
  `e20dc757035005b14d336b4e381d74a82314f678e486234984f6f8877fcbcf0f`;
  unauthenticated download returned HTTP 401.
- CPU job `6ac8dfb2095c578089306030` completed, attributed to the llmxive group,
  with a 120-second timeout. It emitted sum 3044 and SHA-256
  `fc655f2213b7128a463cfb4572f9bf233733707362e1bfed3d511541b62d8892`.
- Kimi-K3 via Together returned the requested JSON through HF routing with the
  group billing header: 100 input tokens, 110 output tokens (89 reasoning).
  At the catalog rates observed that day, estimated inference cost was $0.001755;
  the final billing ledger can lag and was not used as proof of exact cost.
- The group dashboard subsequently displayed **$0.01 / $20.00** spent.
- The real repository-recovery audit (979,254 bytes) was archived and downloaded
  byte-for-byte. `pilot-storage-receipt.json` pins its HF revision, SHA-256, and
  source Git commit. This is an additional copy; source files were not deleted.
- The private working bucket is provisioned; its data round trip is not yet tested.

## Routed chat: streamed replies and deadlines

`llmxive.backends.huggingface` requests every chat as a server-sent-events stream
(`stream: true`, `stream_options: {"include_usage": true}`) and assembles it. Two
environment variables bound a call:

- `LLMXIVE_HF_DEADLINE_S` (default 360): the longest silence allowed, both before the
  first data and between data after it. Reasoning deltas count as data.
- `LLMXIVE_HF_TOTAL_DEADLINE_S` (default 1800): the longest a reply that is still
  arriving may take.

Passing either raises `DeadlineExceededError` and stops reading the stream. The token
usage comes from the stream's final chunk; when a provider leaves it out, the funded
ledger charges the call's full reservation. `capture_fixtures.py --stream` records one
short real streamed reply as `tests/fixtures/hf_funded/chat_stream_200.json`.

Evidence (2026-11-24), same long code-writing prompt, `max_tokens=30000`:
`XiaomiMiMo/MiMo-V2.5:deepinfra` without streaming answered HTTP 504 Gateway Time-out
after 120 s; with streaming it completed in 147 s with 86 input and 30,000 output
tokens reported. `zai-org/GLM-5.3-Flash:relace` streamed for 533 s (past the old 360 s
total deadline) without a timeout, but at `max_tokens=60000` it spent the whole budget
reasoning and returned no content (`finish_reason=length`, classified as reasoning
budget exhausted); without streaming at `max_tokens=30000` it did the same in 282 s.

## Funded-provider real-call lane (spec 027, Task 21)

Lane: `tests/real_call/test_hf_funded_real.py`. With Dartmouth made unreachable, each
profile picks a Hugging Face model from the live leaderboard and catalog, reserves on
the production funded ledger, makes a short real chat (`max_tokens=1024`, `retries=1`,
`max_credits=100`, i.e. at most $0.10 reserved per call), and settles the real charge. It spends real money and writes to
`refs/llmxive/funded-ledger`; it fails (never skips) when `HF_TOKEN`,
`LLMXIVE_HF_BILL_TO` or `LLMXIVE_FUNDED_LEDGER_ANCHOR` is missing. It prints model ids,
token counts, dollar amounts and counts only, never a rating, the token or the bill-to id.

Prerequisites, once: `llmxive funded-ledger-bootstrap --remote origin`; set the Actions
variables `LLMXIVE_HF_BILL_TO` and `LLMXIVE_FUNDED_LEDGER_ANCHOR`.

`refs/llmxive/funded-ledger` lies outside `refs/heads` and `refs/tags`, which is all
that GitHub branch and tag rulesets cover (not verified by a test here), so the ref
has no server-side protection. It is guarded by the code's pinned-anchor ancestry
check and compare-and-swap writes, the budget guard's cross-check against the
organization's credit balance, and the resource group's spend limit at Hugging Face.
A party with repository write access could reset the ref to an earlier point that
still descends from the anchor, and the code would accept it.

Run: `LLMXIVE_REAL_TESTS=1 pytest tests/real_call/test_hf_funded_real.py tests/real_call/test_model_selection_snapshot_real.py -q -s`

Acceptance evidence: **not yet run.** Fields to fill after the first real run (no
ratings):

- Date:
- Models served (ids) per profile:
- Input / output tokens per call:
- Total settled cost (USD):
- Leaderboard matched counts (reasoning / coding) and ambiguous names:
- `llmxive preflight` spend line and coverage line after the run:

## Next integration steps

1. Add content-addressed artifact manifests with project/run ownership, SHA-256,
   size, source URL/license, and pinned HF revision. Verify a restore before
   removing any Git-tracked bytes. Keep code, small manifests and curated fixtures
   in Git. Extend the recovered-download verifier before externalizing its blobs.
2. Use bounded HF Jobs for selected research experiments with captured logs,
   reproducible images, input manifests, output validation and per-job budgets.
3. Compare alternate HF models on captured implementation failures before allowing
   paid escalation. Do not assume a larger/newer model is better; preserve all
   scientific acceptance gates and record measured quality and cost.

These integration steps remain work under existing issues #1241, #1285 and #1139;
this pilot does not yet automatically offload production storage or computation.

Sources: [Academia benefits](https://huggingface.co/docs/hub/academia-hub),
[group caps](https://huggingface.co/docs/hub/security-resource-groups#spend-limits),
[Jobs pricing](https://huggingface.co/docs/hub/jobs-pricing),
[inference billing](https://huggingface.co/docs/inference-providers/pricing),
[buckets versus versioned repositories](https://huggingface.co/docs/hub/storage-buckets).
