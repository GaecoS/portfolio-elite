import streamlit as st
import yfinance as yf
import pandas as pd
import time

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="Portfolio Elite 2026", layout="wide")

# --- 2. IL TUO PORTAFOGLIO REALE ---
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
def format_no_dec(n):
    return f"€ {int(round(n, 0)):,}".replace(",", ".")

def get_dynamic_color(p, pl_tot, delistato):
    val = p if (not delistato and abs(p) > 0.01) else pl_tot
    intensity = min(abs(val) / 6.0, 1.0)
    if val >= 0: return f"rgb({int(10+(6*intensity))}, {int(45+(140*intensity))}, {int(25+(104*intensity))})"
    return f"rgb({int(60+(179*intensity))}, {int(15+(53*intensity))}, {int(15+(53*intensity))})"

@st.cache_data(ttl=43200) 
def recupera_target_analisti(p):
    targets = {}
    for t in p:
        if t.get("delistato"): continue
        try:
            tk = yf.Ticker(t["ticker"])
            val = tk.info.get('targetMeanPrice')
            if not val and "ticker_usa" in t:
                tk_usa = yf.Ticker(t["ticker_usa"])
                val = tk_usa.info.get('targetMeanPrice')
            targets[t["ticker"]] = val
        except: targets[t["ticker"]] = None
    return targets

# --- 4. ENGINE RECUPERO DATI ---
@st.cache_data(ttl=15)
def carica_dati(portfolio):
    target_map = recupera_target_analisti(portfolio)
    risultati = []
    for t in portfolio:
        try:
            if t.get("delistato"): 
                p_att, p_ieri = t["prezzo_fissato"], t["prezzo_fissato"]
                target_val = t["target_fissato"]
            else:
                tk = yf.Ticker(t["ticker"]); h = tk.history(period="5d")
                p_att, p_ieri = h['Close'].iloc[-1], h['Close'].iloc[-2]
                target_val = target_map.get(t["ticker"])
            
            val, inv = p_att * t["qty"], t["carico"] * t["qty"]
            
            risultati.append({
                "Titolo": ACRONIMI.get(t["titolo"], t["titolo"]), "Quantità": t["qty"], "Carico": t["carico"],
                "Prezzo": p_att, "Valore": val, "Oggi %": ((p_att - p_ieri) / p_ieri * 100),
                "Oggi €": (p_att - p_ieri) * t["qty"], "Totale €": val - inv,
                "Totale %": ((val - inv) / inv * 100) if inv > 0 else 0,
                "Settore": t["settore"], "Target": target_val, "Cap_Target": (target_val if target_val else p_att) * t["qty"], "delistato": t.get("delistato")
            })
        except: pass
    df = pd.DataFrame(risultati)
    if not df.empty: df['Peso %'] = (df['Valore'] / df['Valore'].sum() * 100)
    return df

df = carica_dati(st.session_state.portfolio)

