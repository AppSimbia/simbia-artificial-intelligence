from flask import Flask, Blueprint
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)

#Registrando todos os blueprints no init do routes
import app.routes as routes
for name, bp in vars(routes).items():
    if isinstance(bp, Blueprint):
        prefix = f"/api/{bp.name}"
        app.register_blueprint(bp, url_prefix=prefix)
        
