import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="Portfolio Elite 2026", layout="wide", initial_sidebar_state="collapsed")

# --- 2. LOGICA DATI CON TARGET ANALISTI ---
@st.cache_data(ttl=900) # Cache di 15 minuti per non bloccare il server
def carica_dati():
    portfolio = [
        {"titolo": "STELLANTIS", "ticker": "STLAM.MI", "qty": 2060, "carico": 12.91}, 
        {"titolo": "AMD",        "ticker": "AMD.DE",   "qty": 170,  "carico": 122.12},
        {"titolo": "FINCANTIERI", "ticker": "FCT.MI",  "qty": 570,  "carico": 13.19},
        {"titolo": "LEONARDO",   "ticker": "LDO.MI",   "qty": 250,  "carico": 38.00}, 
        {"titolo": "UNICREDIT",  "ticker": "UCG.MI",   "qty": 500,  "carico": 43.28},
        {"titolo": "NVIDIA",     "ticker": "NVD.DE",   "qty": 700,  "carico": 93.86},
        {"titolo": "SCK",        "ticker": "SCK.MI",   "qty": 1000, "carico": 7.74, "delistato": True, "prezzo_fissato": 0.939, "target_fissato": 5.0} 
    ]
    
    ACRONIMI = {"STELLANTIS": "STLAM", "UNICREDIT": "UCG", "AMD": "AMD", "LEONARDO": "LDO", "NVIDIA": "NVDA", "FINCANTIERI": "FCT", "SCK": "SCK"}
    risultati = []

    for t in portfolio:
        try:
            tk = yf.Ticker(t["ticker"])
            if t.get("delistato"): 
                p_att, p_ieri, t_val = t["prezzo_fissato"], t["prezzo_fissato"], t["target_fissato"]
            else:
                h = tk.history(period="2d")
                p_att, p_ieri = h['Close'].iloc[-1], h['Close'].iloc[-2]
                # Recupero Target Analisti (Yahoo Finance)
                t_val = tk.info.get("targetMeanPrice", p_att * 1.2)
                
            perf = ((p_att - p_ieri) / p_ieri * 100) if p_ieri != 0 else 0.0
            risultati.append({
                "Titolo": ACRONIMI.get(t["titolo"], t["titolo"]), "qty": t["qty"], "carico": t["carico"], "prezzo": p_att, 
                "valore": p_att * t["qty"], "oggi_p": round(float(perf), 2), "oggi_e": (p_att - p_ieri) * t["qty"], 
                "tot_e": (p_att * t["qty"]) - (t["carico"] * t["qty"]), "target": t_val
            })
        except: pass
    return pd.DataFrame(risultati)

df = carica_dati()
oggi_eu = df['oggi_e'].sum() if not df.empty else 0
color_session = "#10b981" if oggi_eu >= 0 else "#ef4444"

# --- 3. CSS (STRUTTURA SOLIDA) ---
st.markdown(f"""
    <style>
    * {{ box-sizing: border-box !important; }}
    [data-testid="stAppViewContainer"] {{ overflow-x: hidden !important; overflow-y: auto !important; }}
    .block-container {{ padding: 6rem 0.6rem 5rem 0.6rem !important; }}
    
    /* Bordo colorato e contenitore mappa */
    [data-testid="stPlotlyChart"] > div {{
        border-top: 10px solid {color_session} !important;
        border-radius: 12px !important;
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        overflow: hidden !important;
    }}
    
    .flex-row {{ display: flex; flex-wrap: nowrap; gap: 8px; margin-bottom: 15px; }}
    .flex-item {{ flex: 1; padding: 12px 5px !important; background: #1e293b; border-radius: 12px; text-align: center; }}
    .main-price {{ font-size: 1.6rem !important; font-weight: 900 !important; color: white; margin: 0; }}
    .compact-row {{ background: #1e293b; border-radius: 8px; padding: 6px 12px; margin-bottom: 4px; border: 1px solid #334155; display: grid; grid-template-columns: 1.8fr 1fr 1fr 1fr 1fr 1.2fr; gap: 8px; align-items: center; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. RENDER ---
if not df.empty:
    # Metriche
    st.markdown(f'''<div class="flex-row">
        <div class="flex-item" style="border-bottom:5px solid white;"><small style="color:#94a3b8;">VALUE</small><div class="main-price">{int(df["valore"].sum()):,}</div></div>
        <div class="flex-item" style="border-bottom:5px solid {color_session};"><small style="color:#94a3b8;">SESSION</small><div class="main-price" style="color:{color_session};">{int(oggi_eu):+}</div></div>
        <div class="flex-item" style="border-bottom:5px solid #3b82f6;"><small style="color:#94a3b8;">PROFIT</small><div class="main-price" style="color:#3b82f6;">{int(df["tot_e"].sum()):,}</div></div>
    </div>''', unsafe_allow_html=True)

    # Asset
    st.subheader("Asset Details")
    for _, r in df.iterrows():
        c = "#10b981" if r['oggi_p'] >= 0 else "#ef4444"
        st.markdown(f'''<div class="compact-row" style="border-left:5px solid {c};">
            <b style="color:white;">{r["Titolo"]}</b><div style="text-align:center; color:#cbd5e1;">{r["qty"]:.0f}</div>
            <div style="text-align:center; color:#cbd5e1;">{r["carico"]:.2f}</div><div style="text-align:center; color:white;">{r["prezzo"]:.2f}</div>
            <div style="text-align:center; color:{c}; font-weight:900;">{r["oggi_p"]:+.2f}%</div><div style="text-align:right; color:{c}; font-weight:900;">{int(r["oggi_e"]):+}€</div>
        </div>''', unsafe_allow_html=True)

    # Mappa
    st.subheader("Market Map")
    fig = px.treemap(df, path=['Titolo'], values='valore')
    fig.update_traces(marker=dict(cornerradius=12, colorscale=[[0, '#ef4444'], [0.5, '#475569'], [1, '#10b981']]), 
                      texttemplate="<b>%{label}</b><br>%{customdata:+.2f}%", customdata=df['oggi_p'], textposition="middle center")
    fig.update_layout(height=320, margin=dict(t=5, l=5, r=10, b=30), paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, width="stretch", config={'displayModeBar': False})

    # Target Analysts
    st.subheader("Target Prize (Yahoo Analysts)")
    for _, r in df.iterrows():
        p = min(max((r['prezzo']/r['target'])*100, 0), 100)
        st.markdown(f'''<div style="display:flex; justify-content:space-between; font-size:0.8rem; color:#cbd5e1;"><span><b>{r["Titolo"]}</b> (Target: {r["target"]:.2f})</span><span>{p:.1f}%</span></div>
            <div style="width:100%; background:#0f172a; height:10px; border-radius:10px; margin-bottom:12px; border:1px solid #334155; overflow:hidden;">
                <div style="width:{p}%; background:linear-gradient(90deg, #f59e0b, #fbbf24); height:100%;"></div>
            </div>''', unsafe_allow_html=True)