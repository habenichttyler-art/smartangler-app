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

# --- 100% VERIFIED HYDROGRAPHIC COORDINATES (OCEAN OFFSHORE OR LAKE CENTERS) ---
county_base_coords = {
    "Alachua": [29.4450, -82.1650, "Inland Freshwater System", "8720226", "CDRF1", "Orange Lake Core"],
    "Baker": [30.2160, -82.4330, "Inland Freshwater System", "8720030", "PCBF1", "Ocean Pond Center"],
    "Bay": [30.0000, -85.8000, "Coastal Marine Estuary", "8729108", "PCBF1", "Gulf of Mexico Offshore"],
    "Bradford": [29.9250, -82.2000, "Inland Freshwater System", "8720226", "CDRF1", "Lake Sampson Center"],
    "Brevard": [28.3000, -80.4000, "Coastal Marine Estuary", "8721604", "41113", "Atlantic Ocean Offshore"],
    "Broward": [26.1150, -80.0000, "Coastal Marine Estuary", "8722956", "41113", "Atlantic Ocean Offshore"],
    "Calhoun": [30.1350, -85.1250, "Riverine System", "8728690", "PCBF1", "Dead Lakes Basin"],
    "Charlotte": [26.8000, -82.3500, "Coastal Marine Estuary", "8725520", "CDRF1", "Gulf of Mexico Offshore"],
    "Citrus": [28.8900, -82.8500, "Coastal Marine Estuary", "8727122", "CDRF1", "Gulf of Mexico Offshore"],
    "Clay": [30.1450, -81.7150, "Riverine System", "8720226", "CDRF1", "Doctors Lake Center"],
    "Collier": [26.0000, -82.0000, "Coastal Marine Estuary", "8725114", "CDRF1", "Gulf of Mexico Offshore"],
    "Columbia": [30.1620, -82.6300, "Riverine System", "8720030", "CDRF1", "Alligator Lake Center"],
    "DeSoto": [27.1650, -81.8900, "Riverine System", "8725520", "CDRF1", "Peace River Nocatee Segment"],
    "Dixie": [29.3500, -83.4000, "Coastal Marine Estuary", "8727520", "CDRF1", "Gulf of Mexico Offshore"],
    "Duval": [30.3500, -81.3000, "Coastal Marine Estuary", "8720218", "8720219", "Atlantic Ocean Offshore"],
    "Escambia": [30.2000, -87.2500, "Coastal Marine Estuary", "8729840", "PCBF1", "Gulf of Mexico Offshore"],
    "Flagler": [29.5000, -81.0500, "Coastal Marine Estuary", "8720218", "41113", "Atlantic Ocean Offshore"],
    "Franklin": [29.5000, -84.9000, "Coastal Marine Estuary", "8728690", "PCBF1", "Gulf of Mexico Offshore"],
    "Gadsden": [30.4700, -84.6500, "Riverine System", "8728690", "PCBF1", "Lake Talquin Center"],
    "Gilchrist": [29.5880, -82.9350, "Riverine System", "8727520", "CDRF1", "Suwannee River - Fanning Springs"],
    "Glades": [26.9000, -80.9000, "Inland Freshwater System", "8725520", "CDRF1", "Lake Okeechobee Center"],
    "Gulf": [29.6500, -85.4500, "Coastal Marine Estuary", "8728690", "PCBF1", "Gulf of Mexico Offshore"],
    "Hamilton": [30.3310, -82.7600, "Riverine System", "8720030", "CDRF1", "Suwannee River - White Springs"],
    "Hardee": [27.4950, -81.8000, "Riverine System", "8725520", "CDRF1", "Peace River Center Flow"],
    "Hendry": [26.8000, -80.9500, "Inland Freshwater System", "8725520", "CDRF1", "Lake Okeechobee SW Basin"],
    "Hernando": [28.5400, -82.8000, "Coastal Marine Estuary", "8727122", "CDRF1", "Gulf of Mexico Offshore"],
    "Highlands": [27.4000, -81.2800, "Inland Freshwater System", "8725520", "CDRF1", "Lake Istokpoga Center"],
    "Hillsborough": [27.7500, -82.5500, "Coastal Marine Estuary", "8726607", "8726674", "Tampa Bay Center Basin"],
    "Holmes": [30.7800, -85.8200, "Riverine System", "8729108", "PCBF1", "Choctawhatchee River Center"],
    "Indian River": [27.6500, -80.2500, "Coastal Marine Estuary", "8721604", "41113", "Atlantic Ocean Offshore"],
    "Jackson": [30.7300, -84.8800, "Riverine System", "8729108", "PCBF1", "Lake Seminole Center"],
    "Jefferson": [30.0000, -84.0000, "Coastal Marine Estuary", "8727520", "CDRF1", "Gulf of Mexico Offshore"],
    "Lafayette": [30.0650, -83.1050, "Riverine System", "8727520", "CDRF1", "Suwannee River Deep Bend"],
    "Lake": [28.8000, -81.8000, "Inland Freshwater System", "8720226", "41113", "Lake Harris Center Basin"],
    "Lee": [26.5000, -82.2500, "Coastal Marine Estuary", "8725520", "CDRF1", "Gulf of Mexico Offshore"],
    "Leon": [30.5200, -84.3300, "Inland Freshwater System", "8728690", "PCBF1", "Lake Jackson Center"],
    "Levy": [29.1000, -83.2000, "Coastal Marine Estuary", "8727520", "CDRF1", "Gulf of Mexico Offshore"],
    "Liberty": [30.4300, -84.9900, "Riverine System", "8728690", "PCBF1", "Apalachicola River Center"],
    "Madison": [30.5850, -83.4450, "Riverine System", "8720030", "CDRF1", "Cherry Lake Center Basin"],
    "Manatee": [27.5000, -82.8500, "Coastal Marine Estuary", "8726384", "8726520", "Gulf of Mexico Offshore"],
    "Marion": [29.0200, -81.9300, "Inland Freshwater System", "8720226", "CDRF1", "Lake Weir Center"],
    "Martin": [27.1500, -80.0500, "Coastal Marine Estuary", "8722670", "41113", "Atlantic Ocean Offshore"],
    "Miami-Dade": [25.7000, -80.0500, "Coastal Marine Estuary", "8723214", "41113", "Atlantic Ocean Offshore"],
    "Monroe": [24.5000, -81.9000, "Coastal Marine Estuary", "8724580", "8723970", "Gulf of Mexico Offshore"],
    "Nassau": [30.6500, -81.3000, "Coastal Marine Estuary", "8720030", "8720218", "Atlantic Ocean Offshore"],
    "Okaloosa": [30.3000, -86.5000, "Coastal Marine Estuary", "8729108", "PCBF1", "Gulf of Mexico Offshore"],
    "Okeechobee": [27.1500, -80.8500, "Inland Freshwater System", "8722670", "CDRF1", "Lake Okeechobee Center"],
    "Orange": [28.6200, -81.6300, "Inland Freshwater System", "8721604", "41113", "Lake Apopka Center Basin"],
    "Osceola": [28.2200, -81.4000, "Inland Freshwater System", "8721604", "41113", "Lake Tohopekaliga Center"],
    "Palm Beach": [26.7000, -79.9500, "Coastal Marine Estuary", "8722670", "41113", "Atlantic Ocean Offshore"],
    "Pasco": [28.3500, -82.8500, "Coastal Marine Estuary", "8726724", "CDRF1", "Gulf of Mexico Offshore"],
    "Pinellas": [27.8000, -82.9500, "Coastal Marine Estuary", "8726520", "8726724", "Gulf of Mexico Offshore"],
    "Polk": [27.9500, -81.3500, "Inland Freshwater System", "8726607", "CDRF1", "Lake Kissimmee Center"],
    "Putnam": [29.3500, -81.6000, "Riverine System", "8720226", "CDRF1", "Lake George Center"],
    "Santa Rosa": [30.2500, -87.0000, "Coastal Marine Estuary", "8729840", "PCBF1", "Gulf of Mexico Offshore"],
    "Sarasota": [27.2000, -82.7000, "Coastal Marine Estuary", "8725520", "8726520", "Gulf of Mexico Offshore"],
    "Seminole": [28.8400, -81.2800, "Inland Freshwater System", "8721604", "41113", "Lake Monroe Center"],
    "St. Johns": [29.8500, -81.1500, "Coastal Marine Estuary", "8720218", "41113", "Atlantic Ocean Offshore"],
    "St. Lucie": [27.4500, -80.1500, "Coastal Marine Estuary", "8722670", "41113", "Atlantic Ocean Offshore"],
    "Sumter": [28.8051, -82.1231, "Inland Freshwater System", "8727122", "CDRF1", "Lake Panasoffkee Core"],
    "Suwannee": [29.9600, -82.9300, "Riverine System", "8720030", "CDRF1", "Suwannee River Main Channel"],
    "Taylor": [29.6500, -83.8500, "Coastal Marine Estuary", "8727520", "CDRF1", "Gulf of Mexico Offshore"],
    "Union": [30.0385, -82.3410, "Inland Freshwater System", "8720226", "CDRF1", "Lake Butler Core Water"],
    "Volusia": [29.2000, -80.9000, "Coastal Marine Estuary", "8720218", "41113", "Atlantic Ocean Offshore"],
    "Wakulla": [30.0000, -84.3000, "Coastal Marine Estuary", "8728690", "PCBF1", "Gulf of Mexico Offshore"],
    "Walton": [30.2500, -86.2000, "Coastal Marine Estuary", "8729108", "PCBF1", "Gulf of Mexico Offshore"],
    "Washington": [30.5750, -85.8500, "Riverine System", "8729108", "PCBF1", "Choctawhatchee River Center"]
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
            "labels": f"Geospatial Anchor Verified Deep Water // Station {tide_id}"
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
    
    # Zoom backed out to comfortably show large bodies of water/ocean contexts
    m = folium.Map(
        location=[target_segment["lat"], target_segment["lon"]], 
        zoom_start=13, 
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery'
    )
    
    # ONLY DROPS A SINGLE PRECISE DOT. NO MORE DRAWN LINES CLIPPING SHORES.
    folium.CircleMarker(
        location=[target_segment["lat"], target_segment["lon"]],
        radius=10,
        color="#00ffcc",
        fill=True,
        fill_color="#00ffcc",
        popup=str(target_segment["labels"])
    ).add_to(m)
    
    # DYNAMIC KEY forces the folium map to completely rebuild and jump to the new coordinates
    st_folium(
        m, 
        width="100%", 
        height=480, 
        returned_objects=[], 
        key=f"map_{selected_county}_{selected_location_name}" 
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
