import requests
from bs4 import BeautifulSoup
import time
import re
import datetime
# import html

base_url = "https://www.work.ua/"  # our site address
category_city_url = "resumes-kyiv-it/"  # city and category for search (in our case: IT category in Kiev)
page_finder_url = "?page="
n = 1  # n - it's our page numerator
pre_final_url = base_url + category_city_url + page_finder_url
# print(pre_final_url)
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
        # print(soup_resume)
        photo = soup_resume.findAll('div', {"class": "pick-full-load hidden-print"})
        # TODO download photo from here
        #print(photo)
        if not photo:
            return  # exiting from this page, if there is no photo on it
        else:
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
            print(resume_datetime)
            print(resume_date)
            # in this div we'll find: name, position, employment(full-time, part-time etc), birthday
            temp = soup_resume.findAll('div', {"class": "col-sm-8"})
            # print(temp)
            # getting a full name
            name_temp = temp[0].find('h1')
            name = name_temp.text
            print(name)
            # getting desired position
            position_temp = temp[0].find('h2')
            position_and_salary = position_temp.text
            position_and_salary = position_and_salary.strip()
            salary = None
            position = position_and_salary
            if "грн/мес" in position_and_salary:
                salary = position_and_salary.split(",")[-1]
                position = position_and_salary.strip(salary)
                position = position.strip(",")  # here we got desired job positions
                salary = salary.strip(". грн/мес")
                salary = re.sub(" +", "", salary)
                salary = int(salary)  # here we got our salary in int type
            print(position)
            print(salary)
            # TODO categorize position, maybe ditch a salary field(since not all filling this field)
            print(position_and_salary)
            # getting employment type
            temp_employment = temp[0].find('p', {'class': "text-muted"})
            employment_type = temp_employment.text
            # TODO categorize employment type (use dictionary of types)
            print(employment_type)
            # getting birthday
            birthday_temp = temp[0].find('dd')
            birthday = (re.search("<dd>(.*) <s", str(birthday_temp))).group(1)
            # TODO transform birthday into datetime
            print(birthday)
            # Now scraping main body of the resume
            main_body = ""
            for tag in soup_resume.find('h2', {"class": "cut-top"}).next_siblings:
                main_body += str(tag)
                if str(tag) == """<hr class="wide hidden-print"/>""":
                    break
            #print(main_body)
            parsed_info = {}  # dictionary with cleaned personal info
            temp_key = ""
            temp_string = ""
            write_string = False
            for line in main_body.splitlines():  # iterating through each line of main_body
                #print(line)
                if '<h2 class="cut-top">' in line:
                   # print(line)
                    for key in pers_info:
                        # looking for the information block
                        if key in line:
                            #print(key, pers_info[key])
                            temp_key = key
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
        # TODO write parsed_info into database
        for value in parsed_info.values():
            print(value)
    else:
        return  # exiting from function if response not '200'



# TODO starting main loop here
final_url = pre_final_url + str(n)
r_work = requests.get(final_url)
# print(final_url)
print(r_work.status_code)
if r_work.status_code == 200:  # if we get to the web page successfully
    soup_work = BeautifulSoup(r_work.text, 'html.parser')  # our html text is in request.text
    # now we need to find all blocks with search results:
    # required info is in div block with class="card card-hover resume-link card-visited card-photo"
    # we going to get only resume with photo
    search_blocks = soup_work.findAll('div', {'class': "card card-hover resume-link card-visited card-photo"})
    if not search_blocks:
        no_photo_blocks = soup_work.findAll('div', {'class': "card card-hover resume-link card-visited "})
        if not no_photo_blocks:
            # TODO we exiting from main loop here
            print("WE found all and need to exit from the loop")
        else:
            #TODO continue main loop here
            pass # continue
    else:
        for block in search_blocks:
            # now we need to find first link to actual resume page in this block
            # print(block)
            resume_link = block.find('a').get("href")
            # print(resume_link)
            # after we got resume link - parse contained info in our special function
            resume_parse(resume_link)
            time.sleep(1)
    n += 1  # going to the next page of search results
else:
    # TODO if our status code not 200 - wait and retry several times or exit after all tries where unsuccessful
    pass


