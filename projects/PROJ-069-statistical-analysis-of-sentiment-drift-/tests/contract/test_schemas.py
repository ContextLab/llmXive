"""
Contract tests for schema definitions in code/contracts/.

These tests verify that:
1. All schemas can be instantiated with valid data
2. Validation correctly rejects invalid data
3. Example data matches schema requirements
"""

import pytest
from datetime import datetime
from code.contracts import TimeSeries, ModelResult, RecessionPeriod
from code.contracts.model_results import (
    StationarityTestResult,
    CointegrationTestResult,
    GrangerCausalityResult,
    CollinearityDiagnostic,
    BootstrapValidationResult,
)


class TestTimeSeriesSchema:
    """Tests for the TimeSeries schema."""
    
    def test_valid_timeseries_creation(self):
        """Test creating a valid TimeSeries instance."""
        ts = TimeSeries(
            timestamp=datetime(2020, 1, 1),
            sentiment_score=0.65,
            sentiment_polarity_ratio=1.8,
            sentiment_confidence=0.85,
            sentiment_sample_size=15000,
            gdp_growth=2.1,
            unemployment_rate=3.5,
            consumer_confidence=105.2,
            missing_rate_pct=0.0,
            interpolation_method="linear",
            data_quality_flag=True
        )
        assert ts.timestamp.day == 1
        assert ts.sentiment_score == 0.65
        assert ts.data_quality_flag is True
    
    def test_invalid_timestamp_day(self):
        """Test that non-first-day timestamps are rejected."""
        with pytest.raises(ValueError):
            TimeSeries(
                timestamp=datetime(2020, 1, 15),
                sentiment_score=0.5
            )
    
    def test_missing_rate_bounds(self):
        """Test that missing rate is validated."""
        # Valid value
        ts = TimeSeries(
            timestamp=datetime(2020, 1, 1),
            missing_rate_pct=50.0
        )
        assert ts.missing_rate_pct == 50.0
        
        # Invalid value (>100)
        with pytest.raises(ValueError):
            TimeSeries(
                timestamp=datetime(2020, 1, 1),
                missing_rate_pct=101.0
            )
    
    def test_confidence_bounds(self):
        """Test that confidence is between 0 and 1."""
        # Valid value
        ts = TimeSeries(
            timestamp=datetime(2020, 1, 1),
            sentiment_confidence=0.9
        )
        assert ts.sentiment_confidence == 0.9
        
        # Invalid value (>1)
        with pytest.raises(ValueError):
            TimeSeries(
                timestamp=datetime(2020, 1, 1),
                sentiment_confidence=1.1
            )
    
    def test_optional_fields(self):
        """Test that optional fields can be None."""
        ts = TimeSeries(
            timestamp=datetime(2020, 1, 1),
            sentiment_score=None,
            gdp_growth=None,
            unemployment_rate=None,
            consumer_confidence=None
        )
        assert ts.sentiment_score is None
        assert ts.gdp_growth is None


class TestModelResultSchema:
    """Tests for the ModelResult schema."""
    
    def test_valid_model_result_creation(self):
        """Test creating a valid ModelResult instance."""
        model_result = ModelResult(
            model_type="VECM",
            optimal_lag_length=2,
            stationarity_results=[
                StationarityTestResult(
                    variable_name="sentiment_score",
                    statistic=-3.45,
                    p_value=0.02,
                    lag_length=1,
                    is_stationary=True
                )
            ],
            cointegration_result=CointegrationTestResult(
                trace_statistic=25.3,
                trace_p_value=0.01,
                cointegration_rank=1,
                model_selection="VECM"
            ),
            granger_causality_results=[
                GrangerCausalityResult(
                    causal_direction="sentiment_to_gdp",
                    f_statistic=4.2,
                    p_value=0.03,
                    lag_length=2,
                    is_causal=True
                )
            ],
            bootstrap_results=[
                BootstrapValidationResult(
                    variable_name="sentiment_score",
                    original_coefficient=0.15,
                    confidence_interval_95=[0.08, 0.22],
                    ci_width_ratio=0.15,
                    convergence_achieved=True,
                    block_length_months=1,
                    num_iterations=1000
                )
            ]
        )
        assert model_result.model_type == "VECM"
        assert len(model_result.stationarity_results) == 1
    
    def test_invalid_model_type(self):
        """Test that invalid model types are accepted (string validation)."""
        # Note: Model type is a string, so validation is minimal here
        model_result = ModelResult(
            model_type="VAR",
            optimal_lag_length=1,
            stationarity_results=[],
            cointegration_result=CointegrationTestResult(
                trace_statistic=10.0,
                trace_p_value=0.5,
                cointegration_rank=0,
                model_selection="VAR"
            ),
            granger_causality_results=[],
            bootstrap_results=[]
        )
        assert model_result.model_type == "VAR"
    
    def test_collinearity_diagnostic(self):
        """Test creating a CollinearityDiagnostic instance."""
        diag = CollinearityDiagnostic(
            variable_pair="GDP_vs_UNRATE",
            vif_value=45.0,
            is_high_collinearity=True,
            interpretation="Joint relationship"
        )
        assert diag.vif_value == 45.0
        assert diag.is_high_collinearity is True


class TestRecessionPeriodSchema:
    """Tests for the RecessionPeriod schema."""
    
    def test_valid_recession_period_creation(self):
        """Test creating a valid RecessionPeriod instance."""
        recession = RecessionPeriod(
            start_date=datetime(2007, 12, 1),
            end_date=datetime(2009, 6, 1),
            duration_months=18,
            source="NBER"
        )
        assert recession.start_date.year == 2007
        assert recession.end_date.month == 6
        assert recession.duration_months == 18
    
    def test_invalid_start_date(self):
        """Test that non-first-day start dates are rejected."""
        with pytest.raises(ValueError):
            RecessionPeriod(
                start_date=datetime(2007, 12, 15),
                end_date=datetime(2009, 6, 1)
            )
    
    def test_invalid_end_date(self):
        """Test that non-first-day end dates are rejected."""
        with pytest.raises(ValueError):
            RecessionPeriod(
                start_date=datetime(2007, 12, 1),
                end_date=datetime(2009, 6, 15)
            )
    
    def test_duration_calculation(self):
        """Test the calculate_duration method."""
        recession = RecessionPeriod(
            start_date=datetime(2007, 12, 1),
            end_date=datetime(2009, 6, 1)
        )
        assert recession.calculate_duration() == 18
    
    def test_is_in_recession(self):
        """Test the is_in_recession method."""
        recession = RecessionPeriod(
            start_date=datetime(2007, 12, 1),
            end_date=datetime(2009, 6, 1)
        )
        
        # Date within recession
        assert recession.is_in_recession(datetime(2008, 6, 1)) is True
        
        # Date before recession
        assert recession.is_in_recession(datetime(2007, 6, 1)) is False
        
        # Date after recession
        assert recession.is_in_recession(datetime(2010, 1, 1)) is False
    
    def test_optional_fields(self):
        """Test that optional fields can be None."""
        recession = RecessionPeriod(
            start_date=datetime(2007, 12, 1),
            end_date=datetime(2009, 6, 1),
            peak_month=None,
            trough_month=None,
            data_checksum=None
        )
        assert recession.peak_month is None
        assert recession.trough_month is None