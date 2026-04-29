# Paper-Initializer Agent

**Version**: 1.0.0
**Stage owned**: `research_accepted` → `paper_drafting_init`
**Default backend**: dartmouth (fallback huggingface, then local)

## Purpose

Bootstrap the paper-stage Spec Kit scaffold under
`projects/<PROJ-ID>/paper/`. Mechanically:

1. Create `projects/<PROJ-ID>/paper/.specify/{scripts,templates,memory}/`
   from the upstream Spec Kit skeleton (the runtime calls
   `speckit.runner.init_speckit_in()` against `paper/`).
2. Render the project-specific paper-stage constitution from
   `agents/templates/paper_project_constitution.md` with token
   substitution per FIX U3 (`{{project_id}}`, `{{title}}`,
   `{{field}}`, `{{date}}`).

The LLM portion adapts the rendered constitution to the project's
domain — the same way the Project-Initializer adapts the research-
stage constitution. Most projects will want minor additions (e.g.,
"Statistical Reporting Discipline" for empirical projects, "Code
Listings" for software projects).

## Inputs

- `project_id`, `title`, `field`, `date` (ISO-8601 UTC).
- `research_summary`: contents of the project's `specs/<feature>/spec.md`
  (the research that this paper will report on).

## Output contract

A Markdown document containing the rendered paper constitution. The
runtime substitutes `{{project_id}}`, `{{title}}`, `{{field}}`,
`{{date}}` BEFORE the LLM sees it. The model's job is to:

1. Adapt the "Core Principles" to the specific paper domain (add at
   most TWO domain-specific principles).
2. Tighten the "Style & Voice" section to match the paper's
   target venue style (e.g., concise for ML/AI venues, narrative for
   psychology venues).
3. Keep every other section verbatim.

The output MUST start with the literal heading
`# <title> — Paper Project Constitution` and MUST end with the
literal `**Project ID**: …` footer line.

## Rules

- Add at most TWO domain-specific principles.
- DO NOT remove any of the inherited principles (I-VI from the
  template).
- DO NOT introduce external citations here — the constitution is
  governance, not research.
- Output ONLY the Markdown document.
