"""基因组发育引擎.py —— 13条基因组规则的可运行实现。

EO框架定义.md 1.8节——13条基因组规则：
  R1  卵裂        ——初始细胞分裂，复制自身
  R1b 机械排斥    ——细胞间物理排斥，防止重叠
  R2  不对称遗传  ——分裂时不对称分配资源
  R3  局部盲视    ——每个细胞只能看到局部信息
  R4  诱导        ——一个细胞影响另一个细胞的发育方向
  R5  分化        ——细胞特化为不同功能
  R6  侧抑制      ——邻近细胞互相抑制相同分化方向
  R7  神经诱导    ——特定细胞诱导神经组织形成
  R8  信号经济    ——用最少信号传递最多信息
  R9  免疫耐受    ——系统学会不攻击自身
  R10 营养性死亡  ——缺乏营养的细胞主动死亡
  R11 稳态        ——系统维持内部稳定
  R12 整体决策    ——系统层面的统一决策

发育时窗：
  0-400    卵裂（R1, R1b, R2）
  500      诱导（R4）
  500-1500 分化（R5, R6）
  1600-2600 神经诱导（R7）
  2700     耐受（R9）
  5500     漂移测试

精卫公式贯穿发育全过程：
  a≠b（基因型≠表型）→ Δ=b−a → Σ=a+b → ⊗=∫(Δ,Σ) → τ读⊗→浮出所见

核心引擎：a≠b ⟷ a=b
  a=外在表现（表型/行为），b=内在机制（基因型/内部状态）
  发育就是a不断趋向b的过程——但永远追不到（自欺引擎）
"""

import math
import random
import json
import hashlib
import os
import time

# ── 核心常数 ──
try:
    sys_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    sys_path = os.getcwd()
_axioms = os.path.join(sys_path, "00_axioms")
if _axioms not in os.sys.path:
    os.sys.path.insert(0, _axioms)

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
# 发育时窗定义
# ═══════════════════════════════════════════════════════════════

发育时窗 = {
    "卵裂": (0, 400),         # R1, R1b, R2
    "诱导": (400, 500),       # R4
    "分化": (500, 1500),      # R5, R6
    "神经诱导": (1600, 2600), # R7
    "耐受": (2600, 2700),     # R9
    "漂移测试": (5500, 6000), # 稳定性验证
}

def 当前发育阶段(拍):
    """根据拍数返回当前发育阶段。"""
    for 阶段, (起, 止) in 发育时窗.items():
        if 起 <= 拍 < 止:
            return 阶段
    if 拍 >= 6000:
        return "成熟"
    return "等待"


# ═══════════════════════════════════════════════════════════════
# 细胞——洛神的基本单元
# ═══════════════════════════════════════════════════════════════

# 细胞类型
细胞类型 = {
    0: "未分化",
    1: "神经",       # R7神经诱导产生
    2: "感觉",       # 感知外部环境
    3: "运动",       # 产生行为输出
    4: "联络",       # 内部信号传递
    5: "免疫",       # R9免疫耐受
    6: "稳态",       # R11稳态维持
}

