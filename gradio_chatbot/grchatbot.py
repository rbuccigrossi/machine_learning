import gradio as gr
import openai
import os 
import json

# Get the OPEN_API_KEY from the environment
openai.api_key = os.getenv("OPENAI_API_KEY") or "OPENAI_API_KEY"
# print(openai.Engine.list())

# Global variable to hold the messages so far
messages = []

def add_text(history, text):
    global messages  #message[list] is defined globally
    history = history + [(text,'')]
    messages = messages + [{"role":'user', 'content': text}]
    return history, ""

def generate_response(history, model):
    global messages

    try:
        response = openai.ChatCompletion.create(
            model = model,
            messages=messages,
            temperature=0.2,
        )
        
        response_msg = response.choices[0].message.content
        messages = messages + [{"role":'assistant', 'content': response_msg}]
        
        history[-1][1] += response_msg
        yield history
    except Exception as e:
        history[-1][1] += "We received an error: " + str(e);
        yield history
    
#    for char in response_msg:
#        history[-1][1] += char
#        yield history


with gr.Blocks() as demo:
    
    radio = gr.Radio(value='gpt-3.5-turbo', choices=['gpt-3.5-turbo','gpt-4'], label='models')
#    radio = gr.Radio(value='gpt-3.5-turbo', choices=['gpt-3.5-turbo'], label='models')
    chatbot = gr.Chatbot(value=[], elem_id="chatbot").style(height=650)
    with gr.Row():
        with gr.Column(scale=1.00):
            txt = gr.Textbox(
                show_label=False,
                placeholder="Enter text and press enter",
            ).style(container=False) 

    txt.submit(add_text, [chatbot, txt], [chatbot, txt], queue=False).then(
            generate_response, inputs =[chatbot, radio],outputs = chatbot)

# NOTE: Set GRADIO_SERVER_NAME
demo.queue().launch(share=False)
