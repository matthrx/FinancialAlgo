apt update
apt install -y python3-pip build-essential libssl-dev libffi-dev python3-dev
pip3 install requests
git clone https://github.com/matthrx/FinancialAlgo.git
python3 ~/FinancialAlgo/proxy/proxy.py
