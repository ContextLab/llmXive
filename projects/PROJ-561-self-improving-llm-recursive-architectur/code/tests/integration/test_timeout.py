import unittest
import subprocess
import os
import sys
import tempfile
import shutil
import json
import time
from pathlib import Path

class TestTimeoutEnforcement(unittest.TestCase):
    """Integration tests for timeout enforcement in training cycles."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.results_dir = os.path.join(self.test_dir, "results")
        self.logs_dir = os.path.join(self.results_dir, "logs")
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Create a mock config
        self.config_path = os.path.join(self.test_dir, "config_test.py")
        with open(self.config_path, "w") as f:
            f.write("""
import os
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Hyperparameters:
    learning_rate: float = 5e-5
    batch_size: int = 4
    seed: int = 42

@dataclass
class SafetyConstraints:
    max_param_increase: float = 0.3

@dataclass
class PathConfig:
    data_dir: str = "data"
    results_dir: str = "results"
    checkpoints_dir: str = "data/checkpoints"
    logs_dir: str = "results/logs"

@dataclass
class Config:
    hyperparameters: Hyperparameters
    safety: SafetyConstraints
    paths: PathConfig

def get_config():
    return Config(
  hyperparameters=Hyperparameters(),
  safety=SafetyConstraints(),
  paths=PathConfig()
    )

def get_trajectory_path():
    return os.path.join(get_config().paths.results_dir, "trajectory.json")

def ensure_directories():
    config = get_config()
    os.makedirs(config.paths.data_dir, exist_ok=True)
    os.makedirs(config.paths.results_dir, exist_ok=True)
    os.makedirs(config.paths.checkpoints_dir, exist_ok=True)
    os.makedirs(config.paths.logs_dir, exist_ok=True)
""")

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_timeout_creates_log_and_records_metrics(self):
        """Test that timeout creates log file and records partial metrics."""
        # Create a test script that simulates a timeout
        test_script = os.path.join(self.test_dir, "timeout_test.py")
        
        with open(test_script, "w") as f:
            f.write(f"""
import sys
import os
import time
import signal

# Add test dir to path
sys.path.insert(0, '{self.test_dir}')
sys.path.insert(0, 'code')

# Mock config
import config_test as config
sys.modules['config'] = config

# Mock utils.logging
class MockLogger:
    def info(self, msg): pass
    def error(self, msg): pass
    def warning(self, msg): pass

def get_log_path(cycle_num):
    return '{self.logs_dir}/cycle_{cycle_num}.log'

def init_cycle_logger(path):
    return MockLogger()

def log_error(path, msg):
    with open(path, 'a') as f:
  f.write(f"ERROR: {{msg}}\\n")

def log_warning(path, msg):
    with open(path, 'a') as f:
  f.write(f"WARNING: {{msg}}\\n")

sys.modules['utils'] = type(sys)('utils')
sys.modules['utils.logging'] = type(sys)('utils.logging')
sys.modules['utils.logging'].get_log_path = get_log_path
sys.modules['utils.logging'].init_cycle_logger = init_cycle_logger
sys.modules['utils.logging'].log_error = log_error
sys.modules['utils.logging'].log_warning = log_warning

# Mock results.trajectory_schema
class MockTrajectoryEntry:
    def __init__(self, **kwargs):
  self.__dict__.update(kwargs)

def write_trajectory(entry):
    trajectory_path = '{self.results_dir}/trajectory.json'
    with open(trajectory_path, 'a') as f:
  import json
  f.write(json.dumps(entry.__dict__) + '\\n')

sys.modules['results'] = type(sys)('results')
sys.modules['results.trajectory_schema'] = type(sys)('results.trajectory_schema')
sys.modules['results.trajectory_schema'].TrajectoryEntry = MockTrajectoryEntry
sys.modules['results.trajectory_schema'].write_trajectory = write_trajectory

# Import the trainer module
from pipeline.trainer import run_training_cycle_with_timeout, TimeoutError
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

# Create a simple model
class SlowModel(nn.Module):
    def __init__(self):
  super().__init__()
  self.linear = nn.Linear(10, 10)
    
    def forward(self, x):
  # Simulate slow computation
  time.sleep(2)  # Each forward pass takes 2 seconds
  return self.linear(x)

model = SlowModel()

# Create dummy data
data = TensorDataset(torch.randn(100, 10))
loader = DataLoader(data, batch_size=10)

