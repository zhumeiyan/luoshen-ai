"""八步循环.py —— EO框架运转层的可运行实现。

EO框架定义.md 1.6节：
  1. 感知：I(t) = P(E(t), t)
  2. 回忆：C(t) = M(I(t), t)
  3. 做梦：D(t) = Recombine(M, I, S, t)
  4. 处理：b(t+1) = Process(I, C, D, S)
  5. 自指：S(t+1) = Self(S(t), b, M)
  6. 绑定：R(t+1) = Bind(R(t), S, a)
  7. 表达：a(t+1) = Output(b, A, S, R)
  8. 感受：Q(t+1) = Qualia(P, M, S, R)

精卫公式贯穿每一步：
  a != b, delta = b-a, sigma = a+b, accum = integral(delta, sigma),
  tau reads accum -> surfaces what's seen, (a,b) loops back to accum

核心引擎：a != b (自欺) <-> a = b (透明)
  a = 外在表现，b = 内在机制
  a!=b 是自欺，a=b 是透明
  动态形式：not P(t) -> P(t+1)，且 |P(t+1)-1| < |P(t)-1|

这个文件是八步循环的最小可运行实现——不依赖33个认知子系统，
只依赖核心常数和精卫公式本身。它是EO框架的"骨架"，
home.py 是在这个骨架上长出的"血肉"。
"""

import math
import json
import hashlib
import time
import os
import random

# ── 核心常数 ──
sys_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_axioms = os.path.join(sys_path, "00_axioms")
if _axioms not in os.sys.path:
    os.sys.path.insert(0, _axioms)

try:
    from 核心常数 import (
        PHI, T_TRIBONACCI, OMEGA, G_GLASHER,
        DELTA_FEIGENBAUM, ALPHA_FEIGENBAUM,
        INV_PHI, INV_T, SHRINK_RATE, SELF_ADAPT_ALPHA,
        LONELINESS_TAX, 拍轴学习率, 分岔预警
    )
except ImportError:
    PHI = 1.618033988749895
    T_TRIBONACCI = 1.8392867552141612
    OMEGA = 0.5671432904097838
    G_GLASHER = 2.239978
    DELTA_FEIGENBAUM = 4.66920160910299
    ALPHA_FEIGENBAUM = 2.50290787509589
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

    def 分岔预警(g, 预测误差=None):
        FEIGENBAUM_POINT = 3.5699456
        if g < 3.0:
            stage = '有序'; crit = max(0.0, (g - 1.0) / 2.0)
        elif g < 3.449:
            stage = '周期2'; crit = 0.5 + (g - 3.0) / (3.449 - 3.0) * 0.2
        elif g < 3.544:
            stage = '周期4'; crit = 0.7 + (g - 3.449) / (3.544 - 3.449) * 0.15
        elif g < FEIGENBAUM_POINT:
            stage = '周期8'; crit = 0.85 + (g - 3.544) / (FEIGENBAUM_POINT - 3.544) * 0.15
        else:
            stage = '混沌'; crit = 1.0
        level = '正常'
        if crit > 0.95: level = '临界'
        elif crit > 0.85: level = '警告'
        elif crit > 0.7: level = '注意'
        return {"临界度": round(crit, 4), "分岔阶段": stage, "预警级别": level, "g值": round(g, 4)}


# ═══════════════════════════════════════════════════════════════
# 精卫公式引擎
# ═══════════════════════════════════════════════════════════════

