from flask import Flask, render_template, request, redirect, url_for
from bs4 import BeautifulSoup
import requests
import threading


app = Flask(__name__)

listings = {}
maxprice = None
minprice = None
maxdate = None
sort = 'date'
exclude = []
include = []
location = []

@app.route("/error",)
def error():
	return("<h1>no results found</h1>")

@app.route("/search/",methods=['GET', 'POST'])
def search():
	global maxprice,minprice,maxdate,sort,include,exclude
	if listings == {}:
		return redirect(url_for('error'))
	if request.method == "POST":
		value = request.form.get("maxprice")
		if value != "":
			maxprice = value
		if value == "none":
			maxprice = None
		value2 = request.form.get("minprice")
		if value2 != "":
			minprice = value2
		if value == "none":
			minprice = None
		value3 = request.form.get("maxdate")
		if value3 != "":
			maxdate = value3
		if value == "none":
			maxdate = None
		value4 = request.form.get("include")
		print(value4)
		if value4 != "":
			if "," in value4:
				values = value4.split(",")
				for value in values:
					include.append(value)
			else:
				include.append(value4)
		if value4 == "none":
			exclude = []
		value5 = request.form.get("exclude")
		if value5 != "":
			if "," in value5:
				values = value5.split(",")
				for value in values:
					exclude.append(value)
			else:
				exclude.append(value5)
		if value5 == "none":
			exclude = []
		print(maxdate)
		sort = request.form.get("sort")
		poby = ["Colombo","Gampaha","Kandy","kalutara","Kurunegala"]
		for item in poby:
			value = request.form.get(item)
			if value == "on":
				if item.upper() not in location:
					location.append(item.upper())
			if value == None:
				if item.upper() in location:
					position = location.index(item.upper())
					location.pop(position)
		print(include)
		print(exclude)
	filtered = filterr(listings)
	return render_template("search.html",content = filtered,locations = location)

@app.route("/",methods=['GET', 'POST'])
def home():
	global listings,maxprice,minprice,maxdate,sort,exclude,include,location
	listings = {}
	maxprice = None
	minprice = None
	maxdate = None
	sort = 'date'
	exclude = []
	include = []
	location = []
	global pages,searchterm
	if request.method == "POST":
		first_name = request.form.get("fname")
		print(first_name)
		searchterm = first_name
		if "," in first_name:
			startthreads(first_name)
			return redirect(url_for('search'))
		else:
			pages = getpages(first_name)
			print(pages)
			if pages == None:
				return redirect(url_for('error'))
			multithread(searchterm,5)
			return redirect(url_for('search'))

	return render_template("index.html")

def getpages(searchterm):
	url = f"https://ikman.lk/en/ads/sri-lanka?sort=relevance&buy_now=0&urgent=0&query={searchterm}&page={1}"
	print(url)
	page = requests.get(url)
	soup = BeautifulSoup(page.content, "html.parser")
	lrank = None
	for wrapper in soup.find_all('div', {"class":"no-result-text--16bWr"}):
		if lrank == None:
			lrank = (wrapper.text)
			print(lrank)
			if lrank == "No results found!":
				pages = lrank
	for wrapper in soup.find_all('span', {"class":"ads-count-text--1UYy_"}):
		if lrank == None:
			lrank = (wrapper.text)
			print(lrank)
			stuff = lrank.split(" ")
			lrank = stuff[-2]
			pages = int(lrank)/25
			pages = int(pages)+1
			return(pages)

def multithread(searchterm,threadss):
	threads = []
	global pages
	print(pages,threadss)
	if int(threadss) == 1:
		getlistings(searchterm,"none","none")
	else:	
		num2 = int(pages/5)+2
		num1 = 1
		num3 = int(threadss)
		count = 0
		while count<num2:
			if num3+int(threadss) > pages:
				x = threading.Thread(target=getlistings, args=(searchterm,num1,"none"))
			else:
				x = threading.Thread(target=getlistings, args=(searchterm,num1,num3))
			num1 = num1 + int(threadss)
			num3 = num3 + int(threadss)
			x.start()
			threads.append(x)
			count+=1
		for thread in threads:
			thread.join()


def startthreads(searchterm):
	if "," in searchterm:
		threads = []
		searchterms = searchterm.split(",")
		for term in searchterms:
			x = threading.Thread(target=getlistings, args=(term,"none",'none'))
			x.start()
			threads.append(x)
		for item in threads:
			item.join()
	else:
		x = threading.Thread(target=getlistings, args=(searchterm,'none',"none"))
		x.start()
		x.join()

def sort_by_price(items, prices):
    return [i[0] for i in sorted(zip(items, prices), key=lambda x: x[1])]

