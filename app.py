import streamlit as st
import yfinance as yf
import pandas as pd
import time

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="Portfolio Elite 2026", layout="wide")

# CSS AGGRESSIVO: Font dinamici e layout bloccato per Smartphone
st.markdown("""
    <style>
    .flex-row { display: flex; flex-wrap: nowrap; gap: 8px; width: 100%; align-items: stretch; margin-bottom: 15px; }
    .flex-item { flex: 1; min-width: 0; }
    .grid-asset { display: grid; grid-template-columns: 1.8fr 1fr 1fr 1fr 1fr 1.2fr; gap: 8px; align-items: center; width: 100%; }
    
    /* RIGHE ULTRA COMPATTE MA CON FONT LEGGIBILI */
    .compact-row { 
        background: #1e293b; 
        border-radius: 4px; 
        padding: 2px 12px !important; 
        margin-bottom: 2px !important; 
        min-height: 32px !important;
        line-height: 1.2 !important;
    }
    
    /* FONT DINAMICI */
    .main-price { font-size: clamp(1.2rem, 5vw, 2.2rem) !important; font-weight: 900 !important; }
    .asset-name { font-size: clamp(0.85rem, 2vw, 1rem) !important; font-weight: 800 !important; }
    
    [data-testid="column"] { flex: 1 1 0% !important; min-width: 0 !important; }
    h2 { line-height: 1.1 !important; }
    
    .pie-chart { 
        width: 110px; height: 110px; aspect-ratio: 1 / 1; border-radius: 50%; 
        border: 2px solid #0f172a; flex-shrink: 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. IL TUO PORTAFOGLIO BASE ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = [
        {"titolo": "STELLANTIS", "ticker": "STLAM.MI", "qty": 2060, "carico": 12.91, "settore": "Auto"}, 
        {"titolo": "AMD",        "ticker": "AMD.DE",   "ticker_usa": "AMD", "qty": 170,  "carico": 122.12, "settore": "Tech"},
        {"titolo": "FINCANTIERI", "ticker": "FCT.MI",  "qty": 570,  "carico": 13.19, "settore": "Ind"},
        {"titolo": "LEONARDO",   "ticker": "LDO.MI",   "qty": 250,  "carico": 38.00, "settore": "Difesa"}, 
        {"titolo": "UNICREDIT",  "ticker": "UCG.MI",   "qty": 500,  "carico": 43.28, "settore": "Finance"},
        {"titolo": "NVIDIA",     "ticker": "NVD.DE",   "ticker_usa": "NVDA", "qty": 700,  "carico": 93.86, "settore": "Tech"},
        {"titolo": "SCK",        "ticker": "SCK.MI",   "qty": 1000, "carico": 7.74, "settore": "Green", "delistato": True, "prezzo_fissato": 0.939, "target_fissato": 5.0} 
    ]

ACRONIMI = {"NVIDIA": "NVDA", "UNICREDIT": "UCG", "AMD": "AMD", "LEONARDO": "LDO", "STELLANTIS": "STLAM", "FINCANTIERI": "FCT", "SCK": "SCK"}

# --- 3. FUNZIONI ---
def format_pure_num(n): return f"{int(round(n, 0)):,}".replace(",", ".")
def format_euro(n): return f"€ {int(round(n, 0)):,}".replace(",", ".")

def get_heatmap_style(val, delistato):
    if delistato: return 'background: rgba(100, 116, 139, 0.1); color: #94a3b8; padding: 1px 4px; border-radius: 3px; font-size: 0.75rem;'
    color = "#10b981" if val >= 0 else "#ef4444"
    bg = f"rgba(16, 185, 129, 0.25)" if val >= 0 else f"rgba(239, 68, 68, 0.25)"
    return f'background: {bg}; color: {color}; padding: 1px 6px; border-radius: 3px; font-weight: 800; font-size: 0.8rem; border: 1px solid {color}33;'

@st.cache_data(ttl=43200) 
def recupera_target_online(p):
    targets = {}
    for t in p:
        if t.get("delistato"): continue
        try:
            tk = yf.Ticker(t["ticker"]); val = tk.info.get('targetMeanPrice')
            if not val and "ticker_usa" in t: val = yf.Ticker(t["ticker_usa"]).info.get('targetMeanPrice')
            targets[t["ticker"]] = val
        except: targets[t["ticker"]] = None
    return targets

@st.cache_data(ttl=15)
def carica_dati(portfolio):
    target_map = recupera_target_online(portfolio)
    risultati = []
    for t in portfolio:
        try:
            if t.get("delistato"): p_att, p_ieri, target_val = t["prezzo_fissato"], t["prezzo_fissato"], t["target_fissato"]
            else:
                tk = yf.Ticker(t["ticker"]); h = tk.history(period="5d")
                p_att, p_ieri, target_val = h['Close'].iloc[-1], h['Close'].iloc[-2], target_map.get(t["ticker"])
            if not target_val: target_val = p_att
            val, inv = p_att * t["qty"], t["carico"] * t["qty"]
            risultati.append({
                "Titolo": ACRONIMI.get(t["titolo"], t["titolo"]), "qty": t["qty"], "carico": t["carico"], "prezzo": p_att, 
                "valore": val, "oggi_p": ((p_att - p_ieri) / p_ieri * 100) if p_ieri != 0 else 0,
                "oggi_e": (p_att - p_ieri) * t["qty"], "tot_e": val - inv, "settore": t["settore"], 
                "target": target_val, "valore_target": target_val * t["qty"], "delistato": t.get("delistato", False)
            })
        except: pass
    df = pd.DataFrame(risultati)
    if not df.empty: df['Peso %'] = (df['valore'] / df['valore'].sum() * 100)
    return df

df = carica_dati(st.session_state.portfolio)

# --- 4. RENDER ---
if not df.empty:
    tot_cap, tot_target = df['valore'].sum(), df['valore_target'].sum()
    guadagno_futuro, oggi_eu, tot_pl = tot_target - tot_cap, df['oggi_e'].sum(), df['tot_e'].sum()
    bg_o, tx_o = ("#064e3b", "#10b981") if oggi_eu >= 0 else ("#450a0a", "#ef4444")

    # A. TOP METRICS
    st.markdown(f"""
    <div class="flex-row">
        <div class="flex-item" style="background: #1e293b; border-radius: 10px; border-bottom: 5px solid white; padding: 15px; text-align: center;">
            <p style="color: #cbd5e1; margin: 0; font-size: 0.85rem; text-transform: uppercase; font-weight: 800;">Portfolio Value</p>
            <h2 class="main-price" style="color: white; margin: 5px 0;">{format_pure_num(tot_cap)}</h2>
        </div>
        <div class="flex-item" style="background: {bg_o}; border-radius: 10px; border-bottom: 5px solid {tx_o}; padding: 15px; text-align: center;">
            <p style="color: #cbd5e1; margin: 0; font-size: 0.85rem; text-transform: uppercase; font-weight: 800;">Session Impact</p>
            <h2 class="main-price" style="color: {tx_o}; margin: 5px 0;">{format_pure_num(oggi_eu)}</h2>
        </div>
        <div class="flex-item" style="background: #1e293b; border-radius: 10px; border-bottom: 5px solid #3b82f6; padding: 15px; text-align: center;">
            <p style="color: #cbd5e1; margin: 0; font-size: 0.85rem; text-transform: uppercase; font-weight: 800;">Total Profit</p>
            <h2 class="main-price" style="color: #3b82f6; margin: 5px 0;">{format_pure_num(tot_pl)}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # B. ASSET DETAILS
    st.subheader("Asset Details")
    st.markdown('<div class="grid-asset" style="padding:0 15px; margin-bottom:5px; color:#94a3b8; font-size:0.7rem; font-weight:800; text-transform:uppercase;"><div>Titolo</div><div style="text-align:center">Quantità</div><div style="text-align:center">Carico</div><div style="text-align:center">Prezzo</div><div style="text-align:center">Oggi %</div><div style="text-align:right">Oggi €</div></div>', unsafe_allow_html=True)
    for _, row in df.iterrows():
        is_del = row['delistato']; s_color = "#64748b" if is_del else ("#10b981" if row['oggi_p'] >= 0 else "#ef4444")
        st.markdown(f'''
        <div class="grid-asset compact-row" style="border-left:4px solid {s_color};">
            <div style="display:flex; align-items:baseline; gap:6px;"><b class="asset-name" style="color:{"#94a3b8" if is_del else "white"};">{row["Titolo"]}</b><span style="color:#64748b; font-size:0.6rem;">{row["settore"]}</span></div>
            <div style="text-align:center; color:#cbd5e1; font-size:0.9rem;">{row["qty"]:,.0f}</div>
            <div style="text-align:center; color:#cbd5e1; font-size:0.9rem;">{row["carico"]:.2f}</div>
            <div style="text-align:center; color:{"#94a3b8" if is_del else "white"}; font-size:0.9rem; font-weight:700;">{row["prezzo"]:.2f}</div>
            <div style="text-align:center;"><span style="{get_heatmap_style(row["oggi_p"], is_del)}">{row["oggi_p"]:+.2f}%</span></div>
            <div style="text-align:right;"><span style="{get_heatmap_style(row["oggi_e"], is_del)}">{format_euro(row["oggi_e"])}</span></div>
        </div>
        ''', unsafe_allow_html=True)

    # C. STRATEGY & PERFORMANCE
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Strategy & Performance")
    sec_d = df.groupby('settore')['Peso %'].sum().sort_values(ascending=False); colors = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6"]
    conic = ", ".join([f"{colors[i%5]} {sum(sec_d.values[:i]):.1f}% {sum(sec_d.values[:i+1]):.1f}%" for i in range(len(sec_d))])
    top_t, flop_t = df.loc[df['oggi_p'].idxmax()], df.loc[df['oggi_p'].idxmin()]

    st.markdown(f"""
    <div class="flex-row" style="height: 150px;">
        <div class="flex-item" style="background:#1e293b; padding:10px; border-radius:12px; display:flex; align-items:center; border-left:6px solid #3b82f6; flex: 1.2;">
            <div class="pie-chart" style="background:conic-gradient({conic});"></div>
            <div style="font-size:0.8rem; padding-left:15px; color:#cbd5e1; white-space: nowrap;">
                {"".join([f'<div><span style="color:{colors[i%5]}; margin-right:5px;">●</span>{s}: <b>{v:.0f}%</b></div>' for i, (s,v) in enumerate(sec_d.items())])}
            </div>
        </div>
        <div class="flex-item" style="display:flex; flex-direction:column; gap:6px;">
            <div style="background:#1e293b; padding:8px 20px; border-radius:12px; border-left:8px solid #10b981; flex:1; display:flex; align-items:center; justify-content:space-between;">
                <div><small style="color:#10b981; font-weight:bold; font-size:0.65rem;">BEST</small><br><b style="color:white; font-size:1rem;">{top_t["Titolo"]}</b></div>
                <span style="font-size:1.8rem; font-weight:900; color:#10b981;">{top_t["oggi_p"]:+.2f}%</span>
            </div>
            <div style="background:#1e293b; padding:8px 20px; border-radius:12px; border-left:8px solid #ef4444; flex:1; display:flex; align-items:center; justify-content:space-between;">
                <div><small style="color:#ef4444; font-weight:bold; font-size:0.65rem;">WORST</small><br><b style="color:white; font-size:1rem;">{flop_t["Titolo"]}</b></div>
                <span style="font-size:1.8rem; font-weight:900; color:#ef4444;">{flop_t["oggi_p"]:+.2f}%</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # D. EXPECTED TARGET
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Expected Target 2026")
    st.markdown(f'''
        <div style="background:linear-gradient(90deg,#422006,#1e293b); padding:12px 25px; border-radius:12px; border-left:10px solid #fbbf24; display:flex; justify-content:space-around; align-items:center; margin-bottom:15px;">
            <div style="text-align:center;"><p style="color:#fbbf24; margin:0; font-size:0.8rem; font-weight:bold;">CAPITALE TOTALE OBIETTIVO</p><h2 style="color:white; margin:0; font-size:2.2rem; font-weight:900;">{format_euro(tot_target)}</h2></div>
            <div style="width:2px; height:40px; background:rgba(255,255,255,0.1);"></div>
            <div style="text-align:center;"><p style="color:#10b981; margin:0; font-size:0.8rem; font-weight:bold;">GUADAGNO POTENZIALE NETTO</p><h2 style="color:#10b981; margin:0; font-size:2.2rem; font-weight:900;">+ {format_euro(guadagno_futuro)}</h2></div>
        </div>
    ''', unsafe_allow_html=True)
    
    for _, row in df.iterrows():
        if row['target'] > 0:
            prog = min(max((row['prezzo']/row['target'])*100, 0), 100)
            st.markdown(f'''
                <div style="font-size:0.75rem; display:flex; justify-content:space-between; color:#cbd5e1; margin-bottom:2px;">
                    <span><b style="font-size:0.85rem;">{row["Titolo"]}</b> (Target: {row["target"]:.2f}€)</span>
                    <span style="color:#10b981; font-weight:700;">+ {format_euro((row["target"]-row["prezzo"])*row["qty"])}</span>
                </div>
                <div style="width:100%; background:#1e293b; height:6px; border-radius:10px; margin-bottom:10px;">
                    <div style="width:{prog}%; background:#fbbf24; height:6px; border-radius:10px; box-shadow: 0 0 5px #fbbf24;"></div>
                </div>
            ''', unsafe_allow_html=True)

time.sleep(15)
st.rerun()