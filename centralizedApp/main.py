import requests
from datetime import datetime
import socket
import threading
import json
import time
import paramiko
import os


"""
Algorithm working with the London schedule (from 9am to 6pm)
In order to ptimize its usage we will use a VPS from 9 to 6 so delete it at 6 and create another one at 8:45 with a 
bash code that'll be sent through SSH, server 'll be up at 9

Private digital ocean key must be put as a environment variable under the name of DIGITAMOCEAN_KEY

"""

public_api_keys = "ZLMU7QWYIGPGWB3A"
adx_limit = 20
markets = ["EURUSD", "EURGBP", "GBPUSD", "USDJPY", "AUDUSD", "USDCHF"]
frequency = "15min"
digital_ocean_key = os.environ.get("DIGITALOCEAN_KEY")
port = 8080
necessary_value = 2
authorization ={
    'Authorization' : 'Bearer {}'.format(digital_ocean_key),
}
all_files = list()
files_lock = threading.Lock()

# ssh key must already exist

key_id = requests.get("https://api.digitalocean.com/v2/account/keys", headers=authorization).json()["ssh_keys"][0]["id"]


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
    github_repositoy = "https://github.com/matthrx/FinancialAlgo.git"
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(dest, username='root', key_filename="C://Users/matth/.ssh/id_rsa.pub")
        _,_,_ = ssh.exec_command("git clone {}".format(github_repositoy))
        _,_,_ = ssh.exec_command("sh FinancialAlgo/proxy/server_config.sh")
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
        s.close()
        return json.loads(full_answer.split("[END]")[0])

    except socket.error:
        pass


def api_over(message_content):
    return "Note" in message_content.json().keys()


def get_MACD(currency, is_range=False):
    """
    :return: MACD and all elements, moreover will return MACD and MACD(n-1) to determine it there was a 0 intersection
    """
    macd_coeff = 1 if is_range else 1.5
    url = "https://www.alphavantage.co/query?function=MACD&symbol={}&interval={}&series_type=open&apikey={}"
    MACD = requests.get(url=url.format(currency, frequency, public_api_keys))
    print(MACD.json())
    if api_over(MACD):
        MACD = reach_server(url.format(currency, frequency, str()))
        if api_over(MACD):
                time.sleep(15)
                return get_MACD(currency)

    time_n, time_n_1 = list(MACD.json()['Technical Analysis: MACD'])[0], list(MACD.json()['Technical Analysis: MACD'])[1]
    print(time_n)
    macd_n, macd_n_1 = float(MACD.json()['Technical Analysis: MACD'][time_n]['MACD_Hist']), \
                     float(MACD.json()['Technical Analysis: MACD'][time_n_1]['MACD_Hist'])
    print(macd_n, macd_n_1)
    print("Spotting")
    if macd_n > 0 and macd_n_1 <= 0: return (macd_coeff ,0)
    elif macd_n_1 <=0 and macd_n > 0: return (0, macd_coeff)
    elif macd_n > 0: return (0.25*macd_coeff,0)
    else: return (0,0.25*macd_coeff)


def is_range_ADX(currency):
    """

    :param currency: currency we'll study
    :return: ADX value to know whether the market is facing an important range or following a trend so far if <25 avoid trading
    keep position
    """
    url= "https://www.alphavantage.co/query?function=ADX&symbol={}&interval={}&time_period=14&apikey={}"
    ADX = requests.get(url=url.format(currency, frequency, public_api_keys))
    if api_over(ADX):
        ADX = reach_server(url.format(currency, frequency, str()))
        if api_over(ADX):
            time.sleep(15)
            return is_range_ADX(currency)

    print(ADX.json())
    time_n = list(ADX.json()['Technical Analysis: ADX'])[0]
    ADX_n = float(ADX.json()['Technical Analysis: ADX'][time_n]['ADX'])
    return float(ADX_n) <= adx_limit


