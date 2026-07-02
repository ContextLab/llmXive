---
action_items:
- id: aebc03afa545
  severity: writing
  text: The paper presents a novel framework, d-OPSD, for on-policy self-distillation
    in diffusion large language models (dLLMs). From a safety and ethics perspective,
    the primary concerns revolve around the potential for unintended consequences
    of the self-distillation process, the transparency of the training methodology,
    and the broader implications of the technique. First, the methodology relies on
    a "self-teacher" constructed from the model's own correct generations (Pass@k).
    As noted in Appendix A
artifact_hash: 5c8da21032033f700374cf269bb9ef61b58d8799f1e6049fc84e38c052b8b257
artifact_path: projects/PROJ-732-learning-from-the-self-future-on-policy/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T04:40:50.467826Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper presents a novel framework, d-OPSD, for on-policy self-distillation in diffusion large language models (dLLMs). From a safety and ethics perspective, the primary concerns revolve around the potential for unintended consequences of the self-distillation process, the transparency of the training methodology, and the broader implications of the technique.

First, the methodology relies on a "self-teacher" constructed from the model's own correct generations (Pass@k). As noted in Appendix A.4.2, the authors implement a mechanism to clear unmasked tokens in new blocks to prevent "leaking the final answer." While this is a technical necessity for the distillation process, it raises questions about the integrity of the training signal. If the model fails to generate a correct answer, the sample is discarded or the process is repeated. This filtering could introduce a bias towards specific reasoning patterns that are more likely to be correct, potentially leading to a model that is less robust to edge cases or adversarial inputs. The paper should clarify the ethical implications of this filtering process and whether it could inadvertently reinforce specific reasoning paths while discarding others, which might lead to model collapse or reduced robustness.

Second, the paper acknowledges "policy collapse" as a failure mode in Section 4.5, where the model's performance degrades catastrophically after reaching a peak. While this is a technical limitation, the authors should discuss the safety implications of deploying a model trained with d-OPSD that is prone to collapse. If the model collapses during inference or fine-tuning, could it generate harmful or nonsensical outputs more frequently than baseline models? A brief discussion on the safety risks associated with this instability is recommended, particularly in the context of deploying such models in real-world applications.

Third, while the current experiments are conducted on benign datasets like GSM8K and MATH500, the methodology (d-OPSD) is general and could be applied to other domains. The authors should include a statement in the 'Limitations' or 'Ethical Considerations' section acknowledging that while their current experiments are on benign tasks, the method could theoretically be applied to generate harmful content if used with malicious intent. They should also clarify that they have not evaluated the safety of the generated outputs beyond correctness, and that future work should include safety evaluations to ensure the model does not generate harmful content.

Overall, the paper is well-written and the methodology is sound, but a more thorough discussion of the safety and ethical implications of the proposed technique is needed to ensure that the research is conducted responsibly.
