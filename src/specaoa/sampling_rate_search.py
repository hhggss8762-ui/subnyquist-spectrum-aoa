"""P0-3 sampling-rate search: strict candidate counts, margins, and screening."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
from math import gcd, lcm
from time import perf_counter
from typing import Iterable, Sequence

import numpy as np

from .identifiability import MappingConfig
from .margins import fast_joint_margins, temporal_margins


@dataclass(frozen=True)
class SearchConfig:
    candidate_rates_mhz: tuple[int, ...] = (20, 25, 30, 32, 35, 40, 45, 48, 50, 60, 64, 75, 80, 96, 100)
    max_rates: int = 4
    max_total_rate_mhz: int = 250
    frequency_step_hz: int = 5_000_000
    angle_step_deg: float = 2.0
    joint_distance_alpha: float = 0.5
    nearest_frequency_count: int = 12
    category_a_temporal_max: float = 0.95
    category_a_joint_min: float = 0.90
    category_a_gain_min: float = 0.05
    category_a_resolve_min: float = 0.30
    category_d_joint_max: float = 0.80


def rate_metadata(rates_mhz: Sequence[int]) -> dict[str, int]:
    g = 0
    period = 1
    for rate in rates_mhz:
        g = gcd(g, int(rate))
        period = lcm(period, int(rate))
    return {"gcd_mhz": g, "lcm_mhz": period, "temporal_period_mhz": period}


def enumerate_rate_sets(config: SearchConfig, required_mhz: Iterable[Sequence[int]] = ()) -> list[tuple[int, ...]]:
    found = {
        combo
        for count in range(1, config.max_rates + 1)
        for combo in combinations(sorted(set(config.candidate_rates_mhz)), count)
        if sum(combo) <= config.max_total_rate_mhz
    }
    found.update(tuple(sorted(set(map(int, combo)))) for combo in required_mhz)
    return sorted(found, key=lambda combo: (sum(combo), len(combo), combo))


def _counts(frequencies_hz: np.ndarray, angles_deg: np.ndarray, rates_mhz: Sequence[int], mapping: MappingConfig) -> tuple[np.ndarray, np.ndarray]:
    period_hz = rate_metadata(rates_mhz)["temporal_period_mhz"] * 1_000_000
    sin_angles = np.sin(np.deg2rad(angles_deg))
    temporal = np.empty(len(frequencies_hz), dtype=int)
    joint = np.empty((len(frequencies_hz), len(angles_deg)), dtype=int)
    spatial_period_hz = mapping.propagation_speed_m_per_s / mapping.element_spacing_m
    sin_min, sin_max = np.sin(np.deg2rad([mapping.angle_min_deg, mapping.angle_max_deg]))
    for index, frequency_hz in enumerate(frequencies_hz):
        k_min = int(np.ceil((mapping.frequency_min_hz - frequency_hz) / period_hz))
        k_max = int(np.floor((mapping.frequency_max_hz - frequency_hz) / period_hz))
        candidate_f = frequency_hz + period_hz * np.arange(k_min, k_max + 1)
        temporal[index] = len(candidate_f)
        target_u = frequency_hz * sin_angles
        count = np.zeros(len(angles_deg), dtype=int)
        for candidate in candidate_f:
            low = np.ceil((candidate * sin_min - target_u) / spatial_period_hz).astype(int)
            high = np.floor((candidate * sin_max - target_u) / spatial_period_hz).astype(int)
            count += np.maximum(0, high - low + 1)
        joint[index] = count
    return temporal, joint


def _summary(values: np.ndarray, prefix: str) -> dict[str, float]:
    return {
        f"mean_{prefix}": float(np.mean(values)), f"median_{prefix}": float(np.median(values)),
        f"p90_{prefix}": float(np.quantile(values, .90)), f"p95_{prefix}": float(np.quantile(values, .95)),
        f"max_{prefix}": float(np.max(values)),
    }


def classify(row: dict[str, object], config: SearchConfig) -> str:
    temporal, joint, gain = (float(row[key]) for key in ("temporal_unique_coverage", "joint_unique_coverage", "spatial_absolute_gain"))
    if joint < config.category_d_joint_max:
        return "D"
    if temporal <= config.category_a_temporal_max and joint >= config.category_a_joint_min and gain >= config.category_a_gain_min and float(row["resolve_rate_among_temporal_ambiguous"]) >= config.category_a_resolve_min:
        return "A"
    if temporal >= 1.0 - 1e-12 and joint >= 1.0 - 1e-12 and abs(gain) <= 1e-12:
        return "C"
    if temporal > config.category_a_temporal_max and gain < .05 and float(row["joint_margin_min"]) > float(row["temporal_margin_min"]):
        return "B"
    return "unclassified"


def evaluate_combination(rates_mhz: Sequence[int], search: SearchConfig, mapping: MappingConfig) -> tuple[dict[str, object], dict[str, np.ndarray]]:
    """Evaluate one combination and retain grid arrays for requested detail files."""
    start = perf_counter()
    rates_mhz = tuple(sorted(map(int, rates_mhz)))
    rates_hz = tuple(rate * 1_000_000 for rate in rates_mhz)
    frequencies = np.arange(mapping.frequency_min_hz, mapping.frequency_max_hz + .1, search.frequency_step_hz, dtype=float)
    angles = np.arange(mapping.angle_min_deg, mapping.angle_max_deg + .1, search.angle_step_deg, dtype=float)
    temporal, joint = _counts(frequencies, angles, rates_mhz, mapping)
    temporal_grid = np.repeat(temporal[:, None], len(angles), axis=1)
    temporal_margin, temporal_nearest, _ = temporal_margins(frequencies, rates_hz)
    joint_margin, near_f, near_a, near_dt, near_ds = fast_joint_margins(
        frequencies, angles, rates_hz, mapping, search.joint_distance_alpha, search.nearest_frequency_count
    )
    temporal_unique = temporal_grid == 1
    joint_unique = joint == 1
    ambiguous = ~temporal_unique
    reduction = np.where(ambiguous, 1.0 - joint / temporal_grid, np.nan)
    metadata = rate_metadata(rates_mhz)
    row: dict[str, object] = {
        "combination_id": "r_" + "_".join(map(str, rates_mhz)), "sampling_rates_mhz": "+".join(map(str, rates_mhz)),
        "num_rates": len(rates_mhz), "sum_sampling_rate_mhz": sum(rates_mhz), "max_sampling_rate_mhz": max(rates_mhz), **metadata,
        "temporal_unique_coverage": float(np.mean(temporal_unique)), "joint_unique_coverage": float(np.mean(joint_unique)),
        "spatial_absolute_gain": float(np.mean(joint_unique) - np.mean(temporal_unique)),
        "resolve_rate_among_temporal_ambiguous": float(np.mean(joint_unique[ambiguous])) if np.any(ambiguous) else 0.0,
        **_summary(temporal_grid, "temporal_candidates"), **_summary(joint, "joint_candidates"),
        "mean_candidate_reduction": float(np.nanmean(reduction)) if np.any(ambiguous) else 0.0,
        "median_candidate_reduction": float(np.nanmedian(reduction)) if np.any(ambiguous) else 0.0,
        "p10_candidate_reduction": float(np.nanquantile(reduction, .10)) if np.any(ambiguous) else 0.0,
        "p90_candidate_reduction": float(np.nanquantile(reduction, .90)) if np.any(ambiguous) else 0.0,
        "temporal_margin_min": float(np.min(temporal_margin)), "temporal_margin_p05": float(np.quantile(temporal_margin, .05)),
        "temporal_margin_p10": float(np.quantile(temporal_margin, .10)), "temporal_margin_median": float(np.median(temporal_margin)), "temporal_margin_mean": float(np.mean(temporal_margin)),
        "joint_margin_min": float(np.min(joint_margin)), "joint_margin_p05": float(np.quantile(joint_margin, .05)),
        "joint_margin_p10": float(np.quantile(joint_margin, .10)), "joint_margin_median": float(np.median(joint_margin)), "joint_margin_mean": float(np.mean(joint_margin)),
        "broadside_joint_coverage": float(np.mean(joint_unique[:, np.abs(angles) <= 10])),
        "off_broadside_joint_coverage": float(np.mean(joint_unique[:, np.abs(angles) > 10])),
        "runtime_seconds": perf_counter() - start, "status": "ok",
    }
    row["category"] = classify(row, search)
    arrays = {"frequencies_hz": frequencies, "angles_deg": angles, "temporal": temporal_grid, "joint": joint,
              "reduction": reduction, "temporal_margin": np.repeat(temporal_margin[:, None], len(angles), axis=1),
              "joint_margin": joint_margin, "nearest_f": near_f, "nearest_a": near_a, "nearest_dt": near_dt, "nearest_ds": near_ds}
    return row, arrays


def pareto_flags(rows: list[dict[str, object]]) -> None:
    """Mark non-dominated points: cost/candidate count minimized, quality maximized."""
    for row in rows:
        dominated = False
        for other in rows:
            if other is row or other.get("status") != "ok":
                continue
            no_worse = (float(other["sum_sampling_rate_mhz"]) <= float(row["sum_sampling_rate_mhz"]) and float(other["joint_unique_coverage"]) >= float(row["joint_unique_coverage"]) and float(other["spatial_absolute_gain"]) >= float(row["spatial_absolute_gain"]) and float(other["joint_margin_min"]) >= float(row["joint_margin_min"]) and float(other["max_joint_candidates"]) <= float(row["max_joint_candidates"]))
            strictly = (float(other["sum_sampling_rate_mhz"]) < float(row["sum_sampling_rate_mhz"]) or float(other["joint_unique_coverage"]) > float(row["joint_unique_coverage"]) or float(other["spatial_absolute_gain"]) > float(row["spatial_absolute_gain"]) or float(other["joint_margin_min"]) > float(row["joint_margin_min"]) or float(other["max_joint_candidates"]) < float(row["max_joint_candidates"]))
            if no_worse and strictly:
                dominated = True; break
        row["is_pareto_optimal"] = not dominated
