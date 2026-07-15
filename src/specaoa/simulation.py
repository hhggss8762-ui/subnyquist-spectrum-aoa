"""Reproducible single-source complex-array simulator.

All frequencies and sampling rates are in Hz (samples/s for sampling rates),
array positions are in m, snapshot indices are dimensionless, and public angle
arguments are in degrees.  Internally, angles are converted to radians.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

C_M_PER_S = 299_792_458.0


def wrap_to_nyquist(frequency_hz: float | np.ndarray, sample_rate_hz: float) -> tuple[np.ndarray, np.ndarray]:
    """Wrap frequency to the half-open Nyquist interval [-fs/2, fs/2).

    Returns `(aliased_frequency_hz, alias_order)`, where
    `frequency_hz = aliased_frequency_hz + alias_order * sample_rate_hz`.
    """
    if sample_rate_hz <= 0.0:
        raise ValueError("sample_rate_hz must be positive (samples/s).")
    frequency = np.asarray(frequency_hz, dtype=float)
    alias_order = np.floor((frequency + sample_rate_hz / 2.0) / sample_rate_hz).astype(int)
    return frequency - alias_order * sample_rate_hz, alias_order


@dataclass(frozen=True)
class SimulationConfig:
    """Physical and acquisition parameters for one narrowband far-field source."""

    carrier_frequency_hz: float
    aoa_deg: float
    sample_rates_hz: Sequence[float]
    snapshots_per_rate: Sequence[int]
    num_elements: int = 8
    element_spacing_m: float = C_M_PER_S / (2.0 * 1.3e9)
    amplitude: complex = 1.0 + 0.0j
    snr_db: float | None = None
    random_seed: int | None = None
    propagation_speed_m_per_s: float = C_M_PER_S

    def __post_init__(self) -> None:
        if self.carrier_frequency_hz <= 0.0:
            raise ValueError("carrier_frequency_hz must be positive (Hz).")
        if self.num_elements < 1:
            raise ValueError("num_elements must be at least one.")
        if self.element_spacing_m < 0.0:
            raise ValueError("element_spacing_m must be non-negative (m).")
        if self.propagation_speed_m_per_s <= 0.0:
            raise ValueError("propagation_speed_m_per_s must be positive (m/s).")
        if len(self.sample_rates_hz) == 0 or len(self.sample_rates_hz) != len(self.snapshots_per_rate):
            raise ValueError("sample_rates_hz and snapshots_per_rate must be non-empty and have equal length.")
        if any(rate <= 0.0 for rate in self.sample_rates_hz):
            raise ValueError("Every sample rate must be positive (samples/s).")
        if any(count < 1 for count in self.snapshots_per_rate):
            raise ValueError("Every snapshot count must be at least one.")


@dataclass(frozen=True)
class RateObservation:
    """One rate's observation: samples have shape (elements, snapshots)."""

    sample_rate_hz: float
    snapshots: int
    aliased_frequency_hz: float
    alias_order: int
    samples: np.ndarray


@dataclass(frozen=True)
class SimulationResult:
    """Simulator output and the shared ULA steering vector."""

    array_positions_m: np.ndarray
    steering_vector: np.ndarray
    observations: tuple[RateObservation, ...]


def simulate_single_source(config: SimulationConfig) -> SimulationResult:
    """Generate coherent multi-rate ULA samples for a single analytic tone.

    The spatial steering vector is intentionally calculated using the *carrier*
    frequency.  Only the discrete-time temporal phasor uses an aliased frequency.
    A separate complex AWGN realization is generated for every rate when
    ``snr_db`` is supplied; ``None`` produces exactly noiseless samples.
    """
    positions_m = np.arange(config.num_elements, dtype=float) * config.element_spacing_m
    theta_rad = np.deg2rad(config.aoa_deg)
    steering = np.exp(
        -1j
        * 2.0
        * np.pi
        * config.carrier_frequency_hz
        * positions_m
        * np.sin(theta_rad)
        / config.propagation_speed_m_per_s
    )
    generator = np.random.default_rng(config.random_seed)
    observations: list[RateObservation] = []
    for sample_rate_hz, snapshots in zip(config.sample_rates_hz, config.snapshots_per_rate, strict=True):
        aliased, order = wrap_to_nyquist(config.carrier_frequency_hz, float(sample_rate_hz))
        snapshot_index = np.arange(snapshots, dtype=float)
        temporal = np.exp(1j * 2.0 * np.pi * float(aliased) * snapshot_index / sample_rate_hz)
        noiseless = config.amplitude * steering[:, None] * temporal[None, :]
        samples = noiseless.copy()
        if config.snr_db is not None:
            signal_power = float(np.mean(np.abs(noiseless) ** 2))
            noise_power = signal_power / (10.0 ** (config.snr_db / 10.0))
            noise = np.sqrt(noise_power / 2.0) * (
                generator.standard_normal(noiseless.shape) + 1j * generator.standard_normal(noiseless.shape)
            )
            samples += noise
        observations.append(
            RateObservation(float(sample_rate_hz), int(snapshots), float(aliased), int(order), samples)
        )
    return SimulationResult(positions_m, steering, tuple(observations))
