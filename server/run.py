# -*- coding: utf-8 -*-

import os
from eve import Eve
from flask import request,jsonify
from utils import getValue
from settings import DOMAIN

SETTINGS = {
    'DOMAIN': DOMAIN,
#    'SQLALCHEMY_DATABASE_URI': SQLALCHEMY_DATABASE_URI,
#    'DEBUG': DEBUG,
}

# Heroku support: bind to PORT if defined, otherwise default to 5000.
if 'PORT' in os.environ:
    port = int(os.environ.get('PORT'))
    # use '0.0.0.0' to ensure your REST API is reachable from all your
    # network (and not only your computer).
    host = '0.0.0.0'
else:
    port = 80
    host = '0.0.0.0'

app = Eve(settings=SETTINGS)

@app.route('/reniec', methods=['GET'])
def reniec():
    dni = request.args.get('dni', '')
    resp = getValue('dni',dni)
    return jsonify(resp)

@app.route('/sunat', methods=['GET'])
def sunat():
    ruc = request.args.get('ruc', '')
    resp = getValue('ruc',ruc)
    return jsonify(resp)

if __name__ == '__main__':
    app.run(host=host, port=port)
