import re
import csv
import sys
import argparse
from bs4 import BeautifulSoup
import urllib.request 
from argparse import ArgumentParser
import time
from fake_useragent import UserAgent
import random
from urllib.request import Request, urlopen
import zipcode
import datetime



ua = UserAgent(fallback= 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)') # From here we generate a random user agent
proxies = [] # Will contain proxies [ip, port]
all_nums = []
parser = argparse.ArgumentParser(description='test', formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-st', '--state', help='specify State.', required=True)
parser.add_argument('-m', '--miles', help='specify range in miles (10,20,50,100), default is 50.', nargs='?', default=50, type=int)
parser.add_argument('-d', '--depth', help='specify page depth (0-300 recommended). defualt is 5.', nargs='?', default=300, type=int)
parser.add_argument('-s', '--sort', help='specify sort type ((m)ost reviews, (b)est match, (r)ecent reviews). default is best match.', nargs='?', default='b', type=str)
parser.add_argument('-p', '--profession', help='''specify profession. default is all.
		((a)rchitect, (d)esign-build, (g)eneral-contractor,
		(h)ome-builders, (i)interior-designer, (k)itchen-and-bath, 
		(k)itchen-and-bath-(r)emodeling [kr], (l)andscape-architect, 
		(l)andscape-(c)ontractor [lc], (s)tone-pavers, (t)ile-stone-and-countertop, 
		(all) CAUTION - using 'all' could cause tens of thousands of page requests to be made)''', nargs='?', default='all', type=str)
args = parser.parse_args()


hzbaseurl = 'http://www.houzz.com/professionals'
knownlinks = []

# the goods will end up here
businesslist = []
state_abbreviation = ['AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','N','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']
# translate argument into corresponding URL chunk
def prof(p):
	return {

                # new added categories 
                'c': 'cabinets',
                'ca': 'carpenter',
                'dec': 'decks-and-patios',
                'p': 'driveways-and-paving',
                'f': 'fencing-and-gates',
                'fire': 'fireplace',
                'gd': 'garage-doors',
                'han': 'handyman',
                'iron': 'ironwork',
                'pwc': 'paint-and-wall-coverings',
                'sid': 'siding-and-exterior',
                'sc': 'specialty-contractors',
                'sta': 'staircases',
                'spc': 'stone-pavers-and-concrete',
                'wc': 'window-coverings',
                'w': 'windows',
                'hvac': 'hvac-contractors',
                'tile': 'electrical-contractors',
                'esar': 'environmental-services-and-restoration',
                'fur': 'furniture-refinishing-and-upholstery',
                'gals': 'garden-and-landscape-supplies',
                'las': 'lawn-and-sprinklers',
                'mov': 'movers',
                'pain': 'painters',
                'pc': 'pest-control',
                'gdr': 'garage-door-repair',
                'pc': 'plumbing-contractors',
                'rg': 'roofing-and-gutter',
                'sptas': 'septic-tanks-and-systems',
                'sapm': 'spa-and-pool-maintenance',
                'ts': 'tree-service',
                'cc': 'carpet-cleaners',
                'chim': 'chimney-cleaners',
                'exc': 'exterior-cleaners',
                'hc': 'house-cleaners',
                'rr': 'rubbish-removal',
                'wcc': 'window-cleaners',
                'door': 'doors',
                
		
                # original categories | "all" will do all categories that are in the dictonary

                'd': 'design-build',
		'g': 'general-contractor',
		'h': 'home-builders',
		'i': 'interior-designer',
		'k': 'kitchen-and-bath',
		'kr': 'kitchen-and-bath-remodeling',
		'l': 'landscape-architect',
		'lc': 'landscape-contractor',
		's': 'stone-pavers-and-concrete',
		't': 'tile-stone-and-countertop',
		'all': [ 'design-build', 'general-contractor', 'home-builders', 'interior-designer', 'kitchen-and-bath', \
				'kitchen-and-bath-remodeling', 'landscape-architect', 'landscape-contractor','stone-pavers-and-concrete', \
				'tile-stone-and-countertop','cabinets','carpenter','decks-and-patios','driveways-and-paving','fencing-and-gates',\
                        'fireplace','garage-doors','handyman','ironwork','paint-and-wall-coverings','siding-and-exterior','specialty-contractors',\
                        'staircases','window-coverings','windows','hvac-contractors','electrical-contractors',\
                        'environmental-services-and-restoration','furniture-refinishing-and-upholstery','garden-and-landscape-supplies',\
                        'lawn-and-sprinklers','movers','painters','pest-control','garage-door-repair','plumbing-contractors','roofing-and-gutter',\
                        'septic-tanks-and-systems','spa-and-pool-maintenance','tree-service','carpet-cleaners','chimney-cleaners','exterior-cleaners',\
                        'house-cleaners','rubbish-removal','window-cleaners','doors']
       
	}.get(p, 'all')
	
# do the same here
def sorttype(s):
	return {
		'm': 'sortReviews',
		'b': 'sortMatch',
		'r': 'sortRecentReviews'
	}.get(s, 'sortMatch')

def zip_scrape():

	state = args.state
	state_zips = []

	baseurl = 'https://www.unitedstateszipcodes.org/'
	link_zip = '{0}/{1}/#zips-list'.format(baseurl,state)

	zip_req = Request(link_zip)

	zip_req.add_header('User-Agent', ua.random)
	zip_doc = urlopen(zip_req).read().decode('utf8')

	zip_soup = BeautifulSoup(zip_doc, 'html.parser')
	zip_table = zip_soup.find(id='list-group')

	# Save proxies in the array
	
	zips = str(zip_soup.find_all('div', {'class' : 'col-xs-12 prefix-col1'}))

	zips = zips.split('/')

	zips = [item for item in zips if '>' not in item]

	

	return zips
def prox():

	proxies_1 = []
	proxies_2 = []

	try:
		proxies_req_1 = Request('https://free-proxy-list.net/anonymous-proxy.html')
		proxies_req_1.add_header('User-Agent', ua.random)
		proxies_doc_1 = urlopen(proxies_req_1,timeout = 4).read().decode('utf8')

		soup_1 = BeautifulSoup(proxies_doc_1, 'html.parser')
		proxies_table_1 = soup_1.find(id='proxylisttable')

		# Save proxies in the array
		for row in proxies_table_1.tbody.find_all('tr'):
			

			proxies_1.append({
				'ip':row.find_all('td')[0].string,
				'port':row.find_all('td')[1].string,
				'https':row.find_all('td')[6].string
				})

			for item in proxies_1:
				if item['https'] == 'no':
					proxies.append(item)

				else:

					proxies_1.remove(item)
		print('---------------------------------------------')
		print('Proxy Set 1 Grab was successful')
		print('---------------------------------------------')
	except:
		print('+++++++++++++++++++++++++++++++++++++++++++++')
		print('Proxy Set 1 Grab was unsuccessful')
		print('+++++++++++++++++++++++++++++++++++++++++++++')

	try:
		proxies_req_2 = Request('https://free-proxy-list.net')
		proxies_req_2.add_header('User-Agent', ua.random)
		proxies_doc_2 = urlopen(proxies_req_2,timeout = 4).read().decode('utf8')

		soup_2 = BeautifulSoup(proxies_doc_2, 'html.parser')
		proxies_table_2 = soup_2.find(id='proxylisttable')

		# Save proxies in the array
		for row in proxies_table_2.tbody.find_all('tr'):
			

			proxies_2.append({
				'ip':row.find_all('td')[0].string,
				'port':row.find_all('td')[1].string,
				'https':row.find_all('td')[6].string
				})

			for item in proxies_2:
				if item['https'] == 'no':
					proxies.append(item)

				else:

					proxies_2.remove(item)

		print('---------------------------------------------')
		print('Proxy Set 2 Grab was successful')
		print('---------------------------------------------')
		print('')
	except:

		print('+++++++++++++++++++++++++++++++++++++++++++++')
		print('Proxy Set 2 Grab was unsuccessful')
		print('+++++++++++++++++++++++++++++++++++++++++++++')
		print('')

	print(len(proxies))
def get_links(profession,zipcode):
	#this creates a list of links
	links = []
	
	miles = args.miles
	sortby = sorttype(args.sort)

	pagedepth = int(args.depth) * 15


	for p in profession:

		for page in range(0, pagedepth, 15):
			hzsearchurl = '{0}/{1}/c/{2}/d/{3}/{4}/p/{5}'.format(hzbaseurl, profession, zipcode, miles, sortby, page)

			links.append(hzsearchurl)

	return links
	
def create_soup(link):

	# create_soup takes the link and creates soup, from there it gets the phone numbers and returns them to the clean_nums function
	print('')
	print('+++++++++++++++++++++++++++++++')
	print(link)
	print('+++++++++++++++++++++++++++++++')
	print('')
	checker = True
	numbers = []

	
	while checker == True:

		print("Going through loop")
		proxy_index = random.randint(0, len(proxies) - 1)
		proxy = proxies[proxy_index]
		
		try:

			req = Request(link)
			req.add_header('User-Agent', ua.random)
			req.set_proxy(proxy['ip'] + ':' + proxy['port'], 'http')
			req_doc = urlopen(req,timeout = 4).read().decode('utf8')
			print('Using IP: ' + str(proxy))
			checker = False
		
		except: # If error, delete this proxy and find another one
			print("delete: " + str(proxies[proxy_index]))
			del proxies[proxy_index]
			
			if len(proxies) < 200:
				prox()
			checker = True
			

	soup = BeautifulSoup(req_doc,"lxml")

	try:
		
		phonenumber = str(soup.find_all('span', {'class' : 'pro-list-item--text'}))

	except AttributeError:
		phonenumber = 'Phone:N/A'


	print ("")
	print ("")

	split_numbers = phonenumber.split(',')
	
	
	return split_numbers

def clean_nums(numbers,links):
	#this function takes the dirty numbers and cleans them

	cleaned = []
	just_num = []

	for item in numbers:
		
		if "Click to Call" in item:
			
			
			item = item.replace('</a>','|')
			item = item.replace('</span>','|')
			
			cleaned.append(item)


	for item in cleaned:

		item = item.split('|')

		if item[1] not in all_nums:
		
			just_num.append(item[1])
			all_nums.append(item[1])
			print(item[1])
			print('===================================')

	
	if not just_num:
		print('++++++++++++++++++++++++++++++++++++++++')
		print('Could not find new numbers!')
		print('++++++++++++++++++++++++++++++++++++++++')
		del links[:]


	return just_num

		


def writemasterCSV(numbers,state,date):
	# this creates a file that holds all of the phone numbers

	filename = str(state) +'_'+'houzz_'+ date + '.csv'
	with open(filename, 'a') as ofile:
		writer = csv.writer(ofile)
		for num in numbers:
			writer.writerow([num])

def main(): 


	date = datetime.datetime.today().strftime('%m-%d-%y')
	state = args.state
	profession = prof(args.profession)
	zipcode = zip_scrape()
	prox()
	num_of_categories = len(profession) + 1
	num_of_zips = len(zipcode) + 1
	if type(profession) is list:
		print('caution: you have chosen "all". if you have a large page depth set, you might want to get a coffee..')
	
	for z in zipcode:
		z_index = zipcode.index(z) + 1

		print('------------------------------------------------------------')
		print('Zipcode: '+ str(z_index) + ' of '+ str(num_of_zips))
		print('------------------------------------------------------------')


		for p in profession:
			category_index = profession.index(p) + 1
			print('------------------------------------------------------------')
			print('Category: '+ str(category_index) + ' of '+ str(num_of_categories))
			print('------------------------------------------------------------')
			
			if len(proxies) < 200:
				prox()
			links = get_links(p,z)
			
			for link in links:
				numbers = create_soup(link)
				clean_numbers = clean_nums(numbers,links)
				writemasterCSV(clean_numbers,state,date)
				


	print('------------------------------------------------------------')
	print('The Scraper Has Finshed!')
	print('------------------------------------------------------------')
	
if __name__ == '__main__':

	main()
