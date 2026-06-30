"""
Unit tests for the prompt engineering module.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

# Import the module under test
# We need to ensure the code/ directory is in the path if running from tests
import sys
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.generation.prompt_engineering import (
    apply_strategy,
    generate_full_corpus,
    load_base_prompts,
    STRATEGIES,
    STRATEGY_TEMPLATES
)


class TestPromptEngineering(unittest.TestCase):

    def test_apply_strategy_direct(self):
        """Test the Direct strategy template."""
        base = "test scenario"
        result = apply_strategy(base, "Direct")
        self.assertIn("test scenario", result)
        self.assertIn("first-person account", result)

    def test_apply_strategy_hypothetical(self):
        """Test the Hypothetical strategy template."""
        base = "test scenario"
        result = apply_strategy(base, "Hypothetical")
        self.assertIn("test scenario", result)
        self.assertIn("Imagine", result)

    def test_apply_strategy_comparative(self):
        """Test the Comparative strategy template."""
        base = "test scenario"
        result = apply_strategy(base, "Comparative")
        self.assertIn("test scenario", result)
        self.assertIn("compare", result.lower())

    def test_apply_strategy_roleplay(self):
        """Test the Role-play strategy template."""
        base = "test scenario"
        result = apply_strategy(base, "Role-play")
        self.assertIn("test scenario", result)
        self.assertIn("philosopher phenomenologist", result)

    def test_apply_strategy_invalid(self):
        """Test that an invalid strategy raises ValueError."""
        with self.assertRaises(ValueError):
            apply_strategy("test", "InvalidStrategy")

    def test_generate_full_corpus_structure(self):
        """Test the structure of the generated corpus."""
        base_prompts = ["prompt1", "prompt2"]
        strategies = ["Direct", "Role-play"]
        corpus = generate_full_corpus(base_prompts, strategies)

        # Should be 2 base * 2 strategies = 4 items
        self.assertEqual(len(corpus), 4)

        # Check structure of first item
        item = corpus[0]
        self.assertIn("id", item)
        self.assertIn("strategy", item)
        self.assertIn("base_prompt", item)
        self.assertIn("full_prompt", item)

        # Check ID format
        self.assertTrue(item["id"].startswith("Direct_"))

    def test_load_base_prompts_from_file(self):
        """Test loading base prompts from a temporary file."""
        # Create a temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(["p1", "p2", "p3"], f)
            temp_path = f.name

        try:
            # We need to monkey-patch the path or pass it explicitly.
            # The function load_base_prompts has a default arg, but we can pass it.
            # However, the function implementation uses the default if not passed.
            # Let's test by passing the path directly if we modify the call,
            # but the function signature is `load_base_prompts(filepath=...)`.
            # Wait, the function definition is `load_base_prompts(filepath: str = BASE_PROMPTS_PATH)`.
            # So we can pass the temp_path.
            prompts = load_base_prompts(temp_path)
            self.assertEqual(prompts, ["p1", "p2", "p3"])
        finally:
            os.unlink(temp_path)

    def test_corpus_count(self):
        """Verify the corpus size matches expectations (20 base * 4 strategies)."""
        # We can't load the real file in this unit test easily without ensuring the file exists
        # in the test environment. So we simulate with a small set.
        base = [f"p{i}" for i in range(20)]
        corpus = generate_full_corpus(base, STRATEGIES)
        self.assertEqual(len(corpus), 80)


if __name__ == '__main__':
    unittest.main()