from flask import Flask
from flask_sock import Sock
import json
from json import JSONDecodeError
from simple_websocket import ConnectionClosed

from notify_client import start_notifier
from stream_request import stream_request

from db.database_functions import insert_new_connection, commit, rollback
from search_request import search_request, search_update_request

app = Flask(__name__)
sock = Sock(app)

connections = {}


@app.route("/")
def index():
    return "<p>Hier wird nur die API unter /api gehostet \\o/</p>"

@sock.route('/api')
def api(client):
    mapping = {
        'search_request': search_request,
        'search_update_request': search_update_request,
        'stream_request': stream_request,
    }
    global connections
    connection_id = insert_new_connection()
    connections[connection_id] = client

    commit()

    while True:
        raw = "<Failed>"
        try:
            # with transaction():
            raw = client.receive()
            data = json.loads(raw)
            print(f"got request '{data['type']}': {raw}")
            mapping[data['type']](client, connection_id, data)
            commit()

        except JSONDecodeError:
            print("Error: Request body is not json")
            rollback()

        except KeyError:
            print(f"Error: Request body has incorrect json structure: {raw}")
            rollback()

        except ConnectionClosed:
            print("Connection closed")
            return

        except Exception as e:
            print(f"########################\n#### Internal Server Error ####")
            rollback()
            # print(e)
            client.close()
            raise e
            # return

app.run(host="0.0.0.0")

notifier = start_notifier(connections)
notifier.join()

# close()
