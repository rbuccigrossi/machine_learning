"""
chatgpt.py

This module provides an easy interface to maintain a chat session with
ChatGPT, by managing the chat history and environment setup.
"""

import os
import openai

class ChatGPT:
    """
    A class to manage interactions with OpenAI's ChatGPT.

    Attributes
    ----------
    api_key : str
        OpenAI API key obtained from environment variable.
    message_history : list
        List to keep track of the chat history.

    Methods
    -------
    add_user_message(content):
        Adds a user message to the message history.
    add_assistant_message(content):
        Adds an assistant message to the message history.
    chat(message, model="gpt-3.5-turbo"):
        Sends a message to the GPT model and returns its response.
    clear_messages():
        Clears the chat history.
    """

    def __init__(self):
        """
        Constructs necessary attributes for the ChatGPT object.
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key is None:
            raise Exception("OPENAI_API_KEY is not set in the environment variables.")
        
        openai.api_key = self.api_key
        self.message_history = []

    def add_user_message(self, content):
        """
        Adds a user message to the message history.

        Parameters
        ----------
        content : str
            The message from the user.
        """
        self.message_history.append({'role': 'user', 'content': content})

    def add_assistant_message(self, content):
        """
        Adds a GPT message to the message history.

        Parameters
        ----------
        content : str
            The message from the GPT model.
        """
        self.message_history.append({'role': 'assistant', 'content': content})

    def chat(self, message, model="gpt-3.5-turbo"):
        """
        Sends a message to the GPT model and returns its response.

        Parameters
        ----------
        message : str
            The message to be sent to the GPT model.
        model : str, optional
            The GPT model to be used (default is "gpt-3.5-turbo").

        Returns
        -------
        str
            The response from the GPT model.
        """
        self.add_user_message(message)
        response = openai.ChatCompletion.create(
            model=model,
            messages=self.message_history,
        )
        gpt_response = response['choices'][0]['message']['content']
        self.add_assistant_message(gpt_response)
        return gpt_response

    def clear_messages(self):
        """
        Clears the chat history.
        """
        self.message_history = []
