"""
调仓分析 —— Skill 脚本
读取用户 portfolio.json，运行优化算法，输出调仓建议
"""

import json
import os
import sys
from pathlib import Path

PORTFOLIO = Path.home() / ".zcode" / "portfolio.json"

# 确保能找到 etf_diagnose 包
PROJECT = Path(os.environ.get("ZCODE_PROJECT", Path.home() / "ZCodeProject"))
sys.path.insert(0, str(PROJECT))

# 模拟历史收益数据（API 不可用时的 fallback）
# 真实部署时替换为 API 拉取的实时数据
FALLBACK_RETURNS = {
    "512480": {
        "ret_1y": 1.632,    # +163.2%
        "vol_1y": 0.454,     # 45.4%
    },
    "513650": {
        "ret_1y": 0.148,
        "vol_1y": 0.133,
    },
    "511010": {
        "ret_1y": 0.019,
        "vol_1y": 0.009,
    },
    "518850": {
        "ret_1y": 0.166,
        "vol_1y": 0.254,
    },
    "511380": {
        "ret_1y": 0.103,
        "vol_1y": 0.116,
    },
}


def generate_fake_daily(annual_ret: float, annual_vol: float, days: int = 252) -> list[float]:
    """根据年化收益率和波动率生成模拟日收益序列。"""
    import random
    random.seed(42)
    daily_ret = annual_ret / days
    daily_vol = annual_vol / (days ** 0.5)
    return [random.gauss(daily_ret, daily_vol) for _ in range(days)]


def main():
    if not PORTFOLIO.exists():
        print("📭 未找到持仓数据。先用 `/portfolio add` 添加持仓。")
        return

    data = json.loads(PORTFOLIO.read_text())
    holdings = data.get("holdings", {})
    cash = data.get("cash", 0)

    if not holdings:
        print("📭 持仓为空。")
        return

    # 构建输入
    current = {}
    returns = {}
    codes = []

    for code, h in holdings.items():
        current[code] = h["shares"] * h["cost"]
        codes.append(code)
        fb = FALLBACK_RETURNS.get(code, {"ret_1y": 0.05, "vol_1y": 0.20})
        returns[code] = generate_fake_daily(fb["ret_1y"], fb["vol_1y"])

    # 如果有候选资产（不在持仓中），也加入
    candidates = []
    for c in ["511010", "518850", "511380"]:
        if c not in holdings and c in FALLBACK_RETURNS:
            candidates.append(c)
            fb = FALLBACK_RETURNS[c]
            returns[c] = generate_fake_daily(fb["ret_1y"], fb["vol_1y"])
            current[c] = 0  # 当前没有持仓

    all_codes = codes + candidates

    from etf_diagnose.rebalance import run_rebalance, format_report

    report = run_rebalance(current, returns, cash, codes=all_codes)
    print(format_report(report))


if __name__ == "__main__":
    main()
