# Method Design

## 1. Design principle

方法设计按以下顺序推进：

1. 物理模型；
2. 可辨识性；
3. 传统可解释基线；
4. 失败模式诊断；
5. 模型驱动 AI；
6. 不确定性与自适应采样；
7. 系统集成。

不得先确定 CNN、Transformer、Mamba 或 GNN，再反向寻找问题。

---

## 2. Stage 0: Traditional baseline pipeline

### 2.1 Per-rate alias-frequency estimation

对每个采样率 \(f_{s,r}\) 独立估计混叠频率：

\[
\hat{\tilde f}_{k,r}.
\]

首版可采用：

- periodogram / FFT peak；
- zero-padded FFT；
- ESPRIT 或 matrix pencil；
- 后续加入低 SNR 鲁棒估计器。

输出必须包含峰值、峰宽和估计置信度，而不仅是点估计。

---

### 2.2 Candidate generation

根据研究频段和采样率生成真实频率候选：

\[
\mathcal C_{k,r}
=
\{\hat{\tilde f}_{k,r}+qf_{s,r}\}.
\]

实现两类候选融合：

1. 硬交集或鲁棒 CRT；
2. 基于余数误差的软代价函数。

---

### 2.3 Oracle-frequency AoA baseline

使用真实载频构建导向矢量，运行：

- phase-difference estimator；
- MUSIC；
- ESPRIT。

该结果是 AOA 模块的性能上界，用于区分：

- 频率消歧失败；
- AOA 估计本身失败。

---

### 2.4 Sequential baseline

传统顺序链路：

\[
\text{alias-frequency estimation}
\rightarrow
\text{multi-rate frequency recovery}
\rightarrow
\text{MUSIC/ESPRIT AoA}.
\]

该基线必须完整实现，作为后续所有 AI 方法的直接对照。

---

### 2.5 Joint spatio-temporal candidate search

定义联合代价：

\[
J(f,\theta)
=
\sum_{r=1}^{R}
w_{f,r}
D_f
\left(
\operatorname{wrap}_{f_{s,r}}(f),
\hat{\tilde f}_r
\right)^2
+
\lambda
\sum_{m=1}^{M}
w_{\phi,m}
D_\phi
\left(
-\frac{2\pi fp_m\sin\theta}{c},
\hat\phi_m
\right)^2.
\]

在候选频率和连续或离散角度域中搜索

\[
(\hat f,\hat\theta)
=
\arg\min J(f,\theta).
\]

该方法用于回答：传统联合搜索是否已经足够。

---

## 3. Conditional AI design

只有在以下条件同时成立时才进入 AI 阶段：

1. 联合映射在目标区域可辨识；
2. Oracle-frequency AOA 性能良好；
3. 传统方法在低 SNR、多源配对或有限快拍下系统性失败；
4. 失败不能通过简单鲁棒估计或更合理代价函数解决。

### 3.1 AI input

优先使用物理候选和统计特征，而非直接将原始 IQ 作为图片：

- 各采样率混叠频率候选；
- 频率峰值、峰宽和峰置信度；
- 空间协方差实部和虚部；
- 阵元对相位差；
- SNR 估计；
- 采样率标识；
- 候选的余数一致性和空间一致性残差；
- 观测掩码和快拍数。

---

### 3.2 AI tasks

候选 AI 模块只处理传统方法的困难部分：

1. 多采样率多源峰配对；
2. 候选频率–角度联合评分；
3. 错误候选剔除；
4. 连续参数精修；
5. 不确定性估计；
6. 是否需要追加采样的判断。

---

### 3.3 Physics-consistency losses

候选损失包括：

\[
\mathcal L
=
\mathcal L_f
+
\lambda_\theta \mathcal L_\theta
+
\lambda_a \mathcal L_{\text{alias}}
+
\lambda_s \mathcal L_{\text{space}}
+
\lambda_u \mathcal L_{\text{uncertainty}}.
\]

时间混叠一致性：

\[
\mathcal L_{\text{alias}}
=
\sum_r
D_f
\left(
\operatorname{wrap}_{f_{s,r}}(\hat f),
\hat{\tilde f}_r
\right)^2.
\]

空间一致性：

\[
\mathcal L_{\text{space}}
=
\sum_m
D_\phi
\left(
-\frac{2\pi\hat f p_m\sin\hat\theta}{c},
\hat\phi_m
\right)^2.
\]

不得仅使用频率和角度监督误差。

---

## 4. Future active-sampling module

若当前候选后验熵较高，系统从允许的采样率集合 \(\mathcal F_s\) 中选择下一采样率：

\[
f_s^*
=
\arg\max_{f_s\in\mathcal F_s}
\frac{
\mathbb E[\Delta H(\mathcal S)]
}{
C(f_s)
}.
\]

成本可定义为：

\[
C
=
\sum_r f_{s,r}T_r
\]

或总复样本数

\[
C
=
M\sum_rN_r.
\]

该模块属于后续系统扩展，不是 Stage 0 的实现任务。

---

## 5. System boundary

最终软件系统可以包含：

1. 多采样率数据读取和时间窗管理；
2. 每率混叠频率与空间统计提取；
3. 传统或 AI 联合推断；
4. 置信度输出；
5. 采样动作建议；
6. 方向频谱结果可视化。

系统不包含自定义 RF 前端或 ADC 设计。
