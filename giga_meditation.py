import json
import os
import time
import uuid

import langchain
import requests
import streamlit as st
from langchain.chat_models.gigachat import GigaChat
from langchain.schema import HumanMessage, SystemMessage

import retrying

gigachat_user = os.environ.get("GIGA_USER", None)
gigachat_password = os.environ.get("GIGA_PASSWORD", None)
tts_auth = os.environ.get("TTS_AUTH", None)
giga_url = os.environ.get("GIGA_URL", None)


model = GigaChat(
    user=gigachat_user,
    password=gigachat_password,
    verify_ssl=False,
    api_base_url=giga_url,
    model="GigaChat70:latest",
)


def _generate_text(topic, backgound):
    return model(
        [
            HumanMessage(
                content=f"Придумай длинный текст для сеанса медитации. Медетирующий будет слышать {backgound}. Тема медитации - {topic}. Текст должен быть расслабляющий и успокаивающий. Не пиши никаких пояснений к тексту."
            )
        ]
    ).content.replace("\n", "")

@retrying.retry(stop_max_attempt_number=3, wait_fixed=1000)
def _get_tts_token():
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    payload = "scope=SALUTE_SPEECH_CORP"
    headers = {
        "RqUID": "6f0b1291-c7f3-43c6-bb2e-9f3efb2dc98e",
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": tts_auth,
    }

    response = requests.request(
        "POST", url, headers=headers, data=payload, verify=False, timeout=30
    )

    if response.ok:
        return response.json()["access_token"]

    print(response)
    st.error("Ошибка авторизации в сервисе синтеза 😢")
    st.stop()
    return None


def _get_audio(text, backgound, token):
    url = "https://smartspeech.sber.ru/rest/v1/text:synthesize?format=opus&voice=Bsa_24000"

    payload = f'<extra.background-audio src="{backgound}" volume="0.7" loop="crossfade">{text}</extra.background-audio>'
    headers = {"Content-Type": "application/ssml", "Authorization": f"Bearer {token}"}

    response = requests.request(
        "POST",
        url,
        headers=headers,
        data=payload.encode("utf-8"),
        timeout=6000,
        verify=False,
    )
    if response.ok:
        return response.content
    else:
        print("Code: " + str(response.status_code))
        print(response.content)
        st.info("Ошибка при генерации аудио 😢")
        st.stop()
        return None


def start_btn():
    st.session_state.started = True


st.title("Добро пожаловать в GigaZen 🧘🏻‍♀️")
st.subheader("ГигаЧат и SaluteVoice помогут вам создать персональную медитацию.")

st.set_page_config(
    page_title="GigaZen 🧘🏻‍♀️",
    page_icon="🧘🏻‍♀️",
    menu_items={
        'About': "# This is an *extremely* cool app, developed by @Krestnikov",
    }
)

topic = st.text_input(
    "Введите тему для медитации (например 'весенний сад' или 'новый автомобиль')",
    value="утро на море",
)
sounds = {
    "Море": "sm-sounds-nature-sea-2",
    "Ручей": "sm-sounds-nature-stream-2",
    "Дождь": "sm-sounds-nature-rain-2",
    "Лес": "sm-sounds-nature-forest-2",
    "Камин": "sm-sounds-nature-fire-2",
}
genre = st.radio("Выберите звуковой фон для медитации", sounds.keys())
backgound = sounds[genre]

if st.button(
    "Создать медитацию",
    on_click=start_btn,
    disabled=st.session_state.get("started", False),
):
    with st.status(
        f"Создаю медитацию, это займет около 30 секунд. Пока расслабьтесь и настройтесь на позитивную волну ",
        expanded=True,
    ) as status:
        st.write("Пишу текст...")
        meditation_text = _generate_text(topic, genre)
        st.write("Подключаю синтез речи...")
        token = _get_tts_token()
        st.write("Записываю звук...")
        data = _get_audio(meditation_text, backgound, token)
        status.update(
            label="Процесс создания завершен!", state="complete", expanded=False
        )

    st.info("Ваша медитация готова! Наслаждайтесь!")
    st.audio(data, format="audio/wav")
    st.balloons()

st.set_option()