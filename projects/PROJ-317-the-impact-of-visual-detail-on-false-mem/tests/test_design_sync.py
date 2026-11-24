import pathlib

def test_no_prohibited_phrases():
    """
    Ensure that the repository does not contain the disallowed terms
    “Between‑Subjects” or “One‑Way ANOVA”.
    """
    # Project root is two levels up from this test file (tests/ -> project root)
    root = pathlib.Path(__file__).resolve().parents[2]
    prohibited = ["Between‑Subjects", "One‑Way ANOVA"]
    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        # Limit to text-like files
        if file_path.suffix.lower() not in {".md", ".py", ".txt", ".yaml", ".json", ".csv"}:
            continue
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            # Skip files that cannot be read as text
            continue
        for term in prohibited:
            assert term not in content, f"Prohibited term '{term}' found in {file_path}"

# The test will be automatically discovered and run by pytest.