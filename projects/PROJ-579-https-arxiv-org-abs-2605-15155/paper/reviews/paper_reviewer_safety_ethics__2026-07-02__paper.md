---
action_items:
- id: 8611b40245fe
  severity: writing
  text: The paper relies on 'privileged training-only context' (skills) available
    to the teacher but not the student. Explicitly state the source of these skills
    (e.g., human-annotated, synthetic generation) and confirm they do not contain
    PII, copyrighted text, or harmful instructions.
- id: a8e56631f6db
  severity: writing
  text: The method uses a 'SkillBank' from 'SkillRL' (cited as xia2026skillrl). Verify
    the license and data provenance of this external skill library to ensure it does
    not introduce copyright infringement or safety risks (e.g., jailbreak patterns)
    into the training loop.
- id: a06737b8d03c
  severity: writing
  text: The evaluation includes 'WebShop' (online shopping) and 'Search-QA'. Clarify
    if the training data or the 'SkillBank' contains real user transaction logs or
    private search queries. If so, confirm that all data was anonymized and consent
    was obtained, or that only synthetic/public data was used.
artifact_hash: a2fe5096ad1b93f50db064c40f59b84672b255d5a406d9c082d97d449a5f037d
artifact_path: projects/PROJ-579-https-arxiv-org-abs-2605-15155/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:53:03.474462Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript proposes SDAR, a method for stabilizing On-Policy Self-Distillation (OPSD) in multi-turn LLM agents. From a safety and ethics perspective, the primary concerns revolve around the provenance and nature of the "privileged context" (skills) used to train the teacher branch, as well as the potential for the method to amplify harmful behaviors if the skill library is compromised.

**1. Data Provenance and Privacy (Section 2.1, Appendix Hyperparameters):**
The method relies heavily on a `SkillBank` retrieved from an external source (cited as `SkillRL`). The paper states these are "compact, structured demonstrations" but does not explicitly detail their origin.
*   **Concern:** If these skills are derived from human-annotated data, there is a risk of containing Personally Identifiable Information (PII) or sensitive user data. If they are synthetic, the generation process must be verified to ensure they do not encode harmful instructions (e.g., jailbreaks, phishing templates) that the student model might internalize.
*   **Requirement:** The authors must add a statement in the "Implementation Details" or "Data Availability" section clarifying the source of the `SkillBank`. Specifically, confirm whether the data is synthetic, public, or private, and describe any filtering or anonymization steps taken to remove PII or safety-violating content.

**2. Copyright and Licensing (Section 2.1, Appendix):**
The paper references `SkillRL` (xia2026skillrl) for the skill library.
*   **Concern:** Using external datasets or skill libraries without explicit licensing confirmation can lead to copyright infringement, especially if the skills contain copyrighted text or proprietary code snippets.
*   **Requirement:** Explicitly state the license under which the `SkillBank` is distributed and confirm that its use for training the SDAR model complies with that license.

**3. Dual-Use and Safety Alignment (Section 3, Experiments):**
The benchmarks include `WebShop` (e-commerce) and `Search-QA`.
*   **Concern:** While these are standard benchmarks, the "privileged context" mechanism could theoretically be used to inject specific behavioral biases or harmful strategies if the retrieval system is poisoned or if the skill library is not curated for safety. The paper notes that the method "degrades gracefully" with random retrieval, but does not discuss the impact of *malicious* retrieval or the safety of the distilled policies in adversarial settings.
*   **Requirement:** While a full safety audit is beyond the scope of this paper, the authors should include a brief discussion in the "Limitations" or "Ethical Considerations" section regarding the potential for the method to amplify harmful behaviors if the teacher's privileged context is compromised. Additionally, confirm that the evaluation tasks do not inadvertently train the model to perform unsafe actions (e.g., unauthorized purchases, privacy violations) even if the environment rewards them.

**4. Consent and Human Data:**
*   **Concern:** If the `SkillBank` or the training trajectories for ALFWorld/WebShop involve human demonstrations, the paper must confirm that appropriate consent was obtained or that the data is publicly available under terms that allow for this type of research.
*   **Requirement:** Add a sentence confirming the ethical clearance or public availability status of any human-generated data used in the `SkillBank` or training sets.

The paper does not appear to involve human subjects directly in the experiments (using standard benchmarks), so IRB approval is likely not required, but the data provenance of the auxiliary skills must be transparent.
