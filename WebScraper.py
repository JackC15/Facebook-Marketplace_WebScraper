# Jack Canada
# Version: 0.0.1
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
import os
import time
from bs4 import BeautifulSoup
import re
import pandas as pd
import matplotlib.pyplot as plt

def Graph_Creation(x, y, title, data, make, model):
    #Analysis using charts
    plt.figure(figsize=(12, 6))
    plt.xlabel(x)
    plt.ylabel(y)
    plt.title(title)
    plt.xticks(data.index, rotation=45)
    plt.bar(data.index, data.values)
    plt.savefig(f'{make} {model} {x} vs {y}.png')
    plt.show()
    
    
def fbScraper():
    #Configure ChromeDriver
    chrome_install = ChromeDriverManager().install()
    folder = os.path.dirname(chrome_install)
    chromedriver_path = os.path.join(folder, "chromedriver.exe")

    #Base url
    #base_url = "https://www.facebook.com/marketplace/108483599175593/search?"
    base_url = input('Facebook Marketplace URL> ')

    #Search parameters
    min_price = input("Minimum Price> ")
    max_price = input("Maximum Price> ")
    min_mileage = 1000
    max_mileage = input("Maximum Mileage> ")
    min_year = input("Minimum Year> ")
    max_year = input("Maximum Year> ")
    transmission = input("Automatic or Manual> ").lower()
    make = input("Make> ")
    model = input("Model> ")
    radius = "805"

    #Initialize Browser
    options = Options()
    options.add_argument("--disable-notifications") #Disables Chrome Notifications
    browser = webdriver.Chrome(service = Service(chromedriver_path), options=options)
    browser.maximize_window()

    #Setup full url
    search_url = f"{base_url}minPrice={min_price}&maxPrice={max_price}&maxMileage={max_mileage}&maxYear={max_year}&minMileage={min_mileage}&minYear={min_year}&transmissionType={transmission}&query={make}{model}&radius={radius}&exact=false"
    browser.get(search_url)

    time.sleep(1.5)
    try:
        close_button = browser.find_element(By.XPATH, '//div[@aria-label="Close" and @role="button"]')
        close_button.click()
        print("Close button clicked!")
    except:
        print("Couldn't find close button")
        pass

    time.sleep(2)
    #Scroll down to load more vehicle listings
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    #Parse HTML
    html = browser.page_source
    #Create Beautiful Soup object from scraped HTML
    fb_soup = BeautifulSoup(html, 'html.parser')
    #End browser process after scraping website
    browser.quit()


    #Extract all info and put into lists
    titles_div = fb_soup.find_all('span', class_="x1lliihq x6ikm8r x10wlt62 x1n2onr6")
    titles_list = [title.text.strip() for title in titles_div]
    prices_div = fb_soup.find_all('span', class_="x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x xudqn12 x676frb x1lkfr7t x1lbecb7 x1s688f xzsf02u")
    prices_list = [price.text.strip() for price in prices_div]
    locations_miles_div = fb_soup.find_all('span', class_="x1lliihq x6ikm8r x10wlt62 x1n2onr6 xlyipyv xuxw1ft x1j85h84")
    locations_miles_list = [location.text.strip() for location in locations_miles_div]
    urls_div = fb_soup.find_all("div", class_="x9f619 x78zum5 x1r8uery xdt5ytf x1iyjqo2 xs83m0k x1e558r4 x150jy0e x1iorvi4 xjkvuk6 xnpuxes x291uyu x1uepa24")
    url_list = [url.find("a")["href"] for url in urls_div if url.find("a")]

    #Create expression to get city and state entries "City", "State"
    pattern = re.compile(r'(\w+(?:-\w+)?, [A-Z]{2})')
    #Make new list for adjusted mileage entries
    mileage_list = []

    #Iterate through original miles listing
    for i in locations_miles_list:
        mileage_list.append(i)
        
        if i == '':
            mileage_list.insert(-1, "0K miles")
        
        if pattern.match(i) and len(mileage_list) >= 2 and pattern.match(mileage_list[-2]):
            mileage_list.insert(-1, "0K miles")
            
    mileage_pattern = r'(\d+)K miles'
    mileage_pattern2 = r'(\d+)K miles · Dealership'
    location_pattern = r'(\w+(?:-\w+)?, [A-Z]{2})'

    mileage_clean = []
    location_clean = []

    for i in mileage_list:
        match_mileage = re.search(mileage_pattern, i)
        match_location = re.search(location_pattern, i) 

        if match_mileage:
            mileage_clean.append(int(match_mileage.group(1)) * 1000)
        if match_location:
            location_clean.append(match_location.group(1))

    #Add all of information into a list of dictionaries
    vehicles_list = []

    for i, item in enumerate(titles_list):
        cars_dict = {}
        
        title_split = titles_list[i].split()
        
        cars_dict["Year"] = int(title_split[0])
        cars_dict["Make"] = title_split[1]
        if 3 > len(title_split): 
            cars_dict["Model"] = '' 
        else: 
            cars_dict["Model"] = title_split[2]
        price_str = re.sub(r'[^\d.]','', prices_list[i])
        cars_dict["Price"] = int(price_str) if price_str.isdigit() else 0
        if i < len(mileage_clean):
            cars_dict["Mileage"] = mileage_clean[i]
        else:
            cars_dict["Mileage"] = None
        cars_dict["Location"] = location_clean[i]
        cars_dict["URL"] = url_list[i]
        vehicles_list.append(cars_dict)

    #Convert vehicles_list into pandas dataframe
    vehicles_df = pd.DataFrame(vehicles_list)
    vehicles_df['URL'] = 'https://facebook.com' + vehicles_df['URL'] #Adds facebook url to marketplace url
    filtered_df = vehicles_df[vehicles_df['Model'].str.lower().str.contains(model.lower())] #Makes sure no vehicles besides one we searched for are in the dataframe

    print(filtered_df)

    yearly_prices = filtered_df.groupby("Year")["Price"].mean()
    Graph_Creation('Year', 'Price', 'Average Price by Year', yearly_prices, make, model)
    
    yearly_mileage = filtered_df.groupby("Year")["Mileage"].mean()
    Graph_Creation('Year', 'Mileage', 'Average Mileage by Year', yearly_mileage, make, model)
    
    yearly_count = filtered_df.groupby("Year").size()
    Graph_Creation('Year', 'Number of Listings', 'Number of Listings by Year', yearly_count, make, model)

    file_name = f'{make} {model} Data.csv'
    folder_name = 'Data Spreadsheets' 
    relative_path = os.path.join(folder_name, file_name)
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    filtered_df.to_csv(relative_path, index=False)

    print("Done")
    
if __name__ == '__main__':
    fbScraper()