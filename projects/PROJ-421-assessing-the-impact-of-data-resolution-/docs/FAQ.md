# Frequently Asked Questions

## Q: Why use nearest-neighbor resampling?
A: Nearest-neighbor resampling preserves the categorical nature of land cover data, avoiding interpolation artifacts that could introduce false values.
## Q: How is the λ parameter calibrated?
A: λ is estimated via Maximum Likelihood Estimation (MLE) on a random sample of the 30m data.

## Q: What is the significance of the 0.80 power threshold?
A: {{claim:c_fb7194f8}} (Wikipedia: Replication crisis, https://en.wikipedia.org/wiki/Replication_crisis)

## Q: Why is memory management important?
A: High-resolution spatial data can be large. Windowed I/O ensures the pipeline runs within typical RAM constraints (7GB).

## Q: Can I analyze other regions?
A: Yes, modify `code/config.py` to change the data source and region. Ensure the data is available and validated.

## Q: What if the download fails?
A: The pipeline includes retry logic with exponential backoff. Check your internet connection and try again.

## Q: How do I interpret the power curve?
A: The power curve shows how statistical power decreases as resolution becomes coarser. The threshold is where power drops below 0.80.

## Q: What is the Type II error delta?
A: It is the difference between the Type II error rate at a given resolution and the baseline (30m) rate. A higher delta indicates a greater loss of power.
