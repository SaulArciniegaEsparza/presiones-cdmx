#!/bin/bash
git clone https://github.com/SaulArciniegaEsparza/presiones-cdmx.git
cd presiones-cdmx
sudo apt-get install python3-virtualenv
virtualenv -q -p /usr/bin/python3 venv
source ./venv/bin/activate
./venv/bin/pip install -r requirements.txt
./venv/bin/streamlit run 1_Inicio.py