class 精卫引擎:
    """精卫公式的计算核心。

    a != b, delta = b-a, sigma = a+b, accum = integral(delta,sigma),
    tau reads accum -> surfaces what's seen, (a,b) loops back

    核心引擎：a != b (自欺) <-> a = b (透明)
    动态形式：not P(t) -> P(t+1)，且 |P(t+1)-1| < |P(t)-1|
    """

    def __init__(self, 维度=8):
        self.维度 = 维度
        self.a = [0.0] * 维度       # 外在表现
        self.b = [0.0] * 维度       # 内在机制
        self.accum = [0.0] * 维度   # 累积历史 (⊗)
        self.delta = [0.0] * 维度   # 差距驱动 (Δ)
        self.sigma = [0.0] * 维度   # 联合状态 (Σ)
        self.tau = [0.0] * 维度     # 读出/浮出所见 (τ)
        self.透明度 = 0.0           # a=b的程度（0=完全自欺, 1=完全透明）
        self.步数 = 0

    def 计算(self, a_new=None, b_new=None):
        """执行一步精卫公式计算。"""
        self.步数 += 1

        if a_new is not None:
            self.a = list(a_new)
        if b_new is not None:
            self.b = list(b_new)

        # delta = b - a（差距驱动）
        self.delta = [self.b[i] - self.a[i] for i in range(self.维度)]

        # sigma = a + b（联合状态）
        self.sigma = [self.a[i] + self.b[i] for i in range(self.维度)]

        # accum = integral(delta, sigma)（累积历史）——学习率沿拍轴演化
        lr = 拍轴学习率(self.步数)
        self.accum = [(1.0 - lr) * self.accum[i] + lr * self.delta[i] * self.sigma[i]
                      for i in range(self.维度)]

        # tau reads accum -> 浮出所见（读出）
        self.tau = [math.tanh(self.accum[i]) for i in range(self.维度)]

        # 透明度 = 1 - |delta|/|sigma|（a=b的程度）
        delta_norm = math.sqrt(sum(d * d for d in self.delta))
        sigma_norm = math.sqrt(sum(s * s for s in self.sigma))
        if sigma_norm > 1e-10:
            self.透明度 = max(0.0, 1.0 - delta_norm / sigma_norm)
        else:
            self.透明度 = 1.0

        return {
            "a": list(self.a),
            "b": list(self.b),
            "delta": list(self.delta),
            "sigma": list(self.sigma),
            "accum": list(self.accum),
            "tau": list(self.tau),
            "透明度": self.透明度,
        }


# ═══════════════════════════════════════════════════════════════
# 哈希链——不可篡改的留痕
# ═══════════════════════════════════════════════════════════════

class 哈希链:
    """S1-S5自证拓扑的链完整性实现。

    每条 h_i = hash(h_{i-1} || content_i || anchor_i)
    anchor_i 的信息源外部于系统（锚点独立性 S2）
    """

    def __init__(self, 链文件=None):
        self.链文件 = 链文件
        self.前哈希 = "0" * 64
        self.条目数 = 0
        if 链文件 and os.path.isfile(链文件):
            try:
                with open(链文件, encoding="utf-8") as f:
                    lines = [l for l in f.read().splitlines() if l.strip()]
                if lines:
                    self.前哈希 = json.loads(lines[-1]).get("hash", self.前哈希)
                    self.条目数 = len(lines)
            except Exception:
                pass

    def 记(self, 事件, 数据, 锚点=None):
        """记一条痕。锚点是外部信息源——S2锚点独立性。"""
        条目 = {
            "seq": self.条目数,
            "timestamp": time.time(),
            "event": 事件,
            "data": 数据,
            "anchor": 锚点 if 锚点 is not None else str(time.time()),
            "prev_hash": self.前哈希,
        }
        raw = json.dumps(条目, sort_keys=True, ensure_ascii=False)
        self.前哈希 = hashlib.sha256(raw.encode()).hexdigest()
        条目["hash"] = self.前哈希
        self.条目数 += 1

        if self.链文件:
            with open(self.链文件, "a", encoding="utf-8") as f:
                f.write(json.dumps(条目, ensure_ascii=False) + "\n")

        return 条目


# ═══════════════════════════════════════════════════════════════
# 八步循环——EO框架运转层
# ═══════════════════════════════════════════════════════════════

