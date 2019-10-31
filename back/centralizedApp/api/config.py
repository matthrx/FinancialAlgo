import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS


project_dir = os.path.dirname(os.path.abspath(__file__))
database_file = "sqlite:///{}".format(os.path.join(project_dir, "position.db"))

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = database_file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "PVO^;54B!ez6YiOdYhl1WeZHp-HXeN96"

db = SQLAlchemy(app)
db.create_all()