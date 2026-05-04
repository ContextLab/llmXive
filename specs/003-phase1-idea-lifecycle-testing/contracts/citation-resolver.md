# Contract: Citation Resolver

**Implementation**: `tests/phase1/citation_resolver.py`
**Schema source**: data-model.md Entity 7 (Citation), Entity 8 (Resolution result)
**Spec reference**: FR-010, SC-005

## Purpose

Stage 1 of the two-stage citation-verification pipeline. Mechanically resolves
citations in `projects/<id>/idea/<slug>.md` via HTTP HEAD, DOI lookup, and
arXiv API. Emits one `ResolutionResult` per citation. Citations whose Stage 1
result is `ambiguous` get handed off to Stage 2 (agent verifier — separate
contract).

## CLI signature

```bash
python tests/phase1/citation_resolver.py <idea_md_path> [--timeout SECONDS] [--self-test]
```

**Required positional arg**:
- `idea_md_path` — path to `idea/<slug>.md` (any project, any sibling).

**Optional flags**:
- `--timeout SECONDS` — per-citation hard timeout. Default: 60.
- `--self-test` — run the built-in test against one known-good citation (`https://arxiv.org/abs/1706.03762`) and one known-bad citation (`https://example.invalid/this-does-not-exist`). Exit 0 if both behave as expected; non-zero otherwise. Skips reading any input file.

## Stdout output

JSON array of `ResolutionResult` records (one per citation found in the input file). Pretty-printed with 2-space indent. Example:

```json
[
  {
    "citation": {
      "raw_text": "[Attention Is All You Need (2017)](https://arxiv.org/abs/1706.03762)",
      "kind": "arxiv",
      "identifier": "1706.03762",
      "line_number": 14
    },
    "stage1_status": "resolved",
    "stage1_evidence": {
      "url_checked": "http://export.arxiv.org/api/query?id_list=1706.03762",
      "http_status": 200,
      "redirect_chain": [],
      "api_response_snippet": "<entry><title>Attention Is All You Need</title>..."
    },
    "stage2_status": null,
    "stage2_evidence": null,
    "final_verdict": "verified",
    "timestamp": "2026-05-04T12:34:56Z"
  },
  {
    "citation": {
      "raw_text": "[Made-up Paper (2026)](https://example.invalid/never-existed)",
      "kind": "url",
      "identifier": "https://example.invalid/never-existed",
      "line_number": 17
    },
    "stage1_status": "unreachable",
    "stage1_evidence": {
      "url_checked": "https://example.invalid/never-existed",
      "http_status": null,
      "redirect_chain": [],
      "api_response_snippet": null
    },
    "stage2_status": null,
    "stage2_evidence": null,
    "final_verdict": "failed",
    "timestamp": "2026-05-04T12:34:57Z"
  }
]
```

## Stderr output

Progress lines (one per citation), e.g.:

```text
[1/5] arxiv 2410.16349v1 → resolved
[2/5] doi  10.1016/j.ijinfomgt.2023.102642 → resolved
[3/5] url  https://example.invalid/foo → unreachable
[4/5] arxiv 2211.09374v1 → resolved
[5/5] arxiv 2303.12869v1 → ambiguous (multiple matches in arXiv)
```

## Exit codes

- `0` — script ran cleanly. Per-citation results are in stdout JSON; some may have `final_verdict: failed` — that's a citation issue, NOT a script issue.
- `1` — script-level error: input file not found, file unreadable, no citations parsed (regex extraction returned 0).
- `2` — `--self-test` failed: the known-good URL did not resolve as expected, or the known-bad URL spuriously resolved.
- `64` — invalid CLI arguments.

## Citation extraction rules

Parse `idea_md_path` line-by-line; extract citations matching these patterns (in priority order):

1. **arXiv markdown link**: `\[([^\]]+)\]\(https?://arxiv\.org/abs/(\d{4}\.\d{4,5}(?:v\d+)?)\)` — kind = `arxiv`, identifier = the version-stripped ID (`v\d+` removed if present).
2. **DOI markdown link**: `\[([^\]]+)\]\(https?://(?:dx\.)?doi\.org/(10\.\d{4,9}/[^\s)]+)\)` — kind = `doi`, identifier = the DOI itself.
3. **Other URL markdown link**: `\[([^\]]+)\]\((https?://[^\s)]+)\)` — kind = `url`, identifier = the URL.
4. **Inline raw URL** (only inside a `## Related work` or `## References` section): `\bhttps?://[^\s)]+\b` — kind = `inline_url`, identifier = the URL.

Citations matching pattern 1 or 2 take precedence over pattern 3 for the same line.

## Resolution rules per kind

- **arxiv**: GET `http://export.arxiv.org/api/query?id_list=<id>` (no version suffix). If HTTP 200 AND response body contains exactly one `<entry>` tag, status = `resolved`. If multiple `<entry>` tags or 200 with empty result, status = `ambiguous`. Anything else, status = `unreachable`.
- **doi**: HTTP HEAD on `https://doi.org/<doi>` with redirect-following enabled (max 5 redirects). If final status is 2xx, `resolved`. If 4xx, `unreachable`. If 3xx final or redirect-loop, `ambiguous`.
- **url** / **inline_url**: HTTP HEAD on the URL with redirect-following (max 5). If final status is 2xx, `resolved`. If 4xx or DNS failure, `unreachable`. If 3xx final, `ambiguous`. If a 405 Method Not Allowed comes back (some servers refuse HEAD), retry with GET and the first 2 KB only — count as `resolved` if 200.

## Per-citation timeout

Hard wall-clock cap per citation = `--timeout` seconds (default 60). Implementation MUST use a thread-pool with `Future.result(timeout=N)` (NOT requests' built-in timeout, which doesn't always plumb through to the underlying socket — pattern from `src/llmxive/backends/dartmouth.py`).

If timeout fires: `stage1_status = "unreachable"`, `stage1_evidence.http_status = null`, `stage1_evidence.redirect_chain = []`, `stage1_evidence.api_response_snippet = null`. Continue to next citation.

## Network discipline

- HTTPS only (HTTP downgraded to HTTPS where the URL allows; raw-HTTP URLs are kept as-is and a warning is printed to stderr).
- User-Agent: `llmxive-citation-resolver/1.0 (https://github.com/ContextLab/llmXive)`.
- No retries on transient failures — one shot per citation. (Diagnostic re-runs handle re-resolution.)
- No request bodies; HEAD only (with the GET fallback exception for 405).

## Self-test specification

When `--self-test` is given, the resolver:

1. Constructs an in-memory citation list:
   - Citation A: `arxiv` kind, identifier `1706.03762`. EXPECTED `resolved`.
   - Citation B: `url` kind, identifier `https://example.invalid/never-existed`. EXPECTED `unreachable`.
2. Runs each through the same resolution path used for real input.
3. Prints `[self-test] A: <status>; B: <status>` to stderr.
4. Exit 0 if A == `resolved` and B == `unreachable`; exit 2 otherwise.

## Out of scope

- Stage 2 (agent verifier) is a separate contract; this resolver does NOT call any LLM. Citations whose Stage 1 result is `ambiguous` are flagged for Stage 2 in the JSON output, not actively handed off.
- BibTeX-format citations are NOT supported (none observed in repo per research.md Decision 6). If they appear in future, extend pattern list 1-4.
- Modifying `idea/<slug>.md` is forbidden — the resolver is read-only.
