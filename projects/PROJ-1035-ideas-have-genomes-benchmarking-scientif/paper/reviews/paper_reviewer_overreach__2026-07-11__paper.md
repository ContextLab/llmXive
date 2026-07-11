---
action_items:
- id: 4a00e89c5232
  severity: writing
  text: 'Abstract: ''Experiments on 14 LLM-based scientists'' implies broad diversity,
    but Section 5.1 shows 12/14 are GPT-5.5 variants. Narrow to ''14 configurations
    primarily based on GPT-5.5'' or explicitly note the lack of open-weight model
    testing.'
- id: 5a0e3e452145
  severity: writing
  text: 'Abstract/Conclusion: ''Reshuffles rankings rather than helping'' implies
    ineffectiveness, yet Section 5.3 notes a median gain of +4.4. Rephrase to ''reshuffles
    rankings despite providing an average gain'' to accurately reflect the data.'
- id: d4b3b9e8015c
  severity: writing
  text: 'Conclusion: ''Need compositional verification modules'' prescribes a causal
    solution from a correlational finding (Fig 5.4b). Change to ''suggest that compositional
    verification modules may be a necessary component'' to align with the evidence.'
artifact_hash: 3ad519eab3effcd18457f63d397b7e31c9b86e08766b51b9bcdd374f35279468
artifact_path: projects/PROJ-1035-ideas-have-genomes-benchmarking-scientif/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-11T02:52:47.592383Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper generally maintains a strong alignment between its evidence and its claims, particularly in the careful definition of the "Idea Genome" and the specific metrics used. However, there are three instances where the rhetoric slightly exceeds the scope of the demonstrated evidence, primarily regarding the generalizability of the model pool and the interpretation of correlation as design prescription.

First, the Abstract and Introduction frame the evaluation as "Experiments on 14 LLM-based scientists," which suggests a broad, diverse survey of the current state of the art. However, the results in Section 5.1 and Table 1 reveal that the participant pool is heavily concentrated on a single backbone: 12 of the 14 entries are variants of GPT-5.5 (direct, agents, or CLI harnesses), with only two using Claude Opus 4.7. No open-weight models (e.g., Llama, Mistral) or other major closed models are represented in the main comparison. The claim of "14 scientists" creates an impression of a wide-ranging benchmark that the specific model selection does not fully support. The text should be narrowed to reflect that the study evaluates "14 configurations primarily based on GPT-5.5 and Claude Opus" to avoid implying a generalizable finding across all model families.

Second, the Abstract and Conclusion state that structured lineage context "reshuffles system rankings rather than helping every participant uniformly." While the data in Section 5.3 does show heterogeneous gains (e.g., GPT-5.5 gains +2.3 while Kimi gains +6.9), the phrasing "rather than helping" subtly implies the context might be ineffective or neutral on average. The text explicitly notes a "median gain is +4.4," confirming that the context *does* help on average. The rhetoric should be adjusted to "reshuffles rankings despite providing an average gain" to ensure the reader understands the context is beneficial overall, even if the distribution of that benefit is uneven.

Finally, the Conclusion asserts that the findings "point to a concrete design direction: auto-research systems need compositional verification modules." This is a prescriptive claim derived from the moderate positive correlation shown in Figure 5.4b between closed-form understanding and generation heredity. While the correlation supports the hypothesis, the experimental design (observational correlation) does not prove that adding verification modules *causes* better generation, nor does it rule out that both capabilities stem from a third factor (e.g., general reasoning ability). The language should be hedged to "suggest that compositional verification modules may be a necessary component" or "indicate a potential design direction" to align the prescriptive strength with the correlational evidence.
