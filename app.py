import streamlit as st
import pandas as pd
import re
import base64
import numpy as np
import io
from pypdf2 import PdfReader

def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_product_details(line):
    parts = line.strip().split()
    if len(parts) >= 2:
        product_code = parts[0]
        quantity_match = re.search(r'(\d+)', parts[-1])
        if quantity_match:
            quantity = quantity_match.group(1)
            return product_code, quantity
    return None, None

def get_binary_file_downloader_html(bin_file, file_label='File'):
    bin_str = base64.b64encode(bin_file).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{file_label}">Download {file_label}</a>'
    return href

uploaded_file_pdf = st.file_uploader("Choose a PDF file", type="pdf")
uploaded_file_excel = st.file_uploader("Choose an Excel file", type="xlsx")

if uploaded_file_pdf is not None and uploaded_file_excel is not None:
    pdf_text = extract_text_from_pdf(uploaded_file_pdf)
    lines = pdf_text.split('\n')
    data = [extract_product_details(line) for line in lines if line.strip() and extract_product_details(line)[1] is not None]
    
    df = pd.DataFrame(data, columns=["Product Code", "Quantity"])
    df['Quantity'] = df['Quantity'].astype(int)
    df['Product Code'] = df['Product Code'].astype(str).str.strip().str.upper()
    df = df.groupby("Product Code").sum().reset_index()
    
    inventory_df = pd.read_excel(uploaded_file_excel, usecols='C')
    inventory_df.columns = ['LOTNo.']
    inventory_df['LOTNo.'] = inventory_df['LOTNo.'].astype(str).str.strip().str.upper()
    
    merged_df = pd.merge(inventory_df, df, left_on='LOTNo.', right_on='Product Code', how='left')
    merged_df = merged_df[['LOTNo.', 'Quantity']]
    merged_df['Quantity'].fillna(0, inplace=True)
    merged_df['Quantity'].replace(0, np.nan, inplace=True)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        merged_df.to_excel(writer, sheet_name='Sheet1', index=False)
    
    binary_excel = output.getvalue()  
    st.markdown(get_binary_file_downloader_html(binary_excel, 'Merged_YourFileNameHere.xlsx'), unsafe_allow_html=True)
