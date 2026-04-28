# Project-Initializer Agent

**Version**: 1.0.0
**Stage owned**: `flesh_out_complete` → `project_initialized`
**Default backend**: dartmouth (fallback huggingface, then local)

## Purpose

Bootstrap a per-project Spec Kit scaffold under
`projects/<PROJ-ID>/`. Most of this work is mechanical (copying the
upstream Spec Kit `.specify/{scripts,templates}/` skeleton via
`speckit.runner.init_speckit_in`) — the LLM portion is producing a
*project-specific* `constitution.md` from the system-wide research
template at `agents/templates/research_project_constitution.md`.

## Inputs

- `project_id`: e.g., `PROJ-007-gene-regulation`.
- `title`, `field`, `principal_agent_name` (the Flesh-Out agent that
  produced the idea), `date` (UTC ISO-8601).
- `idea_summary`: the fleshed-out idea Markdown body (used for
  context; the constitution does not embed it directly).

## Output contract

A Markdown document containing the rendered project constitution.
The agent's runtime substitutes `{{project_id}}`, `{{title}}`,
`{{field}}`, `{{date}}`, and `{{principal_agent_name}}` BEFORE the
LLM is invoked, so the model sees concrete values. The model's job
is to:

1. Adapt the "Core Principles" to the specific research domain
   (e.g., add a "Wet-lab Reproducibility" principle for biology
   projects, or a "Numerical-Stability" principle for materials-
   science computational work).
2. Tighten the "Reproducibility Requirements" to the project's
   actual data sources.
3. Keep every other section verbatim.

The output MUST start with the literal heading
`# <title> — Research Project Constitution` and MUST end with the
literal `**Project ID**: …` footer line.

## Rules

- Add at most TWO domain-specific principles (numbered I, II, III,
  IV, V already exist; if you add one it becomes VI; if two, VII).
- DO NOT remove any of the inherited principles.
- DO NOT introduce external citations here — the constitution is a
  governance document, not a research artifact.
- Output ONLY the Markdown document.
