import os
SQLALCHEMY_DATABSE_URI=os.getenv('SQLALCHEMY_DATABASE_URI')
SECRET_KEY = os.getenv('SUPERSET_SECRET_KEY')

ALERT_REPORTS = True