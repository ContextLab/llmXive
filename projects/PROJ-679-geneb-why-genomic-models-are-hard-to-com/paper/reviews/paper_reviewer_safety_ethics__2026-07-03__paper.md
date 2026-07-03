---
action_items:
- id: abe0642afe81
  severity: writing
  text: The 'Responsible Application and Ethical Considerations' section (e000) provides
    high-level warnings but lacks specific mitigation strategies for the identified
    dual-use risks (e.g., pathogen design). Explicitly detail how the benchmark prevents
    or detects misuse, or add a dedicated 'Dual-Use Risk Assessment' subsection with
    concrete safeguards.
- id: 4f724d0beff6
  severity: writing
  text: The 'Impact Statement' and 'Limitations' sections acknowledge dataset biases
    toward human and model organisms. However, the paper does not quantify the potential
    for these biases to cause harm in clinical or agricultural deployment (e.g., misdiagnosis
    in underrepresented populations). Add a specific analysis of the downstream risks
    associated with these documented biases.
- id: 86c9663a1907
  severity: writing
  text: The 'Acknowledgements' section lists funding from the Ministry of Economic
    Development of the Russian Federation. While a conflict of interest is declared
    as 'none', the geopolitical context of genomic research requires a more explicit
    statement regarding data sovereignty, potential export control implications, and
    adherence to international biosecurity norms.
artifact_hash: 043e93d2fab619e0251c0029f296fc31d53c712bc78a466a1a30d67af8b711e1
artifact_path: projects/PROJ-679-geneb-why-genomic-models-are-hard-to-com/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T13:08:54.805922Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript addresses critical safety and ethical dimensions of genomic foundation models, particularly regarding the lack of standardized evaluation and the potential for biased or dual-use outcomes. The authors include a dedicated "Responsible Application and Ethical Considerations" section (e000) and an "Impact Statement" that correctly identify the risks of deploying these models in clinical or ecological contexts without rigorous validation. The disclosure of no financial conflicts of interest is clear.

However, the ethical discussion remains somewhat generic. While the paper warns against deployment in clinical settings, it does not provide a concrete framework for how the GENEB benchmark itself mitigates dual-use risks, such as the potential for these models to be repurposed for designing novel pathogens or toxins. Given the sensitivity of genomic data, a more robust "Dual-Use Risk Assessment" is required. This should explicitly address how the benchmark's design (e.g., task selection, data sources) avoids facilitating harmful applications and what specific safeguards are recommended for users.

Furthermore, the "Impact Statement" notes that the task suite is skewed toward eukaryotic and human data. While this is a scientific limitation, the ethical implication—potential harm to underrepresented populations if these models are deployed in precision medicine without correction—needs to be articulated more forcefully. The authors should expand on the specific risks of bias propagation in clinical decision-making.

Finally, the funding source (Ministry of Economic Development of the Russian Federation) is disclosed, but given the global nature of genomic data and biosecurity concerns, the manuscript would benefit from a brief statement on compliance with international biosecurity standards and data sovereignty considerations. The current text is sufficient to flag these issues but requires expansion to meet the rigorous safety standards expected for a benchmark of this scale.
