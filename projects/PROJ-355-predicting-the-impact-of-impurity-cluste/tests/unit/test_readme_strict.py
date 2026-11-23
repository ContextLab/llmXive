import pathlib

def test_readme_strict():
    """
    Verify that README.md contains the required headings in order,
    the exact execution command, and the required phrases in the
    Data Provenance paragraph.
    """
    # Project root is two levels up from this test file
    project_root = pathlib.Path(__file__).resolve().parents[2]
    readme_path = project_root / "README.md"

    assert readme_path.is_file(), "README.md not found at project root"

    # Load lines, stripping trailing newlines but keeping empty lines for heading detection
    lines = [ln.rstrip("\n") for ln in readme_path.read_text().splitlines()]

    # Expected headings in exact order
    expected_headings = [
        "# Predicting the Impact of Impurity Clustering on Grain Boundary Segregation",
        "## Execution",
        "## Data Provenance",
        "## Research Question",
    ]

    # Verify headings appear in order
    heading_idx = 0
    for line in lines:
        if line == expected_headings[heading_idx]:
            heading_idx += 1
            if heading_idx == len(expected_headings):
                break
    assert heading_idx == len(expected_headings), "Required headings not found in the correct order"

    # Verify the exact execution command line exists
    exec_command = "python -m code.main"
    assert any(line.strip() == exec_command for line in lines), (
        f"Execution command line '{exec_command}' not found in README.md"
    )

    # Locate the Data Provenance paragraph (text between its heading and the next heading)
    try:
        prov_start = lines.index("## Data Provenance")
    except ValueError:
        raise AssertionError("Data Provenance heading missing")
    # Collect paragraph lines until the next heading or end of file
    paragraph_parts = []
    for line in lines[prov_start + 1:]:
        if line.startswith("## "):
            break
        paragraph_parts.append(line.strip())
    paragraph = " ".join(paragraph_parts)

    # Required phrases in the Data Provenance paragraph
    required_phrases = [
        "OQMD loader",
        "Materials‑Project waiver",
        "data/raw/",
    ]
    for phrase in required_phrases:
        assert phrase in paragraph, f"Data Provenance paragraph missing required phrase: '{phrase}'"