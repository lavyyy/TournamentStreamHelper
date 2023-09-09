import os
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from flask import Flask, send_from_directory, request
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO, send
import json
from loguru import logger
from .TSHWebServerActions import WebServerActions

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


class WebServer(QThread):
    app = Flask(__name__, static_folder=os.path.curdir)
    cors = CORS(app)
    socketio = SocketIO(app)
    app.config['CORS_HEADERS'] = 'Content-Type'
    actions = None

    def __init__(self, parent=None, scoreboard=None, stageWidget=None) -> None:
        super().__init__(parent)
        WebServer.actions = WebServerActions(
            parent=parent,
            scoreboard=scoreboard,
            stageWidget=stageWidget
        )
        self.host_name = "0.0.0.0"
        self.port = 5000

    @app.route('/ruleset')
    def ruleset():
        return WebServer.actions.ruleset()

    @socketio.on('ruleset', namespace='/ws')
    def ws_ruleset():
        send(WebServer.actions.ruleset())

    @app.route('/stage_strike_stage_clicked', methods=['POST'])
    def stage_clicked():
        return WebServer.actions.stage_clicked(request.get_data())

    @socketio.on('stage_strike_stage_clicked', namespace='/ws')
    def ws_stage_clicked(message):
        send(WebServer.actions.stage_clicked(message))

    @app.route('/stage_strike_confirm_clicked', methods=['POST'])
    def confirm_clicked():
        return WebServer.actions.confirm_clicked()

    @socketio.on('stage_strike_confirm_clicked', namespace='/ws')
    def ws_confirm_clicked():
        send(WebServer.actions.confirm_clicked())

    @app.route('/stage_strike_rps_win', methods=['POST'])
    def rps_win():
        return WebServer.actions.rps_win(json.loads(request.get_data()).get("winner"))

    @socketio.on('stage_strike_rps_win', namespace='/ws')
    def ws_rps_win(message):
        send(WebServer.actions.rps_win(json.loads(message).get("winner")))

    @app.route('/stage_strike_match_win', methods=['POST'])
    def match_win():
        return WebServer.actions.match_win(json.loads(request.get_data()).get("winner"))

    @socketio.on('stage_strike_match_win', namespace='/ws')
    def ws_match_win(message):
        send(WebServer.actions.match_win(json.loads(message).get("winner")))

    @app.route('/stage_strike_set_gentlemans', methods=['POST'])
    def set_gentlemans():
        return WebServer.actions.set_gentlemans(json.loads(request.get_data()).get("value"))

    @socketio.on('stage_strike_set_gentlemans', namespace='/ws')
    def ws_set_gentlemans(message):
        send(WebServer.actions.set_gentlemans(json.loads(message).get("value")))

    @app.route('/stage_strike_undo', methods=['POST'])
    def stage_strike_undo():
        return WebServer.actions.stage_strike_undo()

    @socketio.on('stage_strike_undo', namespace='/ws')
    def ws_stage_strike_undo():
        send(WebServer.actions.stage_strike_undo())

    @app.route('/stage_strike_redo', methods=['POST'])
    def stage_strike_redo():
        return WebServer.actions.stage_strike_redo()

    @socketio.on('stage_strike_redo', namespace='/ws')
    def ws_stage_strike_redo():
        send(WebServer.actions.stage_strike_redo())

    @app.route('/stage_strike_reset', methods=['POST'])
    def reset():
        return WebServer.actions.reset()

    @socketio.on('stage_strike_reset', namespace='/ws')
    def ws_reset():
        send(WebServer.actions.reset())

    @app.route('/score', methods=['POST'])
    def post_score():
        return WebServer.actions.post_score(request.get_data())

    @socketio.on('score', namespace='/ws')
    def ws_post_score(message):
        send(WebServer.actions.post_score(message))

    # Ticks score of Team specified up by 1 point
    @app.route('/team<team>-scoreup')
    def team_scoreup(team):
        return WebServer.actions.team_scoreup(team)

    @socketio.on('team_scoreup', namespace='/ws')
    def ws_team_scoreup(message):
        send(WebServer.actions.team_scoreup(message))

    # Ticks score of Team specified down by 1 point
    @app.route('/team<team>-scoredown')
    def team_scoredown(team):
        return WebServer.actions.team_scoredown(team)

    @socketio.on('team_scoredown', namespace='/ws')
    def ws_team_scoredown(message):
        send(WebServer.actions.team_scoredown(message))

    # Dynamic endpoint to allow flexible sets of information
    # Ex. http://192.168.1.2:5000/set?best-of=5
    #
    # Test Scenario that was used
    # Ex. http://192.168.4.34:5000/set?best-of=5&phase=Top 32&match=Winners Finals
    @app.route('/set')
    def set_route():
        return WebServer.actions.set_route(
            bestOf=request.args.get('best-of'),
            phase=request.args.get('phase'),
            match=request.args.get('match'),
            players=request.args.get('players'),
            characters=request.args.get('characters'),
            losers=request.args.get('losers'),
            team=request.args.get('team')
        )

    @socketio.on('set', namespace='/ws')
    def ws_set_route(message):
        parsed = json.loads(message)
        send(WebServer.actions.set_route(
            bestOf=parsed.get('best_of'),
            phase=parsed.get('phase'),
            match=parsed.get('match'),
            players=parsed.get('players'),
            characters=parsed.get('characters'),
            losers=parsed.get('losers'),
            team=parsed.get('team')
        ))

    # Set player data
    @app.post('/update-team-<team>-<player>')
    def set_team_data(team, player):
        data = request.get_json()
        return WebServer.actions.set_team_data(team, player, data)
    
    @socketio.on('update_team', namespace='/ws')
    def ws_set_team_data(message):
        data = json.loads(message)
        send(WebServer.actions.set_team_data(data.get("team"), data.get("player"), data.get("data")))

    # Get characters
    @app.route('/characters')
    def get_characters():
        return WebServer.actions.get_characters()
    
    @socketio.on('characters', namespace='/ws')
    def ws_get_characters():
        send(WebServer.actions.get_characters())

    # Swaps teams
    @app.route('/swap-teams')
    def swap_teams():
        return WebServer.actions.swap_teams()
    
    @socketio.on('swap_teams', namespace='/ws')
    def ws_swap_teams():
        send(WebServer.actions.swap_teams())

    # Opens Set Selector Window
    @app.route('/open-set')
    def open_sets():
        return WebServer.actions.open_sets()
    
    @socketio.on('open_set', namespace='/ws')
    def ws_open_sets():
        send(WebServer.actions.open_sets())

    # Pulls Current Stream Set
    @app.route('/pull-stream')
    def pull_stream_set():
        return WebServer.actions.pull_stream_set()
    
    @socketio.on('pull_stream', namespace='/ws')
    def ws_pull_stream_set():
        send(WebServer.actions.pull_stream_set())

    # Pulls Current User Set
    @app.route('/pull-user')
    def pull_user_set():
        return WebServer.actions.pull_user_set()
    
    @socketio.on('pull_user', namespace='/ws')
    def ws_pull_user_set():
        send(WebServer.actions.pull_user_set())

    # Resubmits Call for Recent Sets
    @app.route('/stats-recent-sets')
    def stats_recent_sets():
        return WebServer.actions.stats_recent_sets()
    
    @socketio.on('stats_recent_sets', namespace='/ws')
    def ws_stats_recent_sets():
        send(WebServer.actions.stats_recent_sets())

    # Resubmits Call for Upset Factor
    @app.route('/stats-upset-factor')
    def stats_upset_factor():
        return WebServer.actions.stats_upset_factor()
    
    @socketio.on('stats_upset_factor', namespace='/ws')
    def ws_stats_upset_factor():
        send(WebServer.actions.stats_upset_factor())

    # Resubmits Call for Last Sets
    @app.route('/stats-last-sets-<player>')
    def stats_last_sets(player):
        return WebServer.actions.stats_last_sets(player)
    
    @socketio.on('stats_last_sets', namespace='/ws')
    def ws_stats_last_sets(message):
        send(WebServer.actions.stats_last_sets(message))

   # Resubmits Call for History Sets
    @app.route('/stats-history-sets-<player>')
    def stats_history_sets(player):
        return WebServer.actions.stats_history_sets(player)
    
    @socketio.on('stats_history_sets', namespace='/ws')
    def ws_stats_history_sets(message):
        send(WebServer.actions.stats_history_sets(message))

    # Resets scores
    @app.route('/reset-scores')
    def reset_scores():
        return WebServer.actions.reset_scores()
    
    @socketio.on('reset_scores', namespace='/ws')
    def ws_reset_scores():
        send(WebServer.actions.reset_scores())

    # Resets scores, match, phase, and losers status
    @app.route('/reset-match')
    def reset_match():
        return WebServer.actions.reset_match()
    
    @socketio.on('reset_match', namespace='/ws')
    def ws_reset_match():
        send(WebServer.actions.reset_match())

    # Resets scores, match, phase, and losers status
    @app.route('/reset-players')
    def reset_players():
        return WebServer.actions.reset_players()
    
    @socketio.on('reset_players', namespace='/ws')
    def ws_reset_players():
        send(WebServer.actions.reset_players())

    # Resets all values
    @app.route('/clear-all')
    def clear_all():
        return WebServer.actions.clear_all()
    
    @socketio.on('clear_all', namespace='/ws')
    def ws_clear_all():
        send(WebServer.actions.clear_all())

    # Loads a set remotely by providing a set ID to pull from the data provider
    @app.route('/load-set')
    def load_set():
        return WebServer.actions.load_set(request.args.get("set"))

    @socketio.on('load_set', namespace='/ws')
    def ws_load_set(message):
        send(WebServer.actions.load_set(message))

    @app.route('/', defaults=dict(filename=None))
    @app.route('/<path:filename>', methods=['GET', 'POST'])
    @cross_origin()
    def test(filename):
        filename = filename or 'stage_strike_app/build/index.html'
        return send_from_directory(os.path.abspath("."), filename, as_attachment=filename.endswith(".gz"))

    def run(self):
        self.socketio.run(app=self.app, host=self.host_name, port=self.port,
                          debug=False, use_reloader=False)
