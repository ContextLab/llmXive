"""
Unit tests for data models.
"""
import pytest
from datetime import datetime
from code.data_models import Sample, OTU, DiversityMetric, validate_sample_schema, validate_otu_schema, validate_diversity_metric_schema


class TestSample:
    """Tests for the Sample class."""

    def test_valid_sample_creation(self):
        """Test creation of a valid sample."""
        sample = Sample(
            sample_id="S001",
            timestamp=datetime(2023, 6, 15, 10, 30),
            location="East Pacific Rise",
            coordinates="10.5N, 104.5W",
            deployment_event="DEP_2023_01",
            sensor_id="SENS_001",
            fastq_path="data/raw/sample_001.fastq.gz",
            ph=6.5,
            temperature=350.0,
            ph_sd=0.1
        )
        
        assert sample.sample_id == "S001"
        assert sample.ph == 6.5
        assert not sample.ph_outlier
        assert not sample.ph_edge_range
        assert not sample.ph_heterogeneous

    def test_ph_outlier_detection(self):
        """Test pH outlier detection."""
        # Low pH outlier
        sample_low = Sample(
            sample_id="S002",
            timestamp=datetime(2023, 6, 15, 11, 0),
            location="Mid-Atlantic Ridge",
            coordinates="25.0N, 45.0W",
            deployment_event="DEP_2023_02",
            sensor_id="SENS_002",
            fastq_path="data/raw/sample_002.fastq.gz",
            ph=0.5
        )
        assert sample_low.ph_outlier is True
        
        # High pH outlier
        sample_high = Sample(
            sample_id="S003",
            timestamp=datetime(2023, 6, 15, 12, 0),
            location="Indian Ocean Ridge",
            coordinates="20.0S, 65.0E",
            deployment_event="DEP_2023_03",
            sensor_id="SENS_003",
            fastq_path="data/raw/sample_003.fastq.gz",
            ph=11.0
        )
        assert sample_high.ph_outlier is True

    def test_ph_edge_range_detection(self):
        """Test pH edge range detection."""
        # Lower edge range
        sample_low_edge = Sample(
            sample_id="S004",
            timestamp=datetime(2023, 6, 15, 13, 0),
            location="Pacific",
            coordinates="15.0N, 170.0W",
            deployment_event="DEP_2023_04",
            sensor_id="SENS_004",
            fastq_path="data/raw/sample_004.fastq.gz",
            ph=1.5
        )
        assert sample_low_edge.ph_edge_range is True
        
        # Upper edge range
        sample_high_edge = Sample(
            sample_id="S005",
            timestamp=datetime(2023, 6, 15, 14, 0),
            location="Atlantic",
            coordinates="30.0N, 50.0W",
            deployment_event="DEP_2023_05",
            sensor_id="SENS_005",
            fastq_path="data/raw/sample_005.fastq.gz",
            ph=9.0
        )
        assert sample_high_edge.ph_edge_range is True

    def test_ph_heterogeneity_detection(self):
        """Test pH heterogeneity detection."""
        sample_het = Sample(
            sample_id="S006",
            timestamp=datetime(2023, 6, 15, 15, 0),
            location="Arctic",
            coordinates="80.0N, 10.0E",
            deployment_event="DEP_2023_06",
            sensor_id="SENS_006",
            fastq_path="data/raw/sample_006.fastq.gz",
            ph=7.0,
            ph_sd=0.25
        )
        assert sample_het.ph_heterogeneous is True
        
        sample_not_het = Sample(
            sample_id="S007",
            timestamp=datetime(2023, 6, 15, 16, 0),
            location="Southern Ocean",
            coordinates="60.0S, 100.0E",
            deployment_event="DEP_2023_07",
            sensor_id="SENS_007",
            fastq_path="data/raw/sample_007.fastq.gz",
            ph=7.5,
            ph_sd=0.15
        )
        assert sample_not_het.ph_heterogeneous is False

    def test_sample_to_dict(self):
        """Test sample serialization to dictionary."""
        sample = Sample(
            sample_id="S008",
            timestamp=datetime(2023, 6, 15, 17, 0),
            location="Test Location",
            coordinates="0.0, 0.0",
            deployment_event="DEP_TEST",
            sensor_id="SENS_TEST",
            fastq_path="data/raw/test.fastq.gz",
            ph=7.0
        )
        
        sample_dict = sample.to_dict()
        
        assert sample_dict['sample_id'] == "S008"
        assert sample_dict['ph'] == 7.0
        assert 'timestamp' in sample_dict

    def test_sample_from_dict(self):
        """Test sample deserialization from dictionary."""
        sample_data = {
            'sample_id': "S009",
            'timestamp': '2023-06-15T18:00:00',
            'location': "Dict Location",
            'coordinates': "1.0, 1.0",
            'deployment_event': "DEP_DICT",
            'sensor_id': "SENS_DICT",
            'fastq_path': "data/raw/dict.fastq.gz",
            'ph': 6.8,
            'temperature': 300.0
        }
        
        sample = Sample.from_dict(sample_data)
        
        assert sample.sample_id == "S009"
        assert sample.ph == 6.8
        assert isinstance(sample.timestamp, datetime)

    def test_invalid_sample_id(self):
        """Test invalid sample_id raises error."""
        with pytest.raises(ValueError):
            Sample(
                sample_id="",
                timestamp=datetime(2023, 6, 15, 19, 0),
                location="Test",
                coordinates="0,0",
                deployment_event="DEP",
                sensor_id="SENS",
                fastq_path="data/raw/test.fastq.gz"
            )

    def test_invalid_timestamp_type(self):
        """Test invalid timestamp type raises error."""
        with pytest.raises(ValueError):
            Sample(
                sample_id="S010",
                timestamp="not a datetime",
                location="Test",
                coordinates="0,0",
                deployment_event="DEP",
                sensor_id="SENS",
                fastq_path="data/raw/test.fastq.gz"
            )


