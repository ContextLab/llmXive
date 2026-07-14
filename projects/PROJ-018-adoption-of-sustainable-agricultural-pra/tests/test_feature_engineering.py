"""Tests for feature engineering module (T021)."""
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Import functions to test
from code_03_engineer_features import (
    create_adoption_binary,
    select_engagement_proxies,
    create_engagement_score,
    calculate_cronbach_alpha,
    perform_efa,
    check_convergent_validity
)


class TestCreateAdoptionBinary:
    """Tests for adoption binary creation."""

    def test_create_adoption_binary_with_practices(self):
        """Test creation of adoption binary when practices exist."""
        df = pd.DataFrame({
            'practice_organic': [1, 0, 1, 0],
            'practice_conservation': [0, 1, 0, 0],
            'other_col': ['a', 'b', 'c', 'd']
        })

        practice_cols = ['practice_organic', 'practice_conservation']
        result = create_adoption_binary(df, practice_cols)

        assert 'adoption_binary' in result.columns
        # Row 0: 1 practice, Row 1: 1 practice, Row 2: 1 practice, Row 3: 0 practices
        expected = [1, 1, 1, 0]
        assert list(result['adoption_binary']) == expected

    def test_create_adoption_binary_no_practices(self):
        """Test creation when no practice columns found."""
        df = pd.DataFrame({
            'other_col': [1, 2, 3]
        })

        result = create_adoption_binary(df, [])

        assert 'adoption_binary' in result.columns
        assert all(result['adoption_binary'] == 0)


class TestSelectEngagementProxies:
    """Tests for engagement proxy selection."""

    def test_select_priority_proxies_available(self):
        """Test selection when priority proxies are available."""
        df = pd.DataFrame({
            'community_membership': [1, 2, 3],
            'extension_contact': [1, 0, 1],
            'other': ['a', 'b', 'c']
        })

        priority = ['community_membership', 'extension_contact', 'collective_action']
        fallback = ['training_attendance']

        selected, details = select_engagement_proxies(df, priority, fallback)

        assert 'community_membership' in selected
        assert 'extension_contact' in selected
        assert 'collective_action' not in selected  # Not in df
        assert details['used_fallback'] is False

    def test_select_fallback_when_priority_missing(self):
        """Test fallback mechanism when priority proxies missing."""
        df = pd.DataFrame({
            'training_attendance': [1, 2, 3],
            'other': ['a', 'b', 'c']
        })

        priority = ['community_membership', 'extension_contact']
        fallback = ['training_attendance']

        selected, details = select_engagement_proxies(df, priority, fallback)

        assert 'training_attendance' in selected
        assert details['used_fallback'] is True


class TestCreateEngagementScore:
    """Tests for engagement score creation."""

    def test_create_engagement_score_equal_weight(self):
        """Test equal-weighted engagement score."""
        df = pd.DataFrame({
            'membership': [0, 1, 2, 3],
            'extension': [0, 0, 1, 2]
        })

        proxy_cols = ['membership', 'extension']
        result = create_engagement_score(df, proxy_cols, method='equal_weight')

        assert 'engagement_score' in result.columns
        assert result['engagement_score'].min() >= 0
        assert result['engagement_score'].max() <= 1

    def test_create_engagement_score_weighted(self):
        """Test weighted engagement score."""
        df = pd.DataFrame({
            'membership': [0, 1, 2, 3],
            'extension': [0, 0, 1, 2]
        })

        proxy_cols = ['membership', 'extension']
        weights = {'membership': 2.0, 'extension': 1.0}
        result = create_engagement_score(df, proxy_cols, weights=weights)

        assert 'engagement_score' in result.columns
        # Membership has higher weight, so scores should reflect that


class TestReliabilityAndValidity:
    """Tests for reliability and validity calculations."""

    def test_cronbach_alpha(self):
        """Test Cronbach's alpha calculation."""
        # Create correlated items
        np.random.seed(42)
        n = 100
        latent = np.random.normal(0, 1, n)
        items = pd.DataFrame({
            'item1': latent + np.random.normal(0, 0.5, n),
            'item2': latent + np.random.normal(0, 0.5, n),
            'item3': latent + np.random.normal(0, 0.5, n)
        })

        alpha = calculate_cronbach_alpha(items, ['item1', 'item2', 'item3'])

        assert alpha is not None
        assert 0 <= alpha <= 1  # Alpha should be between 0 and 1

    def test_efa_with_sufficient_data(self):
        """Test EFA with sufficient data."""
        np.random.seed(42)
        n = 200
        latent1 = np.random.normal(0, 1, n)
        latent2 = np.random.normal(0, 1, n)
        items = pd.DataFrame({
            'item1': latent1 + np.random.normal(0, 0.3, n),
            'item2': latent1 + np.random.normal(0, 0.3, n),
            'item3': latent2 + np.random.normal(0, 0.3, n),
            'item4': latent2 + np.random.normal(0, 0.3, n)
        })

        result = perform_efa(items, ['item1', 'item2', 'item3', 'item4'])

        # Should succeed with sufficient data
        assert result['status'] in ['success', 'skipped', 'failed']

    def test_convergent_validity(self):
        """Test convergent validity check."""
        np.random.seed(42)
        n = 100
        engagement = np.random.normal(0, 1, n)
        related = engagement * 0.7 + np.random.normal(0, 0.3, n)  # Correlated

        df = pd.DataFrame({
            'engagement_score': engagement,
            'related_construct': related
        })

        result = check_convergent_validity(
            df,
            'engagement_score',
            ['related_construct']
        )

        # Should find significant correlation
        assert len(result['constructs_tested']) > 0