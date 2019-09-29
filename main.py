import requests
import pandas
from datetime import datetime
import socket
import sys
import json


"""
Algorithm working with the London schedule (from 9am to 6pm)
"""

public_api_keys = "ZLMU7QWYIGPGWB3A"
markets = ["EURUSD", "EURGBP", "GBPUSD"]
frequency = "15min"
financial_array = pandas.DataFrame(dtype="float16", columns=[], index=markets)

host = "127.0.0.1"
port = 8081

COEFFSUM = 2
KEY_TO_USE = 0

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host,port))
except socket.error:
    print("It seems connection was refused ...")
    sys.exit(1)


def reach_server(url_format):
    """

    :param url_format: url to reach through our proxy
    :return: json format of the response
    """
    global s
    try:
        s.send(bytes(url_format, "utf-8"))
        full_answer = str()
        print("Received an answer from the server")
        resp = s.recv(4096)
        while (True):
            full_answer += resp.decode("utf-8")
            if len(resp.decode("utf-8")) != 4096 or resp.decode("utf-8") == str():
                break
            resp = s.recv(4096)
        print(json.loads(full_answer))
        s.close()

    except socket.error:
        print("Server cannot answer...")
        sys.exit(1)



def get_MACD(currency):
    """
    :return: MACD and all elements, moreover will return MACD and MACD(n-1) to determine it there was a 0 intersection
    """
    MACD = requests.get("https://www.alphavantage.co/query?function=MACD&symbol={}&interval={}&series_type=open&apikey={}".
                    format(currency, frequency, public_api_keys))
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



if datetime.today().hour in range(0,24): # A coder par apport aux horaires de Londres
    buy_coeff, sell_coeff = float(),float()
    for i in range(len(markets)):
        financial_data = requests.get("https://financialmodellingprep.com/api/v3/forex/{}"
                                      .format(markets[i]))
        if financial_data.status_code == 200:
            open_price = financial_data.json()['open']
            financial_array.loc[markets[i], datetime.today().strftime("%d/%m/%y %H:%M")] = open_price
            SAR_relatif = float(get_SAR(markets[i])['SAR']) - float(open_price) #SAR relatif needs to be positive to indicate a long position (othw short)
            # stoch_n, stoch_n_1 = get_STOCHRSI(markets[i])
            # buy_coeff, sell_coeff = coeff_STOCHARSI_SAR(stoch_n_1, stoch_n, SAR_relatif)
            print(buy_coeff, sell_coeff)
            a = reach_server("https://www.alphavantage.co/query?function=MOM&symbol=EURGBP&interval=15min&time_period=10&series_type=close&apikey=")

            # Add rsistochastique condition




