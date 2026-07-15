# Problem Definition

## 1. Scenario

考虑频率范围

\[
f \in [F_{\min},F_{\max}]
=
[0.3,1.3]\ \text{GHz}
\]

内的 \(K\) 个远场窄带信号，由 \(M\) 阵元接收。阵列为已知位置的一维均匀线阵（ULA）。系统采用 \(R\) 个低采样率进行并行或分时观测。

第一阶段采用单音或极窄带信号，以隔离时间混叠、空间相位和多源配对问题。

---

## 2. Variables and units

| Symbol | Meaning | Dimension / unit |
|---|---|---|
| \(F_{\min},F_{\max}\) | 研究频率范围 | Hz |
| \(K\) | 信号源数量 | scalar |
| \(M\) | 阵元数量 | scalar |
| \(R\) | 采样率数量 | scalar |
| \(N_r\) | 第 \(r\) 个采样率下的快拍数 | scalar |
| \(p_m\) | 第 \(m\) 个阵元位置 | m |
| \(d\) | ULA 阵元间距 | m |
| \(f_k\) | 第 \(k\) 个源的真实载频 | Hz |
| \(\theta_k\) | 第 \(k\) 个源的 AOA | degree or rad |
| \(f_{s,r}\) | 第 \(r\) 个采样率 | samples/s |
| \(\tilde f_{k,r}\) | 第 \(r\) 个采样率下的混叠频率 | Hz |
| \(q_{k,r}\) | 混叠阶数 | integer |
| \(\alpha_{k,r}\) | 复幅度 | complex scalar |
| \(c\) | 传播速度 | m/s |
| \(w_{m,r}[n]\) | 噪声 | complex sample |

---

## 3. Observation model

第 \(r\) 个采样率下，第 \(m\) 个阵元的复观测为

\[
y_{m,r}[n]
=
\sum_{k=1}^{K}
\alpha_{k,r}
e^{j2\pi \tilde f_{k,r}n/f_{s,r}}
e^{-j2\pi f_k p_m\sin\theta_k/c}
+
w_{m,r}[n].
\]

混叠频率定义为

\[
\tilde f_{k,r}
=
\operatorname{wrap}_{[-f_{s,r}/2,f_{s,r}/2)}
(f_k)
=
f_k-q_{k,r}f_{s,r}.
\]

关键区别：

- 时间维观测到的是 \(\tilde f_{k,r}\)；
- 阵元间空间相位由真实载频 \(f_k\) 决定；
- 不同采样率之间允许存在未知公共初相位，因此首阶段不依赖跨采样率绝对相位；
- 每个采样率内部，各阵元必须保持相干同步。

---

## 4. Known quantities

初始模型中假设以下量已知：

- 频率搜索范围 \([F_{\min},F_{\max}]\)；
- 阵元数量和阵元位置；
- 各采样率 \(f_{s,r}\)；
- 每个采样率下的采样时刻；
- 传播速度 \(c\)；
- 最大信号源数量 \(K_{\max}\)；
- 角度视场 \(\Theta=[-60^\circ,60^\circ]\)。

---

## 5. Unknown quantities

需要估计：

\[
\mathcal S
=
\{K,f_k,\theta_k,\alpha_{k,r}\}_{k=1}^{K}.
\]

核心输出为

\[
\hat{\mathcal S}
=
\{(\hat f_k,\hat\theta_k,\hat u_k)\}_{k=1}^{\hat K},
\]

其中 \(\hat u_k\) 为估计不确定性或置信度。

---

## 6. Initial assumptions

Stage 0 使用以下假设：

1. 远场传播；
2. 每个源相对其载频为窄带；
3. 复解析信号；
4. 场景在 \(R\) 个采样率的观测周期内静止；
5. 阵列通道同步且已校准；
6. 首阶段无多径；
7. 首阶段噪声为复高斯白噪声；
8. 阵元间距默认不超过最高频率半波长：

\[
d\leq\frac{c}{2F_{\max}}.
\]

该选择仅用于避免研究频段内的传统空间栅瓣，不保证消除频率–角度耦合歧义。

---

## 7. Candidate sets

第 \(r\) 个采样率产生频率候选集

\[
\mathcal C_r
=
\left\{
\tilde f_{k,r}+qf_{s,r}
:
q\in\mathbb Z,\ 
F_{\min}\leq\tilde f_{k,r}+qf_{s,r}\leq F_{\max}
\right\}.
\]

时间维联合候选为满足所有采样率余数约束的频率集合。

空间相位满足

\[
\phi_m
=
\operatorname{wrap}
\left(
-\frac{2\pi f p_m\sin\theta}{c}
\right).
\]

对于频率候选 \(f^{(i)}\)，其合法角度候选满足

\[
\sin\theta^{(i,\ell)}
=
-\frac{c(\phi+2\pi\ell)}
{2\pi d f^{(i)}}.
\]

---

## 8. Identifiability question

定义观测映射

\[
\mathcal G:
(f,\theta)
\mapsto
\left\{
\tilde f_r,\mathbf a(f,\theta)
\right\}_{r=1}^{R}.
\]

核心理论问题是：在给定参数域、采样率集合和阵列几何下，\(\mathcal G\) 是否为单射。

### Identifiable

若任意两个不同参数对

\[
(f,\theta)\neq(f',\theta')
\]

均产生不同的联合时空观测，则参数可辨识。

### Non-identifiable

若存在不同参数对产生相同混叠频率集合和相同空间相位，则任何算法和 AI 模型都不能唯一恢复真实参数。

---

## 9. Research hypothesis

### H1: Joint information hypothesis

在单采样率不可辨识的区域，多采样率余数与空间相位联合使用能够显著减少等价候选。

### H2: Robustness hypothesis

在低 SNR、少快拍和频率峰估计误差下，传统 CRT、硬候选交集和顺序式“频率恢复后再估计 AOA”存在灾难性错误。

### H3: AI necessity hypothesis

若联合映射理论上可辨识，但传统硬判决在多源配对、低 SNR 或有限观测下不稳定，则模型驱动 AI 可以通过软候选评分和联合后验推断提高成功率。

### H4: Sampling-efficiency hypothesis

通过自适应选择采样率或停止采样，系统能够在目标可靠度下减少总样本数或观测时长。

以上均为待验证假设，不是已确认结论。

---

## 10. Primary research task

当前唯一主任务：

> 建立并验证 0.3–1.3 GHz 参数域内，多采样率时间混叠与阵列空间相位的联合可辨识性和传统方法性能边界。

AI 方法仅在该任务确认存在可解决缺口后启动。
