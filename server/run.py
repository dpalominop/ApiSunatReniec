# -*- coding: utf-8 -*-

import os
from eve import Eve
from flask import request

# Heroku support: bind to PORT if defined, otherwise default to 5000.
if 'PORT' in os.environ:
    port = int(os.environ.get('PORT'))
    # use '0.0.0.0' to ensure your REST API is reachable from all your
    # network (and not only your computer).
    host = '0.0.0.0'
else:
    port = 5000
    host = '127.0.0.1'

app = Eve()

@app.route('/reniec', methods=['GET'])
def reniec():
    dni = request.args.get('dni', '')
    print dni
    return 'Hello Reniec!'

@app.route('/sunat', methods=['GET'])
def sunat():
    ruc = request.args.get('ruc', '')
    print ruc
    return 'Hello Sunat!'

if __name__ == '__main__':
    app.run(host=host, port=port)
