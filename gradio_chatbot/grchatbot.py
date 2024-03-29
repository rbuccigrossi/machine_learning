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

def clear_chat(message_history):
    chatgpt.clear_messages(message_history)
    return [], message_history


def generate_chat_response(chat_display, prompt, message_history, model):
    if (not(prompt)):
        newchat_display = chat_display + [[prompt, f"Please enter a prompt"]]
        return (newchat_display, prompt, message_history)
    try:
        # Now call the chatbot to get the response
        response = chatgpt.chat(prompt, message_history, model)
        # Update the chatbot's response
        newchat_display = chat_display + [[prompt, response]]
        return (newchat_display, "", message_history)
    except Exception as e:
        # Upon error, output the error as the response
        newchat_display = chat_display + [[prompt, f"We received an error: {str(e)}"]]
        print(traceback.format_exc())
        return (newchat_display, prompt, message_history)

def document_lookup_chat(chat_display, search, top_n, prompt, message_history, model):
    if (not(prompt)):
        newchat_display = chat_display + [[prompt, f"Please enter a prompt"]]
        yield (newchat_display, search, prompt, message_history)
        return
    # If search is empty, then use the prompt for the search
    if (not(search)):
        search = prompt
    try:
        # Update status for search
        newchat_display = chat_display + [[prompt, f"Searching for {top_n} documents with '{search}...'"]]
        yield (newchat_display, search, prompt, message_history)
        # Conduct search
        results = docdatabase.query_index(search, top_n)
        newchat_display = chat_display + [[prompt, f"We found {len(results['matches'])} hits. Now executing chat prompt...'"]]
        yield (newchat_display, search, prompt, message_history)
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
            "Request: " + prompt
        )
        # Now call the chatbot to get the response
        response = chatgpt.chat(chat_search, message_history, model)
        newchat_display = chat_display + [[prompt, response]]
        yield (newchat_display, "", "", message_history)
    except Exception as e:
        newchat_display = chat_display + [[prompt, f"We received an error {str(type(e))}: {str(e)}"]]
        print(traceback.format_exc())
        yield (newchat_display, search, prompt, message_history)
        
    
