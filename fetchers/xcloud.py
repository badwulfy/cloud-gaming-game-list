import logging
import re
from typing import Dict, List
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from utils.clean_string import clean_string

import coloredlogs
import requests

logger = logging.getLogger("XCLOUD")
coloredlogs.install(level='INFO', logger=logger,
                    fmt='%(name)s %(asctime)s %(levelname)s %(message)s')


class XCloudGame:
    def __init__(self, name: str, xbox_id: str):
        self.name = name
        self.xbox_id = xbox_id


def remove_url_query_params(url: str) -> str:
    url_parsed = urlparse(url)
    return url_parsed.scheme + "://" + url_parsed.netloc + url_parsed.path


def replace_url_query_string(url: str, params: Dict[str, str]):
    url_parts = list(urlparse(url))
    query = dict(parse_qsl(url_parts[4]))
    query.update(params)
    url_parts[4] = urlencode(query)
    return urlunparse(url_parts)


def fetch_xcloud() -> List[XCloudGame]:
    xcloud_url = "https://www.xbox.com/en-US/xbox-game-pass/games"\
                 "/js/xgpcatPopulate-MWF.js"
    r = requests.get(xcloud_url)

    if(r.status_code != 200):
        raise Exception("XCloud fetch populate script failed")

    data = r.text
    # first : find the allCloud category id (guidAmpt)
    # it is a uuidv4 ID (32 hexadecimal characters and 4 hyphens)
    # https://www.debuggex.com/r/crK1W0FQBBlhO5md
    ms_cv_regex = re.compile(
        "\"allCloud\" : \"([0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12}).*\"")
    cloud_caterory_match = ms_cv_regex.search(data, re.IGNORECASE)

    if cloud_caterory_match is not None:
        cloud_caterory_id = cloud_caterory_match.group(1)
        logger.debug("Cloud games category id: {}".format(cloud_caterory_id))
    else:
        raise Exception("Cannot get cloud games category")

    # extract url to get game list
    # i.e. "https://catalog.gamepass.com/sigls/v2?id=CATEGORY&language=LANG&market=MARK"; # noqa: E501
    games_list_url_regex = re.compile("xgplistUrl = \"(.*)\"")
    games_list_url_match = games_list_url_regex.search(data)

    if games_list_url_match is not None:
        games_list_url = games_list_url_match.group(1)
        logger.debug("Game list URL (not modified): {}".format(games_list_url))
    else:
        raise Exception("Cannot get game list URL")

    # add parameters to the URL
    # TODO : allow to change region
    params = {'id': cloud_caterory_id, 'language': 'en-US', 'market': "US"}
    games_list_url = replace_url_query_string(games_list_url, params)
    logger.debug("Game list URL (with real parameters): {}"
                 .format(games_list_url))

    r = requests.get(games_list_url)
    if(r.status_code != 200):
        raise Exception("Geforce fetch game id list failed")
    game_list_data = r.json()

    game_ids: list[str] = []
    for game in game_list_data:
        if "id" in game:
            game_ids.append(game["id"])
    logger.debug("Found {} game IDs".format(len(game_ids)))

    # extract url to get game informations
    # i.e. https://displaycatalog.mp.microsoft.com/v7.0/products
    game_information_url_regex = re.compile("guidUrl = '(.*\?)")  # noqa: W605
    game_information_url_match = game_information_url_regex.search(data)

    if game_information_url_match is not None:
        game_information_url = game_information_url_match.group(1)
        logger.debug("Game information URL (not modified): {}".format(
            game_information_url))
    else:
        raise Exception("Cannot get game  information URL")

    ms_cv_regex = re.compile("MS-CV=(.*)'")
    ms_cv_match = ms_cv_regex.search(data, re.IGNORECASE)

    if ms_cv_match is not None:
        ms_cv = ms_cv_match.group(1)
        logger.debug("MS CV: {}".format(ms_cv))
    else:
        raise Exception("Cannot get MS CV")

    params = {
        'bigIds': ",".join(game_ids),
        'languages': 'en-US',
        'market': "US",
        "MS-CV": ms_cv
    }
    game_information_url = replace_url_query_string(
        game_information_url, params)
    r = requests.get(game_information_url)
    if(r.status_code != 200):
        raise Exception("Geforce fetch game informations failed: code {} {}"
                        .format(r.status_code, r.text))

    game_list: list[XCloudGame] = list()

    game_information_data = r.json()
    if "Products" not in game_information_data \
            or not isinstance(game_information_data["Products"], list):
        raise Exception("Unexpected games information response format")

    for product in game_information_data["Products"]:
        if "ProductId" not in product or "LocalizedProperties" not in product:
            continue
        localized_properties = product["LocalizedProperties"]
        product_id = product["ProductId"]

        if isinstance(product["LocalizedProperties"], list) \
                and len(localized_properties) > 0 \
                and "ProductTitle" in localized_properties[0]:
            name = clean_string(localized_properties[0]["ProductTitle"])
            game_list.append(XCloudGame(name=name, xbox_id=product_id))

    return game_list


if __name__ == "__main__":
    game_list = fetch_xcloud()

    for game in game_list:
        logger.info("{}: {}".format(game.name, game.xbox_id))
