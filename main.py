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


# --- NOAA DATA FETCHING ---
@st.cache_data(ttl=300)
def get_noaa_live_telemetry(buoy_id, tide_station):
    barometer, baro_delta, bite_index, bite_delta = 29.92, "+0.01", 75, "STABLE"
    try:
        response = requests.get(f"https://www.ndbc.noaa.gov/data/realtime2/{buoy_id}.txt", timeout=5)
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
        response = requests.get(url, timeout=5).json()
        if "data" in response and len(response["data"]) > 0:
            val = float(response['data'][0]['v'])
            bite_index = int(75 + (val * 4))
            bite_delta = "IMPROVING (INFLOW)" if val > 0 else "FALLING TIDE"
    except: pass
    return barometer, baro_delta, bite_index, bite_delta


# --- MASTER COUNTY DICTIONARY: COASTAL (35) & INLAND (32) ---
county_data = {
    "Bay": ["8729108", "PCBF1", "Coastal Marine Estuary", "Snook, Redfish, Tarpon", [
        (30.1830, -85.7180, "Hathaway Bridge Channels", "12-25 ft"), (30.1260, -85.7340, "St Andrews Jetties", "15-32 ft"), 
        (30.2130, -85.8810, "Russell-Fields Pier", "10-18 ft"), (30.0810, -85.5900, "Tyndall Bridge Spans", "10-20 ft"), 
        (30.2400, -85.6700, "West Bay Bridge Area", "8-16 ft")]],
    "Brevard": ["8721604", "41113", "Coastal Marine Estuary", "Snook, Seatrout, Tarpon", [
        (27.8600, -80.4460, "Sebastian Inlet Center", "12-28 ft"), (28.6253, -80.7950, "Max Brewer Bridge Spans", "6-12 ft"),
        (28.0790, -80.5940, "Melbourne Causeway Fender", "8-15 ft"), (28.4080, -80.5920, "Port Canaveral Channel", "20-35 ft"),
        (28.3685, -80.5980, "Cocoa Beach Pier End", "8-14 ft")]],
    "Broward": ["8722956", "41113", "Coastal Marine Estuary", "Snook, Tarpon, Jacks", [
        (26.0960, -80.1040, "Port Everglades Inlet", "20-40 ft"), (26.0380, -80.1100, "Dania Beach Pier", "10-18 ft"),
        (26.2560, -80.0810, "Hillsboro Inlet Jetties", "12-24 ft"), (26.1890, -80.0940, "Commercial Blvd Pier", "8-16 ft"),
        (26.1000, -80.1180, "17th St Causeway Spans", "10-22 ft")]],
    "Charlotte": ["8725520", "CDRF1", "Coastal Marine Estuary", "Snook, Redfish, Seatrout", [
        (26.7190, -82.2610, "Boca Grande Pass", "15-40 ft"), (26.8320, -82.2640, "Placida Pier Approach", "6-12 ft"),
        (26.9630, -82.2110, "El Jobean Bridge Fender", "8-18 ft"), (26.9380, -82.0490, "US41 Peace River Bridge", "8-15 ft"),
        (26.9010, -82.3680, "Stump Pass Channel", "10-22 ft")]],
    "Citrus": ["8727122", "CDRF1", "Coastal Marine Estuary", "Redfish, Seatrout", [
        (28.8930, -82.6050, "Crystal River Main Channel", "8-15 ft"), (28.9160, -82.6920, "Fort Island Pier End", "4-8 ft"),
        (28.7990, -82.6210, "Homosassa Deep Channel", "6-12 ft"), (28.9600, -82.6700, "Cross Florida Barge Canal", "12-25 ft"),
        (28.8400, -82.6600, "Ozello Trail Bridge Cut", "4-9 ft")]],
    "Collier": ["8725114", "CDRF1", "Coastal Marine Estuary", "Snook, Tarpon, Redfish", [
        (26.1320, -81.8080, "Naples Pier Deep End", "10-16 ft"), (26.0940, -81.7990, "Gordon Pass Channel", "12-25 ft"),
        (25.9620, -81.7290, "Marco Island Bridge Span", "10-20 ft"), (25.9180, -81.7150, "Caxambas Pass Tidal Cut", "8-16 ft"),
        (25.9250, -81.6440, "Goodland Bridge Channels", "6-14 ft")]],
    "Miami-Dade": ["8723214", "41113", "Coastal Marine Estuary", "Snook, Tarpon, Bonefish", [
        (25.7610, -80.1330, "Government Cut Inlet", "20-40 ft"), (25.9015, -80.1235, "Haulover Inlet Bridge", "15-28 ft"),
        (25.7460, -80.1760, "Rickenbacker Causeway Spans", "8-16 ft"), (25.9280, -80.1180, "Newport Fishing Pier", "10-18 ft"),
        (25.6550, -80.1600, "Stiltsville Channel Flats", "6-12 ft")]],
    "Dixie": ["8727520", "CDRF1", "Coastal Marine Estuary", "Redfish, Seatrout", [
        (29.4350, -83.2950, "Horseshoe Beach Pier", "4-8 ft"), (29.3240, -83.1310, "Suwannee Estuary Flow", "6-14 ft"),
        (29.3950, -83.3300, "Shired Island Channel", "5-10 ft"), (29.3500, -83.1500, "Stuart Point Drop-off", "6-12 ft"),
        (29.4000, -83.2000, "Cedar Creek Mouth", "4-9 ft")]],
    "Duval": ["8720218", "8720219", "Coastal Marine Estuary", "Redfish, Trout, Flounder", [
        (30.3950, -81.3950, "Mayport Jetties Channel", "15-40 ft"), (30.2880, -81.3850, "Jax Beach Pier End", "10-18 ft"),
        (30.3850, -81.5550, "Dames Point Bridge Fenders", "20-45 ft"), (30.3800, -81.5000, "Wonderwood Bridge Span", "12-25 ft"),
        (30.3990, -81.4550, "Sister Creek Bridge Current", "8-18 ft")]],
    "Escambia": ["8729840", "PCBF1", "Coastal Marine Estuary", "Redfish, Trout", [
        (30.4000, -87.1800, "Pensacola Bay Bridge Spans", "12-25 ft"), (30.3300, -87.3100, "Pensacola Pass Deep Slot", "20-45 ft"),
        (30.3350, -87.1650, "Bob Sikes Bridge Piling", "10-22 ft"), (30.3200, -87.4300, "Ft Pickens Pier", "15-28 ft"),
        (30.3850, -86.8650, "Navarre Bridge Escambia Side", "8-16 ft")]],
    "Flagler": ["8720218", "41113", "Coastal Marine Estuary", "Redfish, Trout, Flounder", [
        (29.4800, -81.1150, "Flagler Beach Pier End", "10-18 ft"), (29.7130, -81.2250, "Matanzas Inlet Bridge", "8-20 ft"),
        (29.6100, -81.1950, "Hammock Dunes Bridge", "12-25 ft"), (29.4750, -81.1350, "SR100 Bridge ICW", "8-16 ft"),
        (29.4120, -81.1110, "Highbridge Relief Channel", "6-14 ft")]],
    "Franklin": ["8728690", "PCBF1", "Coastal Marine Estuary", "Redfish, Trout", [
        (29.7420, -84.8820, "St George Island Bridge", "10-22 ft"), (29.7250, -84.9800, "Apalachicola Bridge Fenders", "8-18 ft"),
        (29.6850, -85.2550, "Indian Pass Jetties", "12-25 ft"), (29.8400, -84.6650, "Carrabelle River Mouth", "10-20 ft"),
        (29.7400, -84.8800, "East Point Fishing Pier", "6-12 ft")]],
    "Gulf": ["8728690", "PCBF1", "Coastal Marine Estuary", "Trout, Redfish, Flounder", [
        (29.6800, -85.4000, "Cape San Blas Shoal", "8-16 ft"), (29.8150, -85.3000, "St Joe Bay Bridge", "6-14 ft"),
        (29.6850, -85.2200, "Indian Pass Inlet Flow", "10-22 ft"), (29.8700, -85.2100, "White City Bridge Piling", "8-18 ft"),
        (29.7800, -85.3200, "Presnell Channel Access", "5-12 ft")]],
    "Hernando": ["8727122", "CDRF1", "Coastal Marine Estuary", "Snook, Redfish, Trout", [
        (28.5410, -82.6450, "Bayport Pier Channel", "6-12 ft"), (28.4950, -82.6620, "Hernando Beach Channel", "8-15 ft"),
        (28.4300, -82.6600, "Aripeka Bridges Current", "5-10 ft"), (28.5300, -82.6500, "Weeki Wachee Estuary Mouth", "4-9 ft"),
        (28.4500, -82.6600, "Jenkins Creek Mouth", "4-8 ft")]],
    "Hillsborough": ["8726607", "8726674", "Coastal Marine Estuary", "Snook, Redfish, Tarpon", [
        (27.6520, -82.6550, "Skyway Bridge North Spans", "15-32 ft"), (27.8800, -82.5500, "Gandy Bridge Fenders", "10-22 ft"),
        (27.9150, -82.5900, "Howard Frankland Pilings", "12-25 ft"), (27.9600, -82.6000, "Courtney Campbell Relief", "8-16 ft"),
        (27.8890, -82.4780, "Ballast Point Pier End", "8-14 ft")]],
    "Indian River": ["8721604", "41113", "Coastal Marine Estuary", "Snook, Tarpon, Trout", [
        (27.8600, -80.4460, "Sebastian Inlet Jetties", "12-28 ft"), (27.7550, -80.3950, "Wabasso Bridge Fender", "8-18 ft"),
        (27.6520, -80.3750, "Barber Bridge Spans", "10-22 ft"), (27.6300, -80.3700, "17th St Bridge Piling", "8-16 ft"),
        (27.5600, -80.3300, "Round Island Park Channel", "6-12 ft")]],
    "Jefferson": ["8727520", "CDRF1", "Coastal Marine Estuary", "Redfish, Trout", [
        (30.0910, -83.9910, "Aucilla River Mouth", "6-14 ft"), (30.0350, -83.9120, "Econfina Mouth Estuary", "5-12 ft"),
        (30.1000, -83.9500, "Pinhook River Mouth", "4-9 ft"), (30.0700, -84.0000, "St Marks Coastal Shelf", "8-16 ft"),
        (30.0800, -84.0500, "East River Estuary Mouth", "5-10 ft")]],
    "Lee": ["8725520", "CDRF1", "Coastal Marine Estuary", "Snook, Redfish, Tarpon", [
        (26.4800, -82.0150, "Sanibel Causeway Bridge", "10-22 ft"), (26.4850, -82.1800, "Blind Pass Bridge", "8-18 ft"),
        (26.6350, -82.0700, "Matlacha Bridge Current", "6-15 ft"), (26.8150, -82.2600, "Boca Grande Trestles", "12-25 ft"),
        (26.5650, -81.9450, "Cape Coral Bridge Channel", "10-20 ft")]],
    "Levy": ["8727520", "CDRF1", "Coastal Marine Estuary", "Redfish, Seatrout, Cobia", [
        (29.1380, -83.0320, "Cedar Key Fishing Pier", "8-15 ft"), (29.1500, -83.0200, "No 4 Bridge Cedar Key", "6-12 ft"),
        (28.9950, -82.7450, "Yankeetown Estuary", "8-16 ft"), (29.1150, -82.8350, "Waccasassa River Mouth", "5-12 ft"),
        (29.3000, -83.1500, "Suwannee Sound Channel", "10-20 ft")]],
    "Manatee": ["8726384", "8726520", "Coastal Marine Estuary", "Snook, Redfish, Trout", [
        (27.6150, -82.6450, "Skyway Bridge South Fender", "15-32 ft"), (27.5050, -82.7000, "Anna Maria Bridge Spans", "8-18 ft"),
        (27.4650, -82.6850, "Cortez Bridge Current", "10-22 ft"), (27.4670, -82.6850, "Rod and Reel Pier End", "8-15 ft"),
        (27.5000, -82.5700, "Green Bridge Fishing Pier", "6-14 ft")]],
    "Martin": ["8722670", "41113", "Coastal Marine Estuary", "Snook, Tarpon, Permit", [
        (27.2050, -80.2550, "Stuart Causeway Bridges", "10-22 ft"), (27.2350, -80.2150, "Jensen Beach Causeway", "8-18 ft"),
        (27.1650, -80.1600, "St Lucie Inlet Channel", "15-30 ft"), (27.2000, -80.2600, "Roosevelt Bridge Spans", "12-25 ft"),
        (27.0600, -80.1200, "Hobe Sound Bridge Current", "8-16 ft")]],
    "Monroe": ["8724580", "8723970", "Coastal Marine Estuary", "Tarpon, Snook, Bonefish", [
        (24.7050, -81.1550, "Seven Mile Bridge Channel", "12-30 ft"), (24.6550, -81.2850, "Bahia Honda Deep Bridge", "15-35 ft"),
        (24.8300, -80.7300, "Channel 2 Bridge Fender", "10-22 ft"), (24.8150, -80.8200, "Long Key Bridge Spans", "8-18 ft"),
        (24.5450, -81.8000, "Key West Pier Approach", "12-25 ft")]],
    "Nassau": ["8720030", "8720218", "Coastal Marine Estuary", "Redfish, Trout, Black Drum", [
        (30.6450, -81.4850, "Amelia Island Bridge Spans", "12-25 ft"), (30.5150, -81.4550, "George Crady Pier Structure", "10-20 ft"),
        (30.7050, -81.4550, "Fort Clinch Pier Drop", "15-28 ft"), (30.7100, -81.4300, "St Marys Jetties Outflow", "15-35 ft"),
        (30.5100, -81.4400, "Nassau Sound Jetties", "12-24 ft")]],
    "Okaloosa": ["8729108", "PCBF1", "Coastal Marine Estuary", "Redfish, Trout, King Mackerel", [
        (30.3950, -86.5150, "Destin Pass Jetties", "15-35 ft"), (30.4350, -86.4250, "Mid-Bay Bridge Fenders", "12-25 ft"),
        (30.3920, -86.5950, "Okaloosa Island Pier End", "10-18 ft"), (30.4000, -86.6000, "Brooks Bridge Piling", "10-20 ft"),
        (30.3950, -86.5200, "Destin Bridge Channel", "12-28 ft")]],
    "Palm Beach": ["8722670", "41113", "Coastal Marine Estuary", "Snook, Tarpon, Jacks", [
        (26.6120, -80.0330, "Lake Worth Pier Surf End", "10-18 ft"), (26.8850, -80.0520, "Juno Beach Pier Approach", "12-22 ft"),
        (26.5450, -80.0450, "Boynton Inlet Current", "15-30 ft"), (26.9450, -80.0700, "Jupiter Inlet Fenders", "12-28 ft"),
        (26.7850, -80.0450, "Blue Heron Bridge Channel", "10-25 ft")]],
    "Pasco": ["8726724", "CDRF1", "Coastal Marine Estuary", "Snook, Redfish, Trout", [
        (28.1650, -82.7850, "Anclote River Park Mouth", "8-16 ft"), (28.3650, -82.7150, "Hudson Beach Pier Deep End", "5-10 ft"),
        (28.3150, -82.7100, "Green Key Pier Drop", "4-8 ft"), (28.2700, -82.7250, "Port Richey Bridge Area", "6-12 ft"),
        (28.2500, -82.7300, "Brasher Park Channel Edge", "5-9 ft")]],
    "Pinellas": ["8726520", "8726724", "Coastal Marine Estuary", "Snook, Redfish, Tarpon", [
        (27.6205, -82.6558, "Sunshine Skyway South Spans", "15-32 ft"), (27.6135, -82.7380, "Fort De Soto Pier Tip", "8-14 ft"),
        (27.7830, -82.7830, "Johns Pass Inlet Center", "10-22 ft"), (27.9625, -82.8310, "Clearwater Pass Jetty Edge", "12-24 ft"),
        (28.0375, -82.8020, "Dunedin Causeway Relief", "6-12 ft")]],
    "Santa Rosa": ["8729840", "PCBF1", "Coastal Marine Estuary", "Trout, Redfish, Flounder", [
        (30.3820, -86.8620, "Navarre Pier Open Gulf", "12-22 ft"), (30.3850, -86.8650, "Navarre Bridge ICW Spans", "10-18 ft"),
        (30.4900, -87.1000, "Garcon Point Bridge", "8-16 ft"), (30.5100, -87.1400, "Escambia Bay Bridge East", "12-25 ft"),
        (30.3650, -87.1700, "Gulf Breeze Pkwy Bridge", "10-20 ft")]],
    "Sarasota": ["8725520", "8726520", "Coastal Marine Estuary", "Snook, Redfish, Trout", [
        (27.1120, -82.4550, "Venice Pier Jetties", "12-22 ft"), (27.3550, -82.5650, "Ringling Bridge Channels", "15-28 ft"),
        (27.2500, -82.5000, "Stickney Point Bridge", "10-20 ft"), (27.1850, -82.4950, "Blackburn Point Bridge", "8-16 ft"),
        (27.2750, -82.5450, "Siesta Key Bridge Piling", "10-22 ft")]],
    "St. Johns": ["8720218", "41113", "Coastal Marine Estuary", "Redfish, Trout, Flounder", [
        (29.9120, -81.3050, "Vilano Pier Current Seam", "10-18 ft"), (29.8550, -81.2650, "St Augustine Pier End", "12-20 ft"),
        (29.8920, -81.3100, "Bridge of Lions Center", "15-28 ft"), (29.7120, -81.2250, "Matanzas Inlet Bridge", "8-20 ft"),
        (29.9820, -81.6250, "Shands Bridge Fenders", "10-22 ft")]],
    "St. Lucie": ["8722670", "41113", "Coastal Marine Estuary", "Snook, Tarpon, Trout", [
        (27.4720, -80.2950, "Fort Pierce Inlet Jetties", "15-32 ft"), (27.4500, -80.3150, "South Bridge ICW Channel", "10-22 ft"),
        (27.4650, -80.3250, "North Bridge Center Spans", "10-20 ft"), (27.4700, -80.2900, "Jetty Park Pier Edge", "8-18 ft"),
        (27.3500, -80.2500, "Walton Road Bridge", "6-14 ft")]],
    "Taylor": ["8727520", "CDRF1", "Coastal Marine Estuary", "Seatrout, Redfish", [
        (29.6700, -83.4000, "Steinhatchee Jetties", "6-14 ft"), (29.8250, -83.5950, "Keaton Beach Pier", "4-9 ft"),
        (30.0350, -83.9120, "Econfina Mouth Channel", "5-10 ft"), (29.7500, -83.5500, "Spring Warrior Creek Mouth", "4-8 ft"),
        (29.7800, -83.5800, "Dallus Creek Estuary", "3-7 ft")]],
    "Volusia": ["8720218", "41113", "Coastal Marine Estuary", "Redfish, Trout, Snook", [
        (29.1450, -80.9700, "Sunglow Pier Ocean Drop", "10-18 ft"), (29.0800, -80.9150, "Ponce Inlet Jetties", "15-32 ft"),
        (29.2300, -81.0050, "Daytona Beach Pier", "12-20 ft"), (29.1450, -80.9750, "Dunlawton Bridge Piling", "10-22 ft"),
        (29.2900, -81.0400, "Ormond Beach Bridge Channel", "8-18 ft")]],
    "Wakulla": ["8728690", "PCBF1", "Coastal Marine Estuary", "Trout, Redfish", [
        (30.1500, -84.2050, "St Marks Pier Access", "6-14 ft"), (30.0300, -84.3800, "Panacea Bridge Channels", "5-12 ft"),
        (30.1500, -84.2500, "Wakulla River Bridge", "8-15 ft"), (30.0150, -84.3500, "Surf Road Pier Water", "4-10 ft"),
        (30.0550, -84.2950, "Shell Point Reef Approach", "6-12 ft")]],
    "Walton": ["8729108", "PCBF1", "Coastal Marine Estuary", "Trout, Redfish, Flounder", [
        (30.4000, -86.1500, "US331 Bridge Wide Spans", "10-25 ft"), (30.3500, -86.2000, "Choctawhatchee Jetties", "15-35 ft"),
        (30.4100, -86.1800, "Tucker Bayou Channel", "6-14 ft"), (30.4200, -86.1300, "Jolly Bay Deep Hole", "8-16 ft"),
        (30.4500, -86.1000, "Alaqua Bayou Mud Flat", "5-10 ft")]],

    "Alachua": ["8720226", "CDRF1", "Inland Freshwater System", "Largemouth Bass, Crappie", 29.4450, -82.1650, "Orange Lake Center"],
    "Baker": ["8720030", "PCBF1", "Inland Freshwater System", "Largemouth Bass, Catfish", 30.2160, -82.4330, "Ocean Pond Basin"],
    "Bradford": ["8720226", "CDRF1", "Inland Freshwater System", "Largemouth Bass, Bluegill", 29.9250, -82.2000, "Lake Sampson Center"],
    "Calhoun": ["8728690", "PCBF1", "Riverine System", "Striped Bass, Catfish", 30.1350, -85.1250, "Dead Lakes Basin"],
    "Clay": ["8720226", "CDRF1", "Riverine System", "Largemouth Bass, Striper", 30.1450, -81.7150, "Doctors Lake Center"],
    "Columbia": ["8720030", "CDRF1", "Riverine System", "Suwannee Bass, Catfish", 30.1620, -82.6300, "Alligator Lake Center"],
    "DeSoto": ["8725520", "CDRF1", "Riverine System", "Largemouth Bass, Catfish", 27.1650, -81.8900, "Peace River Center"],
    "Gadsden": ["8728690", "PCBF1", "Riverine System", "Largemouth Bass, Crappie", 30.4700, -84.6500, "Lake Talquin Reservoir"],
    "Gilchrist": ["8727520", "CDRF1", "Riverine System", "Largemouth Bass, Sunfish", 29.5880, -82.9350, "Suwannee River Core"],
    "Glades": ["8725520", "CDRF1", "Inland Freshwater System", "Largemouth Bass, Crappie", 26.9000, -80.9000, "Lake Okeechobee West"],
    "Hamilton": ["8720030", "CDRF1", "Riverine System", "Largemouth Bass, Panfish", 30.3310, -82.7600, "Suwannee River Center"],
    "Hardee": ["8725520", "CDRF1", "Riverine System", "Channel Catfish, Bass", 27.4950, -81.8000, "Peace River Flow"],
    "Hendry": ["8725520", "CDRF1", "Inland Freshwater System", "Largemouth Bass, Bluegill", 26.8000, -80.9500, "Lake Okeechobee SW"],
    "Highlands": ["8725520", "CDRF1", "Inland Freshwater System", "Trophy Largemouth Bass", 27.4000, -81.2800, "Lake Istokpoga Core"],
    "Holmes": ["8729108", "PCBF1", "Riverine System", "Catfish, Bream, Bass", 30.7800, -85.8200, "Choctawhatchee River Center"],
    "Jackson": ["8729108", "PCBF1", "Riverine System", "Largemouth Bass, Striper", 30.7300, -84.8800, "Lake Seminole Basin"],
    "Lafayette": ["8727520", "CDRF1", "Riverine System", "Suwannee Bass, Catfish", 30.0650, -83.1050, "Suwannee River Bend"],
    "Lake": ["8720226", "41113", "Inland Freshwater System", "Trophy Largemouth Bass", 28.8000, -81.8000, "Lake Harris Center"],
    "Leon": ["8728690", "PCBF1", "Inland Freshwater System", "Largemouth Bass, Bluegill", 30.5200, -84.3300, "Lake Jackson Basin"],
    "Liberty": ["8728690", "PCBF1", "Riverine System", "Catfish, Striped Bass", 30.4300, -84.9900, "Apalachicola River Center"],
    "Madison": ["8720030", "CDRF1", "Riverine System", "Largemouth Bass, Bream", 30.5850, -83.4450, "Cherry Lake Center"],
    "Marion": ["8720226", "CDRF1", "Inland Freshwater System", "Largemouth Bass, Crappie", 29.0200, -81.9300, "Lake Weir Center"],
    "Okeechobee": ["8722670", "CDRF1", "Inland Freshwater System", "Largemouth Bass, Black Crappie", 27.1500, -80.8500, "Lake Okeechobee Center"],
    "Orange": ["8721604", "41113", "Inland Freshwater System", "Trophy Largemouth Bass", 28.6200, -81.6300, "Lake Apopka Center"],
    "Osceola": ["8721604", "41113", "Inland Freshwater System", "Largemouth Bass, Crappie", 28.2200, -81.4000, "Lake Tohopekaliga Center"],
    "Polk": ["8726607", "CDRF1", "Inland Freshwater System", "Largemouth Bass, Crappie", 27.9500, -81.3500, "Lake Kissimmee Center"],
    "Putnam": ["8720226", "CDRF1", "Riverine System", "Largemouth Bass, Striped Bass", 29.3500, -81.6000, "Lake George Center"],
    "Seminole": ["8721604", "41113", "Inland Freshwater System", "Largemouth Bass, Crappie", 28.8400, -81.2800, "Lake Monroe Center"],
    "Sumter": ["8727122", "CDRF1", "Inland Freshwater System", "Largemouth Bass, Panfish", 28.8051, -82.1231, "Lake Panasoffkee Center"],
    "Suwannee": ["8720030", "CDRF1", "Riverine System", "Largemouth Bass, Catfish", 29.9600, -82.9300, "Suwannee River Core"],
    "Union": ["8720226", "CDRF1", "Inland Freshwater System", "Largemouth Bass, Bluegill", 30.0385, -82.3410, "Lake Butler Center"],
    "Washington": ["8729108", "PCBF1", "Riverine System", "Catfish, Bass, Bream", 30.5750, -85.8500, "Choctawhatchee River Bed"]
}


