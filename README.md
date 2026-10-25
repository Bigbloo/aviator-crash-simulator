# Aviator Crash Game Simulator

Reproducible Monte Carlo simulation of the **Aviator** crash game under its published **97% RTP** model.
It powers the [Aviator Simulation Study](https://aviator-tips.com/research/aviator-simulation-study) and the
[Aviator odds chart](https://aviator-tips.com/blog/aviator-strategy-chart) on AviatorTips.

> ⚠️ This is **not** Spribe's source code and it **cannot predict real rounds**. Real Aviator rounds are
> provably fair: each crash point depends on a server seed and the seeds of the first three bettors,
> which don't exist until the round starts. Any app claiming to predict Aviator is a scam.

## Key results (seed 2026, 10,000 sessions × 1,000 rounds per strategy)

| Auto cash-out | Rounds won | Sessions in profit | Sessions broke | Avg end balance ($1,000 start, $10 bets) |
|---|---|---|---|---|
| 1.2x | 80.8% | 2.0% | 0.0% | $700 |
| 1.5x | 64.7% | 9.7% | 0.2% | $699 |
| 2x | 48.5% | 16.5% | 2.1% | $705 |
| 3x | 32.3% | 23.8% | 9.3% | $701 |
| 5x | 19.4% | 30.4% | 21.1% | $726 |
| 10x | 9.7% | 33.6% | 38.9% | $747 |

- Martingale (double after each loss, 2x): the next bet exceeded the balance in **96.3%** of sessions.
- Half of all rounds end below **1.93x**; about **4%** crash instantly at 1.00x.

Full write-up, charts and data: <https://aviator-tips.com/research/aviator-simulation-study>

## The model

The plane reaches a multiplier `x` with probability `0.97 / x`. Crash points are rounded down to two
decimals and values below 1.00 are an instant crash at 1.00x:

```python
u = rng.random()
crash = max(1.0, floor(0.97 / (1 - u) * 100) / 100)
```

## Run it

```bash
pip install -r requirements.txt
python simulate.py   # writes results/results.json and CSV files
python charts.py     # writes the PNG charts and the A4 odds-chart PDF to results/
```

## Try it in the browser

No install needed: the [Aviator calculator](https://aviator-tips.com/tools/aviator-calculator) runs the same
model for your own bankroll, bet and cash-out target.

## License

- Code: MIT
- Data, charts and text: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — credit
  “AviatorTips” with a link to <https://aviator-tips.com/research/aviator-simulation-study>.

Gambling involves risk. 18+. Only play where it is legal, and only with money you can afford to lose.
