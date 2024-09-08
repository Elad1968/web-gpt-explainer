import time

import pytest
from ai_presenter import CLI
import os

from client import Client


class TestPresenter:
    @pytest.fixture(autouse=True)
    def setup(self):
        pass

    @pytest.mark.asyncio
    async def test_output_file_generates(self):
        await CLI(["a.pptx"], 100)()
        assert os.path.exists("a.json")
        with open("a.json", "r") as file:
            text = file.read()
            assert text[0] == '[' and text[-1] == ']'


class TestWebAPI:
    @pytest.fixture(autouse=True)
    def setup(self):
        pass

    def test_web_api(self):
        uid = Client.upload("a.pptx")
        still = True
        while still:
            try:
                status = Client.status(uid)
                assert status.status == "Done"
                assert status.filename == "a.pptx"
                assert status.timestamp
                assert status.explanation
                still = False
            except RuntimeError:
                time.sleep(1)


if __name__ == "__main__":
    pytest.main()
