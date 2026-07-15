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


def _write(p: Path, code: str = "", summary: str | None = None,
           idea: str | None = None) -> Path:
    (p / "code").mkdir(parents=True, exist_ok=True)
    (p / "data").mkdir(parents=True, exist_ok=True)
    if code:
        (p / "code" / "run.py").write_text(code, encoding="utf-8")
    if summary is not None:
        (p / "data" / "summary.json").write_text(summary, encoding="utf-8")
    if idea is not None:
        (p / "idea").mkdir(parents=True, exist_ok=True)
        (p / "idea" / "idea.md").write_text(idea, encoding="utf-8")
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


def test_unauthorized_synthetic_input_data_is_flagged(tmp_path: Path) -> None:
    """Synthetic INPUT data is NOT acceptable unless the project EXPLICITLY
    requires it: a real-world-insight project that substitutes fake data for the
    real dataset produces results that are not real. The project's idea here says
    nothing about synthetic data, so it is flagged (even though a real statistic
    is computed ON the fake data)."""
    code = (
        "import numpy as np, pandas as pd\n"
        "# synthetic sampled input data (real dataset unavailable)\n"
        "X = np.random.randn(200, 3)\n"
        "mean_norm = float(np.linalg.norm(X, axis=1).mean())\n"
        "pd.DataFrame([{'mean_norm': mean_norm}]).to_csv('data/out.csv')\n"
    )
    findings = find_fabrication(_write(tmp_path / "p", code=code))
    assert any("synthetic" in f.lower() for f in findings), (
        f"unauthorized synthetic input must be flagged; got {findings}"
    )


def test_synthetic_input_data_authorized_by_idea_is_clean(tmp_path: Path) -> None:
    """When the project's OWN research idea is about synthetic data (a simulation
    study / synthetic benchmark), synthetic input IS the design — not flagged."""
    code = (
        "import numpy as np, pandas as pd\n"
        "# synthetic data is the subject of this study\n"
        "X = np.random.randn(200, 3)\n"
        "mean_norm = float(np.linalg.norm(X, axis=1).mean())\n"
        "pd.DataFrame([{'mean_norm': mean_norm}]).to_csv('data/out.csv')\n"
    )
    idea = "We study estimator behavior on synthetic data generated under a known model.\n"
    findings = find_fabrication(_write(tmp_path / "p", code=code, idea=idea))
    assert findings == [], f"idea-authorized synthetic data must be clean; got {findings}"


def test_negated_synthetic_mention_is_not_flagged(tmp_path: Path) -> None:
    """A comment that says the code AVOIDS fabrication must not be read AS
    fabrication. These two lines are verbatim from live projects the gate wrongly
    blocked (PROJ-306, PROJ-606): the code is doing exactly the right thing —
    refusing synthetic data — and got flagged for naming it."""
    for line in (
        "# If not present, we skip to avoid fake data.",
        "# using real data (the paper text) rather than synthetic data.",
        "# do NOT fall back to synthetic data; require the real dataset.",
        "# no synthetic data is generated anywhere in this pipeline.",
    ):
        code = (
            "import pandas as pd\n"
            f"{line}\n"
            "df = pd.read_csv('data/raw/real.csv')\n"
            "df.describe().to_json('data/out.json')\n"
        )
        findings = find_fabrication(_write(tmp_path / f"p{hash(line) & 0xffff}", code=code))
        assert not any("synthetic" in f.lower() for f in findings), (
            f"code REFUSING fabrication was flagged as fabrication; line={line!r} "
            f"findings={findings}"
        )


def test_real_synthetic_generation_still_flagged_despite_nearby_negation(tmp_path: Path) -> None:
    """The negation guard must be TIGHT: it clears only a negation IMMEDIATELY before
    the phrase. A sentence that avoids the REAL dataset and then generates synthetic
    (PROJ-636's README pattern) is still real fabrication and must stay flagged."""
    code = (
        "import numpy as np, pandas as pd\n"
        "# Instead of the 138M-sample real dataset, we generate 200 synthetic rows.\n"
        "X = np.random.randn(200, 3)\n"
        "pd.DataFrame(X).to_csv('data/out.csv')\n"
    )
    findings = find_fabrication(_write(tmp_path / "pgen", code=code))
    assert any("synthetic" in f.lower() for f in findings), (
        f"genuine synthetic generation must stay flagged; got {findings}"
    )


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


def test_venv_and_test_code_are_not_scanned(tmp_path: Path) -> None:
    """The fabrication scan must NOT recurse into installed deps (code/.venv/
    site-packages) or test code — third-party docstrings ('tries to simulate the
    result') and test fixtures (synthetic data for unit tests) are NOT a fabricated
    RESEARCH result. Scanning them produced 143 false positives from a single venv
    that wrongly failed the execution gate for nearly every project."""
    p = tmp_path / "proj"
    (p / "code").mkdir(parents=True)
    # honest real analysis
    (p / "code" / "run.py").write_text(
        "import pandas as pd\n"
        "df = pd.read_csv('data/raw.csv')\n"
        "corr = df['x'].corr(df['y'])\n", encoding="utf-8")
    # installed dependency with fabrication language in a docstring
    site = p / "code" / ".venv" / "lib" / "python3.11" / "site-packages" / "PIL"
    site.mkdir(parents=True)
    (site / "ImageCms.py").write_text(
        '"""tries to simulate the result that would be obtained."""\n', encoding="utf-8")
    # a unit test using synthetic fixtures
    (p / "code" / "tests").mkdir()
    (p / "code" / "tests" / "test_run.py").write_text(
        "import numpy as np\n# synthetic data for the unit test\nX = np.random.randn(5, 3)\n",
        encoding="utf-8")
    assert find_fabrication(p) == []
