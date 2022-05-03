# -*- coding: utf-8 -*-
import base64
import datetime
import json
import warnings
from os import listdir
from threading import Thread
import requests
import config as cfg

DIR = cfg.DIR
DAYS = [
    str(a) + str(b) if a > 10 and b > 10 \
    else '0' + str(a) + str(b) if a < 10 and b > 9 \
    else str(a) + '0' + str(b) if a > 9 and b < 10 \
    else '0' + str(a) + '0' + str(b) if a < 10 and b <10 \
    else str(a) + str(b)
    for a in range(1, 13) for b in range(1, 32)
]

warnings.filterwarnings("ignore")


def main():
    for year in range(2012, 2022):
        for dir_day in DAYS:
            try:
                for file in listdir(cfg.FILES_LOCATION + str(year) + '/' + dir_day):
                    with open(cfg.FILES_LOCATION + str(year) + '/' + dir_day + '/' + file, "rb") as f:
                        encoded_string = base64.b64encode(f.read())
                        if encoded_string[0:4] == b'MIIU':
                            response = requests.post(
                                f'https://109.233.109.78/api/full-info/',
                                verify=False,
                                data=json.dumps({"sign": encoded_string.decode()}),
                                headers={
                                    "Content-Type": "application/json",
                                    "Accept-Encoding": "gzip, deflate, br"
                                }
                            )
                            print(response.text)
            except FileNotFoundError:
                pass


if __name__ == '__main__':
    main()