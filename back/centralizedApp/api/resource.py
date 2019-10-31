from back.centralizedApp.api.models import Position, User
from back.centralizedApp.api.config import app
from functools import wraps
from flask_restful import reqparse
from flask_restful import abort
from flask_restful import fields
from flask_restful import Resource
from flask_restful import marshal_with
from flask import request
import jwt
from sqlalchemy import func


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
    "id" : fields.Integer,
    "market" : fields.String,
    "position_type" : fields.String,
    "stepin_market" : fields.DateTime,
    "stepin_value" : fields.Float,
    "dayout_market": fields.String,
    "timeout_market": fields.String,
    "result_percent" : fields.Float
}

parser_response = reqparse.RequestParser()
parser_response.add_argument("id")
parser_response.add_argument('market')
parser_response.add_argument('position_type')
parser_response.add_argument('stepin_market')
parser_response.add_argument('stepin_value')
parser_response.add_argument('dayout_market')
parser_response.add_argument('timeout_market')
parser_response.add_argument('result_percent')


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        print(request.headers);
        if 'x-access-token' in request.headers:
            token = request.headers["x-access-token"]
            print(token)
            if not token:
                return {"error" : "Token is missing"},401
            try:
                data = jwt.decode(token, app.config["SECRET_KEY"])
                print(data)
                _ = User.query.filter_by(id=data['id']).first()
            except:
                return {"error" : "Token not found"}, 401

            return f(*args, **kwargs)
        else:
            return {"error" :"Not appropriate headers"}, 401

    return decorated


class CurrentPosition(Resource):

    @token_required
    @marshal_with(json_response) # necessary to data
    def get(self):
        current_pos = Position.query.filter_by(timeout_market=None).all()
        return current_pos, 200

class PositionSpecificMarket(Resource):

    @token_required
    @marshal_with(json_response)
    def get(self, market):
        specfic_market = Position.query.filter(Position.market==market)\
            .order_by(Position.id.desc()).limit(15).all()
        if not specfic_market:
            abort(400, message="{} isn't a valid parameter for this request or maybe no data was found".format(market))
        else:
            return specfic_market, 200


class HistoricalPositions(Resource):

    @token_required
    @marshal_with(json_response)
    def get(self):
        historical_positions = Position.query.filter(Position.dayout_market != None)\
            .order_by(Position.id.desc()).limit(30).all()
        return historical_positions, 200

#
# class DeleteASpecificPosition(Resource):
#
#     def delete(self,id):
#         Position.query.filter_by(id=id).delete()
#         db.session.commit()
#         return Response(status=200)

class ListAllMarkets(Resource):
    @token_required
    def get(self):
        all_markets = [p.market for p in Position.query.group_by(Position.market).all()]
        return all_markets, 200

