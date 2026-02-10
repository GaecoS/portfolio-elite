import streamlit as st
import yfinance as yf
import pandas as pd
import time
import plotly.express as px

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="Portfolio Elite 2026", layout="wide", initial_sidebar_state="collapsed")

# --- 2. IL TUO PORTAFOGLIO ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = [
        {"titolo": "STELLANTIS", "ticker": "STLAM.MI", "qty": 2060, "carico": 12.91, "settore": "Auto"}, 
        {"titolo": "AMD",        "ticker": "AMD.DE",   "qty": 170,  "carico": 122.12, "settore": "Tech"},
        {"titolo": "FINCANTIERI", "ticker": "FCT.MI",  "qty": 570,  "carico": 13.19, "settore": "Ind"},
        {"titolo": "LEONARDO",   "ticker": "LDO.MI",   "qty": 250,  "carico": 38.00, "settore": "Difesa"}, 
        {"titolo": "UNICREDIT",  "ticker": "UCG.MI",   "qty": 500,  "carico": 43.28, "settore": "Finance"},
        {"titolo": "NVIDIA",     "ticker": "NVD.DE",   "qty": 700,  "carico": 93.86, "settore": "Tech"},
        {"titolo": "SCK",        "ticker": "SCK.MI",   "qty": 1000, "carico": 7.74, "settore": "Green", "delistato": True, "prezzo_fissato": 0.939, "target_fissato": 5.0} 
    ]

ACRONIMI = {"STELLANTIS": "STLAM", "UNICREDIT": "UCG", "AMD": "AMD", "LEONARDO": "LDO", "NVIDIA": "NVDA", "FINCANTIERI": "FCT", "SCK": "SCK"}

# --- 3. LOGICA DATI ---
@st.cache_data(ttl=15)
def carica_dati(portfolio):
    risultati = []
    for t in portfolio:
        try:
            if t.get("delistato"): 
                p_att, p_ieri, t_val = t["prezzo_fissato"], t["prezzo_fissato"], t["target_fissato"]
            else:
                tk = yf.Ticker(t["ticker"]); h = tk.history(period="2d")
                p_att, p_ieri = h['Close'].iloc[-1], h['Close'].iloc[-2]
                t_val = 150.0 
            perf = ((p_att - p_ieri) / p_ieri * 100) if p_ieri != 0 else 0.0
            risultati.append({
                "Titolo": ACRONIMI.get(t["titolo"], t["titolo"]), "qty": t["qty"], "carico": t["carico"], "prezzo": p_att, 
                "valore": p_att * t["qty"], "oggi_p": round(float(perf), 2), "oggi_e": (p_att - p_ieri) * t["qty"], 
                "tot_e": (p_att * t["qty"]) - (t["carico"] * t["qty"]), "settore": t["settore"], "target": t_val
            })
        except: pass
    df = pd.DataFrame(risultati)
    if not df.empty: df['Peso %'] = (df['valore'] / df['valore'].sum() * 100)
    return df

df = carica_dati(st.session_state.portfolio)
oggi_eu = df['oggi_e'].sum() if not df.empty else 0
color_session = "#10b981" if oggi_eu >= 0 else "#ef4444"

