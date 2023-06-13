import gradio as gr
import pinecone
import os 
import json

from tools.chatgpt import ChatGPT
from tools.pinecone import PineconeManager

# Connect to OpenAI ChatGPT (use OPENAI_API_KEY from environment)
chatgpt = ChatGPT()

# Connect to Pinecone
docdatabase = PineconeManager()

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

def add_document(lib_upload):
    filename = os.path.basename(lib_upload.name)
    if (filename in docdatabase.get_document_list()):
        return (None, "File already exists.")
    # Read the file
    with open(lib_upload.name,'r') as file:
        text = file.read()
    # Unlink the file
    os.remove(lib_upload.name)
    # Now insert the file into pinecone
    try:
        num_sections = docdatabase.add_document(filename, text)
    except Exception as e:
        return (None, "We received an error: " + str(e))
    return (gr.Dropdown.update(choices=docdatabase.get_document_list(), value=filename),
            f"File {filename} added, split into {num_sections} sections.")

def remove_document(filename):
    if (filename == None) or (filename == ""):
        return (None, "Please select a file.")
    try:
        num_sections = docdatabase.remove_document(filename)
    except Exception as e:
        return (None, "We received an error: " + str(e))
    return (gr.Dropdown.update(choices=docdatabase.get_document_list(), value=""),
            f"File {filename} with {num_sections} sections removed.")

    
with gr.Blocks(css="footer {visibility: hidden}", title="Chatbot Application") as demo:
    
    with gr.Tab("Chat"):
        radio = gr.Radio(value='gpt-3.5-turbo', choices=['gpt-3.5-turbo','gpt-3.5-turbo-16k','gpt-4'], label='models')
        chatbot = gr.Chatbot(value=[], elem_id="chatbot").style(height=650)
        with gr.Row():
            with gr.Column(scale=1.00):
                txt = gr.Textbox(
                    show_label=False,
                    placeholder="Enter text and press enter",
                ).style(container=False)
    with gr.Tab("Library"):
        with gr.Row(variant="panel"):
            with gr.Column():
                lib_doc_list = gr.Dropdown(docdatabase.get_document_list(),
                                           label='Select file to delete',
                                           interactive=True)
                lib_delete_button = gr.Button("Delete")
        with gr.Row():
            lib_upload = gr.UploadButton(label='Upload a new file', file_types=["text"])
        with gr.Row():
            lib_status = gr.Markdown()

    txt.submit(accept_user_input, [chatbot, txt], [chatbot, txt]).then(
        generate_response, [chatbot, radio], chatbot)
    lib_delete_button.click(remove_document, [lib_doc_list], [lib_doc_list, lib_status])
    lib_upload.upload(add_document, [lib_upload], [lib_doc_list, lib_status])

# NOTE: Set GRADIO_SERVER_NAME
demo.queue().launch(share=False)
