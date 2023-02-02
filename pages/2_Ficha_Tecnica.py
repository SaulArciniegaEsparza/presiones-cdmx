# -*- coding: utf-8 -*-
"""
Fiecha tecnica por estacion

@author: zaula
"""

#%% Libraries
import os
import datetime
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

import data_bases as dbs


#%% Datos iniciales

path = os.path.dirname(os.path.abspath(__file__))

if "ids" not in st.session_state:
    db = dbs.DataBase()
    ids = db.get_stations_id()
    db.close()
    st.session_state["ids"] = ids

#%% Definir funciones

def get_staion_data(ide):
    db = dbs.DataBase()
    data = db.get_station(int(ide))
    db.close()
    return data


def get_pressure_ranges(clave, ide):
    pbd = dbs.PresionesRangosDB()
    pressure_ranges = pbd.get_pressure_ranges(clave, ids=int(ide))
    pbd.close()
    return pressure_ranges


def plot_station(data, basemap, show_sectors=False, sectors_color="#2c3e50",
                show_network=False, network_color="#C1382E"):
    data_table = data.rename({
        "Diametro": "Diámetro (pulg)",
        "Carga": "Carga de Posición (kg/cm2)",
        "Instalacion": "Instalación"
    }).to_frame().transpose()
    
    fig = px.scatter_mapbox(
        data_table,
        lat="Y",
        lon="X",
        hover_name="Nombre",
        size=[10],
        color_discrete_sequence=["#303030"],
        hover_data=["ID", "Nombre", "Diámetro (pulg)",
                   "Carga de Posición (kg/cm2)", "Instalación"],
        mapbox_style=basemap,
        center={"lat": data["Y"], "lon": data["X"]},
        size_max=10,
        opacity=0.9,
        zoom=11,
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        
    mapbox_layers = []
    if show_sectors:
        mapbox_layers.append(
            {
                "sourcetype": "geojson",
                "source": st.session_state["sectors_layer"],
                "type": "line",
                "color": sectors_color,
                "line": {
                    "width": 1,
                    },
            }
        )
    if show_network:
        mapbox_layers.append(
            {
                "sourcetype": "geojson",
                "source": st.session_state["network_layer"],
                "type": "line",
                "color": network_color,
                "line": {
                    "width": 1.5,
                    },
            }
        )
    if mapbox_layers:
        fig["layout"]["mapbox"]["layers"] = mapbox_layers
    
    return fig


#%% App

st.title("Ficha técnica de estaciones")
st.sidebar.title("Sistema de Presiones CDMX")
selection1 = st.sidebar.selectbox("Seleccionar estación", st.session_state["ids"], key="ficha1-select")

st.sidebar.subheader("Opciones de visualización")
basemap1 = st.sidebar.selectbox(
    "Mapa base",
    ["carto-positron", "carto-darkmatter", "open-street-map", "white-bg", "stamen-toner"],
    index=0,
    key="ficha-map-basemap"
)
show_network1 = st.sidebar.checkbox("Mostrar red primaria", key="ficha-map-layer1")
show_sectors1 = st.sidebar.checkbox("Mostrar sectores", key="ficha-map-layer2")
network_color1 = st.sidebar.color_picker("Color de red primaria", "#C1382E", key="ficha-map-clayer1")
sectors_color1 = st.sidebar.color_picker("Color de sectores", "#2c3e50", key="ficha-map-clayer2")

data = get_staion_data(selection1)

if len(data) > 0:
    data_table = data.rename({
        "ID": "Clave",
        "Nombre": "Nombre",
        "X": "Longitud",
        "Y": "Latitud",
        "Diametro": "Diámetro (pulg)",
        "Carga": "Carga de Posición (kg/cm2)",
        "Instalacion": "Fecha de Instalación"
    }).to_frame()
    data_table.columns = ["Información"]

    pressure_ranges = get_pressure_ranges("Constantes", ide=data["ID"])
    pressure_ranges = pressure_ranges.rename({
        "MinPresion": "Presión mínima",
        "MaxPresion": "Presión máxima",
    }).to_frame()
    pressure_ranges.columns = ["Presión (kg/cm2)"]

    fig = plot_station(
        data,
        basemap1,
        show_sectors=show_sectors1,
        sectors_color=sectors_color1,
        show_network=show_network1,
        network_color=network_color1
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Información de la Estación**")
        st.dataframe(data_table, use_container_width=True)
        st.markdown("**Rango de Presiones de Operación**")
        st.markdown("**(Sacmex, Subdirección de Medición y Control de Agua Potable)**")
        st.dataframe(pressure_ranges, use_container_width=True)    

    with col2:
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("Ver Croquis Esquemático"):
            filename = os.path.join(path, "..", "img", f"croquis_{data['ID']}.png")
            if os.path.exists(filename):
                st.image(Image.open(filename), use_column_width="always")
            else:
                st.warning("Imagen no disponible.")






