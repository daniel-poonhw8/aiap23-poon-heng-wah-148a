import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import LabelEncoder, StandardScaler

# Set page config
st.set_page_config(
    page_title="Online Shopping Purchase Predictor",
    page_icon="🛒",
    layout="wide"
)

# Load models and preprocessing objects
@st.cache_resource
def load_models():
    models = {}
    model_files = ['logistic_regression.joblib', 'random_forest.joblib', 'xgboost.joblib']

    for model_file in model_files:
        if os.path.exists(f'models/{model_file}'):
            model_name = model_file.replace('.joblib', '')
            models[model_name] = joblib.load(f'models/{model_file}')

    return models

@st.cache_resource
def load_preprocessing():
    # Load sample data to fit preprocessing
    import sqlite3
    conn = sqlite3.connect('online_shopping.db')
    df = pd.read_sql_query("SELECT * FROM online_shopping LIMIT 1000", conn)
    conn.close()

    # Preprocessing setup
    numerical_cols = ['SpecialDayProximity', 'ExitRate', 'PageValue', 'BounceRate', 'ProductPageTime']
    categorical_cols = ['CustomerType']

    # Handle missing values
    for col in numerical_cols:
        if df[col].isnull().sum() > 0:
            df[col] = df[col].fillna(df[col].median())

    for col in categorical_cols:
        if df[col].isnull().sum() > 0:
            df[col] = df[col].fillna(df[col].mode()[0])

    # Fit label encoder
    label_encoders = {}
    for col in categorical_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        label_encoders[col] = le

    # Fit scaler
    scaler = StandardScaler()
    scaler.fit(df[numerical_cols])

    return label_encoders, scaler, numerical_cols, categorical_cols

def main():
    st.title("🛒 Online Shopping Purchase Predictor")
    st.markdown("Predict whether an online shopping session will result in a purchase")

    # Load models and preprocessing
    models = load_models()
    label_encoders, scaler, numerical_cols, categorical_cols = load_preprocessing()

    if not models:
        st.error("No trained models found. Please run the training pipeline first.")
        return

    # Sidebar for inputs
    st.sidebar.header("Input Features")

    # Customer Type
    customer_type = st.sidebar.selectbox(
        "Customer Type",
        ["Returning_Visitor", "New_Visitor", "Other"],
        help="Type of customer visiting the website"
    )

    # Numerical inputs
    special_day = st.sidebar.slider(
        "Special Day Proximity",
        0.0, 1.0, 0.0,
        help="Closeness to a special day (0-1)"
    )

    exit_rate = st.sidebar.slider(
        "Exit Rate",
        0.0, 1.0, 0.1,
        help="Exit rate from the website"
    )

    page_value = st.sidebar.slider(
        "Page Value",
        0.0, 500.0, 10.0,
        help="Average page value"
    )

    bounce_rate = st.sidebar.slider(
        "Bounce Rate",
        0.0, 1.0, 0.1,
        help="Bounce rate"
    )

    product_time = st.sidebar.slider(
        "Product Page Time",
        0.0, 2000.0, 100.0,
        help="Time spent on product pages"
    )

    traffic_source = st.sidebar.slider(
        "Traffic Source",
        1, 20, 1,
        help="Traffic source code"
    )

    region = st.sidebar.slider(
        "Geographic Region",
        -10, 10, 1,
        help="Geographic region code"
    )

    # Model selection
    selected_model = st.sidebar.selectbox(
        "Select Model",
        list(models.keys()),
        help="Choose the ML model for prediction"
    )

    # Prediction button
    if st.sidebar.button("Predict Purchase", type="primary"):
        # Prepare input data
        input_data = pd.DataFrame({
            'CustomerType': [customer_type],
            'SpecialDayProximity': [special_day],
            'ExitRate': [exit_rate],
            'PageValue': [page_value],
            'TrafficSource': [float(traffic_source)],
            'GeographicRegion': [region],
            'BounceRate': [bounce_rate],
            'ProductPageTime': [product_time]
        })

        # Preprocess
        for col in categorical_cols:
            if col in input_data.columns:
                input_data[col] = label_encoders[col].transform(input_data[col])

        # Scale numerical features
        input_data[numerical_cols] = scaler.transform(input_data[numerical_cols])

        # Make prediction
        model = models[selected_model]
        prediction = model.predict(input_data)[0]
        probabilities = model.predict_proba(input_data)[0]

        # Display results
        st.header("Prediction Results")

        col1, col2 = st.columns(2)

        with col1:
            if prediction == 1:
                st.success("🛍️ **Purchase Likely!**")
                st.markdown("The model predicts this session will result in a purchase.")
            else:
                st.warning("❌ **No Purchase**")
                st.markdown("The model predicts this session will not result in a purchase.")

        with col2:
            st.subheader("Prediction Confidence")
            prob_df = pd.DataFrame({
                'Outcome': ['No Purchase', 'Purchase'],
                'Probability': probabilities
            })
            st.bar_chart(prob_df.set_index('Outcome'))

        # Feature importance (if available)
        if hasattr(model, 'feature_importances_'):
            st.subheader("Feature Importance")
            features = input_data.columns
            importance_df = pd.DataFrame({
                'Feature': features,
                'Importance': model.feature_importances_
            }).sort_values('Importance', ascending=False)

            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(data=importance_df, x='Importance', y='Feature', ax=ax)
            ax.set_title(f'Feature Importance - {selected_model.replace("_", " ").title()}')
            st.pyplot(fig)

    # EDA Section
    st.header("📊 Exploratory Data Analysis Insights")

    tab1, tab2, tab3 = st.tabs(["Data Overview", "Key Findings", "Model Performance"])

    with tab1:
        st.subheader("Dataset Overview")
        st.markdown("""
        - **Total Sessions:** 12,330
        - **Features:** 8 input features + 1 target
        - **Target:** PurchaseCompleted (0/1)
        - **Conversion Rate:** ~15-20%
        """)

        # Sample data
        st.subheader("Sample Data")
        conn = sqlite3.connect('online_shopping.db')
        sample_df = pd.read_sql_query("SELECT * FROM online_shopping LIMIT 5", conn)
        conn.close()
        st.dataframe(sample_df)

    with tab2:
        st.subheader("Key Insights")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Strong Predictors:**")
            st.markdown("- PageValue (positive correlation)")
            st.markdown("- BounceRate (negative correlation)")
            st.markdown("- ExitRate (negative correlation)")

        with col2:
            st.markdown("**Customer Behavior:**")
            st.markdown("- 85% Returning Visitors")
            st.markdown("- Most sessions have zero page value")
            st.markdown("- High variability in engagement time")

    with tab3:
        st.subheader("Model Performance Summary")
        performance_data = {
            'Model': ['Logistic Regression', 'Random Forest', 'XGBoost'],
            'Accuracy': [0.8816, 0.8913, 0.8877],
            'F1-Score': [0.5068, 0.5952, 0.5809],
            'ROC-AUC': [0.8664, 0.8838, 0.8890]
        }

        perf_df = pd.DataFrame(performance_data)
        st.dataframe(perf_df)

        st.markdown("**Best Model:** Random Forest (highest F1-score)")

if __name__ == "__main__":
    main()