from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.postgres_hook import PostgresHook
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

def fetch_amazon_books():
    url = 'https://www.amazon.com/s?i=stripbooks&rh=n%3A5'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    titles = [item.text.strip() for item in soup.select('.s-title')]
    authors = [item.text.strip() for item in soup.select('.s-author')]
    prices = [item.text.strip() for item in soup.select('.s-price')]
    ratings = [item.text.strip() for item in soup.select('.s-rating')]

    books_data = pd.DataFrame({'title': titles, 'author': authors, 'price': prices, 'ratings': ratings})
    books_data.drop_duplicates(inplace=True)

    # store the cleaned data typically
    return books_data.to_dict(orient='records')

def clean_books_data(ti):
    books_data = ti.xcom_pull(task_ids='fetch_books')
    cleaned_data = []

    for book in books_data:
        book['price'] = float(book['price'].replace('$', '')) if '$' in book['price'] else 0
        book['rating'] = float(book['rating'].split()[0]) if book['rating'] else 0
        cleaned_data.append(book)
    
    ti.xcom_push(key='cleaned_books', value=cleaned_data)

def load_books_data(ti):
    cleaned_books = ti.xcom_pull(key='cleaned_books', task_ids='clean_books')
    hook = PostgresHook(postgres_conn_id='books_db')
    conn = hook.get_conn()
    cursor = conn.cursor()

    insert_query = """ INSERT INTO books (title, author, price, rating) VALUES (%s, %s, %s, %s) """
    for book in cleaned_books:
        cursor.execute(insert_query, (book['title'], book['author'], book['price'], book['rating']))
    
    conn.commit()
    cursor.close()
    conn.close()


with DAG(dag_id='fetch_and_store_amazon_books', default_args=default_args, description='A DAG to fetch, clean, and load amazon books data into a postgresql database', 
         schedule='@daily', start_data=datetime(2024, 1,1), catchup=False) as dag:
    # Task 1: Fetch book data from amazon
    fetch_task = PythonOperator(task_id='fetch_books', python_callable=fetch_amazon_books)
    clean_task = PythonOperator(task_id='clean_books', python_callable=clean_books_data)
    load_task = PythonOperator(task_id='load_books', python_callable=load_books_data)

    # task dependencies
    fetch_task >> clean_task >> load_task
