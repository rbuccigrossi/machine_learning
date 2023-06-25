import gradio as gr
import pinecone
import os 
import json
import traceback

from tools.chatgpt import ChatGPT
from tools.pinecone import PineconeManager

# Connect to OpenAI ChatGPT (use OPENAI_API_KEY from environment)
chatgpt = ChatGPT()

# Connect to Pinecone
docdatabase = PineconeManager()

def clear_chat():
    chatgpt.clear_messages()
    return ([])

def generate_chat_response(history, prompt, model):
    if (not(prompt)):
        newhistory = history + [[prompt, f"Please enter a prompt"]]
        return (newhistory, None)
    try:
        # Now call the chatbot to get the response
        response = chatgpt.chat(prompt, model)
        # Update the chatbot's response
        newhistory = history + [[prompt, response]]
        return (newhistory, "")
    except Exception as e:
        # Upon error, output the error as the response
        newhistory = history + [[prompt, f"We received an error: {str(e)}"]]
        print(traceback.format_exc())
        return (newhistory, None)

def document_lookup_chat(history, search, top_n, prompt, model):
    if (not(prompt)):
        newhistory = history + [[prompt, f"Please enter a prompt"]]
        yield (newhistory, None, None)
        return
    # If search is empty, then use the prompt for the search
    if (not(search)):
        search = prompt
    try:
        # Update status for search
        newhistory = history + [[prompt, f"Searching for {top_n} documents with '{search}...'"]]
        yield (newhistory, None, None)
        # Conduct search
        results = docdatabase.query_index(search, top_n)
        newhistory = history + [[prompt, f"We found {len(results['matches'])} hits. Now executing chat prompt...'"]]
        yield (newhistory, None, None)
        chat_search = "The following are a series of document sections for a request below\n\n"
        for r in results['matches']:
            chat_search += (
                "Document Id: " + r['id'] + "\n\n" +
                r['metadata']['text'] + "\n\n"
            )
        chat_search += (
            "Answer the request based upon the above document sections. " +
            "If the answer is not clear from the source, state 'I cannot answer " +
            "based upon the documents provided.'\n\n " +
            "Reqeust: " + prompt
        )
        # Now call the chatbot to get the response
        response = chatgpt.chat(chat_search, model)
        newhistory = history + [[prompt, response]]
        yield (newhistory, "", "")
    except Exception as e:
        newhistory = history + [[prompt, f"We received an error {str(type(e))}: {str(e)}"]]
        print(traceback.format_exc())
        yield (newhistory, None, None)
        
    
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
        with gr.Row():
            with gr.Column(scale=100):
                radio = gr.Radio(value='gpt-3.5-turbo', show_label=False, container=False,
                                 choices=['gpt-3.5-turbo','gpt-3.5-turbo-16k','gpt-4'])
            with gr.Column(scale=2, min_width=110):
                clear_chat_button = gr.Button("Clear Chat")
        chatbot = gr.Chatbot(value=[], elem_id="chatbot").style(height=500)
        with gr.Tab("Normal Chat"):
            with gr.Row():
                with gr.Column(scale=100):
                    nc_prompt = gr.Textbox(
                        show_label=False,
                        placeholder="Enter prompt and press enter",
                    ).style(container=False)
                with gr.Column(scale=2, min_width=110):
                    nc_submit = gr.Button("Submit")
        with gr.Tab("Chat w/ Document Lookup"):
            with gr.Row():
                with gr.Column(scale=100):
                    dl_search = gr.Textbox(
                        show_label=False,
                        placeholder="Search text for documents (leave blank to use prompt for search)",
                    ).style(container=False)
                with gr.Column(scale=1, min_width=40):
                    gr.Markdown("   Top N:")
                with gr.Column(scale=1, min_width=50):
                    dl_top_n = gr.Number(show_label=False,
                                         value=5).style(container=False)
            with gr.Row():
                with gr.Column(scale=100):
                    dl_prompt = gr.Textbox(
                        show_label=False,
                        placeholder="Enter prompt and press enter",
                    ).style(container=False)
                with gr.Column(scale=2, min_width=110):
                    dl_submit = gr.Button("Submit")
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

    # Clear CHAT
    clear_chat_button.click(clear_chat, None, [chatbot])
    # NORMAL CHAT
    nc_prompt.submit(generate_chat_response, [chatbot, nc_prompt, radio], [chatbot, nc_prompt])
    nc_submit.click(generate_chat_response, [chatbot, nc_prompt, radio], [chatbot, nc_prompt])
    # Document lookup and chat
    dl_prompt.submit(document_lookup_chat, [chatbot, dl_search, dl_top_n, dl_prompt, radio],
                    [chatbot, dl_search, dl_prompt])
    dl_submit.click(document_lookup_chat, [chatbot, dl_search, dl_top_n, dl_prompt, radio],
                    [chatbot, dl_search, dl_prompt])
    # Document Lookup Chat
    # LIBRARY DIALOG
    lib_delete_button.click(remove_document, [lib_doc_list], [lib_doc_list, lib_status])
    lib_upload.upload(add_document, [lib_upload], [lib_doc_list, lib_status])

# NOTE: Set GRADIO_SERVER_NAME
demo.queue().launch(share=False)
