#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 28 21:46:09 2025

@author: tpminh
"""

import os
import base64

import folium
import streamlit as st
import streamlit.components.v1 as components
from PIL import ExifTags, Image
from streamlit_folium import st_folium


# --- PAGE CONFIG ---
st.set_page_config(page_title="Atlas Photo Gallery", page_icon="🌏", layout="wide")


# --- STYLING ---
st.markdown(
    """
<style>
    :root {
        --ink: #1d2320;
        --muted: #66716c;
        --paper: #fffaf2;
        --line: rgba(29, 35, 32, 0.12);
        --terracotta: #c95f3f;
        --moss: #55745e;
        --gold: #d69d3a;
    }

    .stApp {
        background:
            radial-gradient(circle at 15% 10%, rgba(214, 157, 58, 0.20), transparent 32rem),
            linear-gradient(135deg, #fff9ef 0%, #f3eadc 48%, #edf3ee 100%);
        color: var(--ink);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1280px;
    }

    h1, h2, h3, h4 {
        letter-spacing: 0;
    }

    .hero {
        padding: 1.4rem 0 1.8rem;
        border-bottom: 1px solid var(--line);
        margin-bottom: 1.1rem;
    }

    .hero-kicker {
        color: var(--terracotta);
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }

    .hero-title {
        font-size: clamp(2.3rem, 4vw, 4.7rem);
        line-height: 0.96;
        font-weight: 900;
        color: var(--ink);
        margin: 0;
    }

    .hero-copy {
        color: var(--muted);
        font-size: 1.04rem;
        max-width: 54rem;
        margin-top: 0.9rem;
    }

    .section-title {
        color: var(--ink);
        font-size: 1rem;
        font-weight: 800;
        margin: 0 0 0.7rem;
    }

    .travel-card {
        background: rgba(255, 250, 242, 0.78);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 18px 50px rgba(79, 65, 43, 0.12);
    }

    .country-card {
        background: #fffaf2;
        border: 1px solid var(--line);
        border-left: 5px solid var(--accent);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }

    .country-name {
        font-size: 1.7rem;
        font-weight: 900;
        margin-bottom: 0.25rem;
        color: var(--ink);
    }

    .country-desc {
        color: var(--muted);
        line-height: 1.55;
        margin-bottom: 0.75rem;
    }

    .stat-row {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.55rem;
        margin-top: 0.8rem;
    }

    .stat {
        background: rgba(255, 255, 255, 0.58);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 0.65rem;
    }

    .stat-label {
        color: var(--muted);
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
    }

    .stat-value {
        color: var(--ink);
        font-size: 0.95rem;
        font-weight: 800;
        margin-top: 0.15rem;
    }

    [data-testid="stImage"] img {
        width: 100% !important;
        height: auto !important;
        border-radius: 8px;
        box-shadow: 0 12px 34px rgba(39, 43, 38, 0.16);
        border: 1px solid rgba(255, 255, 255, 0.7);
    }

    iframe {
        border-radius: 8px;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 8px;
        border-color: var(--line);
        background: rgba(255, 250, 242, 0.45);
    }

    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: 1px solid var(--line);
        background: rgba(255, 250, 242, 0.88);
        color: var(--ink);
        font-weight: 800;
    }

    .stButton > button:hover {
        border-color: var(--terracotta);
        color: var(--terracotta);
    }

    audio {
        width: 100%;
        margin-top: 0.35rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


# --- FIX ORIENTATION FUNCTION ---
def open_image_auto_oriented(path):
    img = Image.open(path)
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == "Orientation":
                break
        exif = img._getexif()
        if exif is not None:
            orientation_value = exif.get(orientation, None)
            if orientation_value == 3:
                img = img.rotate(180, expand=True)
            elif orientation_value == 6:
                img = img.rotate(270, expand=True)
            elif orientation_value == 8:
                img = img.rotate(90, expand=True)
    except Exception:
        pass
    return img


# --- DEFINE LOCATIONS ---
locations = {
    "Vietnam": {
        "city": "Hanoi",
        "coords": [21.0285, 105.8542],
        "images": ["images/vn_1.jpg", "images/vn_2.jpg", "images/vn_3.jpg"],
        "audio": "audio/vietnam.wav",
        "accent": "#c95f3f",
        "marker_icon": "star",
        "sound": "Layered flute, plucked strings, soft drum, bell, and warm drone",
        "season": "Autumn light",
        "flavor": "Lakeside streets",
        "desc": "Vietnam's capital blends Old Quarter lanes, quiet lakes, street food, and layered colonial architecture.",
    },
    "Thailand": {
        "city": "Bangkok",
        "coords": [13.7563, 100.5018],
        "images": ["images/thai_1.jpg", "images/thai_2.jpg", "images/thai_3.jpg"],
        "audio": "audio/thailand.wav",
        "accent": "#d69d3a",
        "marker_icon": "music",
        "sound": "Bright bell melody with plucked rhythm, soft percussion, and pad",
        "season": "Golden evenings",
        "flavor": "Temple markets",
        "desc": "Thailand moves between golden temples, floating markets, tropical color, and an easy street rhythm.",
    },
    "Japan": {
        "city": "Tokyo",
        "coords": [35.6762, 139.6503],
        "images": ["images/japan_1.jpg", "images/japan_2.jpg", "images/japan_3.jpg"],
        "audio": "audio/japan.wav",
        "accent": "#55745e",
        "marker_icon": "leaf",
        "sound": "Gentle flute, koto-like plucks, bell accents, and low drone",
        "season": "Spring calm",
        "flavor": "Garden city",
        "desc": "Japan pairs refined tradition with dense modern life, from quiet gardens to luminous city streets.",
    },
}


def ensure_audio_assets():
    missing_audio = [
        info["audio"] for info in locations.values() if not os.path.exists(info["audio"])
    ]
    if not missing_audio:
        return

    try:
        from scripts.generate_music import main as generate_music_assets

        generate_music_assets()
    except Exception as exc:
        st.warning(f"Unable to generate music assets: {exc}")


def nearest_location(clicked_lat, clicked_lng):
    def dist(coords):
        return (coords[0] - clicked_lat) ** 2 + (coords[1] - clicked_lng) ** 2

    return min(locations.keys(), key=lambda name: dist(locations[name]["coords"]))


ensure_audio_assets()


def render_autoplay_audio(path, label, accent):
    with open(path, "rb") as audio_file:
        encoded_audio = base64.b64encode(audio_file.read()).decode("utf-8")

    components.html(
        f"""
<style>
    .audio-shell {{
        background: rgba(255, 250, 242, 0.84);
        border: 1px solid rgba(29, 35, 32, 0.12);
        border-left: 5px solid {accent};
        border-radius: 8px;
        padding: 0.8rem;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}

    .audio-label {{
        color: #1d2320;
        font-size: 0.86rem;
        font-weight: 800;
        margin-bottom: 0.45rem;
    }}

    audio {{
        width: 100%;
    }}
</style>
<div class="audio-shell">
    <div class="audio-label">{label}</div>
    <audio id="nation-audio" controls autoplay loop playsinline preload="auto">
        <source src="data:audio/wav;base64,{encoded_audio}" type="audio/wav">
    </audio>
</div>
<script>
    const audio = document.getElementById("nation-audio");
    audio.volume = 0.72;
    const startAudio = () => {{
        audio.currentTime = 0;
        audio.play().catch(() => {{}});
    }};
    window.setTimeout(startAudio, 120);
</script>
""",
        height=112,
    )


if "selected_location" not in st.session_state:
    st.session_state.selected_location = "Vietnam"


# --- HEADER ---
st.markdown(
    """
<div class="hero">
    <div class="hero-kicker">Interactive travel atlas</div>
    <h1 class="hero-title">Photo Map Gallery</h1>
    <div class="hero-copy">
        Click a country marker to switch the gallery and hear a short original music loop inspired by that destination.
    </div>
</div>
""",
    unsafe_allow_html=True,
)


button_cols = st.columns(len(locations))
for col, name in zip(button_cols, locations):
    with col:
        if st.button(name, key=f"select_{name}"):
            st.session_state.selected_location = name


# --- CREATE MAP ---
selected_name = st.session_state.selected_location
selected = locations[selected_name]

m = folium.Map(
    location=selected["coords"],
    zoom_start=4,
    tiles=None,
    control_scale=True,
)
folium.TileLayer(
    tiles="CartoDB positron",
    name="Soft atlas",
    control=False,
).add_to(m)

for name, info in locations.items():
    is_selected = name == selected_name
    folium.Marker(
        location=info["coords"],
        tooltip=name,
        popup=f"{name} - {info['city']}",
        icon=folium.Icon(
            color="red" if is_selected else "green",
            icon=info["marker_icon"],
            prefix="fa",
        ),
    ).add_to(m)
    folium.CircleMarker(
        location=info["coords"],
        radius=17 if is_selected else 11,
        color=info["accent"],
        weight=3,
        fill=True,
        fill_color=info["accent"],
        fill_opacity=0.18 if is_selected else 0.08,
    ).add_to(m)


# --- LAYOUT ---
col_map, col_img = st.columns([1.45, 1], gap="large")

with col_map:
    st.markdown('<div class="section-title">Explore the map</div>', unsafe_allow_html=True)
    map_data = st_folium(
        m,
        width=820,
        height=650,
        key="travel_map",
        returned_objects=["last_object_clicked"],
    )

if map_data and map_data.get("last_object_clicked"):
    clicked_lat = map_data["last_object_clicked"]["lat"]
    clicked_lng = map_data["last_object_clicked"]["lng"]
    st.session_state.selected_location = nearest_location(clicked_lat, clicked_lng)

selected_name = st.session_state.selected_location
selected = locations[selected_name]

with col_img:
    st.markdown('<div class="section-title">Destination gallery</div>', unsafe_allow_html=True)
    gallery = st.container(height=650, border=False)

    with gallery:
        st.markdown(
            f"""
<div class="country-card" style="--accent: {selected['accent']}">
    <div class="country-name">{selected_name}</div>
    <div class="country-desc">{selected['desc']}</div>
    <div class="stat-row">
        <div class="stat">
            <div class="stat-label">City</div>
            <div class="stat-value">{selected['city']}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Mood</div>
            <div class="stat-value">{selected['season']}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Scene</div>
            <div class="stat-value">{selected['flavor']}</div>
        </div>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown("#### Local sound")
        st.caption(selected["sound"])
        if os.path.exists(selected["audio"]):
            render_autoplay_audio(
                selected["audio"],
                f"Now playing: {selected_name}",
                selected["accent"],
            )
        else:
            st.warning("Music file is missing for this destination.")

        st.markdown("#### Photos")
        for path in selected["images"]:
            if os.path.exists(path):
                img = open_image_auto_oriented(path)
                st.image(img, width="stretch", clamp=False)
            else:
                st.warning(f"Missing image: {path}")
