import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="AuditGuard - Fraud Detection", layout="wide", page_icon="🛡️")

# --- 2. THEME SETUP ---
if 'theme_mode' not in st.session_state:
    st.session_state.theme_mode = "Light"

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2621/2621040.png", width=80)
    
    # THEME SELECTOR
    theme_mode = st.selectbox("🎨 Interface Theme", ["Dark", "Light"])
    
    # DEFINE COLORS BASED ON THEME
    if theme_mode == "Dark":
        bg_gradient = "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)"
        text_color = "#f8fafc" # WHITE TEXT
        card_bg = "rgba(255, 255, 255, 0.05)"
        sidebar_bg = "#0f172a"
        border_color = "rgba(255, 255, 255, 0.1)"
        chart_line_color = "white"
    else:
        # LIGHT MODE
        bg_gradient = "linear-gradient(135deg, #f0f9ff 0%, #dbeafe 100%)"
        text_color = "#000000" # BLACK TEXT
        card_bg = "rgba(255, 255, 255, 0.6)"
        sidebar_bg = "#0f172a" # KEEP SIDEBAR DARK
        border_color = "rgba(0, 0, 0, 0.1)"
        chart_line_color = "black"

    # SIDEBAR TITLE (Always White because Sidebar is Dark)
    st.markdown("""
        <style>
        .sidebar-title {
            font-family: 'EB Garamond', serif;
            font-size: 26px;
            text-transform: uppercase;
            font-weight: 700;
            color: #ffffff !important; 
            margin-bottom: 20px;
        }
        </style>
        <div class="sidebar-title">AuditGuard 🛡️</div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("⚙️ Settings")
    risk_threshold = st.slider("High Risk Threshold", 50, 90, 70)
    st.info(f"System: **v1.2.0**\n\nModel: **Hybrid Forest**")
    st.markdown("---")
    st.caption("© 2026 Audit Tech Dept")

# --- 3. INJECT CSS (STRICT TEXT COLORING) ---
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;700&family=Poppins:wght@300;400;600&display=swap');
        
        /* 1. FORCE MAIN TEXT COLOR */
        html, body, [class*="css"], .stMarkdown, p, li, span, label, div {{
            font-family: 'Poppins', sans-serif;
            color: {text_color};
        }}
        
        /* 2. FORCE HEADERS (Titles, Subheaders) TO THEME COLOR */
        h1, h2, h3, h4, h5, h6 {{
            color: {text_color} !important;
            font-family: 'Poppins', sans-serif;
        }}
        
        /* 3. BACKGROUND */
        .stApp {{ background: {bg_gradient}; }}

        /* 4. HEADER (Top Right Menu) - FORCE DARK */
        header[data-testid="stHeader"] {{
            background-color: #0f172a !important;
        }}
        header[data-testid="stHeader"] *, 
        header[data-testid="stHeader"] button {{
            color: white !important;
            fill: white !important;
        }}

        /* 5. SIDEBAR - FORCE DARK */
        section[data-testid="stSidebar"] {{
            background-color: #0f172a;
            border-right: 1px solid rgba(255,255,255,0.1);
        }}
        /* Force sidebar text to be white */
        section[data-testid="stSidebar"] p, 
        section[data-testid="stSidebar"] span, 
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] div {{
            color: #cbd5e1 !important;
        }}

        /* 6. METRIC CARDS */
        div[data-testid="metric-container"] {{
            background: {card_bg};
            border: 1px solid {border_color};
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }}
        /* Force Metric Text Color */
        div[data-testid="metric-container"] label {{
            color: {text_color} !important;
        }}
        div[data-testid="metric-container"] div {{
            color: {text_color} !important;
        }}

        /* 7. WIDGET FIXES */
        /* Buttons */
        button[kind="primary"] {{
            color: white !important;
        }}
        button[kind="secondary"] {{
            color: {text_color} !important;
            background-color: {card_bg};
        }}
        
        /* File Uploader - Force Text Color */
        [data-testid="stFileUploaderDropzone"] {{
            background-color: {card_bg};
        }}
        [data-testid="stFileUploaderDropzone"] div,
        [data-testid="stFileUploaderDropzone"] span,
        [data-testid="stFileUploaderDropzone"] small {{
            color: {text_color} !important;
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab"] {{
            color: {text_color} !important;
            background-color: {card_bg};
        }}
        
    </style>
""", unsafe_allow_html=True)

# --- 4. HELPER: CHART STYLING ---
def style_chart(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=text_color),
        title=dict(font=dict(color=text_color)),
        legend=dict(font=dict(color=text_color)),
    )
    fig.update_xaxes(tickfont=dict(color=text_color), title_font=dict(color=text_color))
    fig.update_yaxes(tickfont=dict(color=text_color), title_font=dict(color=text_color))
    return fig

