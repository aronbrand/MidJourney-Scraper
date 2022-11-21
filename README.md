# MidJourney-Scraper
A Python Script to Download all MidJourney renders from any user, written in python and easy to use.

Enhanced version.

- Easy to identify english named files
- Downloads all files on all pages for any midjourny user.
- keeps json metadata and command used to render in a seperate .json file
- Only downloads new files, can be run more than once to keep sync
- Cache database avoids downloading even if you already deleted the downloaded files
- Fetch parameters from command line or environment variable
- Filter to download only upscaled renders, grids, or both

This will download all of the midjourny renders.  All you need to do is provide a user id and your session id from your browser.

You supply the needed parameters from the command line, or by setting the environment variables MJ_API_TOKEN (session token) and MJ_USER_ID.

To get the session id go into Chrome developer tools. CLick on the application tab within the developer tool bar,  click on cookies on the left and use the
__Secure-next-auth.session-token cookie. 

If you don't provide a userid, the program will download your own files.
