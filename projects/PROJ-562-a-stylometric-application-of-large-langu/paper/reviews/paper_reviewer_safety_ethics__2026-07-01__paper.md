---
action_items: []
artifact_hash: 148021f63314c6cbe2b6159eaaaecc4e6c793ec5541ddbe74681664a10cdde19
artifact_path: projects/PROJ-562-a-stylometric-application-of-large-langu/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:24:04.568195Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.5
verdict: accept
---

The manuscript presents a stylometric analysis using Large Language Models (LLMs) trained on public domain texts from Project Gutenberg. From a safety and ethics perspective, the study demonstrates strong adherence to responsible research practices.

**Data Privacy and Consent:**
The dataset consists entirely of works by authors who are deceased and whose writings are in the public domain (e.g., Jane Austen, L. Frank Baum, Mark Twain). As noted in Section 2.1 (lines 134-138), the authors explicitly selected these texts to eliminate confounds and ensure legal/ethical clarity. No personal data, private communications, or sensitive information regarding living individuals were used. Consequently, no Institutional Review Board (IRB) or Informed Consent procedures were required, and the authors correctly omit such declarations.

**Dual-Use and Potential for Harm:**
The primary application discussed is authorship attribution, specifically confirming the historical attribution of the 15th *Oz* book. While stylometric techniques can theoretically be misused for deanonymizing authors in adversarial contexts (e.g., identifying whistleblowers or bypassing privacy protections), the paper's scope is strictly limited to historical literary analysis of public domain works. The authors acknowledge the "black box" nature of the models and the potential for adversarial attacks in the Discussion (Section 5.3, lines 530-545), but they do not provide instructions, code, or methodologies for deploying these models against private or protected datasets. The code is hosted on a public GitHub repository, but the training data is restricted to the public domain, mitigating the risk of the pipeline being used to process sensitive private data without modification.

**Bias and Fairness:**
The study uses a small, homogeneous set of eight authors, all writing in English during overlapping historical periods. While this limits generalizability, it does not introduce active harm or bias against protected groups in the context of this specific experiment. The authors do not claim their method is suitable for high-stakes decision-making (e.g., legal evidence or hiring) where bias could cause real-world harm.

**Conclusion:**
The research is ethically sound. The use of public domain data removes consent and privacy concerns. The potential for dual-use harm is low given the specific application to historical literature and the lack of deployment instructions for adversarial scenarios. No revisions are required regarding safety or ethics.
