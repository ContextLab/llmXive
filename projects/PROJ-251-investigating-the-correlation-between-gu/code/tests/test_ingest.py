"""
Placeholder for Ingest Tests.
"""
import os
import unittest
import yaml
import pandas as pd
from pathlib import Path
from code.utils.validators import validate_dataset_schema

class TestIngest(unittest.TestCase):
    def test_validate_schema_loads_yaml(self):
        pass

    def test_filter_excludes_null_titers(self):
        pass

if __name__ == "__main__":
    unittest.main()
