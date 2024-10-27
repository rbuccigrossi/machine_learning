## Meeting Notes from Transcript Example

Given a transcript (and an optional agenda), can we create a team thatCan we create a team that
will pull out a meeting summary, action items, attendees, and organized notes that are suitable
to be sent as meeting minutes to participants?

This code example will assume that the transcript and agenda are saved in local files and
will use the CrewAI [FileReadTool](https://docs.crewai.com/tools/FileReadTool/) so that agents can
access the information as needed.

### How to Run The Example

For the first run, make sure you have the required packages:

    pip install -r requirements.txt

Make sure you have OPENAI_API_KEY defined (if not already in the environment). For Windows:

    set OPENAI_API_KEY=sk-project-############
    
Run the jupyter notebook (this will open in a new browser):

    jupyter notebook NotesFromTranscript.ipynb
