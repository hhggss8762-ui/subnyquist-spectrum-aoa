"""Single-source Oracle-frequency MUSIC and ESPRIT for a calibrated ULA."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .simulation import C_M_PER_S


def ula_steering_vector(frequency_hz: float, angle_deg: float, num_elements: int, element_spacing_m: float, propagation_speed_m_per_s: float = C_M_PER_S) -> np.ndarray:
    """Return complex ULA steering vector (M,), using RF frequency in Hz."""
    index = np.arange(num_elements, dtype=float)
    return np.exp(-1j * 2.0 * np.pi * frequency_hz * element_spacing_m * index * np.sin(np.deg2rad(angle_deg)) / propagation_speed_m_per_s)


@dataclass(frozen=True)
class MusicEstimate:
    raw_angle_deg: float
    interpolated_angle_deg: float
    spectrum: np.ndarray
    angle_grid_deg: np.ndarray


def music_single_source(covariance: np.ndarray, assumed_frequency_hz: float, angle_grid_deg: np.ndarray, element_spacing_m: float, propagation_speed_m_per_s: float = C_M_PER_S) -> MusicEstimate:
    """Estimate one AoA from an M×M covariance using an oracle source count K=1."""
    if covariance.ndim != 2 or covariance.shape[0] != covariance.shape[1]: raise ValueError("covariance must be square.")
    values, vectors = np.linalg.eigh((covariance + covariance.conj().T) / 2.0)
    noise = vectors[:, :-1]
    angles = np.asarray(angle_grid_deg, dtype=float)
    manifold = np.column_stack([ula_steering_vector(assumed_frequency_hz, angle, covariance.shape[0], element_spacing_m, propagation_speed_m_per_s) for angle in angles])
    denominator = np.sum(np.abs(noise.conj().T @ manifold) ** 2, axis=0)
    spectrum = 1.0 / np.maximum(denominator, 1e-15)
    peak = int(np.argmax(spectrum)); raw = float(angles[peak]); interpolated = raw
    if 0 < peak < len(angles) - 1:
        left, centre, right = np.log(spectrum[peak - 1:peak + 2])
        curvature = left - 2.0 * centre + right
        if abs(curvature) > 1e-15:
            interpolated = float(raw + .5 * (left - right) / curvature * (angles[1] - angles[0]))
    return MusicEstimate(raw, interpolated, spectrum, angles)


def esprit_single_source(covariance: np.ndarray, assumed_frequency_hz: float, element_spacing_m: float, propagation_speed_m_per_s: float = C_M_PER_S) -> float:
    """Return single-source ESPRIT AoA in degrees; NaN means no real arcsine solution."""
    if assumed_frequency_hz == 0.0:
        return float("nan")
    _, vectors = np.linalg.eigh((covariance + covariance.conj().T) / 2.0)
    signal = vectors[:, -1]
    phase = float(np.angle(np.vdot(signal[:-1], signal[1:])))
    argument = -propagation_speed_m_per_s * phase / (2.0 * np.pi * assumed_frequency_hz * element_spacing_m)
    return float(np.rad2deg(np.arcsin(argument))) if abs(argument) <= 1.0 else float("nan")


def predicted_mismatch_angle_deg(true_frequency_hz: float, assumed_frequency_hz: float, true_angle_deg: float) -> float:
    """Return asin((f/fhat)sin(theta)) in degrees, or NaN if physically infeasible."""
    if assumed_frequency_hz == 0.0: return float("nan")
    argument = true_frequency_hz / assumed_frequency_hz * np.sin(np.deg2rad(true_angle_deg))
    return float(np.rad2deg(np.arcsin(argument))) if abs(argument) <= 1.0 else float("nan")
