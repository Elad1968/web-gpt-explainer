import json
from datetime import datetime
import requests


# A client class to interact with the API.
class Client:
    class Status:
        # Init the class with the response uid.
        def __init__(self, uid):
            self.uid = uid
            URL = f"http://127.0.0.1:5000/status/{uid}"
            response = requests.get(URL)
            if response.status_code != requests.codes.OK:
                raise RuntimeError("Error fetch")
            metadata = json.loads(response.text)
            self.status = metadata["status"]
            self.filename = metadata["filename"]
            self.timestamp = datetime.strptime(metadata["timestamp"], '%Y-%m-%d-%H-%M-%S')
            self.explanation = metadata["explanation"]

        # Check if the status of the uid is done.
        def is_done(self):
            return self.status == "Done"

    # Upload the file to the API and get a uid to check for it later.
    @staticmethod
    def upload(file_path):
        URL = 'http://127.0.0.1:5000/upload'
        with open(file_path, 'rb') as f:
            FILES = {'file': f}
            RESPONSE = requests.post(URL, files=FILES)
            return RESPONSE.json()["uid"]

    # Check the status of a uid.
    @staticmethod
    def status(uid):
        status = Client.Status(uid)
        if not status.is_done():
            raise RuntimeError(f"{status.filename} is not done yet.")
        return status
