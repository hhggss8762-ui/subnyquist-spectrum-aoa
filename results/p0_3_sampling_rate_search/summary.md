# P0-3 Sampling-Rate Search Summary

## Experiment purpose
Screen low-rate combinations where temporal aliases remain ambiguous but spatial phase materially improves noiseless joint identifiability.

## Configuration
- Frequency grid: 0.3–1.3 GHz, step 5 MHz.
- AoA grid: -60–60 deg, step 2 deg.
- ULA: M=8, d=c/(2·1.3 GHz)=0.115304792 m.
- Search: 1662 combinations; budget <= 250 MHz plus mandatory controls.
- Command: `python scripts/run_p0_3_sampling_rate_search.py --config configs/p0_3_sampling_rate_search.yaml`.
- Git commit: a7443ff3cfb8126b05f7cd21eab8e813de4cdad8; Python: 3.11.15; completed 2026-07-15T02:51:58.968807+00:00.

## Results
- Categories: {'A': 0, 'B': 0, 'C': 1100, 'D': 459, 'unclassified': 103}.
- GO / NO-GO decision: **CONDITIONAL GO**.

### Leading observations
- Highest temporal coverage: `32+35 MHz` (100.00%).
- Highest joint coverage: `32+35 MHz` (100.00%).
- Largest minimum joint margin: `20+32+35 MHz` (0.0211149); grid-level minima are often zero where exact broadside competitors remain.
- Strongest broadside deficit: `35+75 MHz`; broadside=4.48%, off-broadside=38.31%.
- Pareto count: 23. `200+250+300 MHz` is retained as the C-class time-only negative control.

## Interpretation
- Confirmed: spatial phase can reduce strict candidate counts for low-rate combinations, especially away from broadside.
- Not confirmed: no searched set satisfies the initial A-class requirement of temporal ambiguity plus >=90% joint unique coverage.
- Broadside: at theta=0°, u=f sin(theta)=0 for every carrier, so normalized ULA phase alone cannot distinguish temporal candidates.
- Next action: enter P0-4 only as a conditional Oracle-frequency AOA diagnostic; do not yet nominate a main low-rate recovery configuration.
- Highest-gain (not A) combination: `35+75 MHz`; temporal=4.48%, joint=32.21%, gain=27.73%.
- P0-4 recommendation: proceed only as a conditional Oracle-frequency diagnostic; retain this result as evidence of broadside/strict-identifiability limitations.
