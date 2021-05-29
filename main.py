
import argparse
import logging
from typing import Optional

import coloredlogs

from fetchers.geforce_now import GeforceGame, fetch_geforce_now
from fetchers.google_stadia import StadiaGame, fetch_stadia
from fetchers.playstation_now import PlaystationNowGame, fetch_playstation_now
from fetchers.xcloud import XCloudGame, fetch_xcloud

# suppress overly verbose logs from libraries that aren't helpful
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Main")
logger.setLevel("INFO")
coloredlogs.install(level='INFO', logger=logger,
                    fmt='%(name)s %(asctime)s %(levelname)s %(message)s')


class CrossCloudGame:
    def __init__(self, name: str,
                 geforce_game: Optional[GeforceGame],
                 psnow_game: Optional[PlaystationNowGame],
                 stadia_game: Optional[StadiaGame],
                 xcloud_game: Optional[XCloudGame],
                 ):
        self.name = name
        self.geforce_game = geforce_game
        self.stadia_game = stadia_game
        self.psnow_game = psnow_game
        self.xcloud_game = xcloud_game

    def nb_cloud(self) -> int:
        nb = 0
        if self.geforce_game is not None:
            nb += 1
        if self.stadia_game is not None:
            nb += 1
        if self.psnow_game is not None:
            nb += 1
        if self.xcloud_game is not None:
            nb += 1
        return nb


def normalize_key(name: str):
    key = name
    name_remapping = {
        "Trine 4": "Trine 4: The Nightmare Prince",
        "Cities: Skylines - Xbox One Edition": "Cities: Skylines",
        "Wolfenstein Young Blood": "Wolfenstein Youngblood",
        "ARK: Survival Evolved Explorer's Edition": "ARK: Survival Evolved",
        "Totally Accurate Battle Simulator (Game Preview)": "Totally Accurate Battle Simulator",
        "Tom Clancy's Rainbow Six® Siege Deluxe Edition": "Tom Clancy's Rainbow Six® Siege"
    }

    if name in name_remapping:
        key = name_remapping[name]

    key = key.lower().replace("™", "").replace("®", "").replace("©", "").replace(
        ":", "").replace("'", "").replace("’", "").replace("_", " ")

    return key


def main(output_file: str = None):

    try:
        geforce_games = fetch_geforce_now()
        logger.info("Geforce: {} Games".format(len(geforce_games)))
    except Exception as e:
        logger.error("Cannot get Geforce games:")
        logger.error(e)
        exit(1)

    try:
        stadia_games = fetch_stadia()
        logger.info("Stadia: {} Games".format(len(stadia_games)))
    except Exception as e:
        logger.error("Cannot get Stadia games:")
        logger.error(e)
        exit(1)

    try:
        psnow_games = fetch_playstation_now()
        logger.info("Playstation Now: {} Games".format(len(stadia_games)))
    except Exception as e:
        logger.error("Cannot get Playstation Now games:")
        logger.error(e)
        exit(1)

    try:
        xcloud_games = fetch_xcloud()
        logger.info("XCloud: {} Games".format(len(xcloud_games)))
    except Exception as e:
        logger.error("Cannot get XCloud games:")
        logger.error(e)
        exit(1)

    merged_games: dict[str, CrossCloudGame] = dict()

    for game in geforce_games:
        game_name = game.name
        key = normalize_key(game_name)

        if key not in merged_games:
            merged_games[key] = CrossCloudGame(name=game_name, geforce_game=game, psnow_game=None,
                                               stadia_game=None, xcloud_game=None)
        else:
            merged_games[key].geforce_game = game

    for game in psnow_games:
        game_name = game.name
        key = normalize_key(game_name)

        if key not in merged_games:
            merged_games[key] = CrossCloudGame(name=game_name, geforce_game=None, psnow_game=game,
                                               stadia_game=None, xcloud_game=None)
        else:
            merged_games[key].xcloud_game = game

    for game in stadia_games:
        game_name = game.name
        key = normalize_key(game_name)

        if key not in merged_games:
            merged_games[key] = CrossCloudGame(name=game_name, geforce_game=None, psnow_game=None,
                                               stadia_game=game, xcloud_game=None)
        else:
            merged_games[key].stadia_game = game

    for game in xcloud_games:
        game_name = game.name
        key = normalize_key(game_name)

        if key not in merged_games:
            merged_games[key] = CrossCloudGame(name=game_name, geforce_game=None, psnow_game=None,
                                               stadia_game=None, xcloud_game=game)
        else:
            merged_games[key].xcloud_game = game

    f = None
    if output_file is not None:
        f = open(output_file, "w", encoding="utf-8-sig")
        f.write('Name;Geforce;PSNow;Stadia;XCloud\n')

    games_ordered = sorted(list(merged_games.values()), key=lambda x: x.name)
    for game in games_ordered:
        providers = ""
        if game.geforce_game is not None:
            providers += "Geforce"
        else:
            providers += "".ljust(7)

        providers += " "
        if game.psnow_game is not None:
            providers += "PSNow"
        else:
            providers += "".ljust(5)

        providers += " "
        if game.stadia_game is not None:
            providers += "Stadia"
        else:
            providers += "".ljust(6)

        providers += " "
        if game.xcloud_game is not None:
            providers += ("Xcloud")
        else:
            providers += "".ljust(6)

        to_show = "{} {}".format(game.name.ljust(70), providers)
        logger.debug(to_show)

        if f is not None:
            f.write(
                '"{}";{};{};{};{}\n'
                .format(game.name,
                        game.geforce_game is not None,
                        game.psnow_game is not None,
                        game.stadia_game is not None,
                        game.xcloud_game is not None,
                        )
            )

    logger.info("Total of unique games: {}".format(len(games_ordered)))
    if f is not None:
        logger.info("Output file generated: {}".format(output_file))
        f.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", type=str, default="output.csv", help="output file")
    args = parser.parse_args()

    main(args.output)
