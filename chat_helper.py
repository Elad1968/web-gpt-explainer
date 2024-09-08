import openai


class ChatHelper:
    class Error(Exception):
        def __init__(self, message: str):
            super().__init__(message)

    @staticmethod
    async def send_prompt(prompt: str) -> str:
        # Note that the constructor is empty because the key is loaded from env.
        client: openai.AsyncOpenAI = openai.AsyncOpenAI()
        try:
            completion: openai.types.chat.chat_completion.ChatCompletion = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "user",
                    "content": prompt,
                }]
            )
            if not completion.choices:
                raise ChatHelper.Error("ChatGPT did not return any choice.")
            return completion.choices[0].message.content
        except openai.OpenAIError:
            raise ChatHelper.Error("ChatGPT error.")