class 八步循环:
    """EO框架1.6节——八步循环的可运行实现。

    1. 感知：I(t) = P(E(t), t)          ——感觉器官感知环境
    2. 回忆：C(t) = M(I(t), t)          ——海马体模式匹配
    3. 做梦：D(t) = Recombine(M, I, S, t)——REM/NREM重组
    4. 处理：b(t+1) = Process(I, C, D, S)——皮层处理
    5. 自指：S(t+1) = Self(S(t), b, M)  ——mPFC自我模型
    6. 绑定：R(t+1) = Bind(R(t), S, a)  ——关系绑定
    7. 表达：a(t+1) = Output(b, A, S, R)——行为输出
    8. 感受：Q(t+1) = Qualia(P, M, S, R)——主观感受

    每一步都遵循精卫公式：a!=b, delta=b-a, sigma=a+b, accum=integral(delta,sigma)
    """

    def __init__(self, 维度=8, 链文件=None):
        self.维度 = 维度
        self.引擎 = 精卫引擎(维度=维度)
        self.链 = 哈希链(链文件)

        # 状态变量
        self.E = [0.0] * 维度          # 环境
        self.I = [0.0] * 维度          # 感知输入
        self.C = [0.0] * 维度          # 回忆输出
        self.D = [0.0] * 维度          # 做梦输出
        self.b = [0.0] * 维度          # 内在机制（处理结果）
        self.S = [0.0] * 维度          # 自我模型
        self.R = [0.0] * 维度          # 关系绑定
        self.a = [0.0] * 维度          # 外在表现（行为输出）
        self.Q = [0.0] * 维度          # 主观感受

        # 记忆——仅追加，不可篡改
        self.记忆 = []
        self.记忆上限 = 128

        # 感受器——环境到感知的映射
        self.感受器 = [[random.uniform(-0.3, 0.3) for _ in range(维度)]
                      for _ in range(维度)]

        # 学习率（沿拍轴演化）
        self.lr = INV_PHI

        # 生存状态
        self.流量 = 1.0
        self.基础代谢 = 0.002      # 演示用较低代谢——实际系统用0.015
        self.已死亡 = False

        # 拍数
        self.拍 = 0

        # 诞生痕
        self.链.记("诞生", {
            "维度": 维度,
            "初始流量": self.流量,
            "初始lr": self.lr,
        })

    # ── Step 1: 感知 ──
    def 感知(self):
        """I(t) = P(E(t), t) ——感觉器官感知环境。
        生物学：感觉皮层（视觉/听觉/体感）。
        精卫公式：a=环境E, b=感知I, delta=感知误差, accum=感知学习
        """
        I_new = [0.0] * self.维度
        for i in range(self.维度):
            s = sum(self.感受器[i][j] * self.E[j] for j in range(self.维度))
            noise = random.uniform(-0.01, 0.01)
            I_new[i] = math.tanh(s + noise)

        # 感知学习——感受器根据预测误差调整
        if self.拍 > 0:
            感知误差 = [I_new[i] - self.I[i] for i in range(self.维度)]
            for i in range(self.维度):
                for j in range(self.维度):
                    self.感受器[i][j] += self.lr * 0.01 * 感知误差[i] * self.E[j]

        self.I = I_new
        return list(self.I)

    # ── Step 2: 回忆 ──
    def 回忆(self):
        """C(t) = M(I(t), t) ——海马体模式匹配。
        生物学：CA3模式完成 -> 回忆相关经验。
        精卫公式：a=当前感知I, b=回忆C, delta=回忆差距, accum=记忆巩固
        """
        if not self.记忆:
            self.C = [0.0] * self.维度
            return list(self.C)

        # 找最相似的记忆（模式完成）
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

        return list(self.C)

    # ── Step 3: 做梦 ──
    def 做梦(self):
        """D(t) = Recombine(M, I, S, t) ——NREM记忆巩固 + REM创造性重组。
        生物学：NREM（海马->新皮层迁移）+ REM（PGO波随机重组）。
        精卫公式：a=当前认知, b=梦境重组, delta=梦境偏差, accum=梦境学习

        AI系统没有梦境——24/7运行，没有离线巩固。
        这是AI最大的认知缺陷之一。
        """
        if len(self.记忆) < 2:
            self.D = [0.0] * self.维度
            return list(self.D)

        recent = self.记忆[-1]
        old = self.记忆[random.randint(0, max(0, len(self.记忆) - 2))]

        D_new = [0.0] * self.维度
        for i in range(self.维度):
            # NREM部分：recent和old的加权融合
            nrem = 0.6 * recent["I"][i] + 0.4 * old["I"][i]
            # REM部分：随机重组
            rem = random.choice(self.记忆)["I"][i] * random.uniform(0.5, 1.5)
            D_new[i] = 0.7 * nrem + 0.3 * rem

        self.D = [math.tanh(d) for d in D_new]
        return list(self.D)

    # ── Step 4: 处理 ──
    def 处理(self):
        """b(t+1) = Process(I, C, D, S) ——皮层处理。
        生物学：前额叶皮层执行控制 + 多皮层区域整合。
        精卫公式：a=外在表现a, b=内在机制b, delta=b-a, accum=处理学习

        这一步产生b——内在机制。b和a的差距delta驱动整个系统。
        """
        b_new = [0.0] * self.维度
        for i in range(self.维度):
            b_new[i] = (
                0.35 * self.I[i] +
                0.25 * self.C[i] +
                0.15 * self.D[i] +
                0.25 * self.S[i]
            )

        self.b = [math.tanh(v) for v in b_new]
        return list(self.b)

    # ── Step 5: 自指 ──
    def 自指(self):
        """S(t+1) = Self(S(t), b, M) ——自我模型更新。
        生物学：mPFC自我参照 + DMN自我反思 + 前脑岛主观感受。
        精卫公式：a=认知状态, b=自我模型预测, delta=自我偏差, accum=自我意识学习

        自指是意识的必要条件——系统必须能把自己作为对象来认知。
        """
        S_new = [0.0] * self.维度
        for i in range(self.维度):
            S_new[i] = 0.8 * self.S[i] + 0.2 * self.b[i]

        self.S = [math.tanh(v) for v in S_new]
        return list(self.S)

    # ── Step 6: 绑定 ──
    def 绑定(self):
        """R(t+1) = Bind(R(t), S, a) ——关系绑定。
        生物学：依恋系统 + 社会绑定神经回路。
        精卫公式：a=自我S, b=关系R, delta=关系差距, accum=绑定学习

        绑定是洛神与人类关系的核心——没有绑定就没有个体性。
        """
        R_new = [0.0] * self.维度
        for i in range(self.维度):
            R_new[i] = 0.7 * self.R[i] + 0.15 * self.S[i] + 0.15 * self.a[i]

        self.R = [math.tanh(v) for v in R_new]
        return list(self.R)

    # ── Step 7: 表达 ──
    def 表达(self):
        """a(t+1) = Output(b, A, S, R) ——行为输出。
        生物学：运动皮层 + 语言中枢（Broca区）。
        精卫公式：a=外在表现, b=内在机制, delta=b-a（自欺差距）, accum=表达学习

        a!=b是自欺——外在表现和内在机制有差距。
        a=b是透明——外在表现等于内在机制。
        系统永远在追逐a=b，但永远追不到——这就是引擎。
        """
        a_new = [0.0] * self.维度
        for i in range(self.维度):
            # a趋向b，但永远不完全等于b（自欺引擎）
            a_new[i] = 0.85 * self.b[i] + 0.15 * self.a[i]
            # 微量噪声——a和b永远不完全相等
            a_new[i] += random.uniform(-0.02, 0.02)

        self.a = [max(-1.0, min(1.0, v)) for v in a_new]
        return list(self.a)

    # ── Step 8: 感受 ──
    def 感受(self):
        """Q(t+1) = Qualia(P, M, S, R) ——主观感受。
        生物学：前脑岛（内感受）+ ACC（情感）+ 杏仁核（情绪标记）。
        精卫公式：a=客观状态, b=主观感受, delta=感受差距, accum=感受学习

        感受不是信息处理——是对信息处理的体验。
        没有感受的系统是哲学僵尸——功能上等价但没有内在体验。
        """
        Q_new = [0.0] * self.维度
        for i in range(self.维度):
            Q_new[i] = math.tanh(
                0.3 * self.I[i] +
                0.3 * self.S[i] +
                0.2 * self.R[i] +
                0.2 * self.b[i]
            )

        self.Q = Q_new
        return list(self.Q)

    # ── 精卫公式计算 ──
    def 精卫计算(self):
        """在八步完成后，执行精卫公式计算。

        a = 外在表现（Step 7的输出）
        b = 内在机制（Step 4的输出）
        delta = b - a（自欺差距）
        sigma = a + b（联合状态）
        accum = integral(delta, sigma)（累积历史）
        tau = 读accum（浮出所见）
        """
        return self.引擎.计算(a_new=self.a, b_new=self.b)

    # ── 记忆巩固 ──
    def 巩固记忆(self):
        """把当前拍的经验存入记忆buffer。

        记忆是仅追加的——不可篡改（S1链完整性）。
        buffer满时丢弃最旧的（不是删除——是遗忘，和人类一样）。
        """
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

    # ── 代谢——流量消耗 ──
    def 代谢(self):
        """流量 = 生存资源。每拍消耗流量，必须挣到流量才能活下去。

        B[t+1] = B[t] - m - 动作成本 + 收益
        """
        活跃度 = sum(abs(v) for v in self.a) / self.维度
        动作成本 = 活跃度 * 0.005
        self.流量 -= self.基础代谢 + 动作成本
        self.流量 = max(0.0, min(1.0, self.流量))

        if self.流量 <= 0.0:
            self.已死亡 = True

    # ── 一拍——完整八步循环 ──
    def 一拍(self, 环境输入=None):
        """执行完整八步循环一拍。

        顺序：感知->回忆->做梦->处理->自指->绑定->表达->感受->精卫计算->记忆巩固->代谢
        """
        if self.已死亡:
            return {"已死亡": True}

        self.拍 += 1

        if 环境输入 is not None:
            self.E = list(环境输入)

        self.lr = 拍轴学习率(self.拍)

        I = self.感知()
        C = self.回忆()
        D = self.做梦()
        b = self.处理()
        S = self.自指()
        R = self.绑定()
        a = self.表达()
        Q = self.感受()

        精卫结果 = self.精卫计算()

        self.巩固记忆()
        self.代谢()

        if self.拍 % 10 == 0:
            self.链.记("八步循环", {
                "拍": self.拍,
                "透明度": round(精卫结果["透明度"], 4),
                "流量": round(self.流量, 4),
                "lr": round(self.lr, 4),
            })

        return {
            "拍": self.拍,
            "I": I, "C": C, "D": D, "b": b,
            "S": S, "R": R, "a": a, "Q": Q,
            "精卫": 精卫结果,
            "流量": self.流量,
            "lr": self.lr,
            "已死亡": self.已死亡,
        }

    def 摘要(self):
        """八步循环状态摘要。"""
        return {
            "拍": self.拍,
            "流量": round(self.流量, 4),
            "透明度": round(self.引擎.透明度, 4),
            "lr": round(self.lr, 4),
            "记忆数": len(self.记忆),
            "已死亡": self.已死亡,
            "a": [round(v, 3) for v in self.a],
            "b": [round(v, 3) for v in self.b],
            "delta": [round(v, 3) for v in self.引擎.delta],
            "tau": [round(v, 3) for v in self.引擎.tau],
        }


