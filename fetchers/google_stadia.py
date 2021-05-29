import logging
from typing import List
from utils.clean_string import clean_string

import coloredlogs
import requests

logger = logging.getLogger("Stadia")
coloredlogs.install(level='INFO', logger=logger,
                    fmt='%(name)s %(asctime)s %(levelname)s %(message)s')


class StadiaGame:
    def __init__(self, name: str, pro_discount: bool):
        self.name = name
        self.pro_discount = pro_discount


def fetch_stadia() -> List[StadiaGame]:

    # from https://stadia.google.com/games page
    stadia_url = "https://ssl.gstatic.com/stadia/gamers/landing_page/config/landing_page_us.json"

    r = requests.get(stadia_url)
    if(r.status_code != 200):
        raise Exception("XCloud fetch data failed")

    data = r.json()

    if "stadia_game_list" not in data \
            or "stadia_pro_game_list" not in data\
            or not isinstance(data["stadia_game_list"], list)\
            or not isinstance(data["stadia_pro_game_list"], list):
        raise Exception("Unexpected response format")

    game_list: List[StadiaGame] = list()

    for game in data["stadia_game_list"]:
        if "title" in game:
            game_list.append(StadiaGame(name=clean_string(game["title"]), pro_discount=False))

    for game in data["stadia_pro_game_list"]:
        if "title" in game:
            game_list.append(StadiaGame(name=clean_string(game["title"]), pro_discount=False))

    return game_list


if __name__ == "__main__":
    game_list = fetch_stadia()

    for game in game_list:
        logger.info("{}: {}".format(game.name, game.pro_discount))
