import pathlib
import tomllib


def _load_requirements(path: pathlib.Path) -> list[str]:
    """Read a requirements.txt file and return a list of stripped lines,
    ignoring empty lines and comments."""
    lines = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(stripped)
    return lines


def _load_pyproject_deps(path: pathlib.Path) -> list[str]:
    """Parse pyproject.toml and return the dependencies list in the order
    they appear in the file."""
    data = tomllib.loads(path.read_text())
    deps = data.get("project", {}).get("dependencies", [])
    # Ensure each entry is a simple string like "pkg==x.y.z"
    cleaned = [dep.strip() for dep in deps if isinstance(dep, str)]
    return cleaned


def test_requirements_match_project():
    """
    Verify that the top‑level requirements.txt lists exactly the same
    pinned packages (name and version) as the pyproject.toml [project]
    dependencies, preserving order.
    """
    root = pathlib.Path.cwd()
    req_path = root / "requirements.txt"
    pyproj_path = root / "pyproject.toml"

    req_deps = _load_requirements(req_path)
    pyproj_deps = _load_pyproject_deps(pyproj_path)

    assert req_deps == pyproj_deps, (
        "requirements.txt does not exactly match pyproject.toml dependencies.\\n"
        f"requirements.txt: {req_deps}\\n"
        f"pyproject.toml: {pyproj_deps}"
    )