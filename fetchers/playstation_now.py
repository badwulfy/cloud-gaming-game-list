import logging
import re
from enum import Enum
from typing import List
from utils.clean_string import clean_string

# ignore "mypy" import error for coloredlogs and BeautifulSoup.
# see https://mypy.readthedocs.io/en/latest/running_mypy.html#missing-imports
import coloredlogs  # type: ignore
import requests
from bs4 import BeautifulSoup, NavigableString  # type: ignore

logger = logging.getLogger("PlaystationNow")
coloredlogs.install(level='INFO', logger=logger,
                    fmt='%(name)s %(asctime)s %(levelname)s %(message)s')


class PlaystationModel(Enum):
    PS4 = 'PS4'
    PS3 = 'PS3'
    UNKNOWN = 'UNKNOWN'

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

    @classmethod
    def get_value(cls, value):
        return cls._value2member_map_[value]


class PlaystationNowGame:
    def __init__(self, name: str, console: PlaystationModel):
        self.name = name
        self.console = console


def fetch_playstation_now() -> List[PlaystationNowGame]:
    playstation_now = 'https://www.playstation.com/fr-fr/ps-now/ps-now-games/#all-ps-now-games'

    page = requests.get(playstation_now)
    if(page.status_code != 200):
        raise Exception("Geforce fetch data failed")

    soup = BeautifulSoup(page.text, 'html.parser')

    game_list: List[PlaystationNowGame] = []

    # games are first sorted by letter
    id_regex = re.compile("^tab-content-")
    letter_blocks = soup.find_all("div", id=id_regex)

    for letter_block in letter_blocks:

        # then, games are in multiple columns
        sub_blocks = letter_block.findAll("div", class_="text-block")
        for sub_block in sub_blocks:

            # each column can have a console type (or none) in a h3 or a span
            game_console: PlaystationModel = PlaystationModel.UNKNOWN
            games_type_node = sub_block.find("h3")
            if games_type_node is None or PlaystationModel.has_value(games_type_node.text) is False:
                games_type_node = sub_block.find("span", class_="txt--6")
            if games_type_node is not None and PlaystationModel.has_value(games_type_node.text):
                game_console = PlaystationModel.get_value(games_type_node.text)

            # loop over games
            games = sub_block.findAll("p")
            for game in games:

                # name list can be on one paragraph (separated by <br/>) or in multiple paragraph
                children = list(game.children)
                if len(children) == 1:

                    first_child = children[0]
                    # if it is a string, then it is a game name
                    if isinstance(first_child, NavigableString):
                        game_name = clean_string(first_child)
                        if len(game_name) > 0:
                            game_list.append(PlaystationNowGame(
                                name=game_name, console=game_console))
                    # sometime, Sony put the console type in a span (yes, it's weird !)
                    elif PlaystationModel.has_value(first_child.text):
                        game_console = PlaystationModel.get_value(
                            first_child.text)
                else:

                    # loop over game names and ignoring <br/>
                    for child in children:
                        if isinstance(child, NavigableString):
                            game_name = clean_string(child)
                            if len(game_name) > 0:
                                game_list.append(PlaystationNowGame(
                                    name=game_name, console=game_console))

    return game_list


if __name__ == "__main__":
    game_list = fetch_playstation_now()

    for game in game_list:
        logger.info("{}: {}".format(game.name, game.console.value))
