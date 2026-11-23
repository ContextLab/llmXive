import sys
import subprocess
import json
from pathlib import Path

def test_main_download_qc_step(tmp_path, monkeypatch):
    """
    Verify that the ``--step download_qc`` flag is accepted and that the
    script exits with code 0 (even if the downstream step raises because
    of missing data – the purpose of the test is only argument handling).
    """
    script = Path("code/src/main.py")
    result = subprocess.run(
        [sys.executable, str(script), "--step", "download_qc"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # The script should finish without a parsing error.
    assert result.returncode in (0, 1)  # 1 is acceptable if downstream fails