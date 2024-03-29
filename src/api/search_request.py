import json

from src.db.database_functions import get_connection, get_radio_by_query, update_search_remaining_updates
from src.db.db_helpers import NewTransaction, serialize
import logging

from src.error_handling.error_checkers import get_or_raise
from src.error_handling.error_classes import InternalError
from src.logging_config import configure_logging
configure_logging()

logger = logging.getLogger("search_request.py")


def search_request(client, connection_id, req):
    """
    Client requests to change connection preferences, gets search(_update) response
    @param client: specified client
    @param connection_id: specified connection
    @param req: connection information to be changed
    @return: -
    """

    # TODO add possibility to have filters

    requested_updates = get_or_raise(req, "requested_updates")

    with NewTransaction():
        update_search_remaining_updates(connection_id, requested_updates)
        response = search(connection_id)

    client.send(response)


def search(connection_id):
    """
    Searches DB for connection and its preferences
    @param connection_id: the specified connection
    @return: the connection information in json format
    """

    if connection_id is None:
        raise InternalError(logger, "search(): parameter connection_id can't be None")

    connection = get_connection(connection_id)
    if connection is None:
        raise InternalError(logger, "search(): Couldn't find connection in database")

    radios = get_radio_by_query()

    remaining_updates = update_search_remaining_updates(connection_id)

    # TODO: add possibility for advanced filters

    return json.dumps({
        'type': 'search_update',
        'radios': serialize(radios),
        'remaining_updates': remaining_updates
    }, default=str)


def search_update_request(client, connection_id, req):
    """
    Client requests to receive updates, gets search(_update) response if instant_update is enabled
    @param client: specified client
    @param connection_id: specified connection
    @param req: requested updates
    @return: -
    """

    connection = get_connection(connection_id)
    if connection is None:
        raise InternalError(logger, "search_update_request(): Couldn't find connection in database")

    instant_update = connection.search_remaining_update <= 0
    remaining_updates = get_or_raise(req, 'requested_updates')

    update_search_remaining_updates(connection_id, remaining_updates)

    if instant_update:
        client.send(search(connection_id))
