import requests
import datetime
import socket
import threading
import json
import time
import paramiko
import os
from centralizedApp.api.models import Position
from centralizedApp.api.config import db
import time

"""
Algorithm working with the London schedule (from 9am to 6pm)
In order to ptimize its usage we will use a VPS from 9 to 6 so delete it at 6 and create another one at 8:45 with a 
bash code that'll be sent through SSH, server 'll be up at 9

Private digital ocean key must be put as a environment variable under the name of DIGITAMOCEAN_KEY
 TO DO //Implement SMS API to receive information at the end of the day.
"""


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
        return json.loads(full_answer.split("[END]")[0])

    except socket.error:
        pass


def api_over(message_content):
    return "Note" in message_content.keys()


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
        _, stdout, _ = ssh.exec_command("git clone {}".format(github_repositoy))
        clone_status = stdout.channel.recv_exit_status()
        if clone_status == 0:
            _, _, _ = ssh.exec_command("sh FinancialAlgo/proxy/server_config.sh")
        else:
            print("Clone impossible")
            os.error()
        ssh.close()
    except paramiko.ssh_exception.BadHostKeyException:
        print("Erreur lors de la connection SSH : {}".format(paramiko.ssh_exception))



def coeff_STOCH_SAR(value_n_1, value_n, SAR_relatif, is_range=False):
    """
    SAR will change before the STOCHRSI
    :param SAR_relatif : if SAR_relatif positive then SAR>open price => short othw long
    :param value_n_1: {%K & %D at n-1}
    :param value_n: {%K and %D at n}
    :return: tuple with the needed increment of buy coeff and sell coeff
    """
    buy_coeff, sell_coeff = float(), float()
    quit_overzone=3
    if not is_range:
        SlowD_n_1, SlowK_n, SlowK_n_1, SlowD_n = \
            float(value_n_1['SlowD']), float(value_n['SlowK']),float(value_n_1['SlowK']), float(value_n["SlowD"])
        overbought_zone = SlowK_n>=80 and SlowK_n_1 >= 80
        oversold_zone = SlowK_n<=20 and SlowK_n_1 <=20
        if overbought_zone or oversold_zone:
            return 0,0
        if SlowK_n > 20 and SlowK_n_1 <= 20: return quit_overzone, sell_coeff
        elif SlowK_n_1 >= 80 and SlowK_n < 80: return buy_coeff, quit_overzone
        if SlowD_n > 50 and SlowK_n > 50 : buy_coeff += 0.25
        else: sell_coeff += 0.25
        if SlowK_n>SlowD_n and SAR_relatif < 0 : buy_coeff += 3        # may be add condition to declare a sell even though SAR isn't also negative to optimize
        elif SlowK_n<SlowD_n and SAR_relatif > 0: sell_coeff += 3
    return buy_coeff, sell_coeff



