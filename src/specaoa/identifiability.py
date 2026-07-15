"""Noiseless frequency--AoA equivalence counting for a ULA.

This module evaluates the analytic, phase-normalized observation mapping.  It
does not estimate parameters and contains no learning components.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Sequence

import numpy as np

from .simulation import C_M_PER_S, wrap_to_nyquist


@dataclass(frozen=True)
class MappingConfig:
    """Grid and physical parameters; Hz, degrees, m, and m/s are explicit."""

    frequency_min_hz: float = 0.3e9
    frequency_max_hz: float = 1.3e9
    angle_min_deg: float = -60.0
    angle_max_deg: float = 60.0
    num_elements: int = 8
    element_spacing_m: float = C_M_PER_S / (2.0 * 1.3e9)
    propagation_speed_m_per_s: float = C_M_PER_S
    numeric_tolerance: float = 1e-6

    def __post_init__(self) -> None:
        if not self.frequency_min_hz < self.frequency_max_hz:
            raise ValueError("Frequency bounds must be ascending (Hz).")
        if not self.angle_min_deg < self.angle_max_deg:
            raise ValueError("Angle bounds must be ascending (degrees).")
        if self.num_elements < 2:
            raise ValueError("At least two ULA elements are required for spatial information.")
        if self.element_spacing_m <= 0.0:
            raise ValueError("element_spacing_m must be positive (m).")


def temporal_frequency_candidates(frequency_hz: float, sample_rates_hz: Sequence[float], config: MappingConfig) -> np.ndarray:
    """Return all in-band carriers with the same noiseless alias tuple (Hz)."""
    if not sample_rates_hz:
        raise ValueError("At least one sample rate is required (samples/s).")
    aliases = [float(wrap_to_nyquist(frequency_hz, rate)[0]) for rate in sample_rates_hz]
    first_rate = float(sample_rates_hz[0])
    q_min = int(np.ceil((config.frequency_min_hz - aliases[0]) / first_rate))
    q_max = int(np.floor((config.frequency_max_hz - aliases[0]) / first_rate))
    candidates = aliases[0] + first_rate * np.arange(q_min, q_max + 1, dtype=float)
    compatible = []
    for candidate in candidates:
        if all(np.isclose(wrap_to_nyquist(candidate, rate)[0], alias, atol=config.numeric_tolerance, rtol=0.0)
               for rate, alias in zip(sample_rates_hz[1:], aliases[1:], strict=True)):
            compatible.append(candidate)
    return np.asarray(compatible, dtype=float)


def joint_candidate_count(frequency_hz: float, aoa_deg: float, sample_rates_hz: Sequence[float], config: MappingConfig) -> int:
    """Count noiseless (frequency, AoA) candidates with equal temporal and ULA phase.

    The array response is phase-normalized to the first element, consistent with
    unknown source amplitudes.  Integer spatial wraps are enumerated explicitly,
    so the routine remains valid if a caller deliberately changes the spacing.
    """
    temporal_candidates = temporal_frequency_candidates(frequency_hz, sample_rates_hz, config)
    target_u_hz = frequency_hz * np.sin(np.deg2rad(aoa_deg))
    spatial_period_hz = config.propagation_speed_m_per_s / config.element_spacing_m
    sin_min = np.sin(np.deg2rad(config.angle_min_deg))
    sin_max = np.sin(np.deg2rad(config.angle_max_deg))
    count = 0
    for candidate_hz in temporal_candidates:
        lower = (candidate_hz * sin_min - target_u_hz) / spatial_period_hz
        upper = (candidate_hz * sin_max - target_u_hz) / spatial_period_hz
        for spatial_wrap in range(int(np.ceil(lower)), int(np.floor(upper)) + 1):
            candidate_sin = (target_u_hz + spatial_wrap * spatial_period_hz) / candidate_hz
            if sin_min - config.numeric_tolerance <= candidate_sin <= sin_max + config.numeric_tolerance:
                count += 1
    return count


def evaluate_map(
    frequencies_hz: Sequence[float], angles_deg: Sequence[float], sample_rates_hz: Sequence[float], config: MappingConfig
) -> list[dict[str, float | int]]:
    """Evaluate candidate counts at every requested frequency--angle grid point."""
    rows: list[dict[str, float | int]] = []
    for frequency_hz, aoa_deg in product(frequencies_hz, angles_deg):
        temporal_count = len(temporal_frequency_candidates(float(frequency_hz), sample_rates_hz, config))
        joint_count = joint_candidate_count(float(frequency_hz), float(aoa_deg), sample_rates_hz, config)
        rows.append({
            "frequency_hz": float(frequency_hz),
            "aoa_deg": float(aoa_deg),
            "temporal_equivalent_candidates": temporal_count,
            "joint_equivalent_candidates": joint_count,
        })
    return rows
