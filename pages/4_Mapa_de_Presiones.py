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
import interpolation as intp


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

@st.cache(allow_output_mutation=True)
def load_sectors_layer(filename):
    with open(filename, encoding="utf-8") as fid:
        layer = json.load(fid)
    return layer


@st.cache(allow_output_mutation=True)
def load_network_layer(filename):
    with open(filename, encoding="utf-8") as fid:
        layer = json.load(fid)
    return layer


if "sectors_layer" not in st.session_state:
    st.session_state["sectors_layer"] = load_sectors_layer(os.path.join(PATH, "Datos", "Sectores.geojson"))
if "network_layer" not in st.session_state:
    st.session_state["network_layer"] = load_network_layer(os.path.join(PATH, "Datos", "Red Primaria.geojson"))


def query_map_pressures(date, hour, ids):
    if len(ids) == 0:
        ids = None
    db = dbs.DataBase()
    stations = db.get_stations()
    pressure = db.get_hourly_pressure(date, hour, ids)
    db.close()
    if len(pressure) == 0:
        return [], 0
    stations = stations.loc[:, ["ID", "Nombre", "X", "Y", "Diametro", "Carga", "Instalacion"]]
    stations.columns = ["ID", "Nombre", "X", "Y", "Diámetro (pulg)", "Carga de Posición (kg/cm2)", "Instalación"]
    stations["Fecha"] = pd.to_datetime(date).strftime("%Y-%m-%d")
    stations["Hora"] = hour
    stations["Presion (km/cm2)"] = pressure.round(3)
    stations = stations.dropna()    # preguntar si sustituir en lugar de eliminar
    flag = 1
    return stations, flag
    

def plot_pressure_map(data, basemap, show_sectors=False, sectors_color="#2c3e50",
                      show_network=False, network_color="#C1382E"):
    
    vmin = data["Presion (km/cm2)"].quantile(0.1)
    vmax = data["Presion (km/cm2)"].quantile(0.9)

    fig = px.scatter_mapbox(
        data,
        lat="Y",
        lon="X",
        color="Presion (km/cm2)",
        size="Presion (km/cm2)",
        hover_name="Nombre",
        hover_data=["ID", "Nombre", "Fecha", "Hora", "Presion (km/cm2)",
                    "Diámetro (pulg)", "Carga de Posición (kg/cm2)", "Instalación"],
        color_continuous_scale="icefire",
        mapbox_style=basemap,
        range_color=(vmin, vmax),
        center={"lat": 19.383, "lon": -99.147},
        size_max=15,
        opacity=0.9,
        zoom=9,
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


def plot_interp_pressure_map(data, basemap, show_sectors=False, sectors_color="#2c3e50",
                      show_network=False, network_color="#C1382E"):
    
    with open(os.path.join(PATH, "Datos", "Malla.geojson")) as fid:
        layer = json.load(fid)
    
    grid_table = pd.read_csv(os.path.join(PATH, "Datos", "MallaCoordenadas.csv"))
    grid_table.set_index("ID", drop=False, inplace=True)
    
    grid_table = intp.idw_interpolation(data, grid_table)
    grid_table = grid_table[["ID", "Presion (km/cm2)"]]

    vmin = data["Presion (km/cm2)"].quantile(0.1)
    vmax = data["Presion (km/cm2)"].quantile(0.9)
        
    fig = px.choropleth_mapbox(
            grid_table,
            geojson=layer,
            color="Presion (km/cm2)",
            locations="ID",
            featureidkey="properties.ID",
            hover_data=["ID", "Presion (km/cm2)"],
            range_color=(vmin, vmax),
            opacity=0.6,
            center={"lat": 19.383, "lon": -99.147},
            color_continuous_scale="icefire",
            mapbox_style=basemap,
            zoom=9
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


@st.cache
def download_data(data):
    return data.to_csv().encode('utf-8')


#%% Mapa de presiones

st.title("Mapa de Presiones de la Red de Agua Potable")
st.sidebar.title("Sistema de Presiones CDMX")
interp_map = st.sidebar.checkbox('Interpolar presión', key="press-map-interp")
selection3 = st.sidebar.multiselect("Buscar estaciones", st.session_state["ids"], key="press-map-select")
date3 = st.sidebar.date_input("Seleccionar fecha", value=date2, min_value=date1, max_value=date2, key="press-map-date")
hour3 = st.sidebar.slider("Seleccionar hora", 0, 23, hour2, key="press-map-hour")

st.sidebar.subheader("Opciones de visualización")
basemap3 = st.sidebar.selectbox(
    "Mapa base",
    ["carto-positron", "carto-darkmatter", "open-street-map", "white-bg", "stamen-toner"],
    index=0,
    key="press-map-basemap"
)
show_network3 = st.sidebar.checkbox("Mostrar red primaria", key="press-map-layer1")
show_sectors3 = st.sidebar.checkbox("Mostrar sectores", key="press-map-layer2")
network_color3 = st.sidebar.color_picker("Color de red primaria", "#C1382E", key="press-map-clayer1")
sectors_color3 = st.sidebar.color_picker("Color de sectores", "#2c3e50", key="press-map-clayer2")

table, flag = query_map_pressures(date3, hour3, selection3)
    
if flag == 0:
    st.error("¡No se han encontrado datos de presiones en ninguna estación para esa fecha!")

else:
    if interp_map:
        fig = plot_interp_pressure_map(table, basemap3, show_sectors3, sectors_color3,
                                       show_network3, network_color3)
    else:
        fig = plot_pressure_map(table, basemap3, show_sectors3, sectors_color3,
                                show_network3, network_color3)
    
    st.markdown(f"Presiones de la red el día **{date3} {hour3:02d}:00**")
    st.plotly_chart(fig, use_container_width=True)
    output = download_data(table)
    st.download_button(
        label="Descargar datos de presiones",
        data=output,
        file_name=f"Presiones_{date3}.csv",
        mime="text/csv",
    )
    
    with st.expander(f"Tabla de presiones horarias y estadisticos diarios para la fecha: {date3} {hour3:02d}:00"):
        st.dataframe(table, use_container_width=True)


