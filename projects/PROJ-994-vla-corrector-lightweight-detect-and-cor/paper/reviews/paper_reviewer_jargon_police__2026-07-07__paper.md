---
action_items:
- id: c5fddfdf9206
  severity: writing
  text: "Section 3.4 (OGG Correction) introduces the symbol $\tau$ as 'denoising step'\
    \ without defining the flow-matching context or the range of $\tau$. An adjacent-field\
    \ reader may not know if $\tau \\in [0,1]$ or discrete steps. Add a brief clause:\
    \ 'where $\tau \\in [0,1]$ is the flow-matching time step'."
- id: b62732ba084b
  severity: writing
  text: 'Section 3.4 defines $\Delta Z_{\mathrm{dev}} = \Delta Z_t^{*} = Z_t^{\mathrm{real}}
    - Z_{t-k}^{\mathrm{real}}$ but uses the notation $\Delta Z_t^{*}$ (with a star)
    which was previously defined in Eq. 1 as the target residual from demonstrations.
    This overloads the symbol: in Eq. 1 it is a ground-truth target, here it is an
    observed drift. Clarify the distinction or use a distinct symbol (e.g., $\Delta
    Z_{\mathrm{obs}}$) for the observed drift to avoid confusion.'
- id: 757171a9d1ac
  severity: writing
  text: 'Section 3.3 introduces the patience parameter $p$ in Eq. 5 without defining
    its role or typical value range before the equation. While defined later in the
    appendix, the main text should briefly state: ''where $p$ is a patience threshold
    (e.g., 5 steps) to filter transient spikes''.'
- id: 67923110ad15
  severity: writing
  text: 'Section 3.1 uses the term ''flow matching'' and ''velocity field'' without
    a one-sentence gloss for readers from non-generative-model backgrounds (e.g.,
    standard RL or control). While standard in generative AI, an adjacent control
    theorist might need a brief operational definition: ''a generative process that
    learns a velocity field to transport noise to data''.'
artifact_hash: d7358417426c747fa4ca8d918e3157dfcd577dc0f92cbf50c88254f4dca67f3f
artifact_path: projects/PROJ-994-vla-corrector-lightweight-detect-and-cor/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T03:36:18.436091Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The paper is generally well-written and accessible to a competent reader in robotics or machine learning, with most acronyms (VLA, LVM, OGG) defined at first use. However, there are specific instances of notation overload and undefined symbols that could stall a reader from an adjacent field (e.g., a control theorist or a researcher in standard RL who is less familiar with flow-matching specifics).

First, in Section 3.4, the symbol $\tau$ is introduced as the "denoising step" in the context of flow matching. While standard for diffusion/flow model practitioners, the paper does not explicitly state the domain of $\tau$ (e.g., continuous $[0,1]$ or discrete steps) or the specific flow-matching formulation being used. A reader from a different subfield might struggle to map this to the velocity field update in Eq. 8. A brief parenthetical definition would resolve this.

Second, there is a potential notation collision in Section 3.4. The symbol $\Delta Z_t^{*}$ is used to denote the "accumulated deviation" ($Z_t^{\mathrm{real}} - Z_{t-k}^{\mathrm{real}}$). However, in Section 3.1 (Eq. 1), the notation $\Delta Z_{t+k}^{*}$ is explicitly defined as the *target* residual from demonstrations (ground truth). Using the same starred notation for an *observed* drift in the OGG section creates ambiguity: is this the ground truth target or the actual observed difference? The text implies the latter, but the notation suggests the former. Renaming the observed drift term (e.g., to $\Delta Z_{\mathrm{obs}}$ or $\Delta Z_{\mathrm{dev}}$) would eliminate this confusion.

Finally, the term "flow matching" and "velocity field" are used in Section 3.1 and 3.4 without a brief operational definition. While these are standard in the generative AI community, a reader from a traditional control or standard RL background might not immediately grasp that this refers to a specific generative modeling technique where a network predicts a velocity vector field. A single clarifying clause would ensure the method is self-contained for the broader robotics community.

These are minor fixes that significantly improve the self-containment of the paper for the target "adjacent-field PhD" audience.
