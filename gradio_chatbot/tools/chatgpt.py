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

    Methods
    -------
    add_user_message(content, message_history):
        Adds a user message to the message history.
    add_assistant_message(content, message_history):
        Adds an assistant message to the message history.
    chat(message, message_history, model="gpt-3.5-turbo"):
        Sends a message to the GPT model and returns its response.
    clear_messages(message_history):
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

    def add_user_message(self, content, message_history):
        """
        Adds a user message to the message history.

        Parameters
        ----------
        content : str
            The message from the user.
        message_history : list
            The message history list
        """
        message_history.append({'role': 'user', 'content': content})

    def add_assistant_message(self, content, message_history):
        """
        Adds a GPT message to the message history.

        Parameters
        ----------
        content : str
            The message from the GPT model.
        message_history : list
            The message history list
        """
        message_history.append({'role': 'assistant', 'content': content})

    def chat(self, message, message_history, model="gpt-3.5-turbo"):
        """
        Sends a message to the GPT model and returns its response.

        Parameters
        ----------
        message : str
            The message to be sent to the GPT model.
        message_history : list
            The message history list
        model : str, optional
            The GPT model to be used (default is "gpt-3.5-turbo").

        Returns
        -------
        str
            The response from the GPT model.
        """
        self.add_user_message(message, message_history)
        while True:
            # Try the query
            try:
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=message_history,
                )
                break
            except openai.error.InvalidRequestError as e:
                # Our response was probably too long so remove the first one
                if (len(message_history) < 2):
                    raise e
                else:
                    message_history.pop(0)
        gpt_response = response['choices'][0]['message']['content']
        self.add_assistant_message(gpt_response, message_history)
        return gpt_response

    def clear_messages(self, message_history):
        """
        Clears the chat history.

        Parameters
        ----------
        message_history : list
            The message history list
        """
        message_history.clear()
