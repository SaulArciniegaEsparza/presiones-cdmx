# -*- coding: utf-8 -*-
"""
Gestion de las bases de datos

@author: zaula
"""

#%% Libraries
import os
import toml
import pandas as pd
import streamlit as st

import data_bases as dbs


path = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(os.path.dirname(path), "config.toml")) as fid:
    config = toml.load(fid)


#%% Funciones


@st.cache
def load_range_table():
    fname = os.path.join(os.path.dirname(path), "DatosIniciales", "RangosPresiones.csv")
    table = pd.read_csv(fname)
    return table

ranges_pressure = load_range_table()


@st.cache
def load_table(filename):
    table = pd.DataFrame([])
    if filename is not None:
        table = pd.read_csv(filename)
        success = True
        message = "Se ha leido correctamente el archivo"
    else:
        success = False
        message = "No se ha seleccionado ningún archivo!"
    return table, success, message


@st.cache
def download_data(data):
    return data.to_csv(index=False).encode('utf-8')


#%% App

st.title("Configuración de bases de datos")
st.write("Para actualizar la base de datos se recomienda descargar las plantillas de las estaciones y rango de presiones.")

db = dbs.DataBase()
stations = db.get_stations()
db.close()

col1, col2 = st.columns(2)
with col1:
    st.download_button(
        label="Descargar plantilla de estaciones",
        data=download_data(stations),
        file_name="Estaciones.csv",
        mime="csv",
    )
with col2:
    st.download_button(
        label="Descargar plantilla de rango de presiones",
        data=download_data(ranges_pressure),
        file_name="RangoPresiones.csv",
        mime="csv",
    )

st.subheader("Acceso de administrador")
password = st.text_input("Contraseña de administrador", value="", type="password", max_chars=10, key="adminpass")

if len(password) == 0:
    pass

elif password == config["admin"]["Clave"]:
        
    with st.expander("Actualizar tabla de estaciones"):
        fname = st.file_uploader(
            label="Ingresar tabla de estaciones en formato CSV",
            help="Descargar los datos de estaciones para usar como plantilla"
        )
        table, success, message = load_table(fname)
        if success:
            table = table.sort_values("ID")
            database = dbs.DataBase()
            flag, message = database.update_stations(table)
            database.close()
            st.session_state["ids"] = table["ID"].to_list()
            if flag:
                st.success("Se ha cargado la tabla con exito!")
            else:
                st.warning(message)
        else:
            st.warning(message)
            
    with st.expander("Agregar Rango de Presiones"):
        st.write("En proceso!")

else:
    st.error("¡Contraseña Incorrecta!")



