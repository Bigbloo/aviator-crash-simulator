"""
Aviator crash-game simulator — reproduces the figures published on
https://aviator-tips.com/research/aviator-simulation-study

Model: the plane reaches a multiplier x with probability 0.97 / x (97% RTP),
crash points are rounded down to 2 decimals, anything below 1.00x is an instant
crash at 1.00x. This is the standard crash-game distribution; it is NOT Spribe's
source code and cannot predict real rounds (which are provably fair).

Usage:  python simulate.py            (writes results/*.json and *.csv)
"""
import csv
import json
import numpy as np

RTP = 0.97
SEED = 2026
rng = np.random.default_rng(SEED)


def crash_points(shape):
    u = rng.random(shape)
    m = np.floor(RTP / (1.0 - u) * 100) / 100
    return np.maximum(1.0, m)


def flat_sessions(target, sessions=10_000, rounds=1_000, bankroll=1_000.0, bet=10.0):
    """Flat bet with auto cash-out at `target`. A session stops if the balance can't cover a bet."""
    crashes = crash_points((sessions, rounds))
    wins = crashes >= target
    pnl = np.where(wins, bet * (target - 1), -bet)
    balance = bankroll + np.cumsum(pnl, axis=1)
    # balance before each round: bankroll, then balance[:, :-1]
    before = np.concatenate([np.full((sessions, 1), bankroll), balance[:, :-1]], axis=1)
    broke = before < bet
    any_broke = broke.any(axis=1)
    first = np.where(any_broke, broke.argmax(axis=1), rounds)
    end = np.where(any_broke, before[np.arange(sessions), np.minimum(first, rounds - 1)], balance[:, -1])
    # longest losing streak per session (on rounds actually played)
    longest = np.zeros(sessions, dtype=int)
    run = np.zeros(sessions, dtype=int)
    for r in range(rounds):
        active = r < first
        lost = (~wins[:, r]) & active
        run = np.where(lost, run + 1, np.where(active, 0, run))
        longest = np.maximum(longest, run)
    return {
        "target": target,
        "win_rate_pct": round(float(wins.mean() * 100), 2),
        "theoretical_win_rate_pct": round(RTP / target * 100, 2),
        "mean_end_balance": round(float(end.mean()), 1),
        "median_end_balance": round(float(np.median(end)), 1),
        "p10_end_balance": round(float(np.percentile(end, 10)), 1),
        "p90_end_balance": round(float(np.percentile(end, 90)), 1),
        "sessions_in_profit_pct": round(float((end > bankroll).mean() * 100), 1),
        "sessions_broke_pct": round(float(any_broke.mean() * 100), 1),
        "median_longest_losing_streak": int(np.median(longest)),
        "p90_longest_losing_streak": int(np.percentile(longest, 90)),
    }


def progression_sessions(kind, sessions=10_000, rounds=1_000, bankroll=1_000.0, base=10.0, target=2.0):
    """'martingale' doubles the bet after a loss, 'plus50' raises it by 50%; both reset after a win."""
    factor = 2.0 if kind == "martingale" else 1.5
    balance = np.full(sessions, bankroll)
    bet = np.full(sessions, base)
    alive = np.ones(sessions, dtype=bool)
    for _ in range(rounds):
        can = alive & (balance >= bet)
        alive &= can
        win = crash_points(sessions) >= target
        delta = np.where(win, bet * (target - 1), -bet)
        balance = np.where(alive, balance + delta, balance)
        bet = np.where(alive, np.where(win, base, bet * factor), bet)
    return {
        "strategy": kind,
        "target": target,
        "sessions_broke_pct": round(float((~alive).mean() * 100), 1),
        "sessions_in_profit_pct": round(float((balance > bankroll).mean() * 100), 1),
        "mean_end_balance": round(float(balance.mean()), 1),
    }


def limits_session(sessions=10_000, rounds=200, bankroll=1_000.0, bet=10.0, target=2.0, stop_win=0.30, stop_loss=0.25):
    balance = np.full(sessions, bankroll)
    playing = np.ones(sessions, dtype=bool)
    for _ in range(rounds):
        playing &= (balance < bankroll * (1 + stop_win)) & (balance > bankroll * (1 - stop_loss)) & (balance >= bet)
        win = crash_points(sessions) >= target
        balance = np.where(playing, balance + np.where(win, bet * (target - 1), -bet), balance)
    return {
        "setup": f"{target}x, ${bet:.0f} bets, stop at +{int(stop_win*100)}% / -{int(stop_loss*100)}%, max {rounds} rounds",
        "hit_stop_win_pct": round(float((balance >= bankroll * (1 + stop_win)).mean() * 100), 1),
        "hit_stop_loss_pct": round(float((balance <= bankroll * (1 - stop_loss)).mean() * 100), 1),
        "sessions_in_profit_pct": round(float((balance > bankroll).mean() * 100), 1),
        "mean_end_balance": round(float(balance.mean()), 1),
    }


def distribution(n=1_000_000):
    m = crash_points(n)
    bins = [(1.0, 1.01, "1.00x (instant crash)"), (1.01, 2, "1.01x-1.99x"), (2, 5, "2.00x-4.99x"),
            (5, 10, "5.00x-9.99x"), (10, 100, "10.00x-99.99x"), (100, np.inf, "100x and above")]
    rows = [{"range": label, "share_pct": round(float(((m >= lo) & (m < hi)).mean() * 100), 2)} for lo, hi, label in bins]
    reach = [{"multiplier": x, "observed_pct": round(float((m >= x).mean() * 100), 3), "theoretical_pct": round(RTP / x * 100, 3)}
             for x in [1.1, 1.2, 1.5, 2, 3, 5, 10, 20, 50, 100]]
    return {"rounds": n, "median_crash": float(np.median(m)), "bins": rows, "reach": reach,
            "observed_rtp_at_2x_pct": round(float((m >= 2).mean() * 2 * 100), 2)}


if __name__ == "__main__":
    out = {
        "model": {"rtp": RTP, "seed": SEED},
        "distribution": distribution(),
        "flat": [flat_sessions(t) for t in [1.2, 1.5, 2.0, 3.0, 5.0, 10.0]],
        "progressions": [progression_sessions("plus50"), progression_sessions("martingale")],
        "limits": limits_session(),
    }
    json.dump(out, open("results/results.json", "w"), indent=2)
    with open("results/flat_sessions.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out["flat"][0].keys()))
        w.writeheader(); w.writerows(out["flat"])
    with open("results/crash_distribution.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["range", "share_pct"])
        w.writeheader(); w.writerows(out["distribution"]["bins"])
    print(json.dumps(out, indent=2))
