import tempfile
from pathlib import Path

import pytest

from src.features import calculate_gc_content

def write_fasta(seq: str, file_path: Path):
    """Utility to write a minimal FASTA file."""
    with open(file_path, "w") as f:
        f.write(f">test_seq\\n{seq}\\n")

@pytest.mark.parametrize(
    "sequence,expected",
    [
        # 50% GC overall, first half 40% GC, second half 60% GC
        (
            "ATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGC",  # 80 bases
            {"gc_global": 0.5, "gc_first_half": 0.4, "gc_second_half": 0.6},
        ),
        # All AT (0% GC)
        ("ATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATAT",  # 80 bases
         {"gc_global": 0.0, "gc_first_half": 0.0, "gc_second_half": 0.0}),
        # All GC (100% GC)
        ("GCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGC",  # 80 bases
         {"gc_global": 1.0, "gc_first_half": 1.0, "gc_second_half": 1.0}),
    ],
)
def test_calculate_gc_content(sequence, expected):
    with tempfile.TemporaryDirectory() as tmpdir:
        fasta_path = Path(tmpdir) / "test.fa"
        write_fasta(sequence, fasta_path)

        result = calculate_gc_content(str(fasta_path))

        # Compare each metric with a tolerance for floating point rounding
        for key, exp_val in expected.items():
            assert pytest.approx(result[key], rel=1e-3) == exp_val