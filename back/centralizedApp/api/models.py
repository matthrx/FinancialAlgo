from back.centralizedApp.api.config import db

from .config import app

class Position(db.Model):
    __tablename__ = "position"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    position_type = db.Column(db.String)
    market = db.Column(db.String(6))
    stepin_market = db.Column(db.DateTime)
    dayout_market = db.Column(db.String, default= None)
    timeout_market = db.Column(db.String, default=None)
    stepin_value = db.Column(db.Float(precision='3,8'))
    result_percent = db.Column(db.Float(precision='2,4'), default=0.0)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(32), primary_key = True)
    username = db.Column(db.String(32), index = True)
    password_hash = db.Column(db.String(128))

