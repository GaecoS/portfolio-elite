import streamlit as st
import yfinance as yf
import pandas as pd
import time

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="Portfolio Elite 2026", layout="wide")

# --- 2. IL TUO PORTAFOGLIO REALE ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = [
        {"titolo": "STELLANTIS", "ticker": "STLAM.MI", "qty": 2060.00, "carico": 12.91, "delistato": False}, 
        {"titolo": "AMD",        "ticker": "AMD.DE",   "qty": 170.00,  "carico": 122.12, "delistato": False},
        {"titolo": "FINCANTIERI", "ticker": "FCT.MI",  "qty": 570.00,  "carico": 13.19, "delistato": False},
        {"titolo": "LEONARDO",   "ticker": "LDO.MI",   "qty": 250.00,  "carico": 38.00, "delistato": False}, 
        {"titolo": "UNICREDIT",  "ticker": "UCG.MI",   "qty": 500.00,  "carico": 43.28, "delistato": False},
        {"titolo": "NVIDIA",     "ticker": "NVD.DE",   "qty": 700.00,  "carico": 93.86, "delistato": False},
        {"titolo": "SCK",        "ticker": "SCK.MI",   "qty": 1000.00, "carico": 7.74, "delistato": True, "prezzo_fissato": 0.939} 
    ]

ACRONIMI = {"NVIDIA": "NVDA", "UNICREDIT": "UCG", "AMD": "AMD", "LEONARDO": "LDO", "STELLANTIS": "STLAM", "FINCANTIERI": "FCT", "SCK": "SCK"}

# --- 3. FUNZIONI DI SERVIZIO ---
def format_it(n):
    return f"€ {n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def get_dynamic_color(p, pl_tot, delistato):
    val = p if (not delistato and abs(p) > 0.01) else pl_tot
    intensity = min(abs(val) / 6.0, 1.0)
    if val >= 0:
        return f"rgb({int(10+(6*intensity))}, {int(45+(140*intensity))}, {int(25+(104*intensity))})"
    return f"rgb({int(60+(179*intensity))}, {int(15+(53*intensity))}, {int(15+(53*intensity))})"

# --- 4. ENGINE RECUPERO DATI ---
@st.cache_data(ttl=15)
def carica_dati(portfolio):
    risultati = []
    for t in portfolio:
        try:
            if t.get("delistato"): 
                p_att = t.get("prezzo_fissato", 0.0)
                p_ieri = p_att
            else:
                tk = yf.Ticker(t["ticker"])
                h = tk.history(period="5d")
                p_att = h['Close'].iloc[-1]
                p_ieri = h['Close'].iloc[-2]
            
            val = p_att * t["qty"]
            inv = t["carico"] * t["qty"]
            risultati.append({
                "Titolo": t["titolo"], "Quantità": t["qty"], "Carico": t["carico"],
                "Prezzo": p_att, "Valore": val, "Oggi %": ((p_att - p_ieri) / p_ieri * 100),
                "Oggi €": (p_att - p_ieri) * t["qty"], "Totale €": val - inv,
                "Totale %": ((val - inv) / inv * 100) if inv > 0 else 0, "delistato": t.get("delistato")
            })
        except: pass
    df = pd.DataFrame(risultati)
    if not df.empty: df['Peso %'] = (df['Valore'] / df['Valore'].sum() * 100)
    return df

df = carica_dati(st.session_state.portfolio)

