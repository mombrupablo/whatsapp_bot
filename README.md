This project is about creating a whatsapp bot to interact with a user.

1. Current status:
------------------
The bot has been implemented with a basic functionality. The bot responds to a few hardcoded input words.

2. The stack used to create the bot:
------------------------------------
2.1. Python
The code to integrate with the whatsapp API and respond based on the input from the whatsapp user's session is in Python. The program is called app.py.

2.2. Meta Whatsapp API
This is the API provided by Meta to interact with Whatsapp. To access this API, the following parameters are informed:
- An authentication token provided by Meta. It exists in an environment variable.
- A phone number and ID provided by Meta. This is the phone number used as the bot.
- A destination phone number. This is my personal cell phone that acts as the requesting user.
The three parameters are saved in environment variables, so they're not in the repository.

2.3. Render Cloud Server:
As the Meta whatsapp API requires a cloud server for the integration, I'm using Render.
The Render server is plugged into this repository, so every commit is immediately built and deployed into the server when commiting the changes.
The server is already configured to allow the integration between the python's app and Meta.
I'm currently the only user that can access and configure the Render server as well as access to the Meta app used for the integration.

2.4 SQLite DB:
A small DB with only one table called Log. By now, only the inputs from the user are being registered.
The table include the following columns:
- Datetime
- Log ID
- Text
This DB runs in the Render server and can run in a local environment. The DB is managed by the python's app.

3. What has to be achieved - NEXT STEPS
---------------------------------------
The idea is to extend the current functionality to a CRM feature.
The new tasks to consider are:
- Create a flow with specific questions when a user access to the whatsapp bot.
- Register the user's information and save it as a lead to be contacted in the future.
- Save the responses of the user.
- Improve the logging functionality by registering the interaction between user and bot, including the errors.
- Avoid processing the same inquiry of the same user more than once.
- Design and create the DB schema that will be used.
- Ensure that the best practices are used.
- Generate documentation of the code and the DB's schema (tables, keys, joins).

As the stack for the future functionality, I'm planning to use:
- Python as the main app.
- Meta's API.
- Render Cloud Server.
- PostgreSQL DB (instead of SQLite) as the DB.