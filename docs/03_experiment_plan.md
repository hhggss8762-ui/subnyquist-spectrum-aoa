# Experiment Plan

## 1. Experimental objective

首批实验不以证明新方法优越为目标，而以回答以下问题为目标：

1. 问题是否可辨识；
2. 空间信息是否真正帮助时间频率消歧；
3. 传统方法在哪些条件下失败；
4. AI 是否有必要；
5. 0.3–1.3 GHz 场景是否能形成可实现的系统任务。

---

## 2. Common parameter domain

初始默认配置：

| Parameter | Initial value |
|---|---|
| Frequency range | 0.3–1.3 GHz |
| Array | ULA |
| Number of elements | \(M=8\) |
| Element spacing | \(d=c/(2F_{\max})\) |
| Angle range | \([-60^\circ,60^\circ]\) |
| Sources | \(K=1\), then \(K=2,3\) |
| Signal type | complex sinusoid / very narrowband |
| Noise | complex AWGN |
| Snapshots | 16, 32, 64, 128, 256 |
| SNR | -20 to 20 dB |
| Sampling rates | selected by rate-search experiment |

采样率组合不得凭直觉固定。先在候选集合中搜索并比较：

- 唯一可辨识覆盖率；
- 最小候选间距；
- 对余数误差的敏感度；
- 总采样预算；
- 工程可配置性。

---

## 3. Experiment E0: Simulator verification

### Purpose

验证信号模型、混叠公式和空间相位实现正确。

### Tests

1. 单源无噪声下，混叠频率与理论值一致；
2. 阵元相位差与真实载频一致，而非与混叠频率一致；
3. \(d=c/(2F_{\max})\) 时，研究频段内无传统空间栅瓣；
4. 不同采样率下空间相位一致；
5. 固定随机种子可重复。

### Pass criterion

数值误差在预设容差内，全部单元测试通过。

---

## 4. Experiment E1: Noiseless identifiability map

### Purpose

确定联合映射是否在目标参数域内唯一。

### Independent variables

- 真实频率；
- AOA；
- 单、双、三采样率组合；
- 阵元间距；
- 角度视场。

### Outputs

1. 等价解数量热图；
2. 仅时间信息的候选数量；
3. 时间–空间联合候选数量；
4. 不同采样率组合的唯一可辨识覆盖率；
5. 最小候选距离。

### Success criterion

找到至少一类现实采样率组合，使：

- 单采样率存在大量歧义；
- 多采样率与空间信息联合后目标区域基本可辨识；
- 仍存在值得研究的噪声敏感或多源困难。

### Failure criterion

若大部分目标区域理论上不可辨识，则当前模型不可继续。  
若两个采样率已在全域稳定唯一且传统方法无明显困难，则 AI 联合消歧的研究必要性不足。

---

## 5. Experiment E2: Sampling-rate set search

### Purpose

在总采样预算下选择合理的采样率集合。

### Candidate metrics

