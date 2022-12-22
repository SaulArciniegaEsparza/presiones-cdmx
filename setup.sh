#!/bin/bash
sudo apt-get update
sudo apt-get install python3-virtualenv
python3 -m virtualenv -q -p /usr/bin/python3 venv
source ./venv/bin/activate
./venv/bin/pip install -r requirements.txt
./venv/bin/streamlit run 1_Inicio.py