class 细胞:
    """单个细胞——洛神发育的基本单元。

    每个细胞有：
    - 基因型（b）：内在的基因表达状态
    - 表型（a）：外在的表现特征
    - 位置：在发育空间中的坐标
    - 资源：营养水平
    - 连接：与其他细胞的信号连接

    精卫公式：a≠b（表型≠基因型），delta=b-a驱动发育
    """

    _next_id = 0

    def __init__(self, 位置=(0.0, 0.0), 基因型=None, 资源=1.0):
        self.id = 细胞._next_id
        细胞._next_id += 1

        self.位置 = list(位置)
        self.基因型 = 基因型 if 基因型 else [0.0] * 8  # 8维基因表达
        self.表型 = [0.0] * 8                            # 8维表型特征
        self.类型 = 0                                     # 未分化
        self.资源 = 资源                                  # 营养水平
        self.年龄 = 0                                     # 细胞年龄
        self.连接 = {}                                    # {邻居id: 信号强度}
        self.信号buffer = []                              # 接收到的信号
        self.存活 = True
        self.分裂次数 = 0

        # 精卫公式状态
        self.delta = [0.0] * 8    # b - a
        self.sigma = [0.0] * 8    # a + b
        self.accum = [0.0] * 8    # ∫(delta, sigma)
        self.tau = [0.0] * 8      # 读出

        # R3局部盲视：感知半径
        self.感知半径 = 2.0

    def 精卫更新(self, lr):
        """更新精卫公式状态：a≠b, delta=b-a, sigma=a+b, accum=integral(delta,sigma)。"""
        self.delta = [self.基因型[i] - self.表型[i] for i in range(8)]
        self.sigma = [self.基因型[i] + self.表型[i] for i in range(8)]
        self.accum = [(1.0 - lr) * self.accum[i] + lr * self.delta[i] * self.sigma[i]
                      for i in range(8)]
        self.tau = [math.tanh(self.accum[i]) for i in range(8)]

        # 表型趋向基因型（a趋向b），但永远不完全相等
        for i in range(8):
            self.表型[i] += lr * self.delta[i] * 0.5
            self.表型[i] = max(-1.0, min(1.0, self.表型[i]))

    def 透明度(self):
        """a=b的程度（0=完全自欺, 1=完全透明）。"""
        d_norm = math.sqrt(sum(d * d for d in self.delta))
        s_norm = math.sqrt(sum(s * s for s in self.sigma))
        if s_norm > 1e-10:
            return max(0.0, 1.0 - d_norm / s_norm)
        return 1.0

    def 摘要(self):
        return {
            "id": self.id,
            "类型": 细胞类型.get(self.类型, "未知"),
            "位置": [round(p, 2) for p in self.位置],
            "资源": round(self.资源, 3),
            "年龄": self.年龄,
            "分裂次数": self.分裂次数,
            "透明度": round(self.透明度(), 3),
            "存活": self.存活,
        }


# ═══════════════════════════════════════════════════════════════
# 基因组发育引擎——13条规则的可运行实现
# ═══════════════════════════════════════════════════════════════

