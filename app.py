#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 28 21:46:09 2025

@author: tpminh
"""

import os


import streamlit as st
from streamlit_folium import st_folium
import folium
import os
from PIL import Image, ExifTags



# --- PAGE CONFIG ---
st.set_page_config(page_title="Photo Map Gallery", layout="wide")
st.title("🗺️ Photo Map Gallery")

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
    "Hanoi": {
        "coords": [21.0285, 105.8542],
        "images": ["images/vn_1.jpg", "images/vn_2.jpg", "images/vn_3.jpg"],
        "desc": "Vietnam’s capital – Old Quarter charm, lakes, and street food culture."
    },
    "Thailand": {
        "coords": [13.7563, 100.5018],
        "images": ["images/thai_1.jpg", "images/thai_2.jpg", "images/thai_3.jpg"],
        "desc": "The Land of Smiles – tropical beaches, temples, and vibrant markets."
    },
    "Japan": {
        "coords": [35.6762, 139.6503],
        "images": ["images/japan_1.jpg", "images/japan_2.jpg", "images/japan_3.jpg"],
        "desc": "Tradition meets technology – cherry blossoms, sushi, and samurai heritage."
    },
}


# --- CREATE MAP ---
m = folium.Map(location=[35, 135], zoom_start=3)
for name, info in locations.items():
    folium.Marker(location=info["coords"], tooltip=name, popup=name).add_to(m)


# --- LAYOUT (map bigger, photo smaller) ---
col_map, col_img = st.columns([1.6, 1])

with col_map:
    st.markdown("### 🌍 Click a pin to view photos")
    map_data = st_folium(m, width=900, height=650)

with col_img:
    st.markdown("### 📸 Photo Gallery")

    # ✅ Scrollable Streamlit container (stays aligned with map)
    gallery = st.container(height=650, border=False)

    with gallery:
        if map_data and map_data.get("last_object_clicked"):
            clicked_lat = map_data["last_object_clicked"]["lat"]
            clicked_lng = map_data["last_object_clicked"]["lng"]

            def dist(a, b): return (a[0]-b[0])**2 + (a[1]-b[1])**2
            nearest_name = min(
                locations.keys(),
                key=lambda k: dist(locations[k]["coords"], [clicked_lat, clicked_lng])
            )
            loc = locations[nearest_name]

            st.markdown(f"#### 📍 {nearest_name}")
            st.markdown(f"**{loc['desc']}**")

            # ✅ Full-width images, large and scrollable
            for p in loc["images"]:
                if os.path.exists(p):
                    img = open_image_auto_oriented(p)
                    st.markdown(
                        f"""
                        <div style='margin-bottom:15px;'>
                            <img src='data:image/jpeg;base64,{st.image(img, use_container_width=True, output_format="JPEG")._image_data}'
                                 style='width:100%; border-radius:10px;'>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.info("Click a location pin on the map to see its photo gallery.")
            
            