"""Builds the shareable charts (PNG) and the printable odds chart (PDF) from results/results.json."""
import json, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

out_dir = sys.argv[1] if len(sys.argv) > 1 else "results"
d = json.load(open("results/results.json"))
BG, FG, MUTED, RED, AMBER, GRID = "#09090b", "#f4f4f5", "#a1a1aa", "#ef4444", "#f59e0b", "#27272a"
CREDIT = "Source: AviatorTips simulation study — aviator-tips.com/research/aviator-simulation-study"

def style(ax, fig):
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=11)
    ax.yaxis.grid(True, color=GRID); ax.set_axisbelow(True)

# 1. Session outcomes by cash-out target
flat = d["flat"]
labels = [f'{r["target"]:g}x' for r in flat]
profit = [r["sessions_in_profit_pct"] for r in flat]
broke = [r["sessions_broke_pct"] for r in flat]
fig, ax = plt.subplots(figsize=(12, 6.75), dpi=150); style(ax, fig)
x = range(len(labels)); w = 0.38
b1 = ax.bar([i - w/2 for i in x], profit, w, color=AMBER, label="Sessions ending in profit")
b2 = ax.bar([i + w/2 for i in x], broke, w, color=RED, label="Sessions that went broke")
for bars in (b1, b2):
    for b in bars:
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.8, f"{b.get_height():.1f}%", ha="center", color=FG, fontsize=10)
ax.set_xticks(list(x)); ax.set_xticklabels(labels)
ax.set_xlabel("Auto cash-out target", color=MUTED, fontsize=12)
ax.set_ylabel("% of 10,000 sessions", color=MUTED, fontsize=12)
ax.legend(frameon=False, labelcolor=FG, fontsize=11, loc="upper left")
fig.suptitle(r"Aviator: what happens over 1,000 rounds (\$10 bets, \$1,000 bankroll)", color=FG, fontsize=17, fontweight="bold", x=0.06, ha="left")
ax.set_title("Every target loses ~3% of the money wagered on average — higher targets just swing harder", color=MUTED, fontsize=12, loc="left")
fig.text(0.06, 0.02, CREDIT, color=MUTED, fontsize=9)
fig.subplots_adjust(top=0.84, bottom=0.14, left=0.08, right=0.97)
fig.savefig(f"{out_dir}/aviator-session-outcomes.png", facecolor=BG); plt.close(fig)

# 2. Crash point distribution
bins = d["distribution"]["bins"]
fig, ax = plt.subplots(figsize=(12, 6.75), dpi=150); style(ax, fig)
names = [b["range"].replace(" (instant crash)", "\n(instant crash)") for b in bins]
vals = [b["share_pct"] for b in bins]
bars = ax.bar(names, vals, color=[RED] + [AMBER] * (len(vals) - 1))
for b in bars:
    ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.6, f"{b.get_height():.2f}%", ha="center", color=FG, fontsize=11)
ax.set_ylabel("% of 1,000,000 rounds", color=MUTED, fontsize=12)
fig.suptitle("Where the Aviator plane flies away", color=FG, fontsize=17, fontweight="bold", x=0.06, ha="left")
ax.set_title(f'Half of all rounds end below {d["distribution"]["median_crash"]:.2f}x · about 4 in 100 crash instantly at 1.00x', color=MUTED, fontsize=12, loc="left")
fig.text(0.06, 0.02, CREDIT, color=MUTED, fontsize=9)
fig.subplots_adjust(top=0.84, bottom=0.16, left=0.08, right=0.97)
fig.savefig(f"{out_dir}/aviator-crash-distribution.png", facecolor=BG); plt.close(fig)

# 3. Odds chart (PNG + PDF)
targets = [1.1, 1.2, 1.3, 1.5, 1.8, 2, 2.5, 3, 5, 10, 20, 50, 100]
rows = []
for t in targets:
    p = 0.97 / t
    lose5 = (1 - p) ** 5
    rows.append([f"{t:.2f}x", f"{p*100:.1f}%", f"1 in {1/p:.1f}" if 1/p < 10 else f"1 in {round(1/p)}",
                 "< 0.01%" if lose5 < 0.0001 else (f"{lose5*100:.2f}%" if lose5 < 0.01 else f"{lose5*100:.1f}%")])

def odds_figure():
    fig = plt.figure(figsize=(8.27, 11.69), dpi=150)  # A4 portrait
    fig.patch.set_facecolor("white")
    fig.text(0.07, 0.94, "Aviator Odds Chart", fontsize=26, fontweight="bold", color="#111")
    fig.text(0.07, 0.915, "Real chance of reaching each cash-out target (97% RTP model)", fontsize=12, color="#555")
    ax = fig.add_axes([0.07, 0.30, 0.86, 0.58]); ax.axis("off")
    tbl = ax.table(cellText=rows, colLabels=["Cash out at", "Chance to win", "Wins about…", "5 losses in a row"],
                   loc="upper center", cellLoc="center")
    tbl.auto_set_font_size(False); tbl.set_fontsize(12); tbl.scale(1, 2.1)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor("#ddd")
        if r == 0:
            cell.set_facecolor("#111"); cell.get_text().set_color("white"); cell.get_text().set_fontweight("bold")
        elif r % 2 == 0:
            cell.set_facecolor("#f6f6f6")
    notes = ("• Chance to reach x ≈ 0.97 ÷ x. Verified on 1,000,000 simulated rounds.\n"
             "• Every target returns about 97% over time: no row is a 'winning' strategy.\n"
             "• Use auto cash-out, bet 1–2% of your bankroll, set limits before you start.\n"
             "• No app, signal or 'predictor' can know the next crash point.\n"
             "• Gambling involves risk. 18+. Play only where it is legal.")
    fig.text(0.07, 0.30, notes, fontsize=11, color="#333", linespacing=1.7)
    fig.text(0.07, 0.24, "aviator-tips.com/blog/aviator-strategy-chart", fontsize=11, color="#c0392b", fontweight="bold")
    return fig

f = odds_figure(); f.savefig(f"{out_dir}/aviator-strategy-chart.png"); plt.close(f)
with PdfPages(f"{out_dir}/aviator-strategy-chart.pdf", metadata={"Title": "Aviator Odds Chart — AviatorTips", "Author": "AviatorTips"}) as pdf:
    f = odds_figure(); pdf.savefig(f); plt.close(f)
print("charts written to", out_dir)
