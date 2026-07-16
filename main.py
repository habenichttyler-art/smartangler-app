import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import requests
import time

st.set_page_config(
    page_title="UNIVERSAL REGIONAL ACCESSIBILITY CONSOLE", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Deep Tactical Theme Stylesheet injection — High Contrast Metric Override
st.markdown("""
    <style>
        .stApp { background-color: #060910 !important; }
        
        .console-header { 
            color: #00FFCC !important; 
            font-family: 'Courier New', Courier, monospace !important;
            font-weight: 800; 
            font-size: 2.3rem; 
            letter-spacing: 2px; 
            margin-bottom: 25px;
            border-bottom: 2px solid #1a2942;
            padding-bottom: 10px;
        }
        .section-header { 
            color: #FFFFFF !important; 
            font-family: 'Courier New', Courier, monospace !important;
            font-weight: 700; 
            font-size: 1.4rem; 
            letter-spacing: 1px; 
            margin-bottom: 15px;
            text-transform: uppercase;
        }
        
        /* High-contrast catch-all targets metric subtitles cleanly */
        div[data-testid="stMetricLabel"], 
        div[data-testid="stMetricLabel"] > div, 
        .stMetric label, 
        .stMetric div {
            color: #E2E8F0 !important;
            font-family: 'Courier New', Courier, monospace !important;
            font-weight: bold !important;
            letter-spacing: 1px !important;
        }
        
        /* Clean Professional Badge Overrides */
        .badge-label { 
            font-family: 'Courier New', Courier, monospace !important;
            font-weight: bold; 
            color: #8fa0bc !important; 
            font-size: 0.9rem; 
        }
        .badge-gray {
            background-color: #1a2942;
            color: #ffffff !important;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: bold;
            display: inline-block;
        }
        .badge-cyan {
            background-color: #004d40;
            color: #00FFCC !important;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: bold;
            display: inline-block;
        }
        .badge {
            background-color: #1b5e20;
            color: #a5d6a7 !important;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: bold;
            display: inline-block;
        }
        
        /* Premium Container Box styling */
        div[data-testid="stVVerticalBlock"] > div {
            background-color: #080d1a;
            border-radius: 6px;
        }
    </style>
""", unsafe_allow_html=True)

# Complete 67-County Array
fl_counties = [
    "Alachua", "Baker", "Bay", "Bradford", "Brevard", "Broward", "Calhoun", "Charlotte", "Citrus", "Clay", 
    "Collier", "Columbia", "DeSoto", "Dixie", "Duval", "Escambia", "Flagler", "Franklin", "Gadsden", "Gilchrist", 
    "Glades", "Gulf", "Hamilton", "Hardee", "Hendry", "Hernando", "Highlands", "Hillsborough", "Holmes", "Indian River", 
    "Jackson", "Jefferson", "Lafayette", "Lake", "Lee", "Leon", "Levy", "Liberty", "Madison", "Manatee", 
    "Marion", "Martin", "Miami-Dade", "Monroe", "Nassau", "Okaloosa", "Okeechobee", "Orange", "Osceola", "Palm Beach", 
    "Pasco", "Pinellas", "Polk", "Putnam", "Santa Rosa", "Sarasota", "Seminole", "St. Johns", "St. Lucie", "Sumter", 
    "Suwannee", "Taylor", "Union", "Volusia", "Wakulla", "Walton", "Washington"
]

def get_noaa_live_telemetry(buoy_id, tide_station):
    barometer = 29.92
    baro_delta = "+0.01"
    bite_index = 75
    bite_delta = "STABLE"
    water_level = "0.00 ft"
    
    try:
        buoy_url = f"https://www.ndbc.noaa.gov/data/realtime2/{buoy_id}.txt"
        response = requests.get(buoy_url, timeout=3)
        if response.status_code == 200:
            lines = response.text.split("\n")
            if len(lines) > 3:
                curr = lines[2].split()
                prev = lines[3].split()
                if len(curr) > 12 and len(prev) > 12:
                    c_press = float(curr[12])
                    p_press = float(prev[12])
                    if c_press != 9999.0 and p_press != 9999.0:
                        barometer = round(c_press * 0.02953, 2)
                        diff = round((c_press - p_press) * 0.02953, 2)
                        baro_delta = f"+{diff}" if diff >= 0 else f"{diff}"
    except Exception:
        pass
        
    try:
        tide_url = f"https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?date=latest&station={tide_station}&product=water_level&datum=mllw&units=english&time_zone=gmt&format=json"
        response = requests.get(tide_url, timeout=3).json()
        if "data" in response and len(response["data"]) > 0:
            water_level = f"{response['data'][0]['v']} ft"
            val = float(response['data'][0]['v'])
            bite_index = int(75 + (val * 4))
            bite_delta = "IMPROVING (INFLOW)" if val > 0 else "FALLING TIDE"
    except Exception:
        pass
        
    return barometer, baro_delta, bite_index, bite_delta, water_level

def load_statewide_tactical_matrix():
    matrix = {county: [] for county in fl_counties}
    
    # 1. Citrus County Data
    baro_cit, b_del_cit, bite_cit, bi_del_cit, tide_cit = get_noaa_live_telemetry("CDRF1", "8727122")
    matrix["Citrus"] = [
        {
            "water_name": "Crystal River (Kings Bay Main Channel)", "lat": 28.8933, "lon": -82.6055, "env": "Coastal Marine Estuary",
            "depth": f"Live Tide: {tide_cit}", "species": "Trophy Largemouth Bass, Black Crappie, Bluegill", "bite_index": bite_cit, "bite_delta": bi_del_cit, "barometer": baro_cit, "baro_delta": b_del_cit,
            "structures": [{"path": [[28.8930, -82.6150], [28.8933, -82.6055], [28.8940, -82.5950]], "name": "Spring Channel Deep Navigation Trench"}],
            "highways": [{"path": [[28.9050, -82.6080], [28.8933, -82.6055], [28.8820, -82.6020]], "name": "Seasonal Snook Cold-Front Migration Route"}],
            "labels": f"NOAA REAL-TIME STREAMING // Water-Level Flux: {tide_cit}"
        },
        {
            "water_name": "Fort Island Gulf Beach Pier (Open Gulf)", "lat": 28.9161, "lon": -82.6922, "env": "Coastal Marine Estuary",
            "depth": f"Live Tide: {tide_cit}", "species": "Seatrout, Pompano, Redfish", "bite_index": bite_cit, "bite_delta": bi_del_cit, "barometer": baro_cit, "baro_delta": b_del_cit,
            "structures": [{"path": [[28.9161, -82.6922], [28.9130, -82.6950], [28.9100, -82.6980]], "name": "Public Pier Concrete Piling Grid"}],
            "highways": [{"path": [[28.9180, -82.7200], [28.9161, -82.6922], [28.9120, -82.6600]], "name": "Coastal Surf Line Pompano Highway"}],
            "labels": "SEATROUT GRASS FLATS // Drift live shrimp under corks"
        },
        {
            "water_name": "Lake Henderson Public Launch (Inverness Pool)", "lat": 28.8392, "lon": -82.3215, "env": "Inland Freshwater System",
            "depth": "4 - 10 ft", "species": "Largemouth Bass, Bluegill, Black Crappie", "bite_index": 82, "bite_delta": "STABLE", "barometer": baro_cit, "baro_delta": b_del_cit,
            "structures": [{"path": [[28.8480, -82.3280], [28.8392, -82.3215], [28.8280, -82.3190]], "name": "Submerged Hydrilla & Reed Edge Wall"}],
            "highways": [{"path": [[28.8550, -82.3230], [28.8392, -82.3215], [28.8220, -82.3200]], "name": "Freshwater Gizzard Shad Spawning Runway"}],
            "labels": "LARGEMOUTH BASS BEDDING // Punch mats with creature baits"
        },
        {
            "water_name": "Homosassa River Public Basin & River Run", "lat": 28.7994, "lon": -82.6210, "env": "Coastal Marine Estuary",
            "depth": f"Live Tide: {tide_cit}", "species": "Redfish, Snook, Seatrout", "bite_index": bite_cit, "bite_delta": bi_del_cit, "barometer": baro_cit, "baro_delta": b_del_cit,
            "structures": [{"path": [[28.7980, -82.6350], [28.7994, -82.6210], [28.8010, -82.6100]], "name": "Backcountry Limestone River Ledges"}],
            "highways": [{"path": [[28.7950, -82.6500], [28.7994, -82.6210], [28.8020, -82.5900]], "name": "Tidal Blue Crab Drift Run"}],
            "labels": "REDFISH MANGROVE SEAM // Cast gold spoons inside undercut banks"
        },
        {
            "water_name": "Withlacoochee River Delta Channel Base", "lat": 29.0012, "lon": -82.7215, "env": "Coastal Marine Estuary",
            "depth": f"Live Tide: {tide_cit}", "species": "Tarpon, Redfish, Snook", "bite_index": bite_cit, "bite_delta": bi_del_cit, "barometer": baro_cit, "baro_delta": b_del_cit,
            "structures": [{"path": [[29.0050, -82.7350], [29.0012, -82.7215], [28.9950, -82.7050]], "name": "Oyster Bar Navigation Channel Boundary"}],
            "highways": [{"path": [[29.0100, -82.7450], [29.0012, -82.7215], [28.9900, -82.6950]], "name": "River Mouth Ebb Tide Forage Highway"}],
            "labels": "TARPON OVERLAY RUN // Drift cut mullet on heavy currents"
        }
    ]
    
    # 2. Brevard County Data
    baro_brv, b_del_brv, bite_brv, bi_del_brv, tide_brv = get_noaa_live_telemetry("41113", "8721604")
    matrix["Brevard"] = [
        {
            "water_name": "Eau Gallie Bridge Channel Spans", "lat": 28.1278, "lon": -80.6150, "env": "Coastal Marine Estuary",
            "depth": f"Live Tide: {tide_brv}", "species": "Snook, Tarpon, Black Drum", "bite_index": bite_brv, "bite_delta": bi_del_brv, "barometer": baro_brv, "baro_delta": b_del_brv,
            "structures": [{"path": [[28.1278, -80.6210], [28.1278, -80.6150], [28.1278, -80.6105]], "name": "Eau Gallie Bridge Fender Piling Wall"}],
            "highways": [{"path": [[28.1410, -80.6125], [28.1278, -80.6148], [28.1180, -80.6138]], "name": "Fall Finger Mullet Intracoastal Highway"}],
            "labels": "SNOOK AMBUSH EDDY // Cast tight to fenders"
        },
        {
            "water_name": "Melbourne Causeway Deep Relief Spans", "lat": 28.0784, "lon": -80.5920, "env": "Coastal Marine Estuary",
            "depth": f"Live Tide: {tide_brv}", "species": "Tarpon, Snook, Ladyfish", "bite_index": bite_brv, "bite_delta": bi_del_brv, "barometer": baro_brv, "baro_delta": b_del_brv,
            "structures": [{"path": [[28.0784, -80.6015], [28.0784, -80.5920], [28.0784, -80.5852]], "name": "Main Causeway Channel Span Fender"}],
            "highways": [{"path": [[28.0920, -80.5952], [28.0784, -80.5952], [28.0680, -80.5952]], "name": "Nocturnal Blue Crab Drift Run"}],
            "labels": "TARPON INTERCEPT // Live threadfins in channel"
        },
        {
            "water_name": "Max Brewer Fishing Pier (Titusville)", "lat": 28.6253, "lon": -80.7940, "env": "Coastal Marine Estuary",
            "depth": f"Live Tide: {tide_brv}", "species": "Black Drum, Spotted Seatrout, Redfish", "bite_index": 78, "bite_delta": "STABLE", "barometer": baro_brv, "baro_delta": b_del_brv,
            "structures": [{"path": [[28.6260, -80.8010], [28.6253, -80.7940], [28.6241, -80.7890]], "name": "Barnacle Piling Structure Grid"}],
            "highways": [{"path": [[28.6380, -80.7940], [28.6253, -80.7940], [28.6140, -80.7940]], "name": "Juvenile Menhaden Spring Migration"}],
            "labels": "BLACK DRUM SEAM // Drop crab halves vertically"
        },
        {
            "water_name": "Sebastian Inlet State Park North Jetty Edge", "lat": 27.8605, "lon": -80.4440, "env": "Coastal Marine Estuary",
            "depth": f"Live Tide: {tide_brv}", "species": "Snook, Redfish, Flounder, Tarpon", "bite_index": bite_brv, "bite_delta": bi_del_brv, "barometer": baro_brv, "baro_delta": b_del_brv,
            "structures": [{"path": [[27.8605, -80.4480], [27.8605, -80.4440], [27.8605, -80.4400]], "name": "Granite Rock Inlet Jetty Guard"}],
            "highways": [{"path": [[27.8680, -80.4440], [27.8605, -80.4440], [27.8520, -80.4440]], "name": "Major Pelagic Inlet Entry Corridor"}],
            "labels": "SNOOK BULKHEAD RUN // Cast bucktails on outgoing tide"
        },
        {
            "water_name": "Pineda Causeway Open Navigation Channels", "lat": 28.2085, "lon": -80.6650, "env": "Coastal Marine Estuary",
            "depth": f"Live Tide: {tide_brv}", "species": "Spotted Seatrout, Redfish, Jack Crevalle", "bite_index": 81, "bite_delta": "STABLE", "barometer": baro_brv, "baro_delta": b_del_brv,
            "structures": [{"path": [[28.2085, -80.6750], [28.2085, -80.6650], [28.2085, -80.6550]], "name": "Concrete Causeway Trestle Arrays"}],
            "highways": [{"path": [[28.2200, -80.6650], [28.2085, -80.6650], [28.1950, -80.6650]], "name": "Lagoon Core Baitfish Runway"}],
            "labels": "GATOR SEATROUT SLOUGH // Work soft plastics over potholes"
        }
    ]
    
    # 3. Alachua County Data
    matrix["Alachua"] = [
        {
            "water_name": "Windsor Boat Access (Newnans Lake East)", "lat": 29.6450, "lon": -82.2150, "env": "Inland Freshwater System", "depth": "4 - 8 ft", "species": "Largemouth Bass, Crappie, Bluegill", "bite_index": 70, "bite_delta": "STABLE", "barometer": 29.80, "baro_delta": "0.00",
            "structures": [{"path": [[29.6550, -82.2225], [29.6450, -82.2180]], "name": "Submerged Cypress Edge"}], 
            "highways": [{"path": [[29.6580, -82.2110], [29.6450, -82.2140]], "name": "Shad Run"}], 
            "labels": "BASS GRASS LINES // Flip pads along edges"
        },
        {
            "water_name": "Owens-Illinois Basin (Newnans Lake North)", "lat": 29.6822, "lon": -82.2350, "env": "Inland Freshwater System", "depth": "3 - 6 ft", "species": "Black Crappie, Bluegill, Warmouth", "bite_index": 75, "bite_delta": "STABLE", "barometer": 29.81, "baro_delta": "0.00",
            "structures": [{"path": [[29.6840, -82.2460], [29.6810, -82.2270]], "name": "Pad Contours"}], 
            "highways": [{"path": [[29.6910, -82.2350], [29.6730, -82.2350]], "name": "Shiner Lane"}], 
            "labels": "CRAPPIE LILY PADS // Suspended minnows deep"
        },
        {
            "water_name": "Lochloosa Harbor Open Ramp Area", "lat": 29.5085, "lon": -82.1795, "env": "Inland Freshwater System", "depth": "5 - 10 ft", "species": "Largemouth Bass, Black Crappie", "bite_index": 85, "bite_delta": "STABLE", "barometer": 29.83, "baro_delta": "0.00",
            "structures": [{"path": [[29.5085, -82.1900], [29.5085, -82.1650]], "name": "Old Pier Remnants"}], 
            "highways": [{"path": [[29.5250, -82.1795], [29.4900, -82.1795]], "name": "Basin Highway"}], 
            "labels": "TROPHY BASS PROFILE // Pitch worms around pilings"
        },
        {
            "water_name": "Cross Creek Connecting Water Flume", "lat": 29.4855, "lon": -82.1645, "env": "Inland Freshwater System", "depth": "4 - 9 ft", "species": "Bluegill, Sunfish, Channel Catfish", "bite_index": 80, "bite_delta": "STABLE", "barometer": 29.84, "baro_delta": "0.00",
            "structures": [{"path": [[29.4920, -82.1680], [29.4750, -82.1610]], "name": "Connecting Trench"}], 
            "highways": [{"path": [[29.4990, -82.1645], [29.4700, -82.1645]], "name": "Forage Expressway"}], 
            "labels": "PANFISH FLOW CHANNEL // Fish live crickets in current"
        },
        {
            "water_name": "Orange Lake Public Open Water Basin", "lat": 29.4650, "lon": -82.1750, "env": "Inland Freshwater System", "depth": "5 - 12 ft", "species": "Trophy Largemouth Bass, Crappie", "bite_index": 88, "bite_delta": "STABLE", "barometer": 29.86, "baro_delta": "0.00",
            "structures": [{"path": [[29.4650, -82.1950], [29.4650, -82.1550]], "name": "Tussock Root Barriers"}], 
            "highways": [{"path": [[29.4850, -82.1750], [29.4450, -82.1750]], "name": "Weed-line Channel"}], 
            "labels": "BASS MAT PUNCHING ZONE // Heavy tungsten rigs inside weeds"
        }
    ]
    
    # 4. Bay County Data
    baro_bay, b_del_bay, bite_bay, bi_del_bay, tide_bay = get_noaa_live_telemetry("PCBF1", "8729108")
    matrix["Bay"] = [
        {
            "water_name": "Russell-Fields City Pier (PCB Ocean)", "lat": 30.2132, "lon": -85.8810, "env": "Coastal Marine Estuary", 
            "depth": f"Live Tide: {tide_bay}", "species": "King Mackerel, Spanish Mackerel, Cobia", "bite_index": bite_bay, "bite_delta": bi_del_bay, "barometer": baro_bay, "baro_delta": b_del_bay,
            "structures": [{"path": [[30.2132, -85.8791], [30.2045, -85.8835]], "name": "Concrete Pillars"}], 
            "highways": [{"path": [[30.2112, -85.9100], [30.2122, -85.8550]], "name": "Surf Trough Route"}], 
            "labels": "KING MACKEREL RUNWAY // Free-line live runners"
        },
        {
            "water_name": "St. Andrews State Park Shipping Pass", "lat": 30.1265, "lon": -85.7342, "env": "Coastal Marine Estuary",
            "depth": f"Live Tide: {tide_bay}", "species": "Gag Grouper, Red Snapper, Sheepshead", "bite_index": bite_bay, "bite_delta": bi_del_bay, "barometer": baro_bay, "baro_delta": b_del_bay,
            "structures": [{"path": [[30.1265, -85.7410], [30.1210, -85.7300]], "name": "Deep Shipping Channel Jet Rock Wall"}],
            "highways": [{"path": [[30.1400, -85.7500], [30.1265, -85.7342]], "name": "Gag Grouper Migration Slot"}],
            "labels": "PASS AMBUSH ZONE // Drift pinfish deep"
        },
        {
            "water_name": "Frank Brown Park Youth Fishing Pond", "lat": 30.2230, "lon": -85.8640, "env": "Inland Freshwater System",
            "depth": "3 - 8 ft", "species": "Channel Catfish, Bluegill, Largemouth Bass", "bite_index": 72, "bite_delta": "STABLE", "barometer": baro_bay, "baro_delta": b_del_bay,
            "structures": [{"path": [[30.2230, -85.8660], [30.2230, -85.8620]], "name": "Shoreline Mud Flat Transition"}],
            "highways": [{"path": [[30.2250, -85.8640], [30.2210, -85.8640]], "name": "Aerator Flow Highway"}],
            "labels": "CATFISH FLATS // Bottom fish with chicken liver"
        },
        {
            "water_name": "Carl Gray Park Boat Launch", "lat": 30.1830, "lon": -85.7170, "env": "Coastal Marine Estuary",
            "depth": f"Live Tide: {tide_bay}", "species": "Spotted Seatrout, Redfish, Flounder", "bite_index": 76, "bite_delta": "STABLE", "barometer": baro_bay, "baro_delta": b_del_bay,
            "structures": [{"path": [[30.1830, -85.7190], [30.1830, -85.7150]], "name": "Launch Ramp Concrete Apron"}],
            "highways": [{"path": [[30.1890, -85.7170], [30.1790, -85.7170]], "name": "Bridge Channel Bait Pipeline"}],
            "labels": "DOCK LINE SEATROUT // Work swimbaits around boat slips"
        },
        {
            "water_name": "Grand Lagoon Navigation Channel", "lat": 30.1340, "lon": -85.7510, "env": "Coastal Marine Estuary",
            "depth": f"Live Tide: {tide_bay}", "species": "Mangrove Snapper, Redfish, Flounder", "bite_index": 84, "bite_delta": "STABLE", "barometer": baro_bay, "baro_delta": b_del_bay,
            "structures": [{"path": [[30.1340, -85.7550], [30.1340, -85.7470]], "name": "Grand Lagoon Seawall Piling Arrays"}],
            "highways": [{"path": [[30.1400, -85.7510], [30.1280, -85.7510]], "name": "Grand Lagoon Deep Dredge Trench"}],
            "labels": "MANGROVE SNAPPER WALL // Light fluorocarbon with live shrimp"
        }
    ]

    # Structural backup grids for remaining unpopulated counties
    for county in fl_counties:
        if not matrix[county]:
            matrix[county] = [
                {
                    "water_name": f"{county} Baseline Tactical Zone", "lat": 27.6648, "lon": -81.5158, "env": "Standard Baseline",
                    "depth": "5 - 15 ft", "species": "Scouting Array Initialized", "bite_index": 75, "bite_delta": "STABLE", "barometer": 29.92, "baro_delta": "0.00",
                    "structures": [], "highways": [], "labels": f"{county.upper()} OVERLAY TERMINAL ACTIVE"
                }
            ]
            
    return matrix

data_matrix = load_statewide_tactical_matrix()

# --- TOP SELECTOR PANEL ---
st.markdown("<div class='console-header'>UNIVERSAL REGIONAL ACCESSIBILITY CONSOLE</div>", unsafe_allow_html=True)

col_sel1, col_sel2 = st.columns(2)

with col_sel1:
    selected_county = st.selectbox(
        "Isolate Active County Cluster (67-County System Map Active):", 
        options=sorted(list(data_matrix.keys()))
    )

active_locations = data_matrix[selected_county]
location_names = [loc["water_name"] for loc in active_locations]

with col_sel2:
    selected_location_name = st.selectbox(
        "Select Target Launch / Fishing Access Site Point:", 
        options=location_names
    )

target_segment = next(loc for loc in active_locations if loc["water_name"] == selected_location_name)

# --- DUAL ROW MATRIX DISPLAY ---
col_map, col_readouts = st.columns([1.3, 1])

with col_map:
    st.markdown("<div class='section-header'>VERIFIED UNIVERSAL GEOSPATIAL RADAR</div>", unsafe_allow_html=True)
    st.write(f"Active Scouting Coordinates Center: `{selected_location_name}`")
    
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
    st.markdown("<div class='section-header'>TARGET ACCESS AREA READOUTS</div>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown(f"<span class='badge-label'>Isolated Domain Region:</span> <span class='badge-gray'>{selected_county} County</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='badge-label'>Water Location Target Site:</span> <span class='badge-cyan'>{target_segment['water_name']}</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='badge-label'>Classification Cohort Layer:</span> <span class='badge'>{target_segment['env']}</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='badge-label'>Target Depth Column:</span> <span class='badge-gray'>{target_segment['depth']}</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='badge-label'>Target Species Focus:</span> <span class='badge-cyan'>{target_segment['species']}</span>", unsafe_allow_html=True)
    
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        with st.container(border=True):
            st.metric(
                label="DYNAMIC BITE INDEX",
                value=f"{target_segment['bite_index']}/100",
                delta=target_segment["bite_delta"]
            )
        
    with col_m2:
        with st.container(border=True):
            try:
                d_val = float(target_segment["baro_delta"])
            except ValueError:
                d_val = 0.0
                
            st.metric(
                label="LOCAL BAROMETER",
                value=f"{target_segment['barometer']} inHg",
                delta=f"{target_segment['baro_delta']} inHg" if d_val != 0 else "HOLDING SYSTEM STABLE",
                delta_color="normal" if d_val >= 0 else "inverse"
            )

# 30-Second live network query interval rerun step
time.sleep(30)
st.rerun()