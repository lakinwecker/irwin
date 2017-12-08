import threading
import logging

from modules.core.Game import Game
from modules.core.GameAnalysis import GameAnalysis
from modules.core.GameAnalysisStore import GameAnalysisStore

class RequestAnalyseReportThread(threading.Thread):
  def __init__(self, env):
    threading.Thread.__init__(self)
    self.env = env

  def run(self):
    while True:
      logging.debug('Getting new player ID')
      userId = self.env.api.getNextPlayerId()
      logging.debug('Getting player data for '+userId)
      playerData = self.env.api.getPlayerData(userId)

      # pull what we already have on the player
      gameAnalysisStore = GameAnalysisStore.new()
      gameAnalysisStore.addGames(self.env.gameDB.byUserId(userId))
      gameAnalysisStore.addGameAnalyses(self.env.gameAnalysisDB.byUserId(userId))

      # Filter games and assessments for relevant info
      try:
        gameAnalysisStore.addGames([Game.fromDict(gid, userId, g) for gid, g in playerData['games'].items() if (g.get('initialFen') is None and g.get('variant') is None)])
      except KeyError:
        continue # if this doesn't gather any useful data, skip

      self.env.gameDB.lazyWriteGames(gameAnalysisStore.games)

      logging.debug("Already Analysed: " + str(len(gameAnalysisStore.gameAnalyses)))

      gameAnalysisStore.addGameAnalyses([GameAnalysis.fromGame(game, self.env.engine, self.env.infoHandler, game.white == userId, self.env.settings['stockfish']['nodes']) for game in gameAnalysisStore.randomGamesWithoutAnalysis()])

      self.env.gameAnalysisDB.lazyWriteGameAnalyses(gameAnalysisStore.gameAnalyses)

      logging.warning('Posting report for ' + userId)
      self.env.api.postReport(self.env.irwin.report(userId, gameAnalysisStore))