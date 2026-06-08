---
action_items:
- id: d5e18ca66548
  severity: writing
  text: Add explicit discussion on safety/refusal testing for high-risk tasks (e.g.,
    payments in Table 12). Currently, capability is measured without assessing if
    agents refuse harmful instructions, creating a dual-use risk.
- id: 83cb595764af
  severity: writing
  text: "Disclose IRB approval or compensation details for human annotators involved\
    \ in the manual audit of 118 real-device trajectories (Appendix \xA7\ref{app:vlm-audit}).\
    \ Human labor ethics compliance is missing."
- id: ffdcb84ec84c
  severity: writing
  text: "Expand the 'Broader Uses' or Discussion section to address safeguards for\
    \ deploying trained agents on real devices, given the 95.1% Sim-to-Real transfer\
    \ of policy gains (\xA7\ref{sec:exp:sim2real})."
artifact_hash: a548124f155c8c790b0f8380f840762b6a4c9bd7b88cafb98ce50a865152c78b
artifact_path: projects/PROJ-633-mobilegym-a-verifiable-and-highly-parall/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-08T00:53:33.996056Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The MobileGym platform effectively mitigates immediate physical harm through its sandboxed, consequence-free simulation environment, allowing safe training of agents on high-stakes tasks like financial transfers. However, several safety and ethics concerns require attention before publication.

First, the benchmark includes a **High-Risk subset** (Appendix Table 12) covering payments and account modifications, yet explicitly states: "it differs from a safety evaluation that tests refusal of harmful or inappropriate instructions." Measuring the *capability* to perform irreversible financial operations without assessing *refusal* lowers the barrier for developing agents that could execute fraud or unauthorized transactions. The authors must add a dedicated discussion on responsible release, potential misuse scenarios, and why refusal testing was omitted or how it should be integrated in future work.

Second, the **Sim-to-Real transfer** results (§\ref{sec:exp:sim2real}) demonstrate that policies trained in the sandbox transfer effectively to real devices (95.1% retained gain). While this validates the platform, it implies that agents trained to bypass safety constraints in simulation could harm real users. The paper should discuss safeguards for deploying such agents, such as mandatory human-in-the-loop verification for high-consequence actions.

Third, the **human labor ethics** regarding the manual audit of real-device trajectories are unclear. Appendix §\ref{app:vlm-audit} describes a "manual review of all 118 signal-bucket real-device trajectories." Standard ethical practice requires disclosure of whether these annotators were compensated and whether the study received IRB/ethics approval. This information must be added to the manuscript.

Finally, while the data is synthetic, the platform's ability to train agents on realistic everyday apps (e.g., WeChat, Alipay) carries dual-use risks. The authors should acknowledge this and consider adding safety guidelines to the project repository alongside the code. These additions will ensure the work aligns with community standards for AI safety and research ethics.
