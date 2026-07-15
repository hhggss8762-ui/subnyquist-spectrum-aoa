import unittest

import numpy as np

from specaoa.identifiability import MappingConfig
from specaoa.margins import periodic_distance_hz, spatial_distance_from_u


class MarginMetricTests(unittest.TestCase):
    def test_periodic_distance(self) -> None:
        np.testing.assert_allclose(periodic_distance_hz(np.array([0.0, 100.0, 150.0]), 100.0), [0.0, 0.0, 50.0])

    def test_spatial_equivalence_depends_on_f_sin_theta(self) -> None:
        config = MappingConfig()
        self.assertAlmostEqual(float(spatial_distance_from_u(np.array([0.0]), config)[0]), 0.0)
        # 0.6 GHz * sin(30°) equals 0.3 GHz * sin(90°); the latter is outside
        # the experiment FOV but confirms the normalized ULA identity.
        delta = .6e9 * .5 - .3e9 * 1.0
        self.assertAlmostEqual(float(spatial_distance_from_u(np.array([delta]), config)[0]), 0.0)
