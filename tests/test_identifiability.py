import unittest

from specaoa.identifiability import MappingConfig, evaluate_map, joint_candidate_count, temporal_frequency_candidates


class IdentifiabilityTests(unittest.TestCase):
    def test_single_rate_temporal_candidates_are_expected(self) -> None:
        config = MappingConfig(frequency_min_hz=0.3e9, frequency_max_hz=1.3e9)
        candidates = temporal_frequency_candidates(0.35e9, [0.2e9], config)
        self.assertEqual(list(candidates / 1e9), [0.35, 0.55, 0.75, 0.95, 1.15])

    def test_joint_information_does_not_increase_candidate_count(self) -> None:
        config = MappingConfig()
        temporal_count = len(temporal_frequency_candidates(0.75e9, [0.2e9], config))
        self.assertLessEqual(joint_candidate_count(0.75e9, 30.0, [0.2e9], config), temporal_count)
        self.assertGreaterEqual(joint_candidate_count(0.75e9, 30.0, [0.2e9], config), 1)

    def test_map_records_time_and_joint_counts(self) -> None:
        rows = evaluate_map([0.75e9], [-20.0, 20.0], [0.2e9, 0.25e9], MappingConfig())
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["temporal_equivalent_candidates"] >= row["joint_equivalent_candidates"] >= 1 for row in rows))
