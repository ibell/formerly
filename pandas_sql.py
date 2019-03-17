import pandas
from sqlalchemy import create_engine
engine = create_engine('sqlite:///test.db')
df = pandas.read_sql_table('result', engine)
print(df)