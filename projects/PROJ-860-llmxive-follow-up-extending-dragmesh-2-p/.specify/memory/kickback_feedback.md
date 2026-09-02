# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The estimator formula $k_{est} = |\Delta 	au| / |\Delta v|$ assumes a linear relationship between torque derivative and velocity derivative to proxy stiffness. However, in a friction-dominated regime (sliding), torque is primarily a function of normal force and friction coefficient ($	au pprox \mu N r$), not velocity derivatives. The plan does not account for the confounding variable of normal force (contact load). Without controlling for or measuring normal force, $k_{est}$ may correlate with contact load rather than stiffness, invalidating the construct validity of the 'Virtual Tactile' proxy.
- The plan states 'Generate 50+ articulated objects... distinct from the training distribution' but does not define the 'training distribution' or the mechanism for ensuring the test objects are truly 'zero-shot' (unseen). If the randomization of friction (0.1-2.0) overlaps with the training distribution, the 'zero-shot' claim is invalid. The methodology lacks a clear definition of the domain shift required to validate zero-shot adaptation.
