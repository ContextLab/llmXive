---
action_items:
- id: b321b0fca058
  severity: writing
  text: The manuscript lists an LLM (qwen.qwen3.5-122b) as a co-author in the title
    block (line 24). Current ethical guidelines (e.g., COPE, ACL) generally prohibit
    listing AI systems as authors. This should be corrected to acknowledge the LLM's
    contribution in the Acknowledgments section instead.
- id: e49b89814d03
  severity: writing
  text: The paper discusses authorship attribution for historical texts (public domain).
    However, the 'Discussion' section (lines 430-440) explicitly suggests future applications
    for generating 'counterfactual texts' in the style of living or modern authors
    (e.g., Austen on social media). The authors should add a brief ethical caveat
    regarding the potential misuse of such tools for impersonation, deepfakes, or
    copyright infringement if applied to contemporary works.
artifact_hash: 148021f63314c6cbe2b6159eaaaecc4e6c793ec5541ddbe74681664a10cdde19
artifact_path: projects/PROJ-562-a-stylometric-application-of-large-langu/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:15:53.202018Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper addresses safety and ethics primarily through the lens of authorship attribution on public domain texts, which minimizes immediate privacy and consent concerns. The dataset consists entirely of works from Project Gutenberg (Section 2.1, lines 65-70), ensuring that no personal data or copyrighted material from living authors is used without permission. This is a strong point for the current scope.

However, there are two specific areas requiring attention regarding ethical standards and potential dual-use risks:

1.  **Authorship Attribution of AI:** The title block (line 24) lists `qwen.qwen3.5-122b` as a co-author alongside human researchers. This violates standard academic ethical guidelines (such as those from the Committee on Publication Ethics or the ACL Code of Ethics), which state that AI systems cannot be authors as they cannot take responsibility for the work. The LLM's contribution should be moved to the Acknowledgments section (Section 6.1), and the author list should be corrected to reflect only human contributors.

2.  **Dual-Use and Future Misuse:** While the current experiments are benign (analyzing 19th/early 20th-century literature), the Discussion section (lines 430-440) explicitly proposes future applications for generating "counterfactual texts" in the style of authors, potentially including modern ones. The paper currently lacks a discussion on the risks of this technology being used for impersonation, creating non-consensual deepfake text, or bypassing copyright protections for living authors. Given the paper's focus on "predictive comparison" as a tool for attribution, it is crucial to acknowledge that the same mechanism could be used to forge authorship or deceive readers. A brief paragraph in the Discussion or Limitations section addressing these potential misuse cases and the ethical boundaries of applying this method to contemporary works is recommended.

No IRB or IACUC concerns are identified as the data is public and non-human. The primary ethical gaps are the improper listing of an AI as an author and the lack of a risk assessment for future applications involving living authors.