class FinancialAlgothimBackend:

    def __init__(self):
        self.public_api_keys = "ZLMU7QWYIGPGWB3A"
        self.adx_limit = 20
        self.markets = ["EURUSD", "EURGBP", "GBPUSD", "USDJPY", "AUDUSD", "USDCHF"]
        self.frequency = "15min"
        self.digital_ocean_key = os.environ.get("DIGITALOCEAN_KEY")
        self.port = 8080
        self.necessary_value = 3
        self.authorization ={
            'Authorization' : 'Bearer {}'.format(self.digital_ocean_key),
        }
        self.all_files = list()
        self.files_lock = threading.Lock()
        self.socket_lock = threading.Lock()

        # ssh key must already exist

        self.key_id = requests.get("https://api.digitalocean.com/v2/account/keys", headers=
        self.authorization).json()["ssh_keys"][0]["id"]
        self.running_threads = True
        self.id_api = int()
        self.mutex_api = threading.Lock()


    def create_droplet_and_get_ip(self):
        """

        :return: ip_proxy, id of the new droplet
        """
        self.authorization["Content-type"] = "application/json"
        data_to_send = {
            'name': 'vm-droplet-proxy',
            'region': 'lon1',
            'size': 's-1vcpu-1gb',
            'image': 'ubuntu-16-04-x64',
            'ssh_keys': [self.key_id],
            'backups': False,
            'ipv6': False,
            'user_data': None,
            'private_networking': None,
            'volumes': None,
            'tags': list()
        }
        a = requests.post(url="https://api.digitalocean.com/v2/droplets", headers=self.authorization,
                          data = json.dumps(data_to_send))

        if a.status_code == 202:
            id_droplet = a.json()["droplet"]["id"]
            while True:
                a = requests.get("https://api.digitalocean.com/v2/droplets/{}".format(id_droplet), headers=self.authorization)
                if a.status_code == 200:
                    try:
                        host = a.json()["droplet"]["networks"]["v4"][0]["ip_address"]
                        return host, id_droplet
                    except IndexError:
                        pass
                time.sleep(20)


    def delete_droplet(self, id):
        """

        :param id: id concerned by the ongoing closure
        :return: void
        """
        print("Closing droplet id : {}".format(id))
        a = requests.delete(url="https://api.digitalocean.com/v2/droplets/{}".format(id),
                            headers=self.authorization)
        if a.status_code == 204:
            print("Droplet deleted")
        else:
            print("Error droplet undeletable")


    def get_MACD(self, currency, is_range=False):
        """
        :return: MACD and all elements, moreover will return MACD and MACD(n-1) to determine it there was a 0 intersection
        """
        macd_coeff = 2 if is_range else 1
        url = "https://www.alphavantage.co/query?function=MACD&symbol={}&interval={}&series_type=open&apikey={}"
        MACD = requests.get(url=url.format(currency, self.frequency, self.public_api_keys)).json()
        if api_over(MACD):
            MACD = reach_server(url.format(currency, self.frequency, str()))
            if api_over(MACD):
                    time.sleep(15)
                    return self.get_MACD(currency)

        time_n, time_n_1 = list(MACD['Technical Analysis: MACD'])[0], list(MACD['Technical Analysis: MACD'])[1]
        macd_n, macd_n_1 = float(MACD['Technical Analysis: MACD'][time_n]['MACD_Hist']), \
                         float(MACD['Technical Analysis: MACD'][time_n_1]['MACD_Hist'])
        if macd_n > 0: return (macd_coeff ,0)
        elif macd_n < 0: return (0, macd_coeff)
        else: return (0,0)


    def is_range_ADX(self, currency):
        """

        :param currency: currency we'll study
        :return: ADX value to know whether the market is facing an important range or following a trend so far if <25 avoid trading
        keep position
        """
        url= "https://www.alphavantage.co/query?function=ADX&symbol={}&interval={}&time_period=14&apikey={}"
        ADX = requests.get(url=url.format(currency, self.frequency, self.public_api_keys)).json()
        if api_over(ADX):
            ADX = reach_server(url.format(currency, self.frequency, str()))
            if api_over(ADX):
                time.sleep(15)
                return self.is_range_ADX(currency)

        time_n = list(ADX['Technical Analysis: ADX'])[0]
        ADX_n = float(ADX['Technical Analysis: ADX'][time_n]['ADX'])
        return ADX_n <= self.adx_limit


    def get_STOCH(self, currency):
        """

        :return: %K and %D (or delta between both) + info if overzone.
        Might wait two values to leave
        """
        url = "https://www.alphavantage.co/query?function=STOCH&symbol={}&interval={}&Slowkperiod=14&Slowdmatype=3&apikey={}"
        STOCHRSI = requests.get(url.format(currency, self.frequency, self.public_api_keys)).json()
        if api_over(STOCHRSI):
            STOCHRSI = reach_server(url.format(currency, self.frequency, str()))
            if api_over(STOCHRSI):
                time.sleep(15)
                return self.get_STOCH(currency)
        time_n, time_n_1 = list(STOCHRSI['Technical Analysis: STOCH'])[0], list(STOCHRSI['Technical Analysis: STOCH'])[1]
        return STOCHRSI['Technical Analysis: STOCH'][time_n], STOCHRSI['Technical Analysis: STOCH'][time_n_1]


    def get_SAR(self, currency):
        """

        :return: parabolic SAR value
        """
        url = "https://www.alphavantage.co/query?function=SAR&symbol={}&interval={}&acceleration=0.05&maximum=0.25&apikey={}"
        SAR = requests.get(url.format(currency, self.frequency, self.public_api_keys)).json()
        if api_over(SAR):
            SAR = reach_server(url.format(currency, self.frequency, str()))
            if api_over(SAR):
                time.sleep(20)
                return self.get_SAR(currency)
        time_studied = list(SAR["Technical Analysis: SAR"])[0]
        return SAR["Technical Analysis: SAR"][time_studied]



    def get_info_MOMENTUM(self, currency,  SAR_value,  is_range=False):
        """

        :return: MOMENTUM value
        """
        mom_value = 2 if is_range else 1
        buy_coeff, sell_coeff = float(), float()
        url = "https://www.alphavantage.co/query?function=MOM&symbol={}&interval={}&time_period=10&series_type=close&apikey={}"
        MOM = requests.get(url.format(currency, self.frequency, self.public_api_keys)).json()
        if api_over(MOM):
            MOM = reach_server(url.format(currency, self.frequency, str()))
            if api_over(MOM):
                time.sleep(15)
                return self.get_info_MOMENTUM(currency, is_range, SAR_value)

        time_n, time_n_1 = list(MOM['Technical Analysis: MOM'])[0], list(MOM['Technical Analysis: MOM'])[1]
        mom_n, mom_n_1 = float(MOM['Technical Analysis: MOM'][time_n]['MOM']), \
                             float(MOM['Technical Analysis: MOM'][time_n_1]['MOM'])
        if not is_range:
            if mom_n >= 0 : buy_coeff = mom_value
            elif mom_n <0: sell_coeff = mom_value

        else:
            if  mom_n > 0 and SAR_value < 0: buy_coeff = self.necessary_value
            elif mom_n < 0 and SAR_value > 0 : sell_coeff = self.necessary_value
        return  buy_coeff, sell_coeff


    """
    Must be restructured
    Functionning on a market every minute (to optimize api request) 
    """


    # creation of threads
        # TO DO


    def thread_postions(self, market, socket_lock):
        """

        :param market:
        :param on:
        :return:
        """
        print("Launching thread")
        a = os.getcwd().split("\\")
        has_bought, has_sold = False, False
        price_entrance = float()
        while self.running_threads:
            no_position = not(has_bought^has_sold)

            financial_data = requests.get("https://financialmodellingprep.com/api/v3/forex/{}"
                                          .format(market))
            if financial_data.status_code == 200:
                current_price = float(financial_data.json()['bid'])
                socket_lock.acquire()
                is_range = self.is_range_ADX(market)
                SAR_relatif = float(self.get_SAR(market)['SAR']) - float(current_price) #SAR relatif needs to be positive to indicate a long position (othw short)
                stoch_n, stoch_n_1 = self.get_STOCH(market)
                buy_coeff, sell_coeff = tuple(map(lambda x,y,z : x+y+z, self.get_info_MOMENTUM(market, SAR_relatif, is_range),
                                                  coeff_STOCH_SAR(stoch_n_1, stoch_n, SAR_relatif, is_range),
                                                  self.get_MACD(market, is_range)))
                socket_lock.release()
                resume_file = open("{}\\result_files\\{}.txt".format('\\'.join(a[0:len(a) - 1]),
                                                                    market), 'a+')
                if not no_position:
                    if has_bought:
                        if buy_coeff <= self.necessary_value / 2:
                            position_to_leave = Position.query.filter(market==market).last()
                            date = datetime.datetime.now()

                            position_to_leave.dayout_market = datetime.date.today()
                            position_to_leave.timeout_market = datetime.time(hour=date.hour, minute=date.minute,
                                                                                second=date.second)
                            position_to_leave.result_percent = 100*(current_price - price_entrance)/price_entrance
                            db.session.commit()
                            print("Buy left by {}".format(market))
                            has_bought = False
                            resume_file.write("---- left at {} ---> result {}% \n".format(
                                datetime.datetime.today().strftime("%d/%m/%y %H:%M"),
                                100 * (current_price - price_entrance) / price_entrance))
                    elif has_sold:
                        position_to_leave = Position.query.filter(market==market).last()
                        date = datetime.datetime.now()
                        position_to_leave.dayout_market = datetime.date.today()
                        position_to_leave.timeout_market = datetime.time(hour=date.hour, minute=date.minute,
                                                                            second=date.second)
                        position_to_leave.result_percent = -100 *(current_price - price_entrance)/ price_entrance
                        db.session.commit()
                        if sell_coeff <= self.necessary_value / 2:
                            print("Sold left by {}".format(market))
                            has_sold = False
                            resume_file.write("---- left at {} ---> result {}% \n".format(
                                datetime.datetime.today().strftime("%d/%m/%y %H:%M"),
                                100 * (price_entrance - current_price) / price_entrance))
                else:
                    if buy_coeff >= self.necessary_value:
                        position = Position(
                            position_type="B",
                            market=market,
                            stepin_market= datetime.datetime.today(),
                            stepin_value=current_price,
                        )
                        db.session.add(position)
                        db.session.commit()
                        has_bought = True
                        resume_file.write("++ Position taken at {} ".format(datetime.datetime.today().strftime("%d/%m/%y %H:%M")))
                        price_entrance = current_price
                    # might need an id as a global value with a mutex (same thing for the interaction with the db_session)
                    elif sell_coeff >= self.necessary_value:

                        position = Position(
                            position_type="S",
                            market=market,
                            stepin_market=datetime.datetime.today(),
                            stepin_value=current_price,
                        )
                        db.session.add(position)
                        db.session.commit()
                        print("Sell taken by {}".format(market))
                        has_sold = True
                        resume_file.write("-- Position taken at: {} ".format(datetime.datetime.today().strftime("%d/%m/%y %H:%M")))
                        price_entrance = current_price

                resume_file.close()
                time.sleep(15*60) #wait 15 minutes
            else:
                print("Erreur")
                os.close(-1)
        print("Fermeture du marché")

    def end_market(self, droplet_id):
        """
        remove droplet
        :return: nothing
        """
        self.delete_droplet(droplet_id)
        s.close()


    def run(self):
        while True:
            while True:
                date = datetime.datetime.now()
                if date.hour >= 0 and date.hour < 17 :
                    print("London opens...")
                    ip, droplet_id = self.create_droplet_and_get_ip()
                    time.sleep(60)
                    initialize_proxy(ip)
                    while True:
                        time.sleep(15)
                        try:
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            s.connect((ip,self.port))
                            print("Connection created properly")
                            break
                        except socket.error:
                            pass
                    all_threads = [threading.Thread(target=self.thread_postions, args=(self.markets[i]
                                                                                  , self.socket_lock,
                                                                                  )) for i in range(len(self.markets))]
                    launch_start = False
                    while not launch_start:
                        if datetime.datetime.now().second not in [i for i in range(10)]:
                            time.sleep(1)
                        else:
                            launch_start = True
                    for i in range(0,len(self.markets),2):
                        print("Threads about to be launched")
                        all_threads[i].start()
                        all_threads[i+1].start()
                        time.sleep(65)

                    break
                else:
                    print("Waiting for the market to open")
                    time.sleep(2*60)
            delta_t = datetime.time(17-date.hour, 59-date.minute, 59-date.second)
            to_wait = (datetime.datetime.combine(datetime.date.min, delta_t) - datetime.datetime.min).total_seconds()
            print(to_wait)
            time.sleep(to_wait)
            self.running_threads = False
            for t in all_threads: t.join()
            self.end_market(droplet_id)
            print('End of the day at : {}'.format(datetime.datetime.today().strftime("%d/%m/%y %H:%M")))





