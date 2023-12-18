import logging

from dejavu.recognize import FileRecognizer
from dejavu import Dejavu
import time
from urllib.request import urlopen
import os
import threading
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()
FINGERPRINT_MYSQL_HOST = os.getenv('FINGERPRINT_MYSQL_HOST')
FINGERPRINT_MYSQL_USER = os.getenv('FINGERPRINT_MYSQL_USER')
FINGERPRINT_MYSQL_PASSWORD = os.getenv('FINGERPRINT_MYSQL_PASSWORD')
FINGERPRINT_MYSQL_DB = os.getenv('FINGERPRINT_MYSQL_DB')

logger = logging.getLogger("Finger.py")


config = {
    "database": {
        "host": FINGERPRINT_MYSQL_HOST,
        "user": FINGERPRINT_MYSQL_USER,
        "password": FINGERPRINT_MYSQL_PASSWORD,
        "database": FINGERPRINT_MYSQL_DB
    },
}


def test(Url, Offset, Dauer, FingerThreshold):
    while True:
        try:
            djv = Dejavu(config)

            fname2 = "2_" + str(time.perf_counter())[2:] + ".wav"
            f2 = open(fname2, 'wb')
            fname3 = "3_" + str(time.perf_counter())[2:] + ".wav"
            f3 = open(fname3, 'wb')

            response = urlopen(Url, timeout=10.0)
            i = 3
            while True:
                start = time.time()
                while time.time() - start <= Dauer - Offset:
                    audio = response.read(1024)
                    f2.write(audio)
                    if start + Dauer - 2 * Offset < time.time():
                        f3.write(audio)
                f2.close()

                try:
                    if os.stat(fname2).st_size > 0:
                        finger2 = djv.recognize(FileRecognizer, fname2)
                        if finger2 and finger2["confidence"] > FingerThreshold:
                            logger.info(datetime.now().strftime("%H:%M:%S") + ": " + str(finger2))
                            info = finger2["song_name"].decode().split("_")
                            sender = info[0]
                            Typ = info[1]
                except Exception as e:
                    logger.error("Error " + str(e))

                os.remove(fname2)
                fname2 = str(i) + "_" + str(time.perf_counter())[2:] + ".wav"
                f2 = open(fname2, 'wb')
                i += 1

                while time.time() - start <= 2 * Dauer - Offset:
                    audio = response.read(1024)
                    f3.write(audio)
                    if start + 2 * Dauer - 2 * Offset < time.time():
                        f2.write(audio)
                f3.close()

                try:
                    if os.stat(fname3).st_size > 0:
                        finger3 = djv.recognize(FileRecognizer, fname3)
                        if finger3 and finger3["confidence"] > FingerThreshold:
                            logger.info(datetime.now().strftime("%H:%M:%S") + ": " + str(finger3))
                            info = finger3["song_name"].decode().split("_")
                            sender = info[0]
                            Typ = info[1]
                except Exception as e:
                    logger.error("Error " + str(e))

                os.remove(fname3)
                fname3 = str(i) + "_" + str(time.perf_counter())[2:] + ".wav"
                f3 = open(fname3, 'wb')
                i += 1

        except Exception as e:
            logger.error("Fingerprintthread crashed: " + str(e))
            time.sleep(10)




def StartFinger():
    djv = Dejavu(config)
    djv.fingerprint_directory("OriginalAudio", [".wav"])

    radios = [
        "https://f131.rndfnk.com/ard/wdr/1live/live/mp3/128/stream.mp3?aggregator=radio-de&cid=01FBRZTS1K1TCD4KA2YZ1ND8X3&sid=2ZgOD39nA4EtSY3oeiU1mg7NEqn&token=T3AJgSK9quR8fmsSqvUmAeKyjM0Xl_YULkvmCOCZ4Uc&tvf=KnSoVLnHoRdmMTMxLnJuZGZuay5jb20",
        "https://d121.rndfnk.com/ard/wdr/wdr2/rheinland/mp3/128/stream.mp3?cid=01FBS03TJ7KW307WSY5W0W4NYB&sid=2WfgdbO7GvnQL9AwD8vhvPZ9fs0&token=cz5XFBkPm158lD9VGL4JxM-2zzMfE_3qEd-sX_kdaAA&tvf=x6sCXJp9jRdkMTIxLnJuZGZuay5jb20",
        "https://d121.rndfnk.com/ard/br/br1/franken/mp3/128/stream.mp3?cid=01FCDXH5496KNWQ5HK18GG4HED&sid=2ZDBcNAOweP69799K4rCsFc3Jgw&token=AaURPm1j9atmzP6x_QnojyKUrDLXmpuME5vqVWX1ZI0&tvf=XJJyGEmbnhdkMTIxLnJuZGZuay5jb20"
              ]

    threads = [threading.Thread(target=test, args=(radio, 2, 8, 15))
               for radio in radios]

    for thread in threads:
        thread.start()

    return threads


if __name__ == '__main__':
    threads = StartFinger()
    for thread in threads:
        thread.join()