# --- 4. CSS CHIRURGICO (FIX DEFINITIVO ALTEZZE + SCROLL) ---
st.markdown(f"""
    <style>
    * {{ box-sizing: border-box !important; }}
    [data-testid="stAppViewContainer"] {{ overflow-y: auto !important; overflow-x: hidden !important; }}
    
    /* 1. Spazio Top Calibrato */
    .block-container {{ 
        padding-top: 5rem !important; 
        padding-left: 0.8rem !important; 
        padding-right: 0.8rem !important; 
    }}
    
    /* 2. Celle Top */
    .flex-row {{ display: flex; flex-wrap: nowrap; gap: 8px; width: 100%; margin-bottom: 15px; }}
    .flex-item {{ flex: 1; min-width: 0; padding: 12px 5px !important; }}
    
    /* 3. Asset Details */
    .grid-asset {{ display: grid; grid-template-columns: 1.8fr 1fr 1fr 1fr 1fr 1.2fr; gap: 8px; align-items: center; width: 100%; }}
    .compact-row {{ background: #1e293b; border-radius: 8px; padding: 5px 12px !important; margin-bottom: 4px; border: 1px solid #334155; }}
    
    /* 4. MAPPA: ALTEZZA FISSA MATEMATICA (260px) */
    [data-testid="stPlotlyChart"] > div {{
        border-top: 10px solid {color_session} !important;
        border-radius: 12px !important;
        background-color: #1e293b !important;
        border-bottom: 1px solid #334155 !important;
        border-right: 1px solid #334155 !important;
        border-left: 1px solid #334155 !important;
        
        overflow: hidden !important;
        
        /* Altezza Totale = 250px (Chart) + 10px (Bordo Top) = 260px */
        height: 260px !important; 
        width: 100% !important;
        
        padding: 0 !important;
        margin: 0 !important;
    }}
    
    /* Forza altezza anche sul contenitore interno di Streamlit */
    .stPlotlyChart, .js-plotly-plot {{ overflow: hidden !important; height: 260px !important; }}

    .main-price {{ font-size: clamp(1.4rem, 6vw, 2.2rem) !important; font-weight: 900 !important; color: white; margin: 0; }}
    .asset-name {{ font-size: 1.1rem !important; font-weight: 900 !important; color: white; }}
    .strategy-container {{ display: flex; gap: 10px; align-items: stretch; height: 160px; margin-bottom: 20px; }}
    .strategy-box {{ background: #1e293b; border-radius: 12px; padding: 12px; display: flex; align-items: center; flex: 1; border: 1px solid #334155; }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. RENDER ---
if not df.empty:
    tot_cap, tot_pl = df['valore'].sum(), df['tot_e'].sum()
    
    # A. METRICHE TOP
    st.markdown(f'''
    <div class="flex-row">
        <div class="flex-item" style="background:#1e293b; border-radius:12px; border-bottom:5px solid white; text-align:center;">
            <p style="color:#94a3b8; margin:0; font-size:0.7rem; font-weight:800; text-transform: uppercase;">Value</p>
            <h2 class="main-price">{int(tot_cap):,}</h2>
        </div>
        <div class="flex-item" style="background:#1e293b; border-radius:12px; border-bottom:5px solid {color_session}; text-align:center;">
            <p style="color:#94a3b8; margin:0; font-size:0.7rem; font-weight:800; text-transform: uppercase;">Session</p>
            <h2 class="main-price" style="color:{color_session};">{int(oggi_eu):+}</h2>
        </div>
        <div class="flex-item" style="background:#1e293b; border-radius:12px; border-bottom:5px solid #3b82f6; text-align:center;">
            <p style="color:#94a3b8; margin:0; font-size:0.7rem; font-weight:800; text-transform: uppercase;">Profit</p>
            <h2 class="main-price" style="color:#3b82f6;">{int(tot_pl):,}</h2>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # B. ASSET DETAILS
    st.subheader("Asset Details")
    for _, row in df.iterrows():
        c = "#10b981" if row['oggi_p'] >= 0 else "#ef4444"
        st.markdown(f'''
        <div class="grid-asset compact-row" style="border-left:5px solid {c};">
            <b class="asset-name">{row["Titolo"]}</b>
            <div style="text-align:center; color:#cbd5e1;">{row["qty"]:.0f}</div>
            <div style="text-align:center; color:#cbd5e1;">{row["carico"]:.2f}</div>
            <div style="text-align:center; color:white;">{row["prezzo"]:.2f}</div>
            <div style="text-align:center; color:{c}; font-weight:900;">{row["oggi_p"]:+.2f}%</div>
            <div style="text-align:right; color:{c}; font-weight:900;">{int(row["oggi_e"]):+}€</div>
        </div>
        ''', unsafe_allow_html=True)

    # C. MARKET MAP (AGGIORNATA width='stretch')
    st.subheader("Market Map")
    def get_color(v):
        if v > 1.5: return '#10b981'
        if v > 0: return '#34d399'
        if v > -0.5: return '#475569'
        return '#ef4444'
    df['tile_color'] = df['oggi_p'].apply(get_color)
    
    fig = px.treemap(df, path=['Titolo'], values='valore')
    fig.update_traces(
        marker=dict(colors=df['tile_color'], cornerradius=12),
        root_color="#1e293b",
        texttemplate="<span style='font-size:22px; font-weight:900;'>%{label}</span><br>%{customdata:+.2f}%",
        customdata=df['oggi_p'], textposition="middle center", hoverinfo='none'
    )
    # Altezza 250px esatti per incastrarsi nel box da 260px (con 10px di bordo)
    fig.update_layout(height=250, margin=dict(t=0, l=5, r=5, b=0), paper_bgcolor='rgba(0,0,0,0)')
    
    # FIX ERRORE 2026: width="stretch" invece di use_container_width=True
    st.plotly_chart(fig, width="stretch", config={'displayModeBar': False})

    # D. STRATEGY
    st.subheader("Strategy")
    top_t, flop_t = df.loc[df['oggi_p'].idxmax()], df.loc[df['oggi_p'].idxmin()]
    sec_d = df.groupby('settore')['Peso %'].sum().sort_values(ascending=False)
    colors_p = ['#10b981','#3b82f6','#f59e0b','#ef4444','#8b5cf6']
    conic = ", ".join([f"{colors_p[i%5]} {sum(sec_d.values[:i]):.1f}% {sum(sec_d.values[:i+1]):.1f}%" for i in range(len(sec_d))])
    
    st.markdown(f'''
    <div class="strategy-container">
        <div class="strategy-box" style="border-left:8px solid #3b82f6; width:50%;">
            <div style="width:90px; height:90px; border-radius:50%; flex-shrink:0; background:conic-gradient({conic});"></div>
            <div style="font-size:0.75rem; padding-left:12px; color:#cbd5e1;">
                {"".join([f'<div><span style="color:{colors_p[i%5]};">●</span> {s}: <b>{v:.0f}%</b></div>' for i, (s,v) in enumerate(sec_d.items())])}
            </div>
        </div>
        <div style="flex: 1; display: flex; flex-direction: column; gap: 8px;">
            <div class="strategy-box" style="border-left:8px solid #10b981; height:100%; justify-content:space-between; padding:0 15px;">
                <span><small style="color:#10b981; font-weight:bold;">BEST</small><br><b>{top_t["Titolo"]}</b></span>
                <span style="font-size:1.4rem; font-weight:900; color:#10b981;">{top_t["oggi_p"]:+.2f}%</span>
            </div>
            <div class="strategy-box" style="border-left:8px solid #ef4444; height:100%; justify-content:space-between; padding:0 15px;">
                <span><small style="color:#ef4444; font-weight:bold;">WORST</small><br><b>{flop_t["Titolo"]}</b></span>
                <span style="font-size:1.4rem; font-weight:900; color:#ef4444;">{flop_t["oggi_p"]:+.2f}%</span>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # E. TARGET PRIZE 2026
    st.subheader("Target Prize 2026")
    for _, row in df.iterrows():
        prog = min(max((row['prezzo']/row['target'])*100, 0), 100)
        st.markdown(f'''
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:#cbd5e1; margin-bottom:2px;">
                <span><b>{row["Titolo"]}</b></span>
                <span style="color:#fbbf24; font-weight:bold;">{prog:.1f}%</span>
            </div>
            <div style="width:100%; background:#0f172a; height:10px; border-radius:10px; margin-bottom:12px; border:1px solid #334155; overflow:hidden;">
                <div style="width:{prog}%; background:linear-gradient(90deg, #f59e0b, #fbbf24); height:100%;"></div>
            </div>
        ''', unsafe_allow_html=True)

time.sleep(15)
st.rerun()