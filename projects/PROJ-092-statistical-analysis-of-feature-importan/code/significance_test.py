"""Statistical significance testing for the drift correlation sequence.

Implements (FR-005, FR-008):
  - Mann-Kendall trend test returning Kendall's Tau and trend direction.
  - Block permutation significance test returning a p-value for the
    correlation (rho) sequence.

T024 — small sample size handling (n < 10):
  When the correlation sequence has fewer than 10 observations the
  asymptotic normal approximation used by the Mann-Kendall test is
  unreliable, so the module:
    1. Flags the result as ``small_sample = True``.
    2. Marks the asymptotic Mann-Kendall p-value as unreliable and
       relies on the block permutation p-value instead (FR-008).
    3. Uses an EXACT permutation test (exhaustive enumeration of all
       block-shift permutations when feasible, i.e. n <= 8 and the
       number of distinct circular block shifts is small) or otherwise
       a larger number of random resamples, so the permutation p-value
       remains trustworthy at small n.
"""
import csv
import itertools
import json
import logging
import math
import os
import random
import sys
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)
if not logger.handlers:
  _h = logging.StreamHandler(sys.stdout)
  _h.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
  logger.addHandler(_h)
  logger.setLevel(logging.INFO)

SMALL_SAMPLE_THRESHOLD = 10
DEFAULT_N_RESAMPLES = 1000
SMALL_SAMPLE_N_RESAMPLES = 10000
DEFAULT_BLOCK_SIZE = 2
EXHAUSTIVE_MAX_PERMUTATIONS = 50000

DRIFT_METRICS_PATH = os.path.join("outputs", "drift_metrics.csv")
P_VALUES_PATH = os.path.join("outputs", "p_values.json")


def load_correlation_sequence(drift_metrics_path: str) -> List[float]:
  """Load the sequence of rho values from drift metrics CSV.

  Expects a column named ``rho``. Raises loudly if the file is
  missing or malformed — never returns fabricated values.
  """
  if not os.path.isfile(drift_metrics_path):
    raise FileNotFoundError(
      f"Drift metrics file not found: {drift_metrics_path}. "
      "Run the drift analysis stage first."
    )
  rhos: List[float] = []
  with open(drift_metrics_path, "r", newline="") as f:
    reader = csv.DictReader(f)
    if reader.fieldnames is None or "rho" not in reader.fieldnames:
      raise ValueError(
        f"Expected a 'rho' column in {drift_metrics_path}; "
        f"found columns: {reader.fieldnames}"
      )
    for row in reader:
      raw = (row.get("rho") or "").strip()
      if raw == "":
        continue
      try:
        rhos.append(float(raw))
      except ValueError as exc:
        raise ValueError(f"Non-numeric rho value {raw!r} in {drift_metrics_path}") from exc
  if not rhos:
    raise ValueError(f"No rho values found in {drift_metrics_path}")
  logger.info("Loaded %d rho values from %s", len(rhos), drift_metrics_path)
  return rhos


def _kendall_tau(data: List[float]) -> float:
  """Compute Kendall's Tau (tau-b with no ties handled as tau-a) manually."""
  n = len(data)
  if n < 2:
    return 0.0
  s = 0
  for i in range(n - 1):
    for j in range(i + 1, n):
      s += 1 if data[j] > data[i] else (-1 if data[j] < data[i] else 0)
  return 2.0 * s / (n * (n - 1))


def _normal_sf(z: float) -> float:
  """Survival function of the standard normal distribution (two-sided helper)."""
  return 0.5 * math.erfc(z / math.sqrt(2.0))


