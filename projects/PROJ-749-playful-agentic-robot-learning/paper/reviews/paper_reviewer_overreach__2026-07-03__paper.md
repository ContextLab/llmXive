---
action_items:
- id: 0f25f10bac9f
  severity: writing
  text: The paper makes several claims regarding the autonomy and generalization of
    the \textsc{RATs} system that appear to exceed the evidence provided in the text.
    First, the Abstract and Section 5.3 claim that skills transfer to real-world tasks
    "without finetuning." While the authors state they do not finetune the LLM, the
    claim implies a level of zero-shot generalization that is not fully supported.
    The real-world evaluation (Table 3) shows modest gains (+8.8 pp), but the paper
    does not clarify if
artifact_hash: 50abfa42bd37b77889e3563a6ea1bdb0e8be3fa0ecf45caffb5d23cfc888d2a4
artifact_path: projects/PROJ-749-playful-agentic-robot-learning/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T18:57:51.374478Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims regarding the autonomy and generalization of the \textsc{RATs} system that appear to exceed the evidence provided in the text.

First, the Abstract and Section 5.3 claim that skills transfer to real-world tasks "without finetuning." While the authors state they do not finetune the LLM, the claim implies a level of zero-shot generalization that is not fully supported. The real-world evaluation (Table 3) shows modest gains (+8.8 pp), but the paper does not clarify if the low-level primitives (e.g., grasp controllers, inverse kinematics) used by the generated code were also frozen or if they required environment-specific tuning. If the primitives were tuned for the real robot, the claim of "without finetuning" is misleading regarding the *system's* ability to transfer, as the transfer relies on pre-tuned components. The distinction between "no LLM finetuning" and "no system finetuning" must be precise.

Second, the characterization of the learning process as "self-directed play" (Abstract, Introduction) overstates the autonomy of the Task Proposer. The Appendix (Sec. Appendix Prompt Templates) reveals that the Task Proposer is explicitly conditioned on "KNOWN ENV LIMITATIONS" and "PICK-PRIMITIVE RELIABILITY" lists. This indicates that the "play" is not entirely self-directed or open-ended but is heavily constrained by human-defined priors and safety constraints. The paper should temper the "self-directed" claim to reflect that the agent operates within a bounded, human-curated search space, rather than discovering entirely novel interaction modes from scratch.

Finally, the "Limitations" section vaguely states that "Improper skill reuse can hurt performance." However, Table 3 (Cross-environment transfer) provides a concrete counter-example: the "Two-arm handover" task sees a performance *drop* from 24.0% to 20.0% when using \textsc{RATs} skills. This is not just a theoretical risk but an observed failure mode of the proposed method. The paper should explicitly analyze this negative transfer case in the main text or discussion rather than burying it in a generic limitation, as it challenges the robustness of the "play" curriculum in generating universally beneficial skills.
