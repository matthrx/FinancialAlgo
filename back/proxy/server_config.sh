#!/usr/bin/env bash
apt update
apt -y install python3-pip build-essential libssl-dev libffi-dev python3-dev
pip3 install requests
python3 ~/FinancialAlgo/proxy/proxy.py
