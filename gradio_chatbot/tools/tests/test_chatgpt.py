import os
import pytest
import openai
from unittest.mock import patch
from tools.chatgpt import ChatGPT

@patch.object(openai.ChatCompletion, 'create')
def test_chat(mock_create):
    # Mock the response from OpenAI
    mock_create.return_value = {
        'choices': [{
            'message': {
                'content': 'Hello, user!'
            }
        }]
    }

    # NOTE: OPENAI_API_KEY must be valid for testing
    # os.environ["OPENAI_API_KEY"] = "test-api-key"

    chatgpt = ChatGPT()
    response = chatgpt.chat("Hello, GPT!")

    assert response == "Hello, user!"
    assert len(chatgpt.message_history) == 2
    assert chatgpt.message_history[-1]['content'] == "Hello, user!"
    assert chatgpt.message_history[-1]['role'] == 'assistant'

def test_clear_messages():
    chatgpt = ChatGPT()
    chatgpt.chat("Hello, GPT!")
    chatgpt.clear_messages()

    assert len(chatgpt.message_history) == 0

def test_no_api_key():
    # Remove the API key from environment variables
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]

    with pytest.raises(Exception) as e_info:
        chatgpt = ChatGPT()
