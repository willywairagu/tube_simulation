import streamlit as st
from PIL import Image
import base64

st.set_page_config(
    page_title="London Tube Twin",
    page_icon="🚉",
)

st.write("# London Tube Twin 🚉")

# # background image
def add_bg_from_local(image_file):
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url(data:image/{"jpg"};base64,{encoded_string.decode()});
        background-size: cover;
    }}
    </style>
    """,
    unsafe_allow_html=True
    )

add_bg_from_local('faint_bg.jpg')

st.sidebar.success("Jump onboard above.")

st.markdown(
    """
    The London Underground (aka “The Tube”) is a network of train 
    stations which connects the city.

    *🚂 Jump onboard from the sidebar*  to see graph representation of the network
    and passenger count forecast at each station (entry and exit)!
    ### What to expect from this dashboard?
    - A graph representation of the network
    - Key insights to railway technicians and Planners.
    - A passenger count forecast at each station (entry and exit), in monthly increments since 2018 to 2021,
      based on counts at other stations
"""
)