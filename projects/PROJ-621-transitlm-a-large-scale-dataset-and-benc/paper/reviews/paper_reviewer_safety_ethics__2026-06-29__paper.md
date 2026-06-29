---
action_items:
- id: b9f1683138bd
  severity: science
  text: Section 9 claims re-identification is infeasible due to single-day sampling.
    However, precise GPS + station sequences can uniquely identify users (De Montjoye
    et al., 2013). Provide a formal privacy risk analysis or proof that this specific
    feature set does not leak identity.
- id: 69d3dc2815a6
  severity: science
  text: Section 3.2 mentions segment-level travel times. If relative times are released
    with GPS/station data, re-identification risk remains high. Clarify if relative
    timing is released and assess its impact on privacy.
- id: 345304c365da
  severity: writing
  text: The dataset is a pre-training corpus. Confirm a rigorous deduplication step
    removed PII and sensitive routes (e.g., to hospitals, police stations) beyond
    just removing user IDs.
artifact_hash: edae6ae2d895f06d190c806d301a85f463bbdd062907b9af82e2ca86a0aa3cf7
artifact_path: projects/PROJ-621-transitlm-a-large-scale-dataset-and-benc/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T22:45:30.615469Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper presents a large-scale dataset of transit route planning logs, raising significant safety and ethics concerns regarding user privacy and potential dual-use risks.

**Privacy and Re-identification Risks:**
In Section 9 (Ethics and Privacy), the authors argue that re-identification is infeasible because records are isolated, sampled from a single day, and lack user identifiers. However, this argument is insufficient given the data granularity. The dataset includes precise GPS coordinates for origins and destinations, along with specific station sequences (Section 3.2). As demonstrated by De Montjoye et al. (2013) [cited in the paper], only four spatio-temporal points are often sufficient to uniquely identify 95% of individuals in a mobility dataset. The combination of precise GPS coordinates and the specific sequence of stations visited creates a high-dimensional mobility fingerprint. Even without absolute timestamps, the relative travel times and the specific route structure could allow an adversary to link these records to external datasets (e.g., public transit card logs, known commute patterns) to re-identify users. The claim that "it is infeasible to associate multiple records with the same individual" is not robustly supported without a formal differential privacy analysis or a demonstration that the specific feature set does not leak identity.

**Data Sensitivity and Content:**
The dataset covers four major Chinese cities. While the authors state that "no demographic attributes" are present, the origin and destination coordinates could implicitly reveal sensitive locations (e.g., residential areas, hospitals, government buildings, or places of worship). If the dataset is released as a pre-training corpus, there is a risk that the model could inadvertently memorize and reproduce these sensitive location pairs, potentially aiding in surveillance or targeted harassment. The authors must explicitly describe the filtering process used to remove or mask routes involving sensitive POIs or residential areas before release.

**Dual-Use and Surveillance:**
The capability to generate "map-free" routes from GPS coordinates (Section 1, 5) could be misused for surveillance or tracking if the model is deployed in a context where it can infer user movements from partial data. While the paper frames this as a convenience feature, the underlying technology effectively internalizes the transit network topology and user behavior patterns. The authors should discuss potential misuse scenarios, such as using the model to infer the likely movements of a specific individual given a known origin, and propose mitigation strategies (e.g., access controls, usage policies).

**Recommendation:**
The paper requires a minor revision to address these privacy concerns. The authors must strengthen the Ethics section with a more rigorous privacy risk analysis, specifically addressing the re-identification risk posed by the combination of GPS coordinates and station sequences. They should also clarify the handling of sensitive locations and discuss potential dual-use risks.
