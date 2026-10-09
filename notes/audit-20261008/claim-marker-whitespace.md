# Claim marker cleanup corrupted runnable examples (2026-10-09)

The canary preview at 05:16 UTC failed on `--output-dir./example_output`. Its previously generated runbook used `--output-dir ./example_output`. `strip_claim_artifacts` removed a stale marker anywhere in a document and then collapsed whitespace/punctuation spacing over the entire document, including fenced command lines and Python examples. This also damaged indentation and aligned tables. The no-marker fast path did not protect documents containing a marker on another line.

Cleanup now removes each marker/pointer and joins only whitespace adjacent to that removal. It preserves all unrelated bytes and keeps a separator before relative paths. No claim is automatically accepted and no generated research document is manually fixed.

68 focused tests pass. Five new regressions fail against the old implementation: two actual argparse command examples (marker and pointer), Python indentation/alignment, an inline command on a marker line, and a newly adjacent relative path. The CLI tests execute the extracted command on a real Python subprocess after cleanup. Full scientific acceptance remains pending.