class TestOTU:
    """Tests for the OTU class."""

    def test_valid_otu_creation(self):
        """Test creation of a valid OTU."""
        otu = OTU(
            otu_id="OTU_001",
            sequence="ACGTACGTACGT",
            taxonomy="Bacteria;Proteobacteria;Gammaproteobacteria",
            counts={"S001": 100, "S002": 50}
        )
        
        assert otu.otu_id == "OTU_001"
        assert otu.total_count == 150

    def test_otu_add_count(self):
        """Test adding counts to an OTU."""
        otu = OTU(
            otu_id="OTU_002",
            sequence="GGGGCCCC",
            counts={"S001": 10}
        )
        
        otu.add_count("S002", 20)
        otu.add_count("S003", 30)
        
        assert otu.get_count("S001") == 10
        assert otu.get_count("S002") == 20
        assert otu.get_count("S003") == 30
        assert otu.total_count == 60

    def test_otu_negative_count(self):
        """Test that negative count raises error."""
        otu = OTU(
            otu_id="OTU_003",
            sequence="AAAA",
            counts={}
        )
        
        with pytest.raises(ValueError):
            otu.add_count("S001", -5)

    def test_otu_to_dict(self):
        """Test OTU serialization to dictionary."""
        otu = OTU(
            otu_id="OTU_004",
            sequence="TTTT",
            counts={"S001": 25}
        )
        
        otu_dict = otu.to_dict()
        
        assert otu_dict['otu_id'] == "OTU_004"
        assert otu_dict['total_count'] == 25

    def test_otu_from_dict(self):
        """Test OTU deserialization from dictionary."""
        otu_data = {
            'otu_id': "OTU_005",
            'sequence': "NNNN",
            'taxonomy': "Unknown",
            'counts': {"S001": 15, "S002": 25},
            'total_count': 40
        }
        
        otu = OTU.from_dict(otu_data)
        
        assert otu.otu_id == "OTU_005"
        assert otu.total_count == 40


