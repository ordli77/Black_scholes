import yfinance as yf
from datetime import datetime, timezone
import pandas as pd
from scipy.stats import norm
import math
from utils import BS,BS_vega,find_vol
import numpy




def annualize_hist_vol(prices, trading_days=252):
    logret = np.log(prices).diff().dropna()
    return logret.std() * np.sqrt(trading_days)

def yearfrac(start_dt, end_dt):
    # ACT/365
    return (end_dt - start_dt).days / 365.0

# -----------------------------
# Pull data
# -----------------------------
ticker = "AAPL"      # change me
div_yield_guess = 0.0  # optional dividend yield if you don't want to fetch dividends

tk = yf.Ticker(ticker)

# Spot price (last close + today’s live if available)
spot = tk.history(period="5d")["Close"].iloc[-1]
# Historical vol from ~3 months of daily closes
hist = tk.history(period="6mo", interval="1d")["Close"]
hist_vol = float(annualize_hist_vol(hist.tail(60)))  # 60 trading days

# Risk-free proxy: ^IRX (13-week T-bill discount rate, %). Convert to decimal.
irx = yf.Ticker("^IRX").history(period="10d")["Close"].dropna()
if len(irx):
    r = float(irx.iloc[-1]) / 100.0
else:
    r = 0.05  # fallback if ^IRX missing

# Option expiries and choose a near-dated one (~30–60 days out)
expiries = tk.options
if not expiries:
    raise RuntimeError("No options available for this ticker on Yahoo Finance.")

# Pick the first expiry >= 30 days from now, else use the nearest
now_utc = datetime.now(timezone.utc)
def parse_exp(s):  # Yahoo gives 'YYYY-MM-DD'
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    candidates = [(e, parse_exp(e)) for e in expiries]
candidates.sort(key=lambda x: x[1])
chosen = None
for e, dt in candidates:
    if (dt - now_utc).days >= 30:
        chosen = (e, dt); break
if chosen is None:
    chosen = candidates[0]
expiry_str, expiry_dt = chosen

chain = tk.option_chain(expiry_str)
calls = chain.calls.copy()
puts  = chain.puts.copy()

# Compute mid prices and time to expiry
for df, opt_type in [(calls,"call"), (puts,"put")]:
    df["mid"] = (df["bid"].fillna(0) + df["ask"].fillna(0)) / 2.0
    df["type"] = opt_type
    # Time to maturity in years (ACT/365)
    df["T"] = yearfrac(now_utc, expiry_dt)
    df["S"] = spot
    df["r"] = r
    df["q"] = div_yield_guess

# Combine and keep a clean subset around ATM
df = pd.concat([calls, puts], ignore_index=True)
# Focus on strikes within +/- 20% of spot for a tidy test set
df = df[(df["strike"] > 0.8*spot) & (df["strike"] < 1.2*spot)].copy()

# Theoretical BS price using historical vol as sigma guess
df["bs_price_histvol"] = df.apply(
    lambda row: bs_price(row["S"], row["strike"], row["T"], row["r"], hist_vol, row["q"], row["type"]),
    axis=1
)

# Implied vol from market mid
df["implied_vol"] = df.apply(
    lambda row: implied_vol_from_price(
        mkt_price=float(row["mid"]) if not pd.isna(row["mid"]) else np.nan,
        S=float(row["S"]),
        K=float(row["strike"]),
        T=float(row["T"]),
        r=float(row["r"]),
        q=float(row["q"]),
        option=row["type"]
    ),
    axis=1
)

# Pricing error vs market mid
df["abs_error_vs_mid"] = (df["bs_price_histvol"] - df["mid"]).abs()

# Select neat columns
out_cols = ["type","contractSymbol","strike","lastPrice","bid","ask","mid",
            "S","T","r","q","bs_price_histvol","implied_vol","abs_error_vs_mid"]
result = df[out_cols].sort_values(by=["type","abs_error_vs_mid","strike"]).reset_index(drop=True)

print(f"Ticker: {ticker}")
print(f"Chosen expiry: {expiry_str}  (days to expiry ≈ {(expiry_dt - now_utc).days})")
print(f"Spot (S): {spot:.4f}")
print(f"Hist vol (60d ann.): {hist_vol:.4%}")
print(f"Risk-free (from ^IRX): {r:.4%}")
print("\nSample (top 10 rows):")
print(result.head(10).to_string(index=False))