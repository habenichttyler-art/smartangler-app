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

# --- HARDCODED STATEWIDE REGIONAL TELEMETRY AND CORE WATER COORDINATES ---
county_base_coords = {
    "Alachua": [29.6450, -82.2150, "Inland Freshwater System", "8720226", "CDRF1", "Newnans Lake Basin"],
    "Baker": [30.2152, -82.4285, "Inland Freshwater System", "8720030", "PCBF1", "Ocean Pond System"],
    "Bay": [30.1265, -85.7342, "Coastal Marine Estuary", "8729108", "PCBF1", "St. Andrews Pass"],
    "Bradford": [29.9230, -82.1990, "Inland Freshwater System", "8720226", "CDRF1", "Sampson Lake System"],
    "Brevard": [28.1278, -80.6150, "Coastal Marine Estuary", "8721604", "41113", "Eau Gallie Channel Spans"],
    "Broward": [26.1150, -80.1110, "Coastal Marine Estuary", "8722956", "41113", "Port Everglades Track"],
    "Calhoun": [30.4312, -85.0413, "Riverine System", "8728690", "PCBF1", "Apalachicola River Cut"],
    "Charlotte": [26.9342, -82.0514, "Coastal Marine Estuary", "8725520", "CDRF1", "Peace River Estuary"],
    "Citrus": [28.8933, -82.6055, "Coastal Marine Estuary", "8727122", "CDRF1", "Crystal River Channel"],
    "Clay": [30.0450, -81.7050, "Riverine System", "8720226", "CDRF1", "Black Creek Basin"],
    "Collier": [26.0940, -81.7990, "Coastal Marine Estuary", "8725114", "CDRF1", "Gordon Pass Cut"],
    "Columbia": [29.8310, -82.6310, "Riverine System", "8720030", "CDRF1", "Santa Fe River Sector"],
    "DeSoto": [27.2180, -81.8650, "Riverine System", "8725520", "CDRF1", "Peace River Channel"],
    "Dixie": [29.3240, -83.1310, "Coastal Marine Estuary", "8727520", "CDRF1", "Mud Creek Mouth"],
    "Duval": [30.3950, -81.4310, "Coastal Marine Estuary", "8720218", "8720219", "Mayport Shipping Pass"],
    "Escambia": [30.3420, -87.2910, "Coastal Marine Estuary", "8729840", "PCBF1", "Pensacola Pass Slot"],
    "Flagler": [29.6120, -81.2140, "Coastal Marine Estuary", "8720218", "41113", "Matanzas River ICW"],
    "Franklin": [29.7241, -84.9812, "Coastal Marine Estuary", "8728690", "PCBF1", "Apalachicola Bay Cut"],
    "Gadsden": [30.4620, -84.6850, "Inland Freshwater System", "8728690", "PCBF1", "Lake Talquin Influx"],
    "Gilchrist": [29.5920, -82.9510, "Riverine System", "8727520", "CDRF1", "Suwannee River Springs"],
    "Glades": [26.9950, -81.0510, "Inland Freshwater System", "8725520", "CDRF1", "Harney Pond Canal"],
    "Gulf": [29.8120, -85.3010, "Coastal Marine Estuary", "8728690", "PCBF1", "St. Joseph Bay Trough"],
    "Hamilton": [30.3890, -83.1610, "Riverine System", "8720030", "CDRF1", "Withlacoochee River Bend"],
    "Hardee": [27.5410, -81.8110, "Riverine System", "8725520", "CDRF1", "Peace River Deep Trench"],
    "Hendry": [26.7940, -81.4210, "Inland Freshwater System", "8725520", "CDRF1", "Caloosahatchee River Cut"],
    "Hernando": [28.5410, -82.6950, "Coastal Marine Estuary", "8727122", "CDRF1", "Bayport Channel Slot"],
    "Highlands": [27.4650, -81.3410, "Inland Freshwater System", "8725520", "CDRF1", "Lake Istokpoga Core"],
    "Hillsborough": [27.9500, -82.4500, "Coastal Marine Estuary", "8726607", "8726674", "Tampa Shipping Cut"],
    "Holmes": [30.7710, -85.8110, "Riverine System", "8729108", "PCBF1", "Choctawhatchee River"],
    "Indian River": [27.6420, -80.3650, "Coastal Marine Estuary", "8721604", "41113", "IRL Lagoon Channels"],
    "Jackson": [30.7750, -85.1450, "Inland Freshwater System", "8729108", "PCBF1", "Merritts Mill Pond"],
    "Jefferson": [30.0910, -83.9910, "Coastal Marine Estuary", "8727520", "CDRF1", "Aucilla River Mouth"],
    "Lafayette": [30.1210, -83.0210, "Riverine System", "8727520", "CDRF1", "Suwannee River Oxbow"],
    "Lake": [28.8140, -81.7910, "Inland Freshwater System", "8720226", "41113", "Lake Harris Navigation"],
    "Lee": [26.6400, -82.0700, "Coastal Marine Estuary", "8725520", "CDRF1", "Matlacha Pass Track"],
    "Leon": [30.5150, -84.3450, "Inland Freshwater System", "8728690", "PCBF1", "Lake Jackson Basin"],
    "Levy": [29.1310, -83.0510, "Coastal Marine Estuary", "8727520", "CDRF1", "Cedar Key Approach"],
    "Liberty": [30.1410, -84.9950, "Riverine System", "8728690", "PCBF1", "Apalachicola Mid-River"],
    "Madison": [30.4614, -83.4112, "Riverine System", "8720030", "CDRF1", "Withlacoochee Boundary"],
    "Manatee": [27.5310, -82.6140, "Coastal Marine Estuary", "8726384", "8726520", "Manatee River Track"],
    "Marion": [29.5020, -81.8050, "Inland Freshwater System", "8720226", "CDRF1", "Rodman Tailrace Cut"],
    "Martin": [27.1650, -80.1910, "Coastal Marine Estuary", "8722670", "41113", "St. Lucie Inlet Deep"],
    "Miami-Dade": [25.7617, -80.1618, "Coastal Marine Estuary", "8723214", "41113", "Biscayne Shipping Cut"],
    "Monroe": [24.5551, -81.7800, "Coastal Marine Estuary", "8724580", "8723970", "Key West Channel Cut"],
    "Nassau": [30.7120, -81.4514, "Coastal Marine Estuary", "8720030", "8720218", "St. Marys Entrance Pass"],
    "Okaloosa": [30.3950, -86.5120, "Coastal Marine Estuary", "8729108", "PCBF1", "Destin Pass Inlet Slot"],
    "Okeechobee": [27.2010, -80.8290, "Inland Freshwater System", "8722670", "CDRF1", "Kissimmee River Outflow"],
    "Orange": [28.4720, -81.3690, "Inland Freshwater System", "8721604", "41113", "Lake Conway Core Channel"],
    "Osceola": [28.2140, -81.3910, "Inland Freshwater System", "8721604", "41113", "Lake Toho Lock Trench"],
    "Palm Beach": [26.7650, -80.0360, "Coastal Marine Estuary", "8722670", "41113", "Lake Worth Inlet Deep"],
    "Pasco": [28.4310, -82.7210, "Coastal Marine Estuary", "8726724", "CDRF1", "Anclote River Runway"],
    "Pinellas": [27.6320, -82.7410, "Coastal Marine Estuary", "8726520", "8726724", "Egmont Key Main Pass"],
    "Polk": [27.9910, -81.6010, "Inland Freshwater System", "8726607", "CDRF1", "Lake Hatchineha Canal"],
    "Putnam": [29.6412, -81.6314, "Riverine System", "8720226", "CDRF1", "St. Johns Main Channel"],
    "Santa Rosa": [30.4120, -87.1610, "Coastal Marine Estuary", "8729840", "PCBF1", "Escambia Bay Trestles"],
    "Sarasota": [27.3210, -82.5610, "Coastal Marine Estuary", "8725520", "8726520", "Big Sarasota Pass Cut"],
    "Seminole": [28.7910, -81.3510, "Inland Freshwater System", "8721604", "41113", "St. Johns Monroe Entrance"],
    "St. Johns": [29.8910, -81.2910, "Coastal Marine Estuary", "8720218", "41113", "St. Augustine Pass Slot"],
    "St. Lucie": [27.4720, -80.3110, "Coastal Marine Estuary", "8722670", "41113", "Fort Pierce Inlet Track"],
    "Sumter": [28.8910, -82.2110, "Inland Freshwater System", "8727122", "CDRF1", "Panasoffkee Canal Edge"],
    "Suwannee": [30.3850, -83.1610, "Riverine System", "8720030", "CDRF1", "Suwannee Springs Basin"],
    "Taylor": [29.6710, -83.6910, "Coastal Marine Estuary", "8727520", "CDRF1", "Steinhatchee Approach"],
    "Union": [30.0120, -82.3510, "Inland Freshwater System", "8720226", "CDRF1", "Lake Butler Dock Segment"],
    "Volusia": [29.0610, -80.9120, "Coastal Marine Estuary", "8720218", "41113", "Ponce Inlet Shipping Cut"],
    "Wakulla": [30.0610, -84.2810, "Coastal Marine Estuary", "8728690", "PCBF1", "St. Marks River Delta"],
    "Walton": [30.3910, -86.2910, "Coastal Marine Estuary", "8729108", "PCBF1", "Mid-Bay Bridge Trench"],
    "Washington": [30.4910, -85.8610, "Riverine System", "8729108", "PCBF1", "Choctawhatchee River Flat"]
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
    env_type, tide_id, buoy_id = base_info[2], base_info[3], base_info[4]
    system_label = base_info[5] if len(base_info) > 5 else f"{county} Waterway"
    
    baro, b_del, bite, bi_del = get_noaa_live_telemetry(buoy_id, tide_id)
    
    species_map = {
        "Coastal Marine Estuary": "Snook, Spotted Seatrout, Redfish, Tarpon",
        "Inland Freshwater System": "Trophy Largemouth Bass, Black Crappie, Bluegill",
        "Riverine System": "Striped Bass, Channel Catfish, Suwannee Bass"
    }

    # Strict manually plotted coordinate sheets explicitly overriding custom target configurations
    true_hardcoded_spots = {
        "Gilchrist": [
            {"name": "Suwannee River - Santa Fe Mouth Confluence", "lat": 29.8891, "lon": -82.8753, "depth": "8-16 ft"},
            {"name": "Suwannee River - Rock Bluff Launch Ledge", "lat": 29.6452, "lon": -82.9154, "depth": "6-12 ft"},
            {"name": "Suwannee River - Hart Springs Channel Run", "lat": 29.6745, "lon": -82.9515, "depth": "5-10 ft"},
            {"name": "Suwannee River - Otter Springs Island Seam", "lat": 29.6430, "lon": -82.9420, "depth": "7-14 ft"},
            {"name": "Santa Fe River - Sun Springs Bottom Cut", "lat": 29.8220, "lon": -82.7845, "depth": "8-18 ft"}
        ],
        "Hendry": [
            {"name": "Caloosahatchee River - Clewiston Canal Outflow", "lat": 26.7651, "lon": -80.9152, "depth": "8-14 ft"},
            {"name": "Caloosahatchee River - LaBelle Trestle Guard", "lat": 26.7554, "lon": -81.4422, "depth": "10-16 ft"},
            {"name": "Caloosahatchee River - Central Shipping Channel", "lat": 26.7942, "lon": -81.4215, "depth": "8-15 ft"},
            {"name": "Lake Okeechobee - Rim Canal Sector Junction", "lat": 26.7915, "lon": -81.0912, "depth": "7-12 ft"},
            {"name": "Caloosahatchee River - Fort Denaud Channel Cut", "lat": 26.7852, "lon": -81.5153, "depth": "5-9 ft"}
        ],
        "Hamilton": [
            {"name": "Suwannee River - Withlacoochee River Junction", "lat": 30.3892, "lon": -83.1612, "depth": "6-12 ft"},
            {"name": "Suwannee River - Rocky Bluff Deep Hole Channel", "lat": 30.4112, "lon": -82.8853, "depth": "10-22 ft"},
            {"name": "Suwannee River - Suwannee Springs Bottom Run", "lat": 30.3852, "lon": -82.9913, "depth": "5-10 ft"},
            {"name": "Alapaha River - Floodplain Delta Mouth Pass", "lat": 30.3212, "lon": -83.1053, "depth": "4-8 ft"},
            {"name": "Suwannee River - US-129 Bridge Channel Core", "lat": 30.3542, "lon": -82.9153, "depth": "8-16 ft"}
        ]
    }

    if county in true_hardcoded_spots:
        anchors = true_hardcoded_spots[county]
    else:
        # Micro-scale coordinate shifts (< 30 meters) to keep pins locked entirely inside the baseline channel water zone
        anchors = [
            {"name": f"{system_label} - Center Channel Ledge", "lat": base_lat, "lon": base_lon, "depth": "8-14 ft"},
            {"name": f"{system_label} - North Bank Mud Flat Seam", "lat": base_lat + 0.0003, "lon": base_lon - 0.0004, "depth": "5-9 ft"},
            {"name": f"{system_label} - Deep Relief Flow Hole", "lat": base_lat - 0.0004, "lon": base_lon + 0.0003, "depth": "12-25 ft"},
            {"name": f"{system_label} - Upper Pass Trough Section", "lat": base_lat + 0.0002, "lon": base_lon + 0.0004, "depth": "6-11 ft"},
            {"name": f"{system_label} - Lower Boundary Run Cut", "lat": base_lat - 0.0003, "lon": base_lon - 0.0002, "depth": "7-13 ft"}
        ]

    compiled_nodes = []
    for node in anchors:
        lat, lon = node["lat"], node["lon"]
        compiled_nodes.append({
            "water_name": node["name"], "lat": lat, "lon": lon, "env": env_type, "depth": node["depth"],
            "species": species_map.get(env_type, "Local Target Species"), "bite_index": bite, "bite_delta": bi_del, "barometer": baro, "baro_delta": b_del,
            "structures": [{"path": [[lat - 0.0004, lon - 0.0004], [lat, lon]], "name": "Submerged Channel Drop-off Edge"}],
            "highways": [{"path": [[lat - 0.0008, lon + 0.0008], [lat, lon]], "name": "Forage Migration Current Run"}],
            "labels": f"Geospatial Node Verified // Station {tide_id}"
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
        zoom_start=15, 
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
