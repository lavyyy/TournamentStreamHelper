from collections import Counter
from typing import final
from PyQt5.QtCore import *
from PyQt5.QtGui import QStandardItem, QStandardItemModel
import requests
import os
import traceback
from Helpers.TSHCountryHelper import TSHCountryHelper
from Helpers.TSHDictHelper import deep_get
from TSHGameAssetManager import TSHGameAssetManager
from TSHPlayerDB import TSHPlayerDB
from TournamentDataProvider import TournamentDataProvider
import json
import TSHTournamentDataProvider

from Workers import Worker


class SmashGGDataProvider(TournamentDataProvider.TournamentDataProvider):
    SetsQuery = None
    EntrantsQuery = None

    def __init__(self, url) -> None:
        super().__init__(url)

    def GetTournamentData(self):
        pass

    def GetMatch(self, setId):
        try:
            r = requests.get(
                f'https://smash.gg/api/-/gg_api./set/{setId};bustCache=true;expand=["setTask"];fetchMostRecentCached=true',
                {
                    "extensions": {"cacheControl": {"version": 1, "noCache": True}},
                    "cacheControl": {"version": 1, "noCache": True},
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache"
                }
            )
            respTasks = json.loads(r.text)

            tasks = respTasks.get("entities", {}).get("setTask", [])

            selectedCharMap = {}

            for task in reversed(tasks):
                if task.get("action") == "setup_character" or task.get("action") == "setup_strike":
                    selectedCharMap = task.get(
                        "metadata", {}).get("charSelections", {})
                    break

            selectedChars = [[], []]

            print("Hey!")
            print(respTasks.get("entities", {}))

            for char in selectedCharMap.items():
                if str(char[0]) == str(respTasks.get("entities", {}).get("sets", {}).get("entrant1Id")):
                    selectedChars[0] = char[1]
                if str(char[0]) == str(respTasks.get("entities", {}).get("sets", {}).get("entrant2Id")):
                    selectedChars[1] = char[1]

            latestWinner = None

            for task in reversed(tasks):
                if len(task.get("metadata", [])) == 0:
                    continue
                if task.get("metadata", {}).get("report", {}).get("winnerId", None) is not None:
                    latestWinner = int(task.get("metadata", {}).get(
                        "report", {}).get("winnerId"))
                    break

            allStages = None
            strikedStages = None
            selectedStage = None
            dsrStages = None
            playerTurn = None

            for task in reversed(tasks):
                if task.get("action") in ["setup_strike", "setup_stage", "setup_character", "setup_ban", "report"]:
                    if len(task.get("metadata", [])) == 0:
                        continue

                    base = task.get("metadata", {})

                    if task.get("action") == "report":
                        base = base.get("report", {})

                    print(base)

                    if base.get("strikeStages", None) is not None:
                        allStages = base.get("strikeStages")
                    elif base.get("banStages", None) is not None:
                        allStages = base.get("banStages")

                    if base.get("strikeList", None) is not None:
                        strikedStages = base.get("strikeList")
                    elif base.get("banList", None) is not None:
                        strikedStages = base.get("banList")

                    if base.get("stageSelection", None) is not None:
                        selectedStage = base.get("stageSelection")
                    elif base.get("stageId", None) is not None:
                        selectedStage = base.get("stageId")

                    if (base.get("useDSR") or base.get("useMDSR")) and base.get("stageWins"):

                        loser = next(
                            (p for p in base.get("stageWins").keys()
                                if int(p) != int(latestWinner)),
                            None
                        )

                        if loser is not None:
                            dsrStages = []
                            dsrStages = [int(s) for s in base.get(
                                "stageWins")[loser]]

                    if allStages == None and strikedStages == None and selectedStage == None:
                        continue

                    if allStages == None:
                        continue

                    break

            changed = False

            try:
                allStagesFinal = {}
                for st in allStages:
                    stage = TSHGameAssetManager.instance.GetStageFromSmashGGId(
                        st)
                    if stage:
                        allStagesFinal[stage[1].get("codename")] = stage[1]

                striked = []
                if strikedStages is not None:
                    for stage in strikedStages:
                        stage = TSHGameAssetManager.instance.GetStageFromSmashGGId(
                            stage)
                        if stage:
                            striked.append(stage[1].get("codename"))

                selected = ""
                selectedStage = TSHGameAssetManager.instance.GetStageFromSmashGGId(
                    selectedStage)
                if selectedStage:
                    selected = selectedStage[1]

                dsr = []
                if dsrStages:
                    for stage in dsrStages:
                        stage = TSHGameAssetManager.instance.GetStageFromSmashGGId(
                            stage)
                        if stage:
                            dsr.append(stage[1].get("codename"))

                stageStrikeState = {
                    "stages": allStagesFinal,
                    "striked": striked,
                    "selected": selected,
                    "dsr": dsr,
                    "playerTurn": playerTurn
                }
            except:
                print(traceback.format_exc())
                stageStrikeState = {}

            print(selectedChars)
            print(stageStrikeState)

            entrants = [[], []]

            for i, entrantChars in enumerate(selectedChars):
                for char in entrantChars:
                    entrants[i].append({
                        "mains": TSHGameAssetManager.instance.GetCharacterFromSmashGGId(char)[0]
                    })

            return({
                "stage_strike": stageStrikeState,
                "entrants": entrants if len(entrants[0]) > 0 and len(entrants[1]) > 0 else None,
                "clear": False
            })

        except Exception as e:
            traceback.print_exc()
        return {}

    def GetMatches(self):
        try:
            data = requests.post(
                "https://smash.gg/api/-/gql",
                headers={
                    "client-version": "19",
                    'Content-Type': 'application/json'
                },
                json={
                    "operationName": "EventMatchListQuery",
                    "variables": {
                        "filters": {
                            "state": [
                                1,
                                6,
                                2,
                                3
                            ],
                            "hideEmpty": True
                        },
                        "eventSlug": self.url.split("smash.gg/")[1]
                    },
                    "query": SmashGGDataProvider.SetsQuery
                }

            )
            print(data)

            data = json.loads(data.text)

            sets = deep_get(data, "data.event.sets.nodes", [])
            final_data = []

            for _set in sets:
                p1 = deep_get(_set, "paginatedSlots.nodes", [])[0]
                p2 = deep_get(_set, "paginatedSlots.nodes", [])[1]

                setData = {
                    "id": _set.get("id"),
                    "round_name": _set.get("fullRoundText"),
                    "tournament_phase": deep_get(_set, "phaseGroup.phase.name"),
                    "p1_name": p1.get("entrant", {}).get("name", "") if p1 and p1.get("entrant", {}) != None else "",
                    "p2_name": p2.get("entrant", {}).get("name", "") if p2 and p2.get("entrant", {}) != None else "",
                }

                players = [[], []]

                entrants = [
                    deep_get(_set, "paginatedSlots.nodes", [])[0].get(
                        "entrant", {}).get("participants", []) if deep_get(_set, "paginatedSlots.nodes", [])[0].get(
                        "entrant", {}) is not None else [],
                    deep_get(_set, "paginatedSlots.nodes", [])[1].get(
                        "entrant", {}).get("participants", []) if deep_get(_set, "paginatedSlots.nodes", [])[1].get(
                        "entrant", {}) is not None else [],
                ]

                for i, team in enumerate(entrants):
                    for j, entrant in enumerate(team):
                        player = entrant.get("player")
                        user = entrant.get("user")

                        playerData = {}

                        if player:
                            playerData["prefix"] = player.get("prefix")
                            playerData["gamerTag"] = player.get("gamerTag")
                            playerData["name"] = player.get("name")

                            # Main character
                            playerSelections = Counter()

                            sets = deep_get(player, "sets.nodes", [])
                            playerId = player.get("id")
                            if len(sets) > 0:
                                games = sets[0].get("games", [])
                                if games and len(games) > 0:
                                    for game in games:
                                        selections = game.get("selections", [])
                                        if selections:
                                            for selection in selections:
                                                participants = selection.get(
                                                    "entrant", {}).get("participants", [])
                                                if len(participants) > 0:
                                                    participantId = participants[0].get(
                                                        "player", {}).get("id", None)
                                                    if participantId and participantId == playerId:
                                                        playerSelections[selection.get(
                                                            "selectionValue")] += 1

                            main = playerSelections.most_common(1)

                            if len(main) > 0:
                                playerData["smashggMain"] = main[0][0]

                        if user:
                            if len(user.get("authorizations", [])) > 0:
                                playerData["twitter"] = user.get("authorizations", [])[
                                    0].get("externalUsername")

                            if len(user.get("images")) > 0:
                                playerData["picture"] = user.get("images")[
                                    0].get("url")

                            if user.get("location"):
                                # Country to country code
                                if user.get("location").get("country"):
                                    for country in TSHCountryHelper.countries.values():
                                        if user.get("location").get("country") == country.get("name"):
                                            playerData["country_code"] = country.get(
                                                "code")
                                            break

                                # State -- direct
                                if user.get("location").get("state"):
                                    stateCode = user.get(
                                        "location").get("state")
                                    if stateCode:
                                        playerData["state_code"] = user.get(
                                            "location").get("state")
                                # State -- from city
                                elif user.get("location").get("city"):
                                    stateCode = TSHCountryHelper.FindState(
                                        playerData["country_code"], user.get("location").get("city"))
                                    if stateCode:
                                        playerData["state_code"] = stateCode

                            if playerData.get("smashggMain"):
                                main = TSHGameAssetManager.instance.GetCharacterFromSmashGGId(
                                    playerData.get("smashggMain"))
                                if main:
                                    playerData["mains"] = main[0]

                        players[i].append(playerData)

                setData["entrants"] = players

                final_data.append(setData)

            return(final_data)
        except Exception as e:
            traceback.print_exc()

    def GetEntrants(self):
        self.threadpool = QThreadPool()
        worker = Worker(self.GetEntrantsWorker)
        self.threadpool.start(worker)

    def GetEntrantsWorker(self, progress_callback):
        try:
            page = 1
            totalPages = 1
            # final_data = QStandardItemModel()
            players = []

            while page <= totalPages:
                print(page, "/", totalPages)
                data = requests.post(
                    "https://smash.gg/api/-/gql",
                    headers={
                        "client-version": "19",
                        'Content-Type': 'application/json'
                    },
                    json={
                        "operationName": "EventEntrantsListQuery",
                        "variables": {
                            "eventSlug": self.url.split("smash.gg/")[1],
                            "page": page
                        },
                        "query": SmashGGDataProvider.EntrantsQuery
                    }

                )

                data = json.loads(data.text)

                videogame = deep_get(data, "data.event.videogame.id", None)
                print("videojogo", videogame)
                if videogame:
                    TSHGameAssetManager.instance.SetGameFromSmashGGId(
                        videogame)

                totalPages = deep_get(
                    data, "data.event.entrants.pageInfo.totalPages", [])

                entrants = deep_get(data, "data.event.entrants.nodes", [])
                print("Entrants: ", len(entrants))

                for i, team in enumerate(entrants):
                    for j, entrant in enumerate(team.get("participants", [])):
                        player = entrant.get("player")
                        user = entrant.get("user")

                        playerData = {}

                        if player:
                            playerData["prefix"] = player.get("prefix")
                            playerData["gamerTag"] = player.get("gamerTag")
                            playerData["name"] = player.get("name")

                            # Main character
                            playerSelections = Counter()

                            sets = deep_get(player, "sets.nodes", [])
                            playerId = player.get("id")
                            if len(sets) > 0:
                                games = sets[0].get("games", [])
                                if games and len(games) > 0:
                                    for game in games:
                                        selections = game.get("selections", [])
                                        if selections:
                                            for selection in selections:
                                                participants = selection.get(
                                                    "entrant", {}).get("participants", [])
                                                if len(participants) > 0:
                                                    participantId = participants[0].get(
                                                        "player", {}).get("id", None)
                                                    if participantId and participantId == playerId:
                                                        playerSelections[selection.get(
                                                            "selectionValue")] += 1

                            mains = playerSelections.most_common()

                            if len(mains) > 0:
                                playerData["smashggMains"] = mains

                        if user:
                            if len(user.get("authorizations", [])) > 0:
                                playerData["twitter"] = user.get("authorizations", [])[
                                    0].get("externalUsername")

                            if len(user.get("images")) > 0:
                                playerData["picture"] = user.get("images")[
                                    0].get("url")

                            if user.get("location"):
                                # Country to country code
                                if user.get("location").get("country"):
                                    for country in TSHCountryHelper.countries.values():
                                        if user.get("location").get("country") == country.get("name"):
                                            playerData["country_code"] = country.get(
                                                "code")
                                            break

                                # State -- direct
                                if user.get("location").get("state"):
                                    stateCode = user.get(
                                        "location").get("state")
                                    if stateCode:
                                        playerData["state_code"] = user.get(
                                            "location").get("state")
                                # State -- from city
                                elif user.get("location").get("city"):
                                    stateCode = TSHCountryHelper.FindState(
                                        playerData["country_code"], user.get("location").get("city"))
                                    if stateCode:
                                        playerData["state_code"] = stateCode

                            if playerData.get("smashggMains"):
                                if TSHGameAssetManager.instance.selectedGame:
                                    gameCodename = TSHGameAssetManager.instance.selectedGame.get(
                                        "codename")

                                    mains = []

                                    for sggmain in playerData.get("smashggMains"):
                                        main = TSHGameAssetManager.instance.GetCharacterFromSmashGGId(
                                            sggmain[0])
                                        if main:
                                            mains.append([main[0]])

                                    playerData["mains"] = {
                                        gameCodename: mains
                                    }
                                else:
                                    playerData["mains"] = {}

                        players.append(playerData)

                TSHPlayerDB.AddPlayers(players)
                players = []

                page += 1
        except Exception as e:
            traceback.print_exc()


f = open(os.path.dirname(os.path.realpath(__file__)) + "/" +
         "SmashGGSetsQuery.txt", 'r')
SmashGGDataProvider.SetsQuery = f.read()

f = open(os.path.dirname(os.path.realpath(__file__)) + "/" +
         "SmashGGEntrantsQuery.txt", 'r')
SmashGGDataProvider.EntrantsQuery = f.read()
