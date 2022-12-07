# -*- coding: utf-8 -*-
"""
Reporte por estacion

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

import data_bases as dbs


#%% Datos iniciales
db = dbs.DataBase()
dates = db.get_time_period()
date0 = dates["min"].to_pydatetime().date()
date1 = (dates["max"] - pd.Timedelta(60, "days")).to_pydatetime().date()
date2 = dates["max"].to_pydatetime().date()
db.close()

if "ids" not in st.session_state:
    db = dbs.DataBase()
    ids = db.get_stations_id()
    db.close()
    st.session_state["ids"] = ids


#%% Definir funciones

def temporal_serie(ide, date1, date2):
    db = dbs.DataBase()
    date1 = pd.to_datetime(date1) - pd.Timedelta(30, "minutes")
    date2 = pd.to_datetime(date2) + pd.Timedelta(30, "minutes") + pd.Timedelta(23, "hours")
    pressure = db.get_station_pressure(ide=ide, period=(date1, date2))
    station = db.get_station(ide)
    db.close()
    if len(pressure) == 0:
        name = ""
        stats = pd.DataFrame([])
    else:
        name = station["Nombre"]
        stats = pressure.groupby(pressure.index.hour).agg(["min", "mean", "max"])
        stats.columns = ["Presion Min", "Presion Promedio", "Presion Max"]
        stats.index.rename("Hora", inplace=True)
    return pressure, stats, name


def daily_pressure(ide, date):
    db = dbs.DataBase()
    pressure = db.get_pressure_by_day(date, ide)
    station = db.get_station(ide)
    db.close()
    if len(pressure) == 0:
        name = ""
        stats = pd.DataFrame([])
    else:
        name = station["Nombre"]
        stats = pressure.describe()
        stats.index = ["No. registros", "Promedio", "Std", "Min", "P25", "P50", "P75", "Max"]
    return pressure, stats, name


def hourly_pressure_by_month(ide, year, month):
    db = dbs.DataBase()
    pressure = db.get_hourly_pressure_by_month(year, month, ide)
    station = db.get_station(ide)
    db.close()
    name = station["Nombre"]
    if len(pressure) > 0:
        pressure.columns = ["Presion Min", "Presion Promedio", "Presion Max"]
    return pressure, name


def daily_pressure_by_month(ide, year, month):
    db = dbs.DataBase()
    pressure = db.get_daily_pressure_by_month(year, month, ide)
    station = db.get_station(ide)
    db.close()
    name = station["Nombre"]
    if len(pressure) > 0:
        pressure.columns = ["Presion Min", "Presion Promedio", "Presion Max"]
    return pressure, name


def monthly_pressure_by_year(ide, year):
    db = dbs.DataBase()
    pressure = db.get_monthly_pressure_by_year(year, ide)
    station = db.get_station(ide)
    db.close()
    name = station["Nombre"]
    if len(pressure) > 0:
        pressure.columns = ["Presion Min", "Presion Promedio", "Presion Max"]
    return pressure, name


@st.cache
def download_data(data):
    return data.to_csv().encode('utf-8')


#%% App

st.sidebar.title("Sistema de Presiones CDMX")
selection = st.sidebar.selectbox("Seleccionar estación", st.session_state["ids"])
plot_type = st.sidebar.selectbox(
    "Tipo de grafico",
    ["Serie temporal",
     "Serie horaria en un dia",
     "Estadisticos horarios por mes",
     "Estadisticos diarios por mes",
     "Estadisticos mensuales por año"])

st.title("Reporte de Presiones por Estación")

###############################################################################
if plot_type == "Serie temporal":
    sdate1 = st.sidebar.date_input(
        "Fecha inicial",
        value=date1,
        min_value=date0,
        max_value=date2
    )
    sdate2 = st.sidebar.date_input(
        "Fecha final",
        value=date2,
        min_value=date0,
        max_value=date2
    )
    
    pressure, stats, name = temporal_serie(selection, sdate1, sdate2)
    
    if len(pressure) == 0:
        st.error(f"No se encontraron registros de la estación **{selection}-{name}** para el periodo **{sdate1}** a **{sdate2}**")
    else:
        # plot
        data_plot = [
            go.Scatter(
                x=pressure.index,
                y=pressure,
                mode="lines",
                marker_color="rgba(31, 60, 144, 0.8)"
            )
        ]
        layout = go.Layout(yaxis={"title": "Presión horaria (kg/cm2)"})
        fig = go.Figure(data=data_plot, layout=layout)
        
        st.markdown(f"Presiones horarias en la estación **{selection}-{name}**: **{sdate1}** a **{sdate2}**")
        st.plotly_chart(fig, use_container_width=True)
        
        # downloads
        col1, col2 = st.columns(2)
        with col1:
            output1 = download_data(pressure.rename("Presion_kg-cm2"))
            st.download_button(
                label="Descargar serie",
                data=output1,
                file_name=f"Presiones_{selection}.csv",
                mime="text/csv",
            )
        with col2:
            output2 = download_data(stats)
            st.download_button(
                label="Descargar estadísticos",
                data=output2,
                file_name=f"EstadisticosPresiones_{selection}.csv",
                mime="text/csv",
            )
        
        with st.expander(f"Estadísticos horarios de presión para el periodo {sdate1} a {sdate2}"):
            st.dataframe(stats, use_container_width=True)
    
###############################################################################
elif plot_type == "Serie horaria en un dia":
    sdate = st.sidebar.date_input(
        "Seleccionar fecha",
        value=date2,
        min_value=date0,
        max_value=date2
    )
    
    pressure, stats, name = daily_pressure(selection, sdate)
    
    if len(pressure) == 0:
        st.error(f"No se encontraron registros de la estación **{selection}-{name}** para la fecha **{sdate}**")
    else:
        # plot
        data_plot = [
            go.Scatter(
                x=pressure.index,
                y=pressure,
                mode="lines",
                marker_color="rgba(31, 60, 144, 0.8)"
            )
        ]
        layout = go.Layout(yaxis={"title": "Presión horaria (kg/cm2)"})
        fig = go.Figure(data=data_plot, layout=layout)
        fig.update_xaxes(range=[0, 23])
        
        st.markdown(f"Presiones horarias en la estación **{selection}-{name}**: **{sdate}**")
        st.plotly_chart(fig, use_container_width=True)
        
        # downloads    
        col1, col2 = st.columns(2)
        with col1:
            output1 = download_data(pressure.rename("Presion_kg-cm2"))
            st.download_button(
                label="Descargar serie",
                data=output1,
                file_name=f"Presiones_{selection}_{sdate}.csv",
                mime="text/csv",
            )
        with col2:
            output2 = download_data(stats.rename("Presion_kg-cm2"))
            st.download_button(
                label="Descargar estadísticos",
                data=output2,
                file_name=f"EstadisticosPresiones_{selection}_{sdate}.csv",
                mime="text/csv",
            )
        
        with st.expander(f"Estadísticos horarios de presión para el día: {sdate}"):
            st.dataframe(stats.rename("Presion_kg-cm2"), use_container_width=True)

###############################################################################
if plot_type == "Estadisticos horarios por mes":
    year = st.sidebar.selectbox("Seleccionar año", list(range(date2.year, date0.year-1, -1)), 0)
    month = st.sidebar.selectbox("Seleccionar mes", list(range(1, 13)), date2.month-1)
    
    pressure, name = hourly_pressure_by_month(selection, year, month)
    
    if len(pressure) == 0:
        st.error(f"No se encontraron registros de la estación **{selection}-{name}** para el mes **{year}-{month}**")
    else:
        # plot
        data_plot = [
            go.Scatter(
                x=pressure.index,
                y=pressure["Presion Min"],
                mode="lines",
                marker_color="rgba(35, 125, 11, 0.8)",
                name="Minima"
            ),
            go.Scatter(
                x=pressure.index,
                y=pressure["Presion Promedio"],
                mode="lines",
                marker_color="rgba(31, 60, 144, 0.8)",
                name="Promedio"
            ),
            go.Scatter(
                x=pressure.index,
                y=pressure["Presion Max"],
                mode="lines",
                marker_color="rgba(178, 72, 55, 0.8)",
                name="Maxima"
            ),
        ]
        layout = go.Layout(yaxis={"title": "Presión horaria (kg/cm2)"})
        fig = go.Figure(data=data_plot, layout=layout)
        fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ))
        fig.update_xaxes(range=[0, 23])
        
        st.markdown(f"Presiones horarias en la estación **{selection}-{name}**: **{year}-{month}**")
        st.plotly_chart(fig, use_container_width=True)
        
        # downloads
        output = download_data(pressure)
        st.download_button(
            label="Descargar estadísticos",
            data=output,
            file_name=f"Presiones_{selection}_{year}-{month}.csv",
            mime="text/csv",
        )
        
        with st.expander(f"Estadísticos horarios de presión para el mes: {year}-{month}"):
            st.dataframe(pressure, use_container_width=True)

###############################################################################
if plot_type == "Estadisticos diarios por mes":
    year = st.sidebar.selectbox("Seleccionar año", list(range(date2.year, date0.year-1, -1)), 0)
    month = st.sidebar.selectbox("Seleccionar mes", list(range(1, 13)), date2.month-1)
    
    pressure, name = daily_pressure_by_month(selection, year, month)
    
    if len(pressure) == 0:
        st.error(f"No se encontraron registros de la estación **{selection}-{name}** para el mes **{year}-{month}**")
    else:
        # plot
        data_plot = [
            go.Scatter(
                x=pressure.index,
                y=pressure["Presion Min"],
                mode="lines",
                marker_color="rgba(35, 125, 11, 0.8)",
                name="Minima"
            ),
            go.Scatter(
                x=pressure.index,
                y=pressure["Presion Promedio"],
                mode="lines",
                marker_color="rgba(31, 60, 144, 0.8)",
                name="Promedio"
            ),
            go.Scatter(
                x=pressure.index,
                y=pressure["Presion Max"],
                mode="lines",
                marker_color="rgba(178, 72, 55, 0.8)",
                name="Maxima"
            ),
        ]
        layout = go.Layout(yaxis={"title": "Presión diaria (kg/cm2)"})
        fig = go.Figure(data=data_plot, layout=layout)
        fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ))
        
        st.markdown(f"Presiones diarias en la estación **{selection}-{name}**: **{year}-{month}**")
        st.plotly_chart(fig, use_container_width=True)
        
        # downloads
        output = download_data(pressure)
        st.download_button(
            label="Descargar estadísticos",
            data=output,
            file_name=f"Presiones_{selection}_{year}-{month}.csv",
            mime="text/csv",
        )
        
        with st.expander(f"Estadísticos diarios de presión para el mes: {year}-{month}"):
            st.dataframe(pressure, use_container_width=True)

###############################################################################
if plot_type == "Estadisticos mensuales por año":
    year = st.sidebar.selectbox("Seleccionar año", list(range(date2.year, date0.year-1, -1)), 0)
    
    pressure, name = monthly_pressure_by_year(selection, year)
    
    if len(pressure) == 0:
        st.error(f"No se encontraron registros de la estación **{selection}-{name}** para el año **{year}**")
    else:
        # plot
        data_plot = [
            go.Scatter(
                x=pressure.index,
                y=pressure["Presion Min"],
                mode="lines",
                marker_color="rgba(35, 125, 11, 0.8)",
                name="Minima"
            ),
            go.Scatter(
                x=pressure.index,
                y=pressure["Presion Promedio"],
                mode="lines",
                marker_color="rgba(31, 60, 144, 0.8)",
                name="Promedio"
            ),
            go.Scatter(
                x=pressure.index,
                y=pressure["Presion Max"],
                mode="lines",
                marker_color="rgba(178, 72, 55, 0.8)",
                name="Maxima"
            ),
        ]
        layout = go.Layout(yaxis={"title": "Presión mensual (kg/cm2)"})
        fig = go.Figure(data=data_plot, layout=layout)
        fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ))
        fig.update_xaxes(range=[1, 12])
        
        st.markdown(f"Presiones mensuales en la estación **{selection}-{name}**: **{year}**")
        st.plotly_chart(fig, use_container_width=True)
        
        # downloads
        output = download_data(pressure)
        st.download_button(
            label="Descargar estadísticos",
            data=output,
            file_name=f"Presiones_{selection}_{year}.csv",
            mime="text/csv",
        )
        
        with st.expander(f"Estadísticos mensuales de presión para el año: {year}"):
            st.dataframe(pressure, use_container_width=True)