def filterr(listings):
	names = []
	prices = []
	global maxprice,minprice,maxdate,sort
	sortedd = {}
	for element in listings:
		pas = True
		if maxprice != None:
			price = listings[element]["price"]
			price = price.replace(",","")
			price = int(price)
			maxprice = int(maxprice)
			if price > maxprice:
				pas = False
		if minprice != None:
			price = listings[element]["price"]
			price = price.replace(",","")
			price = int(price)
			minprice = int(minprice)
			if price < minprice:
				pas = False
		if len(location) != 0:
			loc = listings[element]["location"]
			if loc.upper() not in location:
				pas = False
		if len(exclude) != 0:
			for item in exclude:
				if item.upper() in element.upper():
					pas = False
		if len(include) != 0:
			for item in include:
				if item.upper() not in element.upper():
					pas = False
		if maxdate != None:
			date = listings[element]["time"]
			if int(date) > int(maxdate):
				pas = False
		if pas == True:
			if sort == 'date':	
				names.append(listings[element]["title"])
				date = int(listings[element]['time'])
				prices.append(date)
			else:
				names.append(listings[element]["title"])
				price = listings[element]["price"]
				price = price.replace(",","")
				price = int(price)
				prices.append(price)
	if sort == 'price':
		lis = sort_by_price(names,prices)
		for element in lis:
			sortedd[element] = {}
			sortedd[element]["title"] = element
			sortedd[element]["price"] = listings[element]['price']
			sortedd[element]["link"] = listings[element]['link']
			sortedd[element]["time"] = listings[element]['time']
			sortedd[element]["location"] = listings[element]['location']
			sortedd[element]["img"] = listings[element]['img']
	if sort == 'date':
		lis = sort_by_price(names,prices)
		for element in lis:
			sortedd[element] = {}
			sortedd[element]["title"] = element
			sortedd[element]["price"] = listings[element]['price']
			sortedd[element]["link"] = listings[element]['link']
			sortedd[element]["time"] = listings[element]['time']
			sortedd[element]["location"] = listings[element]['location']
			sortedd[element]["img"] = listings[element]['img']
	return(sortedd)

def getlistings(searchterm,startpoint,endpoint):
	global listings
	nextpage = True
	if startpoint == "none":
		pagenum = 1
	else:
		pagenum = startpoint
	while nextpage == True:
		searchterm = searchterm.replace(" ","%20")
		url = f"https://ikman.lk/en/ads/sri-lanka?sort=relevance&buy_now=0&urgent=0&query={searchterm}&page={pagenum}"
		print(url)
		page = requests.get(url)
		soup = BeautifulSoup(page.content, "html.parser")
		lrank = None
		for wrapper in soup.find_all('div', {"class":"no-result-text--16bWr"}):
			#chechking for more pages
			if lrank == None:
				lrank = (wrapper.text)
				if lrank == "No results found!":
					nextpage = False
		for wrapper in soup.find_all('li', {"class":"normal--2QYVk gtm-normal-ad"}):
			###getting listing and data
			if lrank == None:
				listing = (wrapper)
				if listing != None:
					stuffs = str(listing).split(" ")
					fortitle = str(listing).split("h2")
				#print(stuffs)
				#print(fortitle)
				for stuff in fortitle:
					if len(stuff) > 8:
						if stuff[8] == "h":
							titleunformated = stuff
							break
				try:	
					fortime = fortitle[-1].split("<")
					for element in fortime:
						if len(element) > 8:
							time = element
					time = time.split(">")
					time = time[-1]
					time = time.split(" ")
					less = ["HOUR","HOURS","MINUTES","MINUTE"]
					suff = time[-1]
					suff = str(suff)
					if suff.upper() in less:
						time = 1 
					else:
						time = time[0]
				except:
					time = 1
				if time == '' or time == 'days':
					time = 1
				try:	
					titleunformated = titleunformated.split(">")
					titleunformated = titleunformated[1]
					titleunformated = titleunformated.split("<")
					title = titleunformated[0]
				except:
					title = "error occured"
				try:
					fortitle = fortitle[-1]
					fortitle = fortitle.split("description")
					fortitle = fortitle[1]
					fortitle = fortitle.split(">")
					fortitle = fortitle[1]
					fortitle = fortitle.split(",")
					fortitle = fortitle[0]
					location = fortitle
				except:
					location = "a error occured"
				for stuff in stuffs:
					if stuff[0] == "h" and stuff[1] == "r":
						stuff = stuff.split('"')
						link = f"https://ikman.lk{stuff[1]}"
					if stuff[-1] == "n" and stuff[-2] == "a":
						stuff = stuff.split('<')
						price = stuff[0]
					if stuff[0] == "s" and stuff[1] == "r":
						items = stuff.split('"')
						item = items[1]
						items = item.split(">")
						item = items[0]
						image = item
				if "," in price:	
					listings[title]={}
					listings[title]["title"] = title
					listings[title]["price"] = price
					listings[title]["location"] = location
					listings[title]["link"] = link
					listings[title]["time"] = time
					listings[title]['img'] = image
		if endpoint == "none":
			pass
		elif endpoint == pagenum:
			nextpage = False
		pagenum += 1
if __name__ == "__main__":
	print(listings)
	app.run(host='0.0.0.0', port=8080)