def get_STOCH(currency, ):
    """

    :return: %K and %D (or delta between both) + info if overzone.
    Might wait two values to leave
    """
    url = "https://www.alphavantage.co/query?function=STOCH&symbol={}&interval={}&fastkperiod=14&fastdmatype=3&apikey={}"
    STOCHRSI = requests.get(url.format(currency, frequency, public_api_keys))
    if api_over(STOCHRSI):
        STOCHRSI = reach_server(url.format(currency, frequency, str()))
        if api_over(STOCHRSI):
            time.sleep(15)
            return get_STOCH(currency)

    time_n, time_n_1 = list(STOCHRSI.json()['Technical Analysis: STOCH'])[0], list(STOCHRSI.json()['Technical Analysis: STOCH'])[1]
    return STOCHRSI.json()['Technical Analysis: STOCH'][time_n], STOCHRSI.json()['Technical Analysis: STOCH'][time_n_1]



def coeff_STOCH_SAR(value_n_1, value_n, SAR_relatif, is_range=False):
    """
    SAR will change before the STOCHRSI
    :param SAR_relatif : if SAR_relatif positive then SAR>open price => short othw long
    :param value_n_1: {%K & %D at n-1}
    :param value_n: {%K and %D at n}
    :return: tuple with the needed increment of buy coeff and sell coeff
    """
    buy_coeff, sell_coeff = float(), float()
    quit_overzone=1.5
    if not is_range:
        FastD_n_1, FastK_n, FastK_n_1, FastD_n = \
            float(value_n_1['FastD']), float(value_n['FastK']),float(value_n_1['FastK']), float(value_n["FastD"])
        print("Etat du %K (stochastique) en n-1 et N : {},{}".format(FastK_n, FastK_n_1))
        overbought_zone = FastK_n>=80 and FastK_n_1 >= 80
        oversold_zone = FastK_n<=20 and FastK_n_1 <=20
        if overbought_zone or oversold_zone:
            return 0,0
        if FastK_n > 20 and FastK_n_1 <= 20: return quit_overzone, sell_coeff
        elif FastK_n_1 >= 80 and FastK_n < 80: return buy_coeff, quit_overzone
        if FastD_n > 50 and FastK_n > 50 : buy_coeff += 0.25
        else: sell_coeff += 0.25
        if FastK_n_1<=FastD_n_1 and FastK_n>FastD_n and SAR_relatif < 0 : buy_coeff += 2
        # may be add condition to declare a sell even though SAR isn't also negative to optimize
        elif FastK_n_1>= FastD_n_1 and FastK_n<FastD_n and SAR_relatif > 0: sell_coeff += 2
    return buy_coeff, sell_coeff



def get_SAR(currency):
    """

    :return: parabolic SAR value
    """
    url = "https://www.alphavantage.co/query?function=SAR&symbol={}&interval={}&acceleration=0.05&maximum=0.25&apikey={}"
    SAR = requests.get(url.format(currency, frequency, public_api_keys))
    if api_over(SAR):
        SAR = reach_server(url.format(currency, frequency, str()))
        if api_over(SAR):
            time.sleep(20)
            return get_SAR(currency)
    time_studied = list(SAR.json()["Technical Analysis: SAR"])[0]
    return SAR.json()["Technical Analysis: SAR"][time_studied]



def get_info_MOMENTUM(currency,  SAR_value,  is_range=False):
    """

    :return: MOMENTUM value
    """
    mom_value = 2 if is_range else 1
    buy_coeff, sell_coeff = float(), float()
    url = "https://www.alphavantage.co/query?function=MOM&symbol={}&interval={}&time_period=10&series_type=close&apikey={}"
    MOM = requests.get(url.format(currency, frequency, public_api_keys))
    if api_over(MOM):
        MOM = reach_server(url.format(currency, frequency, str()))
        if api_over(MOM):
            time.sleep(15)
            return get_info_MOMENTUM(currency, is_range, SAR_value)

    time_n, time_n_1 = list(MOM.json()['Technical Analysis: MOM'])[0], list(MOM.json()['Technical Analysis: MOM'])[1]
    mom_n, mom_n_1 = float(MOM.json()['Technical Analysis: MOM'][time_n]['MOM']), \
                         float(MOM.json()['Technical Analysis: MOM'][time_n_1]['MOM'])
    if not is_range:
        if mom_n >= 0 and mom_n_1 <=0: buy_coeff = mom_value
        elif mom_n <=0 and mom_n_1 >= 0: sell_coeff = mom_value
        elif mom_n > 0: buy_coeff = 0.25*mom_value
        else: sell_coeff = 0.25*mom_value
    else:
        if  mom_n > 0 and SAR_value < 0: buy_coeff = necessary_value
        elif mom_n < 0 and SAR_value > 0 : sell_coeff = necessary_value
    return  buy_coeff, sell_coeff


