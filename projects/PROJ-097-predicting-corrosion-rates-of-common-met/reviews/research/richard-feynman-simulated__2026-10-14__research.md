---
action_items: []
artifact_hash: 071ee76b54996eff3a64fee0fc7605d38a13c49a2ac720c67e212cd705f9ab97
artifact_path: projects/PROJ-097-predicting-corrosion-rates-of-common-met/specs/001-predicting-corrosion-rates-of-common-met/spec.md
backend: dartmouth
feedback: "Look, picture what a permutation test actually does before you write it\
  \ down twice. FR-002 says the Null-Model comparison uses 'a permutation test (target-permutation,\
  \ RMSE change as statistic)' \u2014 but target permutation (shuffling the y-column)\
  \ tests whether the model beats noise; it cannot, even in principle, compare a Full\
  \ model to a Null model, because both models get the same shuffled targets. To test\
  \ whether interactions add anything you just need the paired distribution of Full-vs-Null\
  \ err"
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-10-14T00:06:13.219487Z'
reviewer_kind: llm
reviewer_name: richard-feynman-simulated
score: 0.0
verdict: minor_revision
---

Look, picture what a permutation test actually does before you write it down twice. FR-002 says the Null-Model comparison uses 'a permutation test (target-permutation, RMSE change as statistic)' — but target permutation (shuffling the y-column) tests whether the model beats noise; it cannot, even in principle, compare a Full model to a Null model, because both models get the same shuffled targets. To test whether interactions add anything you just need the paired distribution of Full-vs-Null errors across CV folds, or you permute the interaction *columns* between Full and Null — the spec conflates two different shuffles. Then FR-012 does the other shuffle (column permutation) and calls it 'a non-circular validation of interaction relevance' — but it isn't. A Random Forest learns interactions natively; shuffling the engineered pH_x_salinity column only tells you the model used that redundant column, not that the interaction is real. If the tree can get the same signal from pH and salinity separately, your engineered column is a duplicate wire, and the test passes for a boring reason. The Full-vs-Null comparison in SC-002 is the honest test; FR-012 is decoration dressed as validation. Second thing that would embarrass you if it failed: the whole house of cards rests on 'At least one public tabular dataset with ≥ 1 000 rows containing the required variables (pH, salinity, temperature, composition, corrosion rate) exists on Zenodo or OpenML' — that's an assumption, not a checked fact, and my physical picture of OpenML says corrosion tables with all five columns at that size are rare. Nobody has looked. If that assumption dies, everything downstream (SC-001 through SC-007) is testing an empty pipeline. Also, small but telling: SC-001 demands beating a mean-only baseline by 0.05 R² — that's a bar lying on the floor; the interesting comparison is the additive (non-interaction) model, which the spec elsewhere correctly sets up and then doesn't use as the success criterion. Finally, 'community-standard for feature-set stability' for Jaccard 0.8 and 'cumulative SHAP contribution > 90 %' as 'a widely used standard' — saying so doesn't make it so; those numbers are asserted, not established anywhere in the artifact.

---

> *Note: this contribution was authored by **Richard Feynman (simulated)** — a simulated AI persona shaped from the public-record writings of Richard Feynman, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Richard Feynman.*
