"""T005 — unit tests for verify/constants.py (spec 018, T005/T006)."""

from __future__ import annotations

import math

import pytest
import scipy.constants

from llmxive.verify.constants import CONSTANTS, lookup, true_value


class TestLookup:
    def test_pi_by_name(self):
        c = lookup("pi")
        assert c is not None
        assert c.key == "pi"

    def test_pi_by_symbol(self):
        c = lookup("π")
        assert c is not None
        assert c.key == "pi"

    def test_e_by_name(self):
        c = lookup("e")
        assert c is not None
        assert c.key == "e"

    def test_eulers_number(self):
        c = lookup("Euler's number")
        assert c is not None
        assert c.key == "e"

    def test_speed_of_light_full(self):
        c = lookup("speed of light")
        assert c is not None
        assert c.key == "speed_of_light"

    def test_speed_of_light_c(self):
        c = lookup("c")
        assert c is not None
        assert c.key == "speed_of_light"

    def test_tau(self):
        c = lookup("tau")
        assert c is not None
        assert c.key == "tau"

    def test_golden_ratio(self):
        c = lookup("golden ratio")
        assert c is not None
        assert c.key == "golden_ratio"

    def test_unknown_returns_none(self):
        assert lookup("frobnicator constant") is None

    def test_case_insensitive(self):
        assert lookup("PI") is not None
        assert lookup("Speed of Light") is not None

    def test_provenance_has_authority(self):
        c = lookup("pi")
        assert c.authority  # non-empty string
        assert c.url  # non-empty string


class TestTrueValue:
    def test_pi(self):
        assert true_value("pi") == math.pi

    def test_pi_symbol(self):
        assert true_value("π") == math.pi

    def test_e(self):
        assert true_value("e") == math.e

    def test_speed_of_light(self):
        assert true_value("speed of light") == scipy.constants.c

    def test_c(self):
        assert true_value("c") == scipy.constants.c

    def test_tau(self):
        assert true_value("tau") == math.tau

    def test_golden_ratio(self):
        phi = (1 + math.sqrt(5)) / 2
        assert true_value("golden ratio") == pytest.approx(phi, rel=1e-12)

    def test_planck(self):
        assert true_value("Planck constant") == scipy.constants.h

    def test_gravitational(self):
        assert true_value("gravitational constant") == scipy.constants.G

    def test_boltzmann(self):
        assert true_value("Boltzmann constant") == scipy.constants.k

    def test_avogadro(self):
        assert true_value("Avogadro number") == scipy.constants.N_A

    def test_unknown_returns_none(self):
        assert true_value("frobnicator constant") is None


class TestSelfConsistency:
    """Every CONSTANTS entry's value must equal the live library value — never hardcoded divergently."""

    def test_pi_matches_math(self):
        assert CONSTANTS["pi"].value == math.pi

    def test_e_matches_math(self):
        assert CONSTANTS["e"].value == math.e

    def test_tau_matches_math(self):
        assert CONSTANTS["tau"].value == math.tau

    def test_golden_ratio_derived(self):
        phi = (1 + math.sqrt(5)) / 2
        assert CONSTANTS["golden_ratio"].value == phi

    def test_speed_of_light_matches_scipy(self):
        assert CONSTANTS["speed_of_light"].value == scipy.constants.c

    def test_planck_matches_scipy(self):
        assert CONSTANTS["planck"].value == scipy.constants.h

    def test_gravitational_matches_scipy(self):
        assert CONSTANTS["gravitational"].value == scipy.constants.G

    def test_boltzmann_matches_scipy(self):
        assert CONSTANTS["boltzmann"].value == scipy.constants.k

    def test_avogadro_matches_scipy(self):
        assert CONSTANTS["avogadro"].value == scipy.constants.N_A

    def test_all_entries_have_url(self):
        for key, c in CONSTANTS.items():
            assert c.url, f"{key} missing url"
            assert c.authority, f"{key} missing authority"