"""
Must be restructured
Functionning on a market every minute (to optimize api request) 
"""


# creation of threads
    # TO DO


def thread_postions(market, lock, on=True):
    """

    :param market:
    :param on:
    :return:
    """
    print("Launching thread")
    resume_file = open("{}\\result_files\\{}.txt".format(''.join(os.getcwd().split()[0:len(os.getcwd())-1]),
                                                    market), 'a+')
    with lock:
        all_files.append(resume_file)
    has_bought, has_sold = False, False
    price_entrance = float()
    while on:
        no_position = not has_bought and not has_sold

        financial_data = requests.get("https://financialmodellingprep.com/api/v3/forex/{}"
                                      .format(market))
        if financial_data.status_code == 200:
            current_price = financial_data.json()['bid']
            is_range = is_range_ADX(markets)
            SAR_relatif = float(get_SAR(market)['SAR']) - float(current_price) #SAR relatif needs to be positive to indicate a long position (othw short)
            stoch_n, stoch_n_1 = get_STOCH(market)
            buy_coeff, sell_coeff = tuple(map(lambda x,y,z : x+y+z, get_info_MOMENTUM(market, SAR_relatif, is_range),
                                              coeff_STOCH_SAR(stoch_n_1, stoch_n, SAR_relatif, is_range),
                                              get_MACD(market, is_range)))

            if no_position:
                if buy_coeff >= necessary_value:
                    has_bought = True
                    resume_file.write("++ Position taken at {} ".format(datetime.today().strftime("%d/%m/%y %H:%M")))
                    price_entrance = current_price
                elif sell_coeff >= necessary_value:
                    has_sold = True
                    resume_file.write("-- Position taken at: {} ".format(datetime.today().strftime("%d/%m/%y %H:%M")))
                    price_entrance = current_price

            else:
                if has_bought:
                    if sell_coeff >= necessary_value:
                        has_bought = False
                        resume_file.write("---- left at {} ---> result {}% \n".format(
                            datetime.today().strftime("%d/%m/%y %H:%M"),
                            (current_price - price_entrance)/price_entrance))
                elif has_sold:
                    if buy_coeff >= necessary_value:
                        has_sold = False
                        resume_file.write("---- left at {} ---> result {}% \n".format(
                            datetime.today().strftime("%d/%m/%y %H:%M"),
                            (price_entrance - current_price) / price_entrance))

            time.sleep(15*60) #wait 15 minutes


def end_market(droplet_id):
    """
    close all files + remove droplet
    :return: nothing
    """
    for f in all_files: f.close()
    delete_droplet(droplet_id)



while True:
    while True:
        if datetime.today().hour >= 9:
            ip, droplet_id = create_droplet_and_get_ip()
            print(ip)
            time.sleep(60)
            initialize_proxy(ip)

            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((ip,port))
            except socket.error:
                print('Error socket connection with {}'.format(ip))
                os.error(1)

            on = True
            all_threads = [threading.Thread(target=thread_postions, args=(markets[i], files_lock, on)) for i in range(len(markets))]
            for i in range(0,len(markets)-3,2):
                all_threads[i].start()
                all_threads[i+1].start()
                time.sleep(70)

            break
        else:
            time.sleep(25*60)
    print("Currently working...")
    while datetime.today().hour < 17:
        time.sleep(25*60)
    on = False
    for t in all_threads: t.join()
    end_market(droplet_id)
    print('End of the day at : {}'.format(datetime.today().strftime("%d/%m/%y %H:%M")))





