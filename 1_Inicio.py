# -*- coding: utf-8 -*-
"""

@author: zaula
"""

#%% Libraries
import os
import json
import streamlit as st
from PIL import Image
import data_bases as dbs

path = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(page_title="Presiones-CDMX", layout="wide")

#%% Datos iniciales
db = dbs.DataBase()
ids = db.get_stations_id()
db.close()

db = dbs.DataBase()
db.close()

st.session_state["ids"] = ids


@st.cache_data(persist="disk")
def load_sectors_layer(filename):
    with open(filename, encoding="utf-8") as fid:
        layer = json.load(fid)
    return layer

st.session_state["sectors_layer"] = load_sectors_layer(os.path.join(path, "Datos", "Sectores.geojson"))


@st.cache_data(persist="disk")
def load_network_layer(filename):
    with open(filename, encoding="utf-8") as fid:
        layer = json.load(fid)
    return layer

st.session_state["network_layer"] = load_network_layer(os.path.join(path, "Datos", "Red Primaria.geojson"))


#%% App

st.title("Sistema de Monitoreo de Presiones de la Red de Agua Potable de la Ciudad de México")

st.sidebar.title("Sistema de Presiones CDMX")

st.markdown("""Plataforma para la visualización y análisis del sistema de presiones de
la red de agua potable de la Ciudad de México.
            
Desarrollado para el Sistema de Aguas de la Ciudad de México ([**SACMEX**](https://www.sacmex.cdmx.gob.mx/))
por **Idinfra S.A. de C.V.**
""")

st.image(Image.open(os.path.join(path, "img", "sacmex.png")), width=150)

