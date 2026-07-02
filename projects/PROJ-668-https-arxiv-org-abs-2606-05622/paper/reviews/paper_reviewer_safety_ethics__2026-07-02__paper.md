---
action_items:
- id: 601a732600e3
  severity: writing
  text: 'The ethics statement claims the dataset is ''manually validated to be free
    of offensive material'' (Section: Ethics statement), but the methodology relies
    on LLMs (GPT-5.4) to generate and filter constraints. Clarify the extent of human
    oversight in the data construction pipeline to ensure no harmful or biased constraints
    were inadvertently generated and retained.'
- id: a9b3170d4431
  severity: writing
  text: 'The benchmark simulates user interactions where an LLM acts as a user providing
    feedback on plans (Section: Runtime Interaction Details). Explicitly state whether
    this simulation was tested for potential to generate harmful, harassing, or psychologically
    distressing feedback scenarios, and confirm that safety filters were applied to
    the user simulator''s output.'
- id: ba7aca3d6c56
  severity: writing
  text: 'The evaluation rubric includes a ''Safety'' dimension (Table: rubrics-details),
    yet the error cases (Appendix: Error Case Study) focus on physical grounding and
    effectiveness. Provide evidence or a brief discussion on how the benchmark specifically
    tests for safety-critical failures (e.g., plans causing physical harm) to ensure
    the ''Safety'' rubric is not merely theoretical.'
artifact_hash: 4c1448d6284f48048906ba145a0a228414d922f3ed6467261dd793143d8d0ecf
artifact_path: projects/PROJ-668-https-arxiv-org-abs-2606-05622/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T21:46:06.405414Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper addresses safety and ethics primarily through a dedicated statement and the inclusion of a 'Safety' rubric dimension. The authors state that the dataset is manually validated to be free of offensive material and that data annotation was performed by PhD-level researchers. However, the data construction pipeline described in the Formalization section (Section: Formalization) relies heavily on LLMs (specifically GPT-5.4) for query rewriting, constraint extraction, and merging. While human validation is mentioned, the manuscript lacks specific details on the human-in-the-loop process for the generation phase. It is unclear if humans reviewed the raw outputs of the LLMs before they were aggregated into the benchmark, or if the 'manual validation' only applied to a final sample. Given the potential for LLMs to generate subtle biases or harmful constraints (e.g., suggesting unsafe tools for household tasks), the scope of human oversight in the data creation pipeline should be explicitly clarified to ensure the dataset does not contain latent safety risks.

Furthermore, the benchmark involves a simulated user interaction where an LLM provides feedback to an agent. The 'User Simulator' prompt (Figure: user-llm-prompt) instructs the model to point out problems and ask for regeneration. While the goal is to test adaptive planning, there is a risk that the simulator could generate feedback that is overly aggressive, confusing, or potentially harmful in a real-world deployment context. The paper should explicitly confirm that safety filters were applied to the user simulator's output to prevent the generation of harmful or harassing feedback during the evaluation process.

Finally, while the 'Safety' rubric is defined (Table: rubrics-details) as avoiding harm to humans, the error analysis in the Appendix focuses on physical grounding (e.g., using ice to unclog a toilet) and effectiveness (e.g., failing to fix a lamp). The paper would benefit from a specific discussion or example demonstrating how the benchmark successfully identifies and penalizes plans that pose direct physical safety risks to humans, rather than just physical implausibility. This would strengthen the claim that the benchmark effectively evaluates safety-critical planning capabilities.
