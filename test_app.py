import streamlit as st
import requests
import time
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_lottie import st_lottie
from typing import List, Tuple, Dict, Optional, Any

# =========================
# Constants & Configuration
# =========================
API_KEY = "49d8e94d834d3810711e4980"  # Consider moving to secrets in production
BASE_URL = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD"
LOTTIE_URL = "https://assets1.lottiefiles.com/packages/lf20_ktwnwv5m.json"
CACHE_TTL = 3600  # 1 hour cache
MAX_HISTORY_ENTRIES = 50

# =========================
# Page Configuration
# =========================
st.set_page_config(
    page_title="Global Currency Converter Pro",
    page_icon="💱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Type Definitions
# =========================
CurrencyPair = Tuple[str, str]
ConversionHistory = Dict[str, Any]

# =========================
# Session State Initialization
# =========================
def initialize_session_state():
    """Initialize all session state variables with defaults"""
    defaults = {
        "theme_dark": False,
        "lang": "en",
        "favorites": [],
        "history": [],
        "last_api_call": None,
        "api_error_count": 0
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# =========================
# i18n (Multi-language Support)
# =========================
LANG = {
    "en": {
        "app_title": "Global Currency Converter Pro",
        "subtitle": "Advanced currency conversion with comprehensive analytics",
        "amount": "Amount",
        "from": "From",
        "to": "To",
        "convert_now": "Convert Now",
        "converting": "Converting...",
        "final_conversion": "Final Conversion",
        "rate_increased": "📈 Rate increased by {pct:.2f}% since yesterday",
        "rate_decreased": "📉 Rate decreased by {pct:.2f}% since yesterday",
        "rate_stable": "🔄 Exchange rate remained stable since yesterday",
        "trend_header": "📊 Exchange Rate Analytics",
        "footer_text": "Exchange rates are updated in real-time using ExchangeRate-API",
        "last_updated": "Last updated",
        "dark_mode": "Dark mode",
        "language": "Language",
        "favorites_title": "Favorites",
        "add_favorite": "Add current pair to favorites",
        "remove_favorite": "Remove selected favorite",
        "favorites_empty": "No favorites yet.",
        "use_favorite": "Use selected favorite",
        "favorites_help": "Save your frequently used currency pairs for quick access.",
        "history_title": "Conversion History",
        "history_help": "Your recent conversions in this session.",
        "clear_history": "Clear history",
        "failed_data": "Failed to get conversion data. Please try again.",
        "error_occurred": "An error occurred",
        "api_limit": "⚠️ API rate limit reached. Using cached data.",
        "added_favorite": "⭐ Added to favorites",
        "removed_favorite": "🗑️ Removed from favorites",
        "history_cleared": "History cleared"
    }
}

def t(key: str, **fmt: Any) -> str:
    """Get translated text with optional formatting"""
    lang_data = LANG.get(st.session_state.lang, LANG["en"])
    txt = lang_data.get(key, LANG["en"].get(key, key))
    return txt.format(**fmt) if fmt else txt

# =========================
# API Functions with Error Handling
# =========================
def safe_api_call(url: str, timeout: int = 10) -> Optional[Dict]:
    """Make API call with proper error handling"""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        st.session_state.last_api_call = datetime.now()
        st.session_state.api_error_count = 0
        return response.json()
    except requests.exceptions.RequestException as e:
        st.session_state.api_error_count += 1
        if st.session_state.api_error_count > 3:
            st.warning(t("api_limit"))
        return None

@st.cache_data(ttl=CACHE_TTL)
def get_currencies() -> List[str]:
    """Get list of available currencies with fallback"""
    data = safe_api_call(BASE_URL)
    if data and 'conversion_rates' in data:
        currencies = list(data['conversion_rates'].keys())
        currencies.append('USD')  # Ensure USD is included
        return sorted(currencies)
    return ['USD', 'EUR', 'JPY', 'GBP', 'AUD', 'CAD', 'CHF', 'CNY', 'INR']

@st.cache_data(ttl=CACHE_TTL)
def get_previous_rate(from_curr: str, to_curr: str) -> Optional[float]:
    """Get yesterday's exchange rate"""
    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/history/{from_curr}/{yesterday}"
        data = safe_api_call(url)
        return data.get('conversion_rates', {}).get(to_curr) if data else None
    except Exception:
        return None

def load_lottie_animation(url: str) -> Optional[Dict]:
    """Load Lottie animation with error handling"""
    data = safe_api_call(url, timeout=8)
    return data if data else None

# =========================
# UI Components
# =========================
def setup_theme(dark: bool) -> str:
    """Configure theme and return Plotly template name"""
    theme = {
        "dark": {
            "bg": "linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%)",
            "text": "#eaeaea",
            "label": "#ffffff",
            "card_bg": "#111824",
            "shadow": "rgba(0,0,0,0.4)",
            "heading": "#ffffff",
            "button_from": "#8E2DE2",
            "button_to": "#4A00E0",
            "metric_color": "#eaeaea",
            "subtitle": "#cfd8dc",
            "border": "#263238",
            "plotly_template": "plotly_dark"
        },
        "light": {
            "bg": "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)",
            "text": "#222",
            "label": "#222",
            "card_bg": "#ffffff",
            "shadow": "rgba(0,0,0,0.1)",
            "heading": "#2c3e50",
            "button_from": "#6a11cb",
            "button_to": "#2575fc",
            "metric_color": "#2c3e50",
            "subtitle": "#444",
            "border": "#e0e0e0",
            "plotly_template": "plotly_white"
        }
    }
    
    mode = "dark" if dark else "light"
    colors = theme[mode]
    
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
        html, body, [class*="css"] {{
            font-family: 'Poppins', sans-serif;
            color: {colors['text']};
        }}
        .main {{
            background: {colors['bg']};
        }}
        label {{
            color: {colors['label']} !important;
            font-weight: 600 !important;
        }}
        div[data-testid="stNumberInput"] label p,
        div[data-testid="stSelectbox"] label p,
        div[data-testid="stTextInput"] label p {{
            color: {colors['label']} !important;
            font-weight: 600 !important;
        }}
        h1, h2, h3, .stTitle {{
            color: {colors['heading']} !important;
        }}
        .stButton>button {{
            background: linear-gradient(to right, {colors['button_from']}, {colors['button_to']});
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px {colors['shadow']};
            border: 1px solid {colors['border']};
        }}
        .stButton>button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 8px {colors['shadow']};
        }}
        .currency-card {{
            background: {colors['card_bg']};
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 6px 18px {colors['shadow']};
            transition: all 0.3s ease;
            margin-bottom: 20px;
            border: 1px solid {colors['border']};
        }}
        .stMetric {{
            color: {colors['metric_color']} !important;
        }}
        .subtitle {{
            color: {colors['subtitle']};
            margin-bottom: 30px;
        }}
    </style>
    """, unsafe_allow_html=True)
    
    return colors['plotly_template']

# =========================
# Visualization Functions
# =========================
def render_trend_chart(from_curr: str, to_curr: str, current_rate: float, template: str):
    """Render multiple historical trend visualizations"""
    st.subheader("📊 Exchange Rate Analytics")
    
    # Create sample historical data (replace with real API data in production)
    dates = pd.date_range(end=datetime.now(), periods=30).tolist()
    rates = [current_rate * (0.98 + 0.04 * (i/30)) for i in range(30)]
    df = pd.DataFrame({'Date': dates, 'Rate': rates, 'Day': range(30)})
    
    # Tab layout for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["Trend Line", "Candlestick", "Histogram", "Comparison"])
    
    with tab1:
        # 1. Main Line Chart with Moving Average
        fig1 = go.Figure()
        
        # Add actual rate line
        fig1.add_trace(go.Scatter(
            x=df['Date'], 
            y=df['Rate'],
            mode='lines',
            name='Exchange Rate',
            line=dict(color='#4CAF50', width=3))
        )
        
        # Add 7-day moving average
        fig1.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Rate'].rolling(7).mean(),
            mode='lines',
            name='7-Day Avg',
            line=dict(color='#FF9800', width=2, dash='dot'))
        )
        
        fig1.update_layout(
            title=f"{from_curr} to {to_curr} - 30 Day Trend with Moving Average",
            template=template,
            hovermode="x unified",
            showlegend=True,
            xaxis_title="Date",
            yaxis_title=f"1 {from_curr} in {to_curr}",
            height=400
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with tab2:
        # 2. Candlestick Chart (Weekly)
        weekly_df = df.iloc[::7]  # Sample weekly data
        fig2 = go.Figure(data=[go.Candlestick(
            x=weekly_df['Date'],
            open=weekly_df['Rate']*0.99,
            high=weekly_df['Rate']*1.01,
            low=weekly_df['Rate']*0.98,
            close=weekly_df['Rate'],
            increasing_line_color='#4CAF50',
            decreasing_line_color='#F44336'
        )])
        fig2.update_layout(
            title=f"Weekly Price Movements ({from_curr} to {to_curr})",
            template=template,
            height=400
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    with tab3:
        # 3. Rate Distribution Histogram
        fig3 = px.histogram(
            df, 
            x='Rate',
            nbins=15,
            title=f"Distribution of {from_curr} to {to_curr} Rates",
            template=template
        )
        fig3.update_layout(
            height=400,
            xaxis_title=f"1 {from_curr} in {to_curr}",
            yaxis_title="Frequency"
        )
        st.plotly_chart(fig3, use_container_width=True)
    
    with tab4:
        # 4. Comparison with other major currencies
        st.info("Comparing with major currencies (sample data)")
        major_currencies = ['EUR', 'GBP', 'JPY', 'AUD', 'CAD']
        comparison_data = []
        
        for curr in major_currencies:
            if curr != from_curr:
                # In a real app, you would fetch these rates from the API
                comparison_data.append({
                    'Currency': curr,
                    'Rate': current_rate * (0.8 + 0.4 * (major_currencies.index(curr)/len(major_currencies)))
                })
        
        comparison_df = pd.DataFrame(comparison_data)
        
        fig4 = px.bar(
            comparison_df,
            x='Currency',
            y='Rate',
            color='Currency',
            title=f"{from_curr} Rates Compared to Major Currencies",
            template=template
        )
        fig4.update_layout(
            height=400,
            yaxis_title=f"1 {from_curr} in Target Currency",
            showlegend=False
        )
        st.plotly_chart(fig4, use_container_width=True)

def render_additional_visualizations(from_curr: str, to_curr: str, rate: float):
    """Render additional financial visualizations"""
    st.subheader("📈 Advanced Financial Metrics")
    
    # Create sample volatility data
    dates = pd.date_range(end=datetime.now(), periods=30).tolist()
    volatility = [0.5 + 0.3 * (i/30) for i in range(30)]
    df = pd.DataFrame({'Date': dates, 'Volatility': volatility})
    
    # 1. Volatility Chart
    fig1 = px.area(
        df, 
        x='Date', 
        y='Volatility',
        title=f"{from_curr}/{to_curr} Estimated Volatility",
        template=setup_theme(st.session_state.theme_dark)
    )
    fig1.update_layout(height=300)
    st.plotly_chart(fig1, use_container_width=True)
    
    # 2. Rate Change Probability
    st.markdown("#### 💹 Rate Change Probability (Next 7 Days)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Increase >1%", "65%", "5%")
    with col2:
        st.metric("Remain Stable", "25%", "-3%")
    with col3:
        st.metric("Decrease >1%", "10%", "2%")

# =========================
# Conversion Logic
# =========================
def perform_conversion(from_curr: str, to_curr: str, amount: float) -> Optional[Tuple[float, float]]:
    """Perform currency conversion with error handling"""
    url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/pair/{from_curr}/{to_curr}/{amount}"
    data = safe_api_call(url)
    
    if not data or 'conversion_result' not in data:
        st.error(t("failed_data"))
        return None
    
    return data['conversion_result'], data['conversion_rate']

def render_conversion_result(from_curr: str, to_curr: str, amount: float, result: float, rate: float):
    """Display conversion result with animations and rate change info"""
    # Animated result display
    with st.empty():
        for percent in range(0, 101, 5):
            display_amount = result * percent / 100
            st.metric(
                label=f"{amount} {from_curr} =",
                value=f"{display_amount:.2f} {to_curr}",
                delta=None
            )
            time.sleep(0.02)
    
    # Display final conversion in black
    st.markdown(
        f"""
        <div style='color: black; font-size: 16px; font-weight: bold; margin: 10px 0;'>
            {t('final_conversion')}: {amount} {from_curr} = {result:.2f} {to_curr}
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Rate change notification
    previous_rate = get_previous_rate(from_curr, to_curr)
    if previous_rate:
        rate_change = ((rate - previous_rate) / previous_rate) * 100
        if rate_change > 0:
            st.success(t("rate_increased", pct=abs(rate_change)))
        elif rate_change < 0:
            st.warning(t("rate_decreased", pct=abs(rate_change)))
        else:
            st.info(t("rate_stable"))
    
    # Render all visualizations
    render_trend_chart(from_curr, to_curr, rate, setup_theme(st.session_state.theme_dark))
    render_additional_visualizations(from_curr, to_curr, rate)
    
    # Add to history
    st.session_state.history.append({
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "From": from_curr,
        "To": to_curr,
        "Amount": amount,
        "Rate": rate,
        "Result": round(result, 4)
    })
    st.session_state.history = st.session_state.history[-MAX_HISTORY_ENTRIES:]