# --- 5. RENDER DASHBOARD ---
if not df.empty:
    tot_cap = df['Valore'].sum()
    oggi_eu = df['Oggi €'].sum()
    tot_pl = df['Totale €'].sum()
    inv_ini = (df['Valore'] - df['Totale €']).sum()

    # Layout 3 Celle Superiori con Percentuali Maggiorate
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"""<div style="background:#1e293b;padding:25px 10px;border-radius:12px;border-bottom:4px solid white;height:170px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;"><p style="color:#94a3b8;margin:0;font-size:0.75rem;text-transform:uppercase;">Capitale Totale</p><h2 style="color:white;margin:5px 0;font-size:1.9rem;font-weight:700;">{format_it(tot_cap)}</h2></div>""", unsafe_allow_html=True)
    
    with c2:
        bg_o, tx_o = ("#064e3b", "#10b981") if oggi_eu >= 0 else ("#450a0a", "#ef4444")
        st.markdown(f"""<div style="background:{bg_o};padding:25px 10px;border-radius:12px;border-bottom:4px solid {tx_o};height:170px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;"><p style="color:#94a3b8;margin:0;font-size:0.75rem;text-transform:uppercase;">Andamento Oggi</p><h2 style="color:{tx_o};margin:5px 0;font-size:1.9rem;font-weight:700;">{format_it(oggi_eu)}</h2><p style="color:{tx_o};margin:0;font-size:1.3rem;font-weight:bold;">{oggi_eu/(tot_cap-oggi_eu)*100:+.2f}%</p></div>""", unsafe_allow_html=True)
    
    with c3:
        bg_p, tx_p = ("#064e3b", "#10b981") if tot_pl >= 0 else ("#450a0a", "#ef4444")
        st.markdown(f"""<div style="background:{bg_p};padding:25px 10px;border-radius:12px;border-bottom:4px solid {tx_p};height:170px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;"><p style="color:#94a3b8;margin:0;font-size:0.75rem;text-transform:uppercase;">P/L Totale</p><h2 style="color:{tx_p};margin:5px 0;font-size:1.9rem;font-weight:700;">{format_it(tot_pl)}</h2><p style="color:{tx_p};margin:0;font-size:1.3rem;font-weight:bold;">{tot_pl/inv_ini*100:+.2f}%</p></div>""", unsafe_allow_html=True)

    st.divider()

    # B. TABELLA TECNICA (Standard 2026)
    st.subheader("Dettaglio Portafoglio")
    def style_rows(v):
        if isinstance(v, (int, float)):
            if v > 0.01: return 'background-color: #064e3b; color: #10b981;'
            if v < -0.01: return 'background-color: #450a0a; color: #ef4444;'
        return 'color: #94a3b8;'

    order = ["Titolo", "Quantità", "Carico", "Prezzo", "Valore", "Peso %", "Oggi %", "Oggi €", "Totale €", "Totale %"]
    st.dataframe(df[order].style.map(style_rows, subset=['Oggi %', 'Oggi €', 'Totale €', 'Totale %']).format({
        'Quantità': '{:,.2f}', 'Carico': '€ {:,.2f}', 'Prezzo': '€ {:,.2f}',
        'Valore': lambda x: format_it(x), 'Oggi €': lambda x: format_it(x), 'Oggi %': '{:+.2f}%',
        'Totale €': lambda x: format_it(x), 'Totale %': '{:+.2f}%', 'Peso %': '{:.2f}%'
    }), width='stretch', hide_index=True)

    st.divider()

    # C. MAPPA TREEMAP
    st.subheader("Asset Allocation")
    ds = df.sort_values(by='Valore', ascending=False)
    titles = ds['Titolo'].tolist(); dm = ds.set_index('Titolo').to_dict('index')
    
    html = f'<div style="position:relative; width:100%; height:320px; border-radius:12px; overflow:hidden; background:#0f172a;">'
    # NVIDIA
    t0 = titles[0]; d0 = dm[t0]; c0 = get_dynamic_color(d0['Oggi %'], d0['Totale %'], d0['delistato'])
    html += f'<div style="position:absolute; left:0; top:0; width:{d0["Peso %"]}%; height:100%; background:{c0}; border:1px solid #0f172a; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center;"><b>{ACRONIMI.get(t0, t0[:4])}</b><small>{d0["Peso %"]:.1f}%</small><div style="font-size:2.2rem; font-weight:bold;">{d0["Oggi %"]:+.2f}%</div></div>'
    
    if len(titles) > 1:
        l_off = d0["Peso %"] + 0.1; r_w = 100 - l_off; p_rest = ds['Peso %'].iloc[1:].sum()
        # MEDI
        tm = titles[1:3]; p_m = ds['Peso %'].iloc[1:3].sum(); w_m = (p_m / p_rest) * r_w
        for i, n in enumerate(tm):
            d = dm[n]; h = (d['Peso %'] / p_m) * 100; tp = 0 if i == 0 else (100-h); cn = get_dynamic_color(d['Oggi %'], d['Totale %'], d['delistato'])
            html += f'<div style="position:absolute; left:{l_off}%; top:{tp}%; width:{w_m}%; height:{h}%; background:{cn}; border:1px solid #0f172a; display:flex; flex-direction:column; justify-content:center; align-items:center;"><b>{ACRONIMI.get(n, n[:4])}</b><div style="font-size:1.3rem; font-weight:bold;">{d["Oggi %"]:+.2f}%</div></div>'
        # PICCOLI
        if len(titles) > 3:
            sl = l_off + w_m + 0.1; ws = 100 - sl; pp = ds['Peso %'].iloc[3:].sum(); ct = 0
            for n in titles[3:]:
                d = dm[n]; hs = (d['Peso %'] / pp) * 100; cn = get_dynamic_color(d['Oggi %'], d['Totale %'], d['delistato'])
                html += f'<div style="position:absolute; left:{sl}%; top:{ct}%; width:{ws}%; height:{hs}%; background:{cn}; border:1px solid #0f172a; display:flex; flex-direction:column; justify-content:center; align-items:center; overflow:hidden; padding:2px;"><b>{ACRONIMI.get(n, n[:3])}</b><small>{(d["Oggi %"] if not d["delistato"] else d["Totale %"]):+.2f}%</small></div>'
                ct += hs
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

time.sleep(15)
st.rerun()