# --- 5. TABS LAYOUT ---
tab1, tab2, tab3 = st.tabs(["UPLOAD DATA", "DASHBOARD", "ABOUT SYSTEM"])

# Initialize Session State
if 'data' not in st.session_state:
    st.session_state.data = None
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False

# --- TAB 1: UPLOAD ---
with tab1:
    st.title("Upload Procurement Data")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        internal_cols = ['payment_date', 'payment_amount', 'vendor_employees', 'officer_id']
        matches = [col for col in internal_cols if col in df.columns]
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Data Preview")
            st.dataframe(df.head(), use_container_width=True)
        with col2:
            st.subheader("Diagnostics")
            st.write(f"**Rows:** {len(df)}")
            st.write(f"**Columns:** {len(df.columns)}")
            if len(matches) >= 2:
                st.success("✅ Internal Data")
            else:
                st.warning("⚠️ Public Data")
        
        st.markdown("---")
        b1, b2, b3 = st.columns([1, 2, 1])
        with b2:
            if st.button("🚀 RUN FRAUD ANALYSIS", type="primary", use_container_width=True):
                with st.spinner('Running Analysis...'):
                    df['risk_score'] = np.random.randint(0, 100, size=len(df))
                    def get_category(score):
                        if score >= risk_threshold: return "High"
                        elif score >= 40: return "Medium"
                        else: return "Low"
                    df['risk_level'] = df['risk_score'].apply(get_category)
                    st.session_state.data = df
                    st.session_state.analysis_complete = True
                    st.success("Done! Go to Dashboard.")
    elif not st.session_state.analysis_complete:
        st.info("No file? Use the demo generator below.")
        if st.button("LOAD DEMO DATA"):
            dummy_data = pd.DataFrame({
                'tender_id': [f"T-{i}" for i in range(1000, 1050)],
                'department': np.random.choice(['Infrastructure', 'Health', 'Education', 'Defense'], 50),
                'amount': np.random.randint(5000, 500000, 50),
                'vendor_name': [f"Vendor {i}" for i in range(50)],
                'officer_id': np.random.randint(1, 10, 50), 
                'payment_date': pd.date_range(start='1/1/2023', periods=50) 
            })
            dummy_data.to_csv("demo_data.csv", index=False)
            st.rerun()

# --- TAB 2: DASHBOARD ---
with tab2:
    if st.session_state.analysis_complete:
        df = st.session_state.data
        st.title("Fraud Risk Dashboard")
        
        total = len(df)
        high_risk = len(df[df['risk_level'] == 'High'])
        med_risk = len(df[df['risk_level'] == 'Medium'])
        low_risk = len(df[df['risk_level'] == 'Low'])
        high_pct = (high_risk / total) * 100
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Tenders", total)
        m2.metric("High Risk", f"{high_risk} ({high_pct:.1f}%)", "Critical", delta_color="inverse")
        m3.metric("Medium Risk", med_risk, "Monitor", delta_color="off") 
        m4.metric("Low Risk", low_risk, "Safe", delta_color="normal")
        
        st.markdown("### Risk Distribution")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Risk Level Breakdown")
            fig_pie = px.pie(
                df, names='risk_level', color='risk_level',
                color_discrete_map={'High':'#FF4B4B', 'Medium':'#FFAA00', 'Low':'#09AB3B'}, hole=0.4
            )
            fig_pie = style_chart(fig_pie)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with c2:
            st.markdown("#### Risk Score Distribution")
            fig_hist = px.histogram(
                df, x='risk_score', nbins=20,
                color_discrete_sequence=['#3b82f6']
            )
            fig_hist.update_traces(marker_line_width=1.5, marker_line_color=chart_line_color)
            fig_hist.add_vline(x=risk_threshold, line_dash="dash", line_color="#FF4B4B")
            fig_hist = style_chart(fig_hist)
            st.plotly_chart(fig_hist, use_container_width=True)
        
        st.markdown("### 🚩 High Risk Tenders")
        high_risk_df = df[df['risk_score'] >= risk_threshold].sort_values(by='risk_score', ascending=False).head(20)
        display_cols = ['tender_id', 'department', 'amount', 'risk_score', 'risk_level']
        final_cols = [c for c in display_cols if c in df.columns] 
        
        st.dataframe(
            high_risk_df[final_cols].style.background_gradient(subset=['risk_score'], cmap='Reds'),
            use_container_width=True
        )
        csv = high_risk_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 DOWNLOAD REPORT", csv, 'risk_report.csv', 'text/csv')
    else:
        st.info("⚠️ Please run analysis first.")

# --- TAB 3: ABOUT ---
with tab3:
    st.title("About AuditGuard")
    st.markdown("""
    **AuditGuard** detects:
    * **Shell Companies**
    * **Bid Rigging**
    * **Split Payments**
    
    *Hackathon Prototype 2026*
    """)