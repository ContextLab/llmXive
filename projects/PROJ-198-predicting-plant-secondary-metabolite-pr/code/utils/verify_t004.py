import random
import numpy as np
from pathlib import Path
from code.config import load_config, reset_config, get_config
from code.utils.logging import get_logger

def test_reproducibility():
    print("Testing seed reproducibility...")
    
    def get_random_sample():
        return [random.random() for _ in range(5)] + [np.random.random() for _ in range(5)]

    # First run
    reset_config()
    load_config()
    seq1 = get_random_sample()
    
    # Second run
    reset_config()
    load_config()
    seq2 = get_random_sample()
    
    assert seq1 == seq2, f"Sequences not reproducible: {seq1} != {seq2}"
    print("Seed reproducibility verified.")

def test_logging():
    print("Testing logging output...")
    # load_config already triggers a log message
    reset_config()
    load_config()
    
    log_file = Path("logs/run.log")
    assert log_file.exists(), "logs/run.log file was not created"
    
    content = log_file.read_text()
    assert "Configuration loaded" in content, "Log file does not contain the expected 'Configuration loaded' INFO message"
    print("Logging output verified.")

if __name__ == "__main__":
    try:
        test_reproducibility()
        test_logging()
        print("T004 Verification Successful.")
    except Exception as e:
        print(f"T004 Verification Failed: {e}")
        exit(1)