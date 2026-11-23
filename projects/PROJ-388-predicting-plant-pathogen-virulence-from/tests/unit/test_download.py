import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import shutil

from src.data.download import fetch_phenotypes_from_phi_base, DataFetchError
from src.models.isolate import Isolate
from src.models.species_aggregate import SpeciesAggregate


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp)


@pytest.fixture
def sample_isolates():
    """Create a list of sample Isolate objects for testing."""
    return [
        Isolate(
            strain_id="FGSC_4",
            species="Fusarium graminearum",
            genome_path="/fake/path/FGSC_4.fna",
            phenotype_score=0.85,
            metadata={"source": "NCBI"}
        ),
        Isolate(
            strain_id="PSY311",
            species="Pseudomonas syringae",
            genome_path="/fake/path/PSY311.fna",
            phenotype_score=0.42,
            metadata={"source": "NCBI"}
        ),
        Isolate(
            strain_id="Xcc_307",
            species="Xanthomonas campestris",
            genome_path="/fake/path/Xcc_307.fna",
            phenotype_score=None,  # Missing phenotype
            metadata={"source": "NCBI"}
        ),
    ]


class TestPHIBasePhenotypeFetch:
    """Unit tests for PHI-base phenotype fetch and fallback logic."""

    def test_fetch_phenotypes_success(self, temp_dir, sample_isolates):
        """Test successful fetching of phenotypes from PHI-base."""
        # Mock the HTML response from PHI-base
        mock_html = """
        <html>
        <body>
            <table>
                <tr><td>FGSC_4</td><td>Fusarium graminearum</td><td>0.85</td></tr>
                <tr><td>PSY311</td><td>Pseudomonas syringae</td><td>0.42</td></tr>
                <tr><td>Xcc_307</td><td>Xanthomonas campestris</td><td>0.60</td></tr>
            </table>
        </body>
        </html>
        """

        with patch('src.data.download.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = mock_html
            mock_get.return_value = mock_response

            result = fetch_phenotypes_from_phi_base(sample_isolates)

            assert len(result) == 3
            assert result[0].phenotype_score == 0.85
            assert result[1].phenotype_score == 0.42
            assert result[2].phenotype_score == 0.60
            mock_get.assert_called_once()

    def test_fetch_phenotypes_partial_missing(self, temp_dir, sample_isolates):
        """Test handling when some isolates are missing from PHI-base."""
        # Mock HTML where one isolate is missing
        mock_html = """
        <html>
        <body>
            <table>
                <tr><td>FGSC_4</td><td>Fusarium graminearum</td><td>0.85</td></tr>
                <tr><td>PSY311</td><td>Pseudomonas syringae</td><td>0.42</td></tr>
            </table>
        </body>
        </html>
        """

        with patch('src.data.download.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = mock_html
            mock_get.return_value = mock_response

            result = fetch_phenotypes_from_phi_base(sample_isolates)

            # FGSC_4 and PSY311 should have scores, Xcc_307 should remain None
            assert result[0].phenotype_score == 0.85
            assert result[1].phenotype_score == 0.42
            assert result[2].phenotype_score is None

    def test_fetch_phenotypes_http_error(self, temp_dir, sample_isolates):
        """Test that DataFetchError is raised on HTTP error."""
        with patch('src.data.download.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            with pytest.raises(DataFetchError) as exc_info:
                fetch_phenotypes_from_phi_base(sample_isolates)

            assert "404" in str(exc_info.value)

    def test_fetch_phenotypes_connection_error(self, temp_dir, sample_isolates):
        """Test that DataFetchError is raised on connection error."""
        with patch('src.data.download.requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection refused")

            with pytest.raises(DataFetchError) as exc_info:
                fetch_phenotypes_from_phi_base(sample_isolates)

            assert "Connection" in str(exc_info.value)

    def test_fetch_phenotypes_fallback_to_aggregate(self, temp_dir):
        """Test fallback logic when isolate-level data is missing, using species aggregate."""
        # Create isolates with missing phenotypes
        isolates_missing = [
            Isolate(
                strain_id="Xcc_307",
                species="Xanthomonas campestris",
                genome_path="/fake/path/Xcc_307.fna",
                phenotype_score=None,
                metadata={"source": "NCBI"}
            ),
            Isolate(
                strain_id="Xcc_308",
                species="Xanthomonas campestris",
                genome_path="/fake/path/Xcc_308.fna",
                phenotype_score=None,
                metadata={"source": "NCBI"}
            ),
        ]

        # Mock species aggregate data
        mock_aggregate = SpeciesAggregate(
            species_name="Xanthomonas campestris",
            avg_phenotype=0.55,
            isolate_count=10,
            variance=0.02
        )

        # Mock the function that retrieves species aggregates
        with patch('src.data.download._get_species_aggregate') as mock_get_agg:
            mock_get_agg.return_value = mock_aggregate

            with patch('src.data.download.requests.get') as mock_get:
                # Mock empty PHI-base response for these specific isolates
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.text = "<html><body><table></table></body></html>"
                mock_get.return_value = mock_response

                result = fetch_phenotypes_from_phi_base(isolates_missing)

                # Both isolates should now have the aggregate score
                assert result[0].phenotype_score == 0.55
                assert result[1].phenotype_score == 0.55
                mock_get_agg.assert_called_once_with("Xanthomonas campestris")

    def test_fetch_phenotypes_no_fallback_available(self, temp_dir, sample_isolates):
        """Test that missing phenotypes remain None when no aggregate fallback exists."""
        mock_html = """
        <html>
        <body>
            <table>
                <tr><td>FGSC_4</td><td>Fusarium graminearum</td><td>0.85</td></tr>
            </table>
        </body>
        </html>
        """

        with patch('src.data.download.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = mock_html
            mock_get.return_value = mock_response

            # Mock aggregate lookup to return None
            with patch('src.data.download._get_species_aggregate') as mock_get_agg:
                mock_get_agg.return_value = None

                result = fetch_phenotypes_from_phi_base(sample_isolates)

                # FGSC_4 has score, others remain None
                assert result[0].phenotype_score == 0.85
                assert result[1].phenotype_score is None
                assert result[2].phenotype_score is None

    def test_fetch_phenotypes_invalid_score_format(self, temp_dir, sample_isolates):
        """Test handling of invalid phenotype score formats."""
        mock_html = """
        <html>
        <body>
            <table>
                <tr><td>FGSC_4</td><td>Fusarium graminearum</td><td>invalid</td></tr>
                <tr><td>PSY311</td><td>Pseudomonas syringae</td><td>0.42</td></tr>
            </table>
        </body>
        </html>
        """

        with patch('src.data.download.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = mock_html
            mock_get.return_value = mock_response

            result = fetch_phenotypes_from_phi_base(sample_isolates)

            # Invalid score should be treated as None
            assert result[0].phenotype_score is None
            assert result[1].phenotype_score == 0.42

    def test_fetch_phenotypes_empty_response(self, temp_dir, sample_isolates):
        """Test handling of empty PHI-base response."""
        with patch('src.data.download.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "<html><body><table></table></body></html>"
            mock_get.return_value = mock_response

            result = fetch_phenotypes_from_phi_base(sample_isolates)

            # All isolates should have None as no data was found
            assert all(isolate.phenotype_score is None for isolate in result)

    def test_fetch_phenotypes_logging(self, temp_dir, sample_isolates, caplog):
        """Test that appropriate logs are generated during fetch."""
        mock_html = """
        <html>
        <body>
            <table>
                <tr><td>FGSC_4</td><td>Fusarium graminearum</td><td>0.85</td></tr>
            </table>
        </body>
        </html>
        """

        with patch('src.data.download.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = mock_html
            mock_get.return_value = mock_response

            with patch('src.data.download._get_species_aggregate') as mock_get_agg:
                mock_get_agg.return_value = None

                with caplog.at_level("WARNING"):
                    result = fetch_phenotypes_from_phi_base(sample_isolates)

                    # Check that warnings were logged for missing phenotypes
                    assert any("missing phenotype" in record.message for record in caplog.records)