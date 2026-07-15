"""Numerically stable temporal and normalized-ULA separation metrics."""
from __future__ import annotations

from typing import Sequence

import numpy as np

from .identifiability import MappingConfig


def periodic_distance_hz(delta_hz: np.ndarray, period_hz: float) -> np.ndarray:
    """Return D_T(delta), with inputs/output in Hz."""
    remainder = np.remainder(delta_hz + period_hz / 2.0, period_hz) - period_hz / 2.0
    return np.abs(remainder)


def temporal_distance_matrix(frequencies_hz: np.ndarray, rates_hz: Sequence[int]) -> np.ndarray:
    """Weighted normalized remainder distance for every frequency-grid pair."""
    delta = frequencies_hz[:, None] - frequencies_hz[None, :]
    squared = np.zeros_like(delta, dtype=float)
    for rate_hz in rates_hz:
        squared += (periodic_distance_hz(delta, float(rate_hz)) / float(rate_hz)) ** 2
    return np.sqrt(squared / len(rates_hz))


def spatial_distance_from_u(delta_u_hz: np.ndarray, config: MappingConfig) -> np.ndarray:
    """Distance of phase-normalized ULA manifolds with optional global phase.

    With a normalized first element, the optimal common phase is already fixed;
    the usual phase-invariant form is nevertheless used.  The response depends
    only on ``u = f sin(theta)`` (Hz), not on the aliased frequency.
    """
    x = config.element_spacing_m * delta_u_hz / config.propagation_speed_m_per_s
    denominator = np.sin(np.pi * x)
    numerator = np.sin(config.num_elements * np.pi * x)
    ratio = np.full_like(x, float(config.num_elements), dtype=float)
    np.divide(numerator, denominator, out=ratio, where=np.abs(denominator) >= 1e-12)
    correlation = np.clip(np.abs(ratio) / config.num_elements, 0.0, 1.0)
    return np.sqrt(np.maximum(0.0, 2.0 - 2.0 * correlation))


def temporal_margins(frequencies_hz: np.ndarray, rates_hz: Sequence[int]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Nearest non-self temporal distance, candidate index, and full matrix."""
    distance = temporal_distance_matrix(frequencies_hz, rates_hz)
    np.fill_diagonal(distance, np.inf)
    nearest = np.argmin(distance, axis=1)
    return distance[np.arange(len(frequencies_hz)), nearest], nearest, distance


def fast_joint_margins(
    frequencies_hz: np.ndarray,
    angles_deg: np.ndarray,
    rates_hz: Sequence[int],
    config: MappingConfig,
    alpha: float = 0.5,
    nearest_frequency_count: int = 12,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Find a scalable joint nearest competitor on a restricted frequency set.

    For each source frequency, all exact temporal ties and the nearest
    ``nearest_frequency_count`` temporal competitors are examined.  At each
    competitor frequency, only the closest three angle-grid values in ``f sinθ``
    are needed because temporal distance is angle-independent and the ULA
    distance is monotone around each local manifold match.  This is the
    documented ``margin_fast`` mode; it avoids a full 12,261-square comparison.
    """
    temporal = temporal_distance_matrix(frequencies_hz, rates_hz)
    f_count, angle_count = len(frequencies_hz), len(angles_deg)
    u = frequencies_hz[:, None] * np.sin(np.deg2rad(angles_deg))[None, :]
    margins = np.full((f_count, angle_count), np.inf)
    nearest_f = np.full((f_count, angle_count), -1, dtype=int)
    nearest_a = np.full((f_count, angle_count), -1, dtype=int)
    nearest_dt = np.full((f_count, angle_count), np.nan)
    nearest_ds = np.full((f_count, angle_count), np.nan)
    offsets = np.array([-1, 0, 1])
    for source_f in range(f_count):
        order = np.argsort(temporal[source_f])
        zeros = np.flatnonzero(temporal[source_f] <= 1e-12)
        candidates = np.unique(np.concatenate((zeros, order[:nearest_frequency_count])))
        source_u = u[source_f]
        best = np.full(angle_count, np.inf)
        for target_f in candidates:
            insertion = np.searchsorted(u[target_f], source_u)
            candidate_angles = np.clip(insertion[:, None] + offsets, 0, angle_count - 1)
            target_u = u[target_f, candidate_angles]
            spatial = spatial_distance_from_u(source_u[:, None] - target_u, config)
            combined = np.sqrt(alpha * temporal[source_f, target_f] ** 2 + (1.0 - alpha) * spatial ** 2)
            if target_f == source_f:
                combined[candidate_angles == np.arange(angle_count)[:, None]] = np.inf
            local = np.argmin(combined, axis=1)
            value = combined[np.arange(angle_count), local]
            replace = value < best
            best[replace] = value[replace]
            nearest_f[source_f, replace] = target_f
            nearest_a[source_f, replace] = candidate_angles[replace, local[replace]]
            nearest_dt[source_f, replace] = temporal[source_f, target_f]
            nearest_ds[source_f, replace] = spatial[replace, local[replace]]
        margins[source_f] = best
    return margins, nearest_f, nearest_a, nearest_dt, nearest_ds
