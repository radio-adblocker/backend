import vlc
import json
import asyncio
import websockets
import time

address = "ws://185.233.107.253:5000/api"
# address = "ws://185.233.107.253:8080/api"
# address = "ws://127.0.0.1:8080/api"


def search_request(requested_updates=1):
    """
    Look up ServerAPI Documentation (Google Drive)
    @param requested_updates: Number of follow-up updates expected
    @return: json-string
    """
    return (json.dumps({
        'type': 'search_request',
        'requested_updates': requested_updates
    }))


def search_update_request(requested_updates=1):
    """
    Look up ServerAPI Documentation (Google Drive)
    @param requested_updates: Number of follow-up updates expected
    @return: json-string
    """
    return (json.dumps({
        'type': 'search_update_request',
        'requested_updates': requested_updates
    }))


def stream_request(preferred_radios=None, preferred_experience=None):
    """
    Look up ServerAPI Documentation (Google Drive)
    @param preferred_radios: One preferred radio or multiple radios
    @param preferred_experience: bool, preferred experience ads-news-music
    @return: json-string
    """
    return (json.dumps({
        'type': 'stream_request',
        'preferred_radios': preferred_radios,
        'preferred_experience': preferred_experience or {'ad': False, 'news': True, 'music': True, 'talk': True}
    }))


def format_radio(radio, with_padding=True):
    name = f"{radio['name']:<10}"
    if not with_padding:
        name = f"{radio['name']}"
    return f"({radio['id']}) {name}: {'(' + radio['status_label'] + ')':<10} {radio['current_interpret']} - {radio['currently_playing']}"


async def start_client():
    """
    Starts Client -> connect to server -> asks for radio -> play radio -> permanently polling for update
    @return: returns only on Error
    """
    async with websockets.connect(address) as ws:

        ##############################
        ##############################
        commit = stream_request(preferred_radios=[6, 8, 2])
        ##############################
        ##############################

        await ws.send(commit)
        print(f'Client sent: {commit}')

        instance = vlc.Instance()
        player = instance.media_player_new()

        url = ""

        commit = search_request(5)
        await ws.send(commit)
        print(f'Client sent: {commit}')

        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=300)
                print()
                print(f"Client received: {msg}")
                data2 = json.loads(msg)

                if data2["type"] == "search_update":
                    print("\n".join(map(format_radio, data2["radios"])))
                    if data2["remaining_updates"] <= 1:
                        commit = search_request(5)
                        await ws.send(commit)
                        print(f'Client sent: {commit}')

                elif data2["type"] == "radio_stream_event":
                    print(f"switching to (with buffer {data2['buffer']}):")
                    print(format_radio(data2['switch_to'], with_padding=False))

                    new_url = data2["switch_to"]["stream_url"]
                    if url == new_url:
                        print("nvm was actually an update of metadata")
                        continue

                    if url != "":
                        player.stop()

                    media = instance.media_new(new_url)
                    player.set_media(media)
                    player.play()

                    time.sleep(0.5)  # buffer
                    player.set_pause(1)  # buffer
                    time.sleep(data2["buffer"])  # buffer
                    player.play()  # buffer

                    url = new_url

                elif data2["type"] == "radio_update_event":
                    pass

                else:
                    print("Error: No matching function")
                    return

            except websockets.exceptions.ConnectionClosedOK:
                pass

if __name__ == '__main__':
    asyncio.run(start_client())

