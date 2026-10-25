
import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

warnings.filterwarnings("ignore")

# ==========================================================
# 1. SETTINGS
# ==========================================================

DATA_FILE = "prepared_daily_data.csv"
FORECAST_MONTHS = 6
TEST_MONTHS = 12

TARGETS = [
    "Children in HHS Care",
    "Children discharged from HHS Care"
]

os.makedirs("forecast_outputs", exist_ok=True)

print("=" * 65)
print("PREDICTIVE FORECASTING OF CARE LOAD & PLACEMENT DEMAND")
print("=" * 65)

# ==========================================================
# 2. LOAD PREPARED DATA
# ==========================================================

if not os.path.exists(DATA_FILE):
    raise FileNotFoundError(
        f"{DATA_FILE} not found. Run your data preparation code first."
    )

df = pd.read_csv(DATA_FILE, parse_dates=["Date"])
df = df.sort_values("Date")

for col in TARGETS:
    if col not in df.columns:
        raise ValueError(f"Missing required column: {col}")

print("\nPrepared records:", len(df))
print("Date range:", df["Date"].min(), "to", df["Date"].max())

# ==========================================================
# 3. CREATE MONTHLY SERIES
# ==========================================================

# Monthly mean of the available recorded values.
# This is an estimate, not a monthly total.
monthly = (
    df.set_index("Date")[TARGETS]
    .resample("MS")
    .mean()
)

print("\nMonths in monthly calendar:", len(monthly))
print("Missing monthly values before handling:")
print(monthly.isna().sum())

# Interpolate only missing months between observed months.
# Leading/trailing missing months are NOT extrapolated here.
monthly = monthly.interpolate(method="time", limit_area="inside")

print("\nMissing monthly values after interior interpolation:")
print(monthly.isna().sum())

# Save the monthly series used for modelling.
monthly.to_csv("forecast_outputs/monthly_model_data.csv")

# ==========================================================
# 4. FORECASTING FEATURES
# ==========================================================

def make_features(series):
    data = pd.DataFrame({"y": series})
    data["time_index"] = np.arange(len(data))
    data["month_number"] = data.index.month

    for lag in [1, 2, 3, 6, 12]:
        data[f"lag_{lag}"] = data["y"].shift(lag)

    data["rolling_mean_3"] = data["y"].shift(1).rolling(3).mean()
    data["rolling_mean_6"] = data["y"].shift(1).rolling(6).mean()

    return data.dropna()


# ==========================================================
# 5. TRAIN, TEST AND COMPARE MODELS
# ==========================================================

all_results = []
future_results = []
model_scores = {}

def rmse(y_true, y_pred):
    return np.sqrt(mean_squared_error(y_true, y_pred))


