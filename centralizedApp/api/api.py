from flask import Flask
from flask_restful import Api
from centralizedApp.api.resource import *
from centralizedApp.algorithm import FinancialAlgothimBackend
import threading
from centralizedApp.api.config import db, app

# Never put two Flask(__name__)
api = Api(app)

api.add_resource(CurrentPosition, '/current/', endpoint="current")
api.add_resource(PositionResultsPerDay, '/day/', endpoint="per_day")
api.add_resource(PositionSpecificMarket, "/market/<string:market>", endpoint="specific_market")
api.add_resource(HistoricalPositions, "/historical/", endpoint="historical")

def run_algorithm(): FinancialAlgothimBackend().run()

if __name__ == "__main__":
    try:
        db.create_all()
    except:
        pass
    threading.Thread(target=run_algorithm).start()
    app.run(debug=True, port=8000)
