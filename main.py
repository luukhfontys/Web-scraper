import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from functions import *
import xlsxwriter
import io

st.set_page_config(
    page_title='Gaspedaal webscraper',         #Titel in browser
    layout="wide",                          #Type pagina, deze is breed zodat hij het hele scherm vult
    page_icon="🚗",                         #Icoontje van pagina
    initial_sidebar_state="expanded",       #Zorgen dat het menu gelijk open staat
)

if 'page' not in st.session_state:
    st.session_state['page'] = 'Keuze'
    st.session_state.selected_brand = None
    st.session_state.Geselecteerde_autos = []
    st.session_state.elements_list = []
    
def Keuze():
    st.title('Gaspedaal.nl webscraper')
    opties = get_car_models()
    selected_brand = st.selectbox('Selecteer merk:', list(opties.keys()))
    st.session_state.selected_brand = selected_brand
    if st.session_state.selected_brand:
        # Get the models for the selected brand
        selected_models = opties[st.session_state.selected_brand]

        # Dropdown for selecting a model
        selected_model = st.selectbox('Selecteer model:', selected_models)
        if selected_model:
            # Button to add the selected car to the list
            if st.button('Toevoegen aan scrape lijst'):
                # Initialize the list if not already created
                if 'Geselecteerde_autos' not in st.session_state:
                    st.session_state.Geselecteerde_autos = []
                    
                # Add the selected car to the list
                if {'brand': selected_brand, 'model': selected_model} not in st.session_state.Geselecteerde_autos:
                    st.session_state.Geselecteerde_autos.append({'brand': selected_brand, 'model': selected_model})
    if 'Geselecteerde_autos' in st.session_state and st.session_state.Geselecteerde_autos:
        df_selected_cars = pd.DataFrame(st.session_state.Geselecteerde_autos)
        st.dataframe(df_selected_cars)
        if st.button('Clear selectie'):
            st.session_state.Geselecteerde_autos = []
            st.rerun()
        
        index = list(df_selected_cars.index.values)
        brand = list(df_selected_cars.brand.values)
        model = list(df_selected_cars.model.values)

        # Create a list of strings by concatenating index, brand, and model
        merged_list = [f"{idx} {brand} {model}" for idx, brand, model in zip(index, brand, model)]

        remove_select = st.selectbox('Verwijder selectie:', merged_list)
        if st.button('Verwijder'):
            lijst_temp = st.session_state.Geselecteerde_autos
            lijst_temp.pop(int(remove_select[0]))
            st.rerun()
            
        importEU = st.checkbox('EU import auto\'s ook meenemen?')
        if st.button('Start scrape'):
            merken = [car["brand"] for car in st.session_state.Geselecteerde_autos]
            modellen = [car["model"] for car in st.session_state.Geselecteerde_autos]
            progress_bar = st.progress(0)
            with st.spinner('Looking for matches...'):
                elements, merkenindex, modellenindex, total_elements = get_elements(merken, modellen, importEU)
            st.success(f'{total_elements} matches found!')
            df = scrape_data_df(elements, merkenindex, modellenindex, progress_bar)
            st.dataframe(df)
            buffer = io.BytesIO()
            df.to_excel(buffer, sheet_name='Sheet1', index=False, engine='xlsxwriter')
            buffer.seek(0)
            download_button = st.download_button(
                label="Download data als Excel",
                data=buffer,
                file_name='Gaspedaal_scraped_data.xlsx',
                mime='application/vnd.ms-excel'
            )

            # Display the download button
            if download_button:
                st.success("Downloaded successfully!")
            
if st.session_state['page'] == 'Keuze':
    Keuze()