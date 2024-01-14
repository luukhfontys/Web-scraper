import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import streamlit as st
from io import BytesIO
from pyxlsb import open_workbook as open_xlsb

def get_car_models():
    """"Haalt alle modellen autos van gaspedaal.nl af en returned dictionary met {'Merk': ['Modellen', ...]}"""
    url = 'https://www.gaspedaal.nl/blog/autoblog/auto-abc/22-automerken'
    html = requests.get(url)

    s = BeautifulSoup(html.content, 'html.parser')

    # Vind alle auto merken met model.
    results = s.find_all('li')

    text_list = []

    for li in results:
        text_content = li.text.strip()  # Use strip() to remove leading and trailing whitespaces
        text_list.append(text_content)

    filtered_text_list = [item for item in text_list if "|" in item]

    result_dict = {
        item.split(' | ')[0].replace('.', '').replace(' ', '-').replace('ë', 'e'): 
        [model.replace('.', '').replace(' ', '-').replace('ë', 'e') for model in item.split(' | ')[1].split(', ')] 
        for item in filtered_text_list
    }
    
    return result_dict

def construct_search_query(make, model=None, bmin=None, bmax=None, importEU=False, elektrisch=False):
    query_params = {'bmin': bmin, 'bmax': bmax}

    if model and elektrisch:
        # If model is specified, include it in the query
        search_query = f"{make}/{model}/elektrisch"
    elif model:
        search_query = f"{make}/{model}"
    else:
        # If model is not specified, only include the make in the query
        search_query = make

    # Append the query parameters
    query_string = "&".join([f"{key}={value}" for key, value in query_params.items() if value])

    # Final search query
    final_query = f"{search_query}?{query_string}" if query_string else search_query
    if importEU:
        final_query = 'https://www.gaspedaal.nl/importautos/' + final_query
    else:
        final_query = 'https://www.gaspedaal.nl/' + final_query

    if '?' in final_query:
        final_query += '&srt=df-a'
    else:
        final_query += '?srt=df-a'
        
    return final_query

def extract_bouwjaar_km(info_string):
    
    bouwjaar_match = re.search(r'Bouwjaar:\s*(\d+)', info_string)
    km_stand_match = re.search(r'Km.stand:\s*([\d.]+)\s*km', info_string)

    bouwjaar_value = bouwjaar_match.group(1) if bouwjaar_match else None
    km_stand_value = km_stand_match.group(1).replace(".", "") if km_stand_match else None
    
    return bouwjaar_value, km_stand_value

def extract_properties_of_car(car):
    
    volledige_naam = car.find('h4').text.strip()
    properties = car.find_all('p')
    website = 'https://www.gaspedaal.nl' + car.get('href')
    
    prop_strip = []

    for i in range(len(properties)):
        prop_strip.append(properties[i].text.strip())

    bouwjaar, km_stand = extract_bouwjaar_km(prop_strip[1])
    prijs = prop_strip[0].replace(".", "")
    
    locatie = prop_strip[-2]
    
    return [volledige_naam, prijs, bouwjaar, km_stand, locatie, website]

def extract_page_info(page):
    return page.find_all(attrs={"data-testid": "occasion-item"})

def get_elements(merken: list, modellen: list, importEU: bool, elektrisch: bool):
    elements_list = []
    merkenindex = []
    modellenindex = []
    for merk, model in zip(merken, modellen):
        url = construct_search_query(merk, model=model, elektrisch = elektrisch, bmin=None, bmax=None)
        html = requests.get(url)
        page = BeautifulSoup(html.content, 'html.parser')
        elements = extract_page_info(page)
        
        i = 2
        while len(elements) > 0:
            elements_list.append(elements)
            urlpage = url + '&page=' + str(i)
            html = requests.get(urlpage)
            page = BeautifulSoup(html.content, 'html.parser')
            elements = extract_page_info(page)
            i += 1
            merkenindex.append(merk)
            modellenindex.append(model)
    
    if importEU:
        for merk, model in zip(merken, modellen):
            url = construct_search_query(merk, model=model, importEU=importEU)
            html = requests.get(url)
            page = BeautifulSoup(html.content, 'html.parser')
            elements = extract_page_info(page)
        
            i = 2
            while len(elements) > 0:
                elements_list.append(elements)
                urlpage = url + '&page=' + str(i)
                html = requests.get(urlpage)
                page = BeautifulSoup(html.content, 'html.parser')
                elements = extract_page_info(page)
                i += 1
                merkenindex.append(merk)
                modellenindex.append(model)
            
    total_elements = sum(len(inner_list) for inner_list in elements_list)
    return elements_list, merkenindex, modellenindex, total_elements
  
def scrape_data_df(element_list: list, merkenindex: list, modellenindex: list, progress_bar=None) -> pd.DataFrame:
    total_elements = sum(len(inner_list) for inner_list in element_list)
    property_list = []
    counter = 0
    i = 0
    for elements in element_list:

        url = construct_search_query(merkenindex[i], model=modellenindex[i], bmin=None, bmax=None)
        for element in elements:
            property_temp = extract_properties_of_car(element)
            for j in range(1, 4):
                property_temp[j] = int(property_temp[j])
            property_list.append([f'{merkenindex[i]} {modellenindex[i]}'] + property_temp)
            counter += 1
            
        i += 1
        progresscount = counter/total_elements
        if progress_bar is not None:
            progress_bar.progress(progresscount)
            if counter % 100 == 0:
                st.rerun()

    columns = ['Naam auto', 'Volledige naam', 'Prijs (euro)', 'Bouwjaar', 'Kilometer stand', 'Locatie', 'Website']
    df = pd.DataFrame(property_list, columns = columns)

    return df
# Testing:


# x=1

# merken = ['tesla']
# modellen = ['model-3']

# # test = get_elements(merken, modellen)

# # x= 1
# url = get_elements(merken, modellen, importEU=True)

x = 1
x=2
# df = scrape_data_df(url)

# df.to_excel(f'Resultaat_{merk}_{model}.xlsx')

# x=1