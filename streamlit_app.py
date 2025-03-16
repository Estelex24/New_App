import streamlit as st
import pandas as pd
from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(page_title="MyFridge", page_icon="🧊", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS to match the dark theme in the image
st.markdown("""
<style>
    .stApp {
        background-color: #1e1e1e;
    }
    .stTextInput, .stSelectbox, .stNumberInput {
        background-color: #2d2d2d;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    .blue-container {
        background-color: #6ea8d5;
        padding: 10px;
        border-radius: 5px;
        color: black;
        margin: 10px 0;
    }
    .main-header {
        color: white;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .dataframe {
        background-color: #2d2d2d !important;
    }
    div[data-testid="stDataFrame"] div[data-testid="stTable"] {
        background-color: #2d2d2d;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize connection to Supabase
@st.cache_resource
def init_connection():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        st.error("Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_KEY in your .env file.")
        st.stop()
    
    return create_client(url, key)

# Attempt to connect to Supabase
try:
    supabase = init_connection()
except Exception as e:
    st.error(f"Failed to connect to Supabase: {str(e)}")
    st.stop()

# App title
# st.markdown('<div class="main-header">MyFridge</div>', unsafe_allow_html=True)

# Function to fetch data from the items table
def fetch_items():
    response = supabase.table("items").select("*").order("id").execute()
    return pd.DataFrame(response.data)

# Function to insert a new item
def insert_item(name, quantity, shelf):
    data = {
        "name": name,
        "quantity": quantity,
        "shelf": shelf,
        "created_at": datetime.now().isoformat()
    }
    response = supabase.table("items").insert(data).execute()
    return response

# Function to update an item
def update_item(id, name, quantity, shelf):
    data = {
        "name": name,
        "quantity": quantity,
        "shelf": shelf
    }
    response = supabase.table("items").update(data).eq("id", id).execute()
    return response

# Function to delete an item
def delete_item(id):
    response = supabase.table("items").delete().eq("id", id).execute()
    return response

# Create two columns for the input fields
col1, col2 = st.columns(2)

# Input fields
with col1:
    st.markdown('<div class="blue-container">item</div>', unsafe_allow_html=True)
    with st.container():
        item_name = st.text_input("", placeholder="Enter item name", label_visibility="collapsed")

with col2:
    st.markdown('<div class="blue-container"></div>', unsafe_allow_html=True)
    with st.container():
        add_button = st.button("Add Item")

# Shelf selection
col3, col4 = st.columns(2)

with col3:
    st.markdown('<div class="blue-container">Fridge shelf</div>', unsafe_allow_html=True)
    with st.container():
        shelf_options = ["Top", "Middle", "Bottom", "Door", "Freezer"]
        shelf = st.selectbox("", options=shelf_options, label_visibility="collapsed")

with col4:
    st.markdown('<div class="blue-container"></div>', unsafe_allow_html=True)
    with st.container():
        quantity = st.number_input("", min_value=1, value=1, label_visibility="collapsed")

# Handle adding new items
if add_button and item_name:
    insert_item(item_name, quantity, shelf)
    st.success(f"Added {quantity} {item_name}(s) to the {shelf} shelf")
    # Clear input fields
    item_name = ""

# Display items in the fridge
items_df = fetch_items()

if not items_df.empty:
    # Optional: Format the timestamp for better readability
    if 'created_at' in items_df.columns:
        items_df['created_at'] = pd.to_datetime(items_df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Display the dataframe with styling
    st.dataframe(
        items_df,
        use_container_width=True,
        hide_index=False,
        column_order=["id", "name", "quantity", "shelf", "created_at"],
        column_config={
            "id": st.column_config.NumberColumn("id", help="Item ID", format="%d"),
            "name": st.column_config.TextColumn("name", help="Item name"),
            "quantity": st.column_config.NumberColumn("quantity", help="Item quantity", format="%d"),
            "shelf": st.column_config.TextColumn("shelf", help="Shelf location"),
            "created_at": st.column_config.DatetimeColumn("created_at", help="Date added", format="YYYY-MM-DD HH:mm:ss")
        }
    )
else:
    st.info("No items in your fridge yet. Add some using the form above.")

# Add item management section
st.markdown("---")
st.subheader("Manage Items")

# Create columns for editing/deleting
col_edit1, col_edit2, col_edit3, col_edit4 = st.columns(4)

with col_edit1:
    if not items_df.empty:
        item_ids = items_df["id"].tolist()
        selected_id = st.selectbox("Select item to edit/delete", options=item_ids)
        selected_item = items_df[items_df["id"] == selected_id].iloc[0] if selected_id else None
    else:
        st.info("No items to edit")
        selected_item = None

if selected_item is not None:
    with col_edit2:
        edit_name = st.text_input("Name", value=selected_item["name"])
        
    with col_edit3:
        edit_quantity = st.number_input("Quantity", min_value=1, value=int(selected_item["quantity"]))
        
    with col_edit4:
        edit_shelf = st.selectbox("Shelf", options=shelf_options, index=shelf_options.index(selected_item["shelf"]) if selected_item["shelf"] in shelf_options else 0)
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("Update Item"):
            update_item(selected_id, edit_name, edit_quantity, edit_shelf)
            st.success(f"Updated item: {edit_name}")
            st.rerun()
            
    with col_btn2:
        if st.button("Delete Item", type="primary"):
            delete_item(selected_id)
            st.success(f"Deleted item: {selected_item['name']}")
            st.rerun()
