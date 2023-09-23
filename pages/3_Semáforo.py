# -*- coding: utf-8 -*-
"""
Mapa de visualizacion y tabla de estaciones

@author: zaula
"""

#%% Libraries
import os
import json
import datetime
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data_bases as dbs
import pressure_ranges as poperation


#%% Datos iniciales
PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

db = dbs.DataBase()
dates = db.get_time_period()
date1 = dates["min"].to_pydatetime().date()
date2 = dates["max"].to_pydatetime().date()
hour2 = dates["max"].hour
db.close()

if "ids" not in st.session_state:
    db = dbs.DataBase()
    ids = db.get_stations_id()
    db.close()
    st.session_state["ids"] = ids


#%% Funciones

@st.cache_data(persist="disk")
def load_sectors_layer(filename):
    with open(filename, encoding="utf-8") as fid:
        layer = json.load(fid)
    return layer


@st.cache_data(persist="disk")
def load_network_layer(filename):
    with open(filename, encoding="utf-8") as fid:
        layer = json.load(fid)
    return layer


if "sectors_layer" not in st.session_state:
    st.session_state["sectors_layer"] = load_sectors_layer(os.path.join(PATH, "Datos", "Sectores.geojson"))
if "network_layer" not in st.session_state:
    st.session_state["network_layer"] = load_network_layer(os.path.join(PATH, "Datos", "Red Primaria.geojson"))


def query_pressures2(date, hour, ids):
    if len(ids) == 0:
        ids = None
    db = dbs.DataBase()
    stations = db.get_stations()
    pressure = db.get_hourly_pressure(date, hour, ids)
    db.close()
    if len(pressure) == 0:
        return [], 0, {}
    
    # Numero de estaciones operativas
    if ids is None:
        year = pd.to_datetime(date).year
        mask = stations["Instalacion"] <= year  # solo estaciones instaladas
        stations = stations.loc[mask, :]
        ne = stations.shape[0]                  # numero total de estaciones
    else:
        ne = len(ids)

    stations = stations.loc[:, ["ID", "Nombre", "X", "Y", "Diametro", "Carga", "Instalacion"]]
    stations.columns = ["ID", "Nombre", "X", "Y", "Diámetro (pulg)", "Carga de Posición (kg/cm2)", "Instalación"]
    stations["Fecha"] = pd.to_datetime(date).strftime("%Y-%m-%d")
    stations["Hora"] = hour
    stations["Presion (km/cm2)"] = pressure.round(3)
    stations = stations.dropna()

    oe = stations.shape[0]  # estaciones con datos
    noe = ne - oe           # estaciones sin datos
    operation = {
        "Estaciones": ne,
        "Sin Datos": noe
    }

    flag = 1
    return stations, flag, operation
    

def plot_map(data, color_sequence, basemap, show_sectors=False, sectors_color="#2c3e50",
                      show_network=False, network_color="#C1382E"):
        
    fig = px.scatter_mapbox(
        data,
        lat="Y",
        lon="X",
        color="Semaforo",
        size="Presion (km/cm2)",
        hover_name="Nombre",
        hover_data=["ID", "Nombre", "Fecha", "Hora", "Presion (km/cm2)",
                    "Diámetro (pulg)", "Carga de Posición (kg/cm2)", "Instalación"],
        color_discrete_map=color_sequence,
        mapbox_style=basemap,
        center={"lat": 19.383, "lon": -99.147},
        size_max=15,
        opacity=0.9,
        zoom=9,
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
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


@st.cache_data
def download_data(data):
    return data.to_csv().encode('utf-8')


#%% Mapa de presiones

st.title("Semáforo de Operación de la Red de Agua Potable")
st.sidebar.title("Sistema de Presiones CDMX")
ranges_option2 = st.sidebar.selectbox("Tipo de rangos", ["Variables", "Recomendado"], key="ranges-map-option",
    help="""Rango **Recomendado** corresponde a las presiones recomendadas en el MAPAS de Conagua,
    que en este caso sería de 1.5 a 5 kg/cm² más la carga de posición de cada estación.
    Y los rangos **Variables** corresponden a los rangos normales de operación según el día y el horario,
    con base en el análisis de la información de 2021.""")
selection2 = st.sidebar.multiselect("Buscar estaciones", st.session_state["ids"], key="operation-map-select")
date2 = st.sidebar.date_input("Seleccionar fecha", value=date2, min_value=date1, max_value=date2, key="operation-map-date")
hour2 = st.sidebar.slider("Seleccionar hora", 0, 23, hour2, key="operation-map-hour")

st.sidebar.subheader("Opciones de visualización")
basemap2 = st.sidebar.selectbox(
    "Mapa base",
    ["carto-positron", "carto-darkmatter", "open-street-map", "white-bg", "stamen-toner"],
    index=0,
    key="operation-map-basemap"
)
show_network2 = st.sidebar.checkbox("Mostrar red primaria", key="operation-map-layer1")
show_sectors2 = st.sidebar.checkbox("Mostrar sectores", key="operation-map-layer2")
network_color2 = st.sidebar.color_picker("Color de red primaria", "#C1382E", key="operation-map-clayer1")
sectors_color2 = st.sidebar.color_picker("Color de sectores", "#2c3e50", key="operation-map-clayer2")

table, flag, status = query_pressures2(date2, hour2, selection2)

if flag == 0:
    st.error("¡No se han encontrado datos de presiones en ninguna estación para esa fecha!")

else:
    if ranges_option2 == "Variables":
        ranges_table = pd.read_csv(os.path.join(PATH, "DatosIniciales", "RangosPresiones_variables.csv"))
        table, operation, color_sequence = poperation.stations_operation(table, date2, hour2, ranges_table)

    elif ranges_option2 == "Recomendado":
        ranges_table = pd.read_csv(os.path.join(PATH, "DatosIniciales", "RangosPresiones_constantes.csv"))
        table, operation, color_sequence = poperation.constant_operation(table, ranges_table)

    fig = plot_map(table, color_sequence, basemap2, show_sectors2, sectors_color2,
                   show_network2, network_color2)

    st.markdown(f"Operación de la red el día **{date2} {hour2:02d}:00**")
    col1, col2 = st.columns(2)
    col1.metric("Estaciones", status["Estaciones"])
    col2.metric("Sin Datos", status["Sin Datos"])
    
    cols = st.columns(len(operation))
    for i, key in enumerate(operation.keys()):
        cols[i].metric(key, operation[key])
    
    st.plotly_chart(fig, use_container_width=True)
    output = download_data(table)
    st.download_button(
        label="Descargar datos de presiones",
        data=output,
        file_name=f"Presiones_{date2}.csv",
        mime="text/csv",
    )
    
    with st.expander(f"Tabla presiones en la red para el día: {date2} {hour2:02d}:00"):
        st.dataframe(table, use_container_width=True)


