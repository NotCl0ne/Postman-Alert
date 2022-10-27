#!/usr/bin/python3
from flask import message_flashed
from telegram.ext import Updater
import requests
import re
import yaml
from constants import BOT_TOKEN,CHAT_ID
import postman
#import os

#os.chdir('/home/antqt/Security-Alert/')
def send(messages):
	updater = Updater(token=BOT_TOKEN, use_context=True)
	for message in messages:
		updater.bot.send_message(chat_id=CHAT_ID, text=message)

def load_urls(links_path):
	with open(links_path) as f:
		data = yaml.load(f,Loader=yaml.FullLoader)
	return data

def load_config(yaml_path):
	with open(yaml_path) as f:
		config = yaml.load(f,Loader=yaml.FullLoader)
		host=config['host']
		tuple_location=config['tuple_location']

		data_location=config['data_location']
		number_rows=config['number_rows']
		pages=config['pages']
		empty_page=config['empty_page']

		report_location=config['report_location']
		api_link=config['api_link']

	return host,tuple_location,data_location,number_rows,pages,empty_page,report_location,api_link


def get_current_record(tuple_location,data_location,number_rows,pages,empty_page,url,api_link):
	page=1
	all_res=''
	records={}

	session = requests.session()

	if(api_link==""):
		if(pages!=''):
			while (True):
				res = session.get(url+pages+str(page))
				if(empty_page in res.text): break
				all_res+=res.text
				page+=1
		else:
			all_res=session.get(url).text

		all_tuples=re.findall(tuple_location,all_res)


		for _tuple in all_tuples:
			data=[]
			data_on_1_line={}
			for _data_location in data_location:
				data.append(re.findall(data_location[_data_location],_tuple)[0])
			data_on_1_line[data[0]]=data[1:]
			records.update(data_on_1_line)
			
				
	else:
		all_res = session.get(api_link).json()
		all_tuples=all_res[tuple_location]

		for _tuple in all_tuples:
			data_list=[]
			data_on_1_line={}
			for _data_location in data_location:
				data_element ="" if data_location[_data_location] == "" else _tuple[data_location[_data_location]]
				data= "Pending" if data_element == None else data_element
				data_list.append(data)
			data_on_1_line[data_list[0]]=data_list[1:]
			records.update(data_on_1_line)

	return dict(list(records.items())[:number_rows])

# def get_old_record(location):
# 	try:
# 		with open(location) as f:
# 			records = 
# 	except:
# 		print("Can't find old records!")
# 		records={}

	return records

def write_yaml(destination,content):
	with open(destination, 'w') as file:
		yaml.dump(content, file)

def format_message(links):
	messages=[]
	for link in links:
		message="""[*] Found sensitive in collection Link: {}
		""".format(link)
		messages.append(message)
	return messages
	

if __name__ == '__main__':
	old_record=postman.read_file_into_list("log.txt")
	current_record=postman.run()
	
	diff =  list(set(current_record) - set(old_record))

	if(len(diff)!=0):
		message_list=format_message(diff)
		send(message_list)
		postman.print_and_write("log.txt","\n".join(current_record),"w")