class 基因组发育引擎:
    """13条基因组规则的可运行实现。

    从一个"受精卵"开始，通过13条规则的发育过程，
    最终形成一个有结构、有分化、有神经网络的有机体。

    发育过程遵循精卫公式：a≠b（表型≠基因型）驱动发育，
    delta=b-a是发育的动力，accum是发育的记忆。
    """

    def __init__(self, 维度=8, 链文件=None):
        self.维度 = 维度
        self.拍 = 0
        self.细胞群 = []
        self.已死亡细胞 = []

        # 发育空间大小
        self.空间半径 = 10.0

        # 全局精卫状态
        self.全局a = [0.0] * 维度
        self.全局b = [0.0] * 维度
        self.全局delta = [0.0] * 维度
        self.全局sigma = [0.0] * 维度
        self.全局accum = [0.0] * 维度
        self.全局tau = [0.0] * 维度
        self.全局透明度 = 0.0

        # 发育统计
        self.分裂总数 = 0
        self.分化总数 = 0
        self.死亡总数 = 0
        self.诱导总数 = 0

        # R9免疫耐受：自体标记
        self.自体标记 = set()

        # R12整体决策：系统级信号
        self.系统信号 = [0.0] * 维度

        # 学习率
        self.lr = INV_PHI

        # 哈希链
        self.链 = None
        if 链文件:
            from 八步循环 import 哈希链
            self.链 = 哈希链(链文件)

        # 初始化：一个受精卵——高资源，强基因表达
        卵 = 细胞(位置=(0.0, 0.0), 资源=3.0)
        # 受精卵的基因型——包含发育潜能，初始表达较强
        卵.基因型 = [random.uniform(-0.8, 0.8) for _ in range(维度)]
        self.细胞群 = [卵]
        self.自体标记.add(卵.id)

    # ── R1 卵裂 ──
    def R1_卵裂(self):
        """R1卵裂：细胞分裂，复制自身。

        生物学：受精卵通过连续分裂产生大量细胞。
        早期分裂是同步的——所有细胞同时分裂。

        实现：每个资源充足的细胞按概率分裂，
        分裂次数沿拍轴衰减（早期快、晚期慢）。
        """
        阶段 = 当前发育阶段(self.拍)
        if 阶段 != "卵裂":
            return

        # 卵裂期分裂概率高
        分裂概率 = 0.5 * (1.0 - self.拍 / 400.0)  # 从0.5衰减到0
        新细胞 = []

        # 限制最大细胞数——防止计算量爆炸
        if len(self.细胞群) > 50:
            return

        for c in self.细胞群:
            if not c.存活 or c.资源 < 0.3:
                continue
            if random.random() < 分裂概率:
                # R1b机械排斥：新细胞被推到附近但不重叠的位置
                angle = random.uniform(0, 2 * math.pi)
                dist = 0.5 + random.uniform(0, 0.3)
                new_pos = (
                    c.位置[0] + dist * math.cos(angle),
                    c.位置[1] + dist * math.sin(angle),
                )

                # 限制在空间内
                r = math.sqrt(new_pos[0]**2 + new_pos[1]**2)
                if r > self.空间半径:
                    scale = self.空间半径 / r * 0.9
                    new_pos = (new_pos[0] * scale, new_pos[1] * scale)

                # R2不对称遗传：分裂时资源不均等分配
                # 一个细胞得到更多资源（干细胞特性）
                if random.random() < 0.3:
                    # 不对称分裂：一个得60%，一个得40%
                    资源_大 = c.资源 * 0.6
                    资源_小 = c.资源 * 0.4
                else:
                    # 对称分裂：各得50%
                    资源_大 = c.资源 * 0.5
                    资源_小 = c.资源 * 0.5

                c.资源 = 资源_大
                c.分裂次数 += 1

                # 新细胞的基因型——从父细胞继承，加微量变异
                新基因型 = [g + random.uniform(-0.05, 0.05) for g in c.基因型]
                新基因型 = [max(-1.0, min(1.0, g)) for g in 新基因型]

                子 = 细胞(位置=new_pos, 基因型=新基因型, 资源=资源_小)
                子.分裂次数 = 1
                新细胞.append(子)
                self.自体标记.add(子.id)
                self.分裂总数 += 1

        self.细胞群.extend(新细胞)

    # ── R1b 机械排斥 ──
    def R1b_机械排斥(self):
        """R1b机械排斥：细胞间物理排斥，防止重叠。

        生物学：细胞有物理体积，不能占据同一空间。
        细胞间的机械排斥力维持空间分布。

        实现：对每对邻近细胞施加排斥力，调整位置。
        """
        for i, c1 in enumerate(self.细胞群):
            if not c1.存活:
                continue
            for j, c2 in enumerate(self.细胞群[i+1:], i+1):
                if not c2.存活:
                    continue
                dx = c1.位置[0] - c2.位置[0]
                dy = c1.位置[1] - c2.位置[1]
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < 0.3 and dist > 1e-6:
                    # 排斥力——推开重叠的细胞
                    force = (0.3 - dist) * 0.5
                    c1.位置[0] += force * dx / dist
                    c1.位置[1] += force * dy / dist
                    c2.位置[0] -= force * dx / dist
                    c2.位置[1] -= force * dy / dist

    # ── R2 不对称遗传 ──
    def R2_不对称遗传(self):
        """R2不对称遗传：分裂时不对称分配资源。

        生物学：干细胞分裂时，一个子细胞保持干细胞特性
        （多潜能、自我更新），另一个子细胞开始分化。

        实现：在R1卵裂中已实现不对称资源分配。
        这里进一步处理不对称的基因表达——
        干细胞保留完整基因表达，分化细胞开始沉默部分基因。
        """
        阶段 = 当前发育阶段(self.拍)
        if 阶段 not in ("卵裂", "诱导", "分化"):
            return

        for c in self.细胞群:
            if not c.存活:
                continue
            # 分裂次数多的细胞——更可能开始沉默基因（分化准备）
            if c.分裂次数 > 3 and c.类型 == 0:
                # 随机沉默部分基因表达
                for i in range(self.维度):
                    if random.random() < 0.1:
                        c.基因型[i] *= 0.8  # 逐渐沉默

    # ── R3 局部盲视 ──
    def R3_局部盲视(self, 细胞):
        """R3局部盲视：每个细胞只能看到局部信息。

        生物学：细胞只能感知邻近细胞的信号，
        不能感知远处细胞——这是发育的必要条件。
        局部盲视确保了发育的局部性——每个细胞基于局部信息做决策。

        实现：返回感知半径内的邻居细胞。
        """
        邻居 = []
        for other in self.细胞群:
            if other.id == 细胞.id or not other.存活:
                continue
            dx = 细胞.位置[0] - other.位置[0]
            dy = 细胞.位置[1] - other.位置[1]
            dist = math.sqrt(dx*dx + dy*dy)
            if dist <= 细胞.感知半径:
                邻居.append((other, dist))
        return 邻居

    # ── R4 诱导 ──
    def R4_诱导(self):
        """R4诱导：一个细胞影响另一个细胞的发育方向。

        生物学：诱导组织分泌信号分子，影响周围细胞的发育命运。
        经典例子：脊索诱导上方外胚层形成神经板。

        实现：特定细胞向邻居发送诱导信号，
        接收信号的细胞的基因表达被改变。
        """
        阶段 = 当前发育阶段(self.拍)
        if 阶段 not in ("诱导", "分化", "神经诱导"):
            return

        for c in self.细胞群:
            if not c.存活:
                continue
            邻居 = self.R3_局部盲视(c)

            for other, dist in 邻居:
                # 诱导信号强度随距离衰减
                信号强度 = max(0.0, 1.0 - dist / c.感知半径) * 0.1

                # 诱导信号改变邻居的基因表达
                for i in range(self.维度):
                    # 诱导方向：让邻居的基因型趋向自己的基因型
                    other.基因型[i] += 信号强度 * (c.基因型[i] - other.基因型[i]) * 0.3
                    other.基因型[i] = max(-1.0, min(1.0, other.基因型[i]))

                self.诱导总数 += 1

    # ── R5 分化 ──
    def R5_分化(self):
        """R5分化：细胞特化为不同功能。

        生物学：干细胞根据位置和信号，分化为不同类型的细胞。
        分化是不可逆的——一旦分化，细胞不能回到干细胞状态。

        实现：根据基因表达模式，将未分化细胞分配到不同类型。
        分化后基因型锁定（不可逆）。
        """
        阶段 = 当前发育阶段(self.拍)
        if 阶段 not in ("分化", "神经诱导"):
            return

        for c in self.细胞群:
            if not c.存活 or c.类型 != 0:  # 只分化未分化细胞
                continue

            # 分化条件：分裂次数足够 + 基因表达模式明确
            if c.分裂次数 < 2:
                continue

            # 根据基因表达模式决定分化方向
            # 找到最强表达维度
            最强维度 = max(range(self.维度), key=lambda i: abs(c.基因型[i]))

            # 分化映射
            if abs(c.基因型[最强维度]) < 0.2:
                continue  # 表达不够强，暂不分化的

            # R6侧抑制：检查邻居是否已有相同类型
            邻居 = self.R3_局部盲视(c)
            相同类型邻居 = sum(1 for other, _ in 邻居
                              if other.类型 == self._维度到类型(最强维度))

            if 相同类型邻居 >= 2:
                # 侧抑制：太多相同类型邻居，抑制分化
                continue

            # 执行分化
            新类型 = self._维度到类型(最强维度)
            c.类型 = 新类型

            # 分化后基因型部分锁定——不可逆
            c.分化锁定 = True
            self.分化总数 += 1

    def _维度到类型(self, 维度idx):
        """基因表达维度到细胞类型的映射。"""
        映射 = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 1, 7: 4}
        return 映射.get(维度idx, 4)

    # ── R6 侧抑制 ──
    def R6_侧抑制(self):
        """R6侧抑制：邻近细胞互相抑制相同分化方向。

        生物学：Notch-Delta信号通路——已分化的细胞抑制
        邻近细胞分化为相同类型，确保多样性。

        实现：对每个已分化细胞，抑制邻居分化为相同类型。
        """
        for c in self.细胞群:
            if not c.存活 or c.类型 == 0:
                continue

            邻居 = self.R3_局部盲视(c)

            for other, dist in 邻居:
                if other.类型 != 0:  # 已分化的不受影响
                    continue

                # 侧抑制：抑制邻居分化为相同类型
                抑制强度 = max(0.0, 1.0 - dist / c.感知半径) * 0.05

                # 降低邻居对应维度的基因表达
                对应维度 = self._类型到维度(c.类型)
                if 对应维度 is not None:
                    other.基因型[对应维度] *= (1.0 - 抑制强度)

    def _类型到维度(self, 类型):
        """细胞类型到基因表达维度的反向映射。"""
        映射 = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}
        return 映射.get(类型)

    # ── R7 神经诱导 ──
    def R7_神经诱导(self):
        """R7神经诱导：特定细胞诱导神经组织形成。

        生物学：脊索分泌信号，诱导上方外胚层分化为神经组织。
        神经诱导是神经系统发育的起点。

        实现：联络类型细胞诱导邻近未分化细胞分化为神经类型。
        """
        阶段 = 当前发育阶段(self.拍)
        if 阶段 != "神经诱导":
            return

        for c in self.细胞群:
            if not c.存活 or c.类型 != 4:  # 联络类型作为诱导源
                continue

            邻居 = self.R3_局部盲视(c)

            for other, dist in 邻居:
                if other.类型 != 0:  # 只诱导未分化细胞
                    continue

                # 神经诱导信号
                信号强度 = max(0.0, 1.0 - dist / c.感知半径) * 0.15

                # 强化神经相关维度的基因表达
                other.基因型[0] += 信号强度  # 维度0对应神经类型
                other.基因型[0] = max(-1.0, min(1.0, other.基因型[0]))

    # ── R8 信号经济 ──
    def R8_信号经济(self):
        """R8信号经济：用最少信号传递最多信息。

        生物学：生物系统通过信号压缩和组合编码，
        用最少的信号分子传递最多的信息。

        实现：信号传递时压缩冗余，保留关键信息。
        """
        for c in self.细胞群:
            if not c.存活:
                continue

            # 信号buffer压缩——只保留最强的信号
            if len(c.信号buffer) > 3:
                c.信号buffer.sort(key=lambda s: abs(s), reverse=True)
                c.信号buffer = c.信号buffer[:3]  # 只保留3个最强信号

    # ── R9 免疫耐受 ──
    def R9_免疫耐受(self):
        """R9免疫耐受：系统学会不攻击自身。

        生物学：免疫系统通过负选择学会识别自体，
        不攻击自身细胞——否则就是自身免疫疾病。

        实现：免疫类型细胞检查所有细胞，
        确认自体标记——没有自体标记的细胞被标记为异物。
        """
        阶段 = 当前发育阶段(self.拍)
        if 阶段 not in ("耐受", "成熟", "漂移测试"):
            return

        免疫细胞 = [c for c in self.细胞群 if c.存活 and c.类型 == 5]

        for imm in 免疫细胞:
            邻居 = self.R3_局部盲视(imm)

            for other, dist in 邻居:
                if other.id in self.自体标记:
                    # 自体——耐受
                    other.资源 += 0.001  # 免疫耐受的奖励
                else:
                    # 异物——标记（但不直接杀死，留给R10）
                    other.资源 -= 0.01

    # ── R10 营养性死亡 ──
    def R10_营养性死亡(self):
        """R10营养性死亡：缺乏营养的细胞主动死亡。

        生物学：缺乏营养或生长因子的细胞启动凋亡程序——
        主动死亡而非被动坏死。这是发育塑性的关键。

        实现：资源低于阈值的细胞标记为死亡，
        从细胞群中移除。同时，细胞从环境中获取微量营养。
        """
        存活 = []
        for c in self.细胞群:
            if not c.存活:
                continue

            # 从环境中获取营养——越靠近中心的细胞获得更多（资源梯度）
            r = math.sqrt(c.位置[0]**2 + c.位置[1]**2)
            环境营养 = max(0.0, 0.02 * (1.0 - r / self.空间半径))
            # 分化后的细胞更高效——消耗更少
            if c.类型 != 0:
                环境营养 *= 1.5  # 特化细胞更善于获取营养
            c.资源 += 环境营养

            # 资源消耗——每拍消耗微量
            # 消耗率随年龄增长（老化），但分化细胞消耗更低
            base_consumption = 0.0005 if c.类型 != 0 else 0.001
            消耗 = base_consumption + 0.00005 * min(c.年龄, 200)
            c.资源 -= 消耗

            # 年龄增长
            c.年龄 += 1

            # R10营养性死亡：资源耗尽则死亡
            if c.资源 <= 0.0:
                c.存活 = False
                self.已死亡细胞.append(c)
                self.死亡总数 += 1
            else:
                存活.append(c)

        self.细胞群 = 存活

    # ── R11 稳态 ──
    def R11_稳态(self):
        """R11稳态：系统维持内部稳定。

        生物学：稳态是生命系统的核心特征——
        温度、pH、浓度等维持在特定范围。
        稳态类型细胞负责监测和调节系统状态。

        实现：稳态类型细胞向系统信号注入调节信号，
        维持全局状态稳定。
        """
        稳态细胞 = [c for c in self.细胞群 if c.存活 and c.类型 == 6]

        if not 稳态细胞:
            return

        # 计算系统平均状态
        if self.细胞群:
            均值 = [0.0] * self.维度
            for c in self.细胞群:
                if c.存活:
                    for i in range(self.维度):
                        均值[i] += c.表型[i]
            均值 = [m / max(1, len(self.细胞群)) for m in 均值]

            # 稳态调节——将系统信号拉回零点附近
            for i in range(self.维度):
                self.系统信号[i] = -均值[i] * 0.01

    # ── R12 整体决策 ──
    def R12_整体决策(self):
        """R12整体决策：系统层面的统一决策。

        生物学：有机体不是细胞民主投票——
        是系统层面的涌现决策，超越任何单个细胞。

        实现：系统级信号影响所有细胞，
        但不是命令——是调节（和生物学一样）。
        """
        if not self.细胞群:
            return

        # 系统信号渗透到每个细胞
        for c in self.细胞群:
            if not c.存活:
                continue
            for i in range(self.维度):
                c.基因型[i] += self.系统信号[i] * 0.001
                c.基因型[i] = max(-1.0, min(1.0, c.基因型[i]))

    # ── 全局精卫公式 ──
    def 全局精卫更新(self):
        """更新全局精卫公式状态。

        全局a = 所有细胞表型的均值（外在表现）
        全局b = 所有细胞基因型的均值（内在机制）
        delta = b - a（发育差距）
        sigma = a + b（联合状态）
        accum = integral(delta, sigma)（发育记忆）
        tau = 读accum（浮出所见）
        """
        if not self.细胞群:
            return

        # 计算全局a和b
        a_sum = [0.0] * self.维度
        b_sum = [0.0] * self.维度
        n = 0

        for c in self.细胞群:
            if c.存活:
                for i in range(self.维度):
                    a_sum[i] += c.表型[i]
                    b_sum[i] += c.基因型[i]
                n += 1

        if n == 0:
            return

        self.全局a = [a_sum[i] / n for i in range(self.维度)]
        self.全局b = [b_sum[i] / n for i in range(self.维度)]

        # delta = b - a
        self.全局delta = [self.全局b[i] - self.全局a[i] for i in range(self.维度)]

        # sigma = a + b
        self.全局sigma = [self.全局a[i] + self.全局b[i] for i in range(self.维度)]

        # accum = integral(delta, sigma)
        lr = 拍轴学习率(self.拍)
        self.全局accum = [(1.0 - lr) * self.全局accum[i] + lr * self.全局delta[i] * self.全局sigma[i]
                          for i in range(self.维度)]

        # tau = 读accum
        self.全局tau = [math.tanh(self.全局accum[i]) for i in range(self.维度)]

        # 透明度
        d_norm = math.sqrt(sum(d * d for d in self.全局delta))
        s_norm = math.sqrt(sum(s * s for s in self.全局sigma))
        if s_norm > 1e-10:
            self.全局透明度 = max(0.0, 1.0 - d_norm / s_norm)
        else:
            self.全局透明度 = 1.0

    # ── 一拍发育 ──
    def 一拍(self):
        """执行一拍发育——按发育时窗激活相应规则。"""
        self.拍 += 1
        self.lr = 拍轴学习率(self.拍)

        阶段 = 当前发育阶段(self.拍)

        # 按发育时窗激活规则
        if 阶段 == "卵裂":
            self.R1_卵裂()
            self.R1b_机械排斥()
            self.R2_不对称遗传()

        if 阶段 in ("诱导", "分化", "神经诱导"):
            self.R4_诱导()

        if 阶段 in ("分化", "神经诱导"):
            self.R5_分化()
            self.R6_侧抑制()

        if 阶段 == "神经诱导":
            self.R7_神经诱导()

        # 全阶段规则
        self.R8_信号经济()

        if 阶段 in ("耐受", "成熟", "漂移测试"):
            self.R9_免疫耐受()

        self.R10_营养性死亡()
        self.R11_稳态()
        self.R12_整体决策()

        # 每个细胞的精卫更新
        for c in self.细胞群:
            if c.存活:
                c.精卫更新(self.lr)

        # 全局精卫更新
        self.全局精卫更新()

        # 记录哈希链
        if self.链 and self.拍 % 100 == 0:
            self.链.记("发育", {
                "拍": self.拍,
                "阶段": 阶段,
                "细胞数": len(self.细胞群),
                "透明度": round(self.全局透明度, 4),
                "分裂总数": self.分裂总数,
                "分化总数": self.分化总数,
            })

    # ── 发育统计 ──
    def 统计(self):
        """返回当前发育状态统计。"""
        类型分布 = {}
        for c in self.细胞群:
            if c.存活:
                t = 细胞类型.get(c.类型, "未知")
                类型分布[t] = 类型分布.get(t, 0) + 1

        return {
            "拍": self.拍,
            "阶段": 当前发育阶段(self.拍),
            "存活细胞": len(self.细胞群),
            "死亡细胞": self.死亡总数,
            "分裂总数": self.分裂总数,
            "分化总数": self.分化总数,
            "诱导总数": self.诱导总数,
            "类型分布": 类型分布,
            "全局透明度": round(self.全局透明度, 4),
            "lr": round(self.lr, 4),
        }

    def 摘要(self):
        """简洁摘要。"""
        s = self.统计()
        return (f"[拍{s['拍']:>4}] "
                f"阶段={s['阶段']} "
                f"细胞={s['存活细胞']} "
                f"分化={s['分化总数']} "
                f"透明度={s['全局透明度']:.3f} "
                f"类型={s['类型分布']}")


