"""
Tests for the data retrieval module.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add the project root to the path
sys_path = Path(__file__).parent.parent
if str(sys_path) not in os.sys.path:
    os.sys.path.insert(0, str(sys_path))

from code.data.retrieval import extract_records, write_raw_data


def test_extract_records():
    """Test that extract_records correctly processes API response."""
    # Mock API response
    mock_page_data = {
        'assays': [
            {
                'assay_id': 12345,
                'chembl_id': 'CHEMBL123',
                'organism': {'scientific_name': 'Homo sapiens'},
                'targets': [{'organism': {'scientific_name': 'Homo sapiens'}}],
                'documents': [{'doc_id': 'DOC123'}]
            }
        ]
    }

    # Mock the requests.get call for activities
    mock_activity_response = {
        'activities': [
            {
                'molecule_structures': {'canonical_smiles': 'CCO'},
                'standard_value': -6.5,
                'standard_units': 'logM',
                'standard_type': 'MEASUREMENT',
                'relation': '=',
                'comment': 'Test comment'
            }
        ]
    }

    with patch('code.data.retrieval.requests.get') as mock_get:
        # First call returns assay page, second call returns activities
        mock_get.side_effect = [
            MagicMock(json=lambda: mock_page_data),
            MagicMock(json=lambda: mock_activity_response, raise_for_status=lambda: None)
        ]

        records = extract_records(mock_page_data)

        assert len(records) == 1
        record = records[0]
        assert record['smiles'] == 'CCO'
        assert record['logPapp'] == -6.5
        assert 'protocol_metadata' in record

        # Verify protocol_metadata is a JSON string
        metadata = json.loads(record['protocol_metadata'])
        assert metadata['assay_id'] == '12345'
        assert metadata['standard_type'] == 'MEASUREMENT'


def test_write_raw_data():
    """Test that write_raw_data correctly writes to CSV."""
    records = [
        {
            'smiles': 'CCO',
            'logPapp': -6.5,
            'assay_id': '12345',
            'protocol_metadata': json.dumps({'standard_type': 'MEASUREMENT'})
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'test.csv'
        write_raw_data(records, output_path)

        assert output_path.exists()

        # Read back and verify
        with open(output_path, 'r') as f:
            import csv
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]['smiles'] == 'CCO'
        assert rows[0]['logPapp'] == '-6.5'