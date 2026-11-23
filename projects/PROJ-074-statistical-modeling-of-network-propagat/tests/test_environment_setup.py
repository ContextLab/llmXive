"""Tests for T002: project initialization and dependency installation.

These tests verify (a) that the pinned dependency set is consistent
between ``requirements.txt`` and ``pyproject.toml``, and (b) that the
required scientific stack, including numpyro, actually imports in the
project environment.
"""

import importlib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _parse_requirements(path: Path):
    pinned = {}
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if "==" in line:
            name, _, version = line.partition("==")
            pinned[name.strip()] = version.strip()
    return pinned


def test_requirements_file_exists():
    assert (PROJECT_ROOT / "requirements.txt").is_file()


def test_pyproject_exists():
    assert (PROJECT_ROOT / "pyproject.toml").is_file()


def test_requirements_and_pyproject_are_consistent():
    import tomllib

    requirements = _parse_requirements(PROJECT_ROOT / "requirements.txt")
    pyproject = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text()
    )
    pyproject_deps = {}
    for dep in pyproject["project"]["dependencies"]:
        name, _, version = dep.partition("==")
        pyproject_deps[name.strip()] = version.strip()
    assert requirements == pyproject_deps


def test_key_dependencies_pinned():
    requirements = _parse_requirements(PROJECT_ROOT / "requirements.txt")
    for pkg in [
        "numpy",
        "pandas",
        "numpyro",
        "jax",
        "jaxlib",
        "networkx",
        "scikit-learn",
    ]:
        assert pkg in requirements, f"{pkg} missing from requirements.txt"
        assert requirements[pkg], f"{pkg} is not pinned to a version"


@pytest.mark.parametrize(
    "module",
    [
        "numpy",
        "pandas",
        "numpyro",
        "jax",
        "networkx",
        "sklearn",
        "yaml",
        "jsonschema",
    ],
)
def test_required_packages_import(module):
    importlib.import_module(module)


def test_numpyro_smoke_test():
    """The previously failing numpyro import chain must now work."""
    import jax.numpy as jnp
    import numpyro
    import numpyro.distributions as dist

    with numpyro.handlers.seed(rng_seed=0):
      numpyro.sample("x", dist.Bernoulli(0.5), obs=jnp.array([1.0]))