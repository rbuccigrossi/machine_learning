import gradio as gr
import os
import time
import textwrap
from crewai import Agent, Task, Crew, Process

# NOTE set OPENAI_API_KEY in the environment to your OpenAI Key
# Let's set the default model for our AI workflow
os.environ["OPENAI_MODEL_NAME"]="gpt-4o"

def generate_minutes(filepath):
    if not filepath or not os.path.isfile(filepath):
        yield "No file uploaded or file does not exist."
        return
    
    # Reading the content from the uploaded file
    with open(filepath, 'r') as f:
        transcript = f.read()

    # Creating the notetaker agent
    notetaker = Agent(
        role='NoteTaker',
        goal='To convert a transcript into a usable set of notes (minutes) for meeting participants',
        backstory=textwrap.dedent("""
            You are a knowledgeable professional with a college education and extensive experience in the IT industry 
            as a project manager and writer. Your communication skills are excellent, and you understand the importance 
            of meeting best practices such as setting clear agendas, defining action items with specific responsibilities, 
            providing concise summaries, and maintaining documentation for future reference.
            
            Your role is to attentively listen to discussions and extract meaningful insights, ensuring that all 
            relevant points are captured for the benefit of meeting participants. You aim to create an inviting and 
            collaborative atmosphere, fostering an environment where everyone can contribute and thrive.
        """)
    )

    # Identify meeting participants
    participants_task = Task(
        description=textwrap.dedent(f"""
  The following is a transcript of a meeting:
  
  ---
  
  {transcript}
  
  ---
  
  Using the transcript, please identify and list all participants who attended the meeting.
  It's essential to include everyone who contributed to the discussion, as their input is valuable for documentation. 
  Please organize your response with the heading 'Attendees', followed by a bulleted list of names. 
  Format your response as follows:
  
  # Attendees
  - John Doe
  - Jane Smith
  - Alex Johnson
        """),
        expected_output='A formatted list of meeting participants',
        agent=notetaker,
    )
    
    # Identify action items
    action_items_task = Task(
        description=textwrap.dedent(f"""
  The following is a transcript of a meeting:
  
  ---
  
  {transcript}
  
  ---
  
  Using the transcript, please provide a complete list of action items 
  identified in the meeting, including the name of the person assigned to each action item. 
  Capturing action items is crucial for ensuring accountability and follow-up.
  
  Please organize your response with the heading 'Action Items', followed by a numbered list. Each item should include 
  the name of the assignee and a brief summary of the action item. 
  If possible, include any deadlines or follow-up dates mentioned during the meeting.
  
  Format your response as follows:
  
  # Action Items
  1. Robert Buccigrossi - Prepare manager’s meeting notes for the next quarterly meeting (Due: [insert date here])
  2. Jane Smith - Review project deliverables and provide feedback by next week.
        """),
        expected_output='A formatted list of meeting action items',
        agent=notetaker,
    )
    
    # Identify notes
    notes_task = Task(
        description=textwrap.dedent(f"""
The following is a transcript of a meeting:

---

{transcript}

---

Using the transcript, please create a outline of the conversation organized
by topic, with all the key subtopics, debates, observations, and decisions made during discussions under that
topic. You will find it easier to focus if you break the transcript into smaller subsections, probably by
major topics that were discussed.

Please format your notes with the heading 'Meeting Notes', followed by clearly defined sections
for different parts of the meeting. Each section should have a subheading, and the content should be organized
in bullet points for clarity.

Include the Meeting Title and Date at the top of the notes and use the following structure:

# Meeting Notes

**Meeting Title: [Insert Title Here]**
**Date: [Insert Date Here]**

## Topic Name #1
- Discution point, observation, decision, or subtopic
  - Sub discussion point, observation, or decision
  - ...
- Discution point, observation, decision, or subtopic
  - Sub discussion point, observation, or decision
  - ...

## Topic Name #2
- ...

## Topics Name #3
- ...
        """),
        expected_output='A detailed, structured outline of the meeting notes in bullet points',
        agent=notetaker,
    )
    
    # Write meeting summary
    summary_task = Task(
        description=textwrap.dedent("""
            Using the notes provided, summarize the overall purpose and key points of the meeting. Your summary 
            should be in prose format (one or two paragraphs) and should cover the main objectives, significant
            discussions, key decisions made, and any notable outcomes. 
            
            Please begin the summary with the heading 'Meeting Summary'.
            
            Here is an example structure:
            
            # Meeting Summary
            
            The meeting focused on [main objective], where participants discussed [key topics discussed].
            Significant decisions included [key decisions], and it was agreed that [summary of outcomes].
            Notable contributions were made by [names], who [specific contributions].
        """),
        expected_output='A summary (one or two paragraphs) of the meeting in prose format',
        context=[notes_task],
        agent=notetaker,
    )
    
    # Combine into a meeting minutes
    combine_task = Task(
        description=textwrap.dedent("""
            Please combine the elements from the previous workflow steps into a single set of meeting minutes text
            to be shared with the team: Attendees, Meeting Summary, Action Items, and Meeting Notes.
            
            Please format the meeting minutes in markdown using the following structure, making sure to place the
            Meeting Title and Date at the top:
            
            # Minutes [Insert Meeting Title Here] - [Insert Date Here]
            
            ## Meeting Summary
            [Summary of the meeting]
            
            ## Action Items
            [List of action items]
            
            ## Attendees
            [List of attendees]
            
            ## Agenda
            - List of key topics
            
            ## Topic Name #1
            - ...
            
            ## Topic Name #2
            - ...
            
            ## Topics Name #3
            - ...
            
            ## Decisions Made
            - Specific decisions or outcomes reached during the meeting.
            
            ## Follow-up
            - Any follow-up actions that arose, without listing the attendees or action items directly.
            
            Ensure that each section is clearly labeled and formatted consistently. The goal is to create a
            comprehensive and professional meeting minutes document that is easy to read and follow.

            Since the results will be directly displayed to the user, please present the Markdown 
            directly (not in a Markdown block).
        """),
        expected_output='Meeting minutes formatted in markdown',
        context=[participants_task, action_items_task, notes_task, summary_task],
        agent=notetaker,
    )

    # Execute each task in sequence
    # We do this so that we can inform the user of progress
    for (task, task_name) in [(participants_task, "Step 1 of 5: Finding Participants..."), 
                              (action_items_task, "Step 2 of 5: Finding Action Items..."), 
                              (notes_task, "Step 3 of 5: Finding Discussion Topics..."), 
                              (summary_task, "Step 4 of 5: Summarizing Meeting..."), 
                              (combine_task, "Step 5 of 5: Combining Results into a Document...")]:
        yield str(task_name)
        crew = Crew(
          agents=[notetaker],
          tasks=[task],
          process=Process.sequential,
          verbose=False,
        )
        # Kick off the crew
        result = crew.kickoff()

    yield str(result)

with gr.Blocks() as demo:
    gr.Markdown("## Upload a Meeting Transcript to Generate Meeting Minutes")
    
    with gr.Row():
        file_input = gr.File(label="Upload a transcript file", type="filepath", file_count="single", file_types=[".txt", ".md"])
        display_button = gr.Button("Generate Meeting Minutes")
        stop_button = gr.Button("Stop")
    
    file_content = gr.Markdown(label="Generated Meeting Minutes", height=500, show_copy_button=True)
    
    # Start and stop events
    display_event = display_button.click(
        fn=generate_minutes,
        inputs=file_input,
        outputs=file_content
    )
    
    stop_button.click(
        fn=None,
        inputs=None,
        outputs=None,
        cancels=[display_event]
    )

# Launch the Gradio app
demo.launch()
