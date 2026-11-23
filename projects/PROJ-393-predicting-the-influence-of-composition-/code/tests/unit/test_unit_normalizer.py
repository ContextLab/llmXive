"""
Unit tests for unit_normalizer.py.
Tests conversion of coercivity and saturation magnetization units.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.preprocessing.unit_normalizer import (
    normalize_unit,
    normalize_coercivity,
    normalize_saturation_magnetization,
    standardize_units,
    H_TO_OE,
    MS_TO_EMU_G
)

class TestNormalizeUnit:
    def test_oe_to_oe(self):
        assert normalize_unit(100.0, "Oe", H_TO_OE, "Coercivity") == 100.0

    def test_koe_to_oe(self):
        # 1 kOe = 1000 Oe
        assert normalize_unit(1.0, "kOe", H_TO_OE, "Coercivity") == 1000.0

    def test_ao_to_oe(self):
        # 1 A/m approx 0.012566 Oe
        result = normalize_unit(100.0, "A/m", H_TO_OE, "Coercivity")
        expected = 100.0 * 0.012566370614359172
        assert abs(result - expected) < 1e-6

    def test_emu_g_to_emu_g(self):
        assert normalize_unit(50.0, "emu/g", MS_TO_EMU_G, "Saturation Magnetization") == 50.0

    def test_ams2_kg_to_emu_g(self):
        # 1 A m^2 / kg = 1 emu/g
        assert normalize_unit(50.0, "A m^2/kg", MS_TO_EMU_G, "Saturation Magnetization") == 50.0

    def test_unknown_unit_warning(self, caplog):
        result = normalize_unit(100.0, "Tesla", H_TO_OE, "Coercivity")
        # Should return original value and log warning
        assert result == 100.0
        assert "Unknown unit" in caplog.text

class TestNormalizeCoercivity:
    def test_basic_conversion(self):
        df = pd.DataFrame({
            'coercivity': [1.0, 100.0, 1000.0],
            'coercivity_unit': ['kOe', 'Oe', 'A/m']
        })
        result = normalize_coercivity(df)
        
        assert 'coercivity_oe' in result.columns
        # Row 0: 1 kOe -> 1000 Oe
        assert result.iloc[0]['coercivity_oe'] == 1000.0
        # Row 1: 100 Oe -> 100 Oe
        assert result.iloc[1]['coercivity_oe'] == 100.0
        # Row 2: 1000 A/m -> ~12.566 Oe
        expected = 1000.0 * 0.012566370614359172
        assert abs(result.iloc[2]['coercivity_oe'] - expected) < 1e-4

    def test_missing_unit_column(self, caplog):
        df = pd.DataFrame({
            'coercivity': [100.0, 200.0]
        })
        result = normalize_coercivity(df)
        assert 'coercivity_oe' in result.columns
        assert result.iloc[0]['coercivity_oe'] == 100.0
        assert "Unit column for coercivity not found" in caplog.text

    def test_missing_value(self):
        df = pd.DataFrame({
            'coercivity': [1.0, np.nan],
            'coercivity_unit': ['kOe', 'Oe']
        })
        result = normalize_coercivity(df)
        assert pd.isna(result.iloc[1]['coercivity_oe'])

class TestNormalizeSaturationMagnetization:
    def test_basic_conversion(self):
        df = pd.DataFrame({
            'saturation_magnetization': [1.0, 100.0],
            'ms_unit': ['A m^2/kg', 'emu/g']
        })
        result = normalize_saturation_magnetization(df)
        
        assert 'saturation_magnetization_emu_g' in result.columns
        # Row 0: 1 A m^2/kg -> 1 emu/g
        assert result.iloc[0]['saturation_magnetization_emu_g'] == 1.0
        # Row 1: 100 emu/g -> 100 emu/g
        assert result.iloc[1]['saturation_magnetization_emu_g'] == 100.0

    def test_missing_unit_column(self, caplog):
        df = pd.DataFrame({
            'saturation_magnetization': [50.0, 60.0]
        })
        result = normalize_saturation_magnetization(df)
        assert 'saturation_magnetization_emu_g' in result.columns
        assert result.iloc[0]['saturation_magnetization_emu_g'] == 50.0
        assert "Unit column for saturation magnetization not found" in caplog.text

    def test_tesla_without_density(self, caplog):
        df = pd.DataFrame({
            'saturation_magnetization': [1.0],
            'ms_unit': ['T']
        })
        result = normalize_saturation_magnetization(df)
        # Should return NaN and log warning
        assert pd.isna(result.iloc[0]['saturation_magnetization_emu_g'])
        assert "Tesla unit detected but density column missing" in caplog.text

class TestNormalizeUnitIntegration:
    def test_standardize_units_full(self):
        df = pd.DataFrame({
            'coercivity': [1.0, 100.0],
            'coercivity_unit': ['kOe', 'Oe'],
            'saturation_magnetization': [50.0, 100.0],
            'ms_unit': ['A m^2/kg', 'emu/g']
        })
        result = standardize_units(df)
        
        assert 'coercivity_oe' in result.columns
        assert 'saturation_magnetization_emu_g' in result.columns
        assert result.iloc[0]['coercivity_oe'] == 1000.0
        assert result.iloc[0]['saturation_magnetization_emu_g'] == 50.0
        assert result.iloc[1]['coercivity_oe'] == 100.0
        assert result.iloc[1]['saturation_magnetization_emu_g'] == 100.0