import requests
import pandas
from datetime import datetime
import socket
import sys
import json
import time
import paramiko
import scp
import os


"""
Algorithm working with the London schedule (from 9am to 6pm)
In order to ptimize its usage we will use a VPS from 9 to 6 so delete it at 6 and create another one at 8:45 with a 
bash code that'll be sent through SSH, server 'll be up at 9

"""

public_api_keys = "ZLMU7QWYIGPGWB3A"
markets = ["EURUSD", "EURGBP", "GBPUSD"]
frequency = "15min"
financial_array = pandas.DataFrame(dtype="float16", columns=[], index=markets)

port = 8080
authorization ={
    'Authorization' : 'Bearer 0b3b5c4386324917981668793e4425e12d2f4dd0863e808203bc8de7fe6c6caf',
}

COEFFSUM = 2
KEY_TO_USE = 0

# ssh key must already exist

key_id = requests.get("https://api.digitalocean.com/v2/account/keys", headers=authorization).json()["ssh_keys"][0]["id"]

host = "157.245.32.65"


def create_droplet_and_get_ip():
    """

    :return: ip_proxy, id of the new droplet
    """
    authorization["Content-type"] = "application/json"
    data_to_send = {
        'name': 'vm-droplet-proxy',
        'region': 'lon1',
        'size': 's-1vcpu-1gb',
        'image': 'ubuntu-16-04-x64',
        'ssh_keys': [key_id],
        'backups': False,
        'ipv6': False,
        'user_data': None,
        'private_networking': None,
        'volumes': None,
        'tags': list()
    }
    a = requests.post(url="https://api.digitalocean.com/v2/droplets", headers=authorization,
                      data = json.dumps(data_to_send))

    if a.status_code == 202:
        id_droplet = a.json()["droplet"]["id"]
        time.sleep(5)
        a = requests.get("https://api.digitalocean.com/v2/droplets/{}".format(id_droplet), headers=authorization)
        print(a.json())
        print(a.status_code)
        if a.status_code == 200:
            host = a.json()["droplet"]["networks"]["v4"][0]["ip_address"]
            return host, id_droplet


def initialize_proxy(dest):
    """

    :param dest: ip dest of the proxy server
    :return: void
    """
    current_path = '/'.join(os.path.dirname(os.path.realpath(__file__)).split("\\")[:-1]) + "/proxy/server_config.sh"
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(dest, username='root', key_filename="C://Users/matth/.ssh/id_rsa.pub")
        scp_transfer = scp.SCPClient(ssh.get_transport())
        scp_transfer.put(current_path, "~")
        _,stdout,_ = ssh.exec_command('pwd')
        print(stdout.readlines())
        ssh.close()
    except paramiko.ssh_exception.BadHostKeyException:
        print("Erreur lors de la connection SSH : {}".format(paramiko.ssh_exception))


def delete_droplet(id):
    """

    :param id: id concerned by the ongoing closure
    :return: void
    """
    print("Closing droplet id : {}".format(id))
    a = requests.delete(url = "https://api.digitalocean.com/v2/droplets/{}".format(id),
                        headers=authorization)
    if a.status_code == 204:
        print("Droplet deleted")
    else:
        print("Error droplet undeletable")




def reach_server(url_format):
    """

    :param url_format: url to reach through our proxy
    :return: json format of the response
    """
    global s
    try:
        s.send(bytes(url_format, "utf-8"))
        full_answer = str()
        while (True):
            resp = s.recv(4096)
            full_answer += resp.decode("utf-8")
            if "[END]" in resp.decode("utf-8"):
                break
        print(json.loads(full_answer.split("[END]")[0]))
        s.close()

    except socket.error:
        pass


def get_MACD(currency):
    """
    :return: MACD and all elements, moreover will return MACD and MACD(n-1) to determine it there was a 0 intersection
    """
    url = "https://www.alphavantage.co/query?function=MACD&symbol={}&interval={}&series_type=open&apikey={}"
    MACD = requests.get(url=url.format(currency, frequency, public_api_keys))
    if "Note" in MACD.content.json().keys():
        MACD = reach_server(url.format(currency, frequency, str()))

    time_n, time_n_1 = list(MACD.json()['Technical Analysis: MACD'])[0], list(MACD.json()['Technical Analysis: MACD'])[1]
    return MACD.json()['Technical Analysis: MACD'][time_n], MACD.json()['Technical Analysis: MACD'][time_n_1]