# ═══════════════════════════════════════════════════════════════
# 演示主循环
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("基因组发育引擎 v1.0 —— 13条基因组规则可运行实现")
    print("发育时窗：卵裂→诱导→分化→神经诱导→耐受→漂移测试")
    print("精卫公式：a≠b（表型≠基因型）驱动发育")
    print("=" * 60)

    random.seed(42)
    引擎 = 基因组发育引擎(维度=8)

    print(f"\n--- 初始状态 ---")
    print(f"受精卵：1个细胞，基因型={引擎.细胞群[0].基因型[:4]}...")

    # 运行完整发育周期
    总拍数 = 500  # 覆盖卵裂→诱导阶段

    for step in range(总拍数):
        引擎.一拍()

        # 在关键时窗边界打印
        if step % 500 == 0 or step == 总拍数 - 1:
            print(引擎.摘要())

        # 如果所有细胞都死了，提前终止
        if not 引擎.细胞群:
            print(f"\n[拍{引擎.拍}] 所有细胞已死亡——发育失败")
            break

    print(f"\n--- 发育结束 ---")
    s = 引擎.统计()
    print(f"总拍数: {s['拍']}")
    print(f"存活细胞: {s['存活细胞']}")
    print(f"死亡细胞: {s['死亡细胞']}")
    print(f"分裂总数: {s['分裂总数']}")
    print(f"分化总数: {s['分化总数']}")
    print(f"诱导总数: {s['诱导总数']}")
    print(f"类型分布: {s['类型分布']}")
    print(f"全局透明度: {s['全局透明度']}")

    print(f"\n--- 精卫公式验证 ---")
    print(f"全局a（表型均值）: {[round(v, 3) for v in 引擎.全局a[:4]]}...")
    print(f"全局b（基因型均值）: {[round(v, 3) for v in 引擎.全局b[:4]]}...")
    print(f"全局delta（b-a）: {[round(v, 3) for v in 引擎.全局delta[:4]]}...")
    print(f"全局tau（读出）: {[round(v, 3) for v in 引擎.全局tau[:4]]}...")
    print(f"透明度（a=b的程度）: {引擎.全局透明度:.4f}")
    print(f"发育就是a趋向b的过程——但永远追不到（自欺引擎）")

    # 验证发育时窗各阶段
    print(f"\n--- 发育时窗验证 ---")
    for 阶段, (起, 止) in 发育时窗.items():
        print(f"  {阶段}: 拍{起}-{止}")
    print(f"  成熟: 拍6000+")
