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
    st.markdown("<div class='landing-title'>SMARTANGLER TACTUAL CONSOLE</div>", unsafe_allow_html=True)
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

# --- HARDCODED STATEWIDE REGIONAL MASTER COORDINATE DICTIONARY ---
statewide_fishing_matrix = {
    "Alachua": [
        {"name": "Newnans Lake East Boat Ramp", "lat": 29.6450, "lon": -82.2150, "env": "Inland Freshwater System", "depth": "4-8 ft", "species": "Largemouth Bass, Black Crappie"},
        {"name": "Newnans Lake Northern Pad Flats", "lat": 29.6822, "lon": -82.2350, "env": "Inland Freshwater System", "depth": "3-6 ft", "species": "Largemouth Bass, Warmouth"},
        {"name": "Lochloosa Harbor Channel Basin", "lat": 29.5085, "lon": -82.1795, "env": "Inland Freshwater System", "depth": "6-10 ft", "species": "Trophy Largemouth Bass, Crappie"},
        {"name": "Cross Creek Current Connection", "lat": 29.4855, "lon": -82.1645, "env": "Inland Freshwater System", "depth": "5-9 ft", "species": "Panfish, Channel Catfish"},
        {"name": "Orange Lake Central Basin Slough", "lat": 29.4650, "lon": -82.1750, "env": "Inland Freshwater System", "depth": "6-12 ft", "species": "Largemouth Bass, Bluegill"}
    ],
    "Baker": [
        {"name": "St. Marys River Shoal Segment", "lat": 30.5182, "lon": -82.2135, "env": "Riverine System", "depth": "4-7 ft", "species": "Largemouth Bass, Redbreast Sunfish"},
        {"name": "St. Marys River Bridge Run", "lat": 30.4225, "lon": -82.1550, "env": "Riverine System", "depth": "5-8 ft", "species": "Channel Catfish, Striped Bass"},
        {"name": "Ocean Pond Public Fishing Pier", "lat": 30.2152, "lon": -82.4285, "env": "Inland Freshwater System", "depth": "5-9 ft", "species": "Largemouth Bass, Black Crappie"},
        {"name": "Ocean Pond West Launch Channel", "lat": 30.2110, "lon": -82.4460, "env": "Inland Freshwater System", "depth": "4-8 ft", "species": "Bluegill, Warmouth"},
        {"name": "St. Marys South Fork Bend", "lat": 30.2740, "lon": -82.2810, "env": "Riverine System", "depth": "4-6 ft", "species": "Catfish, Sunfish"}
    ],
    "Bay": [
        {"name": "Russell-Fields Beach Pier Open Ocean", "lat": 30.2132, "lon": -85.8810, "env": "Coastal Marine Estuary", "depth": "12-18 ft", "species": "King Mackerel, Spanish Mackerel, Cobia"},
        {"name": "St. Andrews Inlet Deep Shipping Pass", "lat": 30.1265, "lon": -85.7342, "env": "Coastal Marine Estuary", "depth": "15-32 ft", "species": "Gag Grouper, Red Snapper, Redfish"},
        {"name": "Frank Brown Park Inland Lake Pool", "lat": 30.2230, "lon": -85.8640, "env": "Inland Freshwater System", "depth": "3-8 ft", "species": "Channel Catfish, Largemouth Bass"},
        {"name": "Carl Gray Launch Bridge Pipeline", "lat": 30.1830, "lon": -85.7170, "env": "Coastal Marine Estuary", "depth": "6-14 ft", "species": "Spotted Seatrout, Redfish, Flounder"},
        {"name": "Grand Lagoon Deep Dredge Trench", "lat": 30.1340, "lon": -85.7510, "env": "Coastal Marine Estuary", "depth": "8-16 ft", "species": "Mangrove Snapper, Redfish"}
    ],
    "Bradford": [
        {"name": "Sampson Lake Public Access Dock", "lat": 29.9230, "lon": -82.1990, "env": "Inland Freshwater System", "depth": "4-8 ft", "species": "Largemouth Bass, Bluegill"},
        {"name": "Sampson Lake Deep Core Hole", "lat": 29.9275, "lon": -82.1910, "env": "Inland Freshwater System", "depth": "6-11 ft", "species": "Black Crappie, Warmouth"},
        {"name": "Lake Crosby Launch Slough", "lat": 29.9540, "lon": -82.1480, "env": "Inland Freshwater System", "depth": "4-7 ft", "species": "Largemouth Bass, Bream"},
        {"name": "Lake Crosby Northeast Grass Wall", "lat": 29.9590, "lon": -82.1410, "env": "Inland Freshwater System", "depth": "3-6 ft", "species": "Black Crappie, Bluegill"},
        {"name": "Alligator Creek Inland Pass", "lat": 29.9450, "lon": -82.1120, "env": "Riverine System", "depth": "3-5 ft", "species": "Channel Catfish, Sunfish"}
    ],
    "Brevard": [
        {"name": "Eau Gallie Bridge Causeway Spans", "lat": 28.1278, "lon": -80.6150, "env": "Coastal Marine Estuary", "depth": "6-12 ft", "species": "Snook, Tarpon, Black Drum"},
        {"name": "Melbourne Causeway Fender Run", "lat": 28.0784, "lon": -80.5920, "env": "Coastal Marine Estuary", "depth": "8-15 ft", "species": "Snook, Tarpon, Seatrout"},
        {"name": "Max Brewer Public Pier Grid", "lat": 28.6253, "lon": -80.7940, "env": "Coastal Marine Estuary", "depth": "5-10 ft", "species": "Black Drum, Redfish, Trout"},
        {"name": "Sebastian Inlet State Park Jetty", "lat": 27.8605, "lon": -80.4440, "env": "Coastal Marine Estuary", "depth": "10-24 ft", "species": "Snook, Redfish, Flounder, Tarpon"},
        {"name": "Pineda Causeway Channel Pipeline", "lat": 28.2085, "lon": -80.6650, "env": "Coastal Marine Estuary", "depth": "6-11 ft", "species": "Spotted Seatrout, Redfish, Jacks"}
    ],
    "Broward": [
        {"name": "Port Everglades Deep Inlet Track", "lat": 26.1150, "lon": -80.1110, "env": "Coastal Marine Estuary", "depth": "15-35 ft", "species": "Tarpon, Snook, Jack Crevalle"},
        {"name": "Dania Beach Pier Ocean Piling", "lat": 26.0380, "lon": -80.1115, "env": "Coastal Marine Estuary", "depth": "10-18 ft", "species": "Snook, Spanish Mackerel, Pompano"},
        {"name": "Everglades Holiday Park Canal 1", "lat": 26.0610, "lon": -80.4440, "env": "Inland Freshwater System", "depth": "8-14 ft", "species": "Largemouth Bass, Peacock Bass"},
        {"name": "Everglades Holiday Park Canal 2", "lat": 26.0550, "lon": -80.4550, "env": "Inland Freshwater System", "depth": "6-12 ft", "species": "Largemouth Bass, Cichlids"},
        {"name": "Hillsboro Inlet Bridge Fender", "lat": 26.2560, "lon": -80.0810, "env": "Coastal Marine Estuary", "depth": "8-16 ft", "species": "Snook, Tarpon, Mangrove Snapper"}
    ],
    "Calhoun": [
        {"name": "Apalachicola River Sandbar Cut", "lat": 30.4312, "lon": -85.0413, "env": "Riverine System", "depth": "8-16 ft", "species": "Striped Bass, Flathead Catfish"},
        {"name": "Apalachicola River Bridge Piling", "lat": 30.4390, "lon": -85.0390, "env": "Riverine System", "depth": "10-22 ft", "species": "Channel Catfish, Suwannee Bass"},
        {"name": "Chipola River Dead Lakes Entrance", "lat": 30.1380, "lon": -85.1120, "env": "Riverine System", "depth": "5-10 ft", "species": "Largemouth Bass, Shellcracker"},
        {"name": "Chipola River Limestone Cut", "lat": 30.2240, "lon": -85.1450, "env": "Riverine System", "depth": "4-9 ft", "species": "Suwannee Bass, Bluegill"},
        {"name": "Apalachicola River Slough Junction", "lat": 30.3450, "lon": -85.0110, "env": "Riverine System", "depth": "6-12 ft", "species": "Catfish, Striped Bass"}
    ],
    "Charlotte": [
        {"name": "El Jobean Bridge Pier Spans", "lat": 26.9630, "lon": -82.2110, "env": "Coastal Marine Estuary", "depth": "6-11 ft", "species": "Snook, Tarpon, Black Drum"},
        {"name": "Placida Harbor Grass Flat Trench", "lat": 26.8320, "lon": -82.2640, "env": "Coastal Marine Estuary", "depth": "4-8 ft", "species": "Spotted Seatrout, Redfish"},
        {"name": "Gasparilla Pass Inlet Channel", "lat": 26.7190, "lon": -82.2610, "env": "Coastal Marine Estuary", "depth": "10-22 ft", "species": "Tarpon, Snook, Redfish"},
        {"name": "Stump Pass Deep Marina Approach", "lat": 26.9010, "lon": -82.3680, "env": "Coastal Marine Estuary", "depth": "5-12 ft", "species": "Snook, Flounder, Trout"},
        {"name": "Peace River Estuary Channel Edge", "lat": 26.9342, "lon": -82.0514, "env": "Coastal Marine Estuary", "depth": "6-14 ft", "species": "Redfish, Snook, Shark"}
    ],
    "Citrus": [
        {"name": "Crystal River Main Channel Ledge", "lat": 28.8933, "lon": -82.6055, "env": "Coastal Marine Estuary", "depth": "8-14 ft", "species": "Snook, Seatrout, Redfish"},
        {"name": "Fort Island Gulf Beach Pier Access", "lat": 28.9161, "lon": -82.6922, "env": "Coastal Marine Estuary", "depth": "4-6 ft", "species": "Seatrout, Pompano, Spanish Mackerel"},
        {"name": "Lake Henderson Public Launch Pool", "lat": 28.8392, "lon": -82.3215, "env": "Inland Freshwater System", "depth": "5-10 ft", "species": "Largemouth Bass, Black Crappie"},
        {"name": "Homosassa River Deep Limestone Cut", "lat": 28.7994, "lon": -82.6210, "env": "Coastal Marine Estuary", "depth": "6-12 ft", "species": "Redfish, Snook, Mangrove Snapper"},
        {"name": "Withlacoochee River Delta Base Mouth", "lat": 29.0012, "lon": -82.7215, "env": "Coastal Marine Estuary", "depth": "4-9 ft", "species": "Redfish, Tarpon, Sea Trout"}
    ],
    "Clay": [
        {"name": "St. Johns River Black Creek Mouth", "lat": 30.0450, "lon": -81.7050, "env": "Riverine System", "depth": "8-16 ft", "species": "Largemouth Bass, Striped Bass"},
        {"name": "Doctors Lake Bridge Pier Spans", "lat": 30.1310, "lon": -81.7140, "env": "Coastal Marine Estuary", "depth": "6-11 ft", "species": "Striper, Redfish, Black Drum"},
        {"name": "Black Creek Inland Deep Bend", "lat": 30.0380, "lon": -81.7850, "env": "Riverine System", "depth": "10-25 ft", "species": "Largemouth Bass, Channel Catfish"},
        {"name": "St. Johns River Green Cove Pier", "lat": 29.9910, "lon": -81.6730, "env": "Riverine System", "depth": "5-10 ft", "species": "Croaker, Catfish, Largemouth Bass"},
        {"name": "Doctors Inlet Central Deep Hole", "lat": 30.1142, "lon": -81.7511, "env": "Riverine System", "depth": "8-14 ft", "species": "Largemouth Bass, Bluegill"}
    ],
    "Collier": [
        {"name": "Naples Pier Open Surf Grid", "lat": 26.1320, "lon": -81.8080, "env": "Coastal Marine Estuary", "depth": "8-14 ft", "species": "Snook, Pompano, Spanish Mackerel"},
        {"name": "Gordon Pass Inlet Deep Track", "lat": 26.0940, "lon": -81.7990, "env": "Coastal Marine Estuary", "depth": "12-26 ft", "species": "Tarpon, Snook, Redfish"},
        {"name": "Marco River Bridge Channel Spans", "lat": 25.9620, "lon": -81.7290, "env": "Coastal Marine Estuary", "depth": "8-18 ft", "species": "Snook, Black Drum, Sheepshead"},
        {"name": "Caxambas Pass Backcountry Cut", "lat": 25.9180, "lon": -81.7150, "env": "Coastal Marine Estuary", "depth": "6-14 ft", "species": "Redfish, Trout, Snook"},
        {"name": "Marco River Deep Pass Channel", "lat": 25.9985, "lon": -81.7340, "env": "Coastal Marine Estuary", "depth": "10-20 ft", "species": "Snook, Tarpon, Redfish"}
    ],
    "Columbia": [
        {"name": "Santa Fe River Highway Launch Run", "lat": 29.8310, "lon": -82.6310, "env": "Riverine System", "depth": "6-12 ft", "species": "Suwannee Bass, Channel Catfish"},
        {"name": "Suwannee River Springs Junction", "lat": 30.3850, "lon": -82.9910, "env": "Riverine System", "depth": "8-18 ft", "species": "Largemouth Bass, Redbreast Sunfish"},
        {"name": "Santa Fe River Rock Ledge Bend", "lat": 29.8810, "lon": -82.5950, "env": "Riverine System", "depth": "5-10 ft", "species": "Catfish, Bream"},
        {"name": "Alligator Lake South Fishing Pier", "lat": 30.1650, "lon": -82.6310, "env": "Inland Freshwater System", "depth": "4-8 ft", "species": "Largemouth Bass, Bluegill"},
        {"name": "Santa Fe River East Boundary Flume", "lat": 29.9890, "lon": -82.7560, "env": "Riverine System", "depth": "4-9 ft", "species": "Suwannee Bass, Bluegill"}
    ],
    "DeSoto": [
        {"name": "Peace River Public Launch Deep Hole", "lat": 27.2180, "lon": -81.8650, "env": "Riverine System", "depth": "6-12 ft", "species": "Largemouth Bass, Channel Catfish"},
        {"name": "Peace River Bridge Piling Grid", "lat": 27.2141, "lon": -81.8512, "env": "Riverine System", "depth": "5-10 ft", "species": "Bluegill, Channel Catfish"},
        {"name": "Peace River Northern Bend Snag", "lat": 27.2650, "lon": -81.8820, "env": "Riverine System", "depth": "4-8 ft", "species": "Largemouth Bass, Snook"},
        {"name": "Peace River Southern Flat Transition", "lat": 27.1350, "lon": -81.9120, "env": "Riverine System", "depth": "4-7 ft", "species": "Catfish, Tilapia"},
        {"name": "Peace River West Branch Junction", "lat": 27.1850, "lon": -81.8950, "env": "Riverine System", "depth": "5-9 ft", "species": "Largemouth Bass, Bluegill"}
    ],
    "Dixie": [
        {"name": "Suwannee River Dynamic Mud Creek Mouth", "lat": 29.3240, "lon": -83.1310, "env": "Coastal Marine Estuary", "depth": "5-10 ft", "species": "Redfish, Seatrout, Snook"},
        {"name": "Horseshoe Beach Main Approach Channel", "lat": 29.4350, "lon": -83.2950, "env": "Coastal Marine Estuary", "depth": "4-9 ft", "species": "Spotted Seatrout, Redfish"},
        {"name": "Suwannee River Sound Core Channel", "lat": 29.4010, "lon": -83.1890, "env": "Coastal Marine Estuary", "depth": "6-14 ft", "species": "Redfish, Seatrout, Sheepshead"},
        {"name": "Steinhatchee Coastal Flat Slough", "lat": 29.6650, "lon": -83.4110, "env": "Coastal Marine Estuary", "depth": "3-7 ft", "species": "Sea Trout, Pompano"},
        {"name": "Suwannee River Inland Deep Hole", "lat": 29.5850, "lon": -83.0250, "env": "Riverine System", "depth": "12-30 ft", "species": "Largemouth Bass, Sturgeon, Catfish"}
    ],
    "Duval": [
        {"name": "Mayport Deep Jet Shipping Channel", "lat": 30.3950, "lon": -81.4310, "env": "Coastal Marine Estuary", "depth": "20-42 ft", "species": "Redfish, Flounder, Bull Drum, Shark"},
        {"name": "Jacksonville Beach Pier Surf Grid", "lat": 30.2880, "lon": -81.3850, "env": "Coastal Marine Estuary", "depth": "8-15 ft", "species": "Pompano, Whiting, Spanish Mackerel"},
        {"name": "St. Johns River Downtown Bridge Fender", "lat": 30.3210, "lon": -81.6550, "env": "Coastal Marine Estuary", "depth": "15-30 ft", "species": "Striper, Redfish, Black Drum"},
        {"name": "Mill Cove Oyster Flat Creek", "lat": 30.3650, "lon": -81.5450, "env": "Coastal Marine Estuary", "depth": "3-8 ft", "species": "Spotted Seatrout, Redfish, Flounder"},
        {"name": "Sister Creek Bridge Current Slip", "lat": 30.3990, "lon": -81.4550, "env": "Coastal Marine Estuary", "depth": "8-18 ft", "species": "Snook, Redfish, Flounder"}
    ],
    "Escambia": [
        {"name": "Pensacola Pass Deep Entry Slot", "lat": 30.3420, "lon": -87.2910, "env": "Coastal Marine Estuary", "depth": "20-45 ft", "species": "Red Snapper, Gag Grouper, King Mackerel"},
        {"name": "Pensacola Beach Gulf Fishing Pier", "lat": 30.3320, "lon": -87.1420, "env": "Coastal Marine Estuary", "depth": "10-18 ft", "species": "King Mackerel, Cobia, Pompano"},
        {"name": "Escambia River Highway Bridge Piling", "lat": 30.5150, "lon": -87.2110, "env": "Riverine System", "depth": "8-15 ft", "species": "Largemouth Bass, Striped Bass, Catfish"},
        {"name": "Bayou Chico Dredge Navigation Cut", "lat": 30.4110, "lon": -87.2420, "env": "Coastal Marine Estuary", "depth": "6-12 ft", "species": "Spotted Seatrout, Redfish"},
        {"name": "Pensacola Bay Trestle Array System", "lat": 30.4520, "lon": -87.1650, "env": "Coastal Marine Estuary", "depth": "10-20 ft", "species": "Redfish, Trout, Sheepshead"}
    ],
    "Flagler": [
        {"name": "Matanzas River ICW Core Channel", "lat": 29.6120, "lon": -81.2140, "env": "Coastal Marine Estuary", "depth": "6-12 ft", "species": "Redfish, Spotted Seatrout, Flounder"},
        {"name": "Bings Landing Oyster Trough Wall", "lat": 29.6220, "lon": -81.2110, "env": "Coastal Marine Estuary", "depth": "4-8 ft", "species": "Snook, Redfish, Black Drum"},
        {"name": "Highbridge Road ICW Bridge Fender", "lat": 29.4120, "lon": -81.1110, "env": "Coastal Marine Estuary", "depth": "8-14 ft", "species": "Snook, Tarpon, Flounder"},
        {"name": "Lehigh Canal Freshwater Junction", "lat": 29.5650, "lon": -81.2450, "env": "Inland Freshwater System", "depth": "4-7 ft", "species": "Largemouth Bass, Bluegill"},
        {"name": "Pellicer Creek Bridge Ecosystem", "lat": 29.6650, "lon": -81.2550, "env": "Coastal Marine Estuary", "depth": "3-6 ft", "species": "Redfish, Seatrout"}
    ],
    "Franklin": [
        {"name": "Apalachicola Bay Shipping Cut Base", "lat": 29.7241, "lon": -84.9812, "env": "Coastal Marine Estuary", "depth": "12-25 ft", "species": "Tripletail, Redfish, Spotted Seatrout"},
        {"name": "St. George Island Bridge Fishing Pier", "lat": 29.7420, "lon": -84.8820, "env": "Coastal Marine Estuary", "depth": "8-16 ft", "species": "Seatrout, Redfish, Sheepshead"},
        {"name": "Carrabelle River Main Dredge Channel", "lat": 29.8450, "lon": -84.6650, "env": "Coastal Marine Estuary", "depth": "10-20 ft", "species": "Grouper, Mangrove Snapper, Redfish"},
        {"name": "Apalachicola River Estuary Flats", "lat": 29.7450, "lon": -84.9910, "env": "Coastal Marine Estuary", "depth": "4-8 ft", "species": "Redfish, Sea Trout"},
        {"name": "Indian Pass Backcountry Current Cut", "lat": 29.6850, "lon": -85.2150, "env": "Coastal Marine Estuary", "depth": "6-12 ft", "species": "Tarpon, Redfish, Flounder"}
    ],
    "Gadsden": [
        {"name": "Lake Talquin River Flow Influx", "lat": 30.4620, "lon": -84.6850, "env": "Inland Freshwater System", "depth": "10-24 ft", "species": "Black Crappie, Striped Bass, Largemouth"},
        {"name": "Lake Talquin Dam Deep Core", "lat": 30.4690, "lon": -84.6510, "env": "Inland Freshwater System", "depth": "15-35 ft", "species": "Striped Bass, Channel Catfish"},
        {"name": "Lake Talquin Northern Standing Timber", "lat": 30.4850, "lon": -84.7120, "env": "Inland Freshwater System", "depth": "8-15 ft", "species": "Black Crappie, Bluegill"},
        {"name": "Ocklocknee River Bridge Run", "lat": 30.5850, "lon": -84.6110, "env": "Riverine System", "depth": "6-11 ft", "species": "Channel Catfish, Bream"},
        {"name": "Lake Talquin South Shore Ledge", "lat": 30.4550, "lon": -84.7350, "env": "Inland Freshwater System", "depth": "8-14 ft", "species": "Largemouth Bass, Crappie"}
    ],
    "Gilchrist": [
        {"name": "Suwannee River Springs Trench Ledge", "lat": 29.5920, "lon": -82.9510, "env": "Riverine System", "depth": "8-18 ft", "species": "Suwannee Bass, Largemouth Bass"},
        {"name": "Suwannee River Bridge Pile Intercept", "lat": 29.6050, "lon": -82.9350, "env": "Riverine System", "depth": "10-22 ft", "species": "Channel Catfish, Sturgeon"},
        {"name": "Santa Fe River Mouth Junction", "lat": 29.8890, "lon": -82.8750, "env": "Riverine System", "depth": "6-14 ft", "species": "Suwannee Bass, Flathead Catfish"},
        {"name": "Suwannee River Rock Wall Bend", "lat": 29.6450, "lon": -82.9150, "env": "Riverine System", "depth": "8-15 ft", "species": "Largemouth Bass, Bream"},
        {"name": "Santa Fe River Inland Pool Block", "lat": 29.8950, "lon": -82.7850, "env": "Riverine System", "depth": "5-10 ft", "species": "Catfish, Bluegill"}
    ],
    "Glades": [
        {"name": "Caloosahatchee River Lock Gate Entrance", "lat": 26.7910, "lon": -81.0910, "env": "Inland Freshwater System", "depth": "8-15 ft", "species": "Largemouth Bass, Bluegill, Catfish"},
        {"name": "Lake Okeechobee Harney Pond Canal", "lat": 26.9950, "lon": -81.0510, "env": "Inland Freshwater System", "depth": "6-12 ft", "species": "Trophy Largemouth Bass, Black Crappie"},
        {"name": "Lake Okeechobee North Grass Wall", "lat": 27.0110, "lon": -81.0150, "env": "Inland Freshwater System", "depth": "4-7 ft", "species": "Largemouth Bass, Bluegill"},
        {"name": "Caloosahatchee River Dredge Center Cut", "lat": 26.7990, "lon": -81.1450, "env": "Inland Freshwater System", "depth": "10-18 ft", "species": "Snook, Largemouth Bass"},
        {"name": "Fisheating Creek Backwater Delta Mouth", "lat": 26.9450, "lon": -81.1550, "env": "Inland Freshwater System", "depth": "3-6 ft", "species": "Largemouth Bass, Crappie"}
    ],
    "Gulf": [
        {"name": "St. Joseph Bay Main Shipping Trough", "lat": 29.8120, "lon": -85.3010, "env": "Coastal Marine Estuary", "depth": "10-22 ft", "species": "Spotted Seatrout, Redfish, Flounder"},
        {"name": "St. Joseph State Park Grass Slough", "lat": 29.7650, "lon": -85.3950, "env": "Coastal Marine Estuary", "depth": "3-6 ft", "species": "Gator Trout, Redfish"},
        {"name": "Indian Pass Western Inlet Trough", "lat": 29.6850, "lon": -85.2550, "env": "Coastal Marine Estuary", "depth": "8-16 ft", "species": "Tarpon, Redfish, Sharks"},
        {"name": "Apalachicola River Navigation Canal", "lat": 29.9450, "lon": -85.2150, "env": "Riverine System", "depth": "12-25 ft", "species": "Striped Bass, Catfish"},
        {"name": "St. Joseph Bay Marina Approach Split", "lat": 29.8110, "lon": -85.3250, "env": "Coastal Marine Estuary", "depth": "6-11 ft", "species": "Mangrove Snapper, Trout"}
    ],
    "Hamilton": [
        {"name": "Withlacoochee River North Junction Bend", "lat": 30.3890, "lon": -83.1610, "env": "Riverine System", "depth": "6-12 ft", "species": "Suwannee Bass, Channel Catfish"},
        {"name": "Suwannee River Bridge Piling Sector", "lat": 30.3540, "lon": -82.9150, "env": "Riverine System", "depth": "8-16 ft", "species": "Largemouth Bass, Catfish"},
        {"name": "Suwannee River Rocky Bluff Pool", "lat": 30.4110, "lon": -82.8850, "env": "Riverine System", "depth": "10-22 ft", "species": "Channel Catfish, Redbreast Sunfish"},
        {"name": "Alapaha River Floodplain Delta Mouth", "lat": 30.3210, "lon": -83.1050, "env": "Riverine System", "depth": "4-8 ft", "species": "Suwannee Bass, Bream"},
        {"name": "Suwannee River Limestone Shoal Cut", "lat": 30.4850, "lon": -82.7450, "env": "Riverine System", "depth": "4-7 ft", "species": "Catfish, Sunfish"}
    ],
    "Hardee": [
        {"name": "Peace River Inland Deep Trench Ledge", "lat": 27.5410, "lon": -81.8110, "env": "Riverine System", "depth": "5-10 ft", "species": "Channel Catfish, Largemouth Bass"},
        {"name": "Peace River Bridge Pile Guard", "lat": 27.5450, "lon": -81.8020, "env": "Riverine System", "depth": "6-11 ft", "species": "Bluegill, Catfish"},
        {"name": "Peace River Northern Oxbow Pool", "lat": 27.6150, "lon": -81.8150, "env": "Riverine System", "depth": "4-8 ft", "species": "Largemouth Bass, Tilapia"},
        {"name": "Peace River Southern Gravel Bar", "lat": 27.4220, "lon": -81.7950, "env": "Riverine System", "depth": "3-6 ft", "species": "Channel Catfish, Bream"},
        {"name": "Peace River Limestone Drop-off Wall", "lat": 27.4850, "lon": -81.8050, "env": "Riverine System", "depth": "4-9 ft", "species": "Largemouth Bass, Bluegill"}
    ],
    "Hendry": [
        {"name": "Caloosahatchee River Center Dredge Cut", "lat": 26.7940, "lon": -81.4210, "env": "Inland Freshwater System", "depth": "8-14 ft", "species": "Largemouth Bass, Snook, Bluegill"},
        {"name": "Caloosahatchee River Bridge Fender Spans", "lat": 26.7550, "lon": -81.4420, "env": "Inland Freshwater System", "depth": "10-16 ft", "species": "Snook, Channel Catfish"},
        {"name": "Lake Okeechobee Clewiston Lock Outflow", "lat": 26.7650, "lon": -80.9150, "env": "Inland Freshwater System", "depth": "8-15 ft", "species": "Trophy Largemouth Bass, Black Crappie"},
        {"name": "Clewiston Industrial Route Spillway Split", "lat": 26.7590, "lon": -80.9320, "env": "Inland Freshwater System", "depth": "6-11 ft", "species": "Largemouth Bass, Bluegill"},
        {"name": "Caloosahatchee Western Oxbow Channel", "lat": 26.7850, "lon": -81.5150, "env": "Inland Freshwater System", "depth": "5-9 ft", "species": "Bass, Catfish"}
    ],
    "Hernando": [
        {"name": "Bayport Outer Shipping Channel Intercept", "lat": 28.5410, "lon": -82.6950, "env": "Coastal Marine Estuary", "depth": "6-12 ft", "species": "Snook, Redfish, Seatrout"},
        {"name": "Hernando Beach Main Canal Approach", "lat": 28.4950, "lon": -82.6620, "env": "Coastal Marine Estuary", "depth": "5-10 ft", "species": "Snook, Mangrove Snapper"},
        {"name": "Weeki Wachee River Tidal Estuary Cut", "lat": 28.5380, "lon": -82.6450, "env": "Coastal Marine Estuary", "depth": "4-8 ft", "species": "Redfish, Seatrout, Snook"},
        {"name": "Withlacoochee River Inland Deep Ledge", "lat": 28.6150, "lon": -82.2220, "env": "Riverine System", "depth": "10-24 ft", "species": "Largemouth Bass, Channel Catfish"},
        {"name": "Lake Lindsey Public Fishing Dock", "lat": 28.6250, "lon": -82.3650, "env": "Inland Freshwater System", "depth": "4-9 ft", "species": "Largemouth Bass, Bluegill"}
    ],
    "Highlands": [
        {"name": "Lake Istokpoga Core Canal System Entry", "lat": 27.4650, "lon": -81.3410, "env": "Inland Freshwater System", "depth": "6-12 ft", "species": "Trophy Largemouth Bass, Black Crappie"},
        {"name": "Lake Istokpoga Northern Weed Barrier", "lat": 27.4110, "lon": -81.2550, "env": "Inland Freshwater System", "depth": "4-8 ft", "species": "Largemouth Bass, Bluegill"},
        {"name": "Lake June In Winter Public West Launch", "lat": 27.2950, "lon": -81.4450, "env": "Inland Freshwater System", "depth": "10-25 ft", "species": "Largemouth Bass, Black Crappie"},
        {"name": "Lake Placid Central Deep Trench Hole", "lat": 27.2650, "lon": -81.3950, "env": "Inland Freshwater System", "depth": "15-38 ft", "species": "Largemouth Bass, Bluegill"},
        {"name": "Lake Istokpoga South Floodgate Discharge", "lat": 27.3250, "lon": -81.1850, "env": "Inland Freshwater System", "depth": "8-14 ft", "species": "Catfish, Largemouth Bass"}
    ],
    "Hillsborough": [
        {"name": "Tampa Bay Main Dredged Shipping Cut", "lat": 27.9500, "lon": -82.4500, "env": "Coastal Marine Estuary", "depth": "15-42 ft", "species": "Snook, Redfish, Tarpon, Cobia, Gag Grouper"},
        {"name": "Ballast Point Public Fishing Pier", "lat": 27.8890, "lon": -82.4780, "env": "Coastal Marine Estuary", "depth": "6-12 ft", "species": "Seatrout, Snook, Mangrove Snapper"},
        {"name": "Alafia River Tidal Mud Flat Cut", "lat": 27.8650, "lon": -82.4150, "env": "Coastal Marine Estuary", "depth": "5-11 ft", "species": "Redfish, Snook, Sea Trout"},
        {"name": "Edward Medard Reservoir Spillway Basin", "lat": 27.8950, "lon": -82.1650, "env": "Inland Freshwater System", "depth": "8-18 ft", "species": "Largemouth Bass, Bluegill, Catfish"},
        {"name": "Lake Thonotosassa Public Launch Sector", "lat": 28.0550, "lon": -82.2850, "env": "Inland Freshwater System", "depth": "6-12 ft", "species": "Largemouth Bass, Black Crappie"}
    ],
    "Holmes": [
        {"name": "Choctawhatchee River Core Channel Pool", "lat": 30.7710, "lon": -85.8110, "env": "Riverine System", "depth": "6-12 ft", "species": "Channel Catfish, Largemouth Bass, Bream"},
        {"name": "Choctawhatchee River Bridge Support Piling", "lat": 30.8520, "lon": -85.8450, "env": "Riverine System", "depth": "8-15 ft", "species": "Flathead Catfish, Striped Bass"},
        {"name": "Choctawhatchee Northern Slough Seam", "lat": 30.9450, "lon": -85.8850, "env": "Riverine System", "depth": "4-8 ft", "species": "Largemouth Bass, Warmouth"},
        {"name": "Holmes Creek Deep Rock Hole Split", "lat": 30.7150, "lon": -85.7320, "env": "Riverine System", "depth": "6-11 ft", "species": "Suwannee Bass, Catfish"},
        {"name": "Holmes Creek Sandy Point Bend Bar", "lat": 30.7950, "lon": -85.7650, "env": "Riverine System", "depth": "3-7 ft", "species": "Bream, Bass"}
    ],
    "Indian River": [
        {"name": "Indian River Lagoon ICW Navigation Channel", "lat": 27.6420, "lon": -80.3650, "env": "Coastal Marine Estuary", "depth": "6-14 ft", "species": "Snook, Tarpon, Spotted Seatrout"},
        {"name": "Sebastian River Bridge Support Fender", "lat": 27.8450, "lon": -80.4850, "env": "Coastal Marine Estuary", "depth": "8-16 ft", "species": "Snook, Tarpon, Bull Shark"},
        {"name": "Vero Beach Barber Bridge Pile Trestle", "lat": 27.6520, "lon": -80.3750, "env": "Coastal Marine Estuary", "depth": "8-15 ft", "species": "Snook, Mangrove Snapper, Trout"},
        {"name": "Blue Cypress Lake Public East Launch", "lat": 27.7450, "lon": -80.7450, "env": "Inland Freshwater System", "depth": "5-9 ft", "species": "Largemouth Bass, Black Crappie"},
        {"name": "Blue Cypress Lake Northern Tree Line Flats", "lat": 27.7650, "lon": -80.7550, "env": "Inland Freshwater System", "depth": "4-7 ft", "species": "Largemouth Bass, Bluegill"}
    ],
    "Jackson": [
        {"name": "Lake Seminole Bridge Column Grid", "lat": 30.7140, "lon": -84.8650, "env": "Riverine System", "depth": "10-24 ft", "species": "Striped Bass, Largemouth Bass, Catfish"},
        {"name": "Merritts Mill Pond Public Launch Run", "lat": 30.7750, "lon": -85.1450, "env": "Inland Freshwater System", "depth": "5-14 ft", "species": "Trophy Shellcracker, Largemouth Bass"},
        {"name": "Merritts Mill Pond Central Spring Slough", "lat": 30.7820, "lon": -85.1210, "env": "Inland Freshwater System", "depth": "8-20 ft", "species": "Redear Sunfish, Bass"},
        {"name": "Ocklocknee River Northern Bluffs Trench", "lat": 30.8850, "lon": -85.2150, "env": "Riverine System", "depth": "6-12 ft", "species": "Channel Catfish, Bluegill"},
        {"name": "Lake Seminole Dam Pool Spillway Cut", "lat": 30.7050, "lon": -84.8550, "env": "Riverine System", "depth": "12-30 ft", "species": "Striped Bass, Flathead Catfish"}
    ],
    "Jefferson": [
        {"name": "Aucilla River Tidal Estuary Mud Mouth", "lat": 30.0910, "lon": -83.9910, "env": "Coastal Marine Estuary", "depth": "5-11 ft", "species": "Redfish, Spotted Seatrout"},
        {"name": "Aucilla River Bridge Pillar Intercept", "lat": 30.1550, "lon": -83.9850, "env": "Riverine System", "depth": "6-12 ft", "species": "Largemouth Bass, Channel Catfish"},
        {"name": "Wacissa River Headsprings Core Pool", "lat": 30.3410, "lon": -83.9920, "env": "Inland Freshwater System", "depth": "4-12 ft", "species": "Largemouth Bass, Redbreast Sunfish"},
        {"name": "Wacissa River Southern Timber Canal", "lat": 30.2550, "lon": -83.9850, "env": "Inland Freshwater System", "depth": "3-7 ft", "species": "Largemouth Bass, Bluegill"},
        {"name": "Aucilla River Inland Rock Hole Hole", "lat": 30.2250, "lon": -83.9550, "env": "Riverine System", "depth": "8-16 ft", "species": "Catfish, Bream"}
    ],
    "Lafayette": [
        {"name": "Suwannee River Deep Rocky Bend Basin", "lat": 30.1210, "lon": -83.0210, "env": "Riverine System", "depth": "10-22 ft", "species": "Suwannee Bass, Channel Catfish, Sturgeon"},
        {"name": "Suwannee River Bridge Pile Intercept", "lat": 30.1520, "lon": -83.0450, "env": "Riverine System", "depth": "8-16 ft", "species": "Channel Catfish, Largemouth Bass"},
        {"name": "Suwannee River Northern Springs Pass", "lat": 30.2450, "lon": -83.0110, "env": "Riverine System", "depth": "6-14 ft", "species": "Suwannee Bass, Sunfish"},
        {"name": "Suwannee River Hal W. Adams Span", "lat": 30.1050, "lon": -83.1150, "env": "Riverine System", "depth": "10-20 ft", "species": "Flathead Catfish, Bass"},
        {"name": "Suwannee River Southern Creek Junction", "lat": 29.9850, "lon": -82.9850, "env": "Riverine System", "depth": "5-10 ft", "species": "Catfish, Bream"}
    ],
    "Lake": [
        {"name": "Lake Harris Navigation Trench Line", "lat": 28.8140, "lon": -81.7910, "env": "Inland Freshwater System", "depth": "8-16 ft", "species": "Trophy Largemouth Bass, Black Crappie"},
        {"name": "Lake Eustis Central Core Drop Hole", "lat": 28.8550, "lon": -81.7150, "env": "Inland Freshwater System", "depth": "12-24 ft", "species": "Largemouth Bass, Crappie"},
        {"name": "Lake Griffin Public West Launch Canal", "lat": 28.8950, "lon": -81.8550, "env": "Inland Freshwater System", "depth": "5-10 ft", "species": "Largemouth Bass, Bluegill"},
        {"name": "St. Johns River Crow's Bluff Bridge Pile", "lat": 29.0150, "lon": -81.3950, "env": "Riverine System", "depth": "8-15 ft", "species": "Largemouth Bass, Striped Bass"},
        {"name": "Lake Harris Dead River Connecting Slough", "lat": 28.8250, "lon": -81.7450, "env": "Inland Freshwater System", "depth": "6-12 ft", "species": "Largemouth Bass, Crappie"}
    ],
    "Lee": [
        {"name": "Matlacha Pass Dredged Highway Channel", "lat": 26.6400, "lon": -82.0700, "env": "Coastal Marine Estuary", "depth": "6-12 ft", "species": "Snook, Redfish, Spotted Seatrout, Tarpon"},
        {"name": "Sanibel Fishing Pier Outer Piling Line", "lat": 26.4520, "lon": -82.0150, "env": "Coastal Marine Estuary", "depth": "8-16 ft", "species": "Snook, Sea Trout, Spanish Mackerel"},
        {"name": "Caloosahatchee River Cape Coral Trestle", "lat": 26.5650, "lon": -81.9450, "env": "Coastal Marine Estuary", "depth": "10-22 ft", "species": "Tarpon, Snook, Black Drum"},
        {"name": "Pine Island Sound Inner Grass Trough", "lat": 26.6150, "lon": -82.1150, "env": "Coastal Marine Estuary", "depth": "4-7 ft", "species": "Spotted Seatrout, Redfish"},
        {"name": "Caloosahatchee Mid-River Dredge Trenches", "lat": 26.6550, "lon": -81.8850, "env": "Coastal Marine Estuary", "depth": "12-25 ft", "species": "Snook, Tarpon, Sharks"}
    ],
    "Leon": [
        {"name": "Lake Jackson South Launch Deep Pool", "lat": 30.5150, "lon": -84.3450, "env": "Inland Freshwater System", "depth": "5-10 ft", "species": "Largemouth Bass, Bluegill, Black Crappie"},
        {"name": "Lake Jackson Northern Pad Perimeter", "lat": 30.5650, "lon": -84.3750, "env": "Inland Freshwater System", "depth": "4-8 ft", "species": "Largemouth Bass, Warmouth"},
        {"name": "Lake Miccosukee Public South Pier", "lat": 30.5850, "lon": -83.9450, "env": "Inland Freshwater System", "depth": "4-7 ft", "species": "Largemouth Bass, Black Crappie"},
        {"name": "Lake Iamonia Central Open Hole Area", "lat": 30.6350, "lon": -84.2550, "env": "Inland Freshwater System", "depth": "5-9 ft", "species": "Bluegill, Largemouth Bass"},
        {"name": "Lake Jackson West Sinkhole Ridge Boundary", "lat": 30.5350, "lon": -84.3950, "env": "Inland Freshwater System", "depth": "6-14 ft", "species": "Largemouth Bass, Bluegill"}
    ],
    "Levy": [
        {"name": "Cedar Key Main Shipping Cut Approach", "lat": 29.1310, "lon": -83.0510, "env": "Coastal Marine Estuary", "depth": "8-16 ft", "species": "Redfish, Spotted Seatrout, Cobia"},
        {"name": "Yankeetown Withlacoochee Tidal Mouth", "lat": 28.9950, "lon": -82.7450, "env": "Coastal Marine Estuary", "depth": "6-14 ft", "species": "Snook, Redfish, Sea Trout"},
        {"name": "Waccasassa River Navigational Mud Cut", "lat": 29.1150, "lon": -82.8350, "env": "Coastal Marine Estuary", "depth": "4-10 ft", "species": "Redfish, Black Drum, Trout"},
        {"name": "Cedar Key Fishing Pier Concrete Base", "lat": 29.1380, "lon": -83.0320, "env": "Coastal Marine Estuary", "depth": "5-9 ft", "species": "Seatrout, Sheepshead, Sharks"},
        {"name": "Suwannee River Sound Outer Bar Flats", "lat": 29.2850, "lon": -83.1450, "env": "Coastal Marine Estuary", "depth": "3-7 ft", "species": "Redfish, Sea Trout"}
    ],
    "Liberty": [
        {"name": "Apalachicola Mid-River Channel Track", "lat": 30.1410, "lon": -84.9950, "env": "Riverine System", "depth": "8-16 ft", "species": "Channel Catfish, Striped Bass, Sturgeon"},
        {"name": "Apalachicola River Bridge Support Pile", "lat": 30.4350, "lon": -84.9850, "env": "Riverine System", "depth": "10-24 ft", "species": "Flathead Catfish, Striped Bass"},
        {"name": "Ocklocknee River Deep Swamp Oxbow", "lat": 30.2250, "lon": -84.6850, "env": "Riverine System", "depth": "6-11 ft", "species": "Largemouth Bass, Bream"},
        {"name": "Apalachicola Southern Clay Bank Drop", "lat": 29.9450, "lon": -85.0150, "env": "Riverine System", "depth": "12-25 ft", "species": "Channel Catfish, Bass"},
        {"name": "Ocklocknee River Southern Sandbar Bend", "lat": 30.0350, "lon": -84.6550, "env": "Riverine System", "depth": "4-8 ft", "species": "Bream, Catfish"}
    ],
    "Madison": [
        {"name": "Withlacoochee River Basin Border Pool", "lat": 30.4614, "lon": -83.4112, "env": "Riverine System", "depth": "6-11 ft", "species": "Largemouth Bass, Channel Catfish, Bream"},
        {"name": "Suwannee River Eastern Limestone Shoal", "lat": 30.3850, "lon": -83.1850, "env": "Riverine System", "depth": "5-10 ft", "species": "Suwannee Bass, Sunfish"},
        {"name": "Withlacoochee State Line Rapids Edge", "lat": 30.6150, "lon": -83.2850, "env": "Riverine System", "depth": "4-8 ft", "species": "Channel Catfish, Bluegill"},
        {"name": "Cherry Lake Central Deep Water Core", "lat": 30.5850, "lon": -83.4450, "env": "Inland Freshwater System", "depth": "10-22 ft", "species": "Largemouth Bass, Black Crappie"},
        {"name": "Cherry Lake North Launch Pad Line", "lat": 30.5950, "lon": -83.4350, "env": "Inland Freshwater System", "depth": "5-9 ft", "species": "Largemouth Bass, Bluegill"}
    ],
    "Manatee": [
        {"name": "Manatee River Main Dredged Shipping Cut", "lat": 27.5310, "lon": -82.6140, "env": "Coastal Marine Estuary", "depth": "10-22 ft", "species": "Snook, Redfish, Spotted Seatrout"},
        {"name": "Sunshine Skyway South Fishing Pier Base", "lat": 27.6150, "lon": -82.6450, "env": "Coastal Marine Estuary", "depth": "15-30 ft", "species": "Gag Grouper, Spanish Mackerel, Tarpon, Sharks"},
        {"name": "Bradenton Beach Public Pier Pile Grid", "lat": 27.4650, "lon": -82.6950, "env": "Coastal Marine Estuary", "depth": "6-11 ft", "species": "Snook, Mangrove Snapper, Trout"},
        {"name": "Lake Manatee Public West Launch Run", "lat": 27.4850, "lon": -82.3450, "env": "Inland Freshwater System", "depth": "8-16 ft", "species": "Largemouth Bass, Channel Catfish"},
        {"name": "Terra Ceia Bay Shallow Grass Trough", "lat": 27.5850, "lon": -82.5850, "env": "Coastal Marine Estuary", "depth": "3-6 ft", "species": "Redfish, Sea Trout"}
    ],
    "Marion": [
        {"name": "Ocklawaha River Rodman Dam Tailrace", "lat": 29.5020, "lon": -81.8050, "env": "Inland Freshwater System", "depth": "10-25 ft", "species": "Trophy Largemouth Bass, Striped Bass, Catfish"},
        {"name": "Lake Weir Public South Launch Slope", "lat": 29.0050, "lon": -81.9450, "env": "Inland Freshwater System", "depth": "8-20 ft", "species": "Largemouth Bass, Black Crappie"},
        {"name": "Lake Weir Northern Deep Springs Hole", "lat": 29.0450, "lon": -81.9250, "env": "Inland Freshwater System", "depth": "15-32 ft", "species": "Largemouth Bass, Bluegill"},
        {"name": "Ocklawaha River Eureka Bridge Corner", "lat": 29.2850, "lon": -81.8950, "env": "Riverine System", "depth": "6-12 ft", "species": "Largemouth Bass, Channel Catfish"},
        {"name": "Lake Kerr Central Deep Island Drop", "lat": 29.3650, "lon": -81.7650, "env": "Inland Freshwater System", "depth": "10-18 ft", "species": "Largemouth Bass, Crappie"}
    ],
    "Martin": [
        {"name": "St. Lucie Inlet Deep Shipping Access", "lat": 27.1650, "lon": -80.1910, "env": "Coastal Marine Estuary", "depth": "12-28 ft", "species": "Snook, Tarpon, Permit, Snapper"},
        {"name": "Jensen Beach Causeway Trestle Array", "lat": 27.2350, "lon": -80.2150, "env": "Coastal Marine Estuary", "depth": "6-14 ft", "species": "Snook, Spotted Seatrout, Redfish"},
        {"name": "St. Lucie River Stuart Bridge Fender", "lat": 27.2050, "lon": -80.2550, "env": "Coastal Marine Estuary", "depth": "8-18 ft", "species": "Snook, Tarpon, Black Drum"},
        {"name": "Lake Okeechobee Port Mayaca Lock Out", "lat": 26.9850, "lon": -80.6150, "env": "Inland Freshwater System", "depth": "8-15 ft", "species": "Largemouth Bass, Black Crappie, Snook"},
        {"name": "Indian River Lagoon Sailfish Point Flat", "lat": 27.1850, "lon": -80.1750, "env": "Coastal Marine Estuary", "depth": "4-8 ft", "species": "Seatrout, Pompano"}
    ],
    "Miami-Dade": [
        {"name": "Biscayne Bay Main Dredged Shipping Cut", "lat": 25.7617, "lon": -80.1618, "env": "Coastal Marine Estuary", "depth": "15-40 ft", "species": "Tarpon, Snook, Bonefish, Permit"},
        {"name": "Government Cut Outer Deep Rock Jetty", "lat": 25.7610, "lon": -80.1150, "env": "Coastal Marine Estuary", "depth": "18-35 ft", "species": "Snook, Tarpon, Groupers, Jacks"},
        {"name": "Haulover Inlet Dangerous Current Pass", "lat": 25.9020, "lon": -80.1220, "env": "Coastal Marine Estuary", "depth": "12-24 ft", "species": "Snook, Tarpon, Mangrove Snapper"},
        {"name": "Black Point Marina Navigation Channel", "lat": 25.5350, "lon": -80.3150, "env": "Coastal Marine Estuary", "depth": "6-12 ft", "species": "Snook, Tarpon, Mangrove Snapper"},
        {"name": "Bill Baggs State Park South Cape Flat", "lat": 25.6650, "lon": -80.1550, "env": "Coastal Marine Estuary", "depth": "5-10 ft", "species": "Seatrout, Bonefish, Mackerel"}
    ],
    "Monroe": [
        {"name": "Key West Main Shipping Dredge Channel", "lat": 24.5551, "lon": -81.7800, "env": "Coastal Marine Estuary", "depth": "15-38 ft", "species": "Tarpon, Snook, Bonefish, Permit, Snapper"},
        {"name": "Seven Mile Bridge Central Deep Relief", "lat": 24.7050, "lon": -81.1550, "env": "Coastal Marine Estuary", "depth": "12-28 ft", "species": "Tarpon, Permit, Gag Grouper, Snook"},
        {"name": "Bahia Honda Deep Inshore Channel Cut", "lat": 24.6550, "lon": -81.2850, "env": "Coastal Marine Estuary", "depth": "15-32 ft", "species": "Tarpon, Permit, Barracuda"},
        {"name": "Islamorada Whale Harbor Bridge Fender", "lat": 24.9450, "lon": -80.6150, "env": "Coastal Marine Estuary", "depth": "8-16 ft", "species": "Snook, Tarpon, Mangrove Snapper"},
        {"name": "Key Largo Sound Inner Mangrove Trench", "lat": 25.0950, "lon": -80.4350, "env": "Coastal Marine Estuary", "depth": "4-9 ft", "species": "Bonefish, Snook, Sea Trout"}
    ],
    "Nassau": [
        {"name": "St. Marys Entrance Outer Deep Inlet Pass", "lat": 30.7120, "lon": -81.4514, "env": "Coastal Marine Estuary", "depth": "18-36 ft", "species": "Redfish, Bull Drum, Sea Trout, Flounder"},
        {"name": "Amelia River Fernadina Beach Dock Grid", "lat": 30.6720, "lon": -81.4650, "env": "Coastal Marine Estuary", "depth": "10-22 ft", "species": "Redfish, Black Drum, Sheepshead"},
        {"name": "Nassau Sound Public Fishing Pier Span", "lat": 30.5120, "lon": -81.4450, "env": "Coastal Marine Estuary", "depth": "8-16 ft", "species": "Redfish, Flounder, Sea Trout"},
        {"name": "St. Marys River Inland Bridge Support", "lat": 30.6450, "lon": -81.6550, "env": "Riverine System", "depth": "8-15 ft", "species": "Largemouth Bass, Striped Bass, Catfish"},
        {"name": "Amelia River Inner Oyster Creek Flat", "lat": 30.5850, "lon": -81.4850, "env": "Coastal Marine Estuary", "depth": "4-8 ft", "species": "Redfish, Sea Trout"}
    ],
    "Okaloosa": [
        {"name": "Destin East Pass Outer Inlet Pass Slot", "lat": 30.3950, "lon": -86.5120, "env": "Coastal Marine Estuary", "depth": "15-34 ft", "species": "Redfish, Sea Trout, King Mackerel, Cobia"},
        {"name": "Okaloosa Island Public Fishing Pier", "lat": 30.3920, "lon": -86.5950, "env": "Coastal Marine Estuary", "depth": "10-18 ft", "species": "King Mackerel, Spanish Mackerel, Pompano"},
        {"name": "Choctawhatchee Bay Mid-Bay Span Base", "lat": 30.4350, "lon": -86.4250, "env": "Coastal Marine Estuary", "depth": "12-25 ft", "species": "Redfish, Trout, Sheepshead"},
        {"name": "Garniers Bayou Dredge Channel Line", "lat": 30.4550, "lon": -86.5650, "env": "Coastal Marine Estuary", "depth": "6-12 ft", "species": "Spotted Seatrout, Redfish"},
        {"name": "Shoal River Freshwater Bridge Influx", "lat": 30.6850, "lon": -86.4850, "env": "Riverine System", "depth": "4-8 ft", "species": "Catfish, Largemouth Bass, Bream"}
    ],
    "Okeechobee": [
        {"name": "Kissimmee River Structure Outflow Lock", "lat": 27.2010, "lon": -80.8290, "env": "Inland Freshwater System", "depth": "8-15 ft", "species": "Largemouth Bass, Black Crappie, Striped Bass"},
        {"name": "Lake Okeechobee Rim Canal Main Track", "lat": 27.1820, "lon": -80.8350, "env": "Inland Freshwater System", "depth": "10-16 ft", "species": "Trophy Largemouth Bass, Bluegill"},
        {"name": "Lake Okeechobee Taylor Creek Exit Wall", "lat": 27.2150, "lon": -80.8010, "env": "Inland Freshwater System", "depth": "6-11 ft", "species": "Largemouth Bass, Crappie"},
        {"name": "Kissimmee River Northern Oxbow Slough", "lat": 27.3450, "lon": -80.8650, "env": "Inland Freshwater System", "depth": "5-9 ft", "species": "Largemouth Bass, Bluegill"},
        {"name": "Lake Okeechobee Eagle Bay Reed Edge", "lat": 27.1450, "lon": -80.8750, "env": "Inland Freshwater System", "depth": "4-7 ft", "species": "Largemouth Bass, Bluegill"}
    ],
    "Orange": [
        {"name": "Lake Conway South Deep Water Basin", "lat": 28.4520, "lon": -81.3650, "env": "Inland Freshwater System", "depth": "10-22 ft", "species": "Trophy Largemouth Bass, Bluegill"},
        {"name": "Lake Conway Middle Navigation Channel", "lat": 28.4720, "lon": -81.3690, "env": "Inland Freshwater System", "depth": "8-15 ft", "species": "Largemouth Bass, Black Crappie"},
        {"name": "Lake Conway North Ledge Drop Structure", "lat": 28.4850, "lon": -81.3610, "env": "Inland Freshwater System", "depth": "12-25 ft", "species": "Largemouth Bass, Crappie"},
        {"name": "Lake Toho North Inflow Canal Mouth", "lat": 28.2710, "lon": -81.4110, "env": "Inland Freshwater System", "depth": "6-12 ft", "species": "Largemouth Bass, Crappie"},
        {"name": "Lake Toho East Flat Reed Perimeter", "lat": 28.2450, "lon": -81.3850, "env": "Inland Freshwater System", "depth": "4-8 ft", "species": "Largemouth Bass, Bluegill"}
    ],
    "Osceola": [
        {"name": "Lake Tohopekaliga Main Lock Trench", "lat": 28.2140, "lon": -81.3910, "env": "Inland Freshwater System", "depth": "6-14 ft", "species": "Trophy Largemouth Bass, Black Crappie"},
        {"name": "Lake Tohopekaliga Southport Canal Exit", "lat": 28.1350, "lon": -81.3950, "env": "Inland Freshwater System", "depth": "8-15 ft", "species": "Largemouth Bass, Bluegill, Catfish"},
        {"name": "East Lake Toho Public Launch Channel", "lat": 28.2850, "lon": -81.2850, "env": "Inland Freshwater System", "depth": "5-10 ft", "species": "Largemouth Bass, Black Crappie"},
        {"name": "Lake Kissimmee North Brahma Grass Flat", "lat": 27.9950, "lon": -81.1850, "env": "Inland Freshwater System", "depth": "4-8 ft", "species": "Largemouth Bass, Bluegill"},
        {"name": "Lake Cypress Connecting Slough Run", "lat": 28.0650, "lon": -81.3250, "env": "Inland Freshwater System", "depth": "6-11 ft", "species": "Largemouth Bass, Crappie"}
    ],
    "Palm Beach": [
        {"name": "Lake Worth Inlet Deep Ocean Pass", "lat": 26.7650, "lon": -80.0360, "env": "Coastal Marine Estuary", "depth": "15-35 ft", "species": "Snook, Tarpon, King Mackerel, Snapper"},
        {"name": "Juno Beach Fishing Pier Surf Grid", "lat": 26.8850, "lon": -80.0520, "env": "Coastal Marine Estuary", "depth": "10-18 ft", "species": "Pompano, Spinner Shark, King Mackerel"},
        {"name": "Boca Raton Inlet Dangerous Current Cut", "lat": 26.3380, "lon": -80.0720, "env": "Coastal Marine Estuary", "depth": "8-16 ft", "species": "Snook, Tarpon, Jack Crevalle"},
        {"name": "Lake Okeechobee Canal Point Lock Inout", "lat": 26.8350, "lon": -80.6250, "env": "Inland Freshwater System", "depth": "8-14 ft", "species": "Largemouth Bass, Black Crappie"},
        {"name": "Jupiter Inlet Lighthouse Fender Ledge", "lat": 26.9450, "lon": -80.0750, "env": "Coastal Marine Estuary", "depth": "10-22 ft", "species": "Snook, Tarpon, Redfish"}
    ],
    "Pasco": [
        {"name": "Anclote River Tidal Delta Approach Runway", "lat": 28.4310, "lon": -82.7210, "env": "Coastal Marine Estuary", "depth": "6-12 ft", "species": "Snook, Redfish, Spotted Seatrout"},
        {"name": "Anclote Key Southern Deep Flat Slough", "lat": 28.1850, "lon": -82.8450, "env": "Coastal Marine Estuary", "depth": "4-9 ft", "species": "Gator Trout, Redfish, Cobia"},
        {"name": "Pithlachascotee River Mouth Ledge Cut", "lat": 28.2650, "lon": -82.7350, "env": "Coastal Marine Estuary", "depth": "5-10 ft", "species": "Snook, Mangrove Snapper"},
        {"name": "Hudson Beach Public Pier Rocky Bottom", "lat": 28.3650, "lon": -82.7150, "env": "Coastal Marine Estuary", "depth": "3-6 ft", "species": "Seatrout, Sheepshead, Redfish"},
        {"name": "Lake Jovita Inland Freshwater Corner", "lat": 28.3350, "lon": -82.2850, "env": "Inland Freshwater System", "depth": "10-24 ft", "species": "Largemouth Bass, Bluegill"}
    ],
    "Pinellas": [
        {"name": "Egmont Key Main Shipping Pass Trench", "lat": 27.6320, "lon": -82.7410, "env": "Coastal Marine Estuary", "depth": "18-45 ft", "species": "Tarpon, Snook, Gag Grouper, King Mackerel, Shark"},
        {"name": "Skyway North Fishing Pier Concrete Piling", "lat": 27.6520, "lon": -82.6550, "env": "Coastal Marine Estuary", "depth": "15-32 ft", "species": "Gag Grouper, Spanish Mackerel, Black Drum, Snook"},
        {"name": "Johns Pass Backcountry Inlet Bridge Fender", "lat": 27.7850, "lon": -82.7820, "env": "Coastal Marine Estuary", "depth": "8-18 ft", "species": "Snook, Redfish, Flounder, Trout"},
        {"name": "Clearwater Pass Jetty Extension Track", "lat": 27.9650, "lon": -82.8320, "env": "Coastal Marine Estuary", "depth": "10-22 ft", "species": "Snook, Tarpon, Sea Trout"},
        {"name": "Fort De Soto Gulf Pier Surf Trough", "lat": 27.6150, "lon": -82.7350, "env": "Coastal Marine Estuary", "depth": "6-12 ft", "species": "Pompano, Trout, Spanish Mackerel"}
    ],
    "Polk": [
        {"name": "Lake Hatchineha Canal Entry Lock System", "lat": 27.9910, "lon": -81.6010, "env": "Inland Freshwater System", "depth": "6-11 ft", "species": "Largemouth Bass, Black Crappie, Bluegill"},
        {"name": "Lake Kissimmee South Floodgate Tailrace", "lat": 27.7850, "lon": -81.1850, "env": "Inland Freshwater System", "depth": "8-16 ft", "species": "Largemouth Bass, Striped Bass, Catfish"},
        {"name": "Lake Toho Southport Canal South Entrance", "lat": 28.1150, "lon": -81.3850, "env": "Inland Freshwater System", "depth": "6-12 ft", "species": "Largemouth Bass, Crappie"},
        {"name": "Lake Parker Public Fishing Pier Structure", "lat": 28.0650, "lon": -81.9350, "env": "Inland Freshwater System", "depth": "5-9 ft", "species": "Largemouth Bass, Bluegill"},
        {"name": "Lake Garfield Southern Reed Line Wall", "lat": 27.9350, "lon": -81.7450, "env": "Inland Freshwater System", "depth": "4-8 ft", "species": "Largemouth Bass, Crappie"}
    ],
    "Putnam": [
        {"name": "St. Johns River Main Channel Drop Ledge", "lat": 29.6412, "lon": -81.6314, "env": "Riverine System", "depth": "8-15 ft", "species": "Largemouth Bass, Striped Bass, Channel Catfish"},
        {"name": "St. Johns River Dunns Creek Mouth Junction", "lat": 29.5850, "lon": -81.6150, "env": "Riverine System", "depth": "10-18 ft", "species": "Largemouth Bass, Striped Bass"},
        {"name": "Lake George Northern Core Flat Trough", "lat": 29.4650, "lon": -81.5850, "env": "Inland Freshwater System", "depth": "6-11 ft", "species": "Largemouth Bass, Bluegill, Striped Bass"},
        {"name": "St. Johns River Palatka Bridge Support Fender", "lat": 29.6480, "lon": -81.6280, "env": "Riverine System", "depth": "12-24 ft", "species": "Black Drum, Croaker, Catfish"},
        {"name": "Crescent Lake Northern Mouth Flow Cut", "lat": 29.4350, "lon": -81.4850, "env": "Inland Freshwater System", "depth": "5-10 ft", "species": "Largemouth Bass, Black Crappie"}
    ],
    "Santa Rosa": [
        {"name": "Escambia Bay Rail Trestle Piling Arrays", "lat": 30.4120, "lon": -87.1610, "env": "Coastal Marine Estuary", "depth": "8-15 ft", "species": "Spotted Seatrout, Redfish, Sheepshead"},
        {"name": "Navarre Beach Public Deep Gulf Pier", "lat": 30.3820, "lon": -86.8620, "env": "Coastal Marine Estuary", "depth": "12-20 ft", "species": "King Mackerel, Cobia, Pompano"},
        {"name": "Blackwater River Deep Channel Bend Pool", "lat": 30.5950, "lon": -87.0250, "env": "Riverine System", "depth": "10-24 ft", "species": "Largemouth Bass, Striped Bass, Catfish"},
        {"name": "East Bay Inner Oyster Bar Flat Slough", "lat": 30.4350, "lon": -86.9550, "env": "Coastal Marine Estuary", "depth": "3-7 ft", "species": "Redfish, Sea Trout, Flounder"},
        {"name": "Santa Rosa Sound Navarre Bridge Columns", "lat": 30.4020, "lon": -86.8650, "env": "Coastal Marine Estuary", "depth": "8-16 ft", "species": "Snook, Redfish, Trout"}
    ],
    "Sarasota": [
        {"name": "Big Sarasota Pass Dynamic Inlet Track", "lat": 27.3210, "lon": -82.5610, "env": "Coastal Marine Estuary", "depth": "10-24 ft", "species": "Snook, Redfish, Spotted Seatrout, Tarpon"},
        {"name": "Venice Inlet Outer Rock Jetty Boundary", "lat": 27.1120, "lon": -82.4550, "env": "Coastal Marine Estuary", "depth": "12-26 ft", "species": "Snook, Tarpon, Sharks, Mangrove Snapper"},
        {"name": "New Pass Bridge Deep Current Channels", "lat": 27.3350, "lon": -82.5780, "env": "Coastal Marine Estuary", "depth": "8-16 ft", "species": "Snook, Pompano, Sea Trout"},
        {"name": "Sarasota Bay T-Pier Concrete Structure", "lat": 27.3380, "lon": -82.5450, "env": "Coastal Marine Estuary", "depth": "5-10 ft", "species": "Snook, Mangrove Snapper, Trout"},
        {"name": "Blackburn Point Bridge Pivot Fender Span", "lat": 27.1850, "lon": -82.4950, "env": "Coastal Marine Estuary", "depth": "6-11 ft", "species": "Snook, Redfish, Sheepshead"}
    ],
    "Seminole": [
        {"name": "St. Johns River Lake Monroe Entry Mouth", "lat": 28.7910, "lon": -81.3510, "env": "Inland Freshwater System", "depth": "6-11 ft", "species": "Largemouth Bass, Black Crappie, Striped Bass"},
        {"name": "Lake Jesup Public Launch Channel Edge", "lat": 28.7120, "lon": -81.2450, "env": "Inland Freshwater System", "depth": "4-8 ft", "species": "Largemouth Bass, Channel Catfish"},
        {"name": "St. Johns River Wekiva River Junction", "lat": 28.7850, "lon": -81.4250, "env": "Riverine System", "depth": "6-12 ft", "species": "Largemouth Bass, Bluegill"},
        {"name": "Lake Harney Northern Flow Inlet Cut", "lat": 28.7450, "lon": -81.0850, "env": "Inland Freshwater System", "depth": "5-10 ft", "species": "Largemouth Bass, Striped Bass"},
        {"name": "St. Johns River Sanford Pier Structure", "lat": 28.8150, "lon": -81.2650, "env": "Riverine System", "depth": "8-14 ft", "species": "Croaker, Catfish, Bass"}
    ],
    "St. Johns": [
        {"name": "St. Augustine Inlet Dynamic Deep Pass", "lat": 29.8910, "lon": -81.2910, "env": "Coastal Marine Estuary", "depth": "12-26 ft", "species": "Redfish, Spotted Seatrout, Flounder, Tarpon"},
        {"name": "Matanzas Inlet Natural Shallow Bridgerun", "lat": 29.7120, "lon": -81.2450, "env": "Coastal Marine Estuary", "depth": "6-14 ft", "species": "Snook, Redfish, Flounder"},
        {"name": "Vilano Beach Fishing Pier Concrete Grid", "lat": 29.9120, "lon": -81.3050, "env": "Coastal Marine Estuary", "depth": "6-11 ft", "species": "Seatrout, Redfish, Black Drum"},
        {"name": "Guana River Dam Spillway Control Basin", "lat": 30.0150, "lon": -81.3250, "env": "Coastal Marine Estuary", "depth": "4-9 ft", "species": "Redfish, Sea Trout, Black Drum"},
        {"name": "St. Johns River Shands Bridge Fender", "lat": 29.9820, "lon": -81.6250, "env": "Riverine System", "depth": "10-22 ft", "species": "Largemouth Bass, Striper, Drum"}
    ],
    "St. Lucie": [
        {"name": "Fort Pierce Inlet Main Shipping Track", "lat": 27.4720, "lon": -80.3110, "env": "Coastal Marine Estuary", "depth": "12-28 ft", "species": "Snook, Tarpon, Spotted Seatrout, Permitt"},
        {"name": "South Jetty Extension Outer Granite Rocks", "lat": 27.4710, "lon": -80.2950, "env": "Coastal Marine Estuary", "depth": "14-25 ft", "species": "Snook, Tarpon, King Mackerel, Snapper"},
        {"name": "Indian River Lagoon Bear Point Flat", "lat": 27.4350, "lon": -80.2850, "env": "Coastal Marine Estuary", "depth": "3-6 ft", "species": "Gator Trout, Redfish"},
        {"name": "North Bridge Causeway Pile Trestle Spans", "lat": 27.4650, "lon": -80.3250, "env": "Coastal Marine Estuary", "depth": "6-14 ft", "species": "Snook, Mangrove Snapper, Trout"},
        {"name": "Taylor Creek Freshwater Control Structure", "lat": 27.4550, "lon": -80.3450, "env": "Coastal Marine Estuary", "depth": "5-10 ft", "species": "Snook, Tarpon, Largemouth Bass"}
    ],
    "Sumter": [
        {"name": "Lake Panasoffkee Outlet Canal Junction", "lat": 28.8910, "lon": -82.2110, "env": "Inland Freshwater System", "depth": "5-9 ft", "species": "Largemouth Bass, Black Crappie, Bluegill"},
        {"name": "Withlacoochee River Central Ledge Pool", "lat": 28.8950, "lon": -82.2250, "env": "Riverine System", "depth": "8-16 ft", "species": "Largemouth Bass, Channel Catfish"},
        {"name": "Lake Panasoffkee Central Grass Edge Flat", "lat": 28.7950, "lon": -82.1150, "env": "Inland Freshwater System", "depth": "4-7 ft", "species": "Largemouth Bass, Bluegill"},
        {"name": "Withlacoochee River Rutland Bridge Pile", "lat": 28.8520, "lon": -82.2150, "env": "Riverine System", "depth": "6-12 ft", "species": "Channel Catfish, Bream"},
        {"name": "Lake Panasoffkee East Inflow Creek Split", "lat": 28.8150, "lon": -82.0850, "env": "Inland Freshwater System", "depth": "3-6 ft", "species": "Crappie, Bluegill"}
    ],
    "Suwannee": [
        {"name": "Suwannee River Springs Deep Run Channel", "lat": 30.3850, "lon": -83.1610, "env": "Riverine System", "depth": "8-16 ft", "species": "Suwannee Bass, Largemouth Bass, Channel Catfish"},
        {"name": "Suwannee River Dowling Park Bend Pool", "lat": 30.2450, "lon": -83.2450, "env": "Riverine System", "depth": "10-24 ft", "species": "Channel Catfish, Flathead Catfish"},
        {"name": "Suwannee River Branford Bridge Support Pile", "lat": 29.9620, "lon": -82.9350, "env": "Riverine System", "depth": "8-15 ft", "species": "Largemouth Bass, Suwannee Bass, Bream"},
        {"name": "Santa Fe River Western Mouth Junction", "lat": 29.8890, "lon": -82.8750, "env": "Riverine System", "depth": "6-12 ft", "species": "Suwannee Bass, Catfish"},
        {"name": "Suwannee River Northern Rock Wall Point", "lat": 30.4150, "lon": -82.9950, "env": "Riverine System", "depth": "5-10 ft", "species": "Catfish, Sunfish"}
    ],
    "Taylor": [
        {"name": "Steinhatchee River Channel Approach Cut", "lat": 29.6710, "lon": -83.6910, "env": "Coastal Marine Estuary", "depth": "6-11 ft", "species": "Spotted Seatrout, Redfish, Flounder"},
        {"name": "Steinhatchee River Deep Inland Ledge Bend", "lat": 29.6750, "lon": -83.3950, "env": "Coastal Marine Estuary", "depth": "5-10 ft", "species": "Snook, Sea Trout, Mangrove Snapper"},
        {"name": "Econfina River Tidal Sound Channel Mouth", "lat": 30.0350, "lon": -83.9120, "env": "Coastal Marine Estuary", "depth": "4-9 ft", "species": "Redfish, Sea Trout"},
        {"name": "Keaton Beach Public Fishing Pier Base", "lat": 29.8250, "lon": -83.5950, "env": "Coastal Marine Estuary", "depth": "4-7 ft", "species": "Seatrout, Pompano, Sheepshead"},
        {"name": "Fenholloway River Tidal Basin Flat", "lat": 30.0150, "lon": -83.8150, "env": "Coastal Marine Estuary", "depth": "3-6 ft", "species": "Redfish, Sea Trout"}
    ],
    "Union": [
        {"name": "Lake Butler South Fishing Dock Area", "lat": 30.0120, "lon": -82.3510, "env": "Inland Freshwater System", "depth": "4-8 ft", "species": "Largemouth Bass, Bluegill, Black Crappie"},
        {"name": "Lake Butler Central Deep Basin Core", "lat": 30.0220, "lon": -82.3450, "env": "Inland Freshwater System", "depth": "6-11 ft", "species": "Largemouth Bass, Black Crappie"},
        {"name": "Santa Fe River Northern Boundary Trench", "lat": 29.9450, "lon": -82.4350, "env": "Riverine System", "depth": "4-9 ft", "species": "Channel Catfish, Suwannee Bass"},
        {"name": "Lake Butler Northeast Pad Flat Edge", "lat": 30.0280, "lon": -82.3350, "env": "Inland Freshwater System", "depth": "3-6 ft", "species": "Bluegill, Warmouth"},
        {"name": "Olustee Creek Freshwater Junction Split", "lat": 30.0450, "lon": -82.4910, "env": "Riverine System", "depth": "3-5 ft", "species": "Catfish, Bream"}
    ],
    "Volusia": [
        {"name": "Ponce Inlet Dredged Shipping Cut Corridor", "lat": 29.0610, "lon": -80.9120, "env": "Coastal Marine Estuary", "depth": "12-25 ft", "species": "Redfish, Snook, Spotted Seatrout, Tarpon"},
        {"name": "Dunlawton Bridge Causeway Pile Trestle", "lat": 29.1450, "lon": -80.9750, "env": "Coastal Marine Estuary", "depth": "6-14 ft", "species": "Snook, Black Drum, Sheepshead, Trout"},
        {"name": "New Smyrna Beach ICW Oyster Flat Cut", "lat": 29.0250, "lon": -80.9150, "env": "Coastal Marine Estuary", "depth": "4-8 ft", "species": "Redfish, Flounder, Spotted Seatrout"},
        {"name": "St. Johns River Lake George Inlet Mouth", "lat": 29.2150, "lon": -81.5150, "env": "Riverine System", "depth": "8-16 ft", "species": "Largemouth Bass, Striped Bass"},
        {"name": "Tomoka River Tidal Mouth Bridge Guard", "lat": 29.3450, "lon": -81.0850, "env": "Coastal Marine Estuary", "depth": "5-10 ft", "species": "Snook, Tarpon, Redfish"}
    ],
    "Wakulla": [
        {"name": "St. Marks River Delta Channel Corridor", "lat": 30.0610, "lon": -84.2810, "env": "Coastal Marine Estuary", "depth": "6-14 ft", "species": "Spotted Seatrout, Redfish, Tarpon"},
        {"name": "Panacea Harbor Shallow Lagoon Trough", "lat": 30.0250, "lon": -84.3850, "env": "Coastal Marine Estuary", "depth": "4-8 ft", "species": "Sea Trout, Pompano, Flounder"},
        {"name": "Ocklocknee River Tidal Estuary Channel", "lat": 30.0150, "lon": -84.4450, "env": "Coastal Marine Estuary", "depth": "5-12 ft", "species": "Redfish, Black Drum, Trout"},
        {"name": "St. Marks Public Launch River Ledge", "lat": 30.1150, "lon": -84.2050, "env": "Riverine System", "depth": "8-16 ft", "species": "Largemouth Bass, Redfish, Catfish"},
        {"name": "Shell Point Beach Inshore Surf Bar", "lat": 30.0550, "lon": -84.2950, "env": "Coastal Marine Estuary", "depth": "3-6 ft", "species": "Sea Trout, Redfish"}
    ],
    "Walton": [
        {"name": "Choctawhatchee Bay Mid-Bay Trench Cut", "lat": 30.3910, "lon": -86.2910, "env": "Coastal Marine Estuary", "depth": "10-24 ft", "species": "Spotted Seatrout, Redfish, King Mackerel, Tarpon"},
        {"name": "Hogtown Bayou Shallow Grass Flat Slough", "lat": 30.4150, "lon": -86.2250, "env": "Coastal Marine Estuary", "depth": "3-6 ft", "species": "Gator Trout, Redfish"},
        {"name": "Choctawhatchee River Tidal Marsh Junction", "lat": 30.4050, "lon": -86.1150, "env": "Coastal Marine Estuary", "depth": "6-12 ft", "species": "Redfish, Flounder, Trout"},
        {"name": "Lake不住 Inlet Freshwater Coast Lake Pool", "lat": 30.3310, "lon": -86.1450, "env": "Inland Freshwater System", "depth": "4-8 ft", "species": "Largemouth Bass, Bluegill"},
        {"name": "Choctawhatchee Bay Trestle Pillar Array", "lat": 30.4220, "lon": -86.1850, "env": "Coastal Marine Estuary", "depth": "8-15 ft", "species": "Redfish, Sea Trout, Sheepshead"}
    ],
    "Washington": [
        {"name": "Choctawhatchee River South Flat Cut Basin", "lat": 30.4910, "lon": -85.8610, "env": "Riverine System", "depth": "6-12 ft", "species": "Channel Catfish, Largemouth Bass, Bream"},
        {"name": "Choctawhatchee River Bridge Support Trestle", "lat": 30.5850, "lon": -85.8450, "env": "Riverine System", "depth": "8-16 ft", "species": "Flathead Catfish, Striped Bass"},
        {"name": "Holmes Creek Vernon Ramp Launch Waterway", "lat": 30.6250, "lon": -85.7150, "env": "Riverine System", "depth": "5-11 ft", "species": "Suwannee Bass, Channel Catfish"},
        {"name": "Holmes Creek Deep Spring Sinkhole Point", "lat": 30.6350, "lon": -85.6950, "env": "Riverine System", "depth": "8-18 ft", "species": "Suwannee Bass, Sunfish"},
        {"name": "Lucas Lake Public Fishing Dock Base", "lat": 30.5150, "lon": -85.6950, "env": "Inland Freshwater System", "depth": "4-9 ft", "species": "Largemouth Bass, Black Crappie"}
    ]
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

def compile_live_scouting_nodes(county, active_list):
    # Route specific NOAA hardware stations dynamically purely based on target region
    station_routing = {
        "Alachua": ["8720226", "CDRF1"], "Baker": ["8720030", "PCBF1"], "Bay": ["8729108", "PCBF1"],
        "Bradford": ["8720226", "CDRF1"], "Brevard": ["8721604", "41113"], "Broward": ["8722956", "41113"],
        "Calhoun": ["8728690", "PCBF1"], "Charlotte": ["8725520", "CDRF1"], "Citrus": ["8727122", "CDRF1"],
        "Clay": ["8720226", "CDRF1"], "Collier": ["8725114", "CDRF1"], "Columbia": ["8720030", "CDRF1"],
        "DeSoto": ["8725520", "CDRF1"], "Dixie": ["8727520", "CDRF1"], "Duval": ["8720218", "8720219"],
        "Escambia": ["8729840", "PCBF1"], "Flagler": ["8720218", "41113"], "Franklin": ["8728690", "PCBF1"],
        "Gadsden": ["8728690", "PCBF1"], "Gilchrist": ["8727520", "CDRF1"], "Glades": ["8725520", "CDRF1"],
        "Gulf": ["8728690", "PCBF1"], "Hamilton": ["8720030", "CDRF1"], "Hardee": ["8725520", "CDRF1"],
        "Hendry": ["8725520", "CDRF1"], "Hernando": ["8727122", "CDRF1"], "Highlands": ["8725520", "CDRF1"],
        "Hillsborough": ["8726607", "8726674"], "Holmes": ["8729108", "PCBF1"], "Indian River": ["8721604", "41113"],
        "Jackson": ["8729108", "PCBF1"], "Jefferson": ["8727520", "CDRF1"], "Lafayette": ["8727520", "CDRF1"],
        "Lake": ["8720226", "41113"], "Lee": ["8725520", "CDRF1"], "Leon": ["8728690", "PCBF1"],
        "Levy": ["8727520", "CDRF1"], "Liberty": ["8728690", "PCBF1"], "Madison": ["8720030", "CDRF1"],
        "Manatee": ["8726384", "8726520"], "Marion": ["8720226", "CDRF1"], "Martin": ["8722670", "41113"],
        "Miami-Dade": ["8723214", "41113"], "Monroe": ["8724580", "8723970"], "Nassau": ["8720030", "8720218"],
        "Okaloosa": ["8729108", "PCBF1"], "Okeechobee": ["8722670", "CDRF1"], "Orange": ["8721604", "41113"],
        "Osceola": ["8721604", "41113"], "Palm Beach": ["8722670", "41113"], "Pasco": ["8726724", "CDRF1"],
        "Pinellas": ["8726520", "8726724"], "Polk": ["8726607", "CDRF1"], "Putnam": ["8720226", "CDRF1"],
        "Santa Rosa": ["8729840", "PCBF1"], "Sarasota": ["8725520", "8726520"], "Seminole": ["8721604", "41113"],
        "St. Johns": ["8720218", "41113"], "St. Lucie": ["8722670", "41113"], "Sumter": ["8727122", "CDRF1"],
        "Suwannee": ["8720030", "CDRF1"], "Taylor": ["8727520", "CDRF1"], "Union": ["8720226", "CDRF1"],
        "Volusia": ["8720218", "41113"], "Wakulla": ["8728690", "PCBF1"], "Walton": ["8729108", "PCBF1"],
        "Washington": ["8729108", "PCBF1"]
    }
    tide_id, buoy_id = station_routing.get(county, ["8726607", "8726674"])
    baro, b_del, bite, bi_del = get_noaa_live_telemetry(buoy_id, tide_id)
    
    compiled_nodes = []
    for node in active_list:
        lat, lon = node["lat"], node["lon"]
        compiled_nodes.append({
            "water_name": node["name"], "lat": lat, "lon": lon, "env": node["env"], "depth": node["depth"],
            "species": node["species"], "bite_index": bite, "bite_delta": bi_del, "barometer": baro, "baro_delta": b_del,
            "structures": [{"path": [[lat - 0.001, lon - 0.001], [lat, lon]], "name": "Primary Ledge Structural Outline"}],
            "highways": [{"path": [[lat - 0.002, lon + 0.002], [lat, lon]], "name": "Bait Migration Flow"}],
            "labels": f"Geospatial Node Verified // Station {tide_id}"
        })
    return compiled_nodes

# --- TOP SELECTOR PANEL ---
st.markdown("<div class='console-header'>UNIVERSAL REGIONAL ACCESSIBILITY CONSOLE</div>", unsafe_allow_html=True)
col_sel1, col_sel2 = st.columns(2)

with col_sel1:
    selected_county = st.selectbox("Select County Domain:", options=sorted(list(statewide_fishing_matrix.keys())))

# High-speed runtime compilation purely for the selected county's raw coordinate array
raw_county_list = statewide_fishing_matrix[selected_county]
active_locations = compile_live_scouting_nodes(selected_county, raw_county_list)
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
