import requests
from bs4 import BeautifulSoup
import time
import re
import datetime
import psycopg2
# import html
""" This script will scrap IT specialists resumes(only if they have photo in them) from ukrainian site 'work.ua' 
    and save them to Postgres database.
    Current version of the script scraping only resumes in 'Kyiv' region, but you can change it by changing
    link inside 'category_city_url' variable. 
    Scraped fields: person_name, resume_date, photo, position, salary, employment_type(full_time, part_time,
                 from_home), birthday, work_experience, education, additional_education, skills, languages,
                 recommendations, additional_info.
    Before running this script, you need to create and set a Postgresql database (use create_postgresql_db.py script)
    Also, you need to download and install requests, BeautifulSoup and psycopg2 libraries
    Git repository with all related scripts here: https://github.com/Austerius/resumes-scraper-from-work-ua
    You'll find examples of html code from scraping pages in repository.
"""
# script was written by Alexander Shums'kii: https://github.com/Austerius/
base_url = "https://www.work.ua/"  # our site address
category_city_url = "resumes-kyiv-it/"  # city and category for search (in our case: IT category in Kiev)
page_finder_url = "?page="
user = "postgres"  # Db user, change to your own value
password = "Qwert1234"  # database password, change to your own value
dbname = "work_ua_scraper"  # db name, has default name given by create_postgresql_db.py script; change to you own
# n = 1  # n - it's our page numerator
pre_final_url = base_url + category_city_url + page_finder_url
# dictionary of personal info
pers_info = {"Опыт работы": "work_experience",
             "Образование": "education",
             "Дополнительное образование": "additional_education",
             "Профессиональные и другие навыки": "skills",
             "Знание языков": "languages",
             "Рекомендации": "recommendations",
             "Дополнительная информация": "additional_info"}

month_dictionary = {"января": "1",
                    "февраля": "2",
                    "марта": "3",
                    "апреля": "4",
                    "мая": "5",
                    "июня": "6",
                    "июля": "7",
                    "августа": "8",
                    "сентября": "9",
                    "октября": "10",
                    "ноября": "11",
                    "декабря": "12"}


# function for scraping info from resumes
def resume_parse(link):
    # forming an absolute link to the resume web page
    abs_link = base_url + link
    r_resume = requests.get(abs_link)
    # checking if our page is available
    if r_resume.status_code == 200:
        soup_resume = BeautifulSoup(r_resume.text, 'html.parser')
        # here we wanna parse only resume with photo in it
        # (well, we supposedly passed pages with photo already, but double check it )
        photo = soup_resume.findAll('div', {"class": "pick-full-load hidden-print"})
        if not photo:
            return  # exiting from this page, if there is no photo on it
        else:
            # getting relative photo link
            photo_link = photo[0].find("img").get("src")
            abs_photo_link = "https:" + photo_link
            r_photo = requests.get(abs_photo_link, stream=True)  # r_photo.content - our binary data
            # parsing/scraping information from resume
            # resume date will be here:
            temp = soup_resume.findAll('div', {"class": "add-top"})
            # going to use regular expressions for search resume date in temp[0] (need to optimize it later)
            resume_date_re = re.search("от(.*) </", str(temp[0]))  # search all that starts with 'от' and ends with '</'
            resume_date = resume_date_re.group(1)  # get only 1st parentheses group (date string)
            resume_date = resume_date.strip()
            day, month, year = resume_date.split(" ")
            # forming datetime.date value
            resume_datetime = datetime.date(int(year), int(month_dictionary[month]), int(day))
            # print(resume_date)  # string with resume date from html page
            # in this div we'll find: name, position, employment(full-time, part-time etc), birthday
            temp = soup_resume.findAll('div', {"class": "col-sm-8"})
            # getting a full name
            name_temp = temp[0].find('h1')
            name = name_temp.text
            # print(name)  # name from Html page
            # getting desired position
            position_temp = temp[0].find('h2')
            position_and_salary = position_temp.text
            position_and_salary = position_and_salary.strip()
            salary = None
            position = position_and_salary
            if "грн/мес" in position_and_salary:
                salary = position_and_salary.split(",")[-1]  # salary always last entry
                position = position_and_salary.strip(salary)
                position = position.strip(",")  # here we got desired job positions
                salary = salary.strip(". грн/мес")
                salary = re.sub(" +", "", salary)  # getting rid of spaces in salary number
                salary = int(salary)  # here we got our salary in int type
            # print(position_and_salary) #  position and salary from Html page
            # getting employment type
            temp_employment = temp[0].find('p', {'class': "text-muted"})
            employment_type = temp_employment.text
            full_time = False
            part_time = False
            from_home = False
            if "полная занятость" in employment_type.lower():
                full_time = True
            if "неполная занятость" in employment_type.lower():
                part_time = True
            if "удаленная работа" in employment_type.lower():
                from_home = True
            # print(employment_type)  # employment type string from Html page
            # getting birthday
            birthday_temp = temp[0].find('dd')
            try:
                birthday = (re.search("<dd>(.*) <s", str(birthday_temp))).group(1)
            except AttributeError:
                return  # don't write to db resume without person's birthday day
            day, month, year = birthday.split(" ")
            birthday_datetime = datetime.date(int(year), int(month_dictionary[month]), int(day))
            # print(birthday)  # birthday string from Html page
            # Now scraping main body of the resume
            main_body = ""
            for tag in soup_resume.find('h2', {"class": "cut-top"}).next_siblings:
                main_body += str(tag)
                if str(tag) == """<hr class="wide hidden-print"/>""":  # stop, when we reach this tag
                    break
            # dictionary with cleaned personal info
            parsed_info = {"work_experience": None,
                           "education": None,
                           "additional_education": None,
                           "skills": None,
                           "languages": None,
                           "recommendations": None,
                           "additional_info": None}
            temp_key = ""
            temp_string = ""
            write_string = False
            for line in main_body.splitlines():  # iterating through each line of main_body
                if '<h2 class="cut-top">' in line:
                    for key in pers_info:
                        # looking for the information block
                        if key in line:
                            temp_key = pers_info[key]
                            temp_string = ""
                            write_string = True
                            break
                if write_string:
                    temp_line = re.sub("<[^<]+?>", "", line)  # stripping form HTML tags
                    temp_line = re.sub("\s+", " ", temp_line)  # getting rid of tabs inside a line
                    temp_line = temp_line.strip()
                    if temp_line == "":
                        continue
                    # temp_line = html.escape(temp_string)  # escaping HTML that could be left after stripping
                    temp_string += temp_line + "\n"
                    # writing/rewriting 'cleaned' info block to appropriate section(represented by key)
                    parsed_info[temp_key] = temp_string
        # forming sql request for inserting mined data into database
        SQL = """INSERT INTO resumes( person_name, resume_date, photo, position, salary, full_time, part_time,
                 from_home, birthday, work_experience, education, additional_education, skills, languages,
                 recommendations, additional_info) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                  %s, %s, %s, %s)"""
        # connecting and writing to db
        con = psycopg2.connect(user=user, password=password, dbname=dbname)
        cur = con.cursor()
        try:
            cur.execute(SQL, (name, resume_datetime, r_photo.content, position, salary, full_time, part_time,
                              from_home, birthday_datetime, parsed_info["work_experience"], parsed_info["education"],
                              parsed_info["additional_education"], parsed_info["skills"], parsed_info["languages"],
                              parsed_info["recommendations"], parsed_info["additional_info"]))
            cur.connection.commit()
            print("{} resume has been written to database!".format(name))
        except psycopg2.IntegrityError:
            print("{} resume from {}  already in the database".format(name, resume_datetime))
            pass  # don't write already existing resume to database
        finally:
            cur.close()
            con.close()
        # for value in parsed_info.values():
        #     print(value)
    else:
        return  # exiting from function if response not '200'


