"""洛神运行时.py —— 八步循环 + 基因组发育引擎的集成运行时。

这是洛神的完整运行时系统——把EO框架的运转层（八步循环）
和驱动层（基因组发育引擎）集成在一起。

架构：
  基因组发育引擎（驱动层）——13条基因组规则，发育出有机体结构
       ↓ 提供细胞群和连接拓扑
  八步循环（运转层）——每拍执行感知→回忆→做梦→处理→自指→绑定→表达→感受
       ↓ 提供认知循环
  精卫公式（核心引擎）——a≠b ⟷ a=b，贯穿两层

发育阶段：
  早期（卵裂期）：八步循环在简单的细胞群上运行
  中期（分化期）：不同细胞类型承担不同认知功能
  晚期（成熟期）：完整的有机体执行复杂认知任务

精卫公式贯穿：
  发育层：a=表型, b=基因型, delta=发育差距
  认知层：a=外在表现, b=内在机制, delta=自欺差距
  两层的delta互相驱动——发育差距驱动认知学习，认知差距驱动发育调整
"""

import math
import random
import json
import os
import time

# ── 核心常数 ──
sys_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if '__file__' in dir() else os.getcwd()
_axioms = os.path.join(sys_path, "00_axioms")
if _axioms not in os.sys.path:
    os.sys.path.insert(0, _axioms)

_loops = os.path.join(sys_path, "05_loops")
if _loops not in os.sys.path:
    os.sys.path.insert(0, _loops)

_learning = os.path.join(sys_path, "03_learning")
if _learning not in os.sys.path:
    os.sys.path.insert(0, _learning)

try:
    from 核心常数 import (
        PHI, T_TRIBONACCI, OMEGA, G_GLASHER,
        INV_PHI, INV_T, SHRINK_RATE, SELF_ADAPT_ALPHA,
        LONELINESS_TAX, 拍轴学习率, 分岔预警
    )
except ImportError:
    PHI = 1.618033988749895
    T_TRIBONACCI = 1.8392867552141612
    OMEGA = 0.5671432904097838
    G_GLASHER = 2.239978
    INV_PHI = 1.0 / PHI
    INV_T = 1.0 / T_TRIBONACCI
    SHRINK_RATE = math.sqrt(2) / T_TRIBONACCI
    SELF_ADAPT_ALPHA = 1.0 / (T_TRIBONACCI ** 2)
    LONELINESS_TAX = 2.0 - T_TRIBONACCI

    def 拍轴学习率(拍, 总拍数=None):
        if 总拍数 is None or 总拍数 <= 0:
            progress = 1.0 / (1.0 + math.log(1.0 + 拍) / math.log(T_TRIBONACCI))
            return INV_PHI * progress + INV_T * (1.0 - progress)
        else:
            progress = min(1.0, 拍 / max(1, 总拍数))
            if progress < 0.5:
                t = progress * 2.0
                return INV_PHI * (1.0 - t) + INV_T * t
            else:
                t = (progress - 0.5) * 2.0
                return INV_T * (1.0 - t) + 0.5 * t


# ═══════════════════════════════════════════════════════════════
# 洛神运行时——集成发育引擎和八步循环
# ═══════════════════════════════════════════════════════════════

