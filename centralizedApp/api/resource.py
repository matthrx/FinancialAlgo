from centralizedApp.api.models import Position
from sqlalchemy import func
from flask_restful import reqparse
from flask_restful import abort
from flask_restful import fields
from flask_restful import Resource
from flask_restful import marshal_with
from sqlalchemy import create_engine
from  sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


DB_URI = 'sqlite:///./main.db'
Base = declarative_base()
engine = create_engine(DB_URI)
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
Session.configure()
db_session = Session()

json_response = {
    "market" : fields.String,
    "position_type" : fields.String,
    "stepin_market" : fields.DateTime,
    "stepin_value" : fields.Float,
    "stepout_market": fields.DateTime,
    "result_percent" : fields.Float
}

parser_response = reqparse.RequestParser()
parser_response.add_argument('market')
parser_response.add_argument('position_type')
parser_response.add_argument('stepin_market')
parser_response.add_argument('stepin_value')
parser_response.add_argument('stepout_market')
parser_response.add_argument('result_percent')

class CurrentPosition(Resource):

    @marshal_with(json_response) # necessary to data
    def get(self):
        current_pos = db_session.query(Position).order(Position.stepin_market.desc()).all()
        return current_pos, 200

class PositionSpecificMarket(Resource):

    @marshal_with(json_response)
    def get(self, market):
        specfic_market = db_session.query(Position).filter(Position.market==market)\
            .order(Position.stepin_market.desc()).limit(30).all()
        if not specfic_market:
            abort(400, message="{} isn't a valid parameter for this request".format(market))
        else:
            return specfic_market, 200
        

class PositionResultsPerDay(Resource):
    
    per_day = {
        'day' : fields.DateTime,
        'result_percent' : fields.Float
    }
    parser_day = reqparse.RequestParser()
    parser_day.add_argument('day')
    parser_day.add_argument('result_percent')

    @marshal_with(per_day)
    def get(self):
        per_day_data = db_session.query(Position, func(sum(Position.result_percent))).group_by(Position.stepout_market.day)\
            .limit(15).all()
        return per_day_data, 200


class HistoricalPositions(Resource):

    @marshal_with(json_response)
    def get(self):
        historical_positions = db_session.query(Position).filter(Position.stepout_market is not None)\
            .order_by(Position.stepout_market.desc()).limit(15).all()
        return historical_positions, 200

