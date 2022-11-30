#!/usr/bin/env python3

from genericpath import exists
import unicodedata
import argparse
import re
import json
import os
import logging
import shelve
import asyncio
import aiohttp
import time

def environ_or_required(key):
    return (
        {'default': os.environ.get(key)} if os.environ.get(key)
        else {'required': True}
    )

def parse_cmdline():
	parser = argparse.ArgumentParser(description='Sync files from Midjourney',fromfile_prefix_chars='@')

	parser.add_argument('--token', type=str, help='Midjourney session token', **environ_or_required('MJ_API_TOKEN') )
	parser.add_argument('--uid', type=str, **environ_or_required('MJ_USER_ID'))
	parser.add_argument('--filter', choices=['upscale', 'grid','all'], default='upscale')
	parser.add_argument('--debug', action='store_true')
	parser.add_argument('--json', action='store_true')
	parser.add_argument('--db', type=str, help='DB file for caching already downloaded prompts', default="mjcache")

	return parser.parse_args()


async def main():

	args=parse_cmdline()

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
		# create a list of download tasks
		tasks = []

		async with aiohttp.ClientSession() as session:
			while(True):
				url = "https://www.midjourney.com/api/app/recent-jobs/?amount=50&jobType="+img_type+ \
					"&orderBy=new&user_id_ranked_score=null&jobStatus=completed&userId="+user_id+"&dedupe=true&refreshApi=0&page="+str(page)
				async with session.get(url, cookies=cookies) as response:
					r = await response.json()

				if debug:
					print (r) 

				if ('msg' in r):
					print (r['msg'])
					exit (1)

				for render in r:
					foundImage = 0
					if 'image_paths' in render:
						renderName = slugify(render['full_command'])

						if write_json:
							write_json(render, renderName+".json") 

						for image in render['image_paths']:
							filename = renderName + render['id']+".png"
							if str(filename) not in db:
								db[filename] = True			
								print("Queueing: " + str(totalImages) + ") -> "+ render['full_command'])
								tasks.append(download_image(session, image, filename))

							foundImage += 1
							totalImages += 1
				# no images left.
				if foundImage == 0:
					break
				page += 1;

			# wait for all download tasks to complete
			await asyncio.gather(*tasks)

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

async def download_image(session , url : str, path : str):
	print ("Starting download: ",path, "...", sep=None)

	if not exists(path):
			start_time = time.time()
			async with session.get(url) as r:
				if r.status == 200:
					with open(path, 'wb') as f:
						while True:
							chunk = await r.content.read(1024)
							if not chunk:
								break
							f.write(chunk)
				elapsed_time = time.time() - start_time
				print (path, ": DONE (elapsed time: {:.2f} seconds)\n".format(elapsed_time))
	else:
		print ("SKIPPED\n")			

if __name__ == "__main__":
	asyncio.run(main())
