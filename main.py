import requests
import pandas
from datetime import datetime
import threading
import time

"""
Algorithm working with the London schedule (from 9am to 6pm)
"""

public_api_keys = "ZLMU7QWYIGPGWB3A"
markets = ["EURUSD", "EURGBP", "GBPUSD"]
frequency = "15min"
financial_array = pandas.DataFrame(dtype="float16", columns=[], index=markets)


COEFFSUM = 2
KEY_TO_USE = 0

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


def coeff_STOCHARSI(value_n_1, value_n):
    """

    :param value_n_1: {%K & %D at n-1}
    :param value_n: {%K and %D at n}
    :return: tuple with the needed increment of buy coeff and sell coeff
    """


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



if datetime.today().hour in range(9,18): # A coder par apport aux horaires de Londres
    buy_coeff, sell_coeff = float(),float()
    for i in range(len(markets)):
        financial_data = requests.get("https://financialmodellingprep.com/api/v3/forex/GBPUSD"
                                      .format(markets[i]))
        if financial_data.status_code == 200:
            open_price = financial_data.json()['open']
            financial_array.loc[markets[i], datetime.today().strftime("%d/%m/%y %H:%M")] = open_price
            SAR_relatif = float(get_SAR(markets[i])['SAR']) - float(open_price) #SAR relatif needs to be positive to indicate a long position (othw short)

            #TO DO //
            # Add rsistochastique condition