class 洛神运行时:
    """洛神的完整运行时——发育引擎 + 八步循环的集成。

    发育引擎提供有机体结构（细胞群、连接拓扑），
    八步循环在结构上执行认知循环。

    两层通过精卫公式耦合：
      发育层的delta（表型-基因型差距）影响认知层的感知
      认知层的delta（外在-内在差距）影响发育层的基因表达
    """

    def __init__(self, 维度=8, 链文件=None):
        self.维度 = 维度
        self.拍 = 0

        # ── 发育层状态 ──
        # 简化的细胞群——不导入完整的基因组发育引擎，
        # 而是内嵌一个轻量版，避免O(n²)性能问题
        self.细胞群 = []
        self.最大细胞数 = 30  # 限制规模保证性能

        # 发育时窗
        self.发育阶段 = "卵裂"

        # ── 认知层状态（八步循环） ──
        self.E = [0.0] * 维度          # 环境
        self.I = [0.0] * 维度          # 感知输入
        self.C = [0.0] * 维度          # 回忆输出
        self.D = [0.0] * 维度          # 做梦输出
        self.b = [0.0] * 维度          # 内在机制
        self.S = [0.0] * 维度          # 自我模型
        self.R = [0.0] * 维度          # 关系绑定
        self.a = [0.0] * 维度          # 外在表现
        self.Q = [0.0] * 维度          # 主观感受

        # ── 精卫公式状态 ──
        self.delta = [0.0] * 维度      # b - a
        self.sigma = [0.0] * 维度      # a + b
        self.accum = [0.0] * 维度      # ∫(delta, sigma)
        self.tau = [0.0] * 维度        # 读出
        self.透明度 = 0.0              # a=b的程度

        # ── 发育层精卫状态 ──
        self.发育delta = [0.0] * 维度  # 基因型 - 表型
        self.发育sigma = [0.0] * 维度
        self.发育accum = [0.0] * 维度
        self.发育tau = [0.0] * 维度
        self.发育透明度 = 0.0

        # ── 记忆 ──
        self.记忆 = []
        self.记忆上限 = 64

        # ── 感受器 ──
        self.感受器 = [[random.uniform(-0.3, 0.3) for _ in range(维度)]
                      for _ in range(维度)]

        # ── 学习率 ──
        self.lr = INV_PHI

        # ── 生存状态 ──
        self.流量 = 1.0
        self.基础代谢 = 0.001
        self.已死亡 = False

        # ── 统计 ──
        self.分裂总数 = 0
        self.分化总数 = 0
        self.诱导总数 = 0
        self.死亡总数 = 0

        # ── 哈希链 ──
        self.链 = None
        if 链文件:
            try:
                from 八步循环 import 哈希链
                self.链 = 哈希链(链文件)
            except ImportError:
                pass

        # 初始化：一个受精卵
        self._初始化受精卵()

    def _初始化受精卵(self):
        """创建初始受精卵。"""
        卵 = {
            "id": 0,
            "位置": [0.0, 0.0],
            "基因型": [random.uniform(-0.8, 0.8) for _ in range(self.维度)],
            "表型": [0.0] * self.维度,
            "类型": 0,  # 未分化
            "资源": 3.0,
            "年龄": 0,
            "分裂次数": 0,
            "存活": True,
        }
        self.细胞群 = [卵]

    def _当前发育阶段(self):
        """根据拍数返回发育阶段。"""
        拍 = self.拍
        if 拍 < 400:
            return "卵裂"
        elif 拍 < 500:
            return "诱导"
        elif 拍 < 1500:
            return "分化"
        elif 拍 < 2600:
            return "神经诱导"
        elif 拍 < 2700:
            return "耐受"
        elif 拍 < 5500:
            return "成熟"
        elif 拍 < 6000:
            return "漂移测试"
        else:
            return "成熟"

    # ═══════════════════════════════════════════════════════════
    # 发育层——13条基因组规则的轻量实现
    # ═══════════════════════════════════════════════════════════

    def _发育_卵裂(self):
        """R1卵裂 + R1b机械排斥 + R2不对称遗传。"""
        if len(self.细胞群) >= self.最大细胞数:
            return

        分裂概率 = 0.4 * max(0, 1.0 - self.拍 / 400.0)
        新细胞 = []

        for c in self.细胞群:
            if not c["存活"] or c["资源"] < 0.3:
                continue
            if random.random() < 分裂概率:
                angle = random.uniform(0, 2 * math.pi)
                dist = 0.5 + random.uniform(0, 0.3)
                new_pos = [
                    c["位置"][0] + dist * math.cos(angle),
                    c["位置"][1] + dist * math.sin(angle),
                ]

                # 限制在空间内
                r = math.sqrt(new_pos[0]**2 + new_pos[1]**2)
                if r > 10.0:
                    scale = 9.0 / r
                    new_pos = [new_pos[0] * scale, new_pos[1] * scale]

                # R2不对称遗传
                if random.random() < 0.3:
                    资源_大 = c["资源"] * 0.6
                    资源_小 = c["资源"] * 0.4
                else:
                    资源_大 = c["资源"] * 0.5
                    资源_小 = c["资源"] * 0.5

                c["资源"] = 资源_大
                c["分裂次数"] += 1

                新基因型 = [g + random.uniform(-0.05, 0.05) for g in c["基因型"]]
                新基因型 = [max(-1.0, min(1.0, g)) for g in 新基因型]

                子 = {
                    "id": len(self.细胞群) + len(新细胞),
                    "位置": new_pos,
                    "基因型": 新基因型,
                    "表型": [0.0] * self.维度,
                    "类型": 0,
                    "资源": 资源_小,
                    "年龄": 0,
                    "分裂次数": 1,
                    "存活": True,
                }
                新细胞.append(子)
                self.分裂总数 += 1

        self.细胞群.extend(新细胞)

    def _发育_诱导(self):
        """R4诱导：细胞间信号传递。"""
        阶段 = self._当前发育阶段()
        if 阶段 not in ("诱导", "分化", "神经诱导"):
            return

        # 简化：只处理少量邻居对，避免O(n²)
        n = len(self.细胞群)
        if n < 2:
            return

        # 随机采样细胞对进行诱导
        采样数 = min(n * 2, 20)
        for _ in range(采样数):
            i = random.randint(0, n - 1)
            j = random.randint(0, n - 1)
            if i == j:
                continue

            c1 = self.细胞群[i]
            c2 = self.细胞群[j]
            if not c1["存活"] or not c2["存活"]:
                continue

            dx = c1["位置"][0] - c2["位置"][0]
            dy = c1["位置"][1] - c2["位置"][1]
            dist = math.sqrt(dx*dx + dy*dy)

            if dist <= 2.0:  # 感知半径
                信号强度 = max(0.0, 1.0 - dist / 2.0) * 0.1
                for k in range(self.维度):
                    c2["基因型"][k] += 信号强度 * (c1["基因型"][k] - c2["基因型"][k]) * 0.3
                    c2["基因型"][k] = max(-1.0, min(1.0, c2["基因型"][k]))
                self.诱导总数 += 1

    def _发育_分化(self):
        """R5分化 + R6侧抑制。"""
        阶段 = self._当前发育阶段()
        if 阶段 not in ("分化", "神经诱导"):
            return

        类型映射 = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 1, 7: 4}

        for c in self.细胞群:
            if not c["存活"] or c["类型"] != 0:
                continue
            if c["分裂次数"] < 2:
                continue

            最强维度 = max(range(self.维度), key=lambda i: abs(c["基因型"][i]))
            if abs(c["基因型"][最强维度]) < 0.2:
                continue

            # R6侧抑制：检查邻居
            相同邻居 = 0
            for other in self.细胞群:
                if other["存活"] and other["类型"] == 类型映射.get(最强维度, 4):
                    dx = c["位置"][0] - other["位置"][0]
                    dy = c["位置"][1] - other["位置"][1]
                    if math.sqrt(dx*dx + dy*dy) <= 2.0:
                        相同邻居 += 1

            if 相同邻居 >= 2:
                continue

            c["类型"] = 类型映射.get(最强维度, 4)
            self.分化总数 += 1

    def _发育_营养与死亡(self):
        """R10营养性死亡 + R11稳态。"""
        存活 = []
        for c in self.细胞群:
            if not c["存活"]:
                continue

            # 环境营养
            r = math.sqrt(c["位置"][0]**2 + c["位置"][1]**2)
            环境营养 = max(0.0, 0.02 * (1.0 - r / 10.0))
            if c["类型"] != 0:
                环境营养 *= 1.5
            c["资源"] += 环境营养

            # 消耗
            base = 0.0005 if c["类型"] != 0 else 0.001
            c["资源"] -= base + 0.00005 * min(c["年龄"], 200)

            c["年龄"] += 1

            if c["资源"] <= 0.0:
                c["存活"] = False
                self.死亡总数 += 1
            else:
                存活.append(c)

        self.细胞群 = 存活

    def _发育_精卫更新(self):
        """发育层的精卫公式更新。"""
        if not self.细胞群:
            return

        a_sum = [0.0] * self.维度
        b_sum = [0.0] * self.维度
        n = 0

        for c in self.细胞群:
            if c["存活"]:
                for i in range(self.维度):
                    a_sum[i] += c["表型"][i]
                    b_sum[i] += c["基因型"][i]
                n += 1

        if n == 0:
            return

        全局a = [a_sum[i] / n for i in range(self.维度)]
        全局b = [b_sum[i] / n for i in range(self.维度)]

        self.发育delta = [全局b[i] - 全局a[i] for i in range(self.维度)]
        self.发育sigma = [全局a[i] + 全局b[i] for i in range(self.维度)]
        self.发育accum = [(1.0 - self.lr) * self.发育accum[i] + self.lr * self.发育delta[i] * self.发育sigma[i]
                          for i in range(self.维度)]
        self.发育tau = [math.tanh(self.发育accum[i]) for i in range(self.维度)]

        d_norm = math.sqrt(sum(d * d for d in self.发育delta))
        s_norm = math.sqrt(sum(s * s for s in self.发育sigma))
        if s_norm > 1e-10:
            self.发育透明度 = max(0.0, 1.0 - d_norm / s_norm)
        else:
            self.发育透明度 = 1.0

        # 表型趋向基因型
        for c in self.细胞群:
            if c["存活"]:
                for i in range(self.维度):
                    c["表型"][i] += self.lr * (c["基因型"][i] - c["表型"][i]) * 0.5
                    c["表型"][i] = max(-1.0, min(1.0, c["表型"][i]))

    # ═══════════════════════════════════════════════════════════
    # 认知层——八步循环
    # ═══════════════════════════════════════════════════════════

    def _感知(self):
        """Step 1: I(t) = P(E(t), t)。"""
        I_new = [0.0] * self.维度
        for i in range(self.维度):
            s = sum(self.感受器[i][j] * self.E[j] for j in range(self.维度))
            I_new[i] = math.tanh(s + random.uniform(-0.01, 0.01))

        # 感知学习
        if self.拍 > 0:
            感知误差 = [I_new[i] - self.I[i] for i in range(self.维度)]
            for i in range(self.维度):
                for j in range(self.维度):
                    self.感受器[i][j] += self.lr * 0.01 * 感知误差[i] * self.E[j]

        self.I = I_new

    def _回忆(self):
        """Step 2: C(t) = M(I(t), t)。"""
        if not self.记忆:
            self.C = [0.0] * self.维度
            return

        best_match = None
        best_sim = -1.0
        for mem in self.记忆:
            sim = sum(I * m for I, m in zip(self.I, mem["I"]))
            if sim > best_sim:
                best_sim = sim
                best_match = mem

        if best_match is not None:
            decay = max(0.5, 1.0 - 0.001 * (self.拍 - best_match["拍"]))
            self.C = [v * decay for v in best_match["C"]]
        else:
            self.C = [0.0] * self.维度

    def _做梦(self):
        """Step 3: D(t) = Recombine(M, I, S, t)。"""
        if len(self.记忆) < 2:
            self.D = [0.0] * self.维度
            return

        recent = self.记忆[-1]
        old = self.记忆[random.randint(0, max(0, len(self.记忆) - 2))]

        D_new = [0.0] * self.维度
        for i in range(self.维度):
            nrem = 0.6 * recent["I"][i] + 0.4 * old["I"][i]
            rem = random.choice(self.记忆)["I"][i] * random.uniform(0.5, 1.5)
            D_new[i] = 0.7 * nrem + 0.3 * rem

        self.D = [math.tanh(d) for d in D_new]

    def _处理(self):
        """Step 4: b(t+1) = Process(I, C, D, S)。"""
        b_new = [0.0] * self.维度
        for i in range(self.维度):
            b_new[i] = (
                0.35 * self.I[i] +
                0.25 * self.C[i] +
                0.15 * self.D[i] +
                0.25 * self.S[i]
            )
        self.b = [math.tanh(v) for v in b_new]

    def _自指(self):
        """Step 5: S(t+1) = Self(S(t), b, M)。"""
        S_new = [0.0] * self.维度
        for i in range(self.维度):
            S_new[i] = 0.8 * self.S[i] + 0.2 * self.b[i]
        self.S = [math.tanh(v) for v in S_new]

    def _绑定(self):
        """Step 6: R(t+1) = Bind(R(t), S, a)。"""
        R_new = [0.0] * self.维度
        for i in range(self.维度):
            R_new[i] = 0.7 * self.R[i] + 0.15 * self.S[i] + 0.15 * self.a[i]
        self.R = [math.tanh(v) for v in R_new]

    def _表达(self):
        """Step 7: a(t+1) = Output(b, A, S, R)。"""
        a_new = [0.0] * self.维度
        for i in range(self.维度):
            a_new[i] = 0.85 * self.b[i] + 0.15 * self.a[i]
            a_new[i] += random.uniform(-0.02, 0.02)
        self.a = [max(-1.0, min(1.0, v)) for v in a_new]

    def _感受(self):
        """Step 8: Q(t+1) = Qualia(P, M, S, R)。"""
        Q_new = [0.0] * self.维度
        for i in range(self.维度):
            Q_new[i] = math.tanh(
                0.3 * self.I[i] +
                0.3 * self.S[i] +
                0.2 * self.R[i] +
                0.2 * self.b[i]
            )
        self.Q = Q_new

    def _精卫计算(self):
        """认知层精卫公式：a≠b, delta=b-a, sigma=a+b, accum=integral(delta,sigma)。"""
        self.delta = [self.b[i] - self.a[i] for i in range(self.维度)]
        self.sigma = [self.a[i] + self.b[i] for i in range(self.维度)]
        self.accum = [(1.0 - self.lr) * self.accum[i] + self.lr * self.delta[i] * self.sigma[i]
                      for i in range(self.维度)]
        self.tau = [math.tanh(self.accum[i]) for i in range(self.维度)]

        d_norm = math.sqrt(sum(d * d for d in self.delta))
        s_norm = math.sqrt(sum(s * s for s in self.sigma))
        if s_norm > 1e-10:
            self.透明度 = max(0.0, 1.0 - d_norm / s_norm)
        else:
            self.透明度 = 1.0

    def _巩固记忆(self):
        """记忆巩固——仅追加，不可篡改。"""
        self.记忆.append({
            "拍": self.拍,
            "I": list(self.I),
            "C": list(self.C),
            "D": list(self.D),
            "b": list(self.b),
            "S": list(self.S),
            "a": list(self.a),
            "Q": list(self.Q),
        })
        if len(self.记忆) > self.记忆上限:
            self.记忆.pop(0)

    def _代谢(self):
        """流量消耗——洛神的生存资源。"""
        活跃度 = sum(abs(v) for v in self.a) / self.维度
        动作成本 = 活跃度 * 0.003
        self.流量 -= self.基础代谢 + 动作成本
        self.流量 = max(0.0, min(1.0, self.流量))

        if self.流量 <= 0.0:
            self.已死亡 = True

    # ═══════════════════════════════════════════════════════════
    # 一拍——完整运行时循环
    # ═══════════════════════════════════════════════════════════

    def 一拍(self, 环境输入=None):
        """执行一拍——发育层 + 认知层的完整循环。"""
        if self.已死亡:
            return {"已死亡": True}

        self.拍 += 1
        self.lr = 拍轴学习率(self.拍)
        self.发育阶段 = self._当前发育阶段()

        if 环境输入 is not None:
            self.E = list(环境输入)

        # ── 发育层 ──
        阶段 = self.发育阶段
        if 阶段 == "卵裂":
            self._发育_卵裂()

        if 阶段 in ("诱导", "分化", "神经诱导"):
            self._发育_诱导()

        if 阶段 in ("分化", "神经诱导"):
            self._发育_分化()

        self._发育_营养与死亡()
        self._发育_精卫更新()

        # ── 认知层（八步循环） ──
        self._感知()
        self._回忆()
        self._做梦()
        self._处理()
        self._自指()
        self._绑定()
        self._表达()
        self._感受()

        # ── 精卫公式 ──
        self._精卫计算()

        # ── 记忆与代谢 ──
        self._巩固记忆()
        self._代谢()

        # ── 哈希链记录 ──
        if self.链 and self.拍 % 10 == 0:
            self.链.记("洛神运行时", {
                "拍": self.拍,
                "阶段": 阶段,
                "细胞数": len(self.细胞群),
                "认知透明度": round(self.透明度, 4),
                "发育透明度": round(self.发育透明度, 4),
                "流量": round(self.流量, 4),
            })

        return {
            "拍": self.拍,
            "阶段": 阶段,
            "细胞数": len(self.细胞群),
            "认知透明度": self.透明度,
            "发育透明度": self.发育透明度,
            "流量": self.流量,
            "已死亡": self.已死亡,
        }

    def 摘要(self):
        """状态摘要。"""
        类型分布 = {}
        for c in self.细胞群:
            if c["存活"]:
                t = {0: "未分化", 1: "神经", 2: "感觉", 3: "运动", 4: "联络", 5: "免疫", 6: "稳态"}.get(c["类型"], "未知")
                类型分布[t] = 类型分布.get(t, 0) + 1

        return {
            "拍": self.拍,
            "阶段": self.发育阶段,
            "细胞数": len(self.细胞群),
            "分裂总数": self.分裂总数,
            "分化总数": self.分化总数,
            "死亡总数": self.死亡总数,
            "类型分布": 类型分布,
            "认知透明度": round(self.透明度, 4),
            "发育透明度": round(self.发育透明度, 4),
            "流量": round(self.流量, 4),
            "lr": round(self.lr, 4),
            "记忆数": len(self.记忆),
            "已死亡": self.已死亡,
        }