class TestDiversityMetric:
    """Tests for the DiversityMetric class."""

    def test_valid_metric_creation(self):
        """Test creation of a valid diversity metric."""
        metric = DiversityMetric(
            sample_id="S001",
            metric_name="shannon",
            value=2.5,
            rarefaction_depth=10000
        )
        
        assert metric.sample_id == "S001"
        assert metric.value == 2.5
        assert not metric.transformed

    def test_metric_negative_value(self):
        """Test that negative value raises error."""
        with pytest.raises(ValueError):
            DiversityMetric(
                sample_id="S001",
                metric_name="shannon",
                value=-1.0
            )

    def test_metric_to_dict(self):
        """Test diversity metric serialization to dictionary."""
        metric = DiversityMetric(
            sample_id="S002",
            metric_name="simpson",
            value=0.85,
            rarefaction_depth=5000,
            transformed=True,
            model_type="LME",
            estimate=0.15,
            se=0.05,
            p_value=0.003
        )
        
        metric_dict = metric.to_dict()
        
        assert metric_dict['sample_id'] == "S002"
        assert metric_dict['transformed'] is True
        assert metric_dict['p_value'] == 0.003

    def test_metric_from_dict(self):
        """Test diversity metric deserialization from dictionary."""
        metric_data = {
            'sample_id': "S003",
            'metric_name': "pielou",
            'value': 0.75,
            'rarefaction_depth': 8000,
            'transformed': False,
            'model_type': "Spearman"
        }
        
        metric = DiversityMetric.from_dict(metric_data)
        
        assert metric.sample_id == "S003"
        assert metric.value == 0.75


class TestValidationFunctions:
    """Tests for schema validation functions."""

    def test_validate_sample_schema_valid(self):
        """Test validation of valid sample data."""
        sample_data = {
            'sample_id': "S011",
            'timestamp': datetime(2023, 6, 15, 20, 0),
            'location': "Valid Location",
            'coordinates': "2.0, 2.0",
            'deployment_event': "DEP_VALID",
            'sensor_id': "SENS_VALID",
            'fastq_path': "data/raw/valid.fastq.gz"
        }
        
        assert validate_sample_schema(sample_data) is True

    def test_validate_sample_schema_missing_field(self):
        """Test validation fails on missing required field."""
        sample_data = {
            'sample_id': "S012",
            'timestamp': datetime(2023, 6, 15, 21, 0),
            # Missing location
            'coordinates': "3.0, 3.0",
            'deployment_event': "DEP_MISSING",
            'sensor_id': "SENS_MISSING",
            'fastq_path': "data/raw/missing.fastq.gz"
        }
        
        with pytest.raises(ValueError):
            validate_sample_schema(sample_data)

    def test_validate_otu_schema_valid(self):
        """Test validation of valid OTU data."""
        otu_data = {
            'otu_id': "OTU_006",
            'sequence': "ACGT"
        }
        
        assert validate_otu_schema(otu_data) is True

    def test_validate_otu_schema_missing_field(self):
        """Test validation fails on missing required field."""
        otu_data = {
            'otu_id': "OTU_007"
            # Missing sequence
        }
        
        with pytest.raises(ValueError):
            validate_otu_schema(otu_data)

    def test_validate_diversity_metric_schema_valid(self):
        """Test validation of valid diversity metric data."""
        metric_data = {
            'sample_id': "S013",
            'metric_name': "shannon",
            'value': 2.0
        }
        
        assert validate_diversity_metric_schema(metric_data) is True

    def test_validate_diversity_metric_schema_missing_field(self):
        """Test validation fails on missing required field."""
        metric_data = {
            'sample_id': "S014",
            # Missing metric_name
            'value': 1.5
        }
        
        with pytest.raises(ValueError):
            validate_diversity_metric_schema(metric_data)