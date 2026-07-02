---
action_items:
- id: d8e5966e6c24
  severity: writing
  text: The Impact Statement (Section 7) is generic and dismissive. Given the paper's
    focus on reasoning capabilities and the potential for these models to be used
    in high-stakes domains (e.g., legal, medical, or educational reasoning), the authors
    must expand this section to explicitly discuss risks of automated reasoning errors,
    potential for hallucination in critical contexts, and dual-use concerns regarding
    the optimization of reasoning for malicious tasks.
- id: 7a24deb5d9af
  severity: writing
  text: The study uses self-generated CoT demonstrations from weaker models (Section
    4.2.1) which may contain incorrect reasoning steps. The authors should add a discussion
    on the safety implications of training models on potentially flawed or misleading
    reasoning chains, and whether this could reinforce systematic errors or biases
    in the model's reasoning process.
- id: b95e1b9d2b93
  severity: writing
  text: The paper evaluates on datasets like MATH and GSM8K but does not address the
    potential for these reasoning capabilities to be exploited for generating sophisticated
    disinformation, social engineering scripts, or automated code generation for malicious
    purposes. A brief risk assessment regarding the dual-use nature of improved reasoning
    capabilities is required.
artifact_hash: da80d19d18126d829231e022c90784234c941daee73db4750a219950884e0e6f
artifact_path: projects/PROJ-563-many-shot-cot-icl-making-in-context-lear/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:14:51.103427Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript presents a significant study on the scaling behavior of Chain-of-Thought In-Context Learning (CoT-ICL), reframing it as in-context test-time learning. From a safety and ethics perspective, the work is generally sound in its experimental design, particularly in the use of standard, publicly available benchmarks (MATH, GSM8K, SuperGLUE) and the explicit separation of training and test splits to prevent data leakage (Appendix A.1). The authors also demonstrate awareness of potential biases by comparing reasoning-oriented and non-reasoning models.

However, the **Impact Statement** (Section 7) is insufficient for a paper of this scope. The authors state: "There are many potential societal consequences of our work, none which we feel must be specifically highlighted here." This is a critical oversight. The paper demonstrates that reasoning capabilities can be significantly enhanced through specific prompt engineering and demonstration ordering. This has direct implications for:
1.  **Dual-Use Risks:** Enhanced reasoning capabilities could be leveraged to generate more convincing disinformation, automate complex social engineering attacks, or optimize code for malicious purposes. The "Curvilinear Demonstration Selection" (CDS) method could theoretically be used to make models more robust at generating sophisticated, multi-step deceptive narratives.
2.  **Reliability in High-Stakes Domains:** The paper shows that reasoning performance is unstable and order-dependent for non-reasoning models. Deploying such models in legal, medical, or financial contexts without understanding these instabilities could lead to severe harms. The authors should discuss the risks of deploying these "many-shot" reasoning systems in such environments.
3.  **Bias Amplification:** The reliance on self-generated demonstrations (Section 4.2) raises concerns about the propagation of model-specific biases or errors. If a model generates flawed reasoning chains, using them as demonstrations could reinforce these flaws in a feedback loop.

Additionally, the use of **self-generated CoT** (Section 4.2.1) where models are prompted with their own potentially incorrect reasoning steps (the "Wrong" set) warrants a safety discussion. While the paper shows this can sometimes improve performance due to distributional alignment, it also risks reinforcing systematic errors or "hallucinated" logic patterns. The authors should briefly address the ethical implications of training models on their own flawed outputs.

Finally, while the paper uses standard benchmarks, the authors should explicitly state that their findings on "reasoning" are limited to the specific tasks evaluated (math, logic puzzles) and may not generalize to real-world reasoning tasks involving nuanced ethical judgment or complex social dynamics, where the risks of automated reasoning are highest.

The paper does not appear to involve human subjects, animal testing, or private data, so no IRB/IACUC concerns are raised. The primary safety gaps are the lack of a robust Impact Statement and the absence of a discussion on the dual-use potential of enhanced reasoning capabilities.
