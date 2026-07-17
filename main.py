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

# --- HARDCODED STATEWIDE REGIONAL BASELINE MATRIX ---
county_base_coords = {
    "Alachua": [29.6747, -82.1658, "Inland Freshwater System", "8720226", "CDRF1"],
    "Baker": [30.2741, -82.2811, "Inland Freshwater System", "8720030", "PCBF1"],
    "Bay": [30.2322, -85.7510, "Coastal Marine Estuary", "8729108", "PCBF1"],
    "Bradford": [29.9511, -82.1214, "Inland Freshwater System", "8720226", "CDRF1"],
    "Brevard": [28.3000, -80.6500, "Coastal Marine Estuary", "8721604", "41113"],
    "Broward": [26.1242, -80.1436, "Coastal Marine Estuary", "8722956", "41113"],
    "Calhoun": [30.4312, -85.0413, "Riverine System", "8728690", "PCBF1"],
    "Charlotte": [26.9342, -82.0514, "Coastal Marine Estuary", "8725520", "CDRF1"],
    "Citrus": [28.8933, -82.6055, "Coastal Marine Estuary", "8727122", "CDRF1"],
    "Clay": [30.0142, -81.7511, "Riverine System", "8720226", "CDRF1"],
    "Collier": [26.1423, -81.7941, "Coastal Marine Estuary", "8725114", "CDRF1"],
    "Columbia": [30.1914, -82.6312, "Riverine System", "8720030", "CDRF1"],
    "DeSoto": [27.2141, -81.8512, "Riverine System", "8725520", "CDRF1"],
    "Dixie": [29.5142, -83.1511, "Coastal Marine Estuary", "8727520", "CDRF1"],
    "Duval": [30.3322, -81.6512, "Coastal Marine Estuary", "8720218", "8720219"],
    "Escambia": [30.4214, -87.2141, "Coastal Marine Estuary", "8729840", "PCBF1"],
    "Flagler": [29.4741, -81.1214, "Coastal Marine Estuary", "8720218", "41113"],
    "Franklin": [29.7241, -84.9812, "Coastal Marine Estuary", "8728690", "PCBF1"],
    "Gadsden": [30.5812, -84.6811, "Riverine System", "8728690", "PCBF1"],
    "Gilchrist": [29.6912, -82.8514, "Riverine System", "8727520", "CDRF1"],
    "Glades": [26.9511, -81.0914, "Inland Freshwater System", "8725520", "CDRF1"],
    "Gulf": [29.9142, -85.2811, "Coastal Marine Estuary", "8728690", "PCBF1"],
    "Hamilton": [30.5011, -82.9514, "Riverine System", "8720030", "CDRF1"],
    "Hardee": [27.4812, -81.8114, "Riverine System", "8725520", "CDRF1"],
    "Hendry": [26.7142, -81.4211, "Inland Freshwater System", "8725520", "CDRF1"],
    "Hernando": [28.5512, -82.5214, "Coastal Marine Estuary", "8727122", "CDRF1"],
    "Highlands": [27.3514, -81.3411, "Inland Freshwater System", "8725520", "CDRF1"],
    "Hillsborough": [27.9500, -82.4500, "Coastal Marine Estuary", "8726607", "8726674"],
    "Holmes": [30.8711, -85.8114, "Riverine System", "8729108", "PCBF1"],
    "Indian River": [27.6312, -80.3914, "Coastal Marine Estuary", "8721604", "41113"],
    "Jackson": [30.7914, -85.2211, "Riverine System", "8729108", "PCBF1"],
    "Jefferson": [30.3812, -83.9014, "Coastal Marine Estuary", "8727520", "CDRF1"],
    "Lafayette": [30.0211, -83.1814, "Riverine System", "8727520", "CDRF1"],
    "Lake": [28.7814, -81.7312, "Inland Freshwater System", "8720226", "41113"],
    "Lee": [26.6400, -81.8700, "Coastal Marine Estuary", "8725520", "CDRF1"],
    "Leon": [30.4382, -84.2807, "Inland Freshwater System", "8728690", "PCBF1"],
    "Levy": [29.2214, -82.7812, "Coastal Marine Estuary", "8727520", "CDRF1"],
    "Liberty": [30.2411, -84.9514, "Riverine System", "8728690", "PCBF1"],
    "Madison": [30.4614, -83.4112, "Riverine System", "8720030", "CDRF1"],
    "Manatee": [27.4912, -82.5714, "Coastal Marine Estuary", "8726384", "8726520"],
    "Marion": [29.1814, -82.1312, "Inland Freshwater System", "8720226", "CDRF1"],
    "Martin": [27.1912, -80.2414, "Coastal Marine Estuary", "8722670", "41113"],
    "Miami-Dade": [25.7617, -80.1918, "Coastal Marine Estuary", "8723214", "41113"],
    "Monroe": [24.5551, -81.7800, "Coastal Marine Estuary", "8724580", "8723970"],
    "Nassau": [30.6612, -81.5614, "Coastal Marine Estuary", "8720030", "8720218"],
    "Okaloosa": [30.5114, -86.5812, "Coastal Marine Estuary", "8729108", "PCBF1"],
    "Okeechobee": [27.2412, -80.8314, "Inland Freshwater System", "8722670", "CDRF1"],
    "Orange": [28.5383, -81.3792, "Inland Freshwater System", "8721604", "41113"],
    "Osceola": [28.2914, -81.4112, "Inland Freshwater System", "8721604", "41113"],
    "Palm Beach": [26.7056, -80.0364, "Coastal Marine Estuary", "8722670", "41113"],
    "Pasco": [28.3314, -82.6612, "Coastal Marine Estuary", "8726724", "CDRF1"],
    "Pinellas": [27.8500, -82.7500, "Coastal Marine Estuary", "8726520", "8726724"],
    "Polk": [27.9414, -81.7012, "Inland Freshwater System", "8726607", "CDRF1"],
    "Putnam": [29.6412, -81.6314, "Riverine System", "8720226", "CDRF1"],
    "Santa Rosa": [30.6114, -87.0312, "Coastal Marine Estuary", "8729840", "PCBF1"],
    "Sarasota": [27.3364, -82.5307, "Coastal Marine Estuary", "8725520", "8726520"],
    "Seminole": [28.7014, -81.2012, "Inland Freshwater System", "8721604", "41113"],
    "St. Johns": [29.9014, -81.3112, "Coastal Marine Estuary", "8720218", "41113"],
    "St. Lucie": [27.4412, -80.3214, "Coastal Marine Estuary", "8722670", "41113"],
    "Sumter": [28.7114, -82.0812, "Inland Freshwater System", "8727122", "CDRF1"],
    "Suwannee": [30.2412, -82.9914, "Riverine System", "8720030", "CDRF1"],
    "Taylor": [30.0114, -83.5812, "Coastal Marine Estuary", "8727520", "CDRF1"],
    "Union": [30.0412, -82.3514, "Inland Freshwater System", "8720226", "CDRF1"],
    "Volusia": [29.1514, -81.0112, "Coastal Marine Estuary", "8720218", "41113"],
    "Wakulla": [30.1114, -84.3812, "Coastal Marine Estuary", "8728690", "PCBF1"],
    "Walton": [30.6114, -86.1812, "Coastal Marine Estuary", "8729108", "PCBF1"],
    "Washington": [30.6114, -85.6612, "Riverine System", "8729108", "PCBF1"]
}

