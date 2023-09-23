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

ranges_table = pd.read_csv(os.path.join(os.path.dirname(path), "DatosIniciales", "RangosPresiones_variables.csv"))

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
station_ranges = ranges_table.loc[ranges_table["Estacion"] == selection1, :].iloc[:, 1:]
rcols = ["Mes inicial", "Mes final", "Hora inicial", "Hora final", "Min1 (kg/cm2)", "Max1 (kg/cm2)",
          "Min2 (kg/cm2)", "Max2 (kg/cm2)", "Min3 (kg/cm2)", "Max3 (kg/cm2)", "Min4 (kg/cm2)", "Max4 (kg/cm2)"]
station_ranges.columns = rcols

def highlight_cols(s, coldict):
    if s.name in coldict.keys():
        return ['background-color: {}'.format(coldict[s.name])] * len(s)
    return [''] * len(s)

coldict = {
    "Min1 (kg/cm2)": "#009d5f",
    "Max1 (kg/cm2)": "#009d5f",
    "Min2 (kg/cm2)": "#f4d03f",
    "Max2 (kg/cm2)": "#f4d03f",
    "Min3 (kg/cm2)": "#e74c3c",
    "Max3 (kg/cm2)": "#e74c3c",
    "Min4 (kg/cm2)": "#8e44ad",
    "Max4 (kg/cm2)": "#8e44ad"
}


if len(data) > 0:
    data_station = data[["ID", "Nombre", "X", "Y", "Carga", "Instalacion"]].rename({
        "ID": "Clave",
        "Nombre": "Nombre",
        "X": "Longitud",
        "Y": "Latitud",
        "Carga": "Carga de Posición (kg/cm2)",
        "Instalacion": "Fecha de Instalación",
    }).to_frame()
    data_station.columns = ["Información"]

    if data["FuenteTipo2"]:
        data_source = data[["FuenteTipo1", "FuenteNombre1", "FuenteUbicacion1",
                            "FuenteTipo2", "FuenteNombre2", "FuenteUbicacion2"]].rename({
            "FuenteTipo1": "Tipo 1",
            "FuenteNombre1": "Nombre 1",
            "FuenteUbicacion1": "Ubicación 1",
            "FuenteTipo2": "Tipo 2",
            "FuenteNombre2": "Nombre 2",
            "FuenteUbicacion2": "Ubicación 2"
        }).to_frame()
    else:
        data_source = data[["FuenteTipo1", "FuenteNombre1", "FuenteUbicacion1"]].rename({
            "FuenteTipo1": "Tipo",
            "FuenteNombre1": "Nombre",
            "FuenteUbicacion1": "Ubicación"
        }).to_frame()
    data_source.columns = ["Información"]

    data_sensor = data[["Diametro", "SensorMaterial", "SensorUbicacion"]].rename({
        "Diametro": "Diámetro (pulg)",
        "SensorMaterial": "Material",
        "SensorUbicacion": "Ubicación",
    }).to_frame()
    data_sensor.columns = ["Información"]

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
        st.dataframe(data_station, use_container_width=True)
        st.markdown("**Fuente de Abastecimiento**")
        st.dataframe(data_source, use_container_width=True)
        st.markdown("**Datos del sensor**")
        st.dataframe(data_sensor, use_container_width=True)
        st.markdown("**Rango de Presiones de Operación**")
        st.markdown("**Rango Recomendado**", help="""Rango **Recomendado** corresponde a las presiones recomendadas en el MAPAS de Conagua,
    que en este caso sería de 1.5 a 5 kg/cm² más la carga de posición de cada estación.""")
        st.dataframe(pressure_ranges, use_container_width=True)
        st.markdown("**Rangos Variables**", help="""Rangos **Variables** corresponden a los rangos normales de operación según el día y el horario,
    con base en el análisis de la información de 2021.""")
        st.markdown("Se muestran los rangos de presión para los Semaforos Verde (Buen funcionamiento), Amarillo (Sobrepresión), Rojo (Presión baja), y Violeta (Fuera de funcionamiento).")
        st.dataframe(station_ranges.style.apply(highlight_cols, coldict=coldict), use_container_width=True)
        

    with col2:
        st.markdown("**Ubicación de la Estación**")
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("Ver Croquis Esquemático"):
            filename = os.path.join(path, "..", "img", f"croquis_{data['ID']}.png")
            if os.path.exists(filename):
                st.image(Image.open(filename), use_column_width="always")
            else:
                st.warning("Imagen no disponible.")






