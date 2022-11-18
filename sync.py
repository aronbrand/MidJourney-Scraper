#!/usr/bin/env python3

import requests
import unicodedata
import argparse
import re
import json
import os
import logging
import shelve
from os.path import exists

def environ_or_required(key):
    return (
        {'default': os.environ.get(key)} if os.environ.get(key)
        else {'required': True}
    )

def main():
	parser = argparse.ArgumentParser(description='Sync files from Midjourney',fromfile_prefix_chars='@')

	parser.add_argument('--token', type=str, help='Midjourney session token', **environ_or_required('MJ_API_TOKEN') )
	parser.add_argument('--uid', type=str, **environ_or_required('MJ_USER_ID'))
	parser.add_argument('--filter', choices=['upscale', 'grid','all'], default='upscale')
	parser.add_argument('--debug', action='store_true')
	parser.add_argument('--json', action='store_true')
	parser.add_argument('--db', type=str, help='DB file for caching already downloaded prompts', default="mjcache")

	args=parser.parse_args()

	session_token = args.token
	user_id = args.uid
	img_type = args.filter
	write_json = args.json
	debug = args.debug
	dbfile = args.db

	logging.getLogger('root').setLevel(logging.INFO)

	if not len(session_token):
		session_token = input("What is your MidJourney Session ID? (hint: it starts with eyJ and you get it from your browser): ")

	cookies = {'__Secure-next-auth.session-token': session_token}
	page = 1
	totalImages = 0 

	with shelve.open(dbfile, flag='c') as db:
		while(True):
			r = requests.get("https://www.midjourney.com/api/app/recent-jobs/?amount=50&jobType="+img_type+"&orderBy=new&user_id_ranked_score=null&jobStatus=completed&userId="+user_id+"&dedupe=true&refreshApi=0&page="+str(page), cookies=cookies)
			if debug:
				print (r.json()) 

			for render in r.json():
				foundImage = 0
				if 'image_paths' in render:
					renderName = slugify(render['full_command'])

					if write_json:
						write_json(render, renderName+".json") 

					for image in render['image_paths']:
						filename = renderName + render['id']+".png"
						if str(filename) not in db:
							db[filename] = True			
							print("Syncing: " + str(totalImages) + ") -> "+ render['full_command'])
							download_image(image, filename)
						foundImage += 1
						totalImages += 1
			# no images left.
			if foundImage == 0:
				break
			page += 1;

def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    # remove urls
    value = re.sub(r'http\S+', '', value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    ret = re.sub(r'[-\s]+', '-', value).strip('-_')
    return ret[0:200]

def write_json(obj, path):
	# only sync new files.
	if not exists(path):	
		info = open(path,"w")
		info.write(json.dumps(obj))
		info.close()


def download_image(url, path):
	# only sync new files.
	if not exists(path):
		r = requests.get(url, stream=True)
		if r.status_code == 200:
			with open(path, 'wb') as f:
				for chunk in r:
					f.write(chunk)
		print ("DONE\n") 	
	else:
		print ("SKIPPED\n") 				

if __name__ == "__main__":
	main()
