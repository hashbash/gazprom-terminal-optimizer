import streamlit as st

st.set_page_config(
    page_title="Intro",
    page_icon="👋",
)
st.markdown(
        """
        Решение от команды geo.xyz

        ### Ссылки

        - [Документация](https://docs.google.com/document/d/1EcP_IlliRfnM69gKYGf4v1oneFd9Hh80UFD__nLxQHQ/edit#heading=h.u8vk6x3kzk17)
        - [Презентация](https://docs.google.com/presentation/d/1r2l-Cyt94UEJo7EsTCz_oHnT-aYZ-kaQ/edit#slide=id.g24b8d17357c_1_12)
        - [Описание](https://docs.google.com/document/d/1Ny04dVFHDNoxIe2RwcU10wJVlpUs5ntOtKj3ueBhyBI/edit#heading=h.or2rc6aaptso)
        
    """
    )

st.title('Демонстрация и описание решения')
video_file = open('static/demo.mp4', 'rb')
video_bytes = video_file.read()

st.video(video_bytes)
