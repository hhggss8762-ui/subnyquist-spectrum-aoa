"""Deterministic single-source, unknown-complex-amplitude AoA CRB."""
from __future__ import annotations

import numpy as np

from .doa import ula_steering_vector
from .simulation import C_M_PER_S


def aoa_crb_rad2(frequency_hz: float, angle_deg: float, num_elements: int, element_spacing_m: float, snapshots: int, snr_db: float, propagation_speed_m_per_s: float = C_M_PER_S) -> float:
    """Return CRB in rad² for unit signal power and per-element SNR in dB."""
    theta = np.deg2rad(angle_deg); index = np.arange(num_elements, dtype=float)
    steering = ula_steering_vector(frequency_hz, angle_deg, num_elements, element_spacing_m, propagation_speed_m_per_s)
    derivative = steering * (-1j * 2.0 * np.pi * frequency_hz * element_spacing_m * index * np.cos(theta) / propagation_speed_m_per_s)
    projected_energy = float(np.real(np.vdot(derivative, derivative) - abs(np.vdot(steering, derivative)) ** 2 / np.vdot(steering, steering)))
    noise_variance = 1.0 / (10.0 ** (snr_db / 10.0))
    return noise_variance / max(2.0 * snapshots * projected_energy, 1e-300)
