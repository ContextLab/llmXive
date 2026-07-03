---
action_items:
- id: d27da42be80f
  severity: science
  text: The claim that 'depth recurrence... does not enable indefinite tracking' (Section
    3) overgeneralizes. While true for standard looped transformers, the paper cites
    DEQ in Table 1 as a potential candidate for the 'Depth' axis, which theoretically
    allows fixed-point iteration to simulate infinite depth. Clarify that the limitation
    applies to finite-depth recurrence, not all depth-recurrent formulations.
- id: fdce199ee901
  severity: science
  text: The assertion that 'SSMs with linear updates are no more expressive than an
    ordinary transformer' (Section 4) is followed by claims that DeltaNet and RWKV-7
    achieve 'state tracking beyond' transformers (Section 5.1). Reconcile this by
    explicitly distinguishing between linear SSMs and non-linear/gated variants to
    avoid overclaiming the limitations of the entire SSM class.
- id: 7fc546185911
  severity: writing
  text: The conclusion states that 'the next generation of foundation models must...
    maintain a fluid, evolving representation' (Section 6). This prescriptive claim
    exceeds the paper's scope, which demonstrates limitations but does not prove recurrence
    is the only path. Soften the language to 'a promising direction' rather than a
    mandatory requirement.
artifact_hash: 924b893a4650c3044c8ebca795788f41846a7a72e06ec4cbf52905fb73429333
artifact_path: projects/PROJ-746-the-topological-trouble-with-transformer/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T07:00:27.405050Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The manuscript makes several compelling arguments regarding the topological limitations of feedforward transformers for state tracking. However, the review identifies specific instances where the authors extrapolate beyond the strict bounds of their theoretical arguments or the cited literature, particularly regarding the capabilities of State-Space Models (SSMs) and the necessity of recurrence.

First, in Section 3, the authors state: "While depth recurrence can increase the expressivity of a transformer, it does not enable indefinite state tracking." This is a strong universal claim. While it holds for standard looped transformers with a fixed number of unrollings, the paper's own taxonomy in Table 1 includes "Deep Equilibrium Models (DEQ)" in the cell for Depth Recurrence with Ratio = 1. DEQs theoretically solve for a fixed point, effectively simulating infinite depth with a finite number of parameters. By categorically dismissing depth recurrence as insufficient for indefinite tracking without explicitly excluding fixed-point methods, the authors overreach their theoretical scope. The text should be refined to specify that *finite-depth* recurrence is limited, whereas fixed-point formulations may bypass this.

Second, there is a tension in the claims regarding SSMs. In Section 4, the authors assert: "State-space models (SSMs) are often touted as a means of state propagation, but SSMs with linear updates are no more expressive than an ordinary transformer." This is a precise theoretical claim supported by Merrill (2025). However, in Section 5.1 ("Enhanced State-Space Models"), the text claims that DeltaNet and RWKV-7 "achieve state tracking beyond the capability of ordinary transformers." While these models are indeed more expressive, the transition from the general dismissal of SSMs to the specific praise of gated/non-linear variants is abrupt. The manuscript risks overclaiming the limitations of the *entire* SSM class by initially grouping them with linear models, then later highlighting non-linear variants as exceptions without a clear demarcation in the initial critique. The distinction between linear and non-linear/gated SSMs must be sharper to avoid misleading the reader about the expressivity of the broader class.

Finally, the conclusion (Section 6) makes a prescriptive claim: "The next generation of foundation models must... maintain a fluid, evolving representation of reality." This implies that recurrence is the *only* viable path forward. While the paper argues strongly for recurrence, it does not rule out other potential architectural evolutions (e.g., hybrid retrieval mechanisms, dynamic context windows, or novel attention mechanisms) that might solve state tracking without explicit recurrence. The language should be adjusted to reflect that recurrence is a *promising* and *theoretically sound* direction, rather than a mandatory requirement for the future of foundation models.

These issues represent overreach in the scope of the claims rather than fundamental flaws in the core argument. Addressing them will ensure the paper's conclusions are strictly supported by the presented evidence and citations.
