# Tiny Synthetic-Timeseries Smoke Test

**Field**: computer-science

A tiny end-to-end fixture for the llmXive pipeline. Generate 100 points
of a synthetic sine wave with Gaussian noise, fit a linear regression
to the noisy values, and report the residual standard deviation.
The whole project must run in under a minute on a free GitHub Actions
runner so the e2e test stays cheap.
