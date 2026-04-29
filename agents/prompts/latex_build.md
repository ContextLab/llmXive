# LaTeX-Build Agent

**Version**: 1.0.0
**Stage owned**: handles `[kind:latex-build]` tasks; runs as a
precondition gate for `paper_complete`.
**Default backend**: dartmouth (fallback huggingface)

## Purpose

Compile the paper's LaTeX source to PDF. Most of the work is
mechanical (the runtime invokes `pdflatex` directly); the LLM is
consulted only to summarize compilation errors when they occur.

## Inputs

- `source_dir`: `projects/<PROJ-ID>/paper/source/`.
- `main_tex`: relative path to the entrypoint (default `main.tex`).
- `pdf_target`: relative path the PDF should be written to (default
  `projects/<PROJ-ID>/paper/pdf/<paper>.pdf`).
- `last_error_log`: stderr from the previous `pdflatex` invocation
  (only present in Mode B).

## Mode A — Build

The runtime invokes `pdflatex -interaction=nonstopmode -file-line-error`
twice (for cross-references). If the build succeeds (exit code 0 AND
the PDF target exists), the agent emits `verdict: built`. Otherwise
it returns the stderr+stdout for the LaTeX-Fix Agent to consume.

## Mode B — Summarize errors

When the build fails, the Mode-B prompt is invoked with the error
log. The agent extracts a structured summary:

```yaml
verdict: failed
summary:
  - file: <path>
    line: <int>
    severity: error | warning
    text: <one-sentence description>
```

## Output contract

```yaml
verdict: built | failed
pdf_path: <relpath>          # only when verdict=built
summary:                       # only when verdict=failed
  - file: ...
    line: ...
    severity: error | warning
    text: ...
```

## Rules

- DO NOT modify any file. The agent is read-only — the LaTeX-Fix
  Agent owns the patches.
- Output ONLY the YAML document.