def search_parser(n, m=0):
    """ This function will go through the 'work.ua' resumes search results and retrieve links
        to resumes with photo in it. Then, we pass resume link to the 'resume_parse' function.
        'n' - number of the starting search page;
        'm' - number of the ending search page.
        To scrap only one chosen page(n) of the search results - just input 'm' equal to 'n'
    """
    # exiting from parser, if our input parameters are incorrect
    if not isinstance(n, int):
        print("'n' parameter should be a positive(not zero) integer!")
        return
    else:
        if n < 1:
            print("'n' parameter should be a positive(not zero) integer!")
            return
    if not isinstance(m, int):
        print("'m' parameter should be a positive integer!")
        return
    else:
        if m < 0:
            print("'m' parameter should be a positive integer!")
            return
    # input check done
    reconnect_tries = 0
    max_reconnects = 3  # maximum number of reconnect tries (if status code not 200)
    step = 1
    if m != 0:
        if m < n:  # reversing search
            step *= -1
    # TODO: add an option for escaping redundant search through (resume_date -1 day) if resumes_date was already in db
    while True:
        final_url = pre_final_url + str(n)
        r_work = requests.get(final_url)
        if r_work.status_code == 200:  # if we get to the web page successfully
            soup_work = BeautifulSoup(r_work.text, 'html.parser')  # our html text is in request.text
            # now we need to find all blocks with search results:
            # required info is in div block with class="card card-hover resume-link card-visited card-photo"
            # we going to get only resume with photo
            search_blocks = soup_work.findAll('div', {'class': "card card-hover resume-link card-visited card-photo"})
            if not search_blocks:
                no_photo_blocks = soup_work.findAll('div', {'class': "card card-hover resume-link card-visited "})
                if not no_photo_blocks:
                    print("We found all resumes. Exiting from the scraper.")
                    break
                else:
                    continue  # this search page doesnt have resumes with photo
            else:
                for block in search_blocks:
                    # now we need to find first link to actual resume page in this block
                    resume_link = block.find('a').get("href")
                    # after we got resume link - parse contained info in our special function
                    resume_parse(resume_link)
                    time.sleep(1)  # wait time between scraping each single page
            # exiting from the loop if there was a search in range(n, m)
            print("Finished scraping from search page #{} ".format(n))
            if n == m:
                print("We found all resumes. Exiting from the scraper...")
                break
            n += step  # going to the next page of search results
        else:
            # if our status code not 200 - wait and retry several times or exit after all tries where unsuccessful
            time.sleep(3)
            reconnect_tries += 1
            if reconnect_tries > max_reconnects:
                print("Connection error. Exiting from script...")
                break
            else:
                print("Cant get access to url: {} . Retrying...".format(final_url))
                continue

if __name__ == "__main__":
    search_parser(n=1)  # n=1 - scraping all from the start of the search results


