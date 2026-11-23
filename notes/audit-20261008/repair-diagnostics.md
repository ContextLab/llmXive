# Preserve repair diagnostics and honest inspection outcomes

Production repair run 37871553941 started 2026-10-09 01:48:37 UTC and was
cancelled at 02:23:54 UTC at its 35-minute job limit. The repair step consumed
27m59s after setup. There is no validated candidate from that run.

The upload step reported `include-hidden-files: false` and `No files were found`
for `.repair-output/`; the run's artifact list is empty. GitHub explicitly defines
files under dot-prefixed directories as hidden:
https://github.com/actions/upload-artifact#uploading-hidden-files
The workflow now explicitly includes only that evidence directory's hidden
contents, errors on missing evidence, and reserves cleanup time with a 30-minute
repair-step limit inside a 45-minute job. No credentials or environment dumps are
added to the evidence directory.

The runner now records each phase, selected files, malformed raw model responses
(with known credentials redacted), proposals before validation, and no-input
outcomes. These make timeout and parse failures diagnosable. When GPT-OSS authored
a fallback proposal, request a different free reviewer rather than knowingly
requesting the same author and rejecting its review afterwards; the actual-model
independence guard remains mandatory.

Two inspection defects are also fixed: SKIPPED calls use the supported `no-op`
record instead of an invalid failed-without-error record, and interruption is
recorded as failure before propagating. Previously either could leave an older
success in place or falsely record success for an interrupted call.

Validation: 23 repair and inspection tests pass. Two review-routing cases run
real before/after pytest subprocesses (baseline failure, candidate success); they
inject model replies and do not claim Docker or live model acceptance. Other
regressions prove raw-response redaction, durable rejection context, no-input
artifacts, stale-inspection replacement and interruption logging. Actionlint,
Ruff and diff checks pass. A new production run must verify artifact upload and a
useful independently reviewed candidate after deployment.

The state-reader CI check caught the new diagnostic files without a production
consumer. The workflow now renders them into its Actions step summary, including
an interrupted attempt's last phase and selected problem. No state-reader gate
was weakened or bypassed; the new files have an actual maintained consumer.

Repeated full CI runs also failed on single 15-second Nobel Prize source reads,
across the Kahneman, Curie and Kandel persona URLs. The evidence checker now makes
at most three attempts for timeouts, connection interruptions, rate limits and
transient 5xx responses. Permanent failures, exhausted retries and mismatched
content still fail. Nine local-HTTP source tests verify recovery and those refusal
boundaries; the citation validity policy is unchanged.
