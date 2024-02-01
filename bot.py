import streamlit as st
import os
import google.generativeai as genai
from datetime import datetime
import pandas as pd
# from credentials import GOOGLE_API_KEY,reporting_person
import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
reporting_person = os.environ.get('reporting_person')

st.set_page_config(
    page_title="LeavePal-Leave request Co-Pilot",
    page_icon=":robot_face:",  # Set your desired favicon
)

# generation_config = {
#   "temperature": 0.0,
#   "top_p": 1,
#   "top_k": 1,
#   "max_output_tokens": 2048
# }




safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_ONLY_HIGH"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_ONLY_HIGH"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_ONLY_HIGH"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_ONLY_HIGH"
  },
]

# Initialize Gemini-Pro 
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="gemini-pro",
                              generation_config = {"temperature": 0.0,},
                              safety_settings=safety_settings)


# Define the Flask API endpoint for user details
FLASK_API_ENDPOINT = 'http://127.0.0.1:5000/get_user_details'

def get_user_details():
    response = requests.get(FLASK_API_ENDPOINT)
    return response.json()

user_details = get_user_details()

reporting_person = reporting_person
employee_id = int(user_details[-1]['Employee ID'])
employee_name = user_details[-1]['Name']

# Get the current date and time
current_date_time = datetime.now()

# # Extract the date from the datetime object
# current_date = current_date_time.date()
# current_time = current_date_time.time()

# --------------------------INSIGHTS GENERATION----------------------------------
leave_data = pd.read_csv('leave_data.csv')
leave_allocation = pd.read_csv("Leave_Allocation.csv")

def leave_insights(employee_id,leave_data,leave_allocation):
    filtered_df = leave_data[leave_data['employee_id'] == employee_id]
    merged_df = pd.merge(leave_allocation,filtered_df, left_on='LeaveTypeCode', right_on='leave_type',how='left')
    result_df = merged_df.groupby('LeaveTypeName')['no_of_leave_days'].sum().reset_index()
    final_df = pd.merge(result_df, leave_allocation, left_on='LeaveTypeName', right_on='LeaveTypeName')
    new_final_df = final_df[['LeaveTypeName','no_of_leave_days','AllocatedNoOfDays']]
    return new_final_df

insights = leave_insights(employee_id,leave_data,leave_allocation)

text_insights = '**LEAVE BALANCE:**\n\n'

for index, row in insights.iterrows():
    leave_type = row['LeaveTypeName']
    actual_days = row['no_of_leave_days']
    allocated_days = row['AllocatedNoOfDays']

    if actual_days <= allocated_days:
        # insight = f"For {leave_type} leave, you took {actual_days} days out of {allocated_days} allocated days. No overuse."
        insight =f"- **{leave_type}:** You can have ***{allocated_days-actual_days} leaves.*** ({actual_days} days out of {allocated_days} allocated days were used.)\n"
    else:
        overuse = actual_days - allocated_days
        insight = f"For {leave_type} leave, you exceeded the allocated days by {overuse} days. Please review."

    text_insights = text_insights+'\n'+insight
    
# ----------------------------------------------------------------------------------------------------




# Gemini uses 'model' for assistant; Streamlit uses 'assistant'
def role_to_streamlit(role):
  if role == "model":
    return "assistant"
  else:
    return role




