---
action_items:
- id: 28dd6906245d
  severity: writing
  text: "Replace all non\u2011standard heading commands such as `\\subsubsubsection`\
    \ with supported LaTeX levels (`\\paragraph` or `\\subparagraph`) or define a\
    \ custom hierarchy, and ensure a consistent depth order (section \u2192 subsection\
    \ \u2192 subsubsection \u2192 paragraph)."
- id: a695d5ddc506
  severity: writing
  text: "Remove the duplicated \u201CIntroduction\u201D and \u201CCase Study\u201D\
    \ sections that appear both before and after the appendix; consolidate content\
    \ to a single occurrence to avoid confusion."
- id: 9ef8ae89d921
  severity: writing
  text: "Ensure each figure has a unique label; the teaser figure is labeled `\\label{fig:teaser}`\
    \ twice, which will cause cross\u2011reference collisions. Rename one of them\
    \ (e.g., `fig:teaser_alt`)."
- id: b7b89740e087
  severity: writing
  text: "After `\\appendix`, use proper sectioning commands (`\\section{Appendix}`\
    \ or `\\section*{Appendix}`) before lower\u2011level headings, rather than starting\
    \ directly with `\\subsubsubsection`."
- id: a4cdeb79aa26
  severity: writing
  text: Verify that all tables include a `\centering` directive (some tables rely
    on the surrounding `\begin{center}` environment, which is deprecated) and that
    column specifications match the number of columns to avoid compilation warnings.
- id: 7f9ef3786f7f
  severity: writing
  text: 'Standardize citation formatting: multiple citations should be grouped with
    a single `\cite{...}` command (e.g., `\cite{ref1,ref2,ref3}`) and ensure a consistent
    bibliography style throughout the document.'
- id: 7ca942b03bcd
  severity: writing
  text: Check line wrapping in the source file to keep lines under 80 characters where
    possible; long lines in tables and figure captions can hinder readability and
    version control diffs.
artifact_hash: 5db0f3878ddf869f97ae5b85f5c21e6bee16133e4d0bee899b71eabf9aaf1f3a
artifact_path: projects/PROJ-692-kwai-keye-vl-2-0-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T09:53:40.221363Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_text_formatting
score: 0.0
verdict: minor_revision
---

The manuscript follows a conventional LaTeX structure, but several formatting issues affect readability and could cause compilation problems.

**Heading hierarchy** – The document uses `\subsubsubsection`, which is not a standard LaTeX command. Replace these with supported levels such as `\paragraph` or `\subparagraph`, or define a custom command if deeper nesting is required. Ensure a monotonic hierarchy (section → subsection → subsubsection → paragraph).

**Duplicate sections** – “Introduction” and “Case Study” appear both before and after the appendix, creating redundancy and confusing navigation. Consolidate each duplicated section into a single location.

**Figure labels** – The teaser figure is defined twice with the same label `\label{fig:teaser}`. Duplicate labels cause ambiguous cross‑references. Assign distinct labels (e.g., `fig:teaser_alt`) and update any `\ref` calls.

**Appendix heading** – The appendix begins directly with `\subsubsubsection` after `\appendix`. Proper practice is to introduce the appendix with a top‑level heading (`\section{Appendix}` or `\section*{Appendix}`) before any lower‑level headings, which also resolves the heading‑level issue.

**Table formatting** – Some tables are wrapped in an outer `\begin{center}` environment rather than using the modern `\centering` command inside the table environment. Switch to `\centering` for consistency and avoid deprecated environments. Also verify that column specifications (`{l c c}` etc.) match the actual number of columns to prevent alignment warnings.

**Citation style** – Multiple references are sometimes split across separate `\cite` commands. Group them into a single `\cite{ref1,ref2}` to improve readability and adhere to typical bibliography conventions.

**Line length** – Several source lines, especially in table rows and figure captions, exceed 80 characters. Wrapping these lines enhances version‑control diffs and overall maintainability.

Addressing the items above will bring the manuscript into line with standard LaTeX hygiene, eliminate compilation warnings, and improve the document’s structural clarity.