\[
\text{Coverage}
=
\frac{\#\{\text{uniquely identifiable grid points}\}}
{\#\{\text{all grid points}\}}.
\]

\[
\text{RobustMargin}
=
\min_{i\neq j}
d(\mathbf z_i,\mathbf z_j),
\]

其中 \(\mathbf z_i\) 为参数点对应的联合观测特征。

### Constraints

- \(R=2,3,4\)；
- 每个采样率低于完整 1 GHz 观测带宽的 Nyquist 要求；
- 总采样率或总样本数受限；
- 避免采样率之间产生过小公因数导致鲁棒性差。

### Deliverable

给出 3–5 个后续实验使用的采样率组合，而不是只选择一个组合。

---

## 6. Experiment E3: Single-source noisy performance

### Baselines

1. Oracle frequency + phase/MUSIC；
2. Single-rate naive estimator；
3. Multi-rate hard intersection / robust CRT + MUSIC；
4. Joint spatio-temporal candidate search；
5. Full-rate or true-frequency reference where applicable。

### Independent variables

- SNR；
- snapshots；
- sampling-rate count；
- frequency；
- AOA。

### Metrics

- alias-order recovery accuracy；
- frequency MAE / RMSE；
- catastrophic frequency error rate；
- AOA MAE / RMSE；
- \(P(|e_\theta|\leq2^\circ)\)；
- \(P(|e_\theta|\leq5^\circ)\)；
- runtime；
- total sample count。

### Diagnostic requirement

每个错误必须区分：

- alias-frequency estimation error；
- wrong alias-order selection；
- frequency–AOA ambiguity；
- AOA estimator error。

---

## 7. Experiment E4: Multi-source pairing and collision

### Purpose

验证多源条件是否产生传统方法难以处理的跨采样率配对问题。

### Scenarios

1. 两源在一个采样率下混叠到相近频率；
2. 不同采样率下峰值顺序改变；
3. 两源角度接近；
4. 两源功率不平衡；
5. 一个源被另一个源的旁瓣或噪声峰遮盖；
6. 源数未知。

### Metrics

- source-count F1；
- correct cross-rate pairing rate；
- joint \((f,\theta)\) matching accuracy；
- Hungarian-matched frequency and AOA error；
- missed-source and false-source rates。

### AI gate

只有 E4 表明传统硬匹配存在稳定且可复现的失败模式，才启动 AI 候选配对模块。

---

## 8. Experiment E5: Model mismatch

在 Stage 0 完成后逐项加入：

- 增益误差；
- 通道相位误差；
- 采样时钟偏差；
- 阵元位置误差；
- 有限带宽信号；
- 多径；
- 非高斯干扰。

每次只加入一种失配，避免无法归因。

---

## 9. Experiment E6: Conditional AI evaluation

若进入 AI 阶段，必须比较：

- 传统 sequential baseline；
- 传统 joint-search baseline；
- 黑盒端到端网络；
- 模型驱动 AI；
- 去除物理一致性损失；
- 去除空间特征；
- 去除多采样率特征；
- 去除不确定性模块。

AI 成功标准不是平均误差略有下降，而是：

- 显著降低错误混叠阶数导致的灾难性误差；
- 改善多源配对；
- 在更低样本预算下达到相同可靠度；
- 在未见频率、角度和 SNR 条件下保持物理一致性。

---

## 10. Real-data and system plan

真实验证分为两种可接受层级：

### Level A: High-rate capture with software emulation

使用真实多通道高率数据，离线构造多采样率观测。  
可验证算法对真实噪声、多径和通道误差的鲁棒性，但不能声称降低了实际 ADC 采样率。

### Level B: Off-the-shelf multi-rate receiver

使用现成平台直接获得真实低采样率混叠数据。  
可以支持更强的系统结论，但必须确认：

- 实际 ADC 和前端是否允许所需混叠；
- 是否存在抗混叠滤波；
- 多阵元是否同步；
- 切换采样率时场景是否稳定；
- 前端在 0.3–1.3 GHz 内是否可校准。

不设计硬件不等于可以忽略接收机链路。

---

## 11. Go / no-go decision after Stage 0

### Continue

同时满足：

1. 问题在目标参数域基本可辨识；
2. 传统方法存在清晰失败边界；
3. Oracle 结果表明失败不是信息完全缺失；
4. 多源配对或低 SNR 鲁棒性具有可学习结构；
5. 存在可行的真实数据验证路径。

### Stop or redefine

出现以下任一情况：

1. 大范围参数域不可辨识；
2. 传统方法已稳定解决目标场景；
3. AI 只能依赖训练集频率和角度分布记忆；
4. 无法获得任何可信真实多通道数据；
5. 所谓低采样仅是 SDR 内部数字抽取，但论文仍声称 RF 欠采样；
6. 研究贡献退化为替换网络结构。