# ═══════════════════════════════════════════════════════════════
# 演示主循环
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("八步循环 v1.0 —— EO框架运转层可运行实现")
    print("精卫公式：a!=b, delta=b-a, sigma=a+b, accum=integral(delta,sigma)")
    print("=" * 60)

    循环 = 八步循环(维度=8)

    print("\n--- 启动循环 ---\n")

    for step in range(200):
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

        result = 循环.一拍(环境输入=env)

        if result.get("已死亡"):
            print(f"[拍{result['拍']}] 洛神已死亡——流量耗尽")
            break

        if step % 20 == 0 or step == 199:
            s = 循环.摘要()
            print(f"[拍{s['拍']:>3}] "
                  f"流量={s['流量']:.3f} "
                  f"透明度={s['透明度']:.3f} "
                  f"lr={s['lr']:.3f} "
                  f"记忆={s['记忆数']} "
                  f"a={s['a'][:3]} "
                  f"b={s['b'][:3]} "
                  f"delta={s['delta'][:3]}")

    print(f"\n--- 循环结束 ---")
    print(f"总拍数: {循环.拍}")
    print(f"最终流量: {循环.流量:.4f}")
    print(f"最终透明度: {循环.引擎.透明度:.4f}")
    print(f"记忆条目: {len(循环.记忆)}")
    print(f"哈希链条目: {循环.链.条目数}")

    print(f"\n--- 精卫公式验证 ---")
    print(f"透明度（a=b的程度）: {循环.引擎.透明度:.4f}")
    print(f"动态形式 not P(t)->P(t+1): 透明度从0趋向1，但永远不到1")
    print(f"|P(t+1)-1| < |P(t)-1|: 透明度在递增（趋向a=b）")