# =========================
# Sidebar Components
# =========================
def render_sidebar():
    """Render all sidebar components"""
    st.sidebar.subheader("⚙️ Settings")
    
    # Theme toggle
    st.session_state.theme_dark = st.sidebar.toggle(
        t("dark_mode"), 
        value=st.session_state.theme_dark,
        key="theme_toggle"
    )
    
    # Language selection
    st.session_state.lang = st.sidebar.selectbox(
        t("language"), 
        ["en"],  # Simplified to English only for this example
        index=0,
        key="language_select"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader(f"⭐ {t('favorites_title')}")
    st.sidebar.caption(t("favorites_help"))
    
    # Favorites management
    fav_options = (
        [f"{f} → {t}" for f, t in st.session_state.favorites] 
        if st.session_state.favorites 
        else [t("favorites_empty")]
    )
    
    selected_fav = st.sidebar.selectbox(
        " ", 
        fav_options, 
        index=0, 
        label_visibility="collapsed",
        key="favorites_select"
    )
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        use_selected = st.button(
            f"✅ {t('use_favorite')}", 
            disabled=not st.session_state.favorites,
            use_container_width=True,
            key="use_favorite_btn"
        )
    with col2:
        remove_selected = st.button(
            f"🗑️ {t('remove_favorite')}", 
            disabled=not st.session_state.favorites,
            use_container_width=True,
            key="remove_favorite_btn"
        )
    
    return selected_fav, use_selected, remove_selected

# =========================
# History Section
# =========================
def render_history():
    """Render conversion history section"""
    st.markdown("---")
    hist_col1, hist_col2 = st.columns([3, 1])
    with hist_col1:
        st.subheader(f"🕒 {t('history_title')}")
        st.caption(t("history_help"))
    with hist_col2:
        clear_hist = st.button(
            f"🧹 {t('clear_history')}", 
            use_container_width=True,
            key="clear_history_btn"
        )
    
    if clear_hist:
        st.session_state.history = []
        st.success(t("history_cleared"))
    
    if st.session_state.history:
        hist_df = pd.DataFrame(st.session_state.history)
        st.dataframe(
            hist_df.sort_values("Timestamp", ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Timestamp": st.column_config.DatetimeColumn(
                    "Timestamp",
                    format="YYYY-MM-DD HH:mm:ss"
                ),
                "From": "From",
                "To": "To",
                "Amount": st.column_config.NumberColumn(
                    "Amount",
                    format="%.2f"
                ),
                "Rate": st.column_config.NumberColumn(
                    "Rate",
                    format="%.4f"
                ),
                "Result": st.column_config.NumberColumn(
                    "Result",
                    format="%.4f"
                )
            }
        )
    else:
        st.info("—")

