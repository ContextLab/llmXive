---
action_items:
- id: a4a00151fd0c
  severity: writing
  text: Section 2.1 (Eq. 1) introduces the symbol $\mathcal{B}_d$ in the phrase 'Given
    a domain $\mathcal{B}_d$' without defining it. The subsequent definition of $\mathcal{G}_d$
    uses $\mathcal{C}_d, \mathcal{A}_d, \mathcal{O}_d, \mathcal{V}_d$ but never explicitly
    states what $\mathcal{B}_d$ represents (e.g., 'the set of tasks in domain d' or
    'the domain label'). Define $\mathcal{B}_d$ at first use.
- id: aac8660a00fc
  severity: writing
  text: "Section 2.2 (Eq. 2) introduces the symbol $\bot$ in the trajectory definition\
    \ ($v_t \\in \\mathcal{V}_q \\cup \\{\bot\\}$) without a textual explanation.\
    \ While common in logic, in this context it is unclear if it means 'no verifier\
    \ fired', 'verification failed', or 'undefined'. Add a brief clause: 'where $\b\
    ot$ denotes the absence of a triggered verifier'."
- id: bc0018efeb5b
  severity: writing
  text: Section 2.3 introduces 'SVA' (Salient Vocabulary Alignment) and 'OPD' (On-Policy
    Distillation) as acronyms. While 'OPD' is defined in the section title, 'SVA'
    is only introduced as a phrase in the text without the acronym expansion in parentheses
    at first use (e.g., 'salient vocabulary alignment (SVA)'). Ensure both are explicitly
    expanded at first occurrence in the body text.
- id: 0e8bc70f6cc6
  severity: writing
  text: Section 3.1 (Eq. 10) uses the symbol $\lambda_{\mathrm{neg}}$ in the advantage
    equation without defining its value or role in the text preceding the equation.
    The text mentions 'asymmetric design' but does not explicitly state that $\lambda_{\mathrm{neg}}$
    is a weighting coefficient for the process reward on negative samples. Define
    $\lambda_{\mathrm{neg}}$ where it first appears.
artifact_hash: 7516b8f83d13246ad4b3942c0933109bd30bd10fff09ade393f2aa0326228eae
artifact_path: projects/PROJ-806-scaling-the-horizon-not-the-parameters-r/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T01:30:58.893329Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The paper is generally well-written for a technical audience, but there are a few instances where notation and acronyms are introduced without sufficient definition for a competent reader from an adjacent field (e.g., a researcher in NLP reading a systems paper, or vice versa).

Specifically, in Section 2.1, the symbol $\mathcal{B}_d$ appears in the definition of the Knowledge-Action Graph ("Given a domain $\mathcal{B}_d$") but is never explicitly defined as a set, a label, or a specific entity type. The reader is left to infer its meaning from context, which breaks the self-contained nature of the definition. Similarly, in Section 2.2, the symbol $\bot$ is used in the trajectory equation to represent a state where no verifier fires, but this convention is not explained in the prose, forcing the reader to guess the semantic meaning of the symbol.

Additionally, the acronym "SVA" (Salient Vocabulary Alignment) is used frequently in Section 2.3 but is not explicitly expanded with the acronym in parentheses at its very first mention in the main text (it appears in the section title and later in the text, but the immediate expansion is missing in the introductory sentence of the subsection). While "OPD" is clearer, ensuring all custom acronyms are expanded at first use is a standard requirement for accessibility. Finally, in Section 3.1, the hyperparameter $\lambda_{\mathrm{neg}}$ is introduced in an equation without a preceding textual definition of what it controls, which is a minor but notable omission for reproducibility and clarity.

These issues are easily fixable with one-sentence additions or parenthetical expansions and do not detract from the core scientific contribution, but they do create small friction points for the "adjacent-field PhD" reader.
