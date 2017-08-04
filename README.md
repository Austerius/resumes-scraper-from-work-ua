# resumes-scraper-from-work-ua
script for scraping resumes from work.ua web site
<p>Main script  has name <i>"resume_scraper_from_work_ua.py"</i>. When executed, it will scrap
<b>IT specialists resumes</b>(only if they have photo in them) from ukrainian site 'www.work.ua' 
    and save them to Postgres database.<br/>
    This particular version of the script scraping only resumes in 'Kyiv' region, but you can change it by changing
    link inside 'category_city_url' variable. 
 </p>
   <b>Scraped fields:</b> 
    <li>person_name</li>
    <li>resume_date - date, when resume was uploaded to the site (Will not scrap same resume for particular date twice).</li>
    <li>photo - person's photo in binary format</li>
    <li>position - position, resume applying for</li>
    <li>salary- desired salary</li> 
    <li> employment_type - (full_time, part_time,from_home)</li>
    <li>birthday - person's birthday</li>
    <li>personal information - work_experience, education, additional_education, skills, languages,
                    recommendations, additional_info(some filds can be empty).</li> 
   <p> <b>NOTE:</b> before running <i>"resume_scraper_from_work_ua.py"</i> script,
   you need to create and set up a Postgresql database (use <i>'create_postgresql_db.py'</i> script for this purpose).
    Also, you need to <b>download and install:</b> requests, BeautifulSoup and psycopg2 libraries.<br/>
    You'll find examples of html code from scraping pages in this repository.</p>
