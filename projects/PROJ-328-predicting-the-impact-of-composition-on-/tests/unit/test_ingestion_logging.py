"""
Unit tests for ingestion logging and citation tracking functionality.
"""
import pytest
import os
import json
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from ingestion.logger_setup import IngestionLogger, CitationTracker, setup_ingestion_logging
from ingestion.citation_tracker import get_tracker, reset_tracker


class TestIngestionLogger:
    """Tests for the IngestionLogger class."""
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test fixtures."""
        self.tmp_path = tmp_path
        self.processed_dir = self.tmp_path / "data" / "processed"
        self.processed_dir.mkdir(parents=True)
        
        # Mock config function
        import ingestion.logger_setup as logger_module
        self.original_get_dir = logger_module.get_data_processed_dir
        logger_module.get_data_processed_dir = lambda: self.processed_dir
        
        # Reset tracker
        reset_tracker()
    
    def teardown(self):
        """Tear down test fixtures."""
        import ingestion.logger_setup as logger_module
        logger_module.get_data_processed_dir = self.original_get_dir
    
    def test_instantiation(self):
        """Test that IngestionLogger can be instantiated."""
        logger = IngestionLogger()
        assert logger is not None
        assert hasattr(logger, 'logger')
        assert hasattr(logger, 'citation_tracker')
    
    def test_log_source_fetch_start(self, caplog):
        """Test logging the start of a source fetch."""
        logger = IngestionLogger()
        logger.log_source_fetch_start("Test Source", "http://example.com")
        # Just verify no exception is raised
        assert True
    
    def test_log_source_fetch_success(self):
        """Test logging a successful source fetch."""
        logger = IngestionLogger()
        logger.log_source_fetch_success("Test Source", 100, 50.5)
        assert True
    
    def test_log_source_fetch_failure(self):
        """Test logging a failed source fetch."""
        logger = IngestionLogger()
        logger.log_source_fetch_failure("Test Source", "Connection error", 2)
        assert True
    
    def test_log_partial_data_aggregation(self):
        """Test logging partial data aggregation."""
        logger = IngestionLogger()
        logger.log_partial_data_aggregation(3, 2, 80)
        assert True
    
    def test_register_citation(self):
        """Test registering a citation."""
        logger = IngestionLogger()
        citation_info = {
            "authors": ["Test Author"],
            "year": 2023,
            "title": "Test Title",
            "url": "http://example.com"
        }
        logger.register_citation("Test Source", citation_info)
        
        summary = logger.get_citation_summary()
        assert "Test Source" in summary
        assert summary["Test Source"]["title"] == "Test Title"
    
    def test_save_citations(self):
        """Test saving citations to file."""
        logger = IngestionLogger()
        logger.register_citation("Test Source", {"title": "Test"})
        logger.save_citations()
        
        citation_file = self.processed_dir / "citations.json"
        assert citation_file.exists()
        
        with open(citation_file, 'r') as f:
            data = json.load(f)
        
        assert "Test Source" in data
    
    def test_get_citation_summary(self):
        """Test getting citation summary."""
        logger = IngestionLogger()
        logger.register_citation("Source1", {"title": "Title1"})
        logger.register_citation("Source2", {"title": "Title2"})
        
        summary = logger.get_citation_summary()
        assert len(summary) == 2
        assert "Source1" in summary
        assert "Source2" in summary
        assert summary["Source1"]["title"] == "Title1"


class TestCitationTracker:
    """Tests for the CitationTracker class."""
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test fixtures."""
        self.tmp_path = tmp_path
        self.processed_dir = self.tmp_path / "data" / "processed"
        self.processed_dir.mkdir(parents=True)
        
        import ingestion.citation_tracker as tracker_module
        self.original_get_dir = tracker_module.get_data_processed_dir
        tracker_module.get_data_processed_dir = lambda: self.processed_dir
        
        reset_tracker()
    
    def teardown(self):
        """Tear down test fixtures."""
        import ingestion.citation_tracker as tracker_module
        tracker_module.get_data_processed_dir = self.original_get_dir
    
    def test_add_citation(self):
        """Test adding a citation."""
        tracker = CitationTracker()
        tracker.add_citation("Source", {"title": "Test"})
        
        assert "Source" in tracker.citations
        assert tracker.citations["Source"]["title"] == "Test"
    
    def test_save_to_file(self):
        """Test saving citations to file."""
        tracker = CitationTracker()
        tracker.add_citation("Source", {"title": "Test"})
        tracker.save_to_file()
        
        json_file = self.processed_dir / "citations.json"
        csv_file = self.processed_dir / "citations.csv"
        
        assert json_file.exists()
        assert csv_file.exists()
    
    def test_load_from_file(self):
        """Test loading citations from file."""
        tracker = CitationTracker()
        tracker.add_citation("Source", {"title": "Test"})
        tracker.save_to_file()
        
        # Create a new tracker and load
        tracker2 = CitationTracker()
        loaded = tracker2.load_from_file()
        
        assert loaded is True
        assert "Source" in tracker2.citations
    
    def test_get_citation_string(self):
        """Test getting a formatted citation string."""
        tracker = CitationTracker()
        tracker.add_citation("Source", {
            "authors": ["Author A", "Author B"],
            "year": 2023,
            "title": "Test Title"
        })
        
        citation_str = tracker.get_citation_string("Source")
        assert citation_str is not None
        assert "Author A" in citation_str
        assert "2023" in citation_str
        assert "Test Title" in citation_str
    
    def test_get_citation_string_not_found(self):
        """Test getting citation for non-existent source."""
        tracker = CitationTracker()
        citation_str = tracker.get_citation_string("NonExistent")
        assert citation_str is None
    
    def test_get_all_citation_strings(self):
        """Test getting all formatted citation strings."""
        tracker = CitationTracker()
        tracker.add_citation("Source1", {
            "authors": ["A"],
            "year": 2023,
            "title": "Title1"
        })
        tracker.add_citation("Source2", {
            "authors": ["B"],
            "year": 2024,
            "title": "Title2"
        })
        
        citations = tracker.get_all_citation_strings()
        assert len(citations) == 2


class TestSetupIngestionLogging:
    """Tests for the setup_ingestion_logging function."""
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test fixtures."""
        self.tmp_path = tmp_path
        self.processed_dir = self.tmp_path / "data" / "processed"
        self.processed_dir.mkdir(parents=True)
        
        import ingestion.logger_setup as logger_module
        self.original_get_dir = logger_module.get_data_processed_dir
        logger_module.get_data_processed_dir = lambda: self.processed_dir
    
    def teardown(self):
        """Tear down test fixtures."""
        import ingestion.logger_setup as logger_module
        logger_module.get_data_processed_dir = self.original_get_dir
    
    def test_creates_log_file(self):
        """Test that setup_ingestion_logging creates the log file."""
        logger = setup_ingestion_logging()
        
        log_file = self.processed_dir / "ingestion_log.txt"
        assert log_file.exists()
    
    def test_returns_logger(self):
        """Test that setup_ingestion_logging returns a logger."""
        logger = setup_ingestion_logging()
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'debug')