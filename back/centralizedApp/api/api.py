from flask_restful import Api
from back.centralizedApp.api.resource import *
from back.centralizedApp.algorithm import FinancialAlgothimBackend
from werkzeug.security import generate_password_hash, check_password_hash
from flask import jsonify
import jwt, datetime, uuid
from back.centralizedApp.api.config import db, app
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()
# Never put two Flask(__name__)
api = Api(app)

api.add_resource(CurrentPosition, '/api/current/', endpoint="current")
api.add_resource(PositionSpecificMarket, "/api/market/<string:market>", endpoint="specific_market")
api.add_resource(HistoricalPositions, "/api/historical/", endpoint="historical")
api.add_resource(ListAllMarkets, '/api/all_markets/', endpoint="all_markets")
# api.add_resource(DeleteASpecificPosition, '/delete/<int:id>', endpoint="deletePosition")



@app.route("/api/token")
def login():
    username = request.args.get("username")
    password = request.args.get("password")
    if username == str() or password == str():
        return {
            'error' : "Please provide credentials"
        },400
    user = User.query.filter_by(username=username).first()
    if not user:
        return {
            'error': "user not found"
        },401
    print(user.password_hash)
    if check_password_hash(user.password_hash, password):
        token = jwt.encode({'id': user.id, 'exp': datetime.datetime.utcnow()+datetime.timedelta(minutes=30)}, app.config["SECRET_KEY"])
        return jsonify(
            {
                "token" : token.decode("UTF-8"),
                "username" : user.username,
                "exp" : 30*60
            }
        )
    return {
        "error": "Incorrect credentials"     },401



def run_algorithm(): FinancialAlgothimBackend().run()

if __name__ == "__main__":
    try:
        db.create_all()
    except:
        pass
    # thread = threading.Thread(target=run_algorithm)
    # thread.start()
    hashed_password = generate_password_hash("matthieu", method="sha256")
    # user = User(
    #     id = str(uuid.uuid4()),
    #     username="matthieu",
    #     password_hash=hashed_password
    # )
    #
    # db.session.add(user)
    # db.session.commit()
    app.run(debug=False, port=8000)
