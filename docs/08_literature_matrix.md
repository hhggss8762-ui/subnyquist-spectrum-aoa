# Literature Matrix

## Purpose

本文件用于判断拟议贡献是否已被已有工作覆盖。优先记录原始论文、权威会议期刊和公开代码。

---

## Required categories

1. Multi-rate sub-Nyquist frequency estimation;
2. Robust CRT and remainder-error methods;
3. Joint temporal-spatial sub-Nyquist frequency and DOA estimation;
4. Compressed carrier and DOA estimation;
5. AI-based AoA under low SNR;
6. Model-driven deep AoA;
7. Multi-source association and set prediction;
8. Real multi-channel SDR AoA systems.

---

## Comparison table

| Paper | Venue/year | Signal model | Frequency range | Sampling structure | Array | Unknowns | Identifiability result | Multi-source | Low SNR | AI role | Real data/system | Public code | Key limitation | Overlap with our idea |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

---

## Questions for every paper

1. 真实载频是否未知？
2. 是否存在时间混叠？
3. 是否使用多个采样率？
4. 空间相位是否参与频率消歧？
5. 频率和 AOA 是顺序估计还是联合估计？
6. 是否给出唯一性或最大可辨识源数？
7. 多源跨采样率配对如何完成？
8. 是否测试低 SNR、少快拍和错误混叠阶数？
9. 是否使用真实低采样硬件，还是高速采集后离线降采样？
10. AI 是否解决传统方法的结构性缺陷？
11. 我们相较它新增了什么可证伪能力？

---

## Literature gate

在提出方法创新前，至少完成：

- 5 篇多采样率/CRT原始论文；
- 5 篇时空联合频率–DOA论文；
- 3 篇 AI-AOA 论文；
- 3 篇真实无线定位或方向感知系统论文。

若无法写出与最接近工作的逐项差异，则不得进入论文方法设计。
