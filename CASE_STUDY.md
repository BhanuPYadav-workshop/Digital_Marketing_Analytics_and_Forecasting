# Digital Marketing Analytics & Order Forecasting

**Portfolio case study | Fictional e-commerce store | Synthetic data**

A store owner wants to know which marketing channels drive attributed orders, where acquisition is expensive, and how many orders to plan for next week. This project combines a channel scorecard with a one-week-ahead order forecast, using 156 weeks of simulated history and 624 channel-week records.

## Channel performance: what to investigate next

| Channel | Attributed orders | Session conversion | Ad spend per attributed order | Attributed ROAS |
|---|---:|---:|---:|---:|
| Paid Search | 4,503 | 3.45% | $42.53 | 1.73× |
| Email | 3,617 | 4.66% | Not measured | Not measured |
| Organic Search | 2,635 | 2.69% | Not measured | Not measured |
| Paid Social | 2,410 | 1.55% | $61.34 | 1.18× |

These are totals and weighted rates for the latest 12 simulated weeks. Paid Search led in attributed orders, Email had the highest session conversion rate, and Paid Social had the higher CPA of the two paid channels. The figures do not show incremental sales or profitability. The audience and role of each channel differ.

- **Paid Social:** Check campaign and landing-page breakdowns for a reason behind the higher CPA. On real data, test one change at a time and use margin and new-customer acquisition cost to make a budget decision.
- **Organic Search:** Review the landing pages and queries that attract useful traffic. On real data, match Search Console landing-page trends with GA4 sessions and conversions at the page level before recommending on-page changes.
- **Email:** Treat its high conversion rate as a reason to examine segments, not a reason to assume email caused those orders. An eligible audience split with a no-send holdout could help estimate incremental impact.

## Forecast: does a model beat simple rules?

| Forecast method | Validation MAE | Final 16-week MAE | Final 16-week WAPE |
|---|---:|---:|---:|
| Last week's orders | 87.42 | 202.44 | 15.96% |
| Four-week average | 62.62 | 176.08 | 13.89% |
| Same week last year | 130.04 | 122.00 | 9.62% |
| Calendar + lag ridge | 54.28 | **60.37** | **4.76%** |

The ridge model was selected on the earlier validation period, not on the final 16 weeks. It reduced MAE by about **51% versus the strongest simple baseline on the holdout**. The next simulated week has an illustrative point forecast of about **1,315 orders** with no planned promotion. That week was not scored because there is no actual value for it in the dataset; no prediction interval is estimated.

The test uses a fresh one-week-ahead forecast each week. The generator contains patterns the model can learn, so these results show that the process works in a simulation. They do not show that it can predict a real market, handle an unexpected shock, or attain the same accuracy for a client.

## What a real-data version would require

Start with a weekly, deduplicated store-order export and an up-to-date promotion calendar. Add GA4 channel and landing-page reports, Search Console query and page reports for SEO diagnosis, and ad-platform spend and delivery exports for paid acquisition. Use the store's order total as the forecast target rather than adding each platform's credited conversions: the same order can be attributed by multiple platforms. Align time zones and attribution rules, check tracking changes, and then repeat the time-ordered baseline test. If the history is too short to support yearly comparisons, drop the 52-week baseline and feature.

## Upwork portfolio entry

**Title:** `Digital Marketing Analytics & Weekly Order Forecasting`

**Role:** `Marketing Data Analysis & Forecasting (Portfolio Demo)`

**Description (use after running and reviewing the project):**

> This portfolio demo analyzes SEO, paid search, paid social, and email across 156 weeks of synthetic e-commerce data. The Python and SQL workflow compares channel conversion and acquisition efficiency and tests a one-week order forecast against three simple baselines. On a 16-week simulated holdout, the selected model averaged about 60 orders of error versus 122 for the strongest baseline. This is a simulation, not client work or a claim of real-market accuracy.

**Skills to consider:** Data Analysis, Python, SQL, Marketing Analytics, Forecasting. Use the closest tags available.

**What to show:** Use `weekly_order_forecast.png` as the first visual and `channel_performance.png` as the second. To explain it on a call: “I separated marketing performance from the sales forecast. I checked the channel KPIs in SQL, chose the forecasting model on earlier data, and tested it on later weeks without using future sales.”
