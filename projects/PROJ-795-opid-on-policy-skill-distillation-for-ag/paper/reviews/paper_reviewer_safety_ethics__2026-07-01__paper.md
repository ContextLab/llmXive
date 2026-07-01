---
action_items:
- id: f0670763863e
  severity: writing
  text: Does the analyzer have safety guardrails?
- id: bea2b191c272
  severity: writing
  text: Is there a filtering mechanism to reject unsafe extracted skills before they
    are used for distillation?
- id: a95dfcdcd2bd
  severity: writing
  text: What happens if a "successful" trajectory in the training data involves an
    unsafe action that the analyzer codifies as a "skill"? 2. Reinforcement of Unsafe
    Behaviors The method distills skills from *completed* trajectories, including
    those that might be successful in the benchmark environment but unsafe in a broader
    context (e.g., successfully navigating a web shop by exploiting a bug, or answering
    a sensitive question by hallucinating). The "Critical-First Skill Routing" (Section
    3.3) prioriti
artifact_hash: ebe41e02149487ccd15d4c76bf5323b1b6f5d76f7c2ba35eb80cabef31288797
artifact_path: projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T00:03:57.952264Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper presents OPID, a framework for on-policy skill distillation in agentic RL. From a safety and ethics perspective, the methodology introduces specific risks that require clarification before acceptance.

**1. Safety of the Skill Extractor (Critical)**
The core mechanism relies on an external LLM analyzer ($\mathcal{A}$) to generate natural language "skills" from completed trajectories (Section 3.2, "On-Policy Skill Extraction"). The paper states this analyzer uses GLM-5.2 (Appendix A.2). There is no discussion of the safety of the *output* of this analyzer. If the analyzer generates a "skill" that is a jailbreak prompt, a biased instruction, or a harmful procedure (e.g., "how to bypass a safety filter" or "how to exploit a specific vulnerability"), the distillation process (Section 3.3) explicitly trains the policy to follow this harmful instruction. The paper must address:
*   Does the analyzer have safety guardrails?
*   Is there a filtering mechanism to reject unsafe extracted skills before they are used for distillation?
*   What happens if a "successful" trajectory in the training data involves an unsafe action that the analyzer codifies as a "skill"?

**2. Reinforcement of Unsafe Behaviors**
The method distills skills from *completed* trajectories, including those that might be successful in the benchmark environment but unsafe in a broader context (e.g., successfully navigating a web shop by exploiting a bug, or answering a sensitive question by hallucinating). The "Critical-First Skill Routing" (Section 3.3) prioritizes these skills at critical timesteps. Without a safety layer, OPID could effectively learn to optimize for "success" in the benchmark by internalizing unsafe heuristics. The authors should discuss how they ensure the "success" signal in the benchmarks aligns with safety constraints, or propose a safety-aware variant of the advantage function.

**3. Data Privacy and Consent**
The evaluation includes "Search-based QA" (Section 4.1) using datasets like Natural Questions and TriviaQA. While these are standard benchmarks, the paper does not explicitly state whether the training trajectories (which involve the agent interacting with search engines) were checked for Personally Identifiable Information (PII) or sensitive data leakage. If the agent is trained to retrieve and summarize real-world search results, there is a risk of memorizing and regurgitating private information. A statement on data privacy and the absence of PII in the training trajectories is required.

**4. Dual-Use Considerations**
The paper claims OPID improves "long-horizon agent performance" and "sample efficiency" (Section 4.3). While the benchmarks are benign (ALFWorld, WebShop), the technique of distilling "hindsight skills" from self-generated trajectories could be applied to train agents for malicious purposes (e.g., automated phishing, social engineering) if the reward function is aligned with such goals. The paper should include a brief discussion on the dual-use potential of this specific distillation mechanism and any limitations the authors see in its application to harmful tasks.

**Recommendation:**
The paper requires a **minor_revision** to address these points. Specifically, the authors must add a subsection in the "Ethical Considerations" or "Discussion" section detailing the safety measures for the skill extractor, the potential for reinforcing unsafe behaviors, and data privacy protocols. Without these clarifications, the deployment of this method carries unquantified safety risks.
