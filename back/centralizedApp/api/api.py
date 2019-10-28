from flask_restful import Api
from back.centralizedApp.api.resource import *
from back.centralizedApp.algorithm import FinancialAlgothimBackend
import threading
from back.centralizedApp.api.config import db, app

# Never put two Flask(__name__)
api = Api(app)

api.add_resource(CurrentPosition, '/current/', endpoint="current")
api.add_resource(PositionResultsPerDay, '/day/', endpoint="per_day")
api.add_resource(PositionSpecificMarket, "/market/<string:market>", endpoint="specific_market")
api.add_resource(HistoricalPositions, "/historical/", endpoint="historical")
api.add_resource(ListAllMarkets, '/all_markets/', endpoint="all_markets")
# api.add_resource(DeleteASpecificPosition, '/delete/<int:id>', endpoint="deletePosition")

def run_algorithm(): FinancialAlgothimBackend().run()

if __name__ == "__main__":
    try:
        db.create_all()
    except:
        pass
    # thread = threading.Thread(target=run_algorithm)
    # thread.start()
    # import datetime
    # p = Position(
    #     market="EURGBP",
    #     stepin_value=1.25,
    #     stepin_market= datetime.datetime.now(),
    #     position_type='S'
    #
    # )
    # db.session.add(p)
    # db.session.commit()
    app.run(debug=False, port=8000)
