import requests
import json
import re 
from postmanparser import Collection
from colorama import Fore, Style
from pathlib import Path
from datetime import datetime
import os
import time 

collection = Collection()

# Sensitive Check
zalo_keyword = ["zalo"]
sensitive_keyword = ["token", "secret", "pass", "authoriz", "cookie"]
zalo_url_regex = "^.*\\.(zalo|zdn|zaloapp|zapps)\\.(vn|me|com)((\\/).*)?$"


score_match = 100
keyword_file_location = "keyword.txt"
collection_id_list_file_location = "collection_list.log"
log_file_location="log.txt"
postman_api_key = "PMAK-6352b79d60c700004383173c-dd3d014846f2125ca1572de6586523b486"
search_url = "https://www.postman.com:443/_api/ws/proxy"
get_collection_url = "https://api.getpostman.com/collections/"
header = {"X-Api-Key": postman_api_key, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0", "Accept": "*/*", "Accept-Language": "en-US,en;q=0.5", "Accept-Encoding": "gzip, deflate", "Referer": "https://www.postman.com/search?q=https%3A%2F%2Fstg-event.zalo.me%2Fringback-tone%2Fupdateringtone&scope=public&type=all", "Content-Type": "application/json", "Traceparent": "00-9db216d494aa67f0151f5ecf9a481a0a-3d812dd0cbd04522-01", "Tracestate": "2665918@nr=0-1-2665918-771436762-3d812dd0cbd04522----1666361679817", "X-App-Version": "9.31.26-221020-0605", "X-Entity-Team-Id": "0", "Origin": "https://www.postman.com", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-origin", "Te": "trailers"}

collection_list = []
list_of_error_collection_id = []

class postman_collection:
	def __init__(self, collection_id, publisherHandle, name):
		self._id = collection_id
		self._publisherHandle = publisherHandle
		self._name = name

def read_file_into_list(name):
	result = []
	with open(name) as file:
		while (line := file.readline().rstrip()):
			result.append(line)

	return result

def parse_collection(self, url):
        response = None
        try:
            response = get_request(url)["collection"]
        except Exception:
            pass
        if response is None:
            return
        self.validate(response)
        self.parse(response)
Collection.parse_from_url = parse_collection

def print_and_write(name, content, mode="a+", color="", print_or_not=False):
	if (print_or_not):
		print(color + content + Style.RESET_ALL)
	save_to_file(name, content, mode)
	return content

def check_folder(name):
	Path(name).mkdir(parents=True, exist_ok=True)

def save_to_file(name, content, mode="a+"):
	content = content.encode('ascii',errors='ignore').decode('ascii')
	f = open(name, mode)
	f.write(content)
	f.write("\n")
	f.close()

def post_request(url, body):
	req = requests.post(url, headers=header, json=body)
	result = json.loads(req.text)
	return result

def get_request(url):
	req = requests.get(url, headers=header)
	result = json.loads(req.text)
	return result

def extract_collection_id_from_results(results, score):
	global list_of_error_collection_id

	extracted_result_array = []
	try:
		results = results['data']
		for result in results:
			if result["score"]>=score and result['document']['id'] not in list_of_error_collection_id:
				try:
					if any(element in result['document']['workspaces'][0]['slug'].lower() for element in zalo_keyword) or any(element in result['document']['name'].lower() for element in zalo_keyword) or any(element in result['requests']['document']['name'].lower() for element in zalo_keyword) or re.search(zalo_url_regex, result['requests']['document']['url'].lower()):
						collection = postman_collection(result['document']['id'], result['document']['publisherHandle'], result['document']['workspaces'][0]['slug'])
						extracted_result_array.append(collection)
				except:
					# print_and_write(log_file_location, "[-] id {id} don't have any workspace, pass".format(id=result['document']['id']), Fore.RED)
					list_of_error_collection_id.append(result['document']['id'])
		
	except:
		pass
	return extracted_result_array
	
def find_sensitive(item):
	result = ""
	found = 0
	try:
		api_name = item.url.raw
			# check vl
		if re.search(zalo_url_regex, item.url.raw.lower()):
			try:
				if (item.auth.auth_type is not None):
					# print_and_write(log_file_location,"\t\t[!] Found auth info ({type}) at API <{api_name}>".format(type=item.auth.auth_type, api_name=api_name), Fore.RED)
					result += "\t[!] Found auth info ({type}) at API <{api_name}>\n".format(type=item.auth.auth_type, api_name=api_name)
					found += 1
			except Exception as e:
				#save_to_file(log_file_location, str(e))
				# don't have auth info 
				pass

			for header in item.header:
				if any(element in header.key.lower() for element in sensitive_keyword):
					# print_and_write(log_file_location,"\t\t[!] Found sensitive header at API <{api_name}>".format(api_name=api_name), Fore.RED)
					result += "\t[!] Found sensitive header at API <{api_name}>\n".format(api_name=api_name)
					found += 1
		
			if (item.method == "GET" and any(element in item.url.raw.lower() for element in sensitive_keyword)):
				# print_and_write(log_file_location,"\t\t[!] Found sensitive keyword in URL query at API <{api_name}>".format(api_name=api_name), Fore.RED)
				result += "\t[!] Found sensitive keyword in URL query at API <{api_name}>\n".format(api_name=api_name)
				found += 1


			if (item.method == "POST" and ( any(element in item.url.raw.lower() for element in sensitive_keyword) or any(element in item.body.raw.lower() for element in sensitive_keyword) )):
				# print_and_write(log_file_location,"\t\t[!] Found sensitive keyword in POST data at API <{api_name}>".format(api_name=api_name), Fore.RED)
				result += "\t[!] Found sensitive keyword in POST data at API <{api_name}>\n".format(api_name=api_name)
				found += 1
	except Exception as e:
		# save_to_file(log_file_location, str(e))
		pass
	return result.rstrip(), found



def extract_data_from_collections(collection_object_array):
	global list_of_collection_id
	content = []
	for collection in collection_object_array:
		if collection._id not in list_of_collection_id:
			list_of_collection_id.append(collection._id)
			url = get_collection_url + collection._id
			link_to_collection = "https://www.postman.com/{publisherHandle}/workspace/{name}/overview".format(publisherHandle=collection._publisherHandle, name=collection._name)
			collection_obj = Collection()
			collection_obj.parse_from_url(url)
			requests = collection_obj.get_requests(recursive=False)
			for item in requests:
				result, found = find_sensitive(item)
				if (result != ""):
					if (link_to_collection not in collection_list):
						# print_and_write(log_file_location,"[*] Found sensitive in collection Link: {link}, ID: {id} \n".format(link=link_to_collection, id=collection._id), Fore.GREEN)
						content.append("{link}".format(link=link_to_collection))
						collection_list.append(link_to_collection)
					# print_and_write(log_file_location, result, Fore.RED)
			save_to_file(collection_id_list_file_location, collection._id)
	return content

def check_expired_collection_list_file():
	day_to_delete = 10
	last_edit = os.stat(collection_id_list_file_location).st_ctime
	time_check = time.time() - (day_to_delete * 24 * 60 * 60)
	if os.path.exists(collection_id_list_file_location):
		if time_check >= last_edit:
			Path(collection_id_list_file_location).unlink()

def run():
	global list_of_collection_id
	content = []
	if (Path(collection_id_list_file_location).is_file()):
		check_expired_collection_list_file()
		list_of_collection_id = read_file_into_list(collection_id_list_file_location)
	else:
		list_of_collection_id = []
	keyword_list = read_file_into_list(keyword_file_location)
	for keyword in keyword_list:
		body = {"body": {"clientTraceId": "7ae36598-2500-43cb-a732-1b08c10d61a5", "domain": "public", "from": 0, "mergeEntities": True, "queryIndices": ["collaboration.workspace", "adp.api", "runtime.collection", "apinetwork.team", "flow.flow"], "queryText": keyword, "requestOrigin": "srp", "size": 10}, "method": "POST", "path": "/search-all", "service": "search"}
		collection_object_array = extract_collection_id_from_results(post_request(search_url, body), score_match)
		content.extend(extract_data_from_collections(collection_object_array))
	return content

# if __name__ == "__main__":
# 	content = run()
# 	print(content)	
	
