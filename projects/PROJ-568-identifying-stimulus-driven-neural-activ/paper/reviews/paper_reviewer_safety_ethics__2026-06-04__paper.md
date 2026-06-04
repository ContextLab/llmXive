---
action_items:
- id: 24b56697ed89
  severity: science
  text: Add explicit statement about IRB approval and informed consent procedures
    for all cited intracranial EEG datasets. This survey references data from 53 patients
    (n=5023 electrodes); readers need assurance ethical standards were met.
- id: 1e81764f785d
  severity: science
  text: Include discussion of data privacy and de-identification procedures used in
    the referenced studies. Patient electrode locations and neural recordings could
    potentially be re-identified without proper safeguards.
- id: 6546bb3d33c8
  severity: science
  text: Address dual-use considerations for brain activity decoding methods discussed
    (e.g., neural decoding, stimulus reconstruction). These techniques could have
    applications beyond cognitive neuroscience.
artifact_hash: 88c485888572e5b5ec21db55f3e25c0d533affd80dd028fd7994137fbaf7e64e
artifact_path: projects/PROJ-568-identifying-stimulus-driven-neural-activ/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-04T13:23:46.243011Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

This survey chapter appropriately contextualizes the clinical setting of intracranial EEG (iEEG) data, noting that recordings come from neurosurgical patients with drug-resistant epilepsy (Section: "What are some modality-specific challenges to identifying stimulus-driven brain activity from intracranial recordings?"). This acknowledgment of the vulnerable population is ethically sound.

However, several ethical considerations remain insufficiently addressed:

1. **IRB/Consent Documentation**: The paper references electrode location data from 53 patients (Figure 4, n=5023 electrodes) but does not explicitly state whether IRB approval was obtained for the data sources cited, nor does it describe informed consent procedures for research use of clinical data. Given this is a methodological review that may inform future research using similar data, readers need assurance about ethical standards.

2. **Data Privacy**: Patient-specific electrode locations and neural recordings could potentially be re-identified. The paper should discuss de-identification procedures used in the referenced studies (e.g., OwenEtal20, SedeEtal03).

3. **Dual-Use Considerations**: Methods discussed—including neural decoding (Section: "Generalized linear models and multivariate pattern analysis"), stimulus reconstruction (Figure 3: "Joint geometric models"), and across-participant modeling—could have applications beyond cognitive neuroscience. A brief acknowledgment of these dual-use potential risks would strengthen the ethical framing.

These additions would align the manuscript with best practices for research involving human neural data.
