"""Run a Stage-0 P0-2 noiseless identifiability mapping experiment."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from specaoa.identifiability import MappingConfig, evaluate_map
from specaoa.simulation import C_M_PER_S


def parse_rate_groups(raw: str) -> list[tuple[float, ...]]:
    groups = []
    for group in raw.split(";"):
        rates_mhz = tuple(float(value.strip()) for value in group.split(",") if value.strip())
        if not rates_mhz or len(rates_mhz) > 3:
            raise ValueError("Each rate group needs one to three comma-separated rates in MHz.")
        groups.append(tuple(rate * 1e6 for rate in rates_mhz))
    if not groups:
        raise ValueError("At least one sampling-rate group is required.")
    return groups


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-id", default=None, help="Output directory name under results/.")
    parser.add_argument("--rate-groups", required=True, help="Semicolon-separated groups, values in MHz; e.g. 200;200,250;200,250,300")
    parser.add_argument("--frequency-step-mhz", type=float, default=5.0)
    parser.add_argument("--angle-step-deg", type=float, default=2.0)
    args = parser.parse_args()
    if args.frequency_step_mhz <= 0.0 or args.angle_step_deg <= 0.0:
        raise ValueError("Grid steps must be positive.")

    groups = parse_rate_groups(args.rate_groups)
    experiment_id = args.experiment_id or f"e1_noiseless_map_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
    output_dir = Path("results") / experiment_id
    output_dir.mkdir(parents=True, exist_ok=False)
    config = MappingConfig(element_spacing_m=C_M_PER_S / (2.0 * 1.3e9))
    frequencies_hz = np.arange(config.frequency_min_hz, config.frequency_max_hz + 0.1, args.frequency_step_mhz * 1e6)
    angles_deg = np.arange(config.angle_min_deg, config.angle_max_deg + 0.1, args.angle_step_deg)

    all_rows = []
    maps = []
    for group_index, rates_hz in enumerate(groups, start=1):
        rows = evaluate_map(frequencies_hz, angles_deg, rates_hz, config)
        label = "+".join(f"{rate / 1e6:g}" for rate in rates_hz) + " MHz"
        for row in rows:
            row["rate_group"] = label
            row["rate_count"] = len(rates_hz)
        all_rows.extend(rows)
        maps.append((label, rows))

    csv_path = output_dir / "identifiability_map.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)

    figure, axes = plt.subplots(len(maps), 2, figsize=(12, 4 * len(maps)), squeeze=False, constrained_layout=True)
    for row_index, (label, rows) in enumerate(maps):
        for col_index, (column, title) in enumerate((("temporal_equivalent_candidates", "Temporal only"), ("joint_equivalent_candidates", "Joint temporal-spatial"))):
            array = np.asarray([row[column] for row in rows]).reshape(len(frequencies_hz), len(angles_deg)).T
            image = axes[row_index, col_index].imshow(
                array, origin="lower", aspect="auto", interpolation="nearest",
                extent=[frequencies_hz[0] / 1e9, frequencies_hz[-1] / 1e9, angles_deg[0], angles_deg[-1]],
            )
            axes[row_index, col_index].set(title=f"{label}: {title}", xlabel="Carrier frequency (GHz)", ylabel="AoA (deg)")
            figure.colorbar(image, ax=axes[row_index, col_index], label="Equivalent candidate count")
    png_path = output_dir / "identifiability_heatmaps.png"
    figure.savefig(png_path, dpi=180)
    plt.close(figure)

    summary_lines = [
        "Stage 0 P0-2 noiseless identifiability mapping", "",
        "This is a diagnostic comparison, not a final sampling-rate selection.",
        f"Frequency grid: {frequencies_hz[0] / 1e9:g} to {frequencies_hz[-1] / 1e9:g} GHz, step {args.frequency_step_mhz:g} MHz.",
        f"AoA grid: {angles_deg[0]:g} to {angles_deg[-1]:g} deg, step {args.angle_step_deg:g} deg.",
        f"ULA: M={config.num_elements}, d={config.element_spacing_m:.12g} m = c/(2*1.3 GHz).", "",
    ]
    for label, rows in maps:
        temporal = np.asarray([row["temporal_equivalent_candidates"] for row in rows])
        joint = np.asarray([row["joint_equivalent_candidates"] for row in rows])
        summary_lines.extend([
            f"{label}",
            f"  Temporal-only unique coverage: {np.mean(temporal == 1):.2%}",
            f"  Joint unique coverage: {np.mean(joint == 1):.2%}",
            f"  Mean temporal candidates: {np.mean(temporal):.3f}",
            f"  Mean joint candidates: {np.mean(joint):.3f}",
        ])
    (output_dir / "summary.txt").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
