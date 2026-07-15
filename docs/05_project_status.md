# Project Status

## Current phase

**Stage 0 — Problem validation and traditional baseline**

---

## Previous exploratory experience

以下内容来自旧阶段经验，不复用旧代码，也不直接作为论文证据：

- 单源窄带 MUSIC AOA 仿真；
- 时间欠采样导致频率混叠的观察；
- 阵元间距过大导致空间混叠的观察；
- 端到端频率和 AOA 回归效果与研究价值不理想；
- 初步认识到未知真实载频会影响空间导向矢量构造。

这些结果仅用于帮助定义新问题。

---

## Current confirmed scope

- 频率范围：0.3–1.3 GHz；
- 多个窄带远场源；
- 标准 ULA；
- 多采样率低速观测；
- 真实载频与 AOA 联合恢复；
- 不设计新硬件；
- 目标为 CCF-B 及以上系统型论文；
- AI 作为后续鲁棒联合推断模块。

---

## Immediate milestone

完成 **Baseline-00: 可辨识性与传统联合恢复报告**。

### Required outputs

1. 信号模型单元测试；
2. 单源无噪声歧义热图；
3. 采样率组合搜索结果；
4. Oracle-frequency AOA baseline；
5. multi-rate recovery + MUSIC baseline；
6. joint spatio-temporal search baseline；
7. 低 SNR 和少快拍退化曲线；
8. 是否进入 AI 阶段的 go/no-go 结论。

---

## First sprint tasks

### P0-1 Simulator

- 实现多阵元、多采样率、单源复解析信号；
- 保证空间相位由真实载频决定；
- 支持 AWGN、可复现随机种子；
- 添加单元测试。

### P0-2 Ambiguity mapper

- 在频率–角度网格上生成联合观测特征；
- 统计等价候选数量；
- 输出 CSV、PNG 和摘要。

### P0-3 Sampling-rate search

- 搜索双、三、四采样率组合；
- 比较唯一覆盖率、鲁棒间隔和采样成本；
- 选出后续实验候选集合。

**Completed (2026-07-15):** evaluated 1,662 low-rate and mandatory-control
combinations on the 5 MHz × 2° grid. No combination met the initial A-class
criterion (temporal ambiguity, joint unique coverage >= 90%, and spatial gain
>= 5%). Spatial candidate reduction is observed mainly away from broadside;
the current P0-3 judgement is **CONDITIONAL GO**. Formal artifacts are in
`results/p0_3_sampling_rate_search/`; P0-4 may proceed only as a conditional
Oracle-frequency diagnostic with temporal-only controls retained.

### P0-4 Baselines

- Oracle frequency + phase/MUSIC；
- multi-rate hard recovery + MUSIC；
- joint spatio-temporal candidate search。

### P0-5 Noise boundary

- SNR：-20 至 20 dB；
- snapshots：16 至 256；
- 输出频率消歧成功率和 AOA 误差。

---

## Current blockers

1. 尚未完成对已有多采样率频率–DOA工作的方法矩阵；
2. 尚未确认实验室接收机是否支持真实多采样率混叠；
3. 尚未确定采样率集合；
4. 尚未证明空间信息相对多采样率时间信息具有额外价值；
5. 尚未证明传统联合搜索不足以解决目标场景。

---

## Next decision gate

完成 Stage 0 后只能选择以下之一：

### Path A: Multi-source pairing AI

若主要失败来自跨采样率峰配对和源数未知。

### Path B: Low-SNR soft disambiguation AI

若主要失败来自余数和相位估计误差导致的混叠阶数跳变。

### Path C: Self-calibration AI

若真实数据中主要问题来自阵列和接收通道失配。

### Path D: Stop or redefine

若传统方法已足够，或目标区域不可辨识。