for target in TARGETS:
    print("\n" + "=" * 65)
    print("TARGET:", target)
    print("=" * 65)

    series = monthly[target].dropna().astype(float)

    if len(series) < 24:
        print("Not enough monthly observations for reliable forecasting.")
        continue

    # Hold out the latest months for chronological testing.
    test_size = min(TEST_MONTHS, max(3, len(series) // 5))
    train = series.iloc[:-test_size]
    test = series.iloc[-test_size:]

    feature_data = make_features(series)
    feature_columns = [
        "time_index", "month_number",
        "lag_1", "lag_2", "lag_3", "lag_6", "lag_12",
        "rolling_mean_3", "rolling_mean_6"
    ]

    # Keep training rows strictly before the test period.
    train_features = feature_data.loc[
        feature_data.index < test.index[0]
    ]
    test_features = feature_data.loc[
        feature_data.index.isin(test.index)
    ]

    if len(train_features) < 12 or len(test_features) == 0:
        print("Not enough valid lagged records for model evaluation.")
        continue

    X_train = train_features[feature_columns]
    y_train = train_features["y"]
    X_test = test_features[feature_columns]
    y_test = test_features["y"]

    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(
            n_estimators=300,
            max_depth=5,
            min_samples_leaf=2,
            random_state=42
        )
    }

    predictions = {}

    # Baseline: predict the last observed training value.
    predictions["Naive Baseline"] = np.repeat(
        train.iloc[-1], len(y_test)
    )

    for name, model in models.items():
        model.fit(X_train, y_train)
        predictions[name] = model.predict(X_test)

    score_rows = []

    for name, pred in predictions.items():
        mae = mean_absolute_error(y_test, pred)
        score_rmse = rmse(y_test, pred)

        score_rows.append({
            "Target": target,
            "Model": name,
            "MAE": mae,
            "RMSE": score_rmse
        })

        print(
            f"{name}: MAE={mae:.2f}, RMSE={score_rmse:.2f}"
        )

    scores = pd.DataFrame(score_rows)
    all_results.extend(score_rows)

    # Select the model with the lowest test RMSE.
    best_name = scores.sort_values("RMSE").iloc[0]["Model"]
    print("\nBest model by test RMSE:", best_name)

    model_scores[target] = {
        "best_model": best_name,
        "scores": scores
    }

    # Save held-out predictions for inspection.
    test_output = pd.DataFrame({
        "Date": y_test.index,
        "Actual": y_test.values,
        "Naive Baseline": predictions["Naive Baseline"],
        "Linear Regression": predictions["Linear Regression"],
        "Random Forest": predictions["Random Forest"]
    })

    safe_name = target.lower().replace(" ", "_")
    test_output.to_csv(
        f"forecast_outputs/{safe_name}_test_predictions.csv",
        index=False
    )

    # ======================================================
    # 6. REFIT SELECTED MODEL ON ALL AVAILABLE DATA
    # ======================================================

    final_features = make_features(series)
    X_all = final_features[feature_columns]
    y_all = final_features["y"]

    if best_name == "Linear Regression":
        final_model = LinearRegression()
        final_model.fit(X_all, y_all)
    elif best_name == "Random Forest":
        final_model = RandomForestRegressor(
            n_estimators=300,
            max_depth=5,
            min_samples_leaf=2,
            random_state=42
        )
        final_model.fit(X_all, y_all)
    else:
        final_model = None

    # Recursive forecast: each predicted month becomes a later lag.
    history = series.copy()
    future_dates = pd.date_range(
        series.index[-1] + pd.offsets.MonthBegin(1),
        periods=FORECAST_MONTHS,
        freq="MS"
    )

    future_values = []

    for date in future_dates:
        if final_model is None:
            value = history.iloc[-1]
        else:
            n = len(history)
            row = {
                "time_index": n,
                "month_number": date.month,
                "lag_1": history.iloc[-1],
                "lag_2": history.iloc[-2],
                "lag_3": history.iloc[-3],
                "lag_6": history.iloc[-6],
                "lag_12": history.iloc[-12],
                "rolling_mean_3": history.iloc[-3:].mean(),
                "rolling_mean_6": history.iloc[-6:].mean()
            }

            X_future = pd.DataFrame([row])[feature_columns]
            value = float(final_model.predict(X_future)[0])

        # Counts cannot be negative. Keep unrounded values for iteration.
        value = max(0.0, value)
        future_values.append(value)
        history.loc[date] = value

    future_df = pd.DataFrame({
        "Date": future_dates,
        "Target": target,
        "Forecast": np.round(future_values, 2)
    })

    future_results.append(future_df)

    # ======================================================
    # 7. PLOT ACTUAL HISTORY AND FUTURE FORECAST
    # ======================================================

    plt.figure(figsize=(12, 5))
    plt.plot(
        series.index, series.values,
        label="Historical monthly average"
    )
    plt.plot(
        future_dates, future_values,
        marker="o", linestyle="--",
        label=f"{best_name} forecast"
    )

    plt.axvline(
        series.index[-1],
        linestyle=":",
        label="Forecast starts"
    )

    plt.title(f"Monthly Forecast: {target}")
    plt.xlabel("Month")
    plt.ylabel("Average reported count")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(
        f"forecast_outputs/{safe_name}_forecast.png",
        dpi=150
    )
    plt.close()

    print("Forecast graph saved.")

# ==========================================================
# 8. SAVE ALL RESULTS
# ==========================================================

if all_results:
    results_df = pd.DataFrame(all_results)
    results_df.to_csv(
        "forecast_outputs/model_comparison.csv",
        index=False
    )

    print("\nMODEL COMPARISON")
    print(results_df.to_string(index=False))

if future_results:
    future_all = pd.concat(future_results, ignore_index=True)
    future_all.to_csv(
        "forecast_outputs/future_forecasts.csv",
        index=False
    )

    print("\nFUTURE FORECASTS")
    print(future_all.to_string(index=False))

print("\n" + "=" * 65)
print("FORECASTING RUN COMPLETE")
print("Check the forecast_outputs folder.")
print("=" * 65)
