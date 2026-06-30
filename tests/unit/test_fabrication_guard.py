"""Deterministic anti-fabrication gate (PROJ-604).

A project whose analysis RUNS and writes real files but whose reported numbers are
fabricated (random.* as a metric, tautological constants, or self-declared
"simulated metrics") must FAIL the execution gate — not reach research_complete.
These tests pin the detector's behavior AND its precision (no false positives on
honest real analysis, on synthetic INPUT data, or on legitimate randomness).
"""

from __future__ import annotations

from pathlib import Path

from llmxive.execution.fabrication_guard import (
    find_fabrication,
    scan_text_for_fabrication,
)


def _write(p: Path, code: str = "", summary: str | None = None) -> Path:
    (p / "code").mkdir(parents=True, exist_ok=True)
    (p / "data").mkdir(parents=True, exist_ok=True)
    if code:
        (p / "code" / "run.py").write_text(code, encoding="utf-8")
    if summary is not None:
        (p / "data" / "summary.json").write_text(summary, encoding="utf-8")
    return p


def test_random_as_metric_is_flagged(tmp_path: Path) -> None:
    """PROJ-604's core pattern: a reported metric drawn straight from random.*."""
    code = (
        "import random\n"
        "def simulate_gemm_throughput(dtype):\n"
        "    return random.uniform(1.6, 2.3)  # tuned to the paper's 2.15x claim\n"
        "speedup = simulate_gemm_throughput('fp4')\n"
        "import pandas as pd\n"
        "pd.DataFrame([{'speedup': speedup}]).to_csv('data/r.csv')\n"
    )
    findings = find_fabrication(_write(tmp_path / "p", code=code))
    assert findings, "random-as-metric must be flagged"
    assert any("simulate_gemm_throughput" in f and "RNG" in f for f in findings)
    assert any("`speedup`" in f for f in findings)  # metric assigned from RNG


def test_self_declared_simulated_metrics_in_results_is_flagged(tmp_path: Path) -> None:
    summary = '{"experiment_type": "NVFP4 Simulation", "constraints": "CPU-only, simulated metrics"}'
    findings = find_fabrication(_write(tmp_path / "p", code="x = 1\n", summary=summary))
    assert any("simulated metric" in f.lower() for f in findings)


def test_arbitrary_scaling_comment_is_flagged(tmp_path: Path) -> None:
    code = "t = (mem / 1e6) * 1000  # Arbitrary scaling to ms\n"
    findings = find_fabrication(_write(tmp_path / "p", code=code))
    assert any("arbitrary" in f.lower() for f in findings)


def test_honest_real_analysis_is_clean(tmp_path: Path) -> None:
    """A real computation over real data with no fabrication language: NO findings."""
    code = (
        "import pandas as pd, numpy as np\n"
        "df = pd.read_csv('data/raw.csv')\n"
        "corr = float(np.corrcoef(df['x'], df['y'])[0, 1])\n"
        "pd.DataFrame([{'correlation': corr}]).to_csv('data/out.csv')\n"
    )
    assert find_fabrication(_write(tmp_path / "p", code=code)) == []


def test_synthetic_INPUT_data_and_real_computation_is_clean(tmp_path: Path) -> None:
    """Generating a small synthetic INPUT and then really computing a statistic on
    it is allowed — only a metric drawn DIRECTLY from RNG is fabrication."""
    code = (
        "import numpy as np, pandas as pd\n"
        "# synthetic sampled input data (real dataset unavailable)\n"
        "X = np.random.randn(200, 3)\n"
        "mean_norm = float(np.linalg.norm(X, axis=1).mean())\n"
        "pd.DataFrame([{'mean_norm': mean_norm}]).to_csv('data/out.csv')\n"
    )
    findings = find_fabrication(_write(tmp_path / "p", code=code))
    assert findings == [], f"synthetic input + real compute must be clean; got {findings}"


def test_legit_bootstrap_randomness_is_clean(tmp_path: Path) -> None:
    """A bootstrap resample (legit statistical randomness) is not fabrication: the
    reported number is computed FROM real data, not drawn from RNG."""
    code = (
        "import numpy as np, pandas as pd\n"
        "data = pd.read_csv('data/raw.csv')['v'].values\n"
        "boot = [np.mean(np.random.choice(data, size=len(data), replace=True)) for _ in range(100)]\n"
        "ci_low = float(np.percentile(boot, 2.5))\n"
        "pd.DataFrame([{'ci_low': ci_low}]).to_csv('data/out.csv')\n"
    )
    # ci_low is computed over real data; no metric variable is assigned a bare RNG draw.
    assert find_fabrication(_write(tmp_path / "p", code=code)) == []


def test_text_scan_catches_simulation_intent_in_a_plan(tmp_path: Path) -> None:
    """The same detector applies to earlier-stage prose: a plan that declares it
    will simulate the metrics is caught deterministically before implementation."""
    plan = (
        "## Method\nSince we cannot run the actual CUDA kernels on CI, we will "
        "simulate the speedup metric using a representative range.\n"
    )
    assert scan_text_for_fabrication(plan, source="plan.md")
