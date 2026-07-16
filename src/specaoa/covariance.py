"""Sample covariance construction and coherent-array branch fusion."""
from __future__ import annotations

from typing import Literal, Sequence

import numpy as np


def sample_covariance(samples: np.ndarray) -> np.ndarray:
    """Return Hermitian M×M covariance from complex samples shaped (M, N)."""
    if samples.ndim != 2 or samples.shape[1] < 1:
        raise ValueError("samples must have shape (elements, positive_snapshots).")
    covariance = samples @ samples.conj().T / samples.shape[1]
    return (covariance + covariance.conj().T) / 2.0


def fuse_covariances(covariances: Sequence[np.ndarray], snapshots: Sequence[int], mode: Literal["equal", "snapshot_weighted"] = "equal") -> tuple[np.ndarray, np.ndarray]:
    """Fuse same-size branch covariances; return (Hermitian covariance, weights)."""
    if not covariances or len(covariances) != len(snapshots):
        raise ValueError("covariances and snapshots must be non-empty and equally long.")
    shape = covariances[0].shape
    if any(item.shape != shape for item in covariances):
        raise ValueError("All covariance matrices must have the same shape.")
    if mode == "equal":
        weights = np.full(len(covariances), 1.0 / len(covariances))
    elif mode == "snapshot_weighted":
        total = sum(snapshots)
        if total <= 0: raise ValueError("Snapshot counts must be positive.")
        weights = np.asarray(snapshots, dtype=float) / total
    else:
        raise ValueError("mode must be 'equal' or 'snapshot_weighted'.")
    fused = sum(weight * covariance for weight, covariance in zip(weights, covariances, strict=True))
    return (fused + fused.conj().T) / 2.0, weights
