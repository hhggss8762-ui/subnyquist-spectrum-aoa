import unittest

import numpy as np

from specaoa.simulation import C_M_PER_S, SimulationConfig, simulate_single_source, wrap_to_nyquist


class SimulationTests(unittest.TestCase):
    def test_alias_wrapping_and_order_at_boundaries(self) -> None:
        aliases, orders = wrap_to_nyquist(np.array([50.0, 150.0, -50.0, -150.0]), 100.0)
        np.testing.assert_allclose(aliases, np.array([-50.0, -50.0, -50.0, -50.0]))
        np.testing.assert_array_equal(orders, np.array([1, 2, 0, -1]))

    def test_spatial_phase_uses_true_carrier_not_alias(self) -> None:
        config = SimulationConfig(1.05e9, 30.0, [200e6], [4], num_elements=2, snr_db=None)
        result = simulate_single_source(config)
        expected_ratio = np.exp(-1j * 2 * np.pi * 1.05e9 * config.element_spacing_m * 0.5 / C_M_PER_S)
        alias_ratio = np.exp(-1j * 2 * np.pi * 50e6 * config.element_spacing_m * 0.5 / C_M_PER_S)
        np.testing.assert_allclose(result.steering_vector[1] / result.steering_vector[0], expected_ratio)
        self.assertFalse(np.isclose(result.steering_vector[1] / result.steering_vector[0], alias_ratio))

    def test_output_dimensions_and_noiseless_recovery(self) -> None:
        config = SimulationConfig(0.73e9, -20.0, [180e6, 230e6], [3, 7], num_elements=4, amplitude=2 - 1j)
        result = simulate_single_source(config)
        self.assertEqual([item.samples.shape for item in result.observations], [(4, 3), (4, 7)])
        for item in result.observations:
            n = np.arange(item.snapshots)
            expected = config.amplitude * result.steering_vector[:, None] * np.exp(1j * 2 * np.pi * item.aliased_frequency_hz * n / item.sample_rate_hz)
            np.testing.assert_allclose(item.samples, expected, atol=1e-12)

    def test_fixed_seed_reproduces_awgn(self) -> None:
        config = SimulationConfig(0.85e9, 10.0, [210e6], [16], snr_db=-5.0, random_seed=7)
        first = simulate_single_source(config).observations[0].samples
        second = simulate_single_source(config).observations[0].samples
        np.testing.assert_array_equal(first, second)