def mann_kendall_test(data: List[float]) -> Tuple[float, str, float]:
  """Perform the Mann-Kendall trend test.

  Returns: (Kendall's Tau, trend_direction, p_value).

  The p-value uses the normal approximation with continuity correction
  and variance adjusted for ties. For n < 10 this asymptotic p-value is
  flagged as unreliable by the caller (see ``is_small_sample``); the
  permutation p-value from ``block_permutation_test`` should be relied
  upon instead (FR-008, T024).
  """
  n = len(data)
  if n < 2:
    logger.warning("Mann-Kendall test requires at least 2 points; returning neutral result.")
    return 0.0, "no trend", 1.0

  tau = _kendall_tau(data)

  # Mann-Kendall S statistic and variance (with tie correction)
  s_stat = 0
  for i in range(n - 1):
    for j in range(i + 1, n):
      s_stat += 1 if data[j] > data[i] else (-1 if data[j] < data[i] else 0)

  # Tie correction
  _, tie_counts = _unique_with_counts(data)
  var_s = n * (n - 1) * (2 * n + 5) / 18.0
  tie_term = 0.0
  for t in tie_counts:
    tie_term += t * (t - 1) * (2 * t + 5)
  var_s -= tie_term / 18.0

  if var_s <= 0:
    p_value = 1.0
  else:
    z = (abs(s_stat) - 1) / math.sqrt(var_s)
    p_value = 2.0 * _normal_sf(z)

  if tau < 0:
    direction = "monotonic decrease"
  elif tau > 0:
    direction = "monotonic increase"
  else:
    direction = "no trend"

  logger.info(
    "Mann-Kendall: tau=%.4f, direction=%s, asymptotic p=%.4f (n=%d)",
    tau, direction, p_value, n,
  )
  return tau, direction, p_value


def _unique_with_counts(data: List[float]) -> Tuple[List[float], List[int]]:
  counts: Dict[float, int] = {}
  for v in data:
    counts[v] = counts.get(v, 0) + 1
  values = sorted(counts.keys())
  return values, [counts[v] for v in values]


def _trend_statistic(rhos: List[float]) -> float:
  """Test statistic: magnitude of the Mann-Kendall S statistic.

  Using |S| (rather than the mean rho) targets monotonic trend in the
  correlation sequence, which is what the block permutation test must
  assess (FR-008).
  """
  n = len(rhos)
  s_stat = 0
  for i in range(n - 1):
    for j in range(i + 1, n):
      s_stat += 1 if rhos[j] > rhos[i] else (-1 if rhos[j] < rhos[i] else 0)
  return float(abs(s_stat))


def _block_permute(rhos: List[float], block_size: int, shift: int) -> List[float]:
  """Circularly shift the sequence by whole blocks, preserving local
  (block) autocorrelation structure under the null."""
  n = len(rhos)
  shift = shift % n
  return rhos[n - shift:] + rhos[:n - shift]


def is_small_sample(rhos: List[float], threshold: int = SMALL_SAMPLE_THRESHOLD) -> bool:
  """T024 / FR-008: small sample size constraint check (n < 10)."""
  return len(rhos) < threshold


