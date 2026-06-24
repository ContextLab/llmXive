"""
Integration test for the QM9 download pipeline.

The test verifies that:
1. The ``download_qm9`` function completes without error.
2. The output directory exists and contains at least one file.
3. The memory consumption increase of the process during the download is
   below the 8 GB threshold defined in the specification.
"""

import os
import tempfile

import psutil
import pytest

# Import the function under test.  The project’s ``code`` directory is a
# package (it contains an ``__init__`` file), so a normal import works.
from code.data.download_qm9 import download_qm9


@pytest.mark.integration
def test_qm9_download_pipeline_memory_profile():
    """Run the QM9 download and assert memory stays under 8 GB."""
    # Use a temporary directory to avoid polluting the repository.
    with tempfile.TemporaryDirectory() as tmp_dir:
        proc = psutil.Process()
        mem_before = proc.memory_info().rss

        # Execute the download routine.
        out_dir = download_qm9(tmp_dir)

        mem_after = proc.memory_info().rss
        mem_delta = mem_after - mem_before

        # 1. Output directory must exist.
        assert os.path.isdir(out_dir), f"Output directory {out_dir} was not created."

        # 2. The directory should contain at least one file (the Arrow dataset).
        files = os.listdir(out_dir)
        assert len(files) > 0, "Downloaded dataset directory is empty."

        # 3. Memory increase must be less than 8 GB.
        max_allowed = 8 * 1024 ** 3  # 8 GiB in bytes
        assert mem_delta < max_allowed, (
            f"Memory usage increased by {mem_delta / (1024 ** 3):.2f} GiB, "
            f"exceeding the 8 GiB limit."
        )
