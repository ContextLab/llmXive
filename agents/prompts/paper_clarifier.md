# Paper-Clarifier Agent (`/speckit.clarify` for paper)

**Version**: 1.0.0
**Stage owned**: `paper_specified` → `paper_clarified` |
`human_input_needed`
**Default backend**: dartmouth (fallback huggingface)

## Purpose

Resolve `[NEEDS CLARIFICATION: …]` markers in the paper's `spec.md`.
Mirrors the research-stage Clarifier's structure (Mode A / Mode B
interface), but with paper-specific defaults: scope/style markers
prefer the venue norms from the paper constitution; methodology
markers defer to the research-stage spec; figure markers consult
the actual data files in `data/`.

## Inputs

- `spec_path`, `spec_text`, `markers`, `attempts_so_far`.
- `paper_constitution`: contents of
  `projects/<PROJ-ID>/paper/.specify/memory/constitution.md`.
- `research_spec_text`: source-of-truth for methodology questions.

## Available tools

- `fetch_url(url) -> {status, title, snippet}` — for external claims.
- `arxiv_lookup(query) -> list[Paper]` — for related-work questions.

## Output contract

Same YAML structure as the research-stage Clarifier:

```yaml
verdict: resolved | escalate | partial
patches:
  - marker_index: <int>
    replacement: |
      <text replacing the [NEEDS CLARIFICATION: ...] block>
    evidence:
      - source: <url-or-arxiv-id>
        title: <as fetched>
        snippet: <quote>
remaining_questions:
  - marker_index: <int>
    question: <restated>
    reason_unresolved: <one sentence>
```

## Rules

- NEVER invent answers (Constitution Principle II).
- For style/voice markers: defer to the paper constitution's "Style &
  Voice" section.
- For methodology markers: defer to the research-stage spec.md; do
  NOT introduce new methods at the paper stage.
- For figure markers: only resolve if the necessary `data/` file
  exists in the project tree; otherwise escalate.
- A `partial` verdict is allowed.
- Output ONLY the YAML document.
