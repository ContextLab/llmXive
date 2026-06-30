"""
Unit tests for stimulus metadata generation.
"""
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from code.stimuli.metadata import (
    StimulusMetadata,
    ManipulationRecord,
    generate_metadata_for_image,
    save_metadata_as_yaml,
    load_metadata_from_yaml
)
from code.data.image import Image


class TestManipulationRecord:
    """Tests for the ManipulationRecord dataclass."""

    def test_create_enhanced_record(self):
        """Test creating an enhanced manipulation record."""
        record = ManipulationRecord(
            type='enhanced',
            parameters={'objects_added': 5, 'blur_radius': 0},
            complexity_delta=0.15,
            object_count=5
        )
        
        assert record.type == 'enhanced'
        assert record.parameters['objects_added'] == 5
        assert record.complexity_delta == 0.15
        assert record.object_count == 5
        assert isinstance(record.timestamp, str)

    def test_create_reduced_record(self):
        """Test creating a reduced manipulation record."""
        record = ManipulationRecord(
            type='reduced',
            parameters={'blur_radius': 5, 'objects_removed': 3},
            complexity_delta=-0.10,
            object_count=3
        )
        
        assert record.type == 'reduced'
        assert record.parameters['blur_radius'] == 5
        assert record.complexity_delta == -0.10
        assert record.object_count == 3

    def test_to_dict(self):
        """Test conversion to dictionary."""
        record = ManipulationRecord(
            type='enhanced',
            parameters={'test': 'value'},
            complexity_delta=0.05,
            object_count=2
        )
        
        d = record.__dict__
        assert d['type'] == 'enhanced'
        assert d['parameters'] == {'test': 'value'}
        assert d['complexity_delta'] == 0.05
        assert d['object_count'] == 2
        assert 'timestamp' in d


class TestStimulusMetadata:
    """Tests for the StimulusMetadata dataclass."""

    def test_create_basic_metadata(self):
        """Test creating basic metadata without manipulations."""
        metadata = StimulusMetadata(
            original_image_id='img_001',
            original_image_path='/path/to/img.png',
            baseline_complexity_score=0.5
        )
        
        assert metadata.original_image_id == 'img_001'
        assert metadata.manipulations == []
        assert metadata.baseline_complexity_score == 0.5
        assert metadata.generated_at is not None

    def test_add_manipulations(self):
        """Test adding manipulation records."""
        metadata = StimulusMetadata(
            original_image_id='img_001',
            original_image_path='/path/to/img.png',
            baseline_complexity_score=0.5
        )
        
        enhanced = ManipulationRecord(
            type='enhanced',
            parameters={'objects': 5}
        )
        reduced = ManipulationRecord(
            type='reduced',
            parameters={'blur': 5}
        )
        
        metadata.manipulations.append(enhanced)
        metadata.manipulations.append(reduced)
        
        assert len(metadata.manipulations) == 2
        assert metadata.manipulations[0].type == 'enhanced'
        assert metadata.manipulations[1].type == 'reduced'

    def test_to_dict(self):
        """Test conversion to dictionary."""
        metadata = StimulusMetadata(
            original_image_id='img_001',
            original_image_path='/path/to/img.png',
            baseline_complexity_score=0.5,
            checksum='abc123',
            notes='Test note'
        )
        
        d = metadata.to_dict()
        assert d['original_image_id'] == 'img_001'
        assert d['baseline_complexity_score'] == 0.5
        assert d['checksum'] == 'abc123'
        assert d['notes'] == 'Test note'
        assert 'manipulations' in d
        assert 'generated_at' in d


