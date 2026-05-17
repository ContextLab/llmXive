---
artifact_hash: 88c485888572e5b5ec21db55f3e25c0d533affd80dd028fd7994137fbaf7e64e
artifact_path: projects/PROJ-568-identifying-stimulus-driven-neural-activ/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:47:46.520693Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

This survey chapter appropriately contextualizes the clinical setting of intracranial EEG (iEEG) data, specifically noting in Section 1 ("Invasive approaches") that recordings are typically obtained from neurosurgical patients (e.g., drug-resistant epilepsy) who elect to participate in research separate from treatment. This acknowledgment of the vulnerable patient population is a positive ethical baseline.

However, the manuscript requires a more explicit discussion of data privacy and cognitive liberty risks, particularly given the methods described for neural decoding. In Section 2 ("Identifying stimulus-driven neural activity"), the text cites work on decoding speech and semantic representations (e.g., Pasley et al. 2012; Proix et al. 2022). While these are cited as existing literature, the chapter should explicitly address the ethical implications of reconstructing private internal states (speech, thoughts) from neural data. This touches on emerging concerns regarding "neuro-rights" and cognitive privacy.

Additionally, while the text mentions that patients "elect to participate" (Section 1), it does not detail how data privacy is maintained in multi-patient analyses (Section "Across-participant approaches"). iEEG data is highly sensitive and potentially re-identifiable. A dedicated subsection on Ethical Considerations is recommended. This section should cover:
1.  **Informed Consent:** Ensuring patients understand that their neural data may be used for decoding tasks beyond their clinical care.
2.  **Data Security:** Specific measures taken to anonymize or protect high-fidelity neural recordings from unauthorized access or misuse.
3.  **Dual-Use Risks:** Acknowledging that methods for decoding speech/thoughts could theoretically be misapplied for surveillance or non-consensual interrogation, and how the field mitigates this.

Currently, the ethical framework is implied through clinical context but lacks a proactive safety policy discussion. Please add a brief Ethics Statement or expand the Conclusion to address these privacy and dual-use considerations specifically. This will ensure the chapter aligns with modern standards for responsible neurotechnology research.
