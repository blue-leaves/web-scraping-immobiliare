import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

# First step: scraping the total number of pages from the lower half of the homepage
site = requests.get('https://www.immobiliare.it/vendita-case/torino/?criterio=rilevanza')
soup = BeautifulSoup(site.text, 'lxml')

pages = soup.find_all('div', {'class': 'in-pagination__item hideOnMobile in-pagination__item--disabled'})

last_page = int(pages[2].getText())

# Second step: creating a while loop to extract the url of each ad for each page

idx = 1
urls = []

while idx <= last_page:
    url = 'https://www.immobiliare.it/vendita-case/torino/?criterio=rilevanza&pag=' + str(idx)
    idx += 1
    site = requests.get(url)
    soup = BeautifulSoup(site.text, 'lxml')
    ads = soup.find_all('a', {'class': 'in-card__title'})
    for ad in ads:
        urls.append(re.findall(r'(?=https).*(?=" title)', str(ad)))
        
# Third step: creating a for loop to build a list of lists - to convert to a pandas DataFrame - for storing all the variables needed

row = []

for url in urls:
    ad = requests.get(url[0])
    soup = BeautifulSoup(ad.text, 'lxml')
    
    listing = soup.find('section', {'class': 'im-structure__mainContent'})
    
    # date of publication
    date = listing.find('dd').getText().replace('\n', '').strip().split(' - ')[-1]
    
    # list of appartments stored in the same url
    listing_appartments = listing.find_all('ul', {'class': 'nd-list im-properties__list'})
    
    if listing_appartments:
        
        for ad in listing_appartments:
            appartments = ad.find_all('li', {'class': 'nd-list__item im-properties__item js-units-track'})
            
            for appartment in appartments:
                
                h = []
                
                # discounted
                discounted = 0
                
                # title
                title = appartment.find('a')
                href = 'https://www.immobiliare.it' + (title['href'])
                app = requests.get(href)
                soup = BeautifulSoup(app.text, 'lxml')
                title = soup.find('span', {'class': 'im-titleBlock__title'}).getText()
                
                h.append(title)
                h.append(date)
                
                # price
                price = appartment.find('li',
                                        {'class': 'nd-list__item im-mainFeatures__price'}).find('div').getText().replace('\n','').strip()
                
                # other variables
                amenities = appartment.find_all('span', {'class': 'im-mainFeatures__value'})
                
                # checking for discount
                if 'Prezzo diminuito' in price:
                    discounted = 1
                    price = re.findall(r'(€)(.*?)\1', price)
                    price = ''.join(price[0])
                    h.append(price)
                else:
                    h.append(price)
                    
                h.append(discounted)
                
                for _ in amenities:
                    item = _.getText().replace('\n','').strip()
                    if item != '':
                        h.append(' '.join(item.split()))
                        
                row.append(h)
    else:
        
        # title
        title = listing.find('span', {'class': 'im-titleBlock__title'}).getText()
        
        # discount
        discounted = 0
    
        # price
        price = listing.find('li', {'class': 'nd-list__item im-mainFeatures__price'}).find('div').getText().replace('\n', '').strip()
        
        # removing auction
        if 'da €' not in price:

            h = []
            h.append(title)
            h.append(date)
            
            # checking for discount
            if 'Prezzo diminuito' in price:
                discounted = 1
                price = re.findall(r'(€)(.*?)\1', price)
                price = ''.join(price[0]).strip()
                h.append(price)

            else:
                h.append(price)
            
            h.append(discounted)
            
            # other variables
            amenities = listing.find_all('span', {'class': 'im-mainFeatures__value'})
            
            for _ in amenities:
                item = _.getText().replace('\n','').strip()
                if item != '':
                    h.append(' '.join(item.split()))
                    
            row.append(h)

df = pd.DataFrame(row, columns=['title', 'date', 'price', 'is_discounted', 'locals', 'surface', 'bathrooms', 'floor'])

# Fourth step: convert DataFrame into a csv file

df.to_csv('data.csv', sep=',', header=True, index=False)