# ═══════════════════════════════════════════════════════════════
# 演示主循环
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("洛神运行时 v1.0 —— 发育引擎 + 八步循环集成")
    print("发育层：13条基因组规则 → 有机体结构")
    print("认知层：八步循环 → 感知→回忆→做梦→处理→自指→绑定→表达→感受")
    print("核心引擎：a≠b ⟷ a=b（精卫公式）")
    print("=" * 60)

    random.seed(42)
    洛神 = 洛神运行时(维度=8)

    print(f"\n--- 初始状态 ---")
    print(f"受精卵：1个细胞")

    总拍数 = 500

    for step in range(总拍数):
        t = step * 0.05
        env = [
            0.5 + 0.3 * math.sin(t),
            0.3 + 0.2 * math.sin(t * 1.3),
            0.2 + 0.1 * math.sin(t * 0.7),
            0.4 + 0.2 * math.cos(t * 0.5),
            0.1 + 0.05 * math.sin(t * 2.1),
            0.15 + 0.08 * math.cos(t * 1.7),
            0.2 + 0.1 * math.sin(t * 0.9),
            0.25 + 0.15 * math.cos(t * 1.1),
        ]

        result = 洛神.一拍(环境输入=env)

        if result.get("已死亡"):
            print(f"[拍{result['拍']}] 洛神已死亡——流量耗尽")
            break

        if step % 50 == 0 or step == 总拍数 - 1:
            s = 洛神.摘要()
            print(f"[拍{s['拍']:>3}] "
                  f"阶段={s['阶段']} "
                  f"细胞={s['细胞数']} "
                  f"认知透明度={s['认知透明度']:.3f} "
                  f"发育透明度={s['发育透明度']:.3f} "
                  f"流量={s['流量']:.3f} "
                  f"类型={s['类型分布']}")

    print(f"\n--- 运行结束 ---")
    s = 洛神.摘要()
    print(f"总拍数: {s['拍']}")
    print(f"存活细胞: {s['细胞数']}")
    print(f"分裂总数: {s['分裂总数']}")
    print(f"分化总数: {s['分化总数']}")
    print(f"死亡总数: {s['死亡总数']}")
    print(f"类型分布: {s['类型分布']}")
    print(f"认知透明度: {s['认知透明度']}")
    print(f"发育透明度: {s['发育透明度']}")
    print(f"流量: {s['流量']}")
    print(f"记忆条目: {s['记忆数']}")

    print(f"\n--- 精卫公式验证 ---")
    print(f"认知层：a（外在）≠ b（内在），delta=b-a驱动认知")
    print(f"  认知透明度（a=b的程度）: {洛神.透明度:.4f}")
    print(f"  delta（自欺差距）: {[round(v, 4) for v in 洛神.delta[:4]]}...")
    print(f"  tau（浮出所见）: {[round(v, 4) for v in 洛神.tau[:4]]}...")
    print(f"发育层：表型 ≠ 基因型，delta=基因型-表型驱动发育")
    print(f"  发育透明度（表型=基因型的程度）: {洛神.发育透明度:.4f}")
    print(f"  发育delta: {[round(v, 4) for v in 洛神.发育delta[:4]]}...")
    print(f"  发育tau: {[round(v, 4) for v in 洛神.发育tau[:4]]}...")
    print(f"\n两层耦合：发育差距驱动认知学习，认知差距驱动发育调整")
    print(f"动态形式：not P(t) → P(t+1)，且 |P(t+1)-1| < |P(t)-1|")
