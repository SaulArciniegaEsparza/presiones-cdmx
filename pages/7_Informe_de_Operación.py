

#%% Libraries
import os
import json
import datetime
import numpy as np
import pandas as pd
from calendar import monthrange
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


def operational_hourly_pressure(year, month):
    
    days = monthrange(year, month)[1]
    db = dbs.DataBase()
    ids = db.get_stations_id()
    stations = db.get_stations()
    pressure = []
    for ide in ids:
        p = db.get_station_pressure(ide=ide, year=year, month=month)
        p.index = pd.to_datetime(p.index)
        p = p.resample("1H").mean()
        pressure.append(p)
    db.close()
    
    pressure_frame = pd.concat(pressure, axis=1)
    pressure_frame.columns = ids
    
    ids = []  # ids comunes
    for i in stations["ID"]:
        if i in pressure_frame.columns:
            ids.append(i)
    stations = stations.loc[ids, :]    
    pressure_frame = pressure_frame.loc[:, ids]
    
    return pressure_frame.dropna(axis=1, how="all")


@st.cache_data
def download_data(data):
    return data.to_csv().encode('utf-8')


#%% Operacion de estaciones

st.title("Reporte de operación de estaciones")
st.sidebar.title("Sistema de Presiones CDMX")
year = st.sidebar.selectbox("Seleccionar año", list(range(date2.year, date1.year-1, -1)), 0)
month = st.sidebar.selectbox("Seleccionar mes", list(range(1, 13)), date2.month-1)

if (pd.to_datetime(f"{year}-{month:02d}-01") > pd.to_datetime(f"{date2.year}-{date2.month:02d}-01") or 
    pd.to_datetime(f"{year}-{month:02d}-01") < pd.to_datetime(f"{date1.year}-{date1.month:02d}-01")):
    st.error(f"No se encontraron registros para el mes seleccionado")
else:
    with st.spinner("Generando reporte"):
        ranges_table = pd.read_csv(os.path.join(PATH, "DatosIniciales", "RangosPresiones_variables.csv"))

        press = operational_hourly_pressure(year, month)

        if len(press) == 0:
            st.error(f"No se encontraron registros para el mes **{year}-{month:02d}**")
        else:
            operation_dict, operation_stats_dict, operation_daily = poperation.pressure_ranges_operation(year, month, press, ranges_table)

            st.markdown(f"**Operación de la red el mes {year}-{month:02d}**",
                        help="""Para verificar la operación de las estaciones se utilizaron los rangos **Variables** corresponden
                        a los rangos normales de operación según el día y el horario, con base en el análisis de la información de 2021.""")
            st.markdown("Número de estaciones que presentaron subpresión o sobrepresión en algún momento de su funcionamiento en el mes.")
            cols = st.columns(len(operation_stats_dict))
            for i, key in enumerate(operation_stats_dict.keys()):
                cols[i].metric(key, operation_stats_dict[key])
            
            operation_titles = list(operation_dict.keys())
            tabs = st.tabs(operation_titles)
            for i, tab in enumerate(tabs):
                with tab:
                    st.header(operation_titles[i])

                    fig = px.imshow(
                        operation_dict[operation_titles[i]],
                        labels=dict(x="Día del mes", y="Hora del día", color="No. Estacion"),
                        color_continuous_scale="viridis",
                        text_auto=True,
                        aspect="auto",
                        zmin=0,
                        zmax=int(press.shape[1]/2)
                    )
                    st.markdown("No. de estaciones que presentan problemas en su operación para cada hora y día del mes")
                    st.plotly_chart(fig, use_container_width=True, theme=None)
                    
                    output1 = download_data(operation_dict[operation_titles[i]])
                    st.download_button(
                        label="Descargar datos",
                        data=output1,
                        file_name=f"Operacion por hora_{operation_titles[i]}_{year}-{month}.csv",
                        mime="text/csv",
                    )

                    fig1 = px.imshow(
                        operation_daily[operation_titles[i]],
                        labels=dict(x="Estación", y="Día del mes", color="No. horas"),
                        color_continuous_scale="viridis",
                        text_auto=True,
                        aspect="auto",
                        zmin=0,
                        zmax=24
                    )
                    st.markdown("No. de horas con problemas en la operación por día por estación")
                    st.plotly_chart(fig1, use_container_width=True, theme=None)

                    output2 = download_data(operation_daily[operation_titles[i]])
                    st.download_button(
                        label="Descargar datos",
                        data=output2,
                        file_name=f"Operacion por dia_{operation_titles[i]}_{year}-{month}.csv",
                        mime="text/csv",
                    )


