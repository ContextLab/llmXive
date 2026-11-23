import subprocess
import pathlib

def test_gitignore_behavior(tmp_path):
    # Ensure the repository root contains the .gitignore we created.
    repo_root = pathlib.Path(__file__).parents[2]  # project root
    gitignore = repo_root / ".gitignore"
    assert gitignore.is_file(), ".gitignore file missing"

    # Test that a file under data/raw is ignored.
    result = subprocess.run(
        ["git", "check-ignore", "-v", "data/raw/snps_raw.vcf.gz"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, "data/raw/snps_raw.vcf.gz should be ignored"

    # Test that source_log.txt is NOT ignored.
    result2 = subprocess.run(
        ["git", "check-ignore", "-v", "data/raw/source_log.txt"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert result2.returncode != 0, "data/raw/source_log.txt should NOT be ignored"