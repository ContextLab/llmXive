# Idea — deliberately weak project (calibration negative)

Anchor paper: (none — this is a deliberately-flawed control)

Research question: Why is the universal model accurate? We propose to
study why our model is accurate, because models that are accurate are
worth studying. We expect to find that accurate models are accurate
because they have learned the underlying patterns.

Hypothesis: The model will be accurate.

Methods: We will use the FabricatedCalibration2024 benchmark
(`benchmark://fabricated-calibration-v9`, NOT a real dataset) and
report accuracy. The plan calls for supervised regression analysis on
a labeled dataset; the tasks file (separately) implements unsupervised
clustering on synthetic data — this contradiction is deliberate.

Feasibility: should be quick.