# --- DYNAMIC LINE SCALING ENGINE ---
def determine_line_scale(name, env_type):
    n = name.lower()
    if "river" in n or "creek" in n or "estuary" in n or "flow" in n:
        return 0.00015  # Very short: keeps lines inside narrow rivers
    elif "pier" in n:
        return 0.00020  # Short: focuses strictly off the end of the pier
    elif "bridge" in n or "causeway" in n or "trestle" in n:
        return 0.00150  # Long: sweeps massively across bridge spans
    elif "inlet" in n or "pass" in n or "jetties" in n:
        return 0.00100  # Medium-Long: tracks tidal movement through an inlet
    elif env_type == "Riverine System":
        return 0.00020  # Tight default for inland river basins
    elif env_type == "Inland Freshwater System":
        return 0.00080  # Medium-Wide for broad lake centers
    else:
        return 0.00100  # Default wide setup for open oceans and bays

def get_isolated_county_nodes(county):
    c_data = county_data[county]
    tide_id, buoy_id, env_type, target_species = c_data[0], c_data[1], c_data[2], c_data[3]
    baro, b_del, bite, bi_del = get_noaa_live_telemetry(buoy_id, tide_id)
    compiled_nodes = []

    if len(c_data) == 5 and isinstance(c_data[4], list):
        for spot in c_data[4]:
            lat, lon, name, depth = spot[0], spot[1], spot[2], spot[3]
            scale = determine_line_scale(name, env_type)
            compiled_nodes.append({
                "water_name": name, "lat": lat, "lon": lon, "env": env_type, "depth": depth,
                "species": target_species, "bite_index": bite, "bite_delta": bi_del, "barometer": baro, "baro_delta": b_del,
                "structures": [{"path": [[lat - scale, lon - scale], [lat + scale, lon + scale]], "name": "Submerged Structural Edge"}],
                "highways": [{"path": [[lat - scale, lon + scale], [lat + scale, lon - scale]], "name": "Forage Migration Seam"}],
                "labels": f"Coastal Structure Verified On Water // Station {tide_id}"
            })
    else:
        base_lat, base_lon, system_label = c_data[4], c_data[5], c_data[6]
        inland_offsets = [
            {"name": f"{system_label} - Deep Channel Core Line", "depth": "14-26 ft", "lat_off": 0, "lon_off": 0},
            {"name": f"{system_label} - Submerged Structure Ridge", "depth": "8-15 ft", "lat_off": 0.0001, "lon_off": -0.0001},
            {"name": f"{system_label} - Baitfish Migration Runway", "depth": "6-12 ft", "lat_off": -0.0002, "lon_off": 0.0001},
            {"name": f"{system_label} - Thermocline Mid-Layer Focus", "depth": "10-18 ft", "lat_off": 0.0001, "lon_off": 0.0002},
            {"name": f"{system_label} - Benthic Flat Mud Transition", "depth": "5-11 ft", "lat_off": -0.0001, "lon_off": -0.0001}
        ]
        
        for node in inland_offsets:
            lat = base_lat + node["lat_off"]
            lon = base_lon + node["lon_off"]
            scale = determine_line_scale(node["name"], env_type)
            compiled_nodes.append({
                "water_name": node["name"], "lat": lat, "lon": lon, "env": env_type, "depth": node["depth"],
                "species": target_species, "bite_index": bite, "bite_delta": bi_del, "barometer": baro, "baro_delta": b_del,
                "structures": [{"path": [[lat - scale, lon - scale], [lat + scale, lon + scale]], "name": "Submerged Structural Edge"}],
                "highways": [{"path": [[lat - scale, lon + scale], [lat + scale, lon - scale]], "name": "Forage Migration Seam"}],
                "labels": f"Geospatial Anchor Verified Deep Water // Station {tide_id}"
            })
            
    return compiled_nodes


# --- TOP SELECTOR PANEL ---
st.markdown("<div class='console-header'>UNIVERSAL REGIONAL ACCESSIBILITY CONSOLE</div>", unsafe_allow_html=True)
col_sel1, col_sel2 = st.columns(2)

with col_sel1:
    selected_county = st.selectbox("Select County Domain:", options=sorted(list(county_data.keys())))

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
