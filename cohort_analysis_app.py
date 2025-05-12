# Loading the data
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
import numpy as np
import streamlit as st


df = pd.read_csv("dataset/year_2009-2010.csv", encoding="latin-1")
orders = df[["InvoiceDate", "Customer ID", "Price", "Quantity", "Invoice", "Description"]]

# Basic cleaning
orders.dropna(inplace=True)
orders = orders.drop_duplicates()
orders["revenue"] = orders["Price"] * orders["Quantity"]
orders.rename(columns={"Customer ID": "customer_id", "InvoiceDate": "order_date", "Invoice": "order_id"}, inplace=True)
orders.drop(columns=["Price", "Quantity"], inplace=True)

# Display a sample of the data
st.subheader("Preview of Orders Dataset")
st.write(orders.head())

# Simple analysis: show descriptive stats
st.subheader("Descriptive Statistics")
st.write(orders.describe())

# Example: Visualization using matplotlib/seaborn
st.subheader("Revenue Distribution")
fig, ax = plt.subplots()
sns.histplot(orders["revenue"], bins=50, ax=ax)
st.pyplot(fig)