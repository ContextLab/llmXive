# Reject unreadable YAML completion evidence

At 07:02 UTC on 2026-10-09, the fresh isolated canary had a matching positive T014 verifier receipt for a checksum manifest containing literal `\n` characters instead of actual newlines. PyYAML raises `ScannerError: mapping values are not allowed here`; the persisted semantic verdict nevertheless said it contained all expected hashes. Task evidence validation parsed JSON but treated YAML as arbitrary nonempty text.

The same bounded validation now loads YAML/YML with the safe reader, rejecting malformed or comment-only files before semantic review or receipt reuse. Valid YAML, multi-document YAML and quoted literal backslashes retain support. This is a readability gate, not proof that a manifest's hashes or scientific results are correct. Oversized documents still require semantic review rather than unbounded parsing.

All 49 relevant checks pass. Six regressions fail on the previous implementation, including reuse of an old positive receipt. The read-only probe in `yaml-artifact-live.json` rejects the actual manifest and excludes T014 from verified completion without changing any scientific artifact/task/state. Running canaries have not yet loaded this fix.
