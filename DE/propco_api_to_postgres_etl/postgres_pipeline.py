# import libraries
import json
import requests
import pandas as pd
import csv
import psycopg2

# extraction layer
url = "https://realty-mole-property-api.p.rapidapi.com/randomProperties"

querystring = {"limit":"200000"}

headers = {
	"x-rapidapi-key": "57015117a6msh483a52f18858c6ap1ce26bjsnf768f7285631",
	"x-rapidapi-host": "realty-mole-property-api.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)
data = response.json()

filename = 'propertyRecords.json'
with open(filename, 'w') as file:
    json.dump(data, file, indent=5)


property_json_df = pd.read_json('propertyRecords.json')

# Transformatio Layer
# 1st step, convert dictionary column to string
property_json_df['features'] = property_json_df['features'].apply(json.dumps)

# 2nd step: replace NaN values with appropriate defaults or remove row/columns as neccessary
property_json_df.fillna({
    'assessorID': 'Unknown',
    'legalDescription': 'Not Available',
    'squareFootage': 0,
    'subdivision': 'Not Available',
    'yearBuilt': 0,
    'bathrooms': 0,
    'lotSize': 0,
    'propertyType': 'Unknown',
    'lastSalePrice': 0,
    'lastSaleDate': 'Not Available',
    'features': 'None',
    'taxAssessment': 'Not Available',
    'owner': 'Unknown',
    'propertyTaxes': 'Not Available',
    'bedrooms': 0,
    'ownerOccupied': 0,
    'zoning': 'Unknown',
    'addressLine2': 'Not Available'
}, inplace=True)

# create the fact table
fact_columns = ['addressLine1', 'city', 'state', 'zipCode', 'formattedAddress', 'squareFootage', 'yearBuilt', 'bathrooms', 'bedrooms', 'lotSize', 'propertyType', 'longitude', 'latitude']
fact_table = property_json_df[fact_columns]

# create location dimension
location_dim = property_json_df[['addressLine1','city','state', 'zipCode', 'county', 'longitude', 'latitude']].drop_duplicates().reset_index(drop=True)
location_dim.index.name = 'location_id'


# create sales dimension
sales_dim = property_json_df[['lastSalePrice', 'lastSaleDate']].drop_duplicates().reset_index(drop=True)
sales_dim.index.name = 'sales_id'


# create property features dimension
features_dim = property_json_df[['features', 'propertyType', 'zoning']].drop_duplicates().reset_index(drop=True)
features_dim.index.name = 'features_id'


fact_table.to_csv('property_fact.csv', index=False)
location_dim.to_csv('location_dimension.csv', index=True)
sales_dim.to_csv('sales_dimension.csv', index=True)
features_dim.to_csv('features_dimension.csv', index=True)

# loading layer
# develop a function to connect to pgadmin
def get_db_connection():
    connection = psycopg2.connect(host='127.0.0.1', database='postgres', user='isaacoduh', password='root')
    return connection

# connect to sql database
conn = get_db_connection()

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    create_table_query = '''
        CREATE SCHEMA IF NOT EXISTS propco;

        DROP TABLE IF EXISTS propco.fact_table;
        DROP TABLE IF EXISTS propco.location_dim;
        DROP TABLE IF EXISTS propco.sales_dim;
        DROP TABLE IF EXISTS propco.features_dim;

        CREATE TABLE propco.fact_table (
            addressLine1 VARCHAR(255),
            city VARCHAR(100),
            state VARCHAR(50),
            zipCode INTEGER,
            formattedAddress VARCHAR(255),
            squareFootage FLOAT,
            yearBuilt FLOAT,
            bathrooms FLOAT,
            bedrooms FLOAT,
            lotSize FLOAT,
            propertyType VARCHAR(100),
            longitude FLOAT,
            latitude FLOAT
        );

        CREATE TABLE propco.location_dim (
            location_id SERIAL PRIMARY KEY,
            addressLine1 VARCHAR(255),
            city VARCHAR(100),
            state VARCHAR(50),
            zipCode INTEGER,
            county VARCHAR(100),
            longitude FLOAT,
            latitude FLOAT
        );

        CREATE TABLE propco.sales_dim(
            sales_id SERIAL PRIMARY KEY,
            lastSalePrice FLOAT,
            lastSaleDate DATE
        );

        CREATE TABLE propco.features_dim(
            features_id SERIAL PRIMARY KEY,
            features TEXT,
            propertyType VARCHAR(100),
            zoning VARCHAR
        );
    '''
    cursor.execute(create_table_query)
    conn.commit()
    cursor.close()
    conn.close()

create_tables()

def load_data_from_csv_to_tables(csv_path, table_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader) # skip the header
        for row in reader:
            placeholders = ", ".join(['%s'] * len(row))
            query = f'INSERT INTO {table_name} VALUES ({placeholders});'
            cursor.execute(query, row)
    conn.commit()
    cursor.close()
    conn.close()

# fact table
fact_csv_path = r'/Users/isaacoduh/DevSandbox/data_portfolio/DE/propco_api_to_postgres_etl/property_fact.csv'
load_data_from_csv_to_tables(fact_csv_path, 'propco.fact_table')

# locatioin dimension table
fact_csv_path = r'/Users/isaacoduh/DevSandbox/data_portfolio/DE/propco_api_to_postgres_etl/location_dimension.csv'
load_data_from_csv_to_tables(fact_csv_path, 'propco.location_dim')

# features dimension table
fact_csv_path = r'/Users/isaacoduh/DevSandbox/data_portfolio/DE/propco_api_to_postgres_etl/features_dimension.csv'
load_data_from_csv_to_tables(fact_csv_path, 'propco.features_dim')

# create function to load data to tables
def load_data_from_csv_to_sales_tables(csv_path, table_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        
        next(reader) # skip the header row
        for row in reader:

            # convert empty strings (or 'Not available') in date column
            row = [None if (cell == '' or cell =='Not Available' or cell =='Not available') and col_name == 'lastSaleDate' else cell for cell, col_name in zip(row, ['sales_id', 'lastSalePrice', 'lastSaleDate'])]
            placeholders = ", ".join(['%s'] * len(row))
            query = f'INSERT INTO {table_name} VALUES ({placeholders});'
            cursor.execute(query, row)
            

sales_dim_columns = ['sales_id', 'lastSalePrice', 'lastSaleDate']

fact_csv_path = r'/Users/isaacoduh/DevSandbox/data_portfolio/DE/propco_api_to_postgres_etl/sales_dimension.csv'
load_data_from_csv_to_sales_tables(fact_csv_path, 'propco.sales_dim')

print("Process Complete Notification: Successfully setup pipeline...")