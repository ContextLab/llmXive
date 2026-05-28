# Idea — Cross-study consistency of right-M1 activation in publicly-released OpenNeuro motor-task fMRI datasets (neuroscience)

Data source: OpenNeuro (publicly-released motor-task fMRI datasets) (https://openneuro.org/); publicly accessible under an open-access policy.

Research question: Across publicly-available motor-task fMRI datasets on OpenNeuro spanning right-hand finger-tapping protocols, how consistent are the peak right-M1 activation Z-statistics and voxel coordinates after harmonized preprocessing?

Hypothesis: Peak voxel coordinates cluster within ≈8 mm across studies; peak Z-statistics show 30-50% inter-study variance attributable to scanner vendor + TR differences.

Methods: Identify 5-8 OpenNeuro motor-task datasets matching the right-hand finger-tapping protocol; apply fMRIPrep harmonized preprocessing; per-subject GLM with right-hand-vs-rest contrast; extract peak voxel coordinates + Z-stats in a literature-derived M1 ROI; report inter-study variance decomposition.

Feasibility: implementable with free open-source tooling + the publicly-accessible dataset cited above.
