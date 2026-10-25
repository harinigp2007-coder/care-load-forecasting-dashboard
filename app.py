
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "forecast_outputs"

CARE = "Children in HHS Care"
DISCHARGED = "Children discharged from HHS Care"
TARGETS = [CARE, DISCHARGED]

st.set_page_config(
    page_title="CareCast | Forecast Intelligence",
    page_icon="📈",
    layout="wide",
)

BG = "#0A1020"
PANEL = "#111B2E"
BORDER = "#263751"
TEXT = "#EDF4FF"
MUTED = "#9FB0C8"
TEAL = "#4DE1C1"
VIOLET = "#A78BFA"
BLUE = "#67B7FF"
AMBER = "#FFC66D"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
.stApp {{
    background:radial-gradient(circle at 82% 0%,rgba(103,183,255,.09),transparent 28%),
    radial-gradient(circle at 5% 15%,rgba(77,225,193,.06),transparent 25%),{BG};
    color:{TEXT};
}}
.block-container {{max-width:1500px;padding-top:1.6rem;padding-bottom:3rem;}}
[data-testid="stSidebar"] {{background:#101A2D;border-right:1px solid {BORDER};}}
[data-testid="stSidebar"] * {{color:{TEXT};}}
h1,h2,h3 {{font-family:'Space Grotesk',sans-serif!important;color:{TEXT}!important;}}
p,label {{color:{MUTED};}}
[data-testid="stMetric"] {{
    background:linear-gradient(145deg,#15233A,#0F1A2C);
    border:1px solid {BORDER};border-radius:17px;padding:19px;min-height:110px;
}}
[data-testid="stMetricValue"] {{color:{TEAL}!important;}}
.stButton button,.stDownloadButton button {{
    background:linear-gradient(100deg,#0D9488,#0F766E);
    color:white!important;border-radius:10px;font-weight:600;
}}
.hero {{
    padding:30px;border:1px solid #29415A;border-radius:22px;
    background:linear-gradient(112deg,#14263D,#102B38 54%,#211D42);
    margin-bottom:24px;
}}
.eyebrow {{color:{TEAL};font-size:11px;font-weight:700;letter-spacing:2px;}}
.hero-title {{font-family:'Space Grotesk',sans-serif;font-size:34px;font-weight:700;color:#F5F8FF;margin-top:12px;}}
.hero-sub {{color:#B4C5D9;font-size:14px;margin-top:12px;line-height:1.7;}}
.section-kicker {{color:{TEAL};font-size:11px;letter-spacing:2px;font-weight:700;}}
.section-title {{font-family:'Space Grotesk',sans-serif;font-size:23px;font-weight:600;color:{TEXT};}}
.section-sub {{color:{MUTED};font-size:13px;margin-bottom:18px;}}
.note {{background:rgba(255,198,109,.07);border:1px solid rgba(255,198,109,.24);border-radius:12px;padding:14px;color:#E8D6B4;line-height:1.7;}}
.footer {{color:#7588A2;font-size:11px;text-align:center;padding-top:12px;}}
</style>
""", unsafe_allow_html=True)


# ---------- File helpers ----------

@st.cache_data
def read_csv(path):
    try:
        p = Path(path)
        if not p.is_file():
            return None
        df = pd.read_csv(p)
        return df if not df.empty else None
    except Exception:
        return None


def locate_file(filename, folder=None):
    candidates = []

    if folder:
        candidates.append(Path(folder) / filename)

    candidates.append(BASE_DIR / filename)

    for path in candidates:
        if path.is_file():
            return path

    # Search subfolders if the file is nested elsewhere.
    try:
        matches = list(BASE_DIR.rglob(filename))
        if matches:
            return min(matches, key=lambda p: len(p.parts))
    except Exception:
        pass

    return None


def load_file(filename, folder=None):
    path = locate_file(filename, folder)
    if path is None:
        return None, None
    return read_csv(path), path


def find_col(df, names):
    if df is None:
        return None

    lookup = {
        str(c).strip().lower(): c
        for c in df.columns
    }

    for name in names:
        if name.lower() in lookup:
            return lookup[name.lower()]

    return None


def section(title, subtitle="", kicker="CARECAST / ANALYTICS"):
    st.markdown(
        f'<div class="section-kicker">{kicker}</div>'
        f'<div class="section-title">{title}</div>'
        f'<div class="section-sub">{subtitle}</div>',
        unsafe_allow_html=True,
    )


def num(value, digits=1):
    try:
        if pd.isna(value):
            return "—"
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return "—"


def make_trend(df, x, y, title, color=TEAL):
    fig = go.Figure()

    if df is not None and not df.empty and x in df.columns and y in df.columns:
        fig.add_trace(go.Scatter(
            x=df[x],
            y=df[y],
            mode="lines",
            name=str(y),
            line=dict(color=color, width=2.7, shape="spline"),
            fill="tozeroy",
            hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>",
        ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color=TEXT)),
        height=350,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=MUTED),
        margin=dict(l=10, r=10, t=45, b=10),
        showlegend=False,
        xaxis=dict(gridcolor="rgba(159,176,200,.10)"),
        yaxis=dict(gridcolor="rgba(159,176,200,.10)"),
    )

    return fig


def download_csv(label, df, filename, key):
    if df is not None and not df.empty:
        st.download_button(
            label=label,
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=filename,
            mime="text/csv",
            key=key,
            use_container_width=True,
        )
    else:
        st.caption(f"{filename} is not available.")


# ---------- Load files ----------

daily, daily_path = load_file("prepared_daily_data.csv")

# Prefer the expected generated forecast file.
forecasts, forecast_path = load_file(
    "future_forecasts.csv", OUT_DIR
)

# Fallback to the root-level forecast.csv.
fallback_path = None

if forecasts is None:
    forecasts, fallback_path = load_file("forecast.csv")
    if forecasts is not None:
        forecast_path = fallback_path

models, models_path = load_file(
    "model_comparison.csv", OUT_DIR
)

care_test, care_test_path = load_file(
    "children_in_hhs_care_test_predictions.csv", OUT_DIR
)

discharge_test, discharge_test_path = load_file(
    "children_discharged_from_hhs_care_test_predictions.csv",
    OUT_DIR,
)


# ---------- Validate historical data ----------

if daily is None:
    st.error("prepared_daily_data.csv could not be loaded.")
    st.write("App folder:", str(BASE_DIR))
    st.write("Expected file: prepared_daily_data.csv")
    st.stop()

date_col = find_col(daily, ["Date", "Day"])

if date_col is None:
    st.error("Date column was not found in prepared_daily_data.csv.")
    st.write("Available columns:", list(daily.columns))
    st.stop()

if date_col != "Date":
    daily = daily.rename(columns={date_col: "Date"})

daily["Date"] = pd.to_datetime(daily["Date"], errors="coerce")
daily = daily.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)

# Recognise common variations in target column names.
lookup = {str(c).strip().lower(): c for c in daily.columns}

if CARE not in daily.columns:
    col = find_col(daily, ["Children in care", "Care", "Care_Load"])
    if col:
        daily = daily.rename(columns={col: CARE})

if DISCHARGED not in daily.columns:
    col = find_col(daily, ["Children discharged", "Discharged", "Discharges"])
    if col:
        daily = daily.rename(columns={col: DISCHARGED})

for col in TARGETS:
    if col in daily.columns:
        daily[col] = pd.to_numeric(daily[col], errors="coerce")

if daily.empty:
    st.error("No valid dated records were found.")
    st.stop()

lo = daily["Date"].min().date()
hi = daily["Date"].max().date()

if forecasts is not None:
    forecast_date_col = find_col(
        forecasts, ["Date", "Month", "Forecast Date"]
    )
    if forecast_date_col:
        forecasts[forecast_date_col] = pd.to_datetime(
            forecasts[forecast_date_col], errors="coerce"
        )


# ---------- Sidebar ----------

with st.sidebar:
    st.markdown(
        f'<div style="font-size:27px;font-weight:700;color:{TEXT}">◈ CareCast</div>'
        f'<div style="font-size:10px;letter-spacing:2px;color:{TEAL}">FORECAST INTELLIGENCE</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    page = st.radio("WORKSPACE", [
        "Command Centre",
        "Historical Insights",
        "Forecast Studio",
        "Model Lab",
        "Prediction Validation",
        "Data Explorer",
        "Methodology & Quality",
        "Debug / File Status",
    ])

    st.divider()
    st.markdown("**TIME WINDOW**")

    date_range = st.date_input(
        "Filter historical records",
        value=(lo, hi),
        min_value=lo,
        max_value=hi,
    )

    st.divider()
    st.caption("SOURCE")
    st.write("HHS Unaccompanied Alien Children Program")
    st.caption(f"{len(daily):,} prepared records")


if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = lo, hi

filtered = daily[
    daily["Date"].dt.date.between(start_date, end_date)
].copy()


# ---------- Header ----------

st.markdown("""
<div class="hero">
    <div class="eyebrow">◈ FORECAST INTELLIGENCE PLATFORM</div>
    <div class="hero-title">
        Predictive Forecasting of<br>Care Load &amp; Placement Demand
    </div>
    <div class="hero-sub">
        Explore historical care patterns, compare forecasting models,
        and review future estimates in one analytics workspace.
    </div>
    <div style="margin-top:18px">
        <span class="eyebrow">HISTORICAL ANALYTICS</span> &nbsp;
        <span class="eyebrow">MACHINE LEARNING</span> &nbsp;
        <span class="eyebrow">6-MONTH OUTLOOK</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------- Command Centre ----------

if page == "Command Centre":
    section("Command Centre", "Overview of the selected historical period.", "01 / OVERVIEW")

    cols = st.columns(4)
    values = [
        ("Records in View", f"{len(filtered):,}"),
        ("Average Care Load", num(filtered[CARE].mean(), 0) if CARE in filtered else "—"),
        ("Peak Care Load", num(filtered[CARE].max(), 0) if CARE in filtered else "—"),
        ("Avg. Discharges", num(filtered[DISCHARGED].mean()) if DISCHARGED in filtered else "—"),
    ]

    for col, (label, value) in zip(cols, values):
        with col:
            st.metric(label, value)

    left, right = st.columns(2)

    with left:
        if CARE in filtered:
            st.plotly_chart(
                make_trend(filtered, "Date", CARE, "Children in HHS Care"),
                use_container_width=True,
            )
        else:
            st.info(f"Column not found: {CARE}")

    with right:
        if DISCHARGED in filtered:
            st.plotly_chart(
                make_trend(filtered, "Date", DISCHARGED, "Children Discharged", VIOLET),
                use_container_width=True,
            )
        else:
            st.info(f"Column not found: {DISCHARGED}")

    section("Forecast Snapshot", "Saved forecast values.", "LIVE / OUTLOOK")

    if forecasts is not None and not forecasts.empty:
        st.success(f"Forecast loaded successfully: {len(forecasts)} rows")
        st.dataframe(forecasts, use_container_width=True, hide_index=True)
        download_csv("Download forecast CSV", forecasts, "forecast.csv", "forecast_download")
    else:
        st.error("Forecast CSV could not be loaded. Open Debug / File Status.")

    st.markdown(
        '<div class="note"><b>Interpretation:</b> Forecasts are model estimates, '
        'not official projections. Actual future values may differ.</div>',
        unsafe_allow_html=True,
    )


# ---------- Historical Insights ----------

elif page == "Historical Insights":
    section("Historical Insights", "Explore historical trends and distributions.", "02 / EXPLORE")

    available = [c for c in TARGETS if c in filtered.columns]

    if not available:
        st.warning("Care and discharge columns were not found.")
        st.write("Available columns:", list(filtered.columns))
    else:
        cols = st.columns(2)
        for i, target in enumerate(available):
            with cols[i]:
                color = TEAL if target == CARE else VIOLET
                st.plotly_chart(
                    make_trend(filtered, "Date", target, target, color),
                    use_container_width=True,
                )

        monthly = (
            filtered.set_index("Date")[available]
            .resample("MS").mean().reset_index()
        )

        cols = st.columns(2)
        for i, target in enumerate(available):
            with cols[i]:
                st.plotly_chart(
                    make_trend(monthly, "Date", target, f"Monthly average — {target}", BLUE),
                    use_container_width=True,
                )

        section("Descriptive Statistics", "Summary of the selected records.", "STATISTICS")
        st.dataframe(filtered[available].describe().T, use_container_width=True)

        long_data = filtered[["Date"] + available].melt(
            "Date", var_name="Metric", value_name="Value"
        ).dropna()

        if not long_data.empty:
            fig = px.box(
                long_data, x="Metric", y="Value",
                color="Metric", points=False,
                title="Observed value distribution",
            )
            st.plotly_chart(fig, use_container_width=True)


# ---------- Forecast Studio ----------

elif page == "Forecast Studio":
    section("Forecast Studio", "Explore saved forecast estimates.", "03 / FUTURE")

    if forecasts is None or forecasts.empty:
        st.error("No readable forecast file was found.")
        st.info("Open Debug / File Status to inspect file paths.")
    else:
        target_col = find_col(forecasts, ["Target", "Metric", "Series"])
        value_col = find_col(forecasts, ["Forecast", "Prediction", "Predicted", "yhat"])
        date_col = find_col(forecasts, ["Date", "Month", "Forecast Date"])

        if target_col and value_col:
            targets = forecasts[target_col].dropna().unique().tolist()

            if targets:
                selected_target = st.selectbox("Select forecast target", targets)
                selected = forecasts[forecasts[target_col] == selected_target].copy()
            else:
                selected = forecasts.copy()
                selected_target = "Forecast"

            if date_col:
                selected = selected.sort_values(date_col)

            values = pd.to_numeric(selected[value_col], errors="coerce").dropna()

            a, b, c = st.columns(3)
            a.metric("Forecast periods", len(selected))
            b.metric("First forecast", num(values.iloc[0]) if len(values) else "—")
            c.metric("Last forecast", num(values.iloc[-1]) if len(values) else "—")

            if date_col and not selected.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=selected[date_col],
                    y=selected[value_col],
                    mode="lines+markers",
                    name="Forecast",
                    line=dict(color=TEAL, width=3),
                    marker=dict(color=VIOLET, size=8),
                ))
                fig.update_layout(
                    title=f"Forecast trajectory — {selected_target}",
                    height=400,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color=MUTED),
                )
                st.plotly_chart(fig, use_container_width=True)

            st.dataframe(selected, use_container_width=True, hide_index=True)
            download_csv("Download selected forecast", selected, "selected_forecast.csv", "selected_forecast")
        else:
            st.warning("Forecast loaded, but Target or Forecast columns were not identified.")
            st.write("Available columns:", list(forecasts.columns))
            st.dataframe(forecasts, use_container_width=True, hide_index=True)

    st.markdown(
        '<div class="note"><b>Forecast caution:</b> Values are model estimates and are not guaranteed future counts.</div>',
        unsafe_allow_html=True,
    )


# ---------- Model Lab ----------

elif page == "Model Lab":
    section("Model Lab", "Compare saved model evaluation metrics.", "04 / BENCHMARK")

    if models is None or models.empty:
        st.warning("model_comparison.csv is missing or unreadable.")
    else:
        target_col = find_col(models, ["Target", "Metric", "Series"])
        model_col = find_col(models, ["Model", "Model Name", "Algorithm"])
        rmse_col = find_col(models, ["RMSE", "Test RMSE"])
        mae_col = find_col(models, ["MAE", "Test MAE"])

        if target_col and model_col:
            for target in models[target_col].dropna().unique():
                part = models[models[target_col] == target].copy()
                st.markdown(f"#### {target}")

                if rmse_col:
                    part[rmse_col] = pd.to_numeric(part[rmse_col], errors="coerce")
                    valid = part.dropna(subset=[rmse_col])

                    if not valid.empty:
                        best = valid.loc[valid[rmse_col].idxmin()]
                        st.metric(
                            "Lowest test RMSE model",
                            str(best[model_col]),
                            f"RMSE {best[rmse_col]:,.2f}",
                        )

                metric_cols = [model_col]
                if rmse_col:
                    metric_cols.append(rmse_col)
                if mae_col:
                    metric_cols.append(mae_col)

                if len(metric_cols) > 1:
                    chart_data = part[metric_cols].copy()
                    for col in metric_cols[1:]:
                        chart_data[col] = pd.to_numeric(chart_data[col], errors="coerce")

                    melted = chart_data.melt(
                        model_col, var_name="Metric", value_name="Error"
                    ).dropna()

                    if not melted.empty:
                        fig = px.bar(
                            melted, x=model_col, y="Error",
                            color="Metric", barmode="group",
                            title="Test-period error comparison",
                        )
                        st.plotly_chart(fig, use_container_width=True)

                st.dataframe(part, use_container_width=True, hide_index=True)
        else:
            st.warning("Could not identify model or target columns.")
            st.write("Available columns:", list(models.columns))
            st.dataframe(models, use_container_width=True, hide_index=True)

        download_csv("Download model comparison", models, "model_comparison.csv", "model_download")


# ---------- Prediction Validation ----------

elif page == "Prediction Validation":
    section("Prediction Validation", "Compare actual and predicted values.", "05 / VALIDATE")

    for target, test_df, color in [
        (CARE, care_test, TEAL),
        (DISCHARGED, discharge_test, VIOLET),
    ]:
        st.markdown(f"#### {target}")

        if test_df is None or test_df.empty:
            st.info(f"Test predictions unavailable for {target}.")
            continue

        test_df = test_df.copy()
        date_col = find_col(test_df, ["Date", "Month"])
        actual_col = find_col(test_df, ["Actual", "y_true", "True", "Observed"])
        pred_col = find_col(test_df, ["Predicted", "Prediction", "y_pred", "Forecast"])

        if date_col:
            test_df[date_col] = pd.to_datetime(test_df[date_col], errors="coerce")
            test_df = test_df.sort_values(date_col)

        if actual_col and pred_col:
            test_df[actual_col] = pd.to_numeric(test_df[actual_col], errors="coerce")
            test_df[pred_col] = pd.to_numeric(test_df[pred_col], errors="coerce")
            valid = test_df.dropna(subset=[actual_col, pred_col])

            if not valid.empty:
                x = valid[date_col] if date_col else list(range(len(valid)))

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=x, y=valid[actual_col], mode="lines+markers",
                    name="Actual", line=dict(color=BLUE, width=2.5),
                ))
                fig.add_trace(go.Scatter(
                    x=x, y=valid[pred_col], mode="lines+markers",
                    name="Predicted", line=dict(color=color, width=2.5, dash="dash"),
                ))
                fig.update_layout(
                    title="Actual vs predicted",
                    height=350,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color=MUTED),
                )
                st.plotly_chart(fig, use_container_width=True)

                errors = valid[actual_col] - valid[pred_col]
                a, b, c = st.columns(3)
                a.metric("Test points", len(valid))
                b.metric("MAE", num(errors.abs().mean(), 2))
                c.metric("RMSE", num((errors.pow(2).mean()) ** 0.5, 2))

            st.dataframe(test_df, use_container_width=True, hide_index=True)
            download_csv(
                f"Download {target} predictions",
                test_df,
                f"{target.lower().replace(' ', '_')}_test_predictions.csv",
                f"download_{target}",
            )
        else:
            st.warning("Actual/predicted columns could not be identified.")
            st.write("Available columns:", list(test_df.columns))
            st.dataframe(test_df, use_container_width=True, hide_index=True)


# ---------- Data Explorer ----------

elif page == "Data Explorer":
    section("Data Explorer", "Search and export historical records.", "06 / DATA")

    a, b, c = st.columns(3)
    a.metric("Rows in view", f"{len(filtered):,}")
    b.metric("Columns", len(filtered.columns))
    c.metric("Missing cells", int(filtered.isna().sum().sum()))

    query = st.text_input("Search historical data", placeholder="Type a value")
    view = filtered.copy()

    if query.strip():
        mask = view.astype(str).apply(
            lambda col: col.str.contains(query.strip(), case=False, na=False)
        ).any(axis=1)
        view = view[mask]

    st.dataframe(view, use_container_width=True, hide_index=True)

    a, b = st.columns(2)
    with a:
        download_csv("Download filtered data", view, "filtered_historical_data.csv", "filtered")
    with b:
        download_csv("Download full data", daily, "prepared_daily_data.csv", "full_data")

    missing = filtered.isna().sum().rename("Missing values").reset_index()
    missing = missing.rename(columns={"index": "Column"})
    missing["Missing %"] = (
        missing["Missing values"] / max(len(filtered), 1) * 100
    ).round(2)

    section("Missing Values", "Missing cells in the selected records.", "DATA QUALITY")
    st.dataframe(missing, use_container_width=True, hide_index=True)


# ---------- Methodology & Quality ----------

elif page == "Methodology & Quality":
    section("Methodology & Quality", "Preparation and model limitations.", "07 / TRUST")

    a, b, c, d = st.columns(4)
    a.metric("Prepared records", f"{len(daily):,}")
    b.metric("Duplicate rows", int(daily.duplicated().sum()))
    c.metric(
        "Missing target cells",
        int(daily[TARGETS].isna().sum().sum())
        if all(col in daily.columns for col in TARGETS)
        else "N/A",
    )
    d.metric("Calendar span", f"{(daily.Date.max() - daily.Date.min()).days:,} days")

    workflow = pd.DataFrame({
        "Stage": [
            "1. Data collection",
            "2. Data preparation",
            "3. Monthly aggregation",
            "4. Feature engineering",
            "5. Model comparison",
            "6. Forecasting",
        ],
        "Description": [
            "HHS Unaccompanied Alien Children Program CSV",
            "Repeated-date records were provisionally aggregated; verify source meaning",
            "Monthly means used for modelling where applicable",
            "Lag features and rolling averages may be used by the forecasting script",
            "Naive Baseline, Linear Regression and Random Forest comparison",
            "Forecast estimates based on the available historical data",
        ],
    })

    st.dataframe(workflow, use_container_width=True, hide_index=True)

    quality = pd.DataFrame([
        {
            "Column": col,
            "Missing values": int(daily[col].isna().sum()),
            "Missing %": round(float(daily[col].isna().mean() * 100), 2),
            "Unique values": int(daily[col].nunique(dropna=True)),
        }
        for col in daily.columns
    ])

    st.markdown("#### Data quality report")
    st.dataframe(quality, use_container_width=True, hide_index=True)

    st.markdown(
        '<div class="note"><b>Important:</b> This is an academic analytics project. '
        'Forecasts are estimates, not official HHS projections. Verify source data '
        'and model assumptions before using results for planning.</div>',
        unsafe_allow_html=True,
    )


# ---------- Debug / File Status ----------

elif page == "Debug / File Status":
    section("Debug / File Status", "Check file paths, row counts and CSV columns.", "08 / DEBUG")

    files = [
        ("prepared_daily_data.csv", daily_path, daily),
        ("forecast_outputs/future_forecasts.csv", locate_file("future_forecasts.csv", OUT_DIR),
         read_csv(locate_file("future_forecasts.csv", OUT_DIR))
         if locate_file("future_forecasts.csv", OUT_DIR) else None),
        ("forecast.csv", locate_file("forecast.csv"), read_csv(locate_file("forecast.csv"))
         if locate_file("forecast.csv") else None),
        ("forecast_outputs/model_comparison.csv", models_path, models),
        ("children_in_hhs_care_test_predictions.csv", care_test_path, care_test),
        ("children_discharged_from_hhs_care_test_predictions.csv", discharge_test_path, discharge_test),
    ]

    rows = []
    for name, path, df in files:
        rows.append({
            "File": name,
            "Exists": bool(path and Path(path).is_file()),
            "Resolved path": str(path) if path else "NOT FOUND",
            "Rows": len(df) if df is not None else 0,
            "Columns": ", ".join(map(str, df.columns)) if df is not None else "—",
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("#### Application folder")
    st.code(str(BASE_DIR))

    st.markdown("#### Forecast preview")
    if forecasts is not None and not forecasts.empty:
        st.write("Loaded forecast from:", str(forecast_path))
        st.dataframe(forecasts.head(20), use_container_width=True, hide_index=True)
    else:
        st.error("No readable forecast CSV found. Check the table above.")

    if st.button("Clear cache and reload"):
        st.cache_data.clear()
        st.rerun()


# ---------- Footer ----------

st.markdown("---")
st.markdown(
    '<div class="footer">CARECAST ◈ FORECAST INTELLIGENCE · Python · Pandas · Streamlit · Plotly · Educational analytics project</div>',
    unsafe_allow_html=True,
)
