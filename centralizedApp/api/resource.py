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
from centralizedApp.api.config import db
from datetime import datetime

# DB_URI = 'sqlite:///./position.db'
# Base = declarative_base()
# engine = create_engine(DB_URI)
# Base.metadata.drop_all(engine)
# Base.metadata.create_all(engine)
#
# Session = sessionmaker(bind=engine)
# Session.configure()
# db_session = Session()


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
        current_pos = Position.query.all()
        return current_pos, 200

class PositionSpecificMarket(Resource):

    @marshal_with(json_response)
    def get(self, market):
        specfic_market = Position.query.filter(Position.market==market)\
            .order_by(Position.id.desc()).limit(30).all()
        if not specfic_market:
            abort(400, message="{} isn't a valid parameter for this request or maybe no data was found".format(market))
        else:
            return specfic_market, 200
        

class PositionResultsPerDay(Resource):
    
    per_day = {
        'dayout_market' : fields.DateTime,
        'result_percent' : fields.Float
    }
    parser_day = reqparse.RequestParser()
    parser_day.add_argument('dayout_market')
    parser_day.add_argument('result_percent')

    @marshal_with(per_day)
    def get(self):
        per_day_data = Position.query.group_by(Position.dayout_market).limit(15).all()
        return per_day_data, 200


class HistoricalPositions(Resource):

    @marshal_with(json_response)
    def get(self):
        historical_positions = Position.query.filter(Position.dayout_market != None)\
            .order_by(Position.id.desc()).limit(30).all()
        return historical_positions, 200

