import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
import ast

# Constants
# API_KEY = "4455b5169ed2a312c927cfa2a4161658"
BLOCKCHAIN_OPTIONS = ["ethereum", "polygon", "avalanche", "binance", "ordinals", "linea", "solana"]
TIME_RANGE_OPTIONS = ["24h", "7d", "30d", "90d", "all"]
ITEMS_PER_PAGE = 9

# API Endpoints
METRICS_ENDPOINT = "https://api.unleashnfts.com/api/v2/nft/wallet/gaming/metrics"
COLLECTION_METRICS_ENDPOINT = "https://api.unleashnfts.com/api/v2/nft/wallet/gaming/collection/metrics"
TREND_ENDPOINT = "https://api.unleashnfts.com/api/v2/nft/wallet/gaming/collection/trend"

# Sort options for different tabs
WALLET_METRICS_SORT_OPTIONS = [
    "total_users", "volume", "transactions", "active_users"
]

COLLECTION_METRICS_SORT_OPTIONS = [
    "total_users", "total_users_change",
    "total_interactions_volume", "total_interactions_volume_change",
    "total_marketcap", "total_marketcap_change",
    "active_users", "active_users_change",
    "retention_rate", "retention_rate_change",
    "game_interactions", "game_interactions_change",
    "total_interaction", "total_interaction_change",
    "interaction_rate", "interaction_rate_change",
    "bot_count", "bot_native_price", "bot_volume",
    "unique_wallets", "unique_wallets_change",
    "avg_earnings", "game_revenue",
    "avg_game_action", "nft_count"
]

TREND_SORT_OPTIONS = [
    "active_users", "active_users_change",
    "game_interactions", "game_interactions_change",
    "avg_earnings", "game_revenue",
    "game_activity", "avg_game_action",
    "maxdate"
]

SORT_ORDER_OPTIONS = ["desc", "asc"]

def fetch_data(endpoint, params):
    """Generic function to fetch data from API"""
    headers = {
    "accept": "application/json",
    "x-api-key": st.secrets["API_KEY"]
}
    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

def clean_trend_data(data_list):
    """Clean trend data from string list format"""
    if isinstance(data_list, str):
        try:
            data_list = ast.literal_eval(data_list)
        except:
            return []
    
    if not isinstance(data_list, list):
        return []
    
    cleaned_data = []
    for item in data_list:
        try:
            # Handle both string and numeric inputs
            value = float(str(item).strip("'"))
            if pd.isna(value) or value in [float('inf'), float('-inf')]:
                value = None
            cleaned_data.append(value)
        except (ValueError, TypeError):
            cleaned_data.append(None)
    return cleaned_data

def format_metric(value, is_percentage=False):
    """Format numeric values for display"""
    if value is None or pd.isna(value):
        return "N/A"
    try:
        num = float(value)
        if is_percentage:
            return f"{num:.2f}%"
        if abs(num) >= 1_000_000:
            return f"{num/1_000_000:.2f}M"
        if abs(num) >= 1_000:
            return f"{num/1_000:.2f}K"
        return f"{num:.2f}"
    except (ValueError, TypeError):
        return "N/A"

