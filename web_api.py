import datetime
import json
import os.path
import uuid
from pathlib import Path
from uuid import UUID
import requests.status_codes
from flask import Flask, request, jsonify, Response
from werkzeug.datastructures import FileStorage
import logging
from logging.handlers import TimedRotatingFileHandler


class PresenterWebAPI:
    def __init__(self, name: str, uploads_dir: str, outputs_dir: str, errors_dir: str, logs_dir: str):
        self.app: Flask = Flask(name)
        self.uploads: str = uploads_dir
        self.outputs: str = outputs_dir
        self.errors: str = errors_dir
        self.logs: str = logs_dir
        Path(self.uploads).mkdir(parents=True, exist_ok=True)
        Path(self.outputs).mkdir(parents=True, exist_ok=True)
        Path(self.errors).mkdir(parents=True, exist_ok=True)
        Path(self.logs).mkdir(parents=True, exist_ok=True)
        handler = TimedRotatingFileHandler(
            os.path.join(self.logs, "web_api.log"), when="midnight", interval=1, backupCount=5
        )
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.app.logger.addHandler(handler)
        self.app.logger.setLevel(logging.INFO)
        self.app.add_url_rule("/upload", "upload-presentation", self.upload_presentation, methods=["POST"])
        self.app.add_url_rule("/status/<uid_str>", "get_status", self.get_status, methods=["GET"])

    def __call__(self, debug) -> None:
        self.app.run(debug=debug)

    @staticmethod
    def gen_filename(file_name: str, uid: UUID) -> str:
        time: str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        return f"{time}_{uid}_{file_name}"

    def upload_presentation(self) -> tuple[Response, int]:
        if "file" not in request.files:
            self.app.logger.info("Upload request received without a file attached.")
            return jsonify({"error": "No file detected."}), requests.codes.BAD_REQUEST
        file: FileStorage = request.files["file"]
        if file.filename == "":
            self.app.logger.info("Upload Request received without a selected file.")
            return jsonify({"error": "No file selected."}), requests.codes.BAD_REQUEST
        uid: UUID = uuid.uuid4()
        saved_file_name: str = self.gen_filename(file.filename, uid)
        saved_file_path: str = os.path.join(self.uploads, saved_file_name)
        file.save(saved_file_path)
        self.app.logger.info("Saved uploaded file " + saved_file_name)
        return jsonify({"uid": uid}), requests.codes.OK

    def get_status(self, uid_str: str) -> tuple[Response, int]:
        if not uid_str:
            self.app.logger.info("Status request received without a uid.")
            return jsonify({"error": "Did not get a UID."}), requests.codes.BAD_REQUEST
        metadata = {
            "status": "Not Found",
            "filename": None,
            "timestamp": None,
            "explanation": None
        }
        uploads = [file_name for file_name in os.listdir(self.uploads) if file_name.split('_')[1] == uid_str]
        outputs = [file_name for file_name in os.listdir(self.outputs) if file_name.split('_')[1] == uid_str]
        errors = [file_name for file_name in os.listdir(self.errors) if file_name.split('_')[1] == uid_str]
        if outputs:
            self.app.logger.info("Status request found output file " + outputs[0])
            metadata["status"] = "Done"
            split = outputs[0].split("_")
            metadata["filename"] = split[2].rsplit('.', 1)[0]
            metadata["timestamp"] = split[0]
            with open(os.path.join(self.outputs, outputs[0]), "r") as file:
                json_file = json.load(file)
                metadata["explanation"] = json_file
        elif uploads:
            self.app.logger.info("Status request found uploaded file " + uploads[0])
            metadata["status"] = "Pending"
            split = uploads[0].split("_")
            metadata["filename"] = split[2]
            metadata["timestamp"] = split[0]
        elif errors:
            self.app.logger.info("Status request found error file " + errors[0])
            metadata["status"] = "Error"
            split = errors[0].split("_")
            metadata["filename"] = split[2]
            metadata["timestamp"] = split[0]
        else:
            self.app.logger.warning("Status request didn't find a file for uid " + uid_str)
            return jsonify(metadata), requests.codes.NOT_FOUND
        self.app.logger.info("Status request completed successfully.")
        return jsonify(metadata), requests.codes.OK


def main() -> None:
    PresenterWebAPI("Presenter_Web_API", "uploads", "outputs", "errors", "logs")(True)


if __name__ == "__main__":
    main()