def get_STOCHRSI(currency):
    """

    :return: %K and %D (or delta between both) + info if overzone.
    Might wait two values to leave
    """
    STOCHRSI = requests.get("https://www.alphavantage.co/query?function=STOCHRSI&symbol={}&interval={}&time_period=10&series_type=close&fastkperiod=6&fastdmatype=1&apikey={}".
                            format(currency, frequency, public_api_keys))


    time_n, time_n_1 = list(STOCHRSI.json()['Technical Analysis: STOCHRSI'])[0], list(STOCHRSI.json()['Technical Analysis: STOCHRSI'])[1]
    return STOCHRSI.json()['Technical Analysis: STOCHRSI'][time_n], STOCHRSI.json()['Technical Analysis: STOCHRSI'][time_n_1]


def coeff_STOCHARSI_SAR(value_n_1, value_n, SAR_relatif):
    """
    SAR will change before the STOCHRSI
    :param SAR_relatif : if SAR_relatif positive then SAR>open price => short othw long
    :param value_n_1: {%K & %D at n-1}
    :param value_n: {%K and %D at n}
    :return: tuple with the needed increment of buy coeff and sell coeff
    """
    buy_coeff, sell_coeff = float(), float()
    quit_overzone=1.5
    FastD_n_1, FastK_n, FastK_n_1, FastD_n = \
        float(value_n_1['FastD']), float(value_n['FastK']),float(value_n_1['FastK']), float(value_n["FastD"])
    overbought_zone = FastK_n>=80 and FastK_n_1 >= 80
    oversold_zone = FastK_n<=20 and FastK_n_1 <=20
    if overbought_zone or oversold_zone:
        return 0,0
    if FastK_n > 20 and FastK_n_1 <= 20: return quit_overzone, sell_coeff
    elif FastK_n_1 >= 80 and FastK_n < 80: return buy_coeff, quit_overzone
    if FastD_n > 50 and FastK_n > 50 : buy_coeff += 0.25
    else: sell_coeff += 0.25
    if FastK_n_1<=FastD_n_1 and FastK_n>FastD_n and SAR_relatif < 0 : buy_coeff += 2
    elif FastK_n_1>= FastD_n_1 and FastK_n<FastD_n and SAR_relatif > 0: sell_coeff += 2
    return buy_coeff, sell_coeff

def get_SAR(currency):
    """

    :return: parabolic SAR value
    """

    SAR = requests.get("https://www.alphavantage.co/query?function=SAR&symbol={}&interval={}&acceleration=0.05&maximum=0.25&apikey={}".
                       format(currency, frequency, public_api_keys))
    time_studied = list(SAR.json()["Technical Analysis: SAR"])[0]
    return SAR.json()["Technical Analysis: SAR"][time_studied]


def get_MOMENTUM(currency):
    """

    :return: MOMENTUM value
    """

    MOM = requests.get("https://www.alphavantage.co/query?function=MOM&symbol={}&interval={}&time_period=10&series_type=close&apikey={}".
                   format(currency, frequency, public_api_keys[KEY_TO_USE]))
    time_n, time_n_1 = list(MOM.json()['Technical Analysis: MOM'])[0], list(MOM.json()['Technical Analysis: MOM'])[1]
    return MOM.json()['Technical Analysis: MOM'][time_n], MOM.json()['Technical Analysis: MOM'][time_n_1]



ip, droplet_id = create_droplet_and_get_ip()
initialize_proxy(ip)
time.sleep(10)
delete_droplet(droplet_id)

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip,port))
except socket.error:
    print('Error socket connection with {}'.format(ip))
    sys.exit(1)


if datetime.today().hour in range(0,24): # A coder par apport aux horaires de Londres
    buy_coeff, sell_coeff = float(),float()
    for i in range(len(markets)):
        financial_data = requests.get("https://financialmodellingprep.com/api/v3/forex/{}"
                                      .format(markets[i]))
        if financial_data.status_code == 200:
            open_price = financial_data.json()['open']
            financial_array.loc[markets[i], datetime.today().strftime("%d/%m/%y %H:%M")] = open_price
            SAR_relatif = float(get_SAR(markets[i])['SAR']) - float(open_price) #SAR relatif needs to be positive to indicate a long position (othw short)
            stoch_n, stoch_n_1 = get_STOCHRSI(markets[i])
            buy_coeff, sell_coeff = coeff_STOCHARSI_SAR(stoch_n_1, stoch_n, SAR_relatif)
            print(buy_coeff, sell_coeff)
            time.sleep(60) #wait a whole minute


            # Add rsistochastique condition




