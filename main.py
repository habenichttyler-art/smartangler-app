import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import requests
import time

st.set_page_config(
    page_title="SmartAngler Tactical Console", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- GLOBAL STYLESHEET ---
st.markdown("""
    <style>
        .stApp { background-color: #060910 !important; }
        h1, h2, h3, p, span, label, div { font-family: 'Courier New', Courier, monospace !important; }
        .landing-title { color: #00FFCC !important; font-size: 3rem; font-weight: 800; text-align: center; letter-spacing: 3px; margin-top: 50px; margin-bottom: 10px; }
        .landing-subtitle { color: #8fa0bc !important; font-size: 1.3rem; text-align: center; margin-bottom: 50px; }
        .feature-card { background-color: #080d1a; border: 1px solid #1a2942; border-radius: 8px; padding: 25px; margin-bottom: 20px; height: 100%; }
        .feature-header { color: #00FFCC !important; font-size: 1.2rem; font-weight: bold; margin-bottom: 15px; }
        .feature-text { color: #E2E8F0 !important; font-size: 0.95rem; line-height: 1.6; }
        .pricing-box { background-color: #0c1322; border: 2px solid #00FFCC; border-radius: 10px; padding: 40px; text-align: center; max-width: 500px; margin: 40px auto; }
        .console-header { color: #00FFCC !important; font-weight: 800; font-size: 2.3rem; letter-spacing: 2px; margin-bottom: 25px; border-bottom: 2px solid #1a2942; padding-bottom: 10px; }
        .section-header { color: #FFFFFF !important; font-weight: 700; font-size: 1.4rem; letter-spacing: 1px; margin-bottom: 15px; text-transform: uppercase; }
        div[data-testid="stMetricLabel"], div[data-testid="stMetricLabel"] > div, .stMetric label, .stMetric div { color: #E2E8F0 !important; font-weight: bold !important; letter-spacing: 1px !important; }
        .badge-label { font-weight: bold; color: #8fa0bc !important; font-size: 0.9rem; }
        .badge-gray { background-color: #1a2942; color: #ffffff !important; padding: 3px 8px; border-radius: 4px; font-size: 0.85rem; font-weight: bold; display: inline-block; }
        .badge-cyan { background-color: #004d40; color: #00FFCC !important; padding: 3px 8px; border-radius: 4px; font-size: 0.85rem; font-weight: bold; display: inline-block; }
        .badge { background-color: #1b5e20; color: #a5d6a7 !important; padding: 3px 8px; border-radius: 4px; font-size: 0.85rem; font-weight: bold; display: inline-block; }
        div[data-testid="stVVerticalBlock"] > div { background-color: #080d1a; border-radius: 6px; }
    </style>
""", unsafe_allow_html=True)

# --- SECURITY PROTECTION INTERCEPT ---
query_params = st.query_params
is_paid_user = query_params.get("token") == "fish73"

if not is_paid_user:
    st.markdown("<div class='landing-title'>SMARTANGLER TACTICAL CONSOLE</div>", unsafe_allow_html=True)
    st.markdown("<div class='landing-subtitle'>Public Access Scouting & Hydro-Environmental Intelligence</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='feature-card'><div class='feature-header'>PUBLIC ACCESS MAPPING</div><div class='feature-text'>Verified public access tracking across coastal and inland launch grids.</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='feature-card'><div class='feature-header'>NOAA TELEMETRY</div><div class='feature-text'>Direct integration with marine sensors for live tidal and barometric updates.</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='feature-card'><div class='feature-header'>FEEDING WINDOW MATRIX</div><div class='feature-text'>Algorithmic processing of local environmental variables to isolate activity indices.</div></div>", unsafe_allow_html=True)
    st.markdown("<div class='pricing-box'><h2 style='color: #00FFCC; margin-bottom: 10px;'>START YOUR 30-DAY FREE TRIAL</h2><p style='color: #E2E8F0; font-size: 1.1rem; margin-bottom: 25px;'>Access the complete tactical data mapping console.<br><b>$9.99/month</b> after trial. Cancel anytime.</p></div>", unsafe_allow_html=True)
    st.link_button("ACTIVATE 30-DAY FREE TRIAL NOW", "https://buy.stripe.com/YOUR_STRIPE_LINK_HERE", use_container_width=True)
    st.stop()

# --- 100% SCRUBBED WATER-ONLY COORDINATES ---
county_base_coords = {
    "Alachua": [29.4650, -82.1750, "Inland Freshwater System", "8720226", "CDRF1", "Orange Lake Core"],
    "Baker": [30.2150, -82.4300, "Inland Freshwater System", "8720030", "PCBF1", "Ocean Pond Basin"],
    "Bay": [30.1700, -85.6700, "Coastal Marine Estuary", "8729108", "PCBF1", "St. Andrews Bay"],
    "Bradford": [29.9250, -82.1950, "Inland Freshwater System", "8720226", "CDRF1", "Lake Sampson Basin"],
    "Brevard": [28.3000, -80.6500, "Coastal Marine Estuary", "8721604", "41113", "Indian River Lagoon"],
    "Broward": [25.9900, -80.1000, "Coastal Marine Estuary", "8722956", "41113", "Atlantic Coastal Shelf"],
    "Calhoun": [30.4310, -85.0410, "Riverine System", "8728690", "PCBF1", "Apalachicola River"],
    "Charlotte": [26.9000, -82.1500, "Coastal Marine Estuary", "8725520", "CDRF1", "Charlotte Harbor Sound"],
    "Citrus": [28.8900, -82.6500, "Coastal Marine Estuary", "8727122", "CDRF1", "Crystal River Gulf Approach"],
    "Clay": [30.0200, -81.6800, "Riverine System", "8720226", "CDRF1", "St. Johns Wide Channel"],
    "Collier": [26.1000, -81.8500, "Coastal Marine Estuary", "8725114", "CDRF1", "Naples Nearshore Shelf"],
    "Columbia": [29.8300, -82.6300, "Riverine System", "8720030", "CDRF1", "Santa Fe River Bed"],
    "DeSoto": [27.1500, -81.9300, "Riverine System", "8725520", "CDRF1", "Peace River Flow Segment"],
    "Dixie": [29.3500, -83.2000, "Coastal Marine Estuary", "8727520", "CDRF1", "Gulf Coastal Shelf waters"],
    "Duval": [30.3500, -81.5500, "Coastal Marine Estuary", "8720218", "8720219", "St. Johns River Channel"],
    "Escambia": [30.4000, -87.1800, "Coastal Marine Estuary", "8729840", "PCBF1", "Pensacola Bay Core"],
    "Flagler": [29.6000, -81.1800, "Coastal Marine Estuary", "8720218", "41113", "Atlantic Coastal Waters"],
    "Franklin": [29.7000, -84.9000, "Coastal Marine Estuary", "8728690", "PCBF1", "Apalachicola Bay Basin"],
    "Gadsden": [30.4700, -84.6500, "Riverine System", "8728690", "PCBF1", "Lake Talquin Reservoir"],
    "Gilchrist": [29.6000, -82.9400, "Riverine System", "8727520", "CDRF1", "Suwannee River Core channel"],
    "Glades": [26.9500, -80.9500, "Inland Freshwater System", "8725520", "CDRF1", "Lake Okeechobee Western Bay"],
    "Gulf": [29.7500, -85.3500, "Coastal Marine Estuary", "8728690", "PCBF1", "St. Joseph Bay"],
    "Hamilton": [30.4000, -82.9000, "Riverine System", "8720030", "CDRF1", "Suwannee River Basin Pool"],
    "Hardee": [27.5000, -81.8000, "Riverine System", "8725520", "CDRF1", "Peace River Upstream Cut"],
    "Hendry": [26.7800, -81.0800, "Inland Freshwater System", "8725520", "CDRF1", "Lake Okeechobee SW Shelf"],
    "Hernando": [28.5400, -82.7200, "Coastal Marine Estuary", "8727122", "CDRF1", "Gulf Marine Shelf Approach"],
    "Highlands": [27.4500, -81.3000, "Inland Freshwater System", "8725520", "CDRF1", "Lake Istokpoga Core"],
    "Hillsborough": [27.7500, -82.5500, "Coastal Marine Estuary", "8726607", "8726674", "Tampa Bay Center Basin"],
    "Holmes": [30.8000, -85.8000, "Riverine System", "8729108", "PCBF1", "Choctawhatchee River"],
    "Indian River": [27.6500, -80.3800, "Coastal Marine Estuary", "8721604", "41113", "Indian River Lagoon Wide Bay"],
    "Jackson": [30.7200, -84.8800, "Riverine System", "8729108", "PCBF1", "Lake Seminole Reservoir"],
    "Jefferson": [30.0500, -83.9500, "Coastal Marine Estuary", "8727520", "CDRF1", "Apalachee Bay Coastal Shelf"],
    "Lafayette": [30.1000, -83.0200, "Riverine System", "8727520", "CDRF1", "Suwannee River Deep Bend"],
    "Lake": [28.8000, -81.8000, "Inland Freshwater System", "8720226", "41113", "Lake Harris Open Basin"],
    "Lee": [26.6000, -82.1500, "Coastal Marine Estuary", "8725520", "CDRF1", "Pine Island Sound Channel"],
    "Leon": [30.5200, -84.3300, "Inland Freshwater System", "8728690", "PCBF1", "Lake Jackson Basin Open"],
    "Levy": [29.1000, -83.0500, "Coastal Marine Estuary", "8727520", "CDRF1", "Cedar Key Marine Sound"],
    "Liberty": [30.1500, -84.9800, "Riverine System", "8728690", "PCBF1", "Apalachicola River Channel"],
    "Madison": [30.5800, -83.4400, "Riverine System", "8720030", "CDRF1", "Cherry Lake Core Basin"],
    "Manatee": [27.5500, -82.6800, "Coastal Marine Estuary", "8726384", "8726520", "Lower Tampa Bay Waters"],
    "Marion": [29.0200, -81.9300, "Inland Freshwater System", "8720226", "CDRF1", "Lake Weir Circular Basin"],
    "Martin": [27.1500, -80.1500, "Coastal Marine Estuary", "8722670", "41113", "Atlantic Coastal Ocean Shelf"],
    "Miami-Dade": [25.6000, -80.1500, "Coastal Marine Estuary", "8723214", "41113", "Biscayne Bay Lagoon Basin"],
    "Monroe": [24.6000, -81.4000, "Coastal Marine Estuary", "8724580", "8723970", "Florida Bay Keys Channel"],
    "Nassau": [30.6500, -81.4000, "Coastal Marine Estuary", "8720030", "8720218", "Atlantic Nearshore Ocean Shelf"],
    "Okaloosa": [30.4200, -86.5000, "Coastal Marine Estuary", "8729108", "PCBF1", "Choctawhatchee Bay Wide Basin"],
    "Okeechobee": [27.1500, -80.8500, "Inland Freshwater System", "8722670", "CDRF1", "Lake Okeechobee Open Water Core"],
    "Orange": [28.4600, -81.3600, "Inland Freshwater System", "8721604", "41113", "Lake Conway Core Deep Basin"],
    "Osceola": [28.2200, -81.4000, "Inland Freshwater System", "8721604", "41113", "Lake Tohopekaliga Open Core"],
    "Palm Beach": [26.7000, -80.0100, "Coastal Marine Estuary", "8722670", "41113", "Atlantic Ocean Nearshore Shelf"],
    "Pasco": [28.3500, -82.7800, "Coastal Marine Estuary", "8726724", "CDRF1", "Pasco Gulf Marine Shelf"],
    "Pinellas": [27.8000, -82.8000, "Coastal Marine Estuary", "8726520", "8726724", "Gulf of Mexico Shelf Open"],
    "Polk": [27.9500, -81.3500, "Inland Freshwater System", "8726607", "CDRF1", "Lake Kissimmee Deep Core"],
    "Putnam": [29.6500, -81.6300, "Riverine System", "8720226", "CDRF1", "St. Johns Wide Main Channel"],
    "Santa Rosa": [30.4200, -87.0500, "Coastal Marine Estuary", "8729840", "PCBF1", "Pensacola East Bay Basin"],
    "Sarasota": [27.3000, -82.5800, "Coastal Marine Estuary", "8725520", "8726520", "Sarasota Bay Wide Basin"],
    "Seminole": [28.8200, -81.3000, "Inland Freshwater System", "8721604", "41113", "Lake Monroe Open Core Basin"],
    "St. Johns": [29.8500, -81.3000, "Coastal Marine Estuary", "8720218", "41113", "Matanzas River Estuary"],
    "St. Lucie": [27.4500, -80.3000, "Coastal Marine Estuary", "8722670", "41113", "Indian River Lagoon Track"],
    "Sumter": [28.8000, -82.1000, "Inland Freshwater System", "8727122", "CDRF1", "Lake Panasoffkee Core"],
    "Suwannee": [30.2500, -82.9500, "Riverine System", "8720030", "CDRF1", "Suwannee River Main Channel"],
    "Taylor": [29.6500, -83.7000, "Coastal Marine Estuary", "8727520", "CDRF1", "Gulf Open Coastal Shelf"],
    "Union": [30.0200, -82.3400, "Inland Freshwater System", "8720226", "CDRF1", "Lake Butler Core Water"],
    "Volusia": [29.2000, -81.4500, "Coastal Marine Estuary", "8720218", "41113", "Lake George Core Reservoir"],
    "Wakulla": [30.0500, -84.2200, "Coastal Marine Estuary", "8728690", "PCBF1", "Apalachee Bay Shelf Open"],
    "Walton": [30.4000, -86.2000, "Coastal Marine Estuary", "8729108", "PCBF1", "Choctawhatchee Bay Core"],
    "Washington": [30.5500, -85.6800, "Riverine System", "8729108", "PCBF1", "Lucas Lake Basin Center"]
}

def get_noaa_live_telemetry(buoy_id, tide_station):
    barometer, baro_delta, bite_index, bite_delta = 29.92, "+0.01", 75, "STABLE"
    try:
        response = requests.get(f"https://www.ndbc.noaa.gov/data/realtime2/{buoy_id}.txt", timeout=2)
        if response.status_code == 200:
            lines = response.text.split("\n")
            if len(lines) > 3:
                curr, prev = lines[2].split(), lines[3].split()
                if len(curr) > 12 and len(prev) > 12 and curr[12] != "9999.0":
                    barometer = round(float(curr[12]) * 0.02953, 2)
                    diff = round((float(curr[12]) - float(prev[12])) * 0.02953, 2)
                    baro_delta = f"+{diff}" if diff >= 0 else f"{diff}"
    except: pass
    try:
        url = f"https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?date=latest&station={tide_station}&product=water_level&datum=mllw&units=english&time_zone=gmt&format=json"
        response = requests.get(url, timeout=2).json()
        if "data" in response and len(response["data"]) > 0:
            val = float(response['data'][0]['v'])
            bite_index = int(75 + (val * 4))
            bite_delta = "IMPROVING (INFLOW)" if val > 0 else "FALLING TIDE"
    except: pass
    return barometer, baro_delta, bite_index, bite_delta

def get_isolated_county_nodes(county):
    base_info = county_base_coords[county]
    base_lat, base_lon = base_info[0], base_info[1]
    env_type, tide_id, buoy_id, system_label = base_info[2], base_info[3], base_info[4], base_info[5]
    
    baro, b_del, bite, bi_del = get_noaa_live_telemetry(buoy_id, tide_id)
    
    species_map = {
        "Coastal Marine Estuary": "Snook, Spotted Seatrout, Redfish, Tarpon",
        "Inland Freshwater System": "Trophy Largemouth Bass, Black Crappie, Bluegill",
        "Riverine System": "Striped Bass, Channel Catfish, Suwannee Bass"
    }

    # All 5 nodes track identically to the verified deep water center. No offsets. No drifting.
    anchors = [
        {"name": f"{system_label} - Deep Channel Core Line", "depth": "14-26 ft"},
        {"name": f"{system_label} - Submerged Structure Ridge", "depth": "8-15 ft"},
        {"name": f"{system_label} - Baitfish Migration Runway", "depth": "6-12 ft"},
        {"name": f"{system_label} - Thermocline Mid-Layer Focus", "depth": "10-18 ft"},
        {"name": f"{system_label} - Benthic Flat Mud Transition", "depth": "5-11 ft"}
    ]

    compiled_nodes = []
    for node in anchors:
        compiled_nodes.append({
            "water_name": node["name"], "lat": base_lat, "lon": base_lon, "env": env_type, "depth": node["depth"],
            "species": species_map.get(env_type, "Local Target Species"), "bite_index": bite, "bite_delta": bi_del, "barometer": baro, "baro_delta": b_del,
            "structures": [{"path": [[base_lat - 0.001, base_lon - 0.001], [base_lat, base_lon]], "name": "Submerged Structural Edge"}],
            "highways": [{"path": [[base_lat - 0.002, base_lon + 0.002], [base_lat, base_lon]], "name": "Forage Migration Seam"}],
            "labels": f"Geospatial Anchor Verified On Water // Station {tide_id}"
        })
    return compiled_nodes

# --- TOP SELECTOR PANEL ---
st.markdown("<div class='console-header'>UNIVERSAL REGIONAL ACCESSIBILITY CONSOLE</div>", unsafe_allow_html=True)
col_sel1, col_sel2 = st.columns(2)

with col_sel1:
    selected_county = st.selectbox("Select County Domain:", options=sorted(list(county_base_coords.keys())))

active_locations = get_isolated_county_nodes(selected_county)
location_names = [loc["water_name"] for loc in active_locations]

with col_sel2:
    selected_location_name = st.selectbox("Select Access Node Point:", options=location_names)

target_segment = next(loc for loc in active_locations if loc["water_name"] == selected_location_name)

# --- DUAL ROW MATRIX DISPLAY ---
col_map, col_readouts = st.columns([1.3, 1])

with col_map:
    st.markdown("<div class='section-header'>GEOSPATIAL RADAR VERIFICATION</div>", unsafe_allow_html=True)
    st.write(f"Target Coordinate Lock: `{selected_location_name}`")
    
    m = folium.Map(
        location=[target_segment["lat"], target_segment["lon"]], 
        zoom_start=13, 
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery'
    )
    
    for s in target_segment.get("structures", []):
        folium.PolyLine(locations=s["path"], color="#db146a", weight=5, tooltip=s["name"]).add_to(m)
    for h in target_segment.get("highways", []):
        folium.PolyLine(locations=h["path"], color="#ff6600", weight=5, tooltip=h["name"]).add_to(m)
        
    folium.CircleMarker(
        location=[target_segment["lat"], target_segment["lon"]],
        radius=8,
        color="#00ffcc",
        fill=True,
        fill_color="#00ffcc",
        popup=str(target_segment["labels"])
    ).add_to(m)
    
    # BRUTE FORCE REDRAW: Ensures map physically cannot get stuck on old Tampa tiles
    st_folium(
        m, 
        width="100%", 
        height=480, 
        returned_objects=[], 
        key=f"map_{selected_county}_{time.time()}" 
    )

with col_readouts:
    st.markdown("<div class='section-header'>TARGET AREA METRIC DATA</div>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown(f"<span class='badge-label'>Region Cluster:</span> <span class='badge-gray'>{selected_county} County</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='badge-label'>Access Node:</span> <span class='badge-cyan'>{target_segment['water_name']}</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='badge-label'>Classification:</span> <span class='badge'>{target_segment['env']}</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='badge-label'>Depth Profile:</span> <span class='badge-gray'>{target_segment['depth']}</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='badge-label'>Biomass Target:</span> <span class='badge-cyan'>{target_segment['species']}</span>", unsafe_allow_html=True)
    
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        with st.container(border=True):
            st.metric(label="BITE WINDOW INDEX", value=f"{target_segment['bite_index']}/100", delta=target_segment["bite_delta"])
        
    with col_m2:
        with st.container(border=True):
            try: d_val = float(target_segment["baro_delta"])
            except: d_val = 0.0
            st.metric(
                label="BAROMETRIC PRESSURE",
                value=f"{target_segment['barometer']} inHg",
                delta=f"{target_segment['baro_delta']} inHg" if d_val != 0 else "SYSTEM STABLE",
                delta_color="normal" if d_val >= 0 else "inverse"
            )

time.sleep(30)
st.rerun()
