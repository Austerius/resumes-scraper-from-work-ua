import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

""" this script will create a new postgresql database with required table for 
 resume_scraper_from_work_ua project.
 Note: you need to download psycopg2 library first"""


def create_postgresql_db(user, password, new_db_name="work_ua_scraper", dbname='postgres',
                         host='localhost', port=5432):
    con = psycopg2.connect(user=user, password=password, dbname=dbname, host=host, port=port)
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)  # needed for execution of create database statement
    cur = con.cursor()
    db_exist = True
    # checking postgres db pg_catalog->pg_database for existence of new_db_name
    cur.execute("select datname from pg_database where datname=%s", (new_db_name, ))
    name = cur.fetchone()
    if name is None:
        db_exist = False
    else:
        print("Database '{}' already exist".format(new_db_name))
    if not db_exist:
        # creating new db only if it doesnt already exist
        print("Creating new Database '{}'".format(new_db_name))
        cur.execute("CREATE DATABASE {} ".format(new_db_name))  # placeholder %s cant be used here
    cur.close()
    con.close()


def create_db_table(user, password, dbname, host='localhost', port=5432):
    con = psycopg2.connect(user=user, password=password, dbname=dbname, host=host, port=port)
    cur = con.cursor()
    # Note: Postgresql 9.1 or higher need
    SQL = """CREATE TABLE IF NOT EXISTS resumes(
            id SERIAL,
            person_name VARCHAR(255) NOT NULL,
            resume_date DATE NOT NULL,
            photo BYTEA,
            position VARCHAR(255),
            salary INT4,
            full_time BOOL,
            part_time BOOL,
            from_home BOOL,
            birthday DATE,
            work_experience TEXT,
            education TEXT,
            additional_education TEXT,
            skills TEXT,
            languages TEXT,
            recommendations TEXT,
            additional_info TEXT,
            PRIMARY KEY (person_name, resume_date)
            )"""
    cur.execute(SQL)
    cur.connection.commit()
    cur.close()
    con.close()
if __name__ == "__main__":
    # here don't forgot to enter your own credential
    create_postgresql_db(user="postgres", password="Qwert1234")
    # enter your db name if you didn't use default one
    create_db_table(user="postgres", password="Qwert1234", dbname="work_ua_scraper")
