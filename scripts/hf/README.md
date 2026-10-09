# Hugging Face pilot

The `contextlab` Academia subscription supplies optional storage and burst compute
for llmXive. Dartmouth remains the production model backend. These explicit pilot
commands do not change automatic model selection or upload project directories.

## Provisioned resources

- Organization: `contextlab` (Academia plan verified 2026-10-09).
- Resource group: `llmxive`, ID `6ac8defed831a06784773cfd`.
- Monthly combined compute cap: **$20**; Jobs and Inference Providers share it.
- Paid Spaces and Inference Endpoints: **$0** limits.
- Private versioned artifacts: <https://huggingface.co/datasets/contextlab/llmxive-artifacts>.
- Private working bucket: <https://huggingface.co/buckets/contextlab/llmxive-work>.
- Group settings: <https://huggingface.co/organizations/contextlab/settings/resource-groups/6ac8defed831a06784773cfd?tab=settings>.

Credits are pooled across the organization, not separate wallets attached to ten
bot accounts. The $20 cap represents ten seats' monthly allocation. It does not
reserve credits against other lab usage, and is not an additional subscription.
HF enforces the group limit; jobs must specify this group and inference requests
must use its ID in `X-HF-Bill-To`. HF may stop running work shortly after a limit
is reached, so this is not a promise of zero overshoot.

## Credentials

Never commit credentials, put them in a command-line argument, log them, or use a
credential-bearing URL. The helper reads only `HF_TOKEN` (for a GitHub Actions
secret) or the macOS Keychain service `llmxive-huggingface`, account
`jeremyrmanning`. It does not read a plaintext HF cache or repository `.env` file.
The current local credential is in Keychain. **No HF GitHub secret or recurring
HF workflow has been enabled.** Before enabling CI, create a dedicated fine-grained
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
- The private working bucket is provisioned; its data round trip is not yet tested.

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
