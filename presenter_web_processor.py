import asyncio
import json
import os
import shutil
import time
from pathlib import Path
from ai_presenter import Presenter
import logging
from logging.handlers import TimedRotatingFileHandler


class PresenterWebProcessor:
    def __init__(self, uploads_dir, outputs_dir, errors_dir, logs_dir):
        self.uploads: str = uploads_dir
        self.outputs: str = outputs_dir
        self.errors: str = errors_dir
        self.logs: str = logs_dir
        self.presenter = Presenter()
        Path(self.uploads).mkdir(parents=True, exist_ok=True)
        Path(self.outputs).mkdir(parents=True, exist_ok=True)
        Path(self.errors).mkdir(parents=True, exist_ok=True)
        Path(self.logs).mkdir(parents=True, exist_ok=True)
        handler = TimedRotatingFileHandler(
            os.path.join(self.logs, "presenter_processor.log"), when="midnight", interval=1, backupCount=5
        )
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger = logging.getLogger('presenter_processor')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def __call__(self):
        running: bool = True
        while running:
            self.logger.info("Scanning for files.")
            for file_name in os.listdir(self.uploads):
                self.logger.info("Found file " + file_name)
                file_path = os.path.join(self.uploads, file_name)
                json_file_name = f"{file_name}.json"
                json_file_path = os.path.join(self.outputs, json_file_name)
                try:
                    answer = asyncio.run(self.presenter.get_presentation_summery(file_path, 100))
                    with open(json_file_path, "w") as file:
                        file.write(json.encoder.JSONEncoder().encode(answer))
                    os.remove(file_path)
                    self.logger.info("Successfully processed " + file_name)
                except Presenter.PresenterError:
                    self.logger.error("Error processing file " + file_name)
                    shutil.move(file_path, os.path.join(self.errors, file_name))
            self.logger.info("Done scanning, sleeping for the next 10 seconds.")
            time.sleep(10)


def main() -> None:
    PresenterWebProcessor("uploads", "outputs", "errors", "logs")()


if __name__ == "__main__":
    main()