def map_reduce_chat(chat_display, document, prompt, message_history, model):
    if (not(document) or not(prompt)):
        newchat_display = chat_display + [[prompt, f"Please enter a document and a prompt"]]
        yield (newchat_display, document, prompt, message_history)
        return
    # Split the document into sections
    # Split the text by newline
    lines = document.split('\n')
    
    sections = []
    section = []
    count = 0
    for line in lines:
        line_word_count = len(line.split())
        if count + line_word_count > 1500:
            # Store entry and start new section
            sections.append('\n'.join(section))
            section = [line]
            count = line_word_count
        else:
            # Add line to current section
            section.append(line)
            count += line_word_count
    # Store last entry
    sections.append('\n'.join(section))

    try:
        num_sections = len(sections)
        n = 0
        while (n < num_sections):
            if (num_sections == 1): # There is only one section
                chat_search = "The following is a document to be used for a request below\n\n---\n\n"
                chat_search += sections[n] + "\n\n---\n\n"
                chat_search += (
                    "Answer the request based upon the above document section. " +
                    "If the answer is not clear from the document, state 'I cannot answer " +
                    "based upon the document provided.'\n\n " +
                    "Request: " + prompt
                )
            elif (n < (num_sections - 1)): # Not the last section
                chat_search = f"This is section {n+1} of {num_sections} of a document\n\n---\n\n"
                chat_search += sections[n] + "\n\n---\n\n"
                chat_search += (
                    "Because the full document will not fit into the chat history size, please " +
                    "answer the following request the best you can with what you have received " +
                    "so far and provide details (such as quotes and summary information) " +
                    "that you can then review and use as you receive subsequent sections. " +
                    "If the answer is not clear from the document, state 'I cannot answer " +
                    "based upon the document provided.'\n\n " +
                    "Request: " + prompt
                )
            else: # The last section
                chat_search = f"This is the last section of the document\n\n---\n\n"
                chat_search += sections[n] + "\n\n---\n\n"
                chat_search += (
                    "Answer the request based upon your previous summary and the current section " +
                    "If the answer is not clear from the document, state 'I cannot answer " +
                    "based upon the document provided.'\n\n " +
                    "Request: " + prompt
                )
            # Display the chat_search we are running
            newchat_display = chat_display + [[chat_search, ""]]
            yield (newchat_display, document, prompt, message_history)
            # To avoid message overruns and keep the chatbot focused, limit the message_history to
            # the last response from the chatbot
            if len(message_history) > 0:
                message_history = [message_history[-1]]
            response = chatgpt.chat(chat_search, message_history, model)
            # Display the response (and save it in our local copy of the chat_display)
            chat_display = chat_display + [[chat_search, response]]
            yield (chat_display, document, prompt, message_history)
            # Move to the next section
            n += 1
    except Exception as e:
        newchat_display = chat_display + [[prompt, f"We received an error {str(type(e))}: {str(e)}"]]
        print(traceback.format_exc())
        yield (newchat_display, document, prompt, message_history)
        
    
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
                radio = gr.Radio(value='gpt-3.5-turbo-16k', show_label=False,
                                 choices=['gpt-3.5-turbo','gpt-3.5-turbo-16k','gpt-4'],
                                 container=False)
            with gr.Column(scale=2, min_width=110):
                clear_chat_button = gr.Button("Clear Chat")
        chat_display = gr.Chatbot(value=[], elem_id="chat_display", height=500)
        message_history = gr.State(value=[])
        with gr.Tab("Normal Chat"):
            with gr.Row():
                with gr.Column(scale=100):
                    nc_prompt = gr.Textbox(
                        show_label=False,
                        placeholder="Enter prompt and press enter",
                        container=False)
                with gr.Column(scale=2, min_width=110):
                    nc_submit = gr.Button("Submit")
        with gr.Tab("Chat w/ Document Lookup"):
            with gr.Row():
                with gr.Column(scale=100):
                    dl_search = gr.Textbox(
                        show_label=False,
                        placeholder="Search text for documents (leave blank to use prompt for search)",
                        container=False)
                with gr.Column(scale=1, min_width=30):
                    gr.Markdown(" Hits:")
                with gr.Column(scale=1, min_width=80):
                    dl_top_n = gr.Number(show_label=False, container=False, value=5)
            with gr.Row():
                with gr.Column(scale=100):
                    dl_prompt = gr.Textbox(
                        show_label=False,
                        placeholder="Enter prompt and press enter",
                        container=False)
                with gr.Column(scale=2, min_width=110):
                    dl_submit = gr.Button("Submit")
        with gr.Tab("Question with Large Document"):
            mr_document = gr.Textbox(
                show_label=False, max_lines=5,
                placeholder="Cut and Paste Document Here",
                container=False)
            with gr.Row():
                with gr.Column(scale=100):
                    mr_prompt = gr.Textbox(
                        show_label=False,
                        placeholder="Enter prompt and press enter",
                        container=False)
                with gr.Column(scale=2, min_width=110):
                    mr_submit = gr.Button("Submit")
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
    clear_chat_button.click(clear_chat, [message_history], [chat_display, message_history])
    # NORMAL CHAT
    nc_prompt.submit(generate_chat_response, [chat_display, nc_prompt, message_history, radio],
                     [chat_display, nc_prompt, message_history])
    nc_submit.click(generate_chat_response, [chat_display, nc_prompt, message_history, radio],
                    [chat_display, nc_prompt, message_history])
    # Document lookup and chat
    dl_prompt.submit(document_lookup_chat, [chat_display, dl_search, dl_top_n, dl_prompt, message_history, radio],
                    [chat_display, dl_search, dl_prompt, message_history])
    dl_submit.click(document_lookup_chat, [chat_display, dl_search, dl_top_n, dl_prompt, message_history, radio],
                    [chat_display, dl_search, dl_prompt, message_history])
    # Question with Large Document (Map-Reduce)
    mr_prompt.submit(map_reduce_chat, [chat_display, mr_document, mr_prompt, message_history, radio],
                    [chat_display, mr_document, mr_prompt, message_history])
    mr_submit.click(map_reduce_chat, [chat_display, mr_document, mr_prompt, message_history, radio],
                    [chat_display, mr_document, mr_prompt, message_history])
    # LIBRARY DIALOG
    lib_delete_button.click(remove_document, [lib_doc_list], [lib_doc_list, lib_status])
    lib_upload.upload(add_document, [lib_upload], [lib_doc_list, lib_status])

# NOTE: Set GRADIO_SERVER_NAME
gruser = os.getenv("GRCHATBOT_USER")
grpassword = os.getenv("GRCHATBOT_PASSWORD")
if (gruser is None) or (grpassword is None):
    auth = None
else:
    auth = (gruser, grpassword)

demo.queue().launch(share=False, auth=auth)
