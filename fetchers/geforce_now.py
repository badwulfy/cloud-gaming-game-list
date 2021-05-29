from typing import Dict, List
from utils.clean_string import clean_string
import coloredlogs
import logging
from enum import Enum

import requests

logger = logging.getLogger("GeforceNow")
coloredlogs.install(level='INFO', logger=logger,
                    fmt='%(name)s %(asctime)s %(levelname)s %(message)s')


class GeforceStatus(Enum):
    AVAILABLE = "AVAILABLE"
    MAINTENANCE = "MAINTENANCE"
    PATCHING = "PATCHING"
    UNKNOWN = "AVAILABLE"

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

    @classmethod
    def get_value(cls, value):
        return cls._value2member_map_[value]


class Store(Enum):
    EPIC = "Epic"
    GOG = "GOG"
    ORIGIN = "Origin"
    OTHER = "Other"
    STEAM = "Steam"
    UBISOFT_CONNECT = "Ubisoft Connect"

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

    @classmethod
    def get_value(cls, value):
        return cls._value2member_map_[value]


class GeforceGame:
    def __init__(self, name: str, stores: Dict[Store, GeforceStatus]):
        self.name = name
        self.stores = stores


def fetch_geforce_now() -> List[GeforceGame]:
    geforce_url = "https://static.nvidiagrid.net/supported-public-game-list/locales/gfnpc-en-US.json"
    r = requests.get(geforce_url)

    if r.status_code != 200:
        raise Exception("Geforce fetch data failed")

    data = r.json()
    if not isinstance(data, list):
        raise Exception("Unexpected response format")

    # use a dict becase a same game can be listed multiple time (one for each platform)
    game_list: dict[str, GeforceGame] = dict()

    for game in data:
        title: str = clean_string(game['title'])

        # find game status
        status_str = game["status"]
        status = GeforceStatus.UNKNOWN
        if GeforceStatus.has_value(status_str):
            status = GeforceStatus.get_value(status_str)
        else:
            logger.warn(
                "Unknown status for game {} : {}".format(title, status_str))

        # find store
        store_str: str = game["store"]
        store: Store = None
        if Store.has_value(store_str):
            store = Store.get_value(store_str)
        else:
            store = Store.OTHER
            if store_str == "":
                logger.debug(
                    "Game without platform: {} {}".format(title, status))
            else:
                logger.warning("Unknown platform: {}".format(store_str))

        # find the game on known games
        # each game can be present multiple times; one for each platform (i.e. Steam, Origin, etc.)
        if title in game_list:
            game = game_list[title]
            game.stores[store] = status
        else:
            game = GeforceGame(name=title, stores={store: status})
            game_list[title] = game

    return list(game_list.values())


if __name__ == "__main__":
    game_list = fetch_geforce_now()

    for game in game_list:
        store_names = []
        for store in game.stores:
            store_names.append(store.value)

        logger.info("{} : {}".format(game.name, ", ".join(store_names)))
