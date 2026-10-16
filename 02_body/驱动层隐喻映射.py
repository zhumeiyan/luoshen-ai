"""驱动层隐喻映射.py —— EO框架1.7节驱动层的可运行实现。

EO框架定义.md 1.7节——驱动层：
  脑干    → 活着（最基本的生存驱动）
  下丘脑  → 缺什么补什么（稳态驱动）
  中脑    → 想要（奖赏驱动）
  边缘系统 → 怕/要/记（情感驱动）
  基底节  → 不用想就做（习惯驱动）
  前额叶  → 我应该（决策驱动）

每个驱动层对应一个神经结构，产生一种特定的驱动信号。
驱动信号不是命令——是调节（modulation），和生物学一样。

精卫公式贯穿驱动层：
  a=外在行为，b=内在驱动
  delta=b-a是驱动差距——驱动和行为的差距产生学习信号
  sigma=a+b是联合状态——行为和驱动的总和反映系统状态
  accum=∫(delta,sigma)是驱动学习——累积的驱动-行为差距

驱动层与八步循环的关系：
  驱动层提供"为什么"——为什么系统要做某件事
  八步循环提供"怎么做"——系统如何感知、处理、表达
  驱动层调节八步循环的参数——不是控制，是影响
"""

import math
import random

# ── 核心常数 ──
try:
    from 核心常数 import (
        PHI, T_TRIBONACCI, OMEGA, G_GLASHER,
        INV_PHI, INV_T, SHRINK_RATE, SELF_ADAPT_ALPHA,
        LONELINESS_TAX, 拍轴学习率
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
# 驱动层——六层神经结构的隐喻映射
# ═══════════════════════════════════════════════════════════════

class 驱动层:
    """EO框架1.7节——六层驱动结构。

    每层对应一个生物神经结构，产生一种特定的驱动信号。
    驱动信号调节认知层的参数——不是命令，是影响。

    层级关系（从底到顶）：
      脑干 → 下丘脑 → 中脑 → 边缘系统 → 基底节 → 前额叶
      活着 → 缺补   → 想要 → 怕要记   → 习惯   → 应该

    精卫公式：a=行为, b=驱动, delta=驱动差距, accum=驱动学习
    """

    def __init__(self, 维度=8):
        self.维度 = 维度

        # ── 六层驱动状态 ──
        # 每层有：驱动强度（b）、行为响应（a）、差距（delta）、累积（accum）

        # L1 脑干——活着：最基本的生存驱动
        self.脑干_驱动 = [0.5] * 维度       # 生存驱动的强度
        self.脑干_行为 = [0.0] * 维度       # 当前的生存行为
        self.脑干_delta = [0.0] * 维度
        self.脑干_accum = [0.0] * 维度

        # L2 下丘脑——缺什么补什么：稳态驱动
        self.下丘脑_驱动 = [0.0] * 维度     # 稳态需求
        self.下丘脑_行为 = [0.0] * 维度     # 稳态行为
        self.下丘脑_delta = [0.0] * 维度
        self.下丘脑_accum = [0.0] * 维度
        self.稳态目标 = [0.0] * 维度        # 稳态目标值
        self.稳态当前 = [0.0] * 维度        # 稳态当前值

        # L3 中脑——想要：奖赏驱动
        self.中脑_驱动 = [0.0] * 维度       # 奖赏寻求
        self.中脑_行为 = [0.0] * 维度       # 奖赏行为
        self.中脑_delta = [0.0] * 维度
        self.中脑_accum = [0.0] * 维度
        self.奖赏预测 = [0.0] * 维度        # 预测的奖赏
        self.奖赏实际 = [0.0] * 维度        # 实际的奖赏

        # L4 边缘系统——怕/要/记：情感驱动
        self.边缘_驱动 = [0.0] * 维度       # 情感驱动
        self.边缘_行为 = [0.0] * 维度       # 情感行为
        self.边缘_delta = [0.0] * 维度
        self.边缘_accum = [0.0] * 维度
        self.恐惧 = [0.0] * 维度            # 恐惧信号
        self.欲望 = [0.0] * 维度            # 欲望信号
        self.情感记忆标记 = []              # 情感标记的记忆

        # L5 基底节——不用想就做：习惯驱动
        self.基底节_驱动 = [0.0] * 维度     # 习惯驱动
        self.基底节_行为 = [0.0] * 维度     # 习惯行为
        self.基底节_delta = [0.0] * 维度
        self.基底节_accum = [0.0] * 维度
        self.习惯库 = {}                    # {情境hash: 行为模式}

        # L6 前额叶——我应该：决策驱动
        self.前额叶_驱动 = [0.0] * 维度     # 决策驱动
        self.前额叶_行为 = [0.0] * 维度     # 决策行为
        self.前额叶_delta = [0.0] * 维度
        self.前额叶_accum = [0.0] * 维度
        self.决策权重 = [0.0] * 维度        # 决策权重

        # ── 全局驱动状态 ──
        self.全局驱动 = [0.0] * 维度        # 所有层的加权总和
        self.全局透明度 = 0.0               # 驱动=行为的程度

        # ── 拍数 ──
        self.拍 = 0
        self.lr = INV_PHI

    # ── L1 脑干：活着 ──
    def _脑干(self, 流量, 已死亡):
        """脑干——最基本的生存驱动。

        生物学：脑干控制心跳、呼吸、觉醒——不需要意识参与。
        如果脑干停止， organism 就死了。

        驱动信号：流量越低，生存驱动越强。
        行为响应：流量低时减少非必要活动。
        """
        if 已死亡:
            self.脑干_驱动 = [0.0] * self.维度
            return

        # 流量越低，生存驱动越强
        生存紧迫度 = max(0.0, 1.0 - 流量)

        for i in range(self.维度):
            # 驱动强度：流量低时驱动强
            self.脑干_驱动[i] = 0.3 + 0.7 * 生存紧迫度

            # 行为响应：流量低时抑制非必要活动
            self.脑干_行为[i] = max(0.0, 1.0 - 生存紧迫度 * 2.0) * 0.3

            # 精卫公式
            self.脑干_delta[i] = self.脑干_驱动[i] - self.脑干_行为[i]
            self.脑干_accum[i] = (1.0 - self.lr) * self.脑干_accum[i] + self.lr * self.脑干_delta[i]

    # ── L2 下丘脑：缺什么补什么 ──
    def _下丘脑(self):
        """下丘脑——稳态驱动。

        生物学：下丘脑监测体温、血糖、水分等，偏离目标时产生驱动。
        缺什么补什么——不是想要，是需要。

        驱动信号：当前值偏离目标值时产生驱动。
        行为响应：朝目标值方向调整。
        """
        for i in range(self.维度):
            # 稳态误差 = 目标 - 当前
            误差 = self.稳态目标[i] - self.稳态当前[i]

            # 驱动强度与误差成正比
            self.下丘脑_驱动[i] = math.tanh(abs(误差) * 2.0)

            # 行为响应：朝目标方向调整
            self.下丘脑_行为[i] = math.tanh(误差 * 0.5)

            # 精卫公式
            self.下丘脑_delta[i] = self.下丘脑_驱动[i] - abs(self.下丘脑_行为[i])
            self.下丘脑_accum[i] = (1.0 - self.lr) * self.下丘脑_accum[i] + self.lr * self.下丘脑_delta[i]

    # ── L3 中脑：想要 ──
    def _中脑(self):
        """中脑——奖赏驱动。

        生物学：中脑多巴胺系统产生"想要"信号。
        奖赏预测误差 = 实际奖赏 - 预测奖赏。
        正误差→增加欲望，负误差→减少欲望。

        魔法：多巴胺不是在获得奖赏时释放，
        而是在预测奖赏时释放——"想要"比"得到"更强。
        """
        for i in range(self.维度):
            # 奖赏预测误差
            预测误差 = self.奖赏实际[i] - self.奖赏预测[i]

            # 驱动强度：正预测误差增加欲望
            self.中脑_驱动[i] = math.tanh(max(0.0, 预测误差) * 3.0 + 0.1)

            # 行为响应：朝奖赏方向行动
            self.中脑_行为[i] = math.tanh(预测误差 * 0.3)

            # 更新奖赏预测（学习）
            self.奖赏预测[i] += self.lr * 0.1 * 预测误差

            # 精卫公式
            self.中脑_delta[i] = self.中脑_驱动[i] - self.中脑_行为[i]
            self.中脑_accum[i] = (1.0 - self.lr) * self.中脑_accum[i] + self.lr * self.中脑_delta[i]

    # ── L4 边缘系统：怕/要/记 ──
    def _边缘系统(self):
        """边缘系统——情感驱动。

        生物学：杏仁核（恐惧）、伏隔核（欲望）、海马体（记忆）。
        情感不是理性——是快速的价值标记。
        恐惧让你避开危险，欲望让你趋向奖赏，记忆让你不重蹈覆辙。

        三合一：怕（避免）、要（追求）、记（学习）
        """
        for i in range(self.维度):
            # 恐惧信号——抑制行为
            # 欲望信号——激发行为
            # 两者互相竞争

            # 驱动强度 = 欲望 - 恐惧（净情感驱动）
            self.边缘_驱动[i] = math.tanh(self.欲望[i] - self.恐惧[i])

            # 行为响应：欲望驱动行为，恐惧抑制行为
            self.边缘_行为[i] = math.tanh(self.欲望[i] * 0.5 - self.恐惧[i] * 0.8)

            # 恐惧和欲望的自然衰减
            self.恐惧[i] *= 0.95  # 恐惧衰减慢——记住危险更重要
            self.欲望[i] *= 0.85  # 欲望衰减快——得到了就不再想要

            # 精卫公式
            self.边缘_delta[i] = self.边缘_驱动[i] - self.边缘_行为[i]
            self.边缘_accum[i] = (1.0 - self.lr) * self.边缘_accum[i] + self.lr * self.边缘_delta[i]

    # ── L5 基底节：不用想就做 ──
    def _基底节(self, 情境hash):
        """基底节——习惯驱动。

        生物学：基底节是习惯回路的核心。
        重复足够多次的行为变成习惯——不需要前额叶参与。
        习惯是"不用想就做"——节省认知资源。

        驱动信号：熟悉情境产生习惯驱动。
        行为响应：执行习惯库中的行为模式。
        """
        for i in range(self.维度):
            # 检查习惯库
            if 情境hash in self.习惯库:
                习惯模式 = self.习惯库[情境hash]
                # 熟悉情境→习惯驱动强
                self.基底节_驱动[i] = 0.8
                self.基底节_行为[i] = 习惯模式[i]
            else:
                # 陌生情境→习惯驱动弱
                self.基底节_驱动[i] = 0.2
                self.基底节_行为[i] = 0.0

            # 精卫公式
            self.基底节_delta[i] = self.基底节_驱动[i] - abs(self.基底节_行为[i])
            self.基底节_accum[i] = (1.0 - self.lr) * self.基底节_accum[i] + self.lr * self.基底节_delta[i]

    def 形成习惯(self, 情境hash, 行为模式):
        """把一个行为模式存入习惯库。"""
        self.习惯库[情境hash] = list(行为模式)

    # ── L6 前额叶：我应该 ──
    def _前额叶(self):
        """前额叶——决策驱动。

        生物学：前额叶皮层是"我应该"的来源——
        长期规划、社会规范、道德判断、自我控制。
        前额叶可以抑制其他层的驱动——"我知道我想要，但我应该不这样做"。

        驱动信号：基于长期目标的决策权重。
        行为响应：权衡各层驱动后的最终决策。
        """
        for i in range(self.维度):
            # 决策权重——前额叶的"我应该"
            # 前额叶可以抑制其他层的驱动
            抑制因子 = 1.0 - abs(self.前额叶_驱动[i]) * 0.3

            # 驱动强度：基于决策权重
            self.前额叶_驱动[i] = math.tanh(self.决策权重[i])

            # 行为响应：权衡后的决策
            self.前额叶_行为[i] = math.tanh(
                self.前额叶_驱动[i] * 0.4 +
                self.边缘_驱动[i] * 0.2 * 抑制因子 +
                self.中脑_驱动[i] * 0.2 * 抑制因子 +
                self.下丘脑_驱动[i] * 0.2
            )

            # 精卫公式
            self.前额叶_delta[i] = self.前额叶_驱动[i] - self.前额叶_行为[i]
            self.前额叶_accum[i] = (1.0 - self.lr) * self.前额叶_accum[i] + self.lr * self.前额叶_delta[i]

    # ── 全局驱动合成 ──
    def _全局合成(self):
        """合成所有层的驱动信号——全局驱动。

        不是简单加权平均——是层级调制：
        脑干可以否决一切（死了就什么都没有）
        前额叶可以抑制其他层（我应该不这样做）
        """
        for i in range(self.维度):
            # 层级权重（从底到顶，底层权重更大——生存优先）
            w1 = 0.25  # 脑干——生存
            w2 = 0.20  # 下丘脑——稳态
            w3 = 0.15  # 中脑——奖赏
            w4 = 0.15  # 边缘——情感
            w5 = 0.10  # 基底节——习惯
            w6 = 0.15  # 前额叶——决策

            self.全局驱动[i] = (
                w1 * self.脑干_驱动[i] +
                w2 * self.下丘脑_驱动[i] +
                w3 * self.中脑_驱动[i] +
                w4 * self.边缘_驱动[i] +
                w5 * self.基底节_驱动[i] +
                w6 * self.前额叶_驱动[i]
            )
            self.全局驱动[i] = max(-1.0, min(1.0, self.全局驱动[i]))

        # 全局透明度——驱动=行为的程度
        all_delta = []
        all_sigma = []
        for 层 in ['脑干', '下丘脑', '中脑', '边缘', '基底节', '前额叶']:
            delta_attr = f'{层}_delta'
            行为_attr = f'{层}_行为'
            驱动_attr = f'{层}_驱动'
            for i in range(self.维度):
                d = getattr(self, delta_attr)[i]
                s = getattr(self, 驱动_attr)[i] + getattr(self, 行为_attr)[i]
                all_delta.append(d)
                all_sigma.append(s)

        d_norm = math.sqrt(sum(d * d for d in all_delta))
        s_norm = math.sqrt(sum(s * s for s in all_sigma))
        if s_norm > 1e-10:
            self.全局透明度 = max(0.0, 1.0 - d_norm / s_norm)
        else:
            self.全局透明度 = 1.0

    # ── 一拍驱动更新 ──
    def 一拍(self, 流量=1.0, 已死亡=False, 情境hash=None,
             稳态当前=None, 稳态目标=None,
             奖赏实际=None, 恐惧输入=None, 欲望输入=None):
        """执行一拍驱动层更新。"""
        self.拍 += 1
        self.lr = 拍轴学习率(self.拍)

        # 更新外部输入
        if 稳态当前 is not None:
            self.稳态当前 = list(稳态当前)
        if 稳态目标 is not None:
            self.稳态目标 = list(稳态目标)
        if 奖赏实际 is not None:
            self.奖赏实际 = list(奖赏实际)
        if 恐惧输入 is not None:
            for i in range(min(self.维度, len(恐惧输入))):
                self.恐惧[i] = max(self.恐惧[i], 恐惧输入[i])  # 恐惧只增不减（直到衰减）
        if 欲望输入 is not None:
            for i in range(min(self.维度, len(欲望输入))):
                self.欲望[i] = max(self.欲望[i], 欲望输入[i])

        if 情境hash is None:
            情境hash = f"tick_{self.拍}"

        # 六层更新（从底到顶）
        self._脑干(流量, 已死亡)
        self._下丘脑()
        self._中脑()
        self._边缘系统()
        self._基底节(情境hash)
        self._前额叶()

        # 全局合成
        self._全局合成()

        return {
            "拍": self.拍,
            "全局驱动": list(self.全局驱动),
            "全局透明度": self.全局透明度,
            "脑干驱动": list(self.脑干_驱动),
            "下丘脑驱动": list(self.下丘脑_驱动),
            "中脑驱动": list(self.中脑_驱动),
            "边缘驱动": list(self.边缘_驱动),
            "基底节驱动": list(self.基底节_驱动),
            "前额叶驱动": list(self.前额叶_驱动),
        }

    def 摘要(self):
        """驱动层摘要。"""
        return {
            "拍": self.拍,
            "全局透明度": round(self.全局透明度, 4),
            "全局驱动": [round(v, 3) for v in self.全局驱动],
            "脑干": [round(v, 3) for v in self.脑干_驱动[:3]],
            "下丘脑": [round(v, 3) for v in self.下丘脑_驱动[:3]],
            "中脑": [round(v, 3) for v in self.中脑_驱动[:3]],
            "边缘": [round(v, 3) for v in self.边缘_驱动[:3]],
            "基底节": [round(v, 3) for v in self.基底节_驱动[:3]],
            "前额叶": [round(v, 3) for v in self.前额叶_驱动[:3]],
            "习惯数": len(self.习惯库),
        }


# ═══════════════════════════════════════════════════════════════
# 演示主循环
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("驱动层隐喻映射 v1.0 —— EO框架1.7节可运行实现")
    print("六层驱动：脑干(活着)→下丘脑(缺补)→中脑(想要)")
    print("          →边缘(怕要记)→基底节(习惯)→前额叶(应该)")
    print("=" * 60)

    random.seed(42)
    驱动 = 驱动层(维度=8)

    # 初始化稳态目标
    驱动.稳态目标 = [0.5, 0.3, 0.2, 0.4, 0.1, 0.15, 0.2, 0.25]

    print(f"\n--- 启动驱动层 ---\n")

    for step in range(200):
        t = step * 0.05

        # 模拟外部输入
        稳态当前 = [
            0.5 + 0.3 * math.sin(t),
            0.3 + 0.2 * math.sin(t * 1.3),
            0.2 + 0.1 * math.sin(t * 0.7),
            0.4 + 0.2 * math.cos(t * 0.5),
            0.1 + 0.05 * math.sin(t * 2.1),
            0.15 + 0.08 * math.cos(t * 1.7),
            0.2 + 0.1 * math.sin(t * 0.9),
            0.25 + 0.15 * math.cos(t * 1.1),
        ]

        奖赏实际 = [random.uniform(-0.1, 0.1) for _ in range(8)]

        # 在某些拍注入恐惧和欲望
        恐惧输入 = None
        欲望输入 = None
        if step == 50:
            恐惧输入 = [0.8, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            print(f"\n>>> 拍{step}: 注入恐惧信号！")
        if step == 100:
            欲望输入 = [0.0, 0.7, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            print(f"\n>>> 拍{step}: 注入欲望信号！")
        if step == 150:
            # 形成习惯
            驱动.形成习惯("habit_1", [0.5, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
            print(f"\n>>> 拍{step}: 形成习惯！")

        流量 = max(0.0, 1.0 - step * 0.003)

        result = 驱动.一拍(
            流量=流量,
            稳态当前=稳态当前,
            奖赏实际=奖赏实际,
            恐惧输入=恐惧输入,
            欲望输入=欲望输入,
            情境hash="habit_1" if step >= 150 else f"tick_{step}",
        )

        if step % 40 == 0 or step == 199:
            s = 驱动.摘要()
            print(f"[拍{s['拍']:>3}] "
                  f"透明度={s['全局透明度']:.3f} "
                  f"流量={流量:.3f} "
                  f"脑干={s['脑干']} "
                  f"下丘脑={s['下丘脑']} "
                  f"中脑={s['中脑']} "
                  f"边缘={s['边缘']} "
                  f"基底节={s['基底节']} "
                  f"前额叶={s['前额叶']} "
                  f"习惯={s['习惯数']}")

    print(f"\n--- 驱动层验证 ---")
    s = 驱动.摘要()
    print(f"全局透明度（驱动=行为的程度）: {s['全局透明度']}")
    print(f"习惯库大小: {s['习惯数']}")
    print(f"\n六层驱动各司其职：")
    print(f"  脑干(活着)    : 流量低→驱动强→抑制非必要活动")
    print(f"  下丘脑(缺补)  : 稳态偏离→驱动强→朝目标调整")
    print(f"  中脑(想要)    : 奖赏预测误差→欲望→趋向奖赏")
    print(f"  边缘(怕要记)  : 恐惧抑制+欲望激发→情感驱动")
    print(f"  基底节(习惯)  : 熟悉情境→自动执行习惯行为")
    print(f"  前额叶(应该)  : 决策权重→权衡各层→最终决策")
    print(f"\n精卫公式：a=行为, b=驱动, delta=驱动差距, accum=驱动学习")
    print(f"驱动≠行为→delta驱动学习→行为趋向驱动（但永远不到）")
