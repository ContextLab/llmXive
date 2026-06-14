## Research-question validation

### Phenomenon-vs-method check

**Verdict**: concern

No explicit research question is stated in the idea note. The title "Evaluating the Statistical Validity of Crowdsourced Labels" describes a topic area but not a specific phenomenon, mechanism, or relationship to investigate. The idea appears to be focused on methodology (evaluating statistical validity) rather than a substantive question about crowdsourcing behavior, label quality, or annotation processes.

### Circularity check

**Verdict**: concern

Cannot properly assess circularity without a stated research question. If the idea is "can statistical methods detect noise in crowdsourced labels," the predictor (statistical test) and predicted variable (label quality) must come from independent sources. If both are derived from the same label dataset without external validation, circularity risk is high.

### Triviality check

**Verdict**: concern

Without a specific hypothesis, triviality cannot be assessed. However, the general question "are crowdsourced labels statistically valid?" risks a predetermined answer: labels have known noise patterns (well-documented in literature), so confirming this is not informative. The question needs to specify what conditions, populations, or label types make validity uncertain.

### Question-narrowing check

**Verdict**: fail

The idea as written frames an evaluation task ("evaluating statistical validity") rather than a domain question. This is a methodological checklist, not a research question about how crowdsourced labels behave, under what conditions they fail, or what factors predict label quality.

### Overall verdict

**Verdict**: validator_revise

[REVISED]
Under what task and annotator conditions do crowdsourced labels deviate systematically from expert ground truth, and which statistical indicators (inter-annotator agreement, response time, confidence calibration) best predict these deviations?
[/REVISED]
Reframing names specific domain relationships (task/annotator conditions → label quality) and identifies measurable predictors with an empirical outcome, moving from "evaluate validity" to "predict when validity fails."
