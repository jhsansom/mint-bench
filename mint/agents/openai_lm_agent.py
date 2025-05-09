from .base import LMAgent
import openai
import logging
import traceback
from mint.datatypes import Action
import backoff

LOGGER = logging.getLogger("MINT")


class OpenAILMAgent(LMAgent):
    def __init__(self, config):
        super().__init__(config)
        assert "model_name" in config.keys()

    @backoff.on_exception(
        backoff.fibo,
        # https://platform.openai.com/docs/guides/error-codes/python-library-error-types
        (
            openai.APIError,
            openai.Timeout,
            openai.RateLimitError,
            openai.APIConnectionError,
        ),
    )
    def call_lm(self, messages):
        # Prepend the prompt with the system message
        response = openai.ChatCompletion.create(
            model=self.config["model_name"],
            messages=messages,
            max_tokens=self.config.get("max_tokens", 512),
            temperature=self.config.get("temperature", 0),
            stop=self.stop_words,
        )
        return response.choices[0].message["content"], response["usage"]

    def act(self, state):
        messages = state.history
        #try:
        lm_output, token_usage = self.call_lm(messages)
        state.token_counter['prompt_tokens'] += token_usage.prompt_tokens
        state.token_counter['completion_tokens'] += token_usage.completion_tokens
        state.token_counter['total_tokens'] += token_usage.total_tokens
        action = self.lm_output_to_action(lm_output)
        return action
        #except openai.InvalidRequestError:  # mostly due to model context window limit
        #    tb = traceback.format_exc()
        #    return Action(f"", False, error=f"InvalidRequestError\n{tb}")
        # except Exception as e:
        #     tb = traceback.format_exc()
        #     return Action(f"", False, error=f"Unknown error\n{tb}")