# =========================
# Main App Layout
# =========================
def main():
    # Setup theme and get plotly template
    plotly_template = setup_theme(st.session_state.theme_dark)
    
    # Load animation
    lottie_animation = load_lottie_animation(LOTTIE_URL)
    
    # Header
    col1, col2 = st.columns([3, 2])
    with col1:
        st.title(f"💱 {t('app_title')}")
        st.markdown(f'<div class="subtitle">{t("subtitle")}</div>', unsafe_allow_html=True)
    with col2:
        if lottie_animation:
            st_lottie(lottie_animation, height=200, key="currency_animation")
    
    # Get currency list
    currency_list = get_currencies()
    
    # Sidebar
    selected_fav, use_selected, remove_selected = render_sidebar()
    
    # Handle favorites actions
    current_pair = None
    default_from = 'USD'
    default_to = 'EUR'
    
    if use_selected and st.session_state.favorites:
        try:
            idx = [f"{f} → {t}" for f, t in st.session_state.favorites].index(selected_fav)
            default_from, default_to = st.session_state.favorites[idx]
        except (ValueError, IndexError):
            pass
    
    # Conversion Card
    with st.container():
        st.markdown('<div class="currency-card">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            amount = st.number_input(
                t("amount"), 
                min_value=0.01, 
                value=1.0, 
                step=0.01,
                key="amount_input"
            )
        with col2:
            try:
                from_index = currency_list.index(default_from)
            except ValueError:
                from_index = 0
            from_curr = st.selectbox(
                t("from"), 
                currency_list, 
                index=from_index,
                key="from_currency_select"
            )
        with col3:
            try:
                to_index = currency_list.index(default_to)
            except ValueError:
                to_index = 0 if len(currency_list) == 0 else min(1, len(currency_list)-1)
            to_curr = st.selectbox(
                t("to"), 
                currency_list, 
                index=to_index,
                key="to_currency_select"
            )
        
        current_pair = (from_curr, to_curr)
        
        # Favorites management
        fav_col1, fav_col2 = st.columns([1, 1])
        with fav_col1:
            add_fav = st.button(
                f"⭐ {t('add_favorite')}", 
                use_container_width=True,
                key="add_favorite_btn"
            )
        with fav_col2:
            remove_current = st.button(
                f"🗑️ {t('remove_favorite')}", 
                use_container_width=True,
                key="remove_current_favorite_btn"
            )
        
        convert_btn = st.button(
            t("convert_now"), 
            use_container_width=True,
            key="convert_now_btn"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Handle favorites actions
    if add_fav and current_pair not in st.session_state.favorites:
        st.session_state.favorites.append(current_pair)
        st.success(t("added_favorite"))
    
    if remove_selected and st.session_state.favorites:
        try:
            idx = [f"{f} → {t}" for f, t in st.session_state.favorites].index(selected_fav)
            pair = st.session_state.favorites[idx]
            st.session_state.favorites.remove(pair)
            st.success(t("removed_favorite"))
        except (ValueError, IndexError):
            st.warning("Could not remove the selected favorite")
    
    if remove_current and current_pair in st.session_state.favorites:
        st.session_state.favorites.remove(current_pair)
        st.success(t("removed_favorite"))
    
    # Perform conversion
    if convert_btn:
        with st.spinner(t("converting")):
            conversion_result = perform_conversion(from_curr, to_curr, amount)
            
            if conversion_result:
                result, rate = conversion_result
                render_conversion_result(from_curr, to_curr, amount, result, rate)
    
    # History section
    render_history()
    
    # Footer
    st.markdown(f"""
    <div style="text-align: center; margin-top: 30px; font-size: 14px; opacity: 0.9;">
        <p>{t("footer_text")}</p>
        <p>{t("last_updated")}: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()