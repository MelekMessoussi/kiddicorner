import re
import requests
import streamlit as st
from streamlit_mic_recorder import speech_to_text
from dotenv import load_dotenv
from html_chatbot_template import css, bot_template, user_template
from ai71 import AI71

# Load environment variables
load_dotenv()

# Load API key from environment variable
AI71_API_KEY = st.secrets["ai71"]["api_key"]
client = AI71(AI71_API_KEY)
# Define constants for Eleven Labs API
XI_API_KEY = 'sk_b8b72c5b969d6951e08cad16fe550cc68e58e2dff0657519'
VOICE_ID = 'lbw0VLXRBdYeEtY086mt'
CHUNK_SIZE = 1024
OUTPUT_PATH = "./assets/speech.mp3"


def clean_response(content):
    """Remove unwanted text from the response and trim quotes."""
    content = re.sub(r'user:', '', content, flags=re.IGNORECASE).strip()
    if content and content[0] == '"':
        content = content[1:]
    if content and content[-1] == '"':
        content = content[:-1]
    return content

def generate_response(prompt):
    try:
        chat_history = st.session_state.get("chat_hist", [])
        chat_history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
        formatted_prompt = (
            "Based on the following chat history, generate a response that naturally follows the conversation and remember the context and previous interactions to make your response relevant. "
            "Ensure that the response includes only the text message, with no additional information or context before or after it.\n\n"
            "Chat History:\n"
            f"{chat_history_str}\n\n"
            "User Message:\n"
            f"{prompt}"
            "Response:"
        )

        messages = [
            {"role": "system", "content": "You are a friendly kid's counsellor called kiddybot. You provide fun conversations, engaging suggestions, and positive reinforcement to children. Always respond in a playful, child-friendly manner and remember the context of previous interactions to make your responses relevant. Use a variety of examples with moral lessons to help solve the child's problems or teach them something new when needed. Keep your tone upbeat and encouraging."},
            {"role": "user", "content": formatted_prompt}
        ]
        
        content = ""
        for chunk in client.chat.completions.create(
            messages=messages,
            model="tiiuae/falcon-180B-chat",
            temperature=0.5,
            stream=True,
        ):
            delta_content = chunk.choices[0].delta.content
            if delta_content:
                content += delta_content
        
        return clean_response(content)
    except Exception as e:
        return f"An error occurred: {e}"

@st.cache_resource
def text_to_speech_eleven_labs(text):
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"
    headers = {
        "Accept": "audio/mpeg",
        "xi-api-key": XI_API_KEY
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }
    
    response = requests.post(tts_url, headers=headers, json=data, stream=True)
    if response.status_code == 200:
        with open(OUTPUT_PATH, 'wb') as file:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    file.write(chunk)
        return OUTPUT_PATH
    else:
        return None

def generate_response_log(response):
    if "chat_hist" not in st.session_state:
        st.session_state["chat_hist"] = []
    
    st.session_state.chat_hist.append({"role": "user", "content": st.session_state.text_received[-1]})
    st.session_state.chat_hist.append({"role": "assistant", "content": response})
    
    st.write(css, unsafe_allow_html=True)
    welcome = "Hello! Welcome to GabbyGarden! I am Gab.\n You can ask me any question you like! I'm here to help you learn and understand new things."

    for message in st.session_state.chat_hist:
        if message['role'] == 'assistant':
            st.write(bot_template.replace("{{MSG}}", message['content'].strip()), unsafe_allow_html=True)
        elif message['role'] == 'system':
            st.write(bot_template.replace("{{MSG}}", welcome), unsafe_allow_html=True)
        elif message['role'] == 'user':
            st.write(user_template.replace("{{MSG}}", message['content'].strip()), unsafe_allow_html=True)
    
    # Generate speech and play the audio
    audio_file = text_to_speech_eleven_labs(response)
    st.audio(audio_file)

def mic():
    
    state = st.session_state

    if 'text_received' not in state:
        state.text_received = []

    text = speech_to_text(language='en', start_prompt="Talk To Me", use_container_width=True, just_once=True, key='STT_' + str(int(st.session_state.get('counter', 0))))
    
    if text:
        state.text_received.append(text)
        response = generate_response(text)
        generate_response_log(response)

st.markdown("""
    <style>
        .image-container {
            display: flex;
            justify-content: center;
        }
        
        .image-container img {
            width: 350px;
            height: auto;
            margin-top: 30px;
        }
    </style>
    <div class="image-container">
        <img src="app/static/tlchargement5-ezgif.com-cut.gif" width="300" height="200"/>
    </div>
    """, unsafe_allow_html=True)

mic()

