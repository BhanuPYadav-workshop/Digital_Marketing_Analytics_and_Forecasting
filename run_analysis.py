"""Rebuild the synthetic dataset, backtest, tables, and charts."""
from pathlib import Path
import sqlite3

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"
CHANNELS = {
    "Organic Search": (0.15, 0.040, 0.025, None, None),
    "Paid Search": (0.20, 0.045, 0.032, 0.026, 1.35),
    "Paid Social": (0.24, 0.035, 0.018, 0.015, 0.86),
    "Email": (0.12, 0.045, 0.044, None, None),
}
LABELS = ["Last week", "Four-week average", "Same week last year", "Calendar + lag ridge"]
VALID_START, TEST_START, N_WEEKS = 116, 140, 156


def generate(seed=26):
    """Synthetic last-touch channels, with no competitor or customer-level data."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2023-01-02", periods=N_WEEKS + 1, freq="W-MON")
    phase = np.arange(len(dates)) % 52
    promo = np.isin(phase, [7, 21, 36, 46, 47, 49, 50]).astype(int)
    shock = rng.normal(0, 0.055, N_WEEKS)
    for i in range(1, N_WEEKS):
        shock[i] += 0.40 * shock[i - 1]
    shop, channels = [], []
    for i, date in enumerate(dates[:-1]):
        signal = (1 + 0.004 * i + 0.18 * np.sin(2 * np.pi * (i - 38) / 52)
                  + 0.07 * np.cos(4 * np.pi * i / 52) + shock[i])
        total = 0
        for name, (share, noise, conversion, ctr, cpc) in CHANNELS.items():
            traffic = max(100, round(30000 * share * signal *
                          (1 + 0.17 * promo[i] + rng.normal(0, noise))))
            rate = conversion * (1 + 0.16 * promo[i])
            if name == "Paid Social" and i >= 132:
                rate *= 0.79  # Simulated fatigue; the analysis does not use this flag.
            orders = rng.binomial(traffic, rate)
            total += orders
            ad_clicks = round(traffic / 0.9) if cpc else np.nan
            ad_impressions = round(ad_clicks / (ctr * rng.uniform(0.90, 1.10))) if cpc else np.nan
            spend = round(ad_clicks * cpc * rng.uniform(0.88, 1.12), 2) if cpc else np.nan
            revenue = round(orders * max(20, rng.normal(76 - 6 * promo[i], 5)), 2)
            channels.append((date, name, traffic, orders, revenue, ad_impressions, ad_clicks, spend))
        other_orders = rng.poisson(max(20, 116 * signal * (1 + 0.35 * promo[i])))
        shop.append((date, promo[i], total + other_orders, other_orders))
    weekly = pd.DataFrame(shop, columns=["week", "planned_promo", "store_orders", "other_orders"])
    channel = pd.DataFrame(channels, columns=[
        "week", "channel", "sessions", "attributed_orders", "attributed_revenue",
        "ad_impressions", "ad_clicks", "ad_spend",
    ])
    return weekly, channel, (dates[-1], int(promo[-1]))


def channel_summary(channel):
    result = []
    weeks = sorted(channel["week"].unique())
    for period, selected_weeks in [("prior_12", weeks[-24:-12]), ("latest_12", weeks[-12:])]:
        subset = channel[channel["week"].isin(selected_weeks)]
        grouped = subset.groupby("channel").agg(
            sessions=("sessions", "sum"), orders=("attributed_orders", "sum"),
            revenue=("attributed_revenue", "sum"),
            spend=("ad_spend", lambda x: x.sum(min_count=1)),
            clicks=("ad_clicks", lambda x: x.sum(min_count=1)),
            impressions=("ad_impressions", lambda x: x.sum(min_count=1)),
        )
        grouped["cvr_pct"] = 100 * grouped.orders / grouped.sessions
        grouped["ad_ctr_pct"] = 100 * grouped.clicks / grouped.impressions
        grouped["cpc"] = grouped.spend / grouped.clicks
        grouped["cpa"] = grouped.spend / grouped.orders.replace(0, np.nan)
        grouped["roas"] = grouped.revenue / grouped.spend
        result.append(grouped.assign(period=period).reset_index())
    return pd.concat(result, ignore_index=True)


def design(y, promos, t):
    """All noncalendar inputs predate the target week t."""
    angle = 2 * np.pi * t / 52
    return [t / 52, np.sin(angle), np.cos(angle), np.sin(2 * angle), np.cos(2 * angle),
            promos[t], y[t - 1], np.mean(y[t - 4:t]), y[t - 52]]


def predict_ridge(y, promos, t, alpha):
    train = np.array([design(y, promos, j) for j in range(52, t)])
    mean, std = train.mean(axis=0), train.std(axis=0)
    std[std == 0] = 1
    x = (train - mean) / std
    target = y[52:t]
    beta = np.linalg.solve(x.T @ x + alpha * np.eye(x.shape[1]), x.T @ (target - target.mean()))
    x_next = (np.asarray(design(y, promos, t)) - mean) / std
    return max(0.0, float(target.mean() + x_next @ beta))


def candidates(y, promos, t, alpha):
    return [y[t - 1], np.mean(y[t - 4:t]), y[t - 52], predict_ridge(y, promos, t, alpha)]


def backtest(weekly, next_week):
    y = weekly.store_orders.to_numpy()
    promos = np.append(weekly.planned_promo.to_numpy(), next_week[1])
    grid = [0.1, 1, 5, 20, 50]
    validation = range(VALID_START, TEST_START)
    alpha = min(grid, key=lambda a: np.mean([abs(y[t] - predict_ridge(y, promos, t, a)) for t in validation]))
    val_errors = np.mean([abs(y[t] - np.asarray(candidates(y, promos, t, alpha))) for t in validation], axis=0)
    selected = LABELS[int(np.argmin(val_errors))]
    test = pd.DataFrame(
        [(weekly.week.iloc[t], y[t], *candidates(y, promos, t, alpha))
         for t in range(TEST_START, len(y))], columns=["week", "actual", *LABELS],
    )
    scores = []
    for j, label in enumerate(LABELS):
        err = test[label] - test.actual
        scores.append((label, val_errors[j], err.abs().mean(), 100 * err.abs().sum() / test.actual.sum(),
                       err.mean(), label == selected))
    metrics = pd.DataFrame(scores, columns=[
        "model", "validation_mae", "holdout_mae", "holdout_wape_pct", "holdout_bias", "selected_on_validation",
    ])
    next_value = candidates(y, promos, len(y), alpha)[LABELS.index(selected)]
    return test, metrics, (next_week[0], next_week[1], selected, alpha, next_value)


def verify(weekly, channel, totals, test, metrics):
    assert len(weekly) == 156 and len(channel) == 624
    assert weekly.week.is_unique and not channel.duplicated(["week", "channel"]).any()
    assert (weekly.week.diff().dropna() == pd.Timedelta(weeks=1)).all()
    assert (weekly.store_orders > 0).all()
    assert channel.groupby("week").size().eq(4).all()
    assert (channel.attributed_orders.between(0, channel.sessions)).all()
    assert (channel[["sessions", "attributed_orders", "attributed_revenue"]] >= 0).all().all()
    ad_fields = ["ad_spend", "ad_clicks", "ad_impressions"]
    paid = channel.channel.str.startswith("Paid")
    assert channel.loc[paid, ad_fields].gt(0).all().all()
    assert channel.loc[~paid, ad_fields].isna().all().all()
    assert (channel.loc[paid, "ad_clicks"] <= channel.loc[paid, "ad_impressions"]).all()
    assert np.array_equal(
        weekly.store_orders.to_numpy(),
        weekly.other_orders.to_numpy() + channel.groupby("week").attributed_orders.sum().to_numpy(),
    )
    assert len(test) == N_WEEKS - TEST_START and metrics.selected_on_validation.sum() == 1
    assert np.array_equal(test["Last week"], weekly.store_orders.iloc[TEST_START - 1:-1])
    assert np.array_equal(test["Same week last year"], weekly.store_orders.iloc[TEST_START - 52:N_WEEKS - 52])
    y = weekly.store_orders.to_numpy().copy()
    promos = weekly.planned_promo.to_numpy()
    expected = candidates(y, promos, TEST_START, 5)
    y[TEST_START:] = 1_000_000
    assert np.allclose(expected, candidates(y, promos, TEST_START, 5)), "Lookahead detected"
    with sqlite3.connect(":memory:") as conn:
        channel.assign(week=channel.week.dt.strftime("%Y-%m-%d")).to_sql("channel_week", conn, index=False)
        sql = pd.read_sql_query((ROOT / "channel_scorecard.sql").read_text(), conn).set_index("channel")
    latest = totals[totals.period == "latest_12"].set_index("channel").loc[sql.index]
    for col in ["sessions", "orders", "cvr_pct", "cpa", "roas"]:
        assert np.allclose(sql[col].astype(float), latest[col], equal_nan=True), f"SQL mismatch: {col}"


def plot(test, totals, forecast):
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "text.color": "#122837", "axes.labelcolor": "#122837",
        "axes.edgecolor": "#b6c4cc", "axes.spines.top": False, "axes.spines.right": False,
        "axes.spines.left": False, "xtick.color": "#344e5f", "ytick.color": "#344e5f",
    })
    fig, ax = plt.subplots(figsize=(10, 4.6), layout="constrained")
    ax.set_title("Can last week’s sales predict next week?", loc="left", fontweight="bold", fontsize=16)
    ax.plot(test.week, test.actual, "o-", color="#16333e", label="Actual orders", lw=2, ms=4)
    if forecast[2] != LABELS[0]:
        ax.plot(test.week, test[LABELS[0]], "--", color="#9a601f", label="Last-week baseline", lw=1.4)
    ax.plot(test.week, test[forecast[2]], "o-", color="#027a72", label=forecast[2], lw=2, ms=3)
    ax.set_ylabel("Weekly store orders")
    ax.set_xlabel("Synthetic data | Final 16 weeks | Each forecast uses only earlier sales")
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.grid(axis="y", alpha=0.2)
    ax.legend(frameon=False, ncol=3, fontsize=9)
    fig.savefig(OUT / "weekly_order_forecast.png", dpi=160, facecolor="white")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.7), layout="constrained")
    fig.suptitle("Channel performance: efficiency and volume tell different stories", x=0.02,
                 ha="left", fontweight="bold", fontsize=15)
    latest = totals[totals.period == "latest_12"].sort_values("orders")
    prior = totals[totals.period == "prior_12"].set_index("channel")
    bars = axes[0].barh(latest.channel, latest.orders, color="#027a72")
    axes[0].bar_label(bars, labels=[f"{n:,}" for n in latest.orders], padding=4, fontsize=9)
    axes[0].set_xlim(0, latest.orders.max() * 1.25)
    axes[0].set(title="Attributed orders | Latest 12 weeks", xlabel="Orders")
    paid = latest[latest.spend.notna()]
    x = np.arange(len(paid))
    for vals, shift, color, label in [
        (prior.loc[paid.channel, "cpa"], -0.18, "#a6bfce", "Prior 12 weeks"),
        (paid.cpa, 0.18, "#7753a0", "Latest 12 weeks"),
    ]:
        bars = axes[1].bar(x + shift, vals, width=0.36, color=color, label=label)
        axes[1].bar_label(bars, labels=[f"${n:.0f}" for n in vals], padding=3, fontsize=9)
    axes[1].set_xticks(x, paid.channel)
    axes[1].set(ylim=(0, max(paid.cpa.max(), prior.cpa.max()) * 1.30),
                ylabel="Ad spend per attributed order (USD)", title="Paid acquisition cost")
    axes[1].legend(frameon=False, loc="upper left", fontsize=8)
    for ax in axes:
        ax.tick_params(length=0)
    fig.savefig(OUT / "channel_performance.png", dpi=160, facecolor="white")
    plt.close(fig)


def main():
    DATA.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    weekly, channel, next_week = generate()
    summary = channel_summary(channel)
    test, metrics, forecast = backtest(weekly, next_week)
    verify(weekly, channel, summary, test, metrics)
    for df, path in [
        (weekly, DATA / "store_week.csv"), (channel, DATA / "channel_week.csv"),
        (summary, OUT / "channel_scorecard.csv"), (test, OUT / "holdout_predictions.csv"),
        (metrics, OUT / "model_comparison.csv"),
        (pd.DataFrame([forecast], columns=["week", "planned_promo", "model", "ridge_alpha",
                                          "predicted_orders"]), OUT / "next_week_forecast.csv"),
    ]:
        df.to_csv(path, index=False, float_format="%.6f")
    plot(test, summary, forecast)
    print(metrics.round(2).to_string(index=False))
    print(summary[["period", "channel", "orders", "cvr_pct", "cpa", "roas"]].round(2).to_string(index=False))
    print(f"Next week: {forecast}; verification passed.")


if __name__ == "__main__":
    main()