# Run with very short timeout (should trigger timeout)
try:
    metrics, success = run_training_cycle_with_timeout(
  cycle_number=1,
  model=model,
  train_loader=loader,
  max_time_seconds=3,  # 3 second timeout
  device="cpu"
    )
    
    # Check that log file was created
    log_path = get_log_path(1)
    assert os.path.exists(log_path), f"Log file not created at {{log_path}}"
    
    with open(log_path, 'r') as f:
  log_content = f.read()
  assert "Timeout" in log_content, f"Timeout not logged in {{log_path}}"
    
    # Check that trajectory was updated
    trajectory_path = '{self.results_dir}/trajectory.json'
    assert os.path.exists(trajectory_path), f"Trajectory file not created at {{trajectory_path}}"
    
    with open(trajectory_path, 'r') as f:
  lines = f.readlines()
  assert len(lines) > 0, "No entries in trajectory file"
    
    print("SUCCESS: Timeout enforcement working correctly")
    
except Exception as e:
    print(f"ERROR: {{e}}")
    sys.exit(1)
""")

        # Run the test script with subprocess timeout
        result = subprocess.run(
            [sys.executable, test_script],
            timeout=10,  # Give it 10 seconds to complete
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        # Check output
        self.assertIn("SUCCESS", result.stdout, f"Test failed: {result.stdout} {result.stderr}")
        
        # Verify log file exists and contains "Timeout"
        log_path = os.path.join(self.logs_dir, "cycle_1.log")
        self.assertTrue(os.path.exists(log_path), "Log file was not created")
        
        with open(log_path, 'r') as f:
            log_content = f.read()
            self.assertIn("Timeout", log_content, "Timeout message not found in log")
        
        # Verify trajectory file exists
        trajectory_path = os.path.join(self.results_dir, "trajectory.json")
        self.assertTrue(os.path.exists(trajectory_path), "Trajectory file was not created")

    def test_normal_completion_without_timeout(self):
        """Test that normal completion works without timeout."""
        test_script = os.path.join(self.test_dir, "normal_test.py")
        
        with open(test_script, "w") as f:
            f.write(f"""
import sys
import os
import time
import signal

sys.path.insert(0, '{self.test_dir}')
sys.path.insert(0, 'code')

import config_test as config
sys.modules['config'] = config

class MockLogger:
    def info(self, msg): pass
    def error(self, msg): pass
    def warning(self, msg): pass

def get_log_path(cycle_num):
    return '{self.logs_dir}/cycle_{cycle_num}.log'

def init_cycle_logger(path):
    return MockLogger()

def log_error(path, msg):
    with open(path, 'a') as f:
  f.write(f"ERROR: {{msg}}\\n")

def log_warning(path, msg):
    with open(path, 'a') as f:
  f.write(f"WARNING: {{msg}}\\n")

sys.modules['utils'] = type(sys)('utils')
sys.modules['utils.logging'] = type(sys)('utils.logging')
sys.modules['utils.logging'].get_log_path = get_log_path
sys.modules['utils.logging'].init_cycle_logger = init_cycle_logger
sys.modules['utils.logging'].log_error = log_error
sys.modules['utils.logging'].log_warning = log_warning

class MockTrajectoryEntry:
    def __init__(self, **kwargs):
  self.__dict__.update(kwargs)

def write_trajectory(entry):
    trajectory_path = '{self.results_dir}/trajectory.json'
    with open(trajectory_path, 'a') as f:
  import json
  f.write(json.dumps(entry.__dict__) + '\\n')

sys.modules['results'] = type(sys)('results')
sys.modules['results.trajectory_schema'] = type(sys)('results.trajectory_schema')
sys.modules['results.trajectory_schema'].TrajectoryEntry = MockTrajectoryEntry
sys.modules['results.trajectory_schema'].write_trajectory = write_trajectory

from pipeline.trainer import run_training_cycle_with_timeout
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

class FastModel(nn.Module):
    def __init__(self):
  super().__init__()
  self.linear = nn.Linear(10, 10)
    
    def forward(self, x):
  return self.linear(x)

model = FastModel()
data = TensorDataset(torch.randn(10, 10))
loader = DataLoader(data, batch_size=10)

metrics, success = run_training_cycle_with_timeout(
    cycle_number=2,
    model=model,
    train_loader=loader,
    max_time_seconds=30,
    device="cpu"
)

assert success, "Training should complete successfully"
assert os.path.exists(get_log_path(2)), "Log file should exist"

with open(get_log_path(2), 'r') as f:
    content = f.read()
    assert "completed successfully" in content, "Success message not in log"

print("SUCCESS: Normal completion working")
""")

        result = subprocess.run(
            [sys.executable, test_script],
            timeout=30,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        self.assertIn("SUCCESS", result.stdout, f"Test failed: {result.stdout} {result.stderr}")
        
        log_path = os.path.join(self.logs_dir, "cycle_2.log")
        self.assertTrue(os.path.exists(log_path), "Log file was not created for normal run")