def main():
    st.set_page_config(page_title="NFT Gaming Analytics Dashboard", layout="wide", initial_sidebar_state="expanded")
    
    # Add custom CSS for styling
    st.markdown(
        """
        <style>
        body {
            background-color: #f0f2f5; /* Light background color */
        }
        .stButton > button {
            background-color: #007BFF; /* Blue */
            color: white;
            font-size: 16px;
            border-radius: 5px;
            transition: background-color 0.3s;
        }
        .stButton > button:hover {
            background-color: #0056b3; /* Darker blue on hover */
        }
        .stMetric {
            font-size: 20px;
            font-weight: bold;
            color: #333; /* Dark text color */
        }
        .stHeader {
            color: #FF5733; /* Red */
            font-size: 24px; /* Larger header font size */
            font-weight: bold;
        }
        .stTitle {
            color: #2C3E50; /* Darker title color */
            font-size: 32px; /* Larger title font size */
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True
    )

    # Fun header with emojis
    st.title("🎮 NFT Gaming Analytics Dashboard 🎨")
    st.markdown("Welcome to the NFT Gaming Analytics Dashboard! Explore metrics and trends in the NFT gaming space.")

    # Initialize session state for pagination
    if 'page_number' not in st.session_state:
        st.session_state.page_number = 0

    # Create tabs with colorful headers
    tab1, tab2, tab3 = st.tabs(["🪙 Wallet Gaming Metrics", "📊 Collection Metrics", "📈 Trend Analysis"])

    with tab1:
        st.header("Wallet Gaming Metrics")
        # Sidebar filters for wallet metrics
        with st.sidebar:
            st.subheader("Wallet Metrics Filters")
            w_blockchain = st.selectbox("Blockchain", BLOCKCHAIN_OPTIONS, key="w_blockchain")
            w_time_range = st.selectbox("Time Range", TIME_RANGE_OPTIONS, key="w_time_range")
            w_sort_by = st.selectbox("Sort By", WALLET_METRICS_SORT_OPTIONS, key="w_sort_by")
            w_sort_order = st.selectbox("Sort Order", SORT_ORDER_OPTIONS, key="w_sort_order")
            w_limit = st.slider("Results", 1, 100, 30, key="w_limit")

        if st.button("Fetch Wallet Metrics", key="fetch_wallet"):
            params = {
                "blockchain": w_blockchain,
                "time_range": w_time_range,
                "sort_by": w_sort_by,
                "sort_order": w_sort_order,
                "limit": w_limit
            }
            data = fetch_data(METRICS_ENDPOINT, params)
            if data and "data" in data:
                df = pd.DataFrame(data["data"])
                
                # Convert numeric columns from strings to floats
                numeric_cols = ["total_users", "active_users", "volume", "transactions"]
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = df[col].apply(lambda x: float(x) if x and x != 'null' else 0.0)
                
                # Display metrics in columns with colors
                cols = st.columns(4)
                metrics = ["total_users", "active_users", "volume", "transactions"]
                for col, metric in zip(cols, metrics):
                    with col:
                        if metric in df.columns and not df.empty:
                            current_val = df[metric].iloc[0]
                            # Set delta_color based on the current value
                            delta_color = "normal" if current_val > 0 else "inverse"
                            st.metric(
                                label=metric.replace("_", " ").title(),
                                value=format_metric(current_val),
                                delta_color=delta_color
                            )
                        else:
                            st.metric(
                                label=metric.replace("_", " ").title(),
                                value="N/A"
                            )

                # Add spacing between metrics
                st.markdown("<br>", unsafe_allow_html=True)

                # Display data table with numeric conversions
                st.dataframe(df)

    with tab2:
        st.header("Collection Metrics")
        # Collection metrics filters
        with st.sidebar:
            st.subheader("Collection Metrics Filters")
            c_blockchain = st.selectbox("Blockchain", BLOCKCHAIN_OPTIONS, key="c_blockchain")
            c_time_range = st.selectbox("Time Range", TIME_RANGE_OPTIONS, key="c_time_range")
            c_sort_by = st.selectbox("Sort By", COLLECTION_METRICS_SORT_OPTIONS, key="c_sort_by")
            c_sort_order = st.selectbox("Sort Order", SORT_ORDER_OPTIONS, key="c_sort_order")
            c_limit = st.slider("Results", 1, 100, ITEMS_PER_PAGE, key="c_limit")

        if st.button("Fetch Collection Metrics", key="fetch_collection"):
            params = {
                "blockchain": c_blockchain,
                "time_range": c_time_range,
                "sort_by": c_sort_by,
                "sort_order": c_sort_order,
                "limit": c_limit,
                "offset": st.session_state.page_number * ITEMS_PER_PAGE
            }
            data = fetch_data(COLLECTION_METRICS_ENDPOINT, params)
            if data and "data" in data:
                df = pd.DataFrame(data["data"])
                
                if len(df) > 0:  # Only process if we have data
                    # Display collections grid
                    for i in range(0, len(df), 3):
                        cols = st.columns(3)
                        for j, col in enumerate(cols):
                            if i + j < len(df):
                                with col:
                                    row = df.iloc[i + j]
                                    st.subheader(row.get('game', f"Contract: {row.get('contract_address', 'Unknown')[:10]}..."))
                                    metric_value = row.get(c_sort_by)
                                    is_percentage = any(x in c_sort_by.lower() for x in ['rate', 'change'])
                                    st.write(f"**{c_sort_by}:** {format_metric(metric_value, is_percentage)}")
                                    
                                    with st.expander("View Details"):
                                        for col_name in df.columns:
                                            if col_name not in ['thumbnail_url', 'thumbnail_palette']:
                                                st.write(f"**{col_name}:** {format_metric(row[col_name])}")

                # Pagination controls
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    if st.button("← Previous", key="prev_page") and st.session_state.page_number > 0:
                        st.session_state.page_number -= 1
                        st.experimental_rerun()
                with col2:
                    st.write(f"Page {st.session_state.page_number + 1}")
                with col3:
                    if st.button("Next →", key="next_page") and len(df) == c_limit:
                        st.session_state.page_number += 1
                        st.experimental_rerun()

    with tab3:
        st.header("Trend Analysis")
        # Trend analysis filters
        with st.sidebar:
            st.subheader("Trend Analysis Filters")
            t_blockchain = st.selectbox("Blockchain", BLOCKCHAIN_OPTIONS, key="t_blockchain")
            t_time_range = st.selectbox("Time Range", TIME_RANGE_OPTIONS, key="t_time_range")
            t_sort_by = st.selectbox("Sort By", TREND_SORT_OPTIONS, key="t_sort_by")
            t_sort_order = st.selectbox("Sort Order", SORT_ORDER_OPTIONS, key="t_sort_order")
            t_limit = st.slider("Results", 1, 100, 30, key="t_limit")

        if st.button("Analyze Trends", key="fetch_trends"):
            params = {
                "blockchain": t_blockchain,
                "time_range": t_time_range,
                "sort_by": t_sort_by,
                "sort_order": t_sort_order,
                "limit": t_limit
            }
            data = fetch_data(TREND_ENDPOINT, params)
            if data and "data" in data:
                for i, collection in enumerate(data["data"]):
                    st.subheader(collection.get('game', 'Unknown Game'))
                    
                    # Process maxdate
                    maxdate_str = collection.get('maxdate', '[]')
                    try:
                        maxdate_list = ast.literal_eval(maxdate_str)
                    except:
                        maxdate_list = []
                    
                    dates = []
                    for date_str in maxdate_list:
                        try:
                            cleaned_date_str = date_str.strip("'")
                            dt = datetime.strptime(cleaned_date_str, "%Y-%m-%d %H:%M:%S")
                            dates.append(dt)
                        except:
                            dates.append(None)
                    
                    # Process other metrics
                    metrics_data = {}
                    for metric in ["active_users", "game_interactions", "game_activity", "avg_earnings"]:
                        if metric in collection:
                            metrics_data[metric] = clean_trend_data(collection[metric])
                    
                    # Align metric lengths with dates
                    valid_length = len(dates)
                    for metric in metrics_data:
                        metric_data = metrics_data[metric]
                        if len(metric_data) > valid_length:
                            metrics_data[metric] = metric_data[:valid_length]
                        elif len(metric_data) < valid_length:
                            metrics_data[metric] += [None] * (valid_length - len(metric_data))
                    
                    # Create DataFrame with dates
                    df = pd.DataFrame(metrics_data)
                    df['date'] = dates
                    
                    # Display metrics
                    cols = st.columns(len(metrics_data))
                    for col, (metric, values) in zip(cols, metrics_data.items()):
                        with col:
                            current_val = values[-1] if values else None
                            prev_val = values[-2] if len(values) > 1 else None
                            delta = None
                            if current_val is not None and prev_val is not None and prev_val != 0:
                                delta = ((current_val - prev_val) / prev_val) * 100
                            st.metric(
                                label=metric.replace("_", " ").title(),
                                value=format_metric(current_val),
                                delta=f"{delta:.2f}%" if delta is not None else None
                            )
                    
                    # Display trend charts with dates
                    for metric in metrics_data:
                        fig = px.line(
                            df, x='date', y=metric,
                            title=f"{metric.replace('_', ' ').title()} Trend",
                            labels={'date': 'Date', 'value': metric.replace('_', ' ').title()}
                        )
                        st.plotly_chart(fig, key=f"trend_chart_{i}_{metric}")

if __name__ == "__main__":
    main()
