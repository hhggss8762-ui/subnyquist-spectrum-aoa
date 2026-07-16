"""AOA Monte-Carlo summary statistics; all external angles are degrees."""
from __future__ import annotations
import numpy as np

def doa_metrics(errors_deg: np.ndarray) -> dict[str, float]:
    valid = errors_deg[np.isfinite(errors_deg)]
    if len(valid) == 0: return {key: float('nan') for key in ('bias_deg','mae_deg','rmse_deg','median_abs_error_deg','p90_abs_error_deg','p95_abs_error_deg','success_rate_1deg','success_rate_2deg','catastrophic_rate_5deg','invalid_rate')}
    absolute = np.abs(valid)
    return {'bias_deg':float(np.mean(valid)),'mae_deg':float(np.mean(absolute)),'rmse_deg':float(np.sqrt(np.mean(valid**2))),'median_abs_error_deg':float(np.median(absolute)),'p90_abs_error_deg':float(np.quantile(absolute,.9)),'p95_abs_error_deg':float(np.quantile(absolute,.95)),'success_rate_1deg':float(np.mean(absolute<=1)),'success_rate_2deg':float(np.mean(absolute<=2)),'catastrophic_rate_5deg':float(np.mean(absolute>5)),'invalid_rate':float(1-len(valid)/len(errors_deg))}
