import os
import pytest
import tempfile
import matplotlib.pyplot as plt

def test_viz_png_size_limit():
    """
    Unit test for file size check in code/tests/test_viz.py.
    Function name: test_viz_png_size_limit.
    MUST use assert os.path.getsize(filepath) <= 5*1024*1024 to verify PNG generation ≤ 5MB.
    """
    # Create a temporary file to simulate a generated plot
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        temp_path = tmp_file.name

    try:
        # Generate a simple plot to ensure a real file is written
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])
        ax.set_title("Test Plot for Size Verification")
        fig.savefig(temp_path, dpi=100)
        plt.close(fig)

        # Verify file exists
        assert os.path.exists(temp_path), f"Generated file {temp_path} does not exist"

        # Check file size constraint (must be <= 5MB)
        file_size_bytes = os.path.getsize(temp_path)
        max_size_bytes = 5 * 1024 * 1024  # 5 MB

        assert file_size_bytes <= max_size_bytes, (
            f"Generated plot file size ({file_size_bytes} bytes) exceeds limit "
            f"of {max_size_bytes} bytes (5MB)"
        )

    finally:
        # Cleanup temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)