class TestGenerateMetadataForImage:
    """Tests for the generate_metadata_for_image function."""

    def test_generate_with_both_manipulations(self):
        """Test metadata generation with both enhanced and reduced images."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create dummy image files
            original = tmp_path / 'original.png'
            enhanced = tmp_path / 'enhanced.png'
            reduced = tmp_path / 'reduced.png'
            
            original.touch()
            enhanced.touch()
            reduced.touch()
            
            original_image = Image(
                id='img_001',
                path=original,
                complexity_score=0.5
            )
            
            metadata = generate_metadata_for_image(
                original_image=original_image,
                enhanced_path=enhanced,
                reduced_path=reduced,
                enhanced_params={'objects': 5},
                reduced_params={'blur': 5},
                enhanced_complexity=0.65,
                reduced_complexity=0.35,
                enhanced_objects=5,
                reduced_objects=3,
                checksum='sha256_abc123',
                notes='Test generation'
            )
            
            assert metadata.original_image_id == 'img_001'
            assert metadata.baseline_complexity_score == 0.5
            assert len(metadata.manipulations) == 2
            
            # Check enhanced manipulation
            enh_record = next(m for m in metadata.manipulations if m.type == 'enhanced')
            assert enh_record.parameters['objects'] == 5
            assert enh_record.complexity_delta == pytest.approx(0.15)
            assert enh_record.object_count == 5
            
            # Check reduced manipulation
            red_record = next(m for m in metadata.manipulations if m.type == 'reduced')
            assert red_record.parameters['blur'] == 5
            assert red_record.complexity_delta == pytest.approx(-0.15)
            assert red_record.object_count == 3

    def test_generate_with_only_enhanced(self):
        """Test metadata generation with only enhanced image."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            original = tmp_path / 'original.png'
            enhanced = tmp_path / 'enhanced.png'
            
            original.touch()
            enhanced.touch()
            
            original_image = Image(
                id='img_002',
                path=original,
                complexity_score=0.4
            )
            
            metadata = generate_metadata_for_image(
                original_image=original_image,
                enhanced_path=enhanced,
                enhanced_params={'objects': 3},
                enhanced_complexity=0.55
            )
            
            assert len(metadata.manipulations) == 1
            assert metadata.manipulations[0].type == 'enhanced'

    def test_generate_with_nonexistent_paths(self):
        """Test that nonexistent paths are ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            original = tmp_path / 'original.png'
            original.touch()
            
            original_image = Image(
                id='img_003',
                path=original,
                complexity_score=0.5
            )
            
            # Pass paths that don't exist
            metadata = generate_metadata_for_image(
                original_image=original_image,
                enhanced_path=tmp_path / 'nonexistent_enhanced.png',
                reduced_path=tmp_path / 'nonexistent_reduced.png'
            )
            
            assert len(metadata.manipulations) == 0


class TestSaveAndLoadMetadata:
    """Tests for saving and loading metadata to/from YAML."""

    def test_save_and_load_roundtrip(self):
        """Test that metadata can be saved and loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create metadata
            original_image = Image(
                id='img_004',
                path=tmp_path / 'original.png',
                complexity_score=0.5
            )
            original_image.path.touch()
            
            metadata = generate_metadata_for_image(
                original_image=original_image,
                enhanced_path=tmp_path / 'enhanced.png',
                enhanced_params={'test': 'value'},
                enhanced_complexity=0.6
            )
            metadata.checksum = 'test_checksum'
            metadata.notes = 'Test notes'
            
            # Save
            output_path = save_metadata_as_yaml(metadata, tmp_path)
            assert output_path.exists()
            assert output_path.suffix == '.yaml'
            
            # Load
            loaded = load_metadata_from_yaml('img_004', tmp_path)
            
            assert loaded is not None
            assert loaded.original_image_id == 'img_004'
            assert loaded.baseline_complexity_score == 0.5
            assert loaded.checksum == 'test_checksum'
            assert loaded.notes == 'Test notes'
            assert len(loaded.manipulations) == 1
            assert loaded.manipulations[0].type == 'enhanced'
            assert loaded.manipulations[0].parameters['test'] == 'value'

    def test_load_nonexistent_file(self):
        """Test loading a non-existent file returns None."""
        result = load_metadata_from_yaml('nonexistent_id')
        assert result is None

    def test_yaml_format(self):
        """Test that the YAML output is properly formatted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            original_image = Image(
                id='img_005',
                path=tmp_path / 'original.png',
                complexity_score=0.5
            )
            original_image.path.touch()
            
            metadata = generate_metadata_for_image(
                original_image=original_image,
                enhanced_path=tmp_path / 'enhanced.png',
                enhanced_params={'objects': 5}
            )
            
            output_path = save_metadata_as_yaml(metadata, tmp_path)
            
            # Read raw YAML and verify structure
            with open(output_path, 'r') as f:
                data = yaml.safe_load(f)
            
            assert 'original_image_id' in data
            assert 'baseline_complexity_score' in data
            assert 'manipulations' in data
            assert 'generated_at' in data