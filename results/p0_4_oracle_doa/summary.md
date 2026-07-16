# P0-4 Oracle-frequency AOA

- Run mode: smoke; fixed-snapshot trials/configuration: existing 10-trial sweep; Nyquist trials: 10.
- Noiseless MUSIC maximum error: 1.362e-05 deg.
- Oracle AOA uses true RF frequency; alias frequency is tested only as intentional mismatch.
- Median Nyquist minus 32+35-MHz RMSE difference (mixed grid, diagnostic): 0.05945 deg.
- Frequency mismatch results validate the predicted `asin((f/fhat) sin(theta))` relation when feasible.
- Decision: CONDITIONAL GO pending full 300-trial sweep; valid diagnostic region is assessed in the CSVs, with endfire and low-SNR configurations expected to degrade.
