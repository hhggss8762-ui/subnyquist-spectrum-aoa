import unittest

import numpy as np

from specaoa.identifiability import MappingConfig
from specaoa.sampling_rate_search import SearchConfig, enumerate_rate_sets, evaluate_combination, rate_metadata


class SamplingRateSearchTests(unittest.TestCase):
    def test_lcm_and_endpoint_alias_equivalence(self) -> None:
        self.assertEqual(rate_metadata((200, 250))["lcm_mhz"], 1000)
        row, _ = evaluate_combination((200, 250), SearchConfig(max_total_rate_mhz=500), MappingConfig())
        self.assertAlmostEqual(float(row["temporal_unique_coverage"]), 0.99004975, places=5)

    def test_p0_2_controls_regress(self) -> None:
        config = SearchConfig(max_total_rate_mhz=1000)
        one, _ = evaluate_combination((200,), config, MappingConfig())
        three, _ = evaluate_combination((200, 250, 300), config, MappingConfig())
        self.assertAlmostEqual(float(one["temporal_unique_coverage"]), 0.0)
        self.assertAlmostEqual(float(three["temporal_unique_coverage"]), 1.0)
        self.assertAlmostEqual(float(three["joint_unique_coverage"]), 1.0)

    def test_added_rate_cannot_increase_temporal_candidates(self) -> None:
        base, arrays_base = evaluate_combination((20, 25), SearchConfig(), MappingConfig())
        extended, arrays_extended = evaluate_combination((20, 25, 32), SearchConfig(), MappingConfig())
        self.assertTrue(np.all(arrays_extended["temporal"] <= arrays_base["temporal"]))
        self.assertLessEqual(float(extended["max_joint_candidates"]), float(extended["max_temporal_candidates"]))
