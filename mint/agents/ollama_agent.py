from .openai_lm_agent import OpenAILMAgent
import logging
import traceback
from mint.datatypes import Action
import backoff
import ollama

LOGGER = logging.getLogger("MINT")
# REMEMBER to RUN ALL MODELS


class OllamaAgent(OpenAILMAgent):
    """Inference for open-sourced models with a unified interface with OpenAI's API."""

    def __init__(self, config):
        super().__init__(config)
        self.stop_words = [
            "\nObservation:",
            "\nExpert feedback:",
            "\nTask:",
            "\n---",
            "\nHuman:",
        ]

    def format_prompt(self, messages):
        """Format messages into a prompt for the model."""
        prompt = ""
        for message in messages:
            if message["role"] == "user":
                prompt += f"\n\nHuman: {message['content']}"
            elif message["role"] == "assistant":
                prompt += f"\n\nAssistant: {message['content']}"
        prompt += "\n\nAssistant:"
        return prompt

    def call_lm(self, messages):
        if self.config.get("add_system_message", False):
            messages = self.add_system_message(messages)
            assert messages[0]["role"] == "system"
            # system msg will be formatted by vllm and fastchat, so no need to format here
        else:
            # simply ignore chat messages as it may cause issue for some served models
            pass

        if self.config["chat_mode"]:
            response = ollama.chat(
                model=self.config["model_name"], 
                messages=messages,
                options={
                    'max_tokens': self.config.get("max_tokens", 512),
                    'temperature': self.config.get("temperature", 0),
                    'stop': self.stop_words
                }
            )
            resp_str = response.message.content
        else:
            prompt = self.format_prompt(messages)
            response = ollama.generate(
                model=self.config["model_name"], 
                prompt=prompt,
                options={
                    'max_tokens': self.config.get("max_tokens", 512),
                    'temperature': self.config.get("temperature", 0),
                    'stop': self.stop_words
                }
            )
            resp_str = response.message.content

        usage = {
            'prompt' : response.prompt_eval_count,
            'completion' : response.eval_count
        }

        resp_str = resp_str.rstrip()  # remove trailing spaces (usually caused by llama)
        return resp_str, usage
