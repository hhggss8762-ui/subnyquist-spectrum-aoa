# Decisions

## Decision log

### D-001: Keep AoA as a core output

**Status:** Confirmed  
**Decision:** 不舍弃 AOA。最终任务是频率–AOA 联合方向频谱感知，而不是单独频谱重构。  
**Reason:** AOA 能够利用真实载频相关的空间相位，并形成方向性干扰感知等系统能力。

---

### D-002: Use the 0.3–1.3 GHz observation range

**Status:** Confirmed  
**Decision:** 初始研究频率范围固定为 0.3–1.3 GHz。  
**Reason:** 该范围具有明显的宽频段观测需求，能够形成多个混叠候选。  
**Constraint:** 该选择要求后续严格检查阵列间距、天线带宽、前端滤波和系统校准可行性。

---

### D-003: Model multiple narrowband sources in a wide observation band

**Status:** Confirmed  
**Decision:** 第一阶段研究宽观测带内多个窄带源，不研究单个 1 GHz 带宽源。  
**Reason:** 避免同时引入宽带阵列 beam squint 和复杂传播时延模型。

---

### D-004: Multi-rate temporal observations plus spatial phase

**Status:** Confirmed  
**Decision:** 以多个低采样率产生的混叠频率余数，与阵列空间相位联合恢复真实载频和 AOA。  
**Note:** 多采样率消歧本身不视为创新，必须与已有工作比较。

---

### D-005: No custom hardware design

**Status:** Confirmed  
**Decision:** 不设计 ADC、模拟混频器、天线、PCB 或新阵列结构。  
**Implication:** 最终系统需依赖现成平台或真实高率数据的软件多采样率仿真。

---

### D-006: AI is conditional, not the starting point

**Status:** Confirmed  
**Decision:** Stage 0 不设计神经网络。先证明可辨识性和传统方法失败模式。  
**AI entry condition:** 理论可辨识但传统方法在低 SNR、有限快拍或多源配对下系统性失败。

---

### D-007: Primary target is CCF-B or above

**Status:** Confirmed  
**Decision:** 课题按系统论文组织，而非单一算法精度论文。  
**Required evidence:** 理论或边界、传统基线、AI 必要性、真实数据、采样成本、运行效率和系统能力。

---

### D-008: First baseline is not a single deep-learning paper

**Status:** Confirmed  
**Decision:** 首先实现传统完整链路：每率频率估计、多采样率消歧、联合时空搜索、MUSIC/ESPRIT。  
**Reason:** 必须先确认 AI 是否必要。2024 低 SNR AI-AOA 工作可作为后续模型和实验组织参考，不作为唯一技术骨架。

---

## Open decisions

### O-001: Exact sampling-rate set

需要通过可辨识性覆盖率、鲁棒间隔和总采样成本搜索确定。

### O-002: Parallel or sequential multi-rate acquisition

需要结合设备能力和场景静止假设决定。

### O-003: Real-data platform

需要确认实验室是否有多通道相干 SDR，以及其前端是否允许真实欠采样。

### O-004: Main AI contribution

候选包括：

- 多源跨采样率配对；
- 软候选联合评分；
- 低 SNR 参数精修；
- 不确定性和自适应采样。

必须由 Stage 0 实验选择，不提前锁定。

### O-005: Final network application

候选包括方向性干扰监测、发射源方向追踪和宽带方向频谱图。第一阶段暂不固定复杂网络控制闭环。
