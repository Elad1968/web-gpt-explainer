import asyncio
import json
import sys
from typing import Generator
from presentation_helper import PresentationHelper
from chat_helper import ChatHelper
from pptx.presentation import Presentation
from openai import OpenAIError
import argparse


class Presenter:
    class PresenterError(Exception):
        def __init__(self, message: str):
            super().__init__(message)

    @staticmethod
    async def __call_chat(result: dict[int, str], query: str, slide_text: str, index: int, timeout: int) -> None:
        try:
            result[index] = await asyncio.wait_for(ChatHelper.send_prompt(query + slide_text), timeout=timeout)
        except asyncio.TimeoutError:
            result[index] = "Slide request timed out."
        except OpenAIError as exception:
            result[index] = str(exception)

    @staticmethod
    async def get_presentation_summery(presentation_path: str, request_timeout: int = 10) -> tuple[str, ...]:
        presentation: Presentation = PresentationHelper.get_presentation(presentation_path)
        slides_text: list[str] = PresentationHelper.get_all_text_from_presentation(presentation)
        query: str = "Please give a very short summery of this slide:\n"
        result: dict[int, str] = {}
        jobs: Generator = (Presenter.__call_chat(result, query, slide_text, index, request_timeout)
                           for index, slide_text in enumerate(slides_text))
        await asyncio.gather(*jobs)
        return tuple(result.values())


class CLI:
    @staticmethod
    def __save_as_json(path: str, answer: tuple[str, ...]):
        output_suffix: str = ".json"
        output_path: str = path[0: path.rfind('.')] + output_suffix
        try:
            with open(output_path, "w") as file:
                file.write(json.encoder.JSONEncoder().encode(answer))
        except IOError:
            raise Presenter.PresenterError("Failed to write json file.")

    def __init__(self, presentation_paths: list[str], timeout: int = 10):
        self.__timeout: int = timeout
        self.__presentation_paths: list[str] = presentation_paths

    async def __call__(self):
        for path in self.__presentation_paths:
            try:
                answer: tuple[str, ...] = await Presenter.get_presentation_summery(path, self.__timeout)
                self.__save_as_json(path, answer)
            except Exception as exception:
                print(exception, file=sys.stderr)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", "-t", type=int, help="Set the timeout value in seconds.")
    parser.add_argument(
        'presentations',
        metavar='Presentation',
        type=str,
        nargs='+',
        help='List of presentations to be summarised (at least one presentation required)'
    )
    try:
        args = parser.parse_args()
    except SystemExit:
        exit(-1)
    timeout = args.timeout if args.timeout else 100
    await CLI(args.presentations, timeout)()


if __name__ == "__main__":
    asyncio.run(main())
