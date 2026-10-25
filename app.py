from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

BASE_DIR = Path(__file__).resolve().parent
OUT = BASE_DIR / "forecast_outputs"
CARE = "Children in HHS Care"
DISCHARGED = "Children discharged from HHS Care"
TARGETS = [CARE, DISCHARGED]

st.set_page_config(page_title="CareCast | Forecast Intelligence", page_icon="📈", layout="wide")

BG, PANEL, BORDER = "#0A1020", "#111B2E", "#263751"
TEXT, MUTED, TEAL, VIOLET, BLUE, AMBER = "#EDF4FF", "#9FB0C8", "#4DE1C1", "#A78BFA", "#67B7FF", "#FFC66D"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
.stApp {{background:radial-gradient(circle at 82% 0%,rgba(103,183,255,.09),transparent 28%),radial-gradient(circle at 5% 15%,rgba(77,225,193,.06),transparent 25%),{BG};color:{TEXT};}}
.block-container {{max-width:1500px;padding-top:1.6rem;padding-bottom:3rem;}}
[data-testid="stSidebar"] {{background:linear-gradient(180deg,#101A2D,#0C1424);border-right:1px solid {BORDER};}}
[data-testid="stSidebar"] * {{color:{TEXT};}}
h1,h2,h3 {{font-family:'Space Grotesk',sans-serif!important;color:{TEXT}!important;}}
p,label {{color:{MUTED};}}
[data-testid="stMetric"] {{background:linear-gradient(145deg,#15233A,#0F1A2C);border:1px solid {BORDER};border-radius:17px;padding:19px 20px;min-height:115px;}}
[data-testid="stMetricLabel"] {{color:{MUTED}!important;font-size:13px!important;}}
[data-testid="stMetricValue"] {{color:{TEAL}!important;font-family:'Space Grotesk',sans-serif;font-size:27px!important;}}
[data-testid="stDataFrame"] {{border:1px solid {BORDER};border-radius:12px;overflow:hidden;}}
.stButton button,.stDownloadButton button {{background:linear-gradient(100deg,#0D9488,#0F766E);color:white!important;border:1px solid rgba(77,225,193,.3);border-radius:10px;font-weight:600;}}
hr {{border-color:{BORDER};}}
.hero {{position:relative;overflow:hidden;padding:30px 32px;border:1px solid #29415A;border-radius:22px;background:linear-gradient(112deg,#14263D,#102B38 54%,#211D42);margin-bottom:24px;}}
.hero:after {{content:"";position:absolute;width:220px;height:220px;right:-55px;top:-100px;border:1px solid rgba(77,225,193,.25);border-radius:50%;box-shadow:0 0 0 28px rgba(77,225,193,.035),0 0 0 58px rgba(167,139,250,.035);}}
.eyebrow {{color:{TEAL};font-size:11px;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;}}
.hero-title {{font-family:'Space Grotesk',sans-serif;font-size:clamp(25px,3vw,38px);line-height:1.15;font-weight:700;color:#F5F8FF;margin-top:12px;max-width:850px;}}
.hero-sub {{color:#B4C5D9;font-size:14px;margin-top:12px;max-width:720px;line-height:1.7;}}
.section-kicker {{color:{TEAL};font-size:11px;letter-spacing:1.8px;font-weight:700;text-transform:uppercase;margin-bottom:4px;}}
.section-title {{color:{TEXT};font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:600;margin-bottom:4px;}}
.section-sub {{color:{MUTED};font-size:13px;margin-bottom:18px;}}
.pill {{display:inline-block;padding:5px 9px;border-radius:30px;color:{TEAL};background:rgba(77,225,193,.10);border:1px solid rgba(77,225,193,.18);font-size:11px;font-weight:700;}}
.note {{background:rgba(255,198,109,.07);border:1px solid rgba(255,198,109,.24);border-radius:12px;padding:14px 16px;color:#E8D6B4;font-size:13px;line-height:1.65;}}
.footer {{color:#7588A2;font-size:11px;text-align:center;padding-top:12px;letter-spacing:.4px;}}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def read_csv(path):
    p = Path(path)
    if p.exists():
        try:
            return pd.read_csv(p)
        except Exception:
            return None
    return None

def section(title, subtitle="", kicker="CARECAST / ANALYTICS"):
    st.markdown(f'<div class="section-kicker">{kicker}</div><div class="section-title">{title}</div><div class="section-sub">{subtitle}</div>', unsafe_allow_html=True)

def num(v, digits=1):
    try:
        return "—" if pd.isna(v) else f"{float(v):,.{digits}f}"
    except (TypeError, ValueError):
        return "—"

def find_col(df, options):
    if df is None:
        return None
    lookup = {str(c).strip().lower(): c for c in df.columns}
    return next((lookup[o.lower()] for o in options if o.lower() in lookup), None)

def style_plot(fig, height=350):
    fig.update_layout(
        height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color=MUTED, size=12), margin=dict(l=10,r=10,t=45,b=10),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="left",x=0),
        xaxis=dict(gridcolor="rgba(159,176,200,.10)",linecolor=BORDER,zerolinecolor=BORDER),
        yaxis=dict(gridcolor="rgba(159,176,200,.10)",linecolor=BORDER,zerolinecolor=BORDER),
        hoverlabel=dict(bgcolor=PANEL,bordercolor=BORDER,font_color=TEXT)
    )
    return fig

def trend(frame, xcol, ycol, title, color=TEAL, height=350):
    fig = go.Figure()
    if frame is not None and not frame.empty and xcol in frame.columns and ycol in frame.columns:
        fig.add_trace(go.Scatter(
            x=frame[xcol],y=frame[ycol],mode="lines",name=ycol,
            line=dict(color=color,width=2.8,shape="spline"),
            fill="tozeroy",fillcolor="rgba(77,225,193,.055)" if color==TEAL else "rgba(167,139,250,.055)",
            hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>"
        ))
    fig.update_layout(title=dict(text=title,font=dict(size=15,color=TEXT)),showlegend=False)
    return style_plot(fig,height)

def download(label, frame, filename, key):
    if frame is not None and not frame.empty:
        st.download_button(label,frame.to_csv(index=False).encode("utf-8"),filename,"text/csv",key=key,use_container_width=True)
    else:
        st.caption(f"{filename} is not available yet.")

daily = read_csv(BASE_DIR / "prepared_daily_data.csv")
forecasts = read_csv(OUT / "future_forecasts.csv")

if forecasts is None or forecasts.empty:
    forecasts = read_csv(BASE_DIR / "forecast.csv")
models = read_csv(OUT / "model_comparison.csv")
care_test = read_csv(OUT / "children_in_hhs_care_test_predictions.csv")
discharge_test = read_csv(OUT / "children_discharged_from_hhs_care_test_predictions.csv")

if daily is None or "Date" not in daily.columns:
    st.error("prepared_daily_data.csv missing or does not contain a Date column. Keep app.py beside this CSV.")
    st.stop()

daily["Date"] = pd.to_datetime(daily["Date"],errors="coerce")
daily = daily.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
for c in TARGETS:
    if c in daily.columns:
        daily[c] = pd.to_numeric(daily[c],errors="coerce")
if forecasts is not None:
    fdate = find_col(forecasts,["Date","Month"])
    if fdate:
        forecasts[fdate] = pd.to_datetime(forecasts[fdate],errors="coerce")

with st.sidebar:
    st.markdown(f'<div style="font-family:Space Grotesk;font-size:27px;font-weight:700;color:{TEXT};">◈ CareCast</div><div style="font-size:10px;letter-spacing:2px;color:{TEAL};">FORECAST INTELLIGENCE</div>',unsafe_allow_html=True)
    st.markdown("")
    st.markdown('<span class="pill">● DATA PIPELINE READY</span>',unsafe_allow_html=True)
    st.divider()
    page = st.radio("WORKSPACE",[
        "Command Centre","Historical Insights","Forecast Studio","Model Lab",
        "Prediction Validation","Data Explorer","Methodology & Quality"
    ])
    st.divider()
    st.markdown("**TIME WINDOW**")
    lo,hi = daily["Date"].min().date(),daily["Date"].max().date()
    date_range = st.date_input("Filter historical records",value=(lo,hi),min_value=lo,max_value=hi)
    st.divider()
    st.caption("SOURCE")
    st.write("HHS Unaccompanied Alien Children Program")
    st.caption(f"{len(daily):,} prepared records")

if isinstance(date_range,(tuple,list)) and len(date_range)==2:
    start_date,end_date=date_range
else:
    start_date,end_date=lo,hi
filtered=daily[daily["Date"].dt.date.between(start_date,end_date)].copy()

st.markdown(f"""
<div class="hero">
<div class="eyebrow">◈ FORECAST INTELLIGENCE PLATFORM</div>
<div class="hero-title">Predictive Forecasting of<br>Care Load &amp; Placement Demand</div>
<div class="hero-sub">Explore historical care patterns, compare forecasting models, and review future estimates in one evidence-aware analytics workspace.</div>
<div style="margin-top:18px"><span class="pill">HISTORICAL ANALYTICS</span>&nbsp; <span class="pill">MACHINE LEARNING</span>&nbsp; <span class="pill">6-MONTH OUTLOOK</span></div>
</div>""",unsafe_allow_html=True)

if page=="Command Centre":
    section("Command Centre","A high-level view of the selected historical period.","01 / OVERVIEW")
    cols=st.columns(4)
    vals=[
        ("Records in View",f"{len(filtered):,}"),
        ("Average Care Load",num(filtered[CARE].mean(),0) if CARE in filtered else "—"),
        ("Peak Care Load",num(filtered[CARE].max(),0) if CARE in filtered else "—"),
        ("Avg. Discharges",num(filtered[DISCHARGED].mean(),1) if DISCHARGED in filtered else "—")
    ]
    for col,(label,value) in zip(cols,vals):
        with col: st.metric(label,value)
    left,right=st.columns(2)
    with left:
        if CARE in filtered: st.plotly_chart(trend(filtered,"Date",CARE,"Children in HHS Care",TEAL),use_container_width=True,config={"displayModeBar":False})
    with right:
        if DISCHARGED in filtered: st.plotly_chart(trend(filtered,"Date",DISCHARGED,"Children Discharged from HHS Care",VIOLET),use_container_width=True,config={"displayModeBar":False})
    section("Forecast Snapshot","Latest generated values from the forecasting pipeline.","LIVE / OUTLOOK")
    if forecasts is not None and not forecasts.empty:
        st.dataframe(forecasts,use_container_width=True,hide_index=True)
        download("⬇ Download forecast CSV",forecasts,"future_forecasts.csv","cc_forecast")
    else: st.warning("Forecast file not found. Run main.py first.")
    st.markdown('<div class="note"><b>Interpretation note:</b> Forecasts are model estimates, not official projections. The discharge forecast may be flat because the Naive Baseline repeats the latest observed value.</div>',unsafe_allow_html=True)

elif page=="Historical Insights":
    section("Historical Insights","Explore the shape, range and monthly pattern of the source data.","02 / EXPLORE")
    a,b=st.columns(2)
    with a: st.plotly_chart(trend(filtered,"Date",CARE,"Daily care-load trend",TEAL),use_container_width=True,config={"displayModeBar":False})
    with b: st.plotly_chart(trend(filtered,"Date",DISCHARGED,"Daily discharge trend",VIOLET),use_container_width=True,config={"displayModeBar":False})
    if all(c in filtered.columns for c in TARGETS):
        mon=filtered.set_index("Date")[TARGETS].resample("MS").mean().reset_index()
        a,b=st.columns(2)
        with a: st.plotly_chart(trend(mon,"Date",CARE,"Monthly average care load",BLUE),use_container_width=True,config={"displayModeBar":False})
        with b: st.plotly_chart(trend(mon,"Date",DISCHARGED,"Monthly average discharges",AMBER),use_container_width=True,config={"displayModeBar":False})
        section("Distribution & Summary","Descriptive statistics for the selected period.","STATISTICS")
        a,b=st.columns(2)
        with a: st.dataframe(filtered[TARGETS].describe().T,use_container_width=True)
        with b:
            long=filtered[["Date"]+TARGETS].melt("Date",var_name="Metric",value_name="Value").dropna()
            if not long.empty:
                fig=px.box(long,x="Metric",y="Value",color="Metric",points=False,color_discrete_sequence=[TEAL,VIOLET],title="Observed value distribution")
                st.plotly_chart(style_plot(fig,320),use_container_width=True,config={"displayModeBar":False})

elif page=="Forecast Studio":
    section("Forecast Studio","Inspect the saved six-month forecast for each target.","03 / FUTURE")
    if forecasts is None or forecasts.empty:
        st.error("Forecast results unavailable. Run main.py first.")
    else:
        target_col=find_col(forecasts,["Target"])
        value_col=find_col(forecasts,["Forecast","Prediction","Predicted"])
        date_col=find_col(forecasts,["Date","Month"])
        if target_col and value_col:
            target=st.selectbox("Select forecast target",forecasts[target_col].dropna().unique().tolist())
            selected=forecasts[forecasts[target_col]==target].copy()
            if date_col: selected=selected.sort_values(date_col)
            a,b,c=st.columns(3)
            with a: st.metric("Forecast periods",len(selected))
            with b: st.metric("First forecast",num(selected[value_col].iloc[0]) if len(selected) else "—")
            with c: st.metric("Last forecast",num(selected[value_col].iloc[-1]) if len(selected) else "—")
            if date_col and not selected.empty:
                fig=go.Figure(go.Scatter(x=selected[date_col],y=selected[value_col],mode="lines+markers",name="Forecast",line=dict(color=TEAL,width=3),marker=dict(size=9,color=VIOLET),fill="tozeroy",fillcolor="rgba(77,225,193,.07)"))
                fig.update_layout(title=dict(text=f"Forecast trajectory — {target}",font=dict(color=TEXT,size=16)))
                st.plotly_chart(style_plot(fig,410),use_container_width=True,config={"displayModeBar":False})
            st.markdown("#### Forecast values")
            st.dataframe(selected,use_container_width=True,hide_index=True)
            download("⬇ Download selected forecast",selected,"selected_forecast.csv","selected_forecast")
        else: st.dataframe(forecasts,use_container_width=True,hide_index=True)
    st.markdown('<div class="note"><b>Forecast caution:</b> Values are model outputs based on historical observations and modelling choices. They are not guaranteed future counts or a substitute for official planning data.</div>',unsafe_allow_html=True)

elif page=="Model Lab":
    section("Model Lab","Compare models using chronological holdout metrics.","04 / BENCHMARK")
    if models is None or models.empty: st.error("model_comparison.csv missing. Run main.py first.")
    else:
        target_col=find_col(models,["Target"]); model_col=find_col(models,["Model"])
        rmse_col=find_col(models,["RMSE","Test RMSE"]); mae_col=find_col(models,["MAE","Test MAE"])
        if target_col and model_col:
            for target in models[target_col].dropna().unique():
                part=models[models[target_col]==target].copy()
                st.markdown(f"#### {target}")
                if rmse_col:
                    part[rmse_col]=pd.to_numeric(part[rmse_col],errors="coerce")
                    valid=part.dropna(subset=[rmse_col])
                    if not valid.empty:
                        best=valid.loc[valid[rmse_col].idxmin()]
                        st.metric("Lowest test RMSE model",str(best[model_col]),f"RMSE {best[rmse_col]:,.2f}")
                    cols=[model_col,rmse_col]+([mae_col] if mae_col else [])
                    chart_df=part[cols].copy()
                    for col in cols[1:]: chart_df[col]=pd.to_numeric(chart_df[col],errors="coerce")
                    melted=chart_df.melt(model_col,var_name="Metric",value_name="Error").dropna()
                    if not melted.empty:
                        fig=px.bar(melted,x=model_col,y="Error",color="Metric",barmode="group",title="Test-period error comparison",color_discrete_sequence=[TEAL,VIOLET],labels={model_col:"Model", "Error":"Error (lower is better)"})
                        st.plotly_chart(style_plot(fig,330),use_container_width=True,config={"displayModeBar":False})
                st.dataframe(part,use_container_width=True,hide_index=True)
        else: st.dataframe(models,use_container_width=True,hide_index=True)
        st.markdown('<div class="note"><b>How to read:</b> Lower MAE and RMSE mean smaller errors on the held-out test period. Best historical test performance does not guarantee future performance.</div>',unsafe_allow_html=True)
        download("⬇ Download model comparison",models,"model_comparison.csv","model_download")

elif page=="Prediction Validation":
    section("Prediction Validation","Compare actual and predicted values where saved test predictions exist.","05 / VALIDATE")
    for target,test_df,color in [(CARE,care_test,TEAL),(DISCHARGED,discharge_test,VIOLET)]:
        st.markdown(f"#### {target}")
        if test_df is None or test_df.empty:
            st.info(f"Saved test predictions unavailable for {target}.")
            continue
        test_df=test_df.copy()
        date_col=find_col(test_df,["Date","Month"])
        actual_col=find_col(test_df,["Actual","y_true","True","Observed"])
        pred_col=find_col(test_df,["Predicted","Prediction","y_pred","Forecast"])
        if date_col:
            test_df[date_col]=pd.to_datetime(test_df[date_col],errors="coerce")
            test_df=test_df.sort_values(date_col)
        if actual_col and pred_col:
            test_df[actual_col]=pd.to_numeric(test_df[actual_col],errors="coerce")
            test_df[pred_col]=pd.to_numeric(test_df[pred_col],errors="coerce")
            valid=test_df.dropna(subset=[actual_col,pred_col])
            if not valid.empty:
                x=valid[date_col] if date_col else list(range(1,len(valid)+1))
                fig=go.Figure()
                fig.add_trace(go.Scatter(x=x,y=valid[actual_col],mode="lines+markers",name="Actual",line=dict(color=BLUE,width=2.5)))
                fig.add_trace(go.Scatter(x=x,y=valid[pred_col],mode="lines+markers",name="Predicted",line=dict(color=color,width=2.5,dash="dash")))
                fig.update_layout(title=dict(text="Actual vs predicted",font=dict(color=TEXT,size=15)))
                st.plotly_chart(style_plot(fig,360),use_container_width=True,config={"displayModeBar":False})
                errors=valid[actual_col]-valid[pred_col]
                a,b,c=st.columns(3)
                with a: st.metric("Test points",len(valid))
                with b: st.metric("MAE",num(errors.abs().mean(),2))
                with c: st.metric("RMSE",num((errors.pow(2).mean())**0.5,2))
            st.dataframe(test_df,use_container_width=True,hide_index=True)
            download(f"⬇ Download {target} test predictions",test_df,f"{target.lower().replace(' ','_')}_test_predictions.csv",f"test_{target}")
        else:
            st.warning("Actual/predicted columns could not be identified. Showing the saved file instead.")
            st.dataframe(test_df,use_container_width=True,hide_index=True)

elif page=="Data Explorer":
    section("Data Explorer","Inspect, search and export prepared historical records.","06 / DATA")
    a,b,c=st.columns(3)
    with a: st.metric("Rows in view",f"{len(filtered):,}")
    with b: st.metric("Columns",len(filtered.columns))
    with c: st.metric("Missing cells",int(filtered.isna().sum().sum()))
    query=st.text_input("Quick search across row values",placeholder="Type a value to filter rows")
    view=filtered.copy()
    if query.strip():
        mask=view.astype(str).apply(lambda col:col.str.contains(query.strip(),case=False,na=False)).any(axis=1)
        view=view[mask]
    st.dataframe(view,use_container_width=True,hide_index=True)
    a,b=st.columns(2)
    with a: download("⬇ Download filtered data",view,"filtered_historical_data.csv","filtered_data")
    with b: download("⬇ Download full prepared data",daily,"prepared_daily_data.csv","full_data")
    section("Missing Values","Missing cells in the filtered view.","DATA QUALITY")
    miss=filtered.isna().sum().rename("Missing values").reset_index().rename(columns={"index":"Column"})
    miss["Missing %"]=(miss["Missing values"]/max(len(filtered),1)*100).round(2)
    st.dataframe(miss,use_container_width=True,hide_index=True)

elif page=="Methodology & Quality":
    section("Methodology & Quality","Transparent notes on preparation, evaluation and assumptions.","07 / TRUST")
    a,b,c,d=st.columns(4)
    with a: st.metric("Prepared records",f"{len(daily):,}")
    with b: st.metric("Duplicate full rows",f"{int(daily.duplicated().sum()):,}")
    with c: st.metric("Missing target cells",int(daily[TARGETS].isna().sum().sum()) if all(c in daily.columns for c in TARGETS) else "N/A")
    with d: st.metric("Calendar span",f"{(daily.Date.max()-daily.Date.min()).days:,} days")
    st.markdown("#### Project workflow")
    workflow=pd.DataFrame({
        "Stage":["1. Data collection","2. Data preparation","3. Monthly aggregation","4. Feature engineering","5. Model comparison","6. Forecasting"],
        "Description":[
            "HHS Unaccompanied Alien Children Program CSV",
            "Repeated-date records were provisionally aggregated; source meaning should be verified",
            "Monthly means; one missing internal month was interpolated for modelling",
            "Lag features and rolling averages used by the forecasting script",
            "Naive Baseline, Linear Regression and Random Forest compared on chronological holdout data",
            "Selected model refitted on available history to estimate the next six months"
        ]
    })
    st.dataframe(workflow,use_container_width=True,hide_index=True)
    quality=[]
    for col in daily.columns:
        quality.append({"Column":col,"Missing values":int(daily[col].isna().sum()),"Missing %":round(float(daily[col].isna().mean()*100),2),"Unique values":int(daily[col].nunique(dropna=True))})
    st.markdown("#### Data quality report")
    st.dataframe(pd.DataFrame(quality),use_container_width=True,hide_index=True)
    st.markdown('<div class="note"><b>Important limitations</b><br>• Repeated-date rows were averaged provisionally; confirm source meaning before operational use.<br>• The reporting calendar contains gaps; monthly aggregation and interpolation affect model inputs.<br>• Model performance may change as new data arrives.<br>• This is an academic analytics project, not an official HHS forecasting tool.</div>',unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div class="footer">CARECAST ◈ FORECAST INTELLIGENCE &nbsp; • &nbsp; Python · Pandas · Streamlit · Plotly &nbsp; • &nbsp; Educational analytics project</div>',unsafe_allow_html=True)
