# Experiment Log

> 每次正式实验追加一条记录。不得覆盖旧记录。结果目录必须包含配置、随机种子、Git commit 和原始指标。

---

## Experiment ID

`YYYYMMDD-HHMM_<short_name>`

### Objective

要验证的单一假设：

### Code version

- Git commit:
- Branch:
- Environment:

### Configuration

- Config file:
- Frequency range:
- Sampling rates:
- Array:
- Sources:
- SNR:
- Snapshots:
- Seed:
- Dataset split:

### Baselines

- 
- 

### Metrics

- 
- 

### Results

| Metric | Value |
|---|---:|
|  |  |

### Observations

区分：

- 直接实验观察；
- 数学推论；
- 尚未验证解释。

### Failure analysis

- alias-frequency estimation:
- alias-order decision:
- source pairing:
- AoA estimation:
- numerical issue:
- data leakage check:

### Decision

- Continue / modify / stop:
- Reason:
- Next experiment:

### Artifacts

- Raw results:
- Figures:
- Logs:
- Model checkpoint:

---

## Experiment ID

`20260715_p0_3_sampling_rate_search`

### Objective

Search for low-total-rate sets where temporal aliases remain non-unique while
true-carrier ULA phase materially improves noiseless joint identifiability.

### Code version

- Git commit: `a7443ff3cfb8126b05f7cd21eab8e813de4cdad8` (recorded at run time)
- Environment: `cnnaoa`, Python 3.11.15

### Configuration

- Config: `configs/p0_3_sampling_rate_search.yaml`
- Frequency grid: 0.3–1.3 GHz, 5 MHz step; AoA grid: -60°–60°, 2° step
- ULA: M=8, d=c/(2·1.3 GHz); noiseless single-source identifiability only
- Search: 1,662 combinations (<=250 MHz budget plus mandatory P0-2 controls)

### Results

| Metric | Value |
|---|---:|
| A / B / C / D classes | 0 / 0 / 1,100 / 459 (103 unclassified) |
| Pareto combinations | 23 |
| Highest spatial gain | 27.73% (`35+75 MHz`), but joint coverage only 32.21% |

### Decision

- Continue / modify / stop: **CONDITIONAL GO**
- Reason: spatial gain exists but does not yet yield an adequate main
  configuration under the fixed array/FOV/grid; the gain is mainly off-broadside.
- Next experiment: P0-4 Oracle-frequency AOA only as a diagnostic, retaining
  temporal-only and C-class controls.

### Artifacts

- Raw results / figures / report: `results/p0_3_sampling_rate_search/`
