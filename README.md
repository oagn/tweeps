# tweeps

Code for downloading a stream of tweets, based twython and watchdog. The code was last run in 2019 for a master's project.  

The tweets are downloaded based on 'terms' and 'follows'. In this project the 'terms' are a list of UH Higher Education handles and 'follows' are a list of the corresponding user ids.   

You will need to have an app_key, an app_secret, an oauth_token and an oauth_token_secret. this used to be available through dev.twitter.com and might still be available through https://developer.x.com/en. 
The tweets with corresponding metadata are saved in a mongo database that you will also need to create. See https://www.mongodb.com/resources#pf-content-section for details on setting up and maintaining a mongodb.   

This version of the code was run on an ubuntu VM with limited storage. See monto_maintenance.txt for command line examples on how to export and delete data. 
