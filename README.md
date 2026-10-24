# Predictive Forecasting of Care Load & Placement Demand

## 📌 Project Overview
This project analyzes historical data from the Unaccompanied Alien Children (UAC) program to understand trends in children in HHS care and children discharged from HHS care. It uses machine learning models and forecasting techniques to estimate future care load and discharge demand.

## 🎯 Objectives
- Analyze historical care load and discharge trends.
- Clean and prepare the dataset for analysis.
- Compare forecasting models using evaluation metrics.
- Predict future care load and discharge values.
- Present insights through an interactive Streamlit dashboard.

## 🛠️ Technologies Used
- Python
- Pandas
- NumPy
- Scikit-learn
- Matplotlib
- Plotly
- Streamlit

## 📊 Project Features
- Historical trend analysis
- Data cleaning and preparation
- Forecasting using Naive Baseline, Linear Regression, and Random Forest
- Model performance comparison using MAE and RMSE
- Future forecast visualization
- Interactive dashboard and data exploration
- Forecast output reports

## 📁 Project Structure
```text
care-load-forecasting-dashboard/
├── main.py
├── app.py
├── HHS_Unaccompanied_Alien_Children_Program.csv
├── prepared_daily_data.csv
├── prepared_monthly_data.csv
├── forecast_outputs/
├── children_discharged_trend.png
├── children_in_care_trend.png
├── correlation_matrix.png
├── missing_values_report.csv
├── numeric_summary_report.csv
├── repeated_dates_report.csv
└── README.md
```

## 🚀 How to Run the Project

### 1. Clone the repository
```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd care-load-forecasting-dashboard
```

### 2. Install dependencies
```bash
pip install pandas numpy scikit-learn matplotlib plotly streamlit
```

### 3. Run the forecasting script
```bash
python main.py
```

### 4. Launch the dashboard
```bash
streamlit run app.py
```

Make sure the required dataset and forecast output files are available in the expected project folders.

## 📈 Model Evaluation
The project compares forecasting models using Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE). The best-performing model depends on the target variable and the evaluation results.

## ⚠️ Limitations
- Forecasts are based on historical data and may not reflect future policy or operational changes.
- Forecast accuracy depends on data quality and the available observations.
- Predictions are estimates and should not be treated as guaranteed future values.

## 👩‍💻 Author
Harini

## 📌 Project Type
Machine Learning | Time Series Forecasting | Data Analytics | Streamlit Dashboard
