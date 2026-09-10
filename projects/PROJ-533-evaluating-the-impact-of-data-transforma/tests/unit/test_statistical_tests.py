import pytest
import numpy as np
import pandas as pd
from code.utils.statistical_tests import t_test, anova_one_way, shapiro_test, friedman_test


class TestTTest:
    def test_equal_variance(self):
        # Two normal distributions with same variance
        g1 = np.random.normal(0, 1, 100)
        g2 = np.random.normal(0.5, 1, 100)
        stat, pval = t_test(g1, g2)
        assert isinstance(stat, float)
        assert isinstance(pval, float)
        assert 0 <= pval <= 1

    def test_unequal_variance(self):
        g1 = np.random.normal(0, 1, 100)
        g2 = np.random.normal(0, 2, 100)
        stat, pval = t_test(g1, g2, equal_var=False)
        assert isinstance(stat, float)
        assert isinstance(pval, float)

    def test_empty_input(self):
        with pytest.raises(ValueError):
            t_test([], [1, 2, 3])


class TestAnovaOneWay:
    def test_basic_anova(self):
        g1 = np.random.normal(0, 1, 50)
        g2 = np.random.normal(1, 1, 50)
        g3 = np.random.normal(2, 1, 50)
        stat, pval = anova_one_way([g1, g2, g3])
        assert isinstance(stat, float)
        assert isinstance(pval, float)

    def test_2d_input(self):
        data = np.random.rand(5, 3)  # 5 blocks, 3 treatments
        # Note: Anova expects independent groups, so 2D input here is treated as rows=groups
        # Just checking it runs without error
        stat, pval = anova_one_way(data)
        assert isinstance(stat, float)

    def test_single_group(self):
        with pytest.raises(ValueError):
            anova_one_way([np.array([1, 2, 3])])


class TestShapiroTest:
    def test_normal_data(self):
        data = np.random.normal(0, 1, 100)
        stat, pval = shapiro_test(data)
        assert isinstance(stat, float)
        assert 0 <= pval <= 1

    def test_small_sample(self):
        data = [1, 2, 3]
        stat, pval = shapiro_test(data)
        assert isinstance(stat, float)

    def test_too_small(self):
        with pytest.raises(ValueError):
            shapiro_test([1, 2])

    def test_too_large(self):
        # Shapiro-Wilk limit is 5000
        with pytest.raises(ValueError):
            shapiro_test(np.random.rand(5001))


class TestFriedmanTest:
    def test_basic_friedman(self):
        # 10 subjects, 3 treatments
        data = np.random.rand(10, 3)
        stat, pval = friedman_test(data)
        assert isinstance(stat, float)
        assert isinstance(pval, float)

    def test_dataframe_input(self):
        df = pd.DataFrame(np.random.rand(5, 4))
        stat, pval = friedman_test(df)
        assert isinstance(stat, float)

    def test_non_2d(self):
        with pytest.raises(ValueError):
            friedman_test([1, 2, 3])

    def test_single_column(self):
        with pytest.raises(ValueError):
            friedman_test(np.random.rand(5, 1))