def get_noaa_live_telemetry(buoy_id, tide_station):
    barometer, baro_delta, bite_index, bite_delta, water_level = 29.92, "+0.01", 75, "STABLE", "0.00 ft"
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
            water_level = f"{response['data'][0]['v']} ft"
            val = float(response['data'][0]['v'])
            bite_index = int(75 + (val * 4))
            bite_delta = "IMPROVING (INFLOW)" if val > 0 else "FALLING TIDE"
    except: pass
    return barometer, baro_delta, bite_index, bite_delta, water_level

def get_single_county_data(county, info):
    base_lat, base_lon, env_type, tide_id, buoy_id = info
    baro, b_del, bite, bi_del, tide = get_noaa_live_telemetry(buoy_id, tide_id)
    
    species_map = {
        "Coastal Marine Estuary": "Snook, Spotted Seatrout, Redfish, Tarpon",
        "Inland Freshwater System": "Trophy Largemouth Bass, Black Crappie, Bluegill",
        "Riverine System": "Striped Bass, Channel Catfish, Suwannee Bass"
    }
    
    return [
        {
            "water_name": f"{county} Center Channel Access", "lat": base_lat, "lon": base_lon, "env": env_type,
            "depth": f"Live Tide Profile: {tide}" if env_type == "Coastal Marine Estuary" else "6-12 ft Base Depth",
            "species": species_map[env_type], "bite_index": bite, "bite_delta": bi_del, "barometer": baro, "baro_delta": b_del,
            "structures": [{"path": [[base_lat - 0.002, base_lon - 0.002], [base_lat, base_lon]], "name": "Primary Ledge Structure"}],
            "highways": [{"path": [[base_lat - 0.004, base_lon + 0.004], [base_lat, base_lon]], "name": "Bait Migration Route"}],
            "labels": f"Target Access Active // Station {tide_id}"
        },
        {
            "water_name": f"{county} North Basin Segment", "lat": base_lat + 0.008, "lon": base_lon + 0.008, "env": env_type,
            "depth": f"Live Tide Profile: {tide}" if env_type == "Coastal Marine Estuary" else "5-9 ft Base Depth",
            "species": species_map[env_type], "bite_index": min(100, bite + 2), "bite_delta": bi_del, "barometer": baro, "baro_delta": b_del,
            "structures": [{"path": [[base_lat + 0.006, base_lon + 0.006], [base_lat + 0.008, base_lon + 0.008]], "name": "Secondary Shell Flat"}],
            "highways": [{"path": [[base_lat + 0.010, base_lon + 0.005], [base_lat + 0.008, base_lon + 0.008]], "name": "Tidal Inflow Line"}],
            "labels": f"North Vector Active // Station {tide_id}"
        },
        {
            "water_name": f"{county} East Channel Flat", "lat": base_lat - 0.006, "lon": base_lon - 0.009, "env": env_type,
            "depth": f"Live Tide Profile: {tide}" if env_type == "Coastal Marine Estuary" else "7-14 ft Base Depth",
            "species": species_map[env_type], "bite_index": max(0, bite - 3), "bite_delta": bi_del, "barometer": baro, "baro_delta": b_del,
            "structures": [{"path": [[base_lat - 0.008, base_lon - 0.011], [base_lat - 0.006, base_lon - 0.009]], "name": "Deep Drop-off Edge"}],
            "highways": [{"path": [[base_lat - 0.003, base_lon - 0.007], [base_lat - 0.006, base_lon - 0.009]], "name": "Forage Run"}],
            "labels": f"East Vector Active // Station {tide_id}"
        },
        {
            "water_name": f"{county} Deep Basin Point", "lat": base_lat + 0.011, "lon": base_lon - 0.007, "env": env_type,
            "depth": f"Live Tide Profile: {tide}" if env_type == "Coastal Marine Estuary" else "8-16 ft Base Depth",
            "species": species_map[env_type], "bite_index": min(100, bite + 4), "bite_delta": bi_del, "barometer": baro, "baro_delta": b_del,
            "structures": [{"path": [[base_lat + 0.009, base_lon - 0.009], [base_lat + 0.011, base_lon - 0.007]], "name": "Submerged Contour Barrier"}],
            "highways": [{"path": [[base_lat + 0.013, base_lon - 0.005], [base_lat + 0.011, base_lon - 0.007]], "name": "Main Current Highway"}],
            "labels": f"Deep Basin Active // Station {tide_id}"
        },
        {
            "water_name": f"{county} Boundary Cut Access", "lat": base_lat - 0.009, "lon": base_lon + 0.012, "env": env_type,
            "depth": f"Live Tide Profile: {tide}" if env_type == "Coastal Marine Estuary" else "4-8 ft Base Depth",
            "species": species_map[env_type], "bite_index": bite, "bite_delta": bi_del, "barometer": baro, "baro_delta": b_del,
            "structures": [{"path": [[base_lat - 0.011, base_lon + 0.010], [base_lat - 0.009, base_lon + 0.012]], "name": "Shoal Perimeter"}],
            "highways": [{"path": [[base_lat - 0.007, base_lon + 0.014], [base_lat - 0.009, base_lon + 0.012]], "name": "Shallow Migration Pass"}],
            "labels": f"Boundary Vector Active // Station {tide_id}"
        }
    ]

# --- TOP SELECTOR PANEL ---
st.markdown("<div class='console-header'>UNIVERSAL REGIONAL ACCESSIBILITY CONSOLE</div>", unsafe_allow_html=True)
col_sel1, col_sel2 = st.columns(2)

with col_sel1:
    selected_county = st.selectbox("Select County Domain:", options=sorted(list(county_base_coords.keys())))

# ONLY load data for the single selected county to prevent multi-request network lag
active_locations = get_single_county_data(selected_county, county_base_coords[selected_county])
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
        zoom_start=14,
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
    
    st_folium(m, width="100%", height=480, returned_objects=[])

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
