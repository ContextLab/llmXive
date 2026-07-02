---
action_items:
- id: 008387b118ad
  severity: writing
  text: Define 'MoT' (Mixture-of-Transformers) at first use in Section 3.3. The acronym
    appears without expansion, assuming reader familiarity with the BAGEL paper's
    specific terminology.
- id: da1c23cf0bf6
  severity: writing
  text: Replace 'w.r.t.' with 'with respect to' in the shim layer (line 48) and ensure
    no other instances of this abbreviation appear in the main text, as it is non-standard
    in formal prose.
- id: 43879ea5893b
  severity: writing
  text: Define 'EMA' (Exponential Moving Average) at first use in Section 3.1. While
    common in ML, the paper targets a broader audience and should explicitly state
    the term before using the acronym.
- id: e7d07f69d5fe
  severity: writing
  text: Replace 'x-prediction' with 'velocity prediction' or 'predicting the clean
    signal x' in Section 3.2. The notation 'x-prediction' is internal jargon specific
    to certain diffusion literature and may confuse readers unfamiliar with the specific
    flow-matching formulation.
artifact_hash: 0bf0beeeed30c8d210e5c1e3aba1eedb5ce01456059a286e2a46cd55dbe05f56
artifact_path: projects/PROJ-648-representation-forcing-for-bottleneck-fr/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T11:36:54.209223Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript generally avoids excessive jargon, but several instances of field-specific abbreviations and shorthand remain undefined or could be clarified for a broader audience.

First, the acronym **MoT** (Mixture-of-Transformers) is introduced in Section 3.3 ("Our model adopts the Mixture-of-Transformers (MoT) architecture...") but the expansion is provided only in the context of the BAGEL citation. While the expansion is present, the acronym is then used immediately. It is safer to ensure the full term is clearly established before relying on the acronym, or to spell it out every time if the acronym is not used frequently.

Second, **EMA** (Exponential Moving Average) is used in Section 3.1 ("...extract features from an exponential moving average (EMA) copy..."). The expansion is provided here, which is good practice. However, in the Appendix (Implementation Details), the term "EMA model" is used without re-expansion. While acceptable if defined earlier, consistency is key.

Third, the term **x-prediction** appears in Section 3.2 and the Appendix. This is specific jargon from the diffusion literature (referring to predicting the clean data $\mathbf{x}$ rather than noise $\epsilon$ or velocity $\mathbf{v}$). For a general multimodal audience, this should be clarified as "predicting the clean signal $\mathbf{x}$" or "velocity prediction" to avoid confusion with standard autoregressive "next-token" prediction.

Finally, the shim layer in the LaTeX source (line 48) defines `\wrt` as `w.r.t.`. While this is a LaTeX macro, the resulting text "w.r.t." appears in the compiled document if used. The paper should avoid "w.r.t." in favor of "with respect to" to maintain a formal tone and reduce jargon density.

These are minor issues but align with the goal of making the paper accessible to non-specialists.
