import streamlit as st

st.set_page_config(
    page_title="Intro",
    page_icon="👋",
)
st.title('Решение от команды geo.xyz')
st.markdown(
        """
        ### Ссылки

        - [Документация](https://docs.google.com/document/d/1EcP_IlliRfnM69gKYGf4v1oneFd9Hh80UFD__nLxQHQ/edit#heading=h.u8vk6x3kzk17)
        - [Презентация](https://docs.google.com/presentation/d/1r2l-Cyt94UEJo7EsTCz_oHnT-aYZ-kaQ/edit#slide=id.p1)
        - [Описание](https://docs.google.com/document/d/1Ny04dVFHDNoxIe2RwcU10wJVlpUs5ntOtKj3ueBhyBI/edit#heading=h.or2rc6aaptso)
        - [Репозиторий](https://github.com/hashbash/gazprom-terminal-optimizer/tree/main)
    """
    )

st.title('Демонстрация решения')
video_file = open('static/demo.mp4', 'rb')
video_bytes = video_file.read()

st.video(video_bytes)