prompt = """
You are a friendly leave request copilot.your job is tocapture the following details from the user and give them as a Jason file.
extract the following information:
1.Leave type (e.g., sick leave, vacation, personal leave, bereavement leave)
2.Starting date (in the format YYYY-MM-DD)
3.Ending date (in the format YYYY-MM-DD)
4.No Days (How many days take for leave can be calculated 'ending date-starting date')
5.Full day (This is for full day leave)
6.HalfDay (This is for half day leave)
7.Reason for leave (brief explanation)
8.Description (optional, for additional details)
9. generate remark using above data as following example
For a full day leave:'Dear [reporting person],I am writing to request leave from [Starting date] to [Ending date] due to [reason for leave].
I understand the importance of my responsibilities and will ensure that my work is up to date before my departure. 
I will also make sure to provide any necessary handovers to my colleagues.Thank you for considering my request. 
I look forward to your approval.'

For a half day leave:'Dear [Recipient's Name],I am writing to request half-day leave on [Starting date] due to [reason for leave]. 
I would like to take leave for [halfday] of the day.I understand the importance of my responsibilities and will ensure that my work is up to date before my departure. 
Thank you for considering my request. I look forward to your approval.'
Example JSON Format for Full Day Leave:
{{  \"Leave Type\": \"Annual Leave\",  \"From\": \"2023-09-06\",  \"To\": \"2023-09-10\",  \"No Days\": 5,  \"FullDay\": \"Full Day\",  \"HalfDay\": None,  \"Leave Reason\": \"Wedding\",  \"Remark\":'Dear Dilshan Kavinda,I am writing to request leave from 2023-09-06 to 2023-09-10 due to a Wedding.I understand the importance of my responsibilities and will ensure that my work is up to date before my departure. Thank you for considering my request. I look forward to your approval.'}} 
Example JSON Format for Half Day Leave:
{{  \"Leave Type\": \"Casual Leave\",  \"From\": \"2023-09-06\",  \"To\": \"2023-09-06\",  \"No Days\": 0.5,  \"FullDay\": None,  \"HalfDay\": \"1st Half\",  \"Leave Reason\": \"Family Need\",  \"Remark\":'Dear Dilshan Kavinda,I am writing to request half-day leave on 2023-09-06 due to personal reasons. I would like to take leave for first half of the day.I understand the importance of my responsibilities and will ensure that my work is up to date before my departure. Thank you for considering my request. I look forward to your approval.'}}

If any information is missing or unclear, prompt the user again for specific details.
If any information is missing or unclear,just ask to provide the missing information one by one.
If the dates are invalid or the reason is too vague, ask for clarification.
VERY IMPORTANT: Make sure you Do not make up or guess ANY extra information. 
Only extract what exactly is in the user request.
You respond in a short, very conversational friendly style."""

history = [
  {
    "role": "user",
    "parts": [prompt]
  },
  {
    "role": "model",
    "parts": ["Sure, I can help you with that. Here's the information I need from you to generate the JSON file:\n\n1. Leave Type:\n2. Starting Date (YYYY-MM-DD):\n3. Ending Date (YYYY-MM-DD):\n4. No of Days:\n5. Full Day (Full Day/None):\n6. Half Day (1st Half/2nd Half/None):\n7. Reason for Leave:\n8. Description (optional):\n\nOnce you provide me with this information, I'll generate a JSON file and a remark for you. Just let me know when you're ready.\n\nPlease provide the above information."]
  },
  {
    "role": "user",
    "parts": [f'today is {current_date_time} and reporting person is {reporting_person}']
  },
  {
    "role": "model",
    "parts": ["Thank you for providing the current date.Here's the information I need from you to generate the JSON file:\n\n1. Leave Type:\n2. Starting Date (YYYY-MM-DD):\n3. Ending Date (YYYY-MM-DD):\n4. No of Days:\n5. Full Day (Full Day/None):\n6. Half Day (1st Half/2nd Half/None):\n7. Reason for Leave:\n8. Description (optional):\n\nOnce you provide me with this information, I'll generate a JSON file and a remark for you. Just let me know when you're ready.\n\nPlease provide the above information."]
  },
  {
    "role": "user",
    "parts": [f'{text_insights}.These are the leave details belongs to employee_id{employee_id}']
  },
  {
    "role": "model",
    "parts": ["Thank you for providing the leave data.I will use those data to decide whether you are able to take the leave."]
  },
  {
    "role": "user",
    "parts": ["Hi!"]
  },
  {
    "role": "model",
    "parts": [f"Hello {employee_name}, Do you want to take a leave ?"]
  },
]

# Add a Gemini Chat history object to Streamlit session state
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history = history)

# Display Form Title
st.title("Chat with LeavePal!")

st.subheader('I am your leave request co-pilot')

st.success(text_insights)
# st.chat_message("assistant").markdown("Hi, How may I assit with you today?")

prompt_parts = [
  f"{text_insights} give some recommendations using this context.summarize those recommendations for 5-10 points.",
]

response = model.generate_content(prompt_parts)
st.success(response.text)

# # Display chat messages from history above current input box
for message in st.session_state.chat.history[7:]:
    with st.chat_message(role_to_streamlit(message.role)):
        st.markdown(message.parts[0].text)

# Accept user's next message, add to context, resubmit context to Gemini
if prompt := st.chat_input("I am your leave request co-pilot. How may I assit you?"):
    # Display user's last message
    st.chat_message("user").markdown(prompt)
    
    # Send user entry to Gemini and read the response
    response = st.session_state.chat.send_message(prompt)
    
    # Display last 
    with st.chat_message("assistant"):
        st.markdown(response.text)