---
action_items:
- id: a4589f7d9a9d
  severity: writing
  text: Define 'FM' (Foundation Model) at first use in Section 2. Currently, the text
    jumps to 'Domain-Specific Foundation Model ("FM")' without explicitly stating
    that FM is the acronym for the broader class before narrowing the scope.
- id: 2061a7186d02
  severity: writing
  text: Replace the metaphor-heavy term 'Tsaheylu' with a standard technical descriptor
    (e.g., 'bidirectional interface' or 'modality bridge') in the main text. While
    the Avatar analogy is creative, using a fictional proper noun as a primary technical
    term for a communication protocol creates unnecessary cognitive load for non-fans
    and non-specialists.
- id: f070db347578
  severity: writing
  text: Define 'MAS' (Multi-Agent Systems) at first use in Section 2. The text introduces
    'Multi-Agent Systems (MAS)' but later uses 'EywaMAS' and 'MAS' interchangeably
    without ensuring the acronym is clearly established as a standard term before
    the specific framework name.
- id: e09f86f51346
  severity: writing
  text: Replace 'modality-native' with 'native-modality' or 'native to the modality'
    in Section 1 and 3. The hyphenated adjective 'modality-native' is non-standard
    jargon that obscures meaning; 'native to the modality' is clearer.
- id: 886e43afa9a1
  severity: writing
  text: Define 'MCP' (Model Context Protocol) at first use in Section 3. The text
    states 'Model Context Protocol (MCP)' but assumes the reader knows this is a specific
    protocol standard rather than a generic description. If it is a specific external
    standard, it should be cited or briefly explained for non-LLM-specialists.
artifact_hash: 6f6f16bf33fe17a682df44afbf900ee0d80c1586f03954b67f158a9d54f94900
artifact_path: projects/PROJ-573-https-arxiv-org-abs-2604-27351/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:40:13.873217Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on specialized jargon and coined terminology that obscures the core technical contributions for a general scientific audience. 

First, the term **"Tsaheylu"** is used repeatedly (Sections 1, 3, 4, 5, 6, Appendix) to describe the FM-LLM interface. While the Avatar analogy is engaging, using a fictional proper noun as the primary technical name for a communication protocol is excessive jargon. It forces the reader to constantly map a movie concept to a technical implementation. This should be replaced with a standard descriptive term like "bidirectional interface," "modality bridge," or "translation layer" in the main text, reserving the analogy for the introduction or a footnote.

Second, several acronyms are introduced without clear definition or are used inconsistently. In Section 2, **"FM"** is introduced as "Domain-Specific Foundation Model ('FM')", but the acronym "FM" is often used in literature to mean "Foundation Model" generally. The distinction between the general class and the specific domain model should be clarified immediately. Similarly, **"MAS"** (Multi-Agent Systems) is defined in Section 2, but the specific framework name **"EywaMAS"** is introduced in Section 4 without explicitly reiterating that "MAS" refers to the general class of systems.

Third, the phrase **"modality-native"** (Sections 1, 3, 5, 6) is a non-standard compound adjective. It is unclear whether this means "native to the modality" or "native modality." Replacing this with "native to the modality" or "modality-specific" would improve clarity.

Finally, **"MCP"** (Model Context Protocol) is introduced in Section 3. If this refers to a specific external standard (e.g., from a specific company or open-source project), it requires a citation and a brief explanation of what it is for readers unfamiliar with the specific ecosystem. If it is a generic term coined by the authors, it should be defined as such.

These changes are necessary to ensure the paper is accessible to researchers outside the immediate sub-field of LLM agent orchestration.
