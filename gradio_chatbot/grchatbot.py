import gradio as gr
import openai
import pinecone
import os 
import json

from tools.chatgpt import ChatGPT

# Connect to OpenAI ChatGPT (use OPENAI_API_KEY from environment)
chatgpt = ChatGPT()

# Connect to Pinecone
api_key = os.getenv("PINECONE_API_KEY") or "PINECONE_API_KEY"
# find your environment next to the api key in pinecone console
env = os.getenv("PINECONE_ENVIRONMENT") or "PINECONE_ENVIRONMENT"
pinecone.init(api_key=api_key, enviroment=env)
print(pinecone.whoami())

def accept_user_input(history, text):
    # Output the user side of the dialog
    history = history + [[text,None]]
    # Return thse history to display and clear the message box
    return history, ""

def generate_response(history, model):
    # Grab the user input from the history
    text = history[-1][0];
    try:
        # Now call the chatbot to get the response
        response = chatgpt.chat(text, model)
        # Update the chatbot's response
        history[-1][1] = response
        return history
    except Exception as e:
        # Upon error, output the error as the response
        history[-1][1] = "We received an error: " + str(e)
        return history

with gr.Blocks() as demo:
    
    radio = gr.Radio(value='gpt-3.5-turbo', choices=['gpt-3.5-turbo','gpt-4'], label='models')
    chatbot = gr.Chatbot(value=[], elem_id="chatbot").style(height=650)
    with gr.Row():
        with gr.Column(scale=1.00):
            txt = gr.Textbox(
                show_label=False,
                placeholder="Enter text and press enter",
            ).style(container=False) 

    txt.submit(accept_user_input, [chatbot, txt], [chatbot, txt]).then(
        generate_response, [chatbot, radio], chatbot)

# NOTE: Set GRADIO_SERVER_NAME
demo.queue().launch(share=False)
