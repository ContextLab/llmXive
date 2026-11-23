import unittest
import yaml
import os

class TestConfigSchema(unittest.TestCase):
    """Validate that ``code/config.yaml`` conforms to the expected schema."""

    def setUp(self):
        self.config_path = os.path.join(os.path.dirname(__file__), "..", "..", "code", "config.yaml")
        with open(self.config_path, "r") as f:
            self.cfg = yaml.safe_load(f)

    def test_required_keys_exist(self):
        required_keys = {
            "topology_counts",
            "max_attempts",
            "target_count",
            "timeout_limits",
            "stiffness_range",
            "max_iterations",
            "seed",
            "trial_count",
            "sim_fps",
            "target_zone",
            "baseline_model_url",
            "MAX_TASKS",
        }
        missing = required_keys - set(self.cfg.keys())
        self.assertFalse(missing, f"Missing required config keys: {missing}")

    def test_key_types(self):
        self.assertIsInstance(self.cfg["topology_counts"], list)
        self.assertTrue(all(isinstance(v, int) for v in self.cfg["topology_counts"]))
        self.assertIsInstance(self.cfg["max_attempts"], int)
        self.assertIsInstance(self.cfg["target_count"], int)
        self.assertIsInstance(self.cfg["timeout_limits"], (int, float))
        self.assertIsInstance(self.cfg["stiffness_range"], list)
        self.assertTrue(all(isinstance(v, (int, float)) for v in self.cfg["stiffness_range"]))
        self.assertIsInstance(self.cfg["max_iterations"], int)
        self.assertIsInstance(self.cfg["seed"], int)
        self.assertIsInstance(self.cfg["trial_count"], int)
        self.assertIsInstance(self.cfg["sim_fps"], int)
        self.assertIsInstance(self.cfg["target_zone"], dict)
        self.assertIsInstance(self.cfg["target_zone"]["center"], list)
        self.assertTrue(all(isinstance(v, (int, float)) for v in self.cfg["target_zone"]["center"]))
        self.assertIsInstance(self.cfg["target_zone"]["radius"], (int, float))
        self.assertIsInstance(self.cfg["baseline_model_url"], str)
        self.assertIsInstance(self.cfg["MAX_TASKS"], int)

if __name__ == "__main__":
    unittest.main()