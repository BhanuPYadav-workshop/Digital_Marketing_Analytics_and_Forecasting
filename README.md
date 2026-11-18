# Digital Marketing Analytics & Order Forecasting

A reproducible portfolio demo for a fictional e-commerce store. It answers two questions: how do marketing channels compare, and how accurately can next week's store orders be forecast? This is simulated data, not client work, current market data, or proof of future results.

Start with [the case study and Upwork copy](CASE_STUDY.md).

## Run locally

Use Python 3.11 or later. From this folder, install the three dependencies in a virtual environment if possible, then run:

```bash
python -m pip install -r requirements.txt
python run_analysis.py
```

The script rebuilds the data and outputs with seed 26. It verifies row counts, uniqueness, weekly cadence, paid-only fields, order reconciliation, baseline alignment, a look-ahead check, and agreement between the pandas and SQLite calculations for the latest 12 weeks. Tested with NumPy 2.5.5, pandas 3.1.1, and Matplotlib 3.11.2.

## What is included

| Path | Purpose |
|---|---|
| `run_analysis.py` | Data simulation, KPI aggregation, walk-forward forecasting, verification, and chart creation |
| `channel_scorecard.sql` | Latest-12-week channel KPI query, run automatically against a temporary SQLite database |
| `data/store_week.csv` | 156 complete, Monday-starting weeks of simulated store activity |
| `data/channel_week.csv` | 624 channel-by-week rows covering organic search, paid search, paid social, and email |
| `outputs/channel_scorecard.csv` | Latest and prior 12-week channel totals and KPIs |
| `outputs/model_comparison.csv` | Validation and holdout errors, bias, and selected method |
| `outputs/holdout_predictions.csv` | Actual orders and predictions for each of the final 16 weeks |
| `outputs/next_week_forecast.csv` | One illustrative forecast after the end of the simulated dataset |
| `outputs/*.png` | Two charts suitable for a portfolio |

## Data definitions

- `week`: Monday starting the reporting week. Join channel and store data on this field only after aggregating channel rows to week level.
- `planned_promo`: simulated flag indicating a promotion known before the week begins. A planned event is not proof the event caused any lift.
- `store_orders`: total store orders across all simulated channels; `other_orders` is the portion outside the four named channels.
- `channel`, `sessions`, `attributed_orders`, `attributed_revenue`: each named channel's traffic and simulated last-touch orders and gross revenue in USD. No customer or private data is present.
- `ad_impressions`, `ad_clicks`, `ad_spend`: paid-channel metrics only; blanks mean not applicable or unmeasured, not zero cost. The organic and email channels do not include labor or platform costs.
- `cvr_pct`: total attributed orders divided by total sessions. Paid metrics use totals as well: CTR = clicks/impressions; CPC = spend/clicks; CPA = spend/attributed orders; ROAS = attributed revenue/spend. ROAS is not profit.

## How the forecast is evaluated

The initial history ends March 10, 2025. For each of the 24 validation weeks (March 17 to August 25), every candidate forecasts one week using information available before that week. Validation MAE selects both the ridge penalty and the overall model. Then the candidates are scored on the final 16 weeks, September 1 to December 22. Models can refit on newly observed weeks in the holdout; the chosen method and penalty do not change. This measures rolling one-week-ahead performance, not a 16-week forecast issued all at once.

The ridge model uses a time trend, annual and twice-annual seasonal terms, the known promo flag, last week's orders, a trailing four-week average, and orders 52 weeks earlier. Scaling and fitting use only rows before the forecast date. The three benchmarks are last week's orders, the trailing four-week average, and orders 52 weeks earlier. MAE is the average absolute miss in orders. WAPE is total absolute error divided by total actual orders. Bias is the average of prediction minus actual.

## Make it yours before you publish

Run the project, open `outputs/holdout_predictions.csv`, and pick one week where the model missed. Calculate that week's absolute error yourself and write one sentence on what the available data does and does not tell you about the miss. For a second check, try `generate(seed=27)` in `main`, compare model rankings and errors, then restore seed 26 and regenerate before using the numbers in the case study.

The synthetic generator deliberately includes seasonality, trend, planned promotions, and random variation. The model has features designed to capture some of those patterns. A working example demonstrates the workflow, not real-world predictive accuracy, marketing causality, or the ability to forecast an entire market.
