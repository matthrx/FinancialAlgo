from flask import Flask
from flask_restful import Api
from centralizedApp.api.resource import *
from centralizedApp.algorithm import FinancialAlgothimBackend
import threading

app = Flask(__name__)
api = Api(app)

api.add_resource(CurrentPosition, '/current/', endpoint="current")
api.add_resource(PositionResultsPerDay, '/day/', enpoint="per_day")
api.add_resource(PositionSpecificMarket, "/market/<string:market>", endpoint="specific_market")
api.add_resource(HistoricalPositions, "/historical/", endpoint="historical")

def run_algorithm(): FinancialAlgothimBackend().run()

def run_app(): app.run(debug=True, port=8000)


if __name__ == "__main__":
    algorithm_thread = threading.Thread(target=run_algorithm)
    app_thread = threading.Thread(target=run_app)
    algorithm_thread.start()
    app_thread.start()