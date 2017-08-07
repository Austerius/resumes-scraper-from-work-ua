import os
import psycopg2
import sys
import io
from PIL import Image
""" Little example how to retrieve bytea image data(photo field) from Postgresql database and save it to the hard drive.
    Run this script after 'create_postgresql_db.py' and 'resume_scraper_from_work_ua.py'
    Also, you need to install this libraries beforehand: Pillow, psycopg2.
    Script will create new directory with name 'photos' in the same directory, where 'retrieve_photo_from_db.py'
    file is located(or was called from). After that, photos from first 10 rows(variable n) in resumes table will be
    retrieved and saved to the ./photos directory.  
    Repository link: https://github.com/Austerius/resumes-scraper-from-work-ua
"""
# script was written by Alexander Shums'kii: https://github.com/Austerius/
# use your own values for db
user = 'postgres'  # db user name
password = "Qwert1234"  # password to db
dbname = 'work_ua_scraper'  # db name
host = 'localhost'
port = 5432

photo_dir = "photos"  # that's how we named folder to where resume's photos will be saved
# getting current working directory (from where script was run)
current_path = sys.path[0]  # the directory containing the script that was used to invoke the Python interpreter.
# print(os.path.dirname(os.path.realpath(__file__)))  # the same thing,
print("Current working directory is: {}".format(current_path))
saving_folder = os.path.join(current_path, photo_dir)
print("Resume's photos will be saved to: {}".format(saving_folder))
# creating 'photos' directory
if not (os.path.exists(saving_folder)):
    os.mkdir(saving_folder)
# opening connection to db
con = psycopg2.connect(user=user, password=password, dbname=dbname, host=host, port=port)
cur = con.cursor()
n = 10  # how much photos will be retrieved (first 'n' positions from the table)
cur.execute("SELECT COUNT(*) FROM resumes")
total_count = cur.fetchone()[0]  # total amount of rows in database table
if n > total_count:
    n = total_count
# forming SQL query:
SQL = """SELECT id, person_name, photo 
         FROM resumes
         LIMIT {}""".format(n)
cur.execute(SQL)
i = 1
# saving photos to the folder
while cur:
    try:
        person_id, person_name, person_photo = cur.fetchone()
    except TypeError:
        break  # exit when cur.fetchone() returns None
    person_name = person_name.strip()
    # forming unique photo name
    photo_name = person_name.replace(" ", "_") + "_" + str(person_id) + ".jpg"
    full_photo_path = os.path.join(saving_folder, photo_name)
    # getting byte array image
    img = Image.open(io.BytesIO(person_photo)).convert('RGB')  # some images need to be converted to "RGB" before saving
    print("Photo #{} saved to the disk".format(i))
    i += 1
    img.save(full_photo_path, format="JPEG")
cur.close()
con.close()