# --- 5. RENDER ---
if not df.empty:
    # Calcoli per le metriche
    tot_cap = df['Valore'].sum()
    oggi_eu = df['Oggi €'].sum()
    tot_pl = df['Totale €'].sum()
    cap_t = df['Cap_Target'].sum()
    inv_ini = (df['Valore'] - df['Totale €']).sum()
    
    perc_target = (tot_cap / cap_t * 100) if cap_t > 0 else 0
    perc_oggi = (oggi_eu / (tot_cap - oggi_eu) * 100) if (tot_cap - oggi_eu) != 0 else 0
    perc_totale = (tot_pl / inv_ini * 100) if inv_ini > 0 else 0

    bg_o, tx_o = ("#064e3b", "#10b981") if oggi_eu >= 0 else ("#450a0a", "#ef4444")
    
    # A. TOP METRICS - ALLINEAMENTO RIGIDO
    st.markdown(f"""
    <div style="display: flex; gap: 8px; width: 100%; height: 180px; margin-bottom: 30px; align-items: stretch;">
        <div style="flex: 1; background: #1e293b; border-radius: 12px; border-bottom: 6px solid white; display: flex; flex-direction: column; justify-content: space-between; padding: 20px 10px; text-align: center;">
            <div style="height: 30px; display: flex; align-items: center; justify-content: center;">
                <p style="color: #cbd5e1; margin: 0; font-size: 1.15rem; text-transform: uppercase; font-weight: 800; letter-spacing: 1.5px;">Portfolio Value</p>
            </div>
            <div style="height: 60px; display: flex; align-items: center; justify-content: center;">
                <h2 style="color: white; margin: 0; font-size: clamp(1.4rem, 5vw, 2.6rem); font-weight: 900; line-height: 1;">{format_no_dec(tot_cap)}</h2>
            </div>
            <div style="height: 30px; display: flex; align-items: center; justify-content: center;">
                <p style="color: #94a3b8; margin: 0; font-size: 1.3rem; font-weight: 800;">{perc_target:.1f}% Target Achieved</p>
            </div>
        </div>
        <div style="flex: 1; background: {bg_o}; border-radius: 12px; border-bottom: 6px solid {tx_o}; display: flex; flex-direction: column; justify-content: space-between; padding: 20px 10px; text-align: center;">
            <div style="height: 30px; display: flex; align-items: center; justify-content: center;">
                <p style="color: #cbd5e1; margin: 0; font-size: 1.15rem; text-transform: uppercase; font-weight: 800; letter-spacing: 1.5px;">Session Impact</p>
            </div>
            <div style="height: 60px; display: flex; align-items: center; justify-content: center;">
                <h2 style="color: {tx_o}; margin: 0; font-size: clamp(1.4rem, 5vw, 2.6rem); font-weight: 900; line-height: 1;">{format_no_dec(oggi_eu)}</h2>
            </div>
            <div style="height: 30px; display: flex; align-items: center; justify-content: center;">
                <p style="color: {tx_o}; margin: 0; font-size: 1.3rem; font-weight: 800;">{perc_oggi:+.2f}%</p>
            </div>
        </div>
        <div style="flex: 1; background: #1e293b; border-radius: 12px; border-bottom: 6px solid #3b82f6; display: flex; flex-direction: column; justify-content: space-between; padding: 20px 10px; text-align: center;">
            <div style="height: 30px; display: flex; align-items: center; justify-content: center;">
                <p style="color: #cbd5e1; margin: 0; font-size: 1.15rem; text-transform: uppercase; font-weight: 800; letter-spacing: 1.5px;">Total Return</p>
            </div>
            <div style="height: 60px; display: flex; align-items: center; justify-content: center;">
                <h2 style="color: #3b82f6; margin: 0; font-size: clamp(1.4rem, 5vw, 2.6rem); font-weight: 900; line-height: 1;">{format_no_dec(tot_pl)}</h2>
            </div>
            <div style="height: 30px; display: flex; align-items: center; justify-content: center;">
                <p style="color: #3b82f6; margin: 0; font-size: 1.3rem; font-weight: 800;">{perc_totale:+.2f}%</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # B. TABELLA
    st.dataframe(df[["Titolo", "Quantità", "Carico", "Prezzo", "Peso %", "Oggi %", "Oggi €", "Totale €"]].style.map(lambda v: 'background-color: #064e3b; color: #10b981;' if (isinstance(v, (int, float)) and v > 0.01) else ('background-color: #450a0a; color: #ef4444;' if (isinstance(v, (int, float)) and v < -0.01) else 'color: #94a3b8;'), subset=['Oggi %', 'Oggi €', 'Totale €']).format({
        'Quantità': '{:,.0f}', 'Carico': '€ {:,.2f}', 'Prezzo': '€ {:,.2f}', 'Oggi €': lambda x: f"€ {int(x):,}".replace(",", "."), 'Oggi %': '{:+.2f}%', 'Totale €': lambda x: f"€ {int(x):,}".replace(",", "."), 'Peso %': '{:.2f}%'
    }), width='stretch', hide_index=True)

    # C. MAPPA TREEMAP
    st.subheader("Asset Allocation")
    ds = df.sort_values(by='Valore', ascending=False); titles = ds['Titolo'].tolist(); dm = ds.set_index('Titolo').to_dict('index')
    html_map = f'<div style="position:relative; width:100%; height:320px; border-radius:12px; overflow:hidden; background:#0f172a; margin-bottom: 30px;">'
    t0 = titles[0]; d0 = dm[t0]; c0 = get_dynamic_color(d0['Oggi %'], d0['Totale %'], d0['delistato'])
    html_map += f'<div style="position:absolute; left:0; top:0; width:{d0["Peso %"]}%; height:100%; background:{c0}; border:1px solid #0f172a; display:flex; flex-direction:column; justify-content:center; align-items:center;"><b>{t0}</b><div style="font-size:2rem; font-weight:bold;">{d0["Oggi %"]:+.2f}%</div></div>'
    if len(titles) > 1:
        l_off = d0["Peso %"] + 0.1; r_w = 100 - l_off; p_rest = ds['Peso %'].iloc[1:].sum()
        tm = titles[1:3]; p_m = ds['Peso %'].iloc[1:3].sum(); w_m = (p_m / p_rest) * r_w
        for i, n in enumerate(tm):
            d = dm[n]; h = (d['Peso %'] / p_m) * 100; tp = 0 if i == 0 else (100-h); cn = get_dynamic_color(d['Oggi %'], d['Totale %'], d['delistato'])
            html_map += f'<div style="position:absolute; left:{l_off}%; top:{tp}%; width:{w_m}%; height:{h}%; background:{cn}; border:1px solid #0f172a; display:flex; flex-direction:column; justify-content:center; align-items:center;"><b>{n}</b><div style="font-size:1.2rem; font-weight:bold;">{d["Oggi %"]:+.2f}%</div></div>'
        if len(titles) > 3:
            sl = l_off + w_m + 0.1; ws = 100 - sl; pp = ds['Peso %'].iloc[3:].sum(); ct = 0
            for n in titles[3:]:
                d = dm[n]; hs = (d['Peso %'] / pp) * 100; cn = get_dynamic_color(d['Oggi %'], d['Totale %'], d['delistato'])
                html_map += f'<div style="position:absolute; left:{sl}%; top:{ct}%; width:{ws}%; height:{hs}%; background:{cn}; border:1px solid #0f172a; display:flex; flex-direction:column; justify-content:center; align-items:center;"><b>{n}</b></div>'; ct += hs
    st.markdown(html_map + '</div>', unsafe_allow_html=True)

    # D. ANALISI STRATEGICA
    st.divider()
    # Preparazione dati Torta
    sec_d = df.groupby('Settore')['Peso %'].sum().sort_values(ascending=False)
    colors = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6"]
    parts = []; curr = 0
    for i, (s,v) in enumerate(sec_d.items()):
        parts.append(f"{colors[i % len(colors)]} {curr:.1f}% {curr+v:.1f}%"); curr += v
    
    st.markdown(f'''
        <div style="display: flex; gap: 10px; width: 100%; flex-wrap: nowrap; align-items: stretch; margin-bottom: 20px;">
            <div style="flex: 1; background: #1e293b; border-left: 8px solid #3b82f6; border-radius: 12px; height: 180px; display: flex; align-items: center; padding: 10px 15px; box-sizing: border-box; overflow: hidden;">
                <div style="width: 150px; height: 150px; border-radius: 50%; background: conic-gradient({", ".join(parts)}); flex-shrink: 0; border: 2px solid #0f172a;"></div>
                <div style="flex-grow: 1; padding-left: 15px; color: #f8fafc; overflow: hidden;">
                    {"".join([f'<div style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis;"><span style="color:{colors[i%len(colors)]};">●</span> {s}: <b>{v:.0f}%</b></div>' for i, (s,v) in enumerate(sec_d.items())])}
                </div>
            </div>
            <div style="flex: 1; display: flex; flex-direction: column; gap: 8px; height: 180px;">
                <div style="flex: 1; background: #1e293b; border-left: 8px solid #10b981; border-radius: 12px; padding: 12px 15px; display: flex; align-items: center; justify-content: space-between;">
                    <div><small style="color:#10b981; font-weight:bold; text-transform:uppercase;">Migliore</small><br><b style="font-size:1.1rem;">{df.loc[df['Oggi %'].idxmax()]['Titolo']}</b></div>
                    <span style="font-size: 2.3rem; font-weight: 900; color: #10b981;">{df.loc[df['Oggi %'].idxmax()]['Oggi %']:+.2f}%</span>
                </div>
                <div style="flex: 1; background: #1e293b; border-left: 8px solid #ef4444; border-radius: 12px; padding: 12px 15px; display: flex; align-items: center; justify-content: space-between;">
                    <div><small style="color:#ef4444; font-weight:bold; text-transform:uppercase;">Peggiore</small><br><b style="font-size:1.1rem;">{df.loc[df['Oggi %'].idxmin()]['Titolo']}</b></div>
                    <span style="font-size: 2.3rem; font-weight: 900; color: #ef4444;">{df.loc[df['Oggi %'].idxmin()]['Oggi %']:+.2f}%</span>
                </div>
            </div>
        </div>
    ''', unsafe_allow_html=True)

    # E. OBIETTIVO FINALE
    st.subheader("Obiettivo Finale")
    st.markdown(f'''
        <div style="background: linear-gradient(90deg, #422006, #1e293b); padding: 25px; border-radius: 12px; border-left: 10px solid #f59e0b; display: flex; justify-content: space-around; align-items: center;">
            <div><p style="color:#f59e0b; margin:0; font-size:0.8rem; font-weight:bold;">EXPECTED AT TARGET</p><h2 style="color:#fbbf24; margin:0; font-size:2.5rem; font-weight:900;">{format_no_dec(cap_t)}</h2></div>
            <div style="width:2px; height:50px; background:#4b5563;"></div>
            <div><p style="color:#94a3b8; margin:0; font-size:0.8rem; font-weight:bold;">EXPECTED UPSIDE</p><h2 style="color:#10b981; margin:0; font-size:2.5rem; font-weight:900;">+ {format_no_dec(cap_t - tot_cap)}</h2></div>
        </div>
    ''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    for _, row in df.iterrows():
        if row['Target']:
            p = min(max((row['Prezzo']/row['Target'])*100, 0), 100)
            st.markdown(f'<div style="font-size:0.75rem; display:flex; justify-content:space-between;"><span>{row["Titolo"]}</span><span>{row["Prezzo"]:.2f}/{row["Target"]:.2f}€</span></div><div style="width:100%; background:#1e293b; height:8px; border-radius:10px; margin-bottom:10px;"><div style="width:{p}%; background:#fbbf24; height:8px; border-radius:10px;"></div></div>', unsafe_allow_html=True)

time.sleep(15)
st.rerun()