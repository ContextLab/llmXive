"""
Unit tests for download_guild_source.py
"""
import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
import csv
import json
import yaml

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from data.download_guild_source import (
    validate_guild_source,
    compute_sha256,
    EXPECTED_CITATION
)

class TestDownloadGuildSource(unittest.TestCase):
    """Test cases for guild source download and validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = Path(self.test_dir) / "guild_source.csv"

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_validate_csv_with_correct_citation(self):
        """Test CSV validation with correct source citation."""
        # Create a valid CSV file
        with open(self.test_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['species_id', 'foraging_guild', 'source_citation'])
            writer.writeheader()
            writer.writerow({
                'species_id': 'A001',
                'foraging_guild': 'Seed-eater',
                'source_citation': f'Birds of the World - Cornell Lab of Ornithology'
            })
        
        # Should not raise
        validate_guild_source(self.test_file)

    def test_validate_csv_missing_citation_field(self):
        """Test CSV validation fails when source_citation field is missing."""
        # Create a CSV without source_citation
        with open(self.test_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['species_id', 'foraging_guild'])
            writer.writeheader()
            writer.writerow({'species_id': 'A001', 'foraging_guild': 'Seed-eater'})
        
        # Should raise ValueError
        with self.assertRaises(ValueError) as context:
            validate_guild_source(self.test_file)
        
        self.assertIn('source_citation', str(context.exception))

    def test_validate_csv_wrong_citation(self):
        """Test CSV validation fails when citation doesn't match expected."""
        # Create a CSV with wrong citation
        with open(self.test_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['species_id', 'foraging_guild', 'source_citation'])
            writer.writeheader()
            writer.writerow({
                'species_id': 'A001',
                'foraging_guild': 'Seed-eater',
                'source_citation': 'Some Other Source'
            })
        
        # Should raise ValueError
        with self.assertRaises(ValueError) as context:
            validate_guild_source(self.test_file)
        
        self.assertIn('Birds of the World', str(context.exception))

    def test_validate_json_with_correct_citation(self):
        """Test JSON validation with correct source citation."""
        json_file = Path(self.test_dir) / "guild_source.json"
        data = [{
            'species_id': 'A001',
            'foraging_guild': 'Seed-eater',
            'source_citation': f'Birds of the World - Cornell Lab of Ornithology'
        }]
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        
        # Should not raise
        validate_guild_source(json_file)

    def test_validate_json_missing_citation(self):
        """Test JSON validation fails when source_citation is missing."""
        json_file = Path(self.test_dir) / "guild_source.json"
        data = [{
            'species_id': 'A001',
            'foraging_guild': 'Seed-eater'
        }]
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        
        # Should raise ValueError
        with self.assertRaises(ValueError) as context:
            validate_guild_source(json_file)
        
        self.assertIn('source_citation', str(context.exception))

    def test_validate_xml_with_correct_citation(self):
        """Test XML validation with correct source citation."""
        xml_file = Path(self.test_dir) / "guild_source.xml"
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <guilds>
            <species>
                <species_id>A001</species_id>
                <foraging_guild>Seed-eater</foraging_guild>
                <source_citation>Birds of the World - Cornell Lab of Ornithology</source_citation>
            </species>
        </guilds>'''
        
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        # Should not raise
        validate_guild_source(xml_file)

    def test_validate_xml_missing_citation(self):
        """Test XML validation fails when source_citation is missing."""
        xml_file = Path(self.test_dir) / "guild_source.xml"
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <guilds>
            <species>
                <species_id>A001</species_id>
                <foraging_guild>Seed-eater</foraging_guild>
            </species>
        </guilds>'''
        
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        # Should raise ValueError
        with self.assertRaises(ValueError) as context:
            validate_guild_source(xml_file)
        
        self.assertIn('source_citation', str(context.exception))

    def test_compute_sha256(self):
        """Test SHA-256 hash computation."""
        # Create a test file
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write("test content")
        
        hash1 = compute_sha256(self.test_file)
        hash2 = compute_sha256(self.test_file)
        
        # Same file should produce same hash
        self.assertEqual(hash1, hash2)
        
        # Hash should be 64 characters (SHA-256 hex)
        self.assertEqual(len(hash1), 64)
        
        # Hash should only contain hex characters
        self.assertTrue(all(c in '0123456789abcdef' for c in hash1))

    def test_validate_file_not_found(self):
        """Test validation fails when file doesn't exist."""
        non_existent = Path(self.test_dir) / "non_existent.csv"
        
        with self.assertRaises(FileNotFoundError):
            validate_guild_source(non_existent)

    def test_validate_empty_csv(self):
        """Test validation fails on empty CSV."""
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write("")
        
        with self.assertRaises(ValueError) as context:
            validate_guild_source(self.test_file)
        
        self.assertIn('no headers', str(context.exception).lower())

if __name__ == '__main__':
    unittest.main()