import streamlit as st
import requests
import uuid

query_params = st.experimental_get_query_params()
if 'webhook' in query_params:
    webhook = query_params['webhook'][0]
else:
    st.info("Please pass 'webhook' query parameter to run app.")
    st.stop()

if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = str(uuid.uuid4())
if "chat_user_id" not in st.session_state:
    st.session_state.chat_user_id = str(uuid.uuid4())


# st.title("🤖 GigaApp playground")

def send_request(text):
    print(f"Sending request with text: {text}")

    data = {
        "messageName": "RUN_APP" if not text else "MESSAGE_TO_SKILL",
        "sessionId": st.session_state.chat_session_id,
        "messageId": 1,
        "uuid": {
            "userChannel": "GIGA_APP",
            "userId": st.session_state.chat_user_id
        },
        "payload": {
            "message": {
                "original_text": text,
                "asr_normalized_message": text
            },
            "projectName": "GigaApp",
            "intent": "run_app",
            "server_action": {
                "action_id": "run_app",
                "parameters": {
                }
            }
        }
    }
    print(f"Request: {data}")

    response = requests.post(webhook, json=data, timeout=10)
    print(f"Response: {response.json()}")
    st.session_state.resp = response.json()
    # st._rerun()


def submit_text():
    data = st.session_state.global_text_input
    print("Text submitted: " + data)
    send_request(data)


if "started" not in st.session_state or not st.session_state.started:
    # st.session_state.started = st.button("Start app")
    # print("Update started to " + str(st.session_state.started))
    st.session_state.started = True

if st.session_state.started:
    if "run_app" not in st.session_state:
        st.session_state.run_app = True
        send_request("")

    upper_container = st.container()
    lower_container = st.container()

    has_controls = False
    with upper_container:
        if "resp" in st.session_state:
            items = st.session_state.resp["payload"]["items"]
            for item in items:
                if 'card' in item:
                    for cell in item['card']['cells']:
                        if cell['type'] == 'image_cell_view':
                            st.image(cell['content']['url'])
                        if cell['type'] == 'text_cell_view':
                            st.info(cell['content']['text'])
                        if cell['type'] == 'left_right_cell_view':
                            text = cell['actions'][0]['text']
                            st.button(text, on_click=send_request, args=[text], use_container_width=True)
                            has_controls = True
                if 'bubble' in item:
                    for text in item['bubble']['text'].split('\n'):
                        text = text.strip()
                        if text != "":
                            st.info(text)

            if 'suggestions' in st.session_state.resp["payload"]:
                suggestions = st.session_state.resp["payload"]["suggestions"]
                if 'buttons' in suggestions:
                    for button in suggestions['buttons']:
                        st.button(button['title'], on_click=send_request, args=[button['title']], use_container_width=True)
                        has_controls = True

            if st.session_state.resp["payload"].get("finished", False):
                st.stop()
            else:
                if not has_controls:
                    with lower_container:
                        st.text_area("", height=100, key='global_text_input')
                        st.button("Отправить", on_click=submit_text, use_container_width=True, type="primary")