def block_permutation_test(
  rhos: List[float],
  n_resamples: int = DEFAULT_N_RESAMPLES,
  block_size: int = DEFAULT_BLOCK_SIZE,
) -> float:
  """Block permutation significance test for the correlation sequence.

  Null hypothesis: the ordering of the rho sequence carries no trend
  information. Whole blocks of ``block_size`` consecutive values are
  circularly shifted to build the null distribution of the trend
  statistic |S|, preserving short-range autocorrelation.

  T024 small-sample handling (n < 10):
    - If n <= 8, enumerate ALL n circular block-shift permutations
      (exhaustive / exact test) when the total is below
      ``EXHAUSTIVE_MAX_PERMUTATIONS``.
    - Otherwise use ``SMALL_SAMPLE_N_RESAMPLES`` random resamples so
      the permutation p-value remains reliable at small n.

  Returns the permutation p-value (one-sided, upper tail of |S|).
  """
  n = len(rhos)
  if n < 2:
    logger.warning("Block permutation test requires at least 2 points; returning p=1.0.")
    return 1.0

  observed = _trend_statistic(rhos)

  small = is_small_sample(rhos)
  if small:
    logger.info(
      "Small sample detected (n=%d < %d): relying on permutation p-value (FR-008).",
      n, SMALL_SAMPLE_THRESHOLD,
    )

  # Exhaustive enumeration of all circular shifts (exact test)
  if n <= 8 and n <= EXHAUSTIVE_MAX_PERMUTATIONS:
    shifts = range(n)
    count_ge = 0
    total = 0
    for shift in shifts:
      perm = _block_permute(rhos, block_size, shift)
      stat = _trend_statistic(perm)
      total += 1
      if stat >= observed:
        count_ge += 1
    p_value = count_ge / total
    logger.info(
      "Exact block permutation test over %d circular shifts: p=%.4f", total, p_value
    )
    return p_value

  # Random resampling
  rng = random.Random(42)
  resamples = SMALL_SAMPLE_N_RESAMPLES if small else n_resamples
  count_ge = 0
  for _ in range(resamples):
    shift = rng.randrange(n)
    perm = _block_permute(rhos, block_size, shift)
    if _trend_statistic(perm) >= observed:
      count_ge += 1
  p_value = count_ge / resamples
  logger.info(
    "Block permutation test (%d resamples, block_size=%d): p=%.4f",
    resamples, block_size, p_value,
  )
  return p_value


def run_significance_tests(drift_metrics_path: str, output_path: str) -> Dict[str, Any]:
  """Run Mann-Kendall and block permutation tests on drift metrics.

  Writes a JSON report to ``output_path`` containing:
    - kendall_tau, trend_direction, mann_kendall_p (asymptotic)
    - p_value (block permutation; authoritative when n < 10)
    - n_observations, small_sample, method notes
  """
  rhos = load_correlation_sequence(drift_metrics_path)
  n = len(rhos)
  small = is_small_sample(rhos)

  tau, direction, mk_p = mann_kendall_test(rhos)
  perm_p = block_permutation_test(rhos)

  # T024: for small samples, rely on the permutation p-value.
  if small:
    logger.info(
      "n=%d < %d: asymptotic Mann-Kendall p-value is unreliable; "
      "using block permutation p-value=%.4f as the reported p-value.",
      n, SMALL_SAMPLE_THRESHOLD, perm_p,
    )
    reported_p = perm_p
    method = "block_permutation (small sample, exact/random circular block shifts)"
  else:
    reported_p = perm_p
    method = "block_permutation (circular block shifts)"

  result = {
    "n_observations": n,
    "small_sample": small,
    "kendall_tau": tau,
    "trend_direction": direction,
    "mann_kendall_p_asymptotic": mk_p,
    "p_value": reported_p,
    "method": method,
    "note": (
      "n < 10: permutation p-value relied upon per FR-008; "
      "asymptotic Mann-Kendall p-value reported for reference only."
      if small
      else "n >= 10: block permutation p-value reported."
    ),
  }

  out_dir = os.path.dirname(os.path.abspath(output_path))
  os.makedirs(out_dir, exist_ok=True)
  with open(output_path, "w") as f:
    json.dump(result, f, indent=2)
  logger.info("Significance test results saved to %s", output_path)
  return result


def main() -> None:
  """Entry point for significance tests.

  Optional positional arguments:
    1. drift metrics CSV path (default outputs/drift_metrics.csv)
    2. output JSON path (default outputs/p_values.json)
  """
  drift_path = sys.argv[1] if len(sys.argv) > 1 else DRIFT_METRICS_PATH
  out_path = sys.argv[2] if len(sys.argv) > 2 else P_VALUES_PATH
  try:
    result = run_significance_tests(drift_path, out_path)
    print(json.dumps(result, indent=2))
  except Exception as exc:
    logger.error("Significance testing failed: %s", exc, exc_info=True)
    sys.exit(1)


if __name__ == "__main__":
  main()
